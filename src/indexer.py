"""全量索引与增量更新主流程。"""

import time
import sqlite3
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from src.config import DB_PATH
from src.database import init_db
from src.file_scanner import scan_project, SourceFile
from src.parsers.kotlin_parser import parse_kotlin_file
from src.parsers.java_parser import parse_java_file
from src.parsers.xml_parser import parse_xml_file
from src.parsers.gradle_parser import parse_gradle_file
from src.utils.tokenize import split_identifier

console = Console()


# ──────────────────────────────────────────────
# 解析分发
# ──────────────────────────────────────────────

def _parse_file(sf: SourceFile) -> tuple[list[dict], list[dict], str | None]:
    """
    解析单个文件，返回 (symbols, dep_records, warning)。
    symbols       → 写入 symbols 表
    dep_records   → 写入 module_dependencies 表
    """
    ft = sf.file_type
    fp = sf.file_path
    module = sf.module
    source_set = sf.source_set

    if ft == "kotlin":
        syms, warn = parse_kotlin_file(fp, module, source_set)
        return syms, [], warn
    if ft == "java":
        syms, warn = parse_java_file(fp, module, source_set)
        return syms, [], warn
    if ft == "xml":
        syms, warn = parse_xml_file(fp, module, source_set)
        return syms, [], warn
    if ft == "gradle":
        deps, warn = parse_gradle_file(fp, module)
        return [], deps, warn
    return [], [], None


# ──────────────────────────────────────────────
# 批量写入
# ──────────────────────────────────────────────

_INSERT_SYMBOL = """
INSERT OR IGNORE INTO symbols
    (name, qualified_name, kind, module, file_path, source_set,
     line_number, signature, visibility, is_abstract, is_override,
     parent_class, interfaces, annotations, return_type, parameters,
     resource_value, extra, name_tokens)
VALUES
    (:name, :qualified_name, :kind, :module, :file_path, :source_set,
     :line_number, :signature, :visibility, :is_abstract, :is_override,
     :parent_class, :interfaces, :annotations, :return_type, :parameters,
     :resource_value, :extra, :name_tokens)
"""

_INSERT_DEP = """
INSERT OR IGNORE INTO module_dependencies
    (module, depends_on, dependency_type, dependency_scope, syntax, raw_declaration, source_file)
VALUES
    (:module, :depends_on, :dependency_type, :dependency_scope, :syntax, :raw_declaration, :source_file)
"""

_INSERT_FILE = """
INSERT INTO files
    (file_path, module, file_type, source_set, last_modified, symbol_count, parse_status, parse_error, indexed_at)
VALUES
    (:file_path, :module, :file_type, :source_set, :last_modified, :symbol_count, :parse_status, :parse_error, :indexed_at)
ON CONFLICT(file_path) DO UPDATE SET
    module        = excluded.module,
    file_type     = excluded.file_type,
    source_set    = excluded.source_set,
    last_modified = excluded.last_modified,
    symbol_count  = excluded.symbol_count,
    parse_status  = excluded.parse_status,
    parse_error   = excluded.parse_error,
    indexed_at    = excluded.indexed_at
"""


def _normalize_symbol(sym: dict, rel_path: str) -> dict:
    """确保 symbol 字典包含所有必要的默认字段，并用相对路径覆盖 file_path。"""
    defaults: dict[str, Any] = {
        "name": "",
        "qualified_name": "",
        "kind": "unknown",
        "module": "",
        "file_path": rel_path,
        "source_set": "impl",
        "line_number": None,
        "signature": None,
        "visibility": None,
        "is_abstract": 0,
        "is_override": 0,
        "parent_class": None,
        "interfaces": None,
        "annotations": None,
        "return_type": None,
        "parameters": None,
        "resource_value": None,
        "extra": None,
        "name_tokens": "",
    }
    defaults.update(sym)
    # 始终用相对路径覆盖（parsers 写入的是绝对路径）
    defaults["file_path"] = rel_path
    # 确保 name_tokens 始终基于最新的 name 填充
    if not defaults["name_tokens"] and defaults["name"]:
        defaults["name_tokens"] = split_identifier(defaults["name"])
    return defaults


