"""SQLite schema 初始化与版本迁移。"""

import sqlite3
import time
from pathlib import Path

# 当前代码期望的 schema 版本
SCHEMA_VERSION = 1

# ──────────────────────────────────────────────
# DDL 语句
# ──────────────────────────────────────────────

_CREATE_FILES = """
CREATE TABLE IF NOT EXISTS files (
    file_path     TEXT PRIMARY KEY,
    module        TEXT NOT NULL,
    file_type     TEXT NOT NULL,
    source_set    TEXT NOT NULL DEFAULT 'impl',
    last_modified REAL NOT NULL,
    symbol_count  INTEGER NOT NULL DEFAULT 0,
    parse_status  TEXT NOT NULL DEFAULT 'ok',
    parse_error   TEXT,
    indexed_at    REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_files_module ON files(module);
CREATE INDEX IF NOT EXISTS idx_files_type ON files(file_type);
"""

_CREATE_SYMBOLS = """
CREATE TABLE IF NOT EXISTS symbols (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    qualified_name  TEXT NOT NULL UNIQUE,
    kind            TEXT NOT NULL,
    module          TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    source_set      TEXT NOT NULL,
    line_number     INTEGER,
    signature       TEXT,
    visibility      TEXT,
    is_abstract     INTEGER NOT NULL DEFAULT 0,
    is_override     INTEGER NOT NULL DEFAULT 0,
    parent_class    TEXT,
    interfaces      TEXT,
    annotations     TEXT,
    return_type     TEXT,
    parameters      TEXT,
    resource_value  TEXT,
    extra           TEXT
);
CREATE INDEX IF NOT EXISTS idx_symbols_name           ON symbols(name);
CREATE INDEX IF NOT EXISTS idx_symbols_kind           ON symbols(kind);
CREATE INDEX IF NOT EXISTS idx_symbols_module         ON symbols(module);
CREATE INDEX IF NOT EXISTS idx_symbols_file           ON symbols(file_path);
CREATE INDEX IF NOT EXISTS idx_symbols_parent         ON symbols(parent_class);
CREATE INDEX IF NOT EXISTS idx_symbols_visibility     ON symbols(visibility);
CREATE INDEX IF NOT EXISTS idx_symbols_return_type    ON symbols(return_type);
CREATE INDEX IF NOT EXISTS idx_symbols_resource_value ON symbols(resource_value);
"""

_CREATE_MODULE_DEPS = """
CREATE TABLE IF NOT EXISTS module_dependencies (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    module           TEXT NOT NULL,
    depends_on       TEXT NOT NULL,
    dependency_type  TEXT NOT NULL,
    dependency_scope TEXT NOT NULL,
    syntax           TEXT NOT NULL,
    raw_declaration  TEXT NOT NULL,
    source_file      TEXT NOT NULL,
    UNIQUE(module, depends_on, dependency_scope, syntax)
);
CREATE INDEX IF NOT EXISTS idx_moddep_module     ON module_dependencies(module);
CREATE INDEX IF NOT EXISTS idx_moddep_depends_on ON module_dependencies(depends_on);
CREATE INDEX IF NOT EXISTS idx_moddep_syntax     ON module_dependencies(syntax);
"""

_CREATE_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS symbols_fts USING fts5(
    name,
    qualified_name,
    annotations,
    module,
    content='symbols',
    content_rowid='id',
    tokenize='unicode61'
);
"""

_CREATE_TRIGGERS = """
CREATE TRIGGER IF NOT EXISTS symbols_ai AFTER INSERT ON symbols BEGIN
    INSERT INTO symbols_fts(rowid, name, qualified_name, annotations, module)
    VALUES (new.id, new.name, new.qualified_name,
            COALESCE(new.annotations, ''), new.module);
END;

CREATE TRIGGER IF NOT EXISTS symbols_ad AFTER DELETE ON symbols BEGIN
    INSERT INTO symbols_fts(symbols_fts, rowid, name, qualified_name, annotations, module)
    VALUES ('delete', old.id, old.name, old.qualified_name,
            COALESCE(old.annotations, ''), old.module);
END;

CREATE TRIGGER IF NOT EXISTS symbols_au AFTER UPDATE ON symbols BEGIN
    INSERT INTO symbols_fts(symbols_fts, rowid, name, qualified_name, annotations, module)
    VALUES ('delete', old.id, old.name, old.qualified_name,
            COALESCE(old.annotations, ''), old.module);
    INSERT INTO symbols_fts(rowid, name, qualified_name, annotations, module)
    VALUES (new.id, new.name, new.qualified_name,
            COALESCE(new.annotations, ''), new.module);
END;
"""

_CREATE_SCHEMA_VERSION = """
CREATE TABLE IF NOT EXISTS schema_version (
    version     INTEGER NOT NULL,
    applied_at  REAL NOT NULL,
    description TEXT
);
"""

# ──────────────────────────────────────────────
# 迁移脚本（版本 N → N+1 的 SQL 列表）
# 新增 schema 变更时在此追加
# ──────────────────────────────────────────────
_MIGRATIONS: dict[int, list[str]] = {
    # 版本 1 为初始 schema，无需额外迁移 SQL
}


def get_connection(db_path: Path) -> sqlite3.Connection:
    """返回一个已启用 WAL 模式的 SQLite 连接。"""
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: Path | None = None) -> sqlite3.Connection:
    """
    初始化数据库：创建所有表、索引、触发器，并执行版本迁移。

    启动时读取 schema_version 表中的当前版本；若低于 SCHEMA_VERSION，
    依次执行对应的迁移 SQL，完成后更新 schema_version 记录。
    """
    from src.config import DB_PATH
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = get_connection(path)

    # 1. 创建基础表结构（IF NOT EXISTS 保证幂等）
    for ddl in [_CREATE_FILES, _CREATE_SYMBOLS, _CREATE_MODULE_DEPS,
                _CREATE_SCHEMA_VERSION]:
        conn.executescript(ddl)

    # 2. FTS5 虚拟表和触发器
    conn.executescript(_CREATE_FTS)
    conn.executescript(_CREATE_TRIGGERS)

    conn.commit()

    # 3. 读取当前版本
    row = conn.execute(
        "SELECT MAX(version) as ver FROM schema_version"
    ).fetchone()
    current_version = row["ver"] if row["ver"] is not None else 0

    if current_version == 0:
        # 首次创建，写入初始版本记录
        conn.execute(
            "INSERT INTO schema_version(version, applied_at, description) VALUES (?, ?, ?)",
            (1, time.time(), "initial schema"),
        )
        conn.commit()
        current_version = 1

    # 4. 执行待迁移步骤
    for target_version in range(current_version + 1, SCHEMA_VERSION + 1):
        migration_sqls = _MIGRATIONS.get(target_version, [])
        for sql in migration_sqls:
            conn.execute(sql)
        conn.execute(
            "INSERT INTO schema_version(version, applied_at, description) VALUES (?, ?, ?)",
            (target_version, time.time(), f"migration to v{target_version}"),
        )
        conn.commit()

    return conn