def _index_file(
    conn: sqlite3.Connection,
    sf: SourceFile,
    failures: list[tuple[str, str]],
    project_root: Path,
) -> None:
    """在单个 transaction 内处理一个文件的删旧插新。"""
    rel_path = "/" + str(sf.file_path.relative_to(project_root))
    try:
        mtime = sf.file_path.stat().st_mtime
    except OSError:
        mtime = 0.0

    # 1. 清除该文件的旧符号和旧依赖
    conn.execute("DELETE FROM symbols WHERE file_path = ?", (rel_path,))
    conn.execute("DELETE FROM module_dependencies WHERE source_file = ?", (rel_path,))

    # 2. 解析
    syms, deps, warning = _parse_file(sf)

    parse_status = "ok" if warning is None else "error"
    parse_error = warning

    if warning:
        failures.append((rel_path, warning))

    # 3. 批量插入 symbols
    if syms:
        conn.executemany(_INSERT_SYMBOL, [_normalize_symbol(s, rel_path) for s in syms])

    # 4. 批量插入 module_dependencies（source_file 也改为相对路径）
    if deps:
        rel_deps = [{**d, "source_file": rel_path} for d in deps]
        conn.executemany(_INSERT_DEP, rel_deps)

    # 5. 更新 files 表
    conn.execute(_INSERT_FILE, {
        "file_path": rel_path,
        "module": sf.module,
        "file_type": sf.file_type,
        "source_set": sf.source_set,
        "last_modified": mtime,
        "symbol_count": len(syms),
        "parse_status": parse_status,
        "parse_error": parse_error,
        "indexed_at": time.time(),
    })


# ──────────────────────────────────────────────
# Indexer 主类
# ──────────────────────────────────────────────

class Indexer:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DB_PATH
        self.conn = init_db(self.db_path)

    # ── 全量索引 ──────────────────────────────

    def index_full(self, project_root: Path) -> None:
        """扫描整个项目，全量建立索引（覆盖现有记录）。"""
        console.print(f"[bold]全量索引[/bold] {project_root}")
        source_files = scan_project(project_root)
        if not source_files:
            console.print("[yellow]未发现任何源文件，请确认 settings.gradle 存在。[/yellow]")
            return

        failures: list[tuple[str, str]] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("索引中...", total=len(source_files))

            # 每批 200 个文件提交一次 transaction，平衡性能与内存
            BATCH = 200
            batch: list[SourceFile] = []

            def _flush(batch: list[SourceFile]) -> None:
                with self.conn:
                    for sf in batch:
                        _index_file(self.conn, sf, failures, project_root)

            for sf in source_files:
                batch.append(sf)
                if len(batch) >= BATCH:
                    _flush(batch)
                    progress.advance(task, len(batch))
                    batch = []

            if batch:
                _flush(batch)
                progress.advance(task, len(batch))

        self._report(len(source_files), failures)

    # ── 增量更新 ──────────────────────────────

    def index_update(self, project_root: Path) -> None:
        """扫描项目，仅对新增或修改的文件重新解析，删除已消失的文件记录。"""
        console.print(f"[bold]增量更新[/bold] {project_root}")
        source_files = scan_project(project_root)

        # 读取数据库中已知的 mtime
        rows = self.conn.execute(
            "SELECT file_path, last_modified FROM files"
        ).fetchall()
        db_mtime: dict[str, float] = {r["file_path"]: r["last_modified"] for r in rows}

        current_paths = {"/" + str(sf.file_path.relative_to(project_root)) for sf in source_files}

        # 1. 删除已消失的文件
        deleted = set(db_mtime.keys()) - current_paths
        if deleted:
            with self.conn:
                for fp_str in deleted:
                    self.conn.execute("DELETE FROM symbols WHERE file_path = ?", (fp_str,))
                    self.conn.execute("DELETE FROM module_dependencies WHERE source_file = ?", (fp_str,))
                    self.conn.execute("DELETE FROM files WHERE file_path = ?", (fp_str,))
            console.print(f"  删除失效文件: {len(deleted)} 个")

        # 2. 找出新增 / 修改的文件
        to_index: list[SourceFile] = []
        for sf in source_files:
            rel_path = "/" + str(sf.file_path.relative_to(project_root))
            try:
                current_mtime = sf.file_path.stat().st_mtime
            except OSError:
                continue
            known_mtime = db_mtime.get(rel_path, 0.0)
            if current_mtime > known_mtime:
                to_index.append(sf)

        if not to_index:
            console.print("  [green]无需更新，所有文件均为最新。[/green]")
            return

        console.print(f"  待重新索引: {len(to_index)} 个文件")
        failures: list[tuple[str, str]] = []

        with self.conn:
            for sf in to_index:
                _index_file(self.conn, sf, failures, project_root)

        self._report(len(to_index), failures)

    # ── 工具 ──────────────────────────────────

    def _report(self, total: int, failures: list[tuple[str, str]]) -> None:
        success = total - len(failures)
        console.print(f"\n[green]完成[/green]: 成功 {success}/{total} 个文件")
        if failures:
            console.print(f"[yellow]解析失败 {len(failures)} 个文件:[/yellow]")
            for fp, err in failures:
                console.print(f"  {fp}")
                console.print(f"    {err}")
