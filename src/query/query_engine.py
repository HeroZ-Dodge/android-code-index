"""查询引擎：封装所有 SQLite 查询逻辑。"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from src.config import DB_PATH
from src.database import init_db


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


class QueryEngine:
    def __init__(self, db_path: Path | None = None) -> None:
        self.conn = init_db(db_path or DB_PATH)

    # ──────────────────────────────────────────────
    # 批次 1 (P0) 方法
    # ──────────────────────────────────────────────

    def search(
        self,
        keyword: str,
        kind: str | None = None,
        module: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        符号名全文搜索，返回 {total, items, search_time_ms}。

        使用 FTS5 全文搜索 + BM25 排序，支持：
          - 前缀搜索：Activity → Activity, ActivityManager, ActivityCompat
          - 多词搜索：Base Activity → 同时包含 Base 和 Activity 的结果
          - 精确搜索："Activity" → 完全匹配 Activity

        多因子排序 = BM25 相关度 + 类型权重 (class>function>property) + 名称长度惩罚

        注意：FTS5 查询限定在 name 字段，避免 annotations/qualified_name 中的干扰匹配
        """
        import time
        start = time.perf_counter()

        # 构建 FTS5 查询语句
        # 检测是否为精确搜索（带双引号）
        if keyword.startswith('"') and keyword.endswith('"'):
            # 精确短语匹配（在 name 字段）
            fts_query = f'name:"{keyword[1:-1]}"'
        else:
            # 默认前缀搜索 + 多词支持（仅在 name 字段）
            # 空格分隔的每个词都做前缀匹配
            terms = keyword.split()
            fts_terms = []
            for term in terms:
                # 转义 FTS5 特殊字符
                term = term.replace('"', '""').replace('*', '\\*')
                fts_terms.append(f'name:{term}*')
            fts_query = ' '.join(fts_terms)

        # 构建过滤条件
        filters: list[str] = []
        filter_params: list[Any] = []

        if kind:
            filters.append("s.kind = ?")
            filter_params.append(kind)
        if module:
            filters.append("s.module = ?")
            filter_params.append(module)

        where_clause = ""
        if filters:
            where_clause = " AND " + " AND ".join(filters)

        # 计数查询：使用 CROSS JOIN 优化性能（与主查询一致）
        count_sql = f"""
            SELECT COUNT(*)
            FROM (
                SELECT ft.rowid AS match_id
                FROM symbols_fts ft
                WHERE symbols_fts MATCH ?
            ) fts_matches
            CROSS JOIN symbols s
            WHERE s.id = fts_matches.match_id {where_clause}
        """
        total = self.conn.execute(count_sql, [fts_query] + filter_params).fetchone()[0]

        # 主查询：使用 CROSS JOIN 优化性能
        # 问题：原始 JOIN + WHERE 方式会导致 SQLite 优先使用 kind 索引而非 FTS5，造成性能下降（900ms+）
        # 解决：使用 CROSS JOIN 将 kind/module 过滤放到 WHERE 子句，强制 SQLite 先执行 FTS5 过滤
        # 参考：https://www.sqlite.org/optoverview.html#joins
        sql = f"""
            SELECT s.*
            FROM (
                SELECT ft.rowid AS match_id, bm25(symbols_fts, 10.0, 10.0, 1.0, 1.0) AS score
                FROM symbols_fts ft
                WHERE symbols_fts MATCH ?
            ) fts_matches
            CROSS JOIN symbols s
            WHERE s.id = fts_matches.match_id {where_clause}
            ORDER BY fts_matches.score DESC, LENGTH(s.name), s.name
            LIMIT ? OFFSET ?
        """
        rows = self.conn.execute(
            sql, [fts_query] + filter_params + [limit, offset]
        ).fetchall()

        # 移除内部排序字段
        items = []
        for r in rows:
            d = _row_to_dict(r)
            d.pop("_score", None)
            items.append(d)

        elapsed_ms = (time.perf_counter() - start) * 1000
        return {"total": total, "items": items, "search_time_ms": round(elapsed_ms, 2)}

    def find_class(
        self,
        name: str | None = None,
        module: str | None = None,
        parent_class: str | None = None,
        annotation: str | None = None,
        source_set: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        filters = ["kind IN ('class', 'interface', 'object')"]
        params: list[Any] = []

        if name:
            filters.append("name LIKE ?")
            params.append(f"%{name}%")
        if module:
            filters.append("module = ?")
            params.append(module)
        if parent_class:
            filters.append("parent_class LIKE ?")
            params.append(f"%{parent_class}%")
        if annotation:
            filters.append("annotations LIKE ?")
            params.append(f"%{annotation}%")
        if source_set:
            filters.append("source_set = ?")
            params.append(source_set)

        where = "WHERE " + " AND ".join(filters)

        # 计数
        count_sql = f"SELECT COUNT(*) FROM symbols {where}"
        total = self.conn.execute(count_sql, params).fetchone()[0]

        # 查询并排序：名称匹配度 + 类型权重
        sql = f"""
            SELECT *,
                CASE
                    WHEN name = ? THEN 0
                    WHEN name LIKE ? THEN 1
                    ELSE 2
                END AS _match_order
            FROM symbols {where}
            ORDER BY _match_order, LENGTH(name), name
            LIMIT ? OFFSET ?
        """
        order_params = [name, f"%{name}%"] if name else []
        rows = self.conn.execute(sql, params + order_params + [limit, offset]).fetchall()

        items = []
        for r in rows:
            d = _row_to_dict(r)
            d.pop("_match_order", None)
            items.append(d)

        return {"total": total, "items": items}

    def find_function(
        self,
        name: str | None = None,
        module: str | None = None,
        return_type: str | None = None,
        visibility: str | None = None,
        annotation: str | None = None,
        source_set: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        filters = ["kind = 'function'"]
        params: list[Any] = []

        if name:
            filters.append("name LIKE ?")
            params.append(f"%{name}%")
        if module:
            filters.append("module = ?")
            params.append(module)
        if return_type:
            filters.append("return_type LIKE ?")
            params.append(f"%{return_type}%")
        if visibility:
            filters.append("visibility = ?")
            params.append(visibility)
        if annotation:
            filters.append("annotations LIKE ?")
            params.append(f"%{annotation}%")
        if source_set:
            filters.append("source_set = ?")
            params.append(source_set)

        where = "WHERE " + " AND ".join(filters)

        # 计数
        count_sql = f"SELECT COUNT(*) FROM symbols {where}"
        total = self.conn.execute(count_sql, params).fetchone()[0]

        # 查询并排序
        sql = f"""
            SELECT *,
                CASE
                    WHEN name = ? THEN 0
                    WHEN name LIKE ? THEN 1
                    ELSE 2
                END AS _match_order
            FROM symbols {where}
            ORDER BY _match_order, LENGTH(name), name
            LIMIT ? OFFSET ?
        """
        order_params = [name, f"%{name}%"] if name else []
        rows = self.conn.execute(sql, params + order_params + [limit, offset]).fetchall()

        items = []
        for r in rows:
            d = _row_to_dict(r)
            d.pop("_match_order", None)
            items.append(d)

        return {"total": total, "items": items}

    def find_interface(
        self,
        name: str | None = None,
        module: str | None = None,
        source_set: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        filters = ["kind = 'interface'"]
        params: list[Any] = []

        if name:
            filters.append("name LIKE ?")
            params.append(f"%{name}%")
        if module:
            filters.append("module = ?")
            params.append(module)
        if source_set:
            filters.append("source_set = ?")
            params.append(source_set)

        where = "WHERE " + " AND ".join(filters)

        # 计数
        count_sql = f"SELECT COUNT(*) FROM symbols {where}"
        total = self.conn.execute(count_sql, params).fetchone()[0]

        # 查询并排序
        sql = f"""
            SELECT *,
                CASE
                    WHEN name = ? THEN 0
                    WHEN name LIKE ? THEN 1
                    ELSE 2
                END AS _match_order
            FROM symbols {where}
            ORDER BY _match_order, LENGTH(name), name
            LIMIT ? OFFSET ?
        """
        order_params = [name, f"%{name}%"] if name else []
        rows = self.conn.execute(sql, params + order_params + [limit, offset]).fetchall()

        items = []
        for r in rows:
            d = _row_to_dict(r)
            d.pop("_match_order", None)
            items.append(d)

        return {"total": total, "items": items}

    def get_file_symbols(self, file_path: str) -> list[dict]:
        """返回指定文件中的所有符号。file_path 必须为绝对路径。"""
        rows = self.conn.execute(
            "SELECT * FROM symbols WHERE file_path = ? ORDER BY line_number",
            (file_path,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]

    def get_module_overview(self, module: str) -> dict[str, Any]:
        """返回模块统计：sdk/impl 类数、接口数、函数数、文件数。"""
        def _count(kind: str, source_set: str | None = None) -> int:
            if source_set:
                r = self.conn.execute(
                    "SELECT COUNT(*) FROM symbols WHERE module=? AND kind=? AND source_set=?",
                    (module, kind, source_set),
                ).fetchone()
            else:
                r = self.conn.execute(
                    "SELECT COUNT(*) FROM symbols WHERE module=? AND kind=?",
                    (module, kind),
                ).fetchone()
            return r[0] if r else 0

        file_count = self.conn.execute(
            "SELECT COUNT(*) FROM files WHERE module=?", (module,)
        ).fetchone()

        return {
            "module": module,
            "sdk_classes": _count("class", "sdk"),
            "impl_classes": _count("class", "impl"),
            "interfaces": _count("interface"),
            "functions": _count("function"),
            "files": file_count[0] if file_count else 0,
        }

    # ──────────────────────────────────────────────
    # 批次 2 (P1) 方法
    # ──────────────────────────────────────────────

    def get_inheritance(self, class_name: str) -> list[str]:
        """
        返回 class_name 到根类的继承链（含自身）。

        遇到未知父类时终止，不抛异常。
        """
        chain = [class_name]
        visited: set[str] = {class_name}
        current = class_name

        while True:
            row = self.conn.execute(
                "SELECT parent_class FROM symbols WHERE name = ? AND kind IN ('class','interface')",
                (current,),
            ).fetchone()
            if not row or not row["parent_class"]:
                break
            parent = row["parent_class"]
            if parent in visited:
                break  # 防循环
            chain.append(parent)
            visited.add(parent)
            current = parent

        return chain

    def get_subclasses(
        self,
        class_name: str,
        direct_only: bool = False,
        limit: int = 50,
    ) -> list[dict]:
        """返回直接或所有子类列表。
        class_name 可以是简单名（FeedFragment）或全限定名（com.foo.FeedFragment），
        均取末段简单名做精确匹配。
        """
        simple = class_name.split(".")[-1]

        def _query(name: str) -> list:
            return self.conn.execute(
                "SELECT * FROM symbols WHERE parent_class = ? "
                "AND kind IN ('class','interface','object') LIMIT ?",
                (name, limit),
            ).fetchall()

        if direct_only:
            return [_row_to_dict(r) for r in _query(simple)]

        # BFS 查找所有子类
        result = []
        queue = [simple]
        visited: set[str] = set()

        while queue and len(result) < limit:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            for r in _query(current):
                d = _row_to_dict(r)
                result.append(d)
                queue.append(d["name"])

        return result[:limit]

    def get_implementations(
        self,
        interface_name: str,
        module: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """返回实现了指定接口的所有类。
        interface_name 可以是简单名或全限定名，均取末段做精确 JSON 元素匹配。
        """
        simple = interface_name.split(".")[-1]
        # interfaces 存为 JSON 数组，用 json_each 精确匹配元素
        filters = [
            "EXISTS (SELECT 1 FROM json_each(interfaces) WHERE value = ?)"
        ]
        params: list[Any] = [simple]

        if module:
            filters.append("module = ?")
            params.append(module)

        where = "WHERE " + " AND ".join(filters)
        sql = f"SELECT * FROM symbols {where} LIMIT ?"
        rows = self.conn.execute(sql, params + [limit]).fetchall()
        return [_row_to_dict(r) for r in rows]

    def get_class_api(
        self,
        class_name: str,
        include_private: bool = False,
    ) -> list[dict]:
        """返回类的公开（或全部）成员。"""
        filters = ["parent_class = ?"]
        params: list[Any] = [class_name]

        if not include_private:
            filters.append("visibility NOT IN ('private')")

        where = "WHERE " + " AND ".join(filters)
        sql = f"SELECT * FROM symbols {where} ORDER BY kind, name"
        rows = self.conn.execute(sql, params).fetchall()
        return [_row_to_dict(r) for r in rows]

    def find_layout(
        self,
        name: str | None = None,
        module: str | None = None,
        view_id: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        filters = ["kind IN ('layout', 'view_id')"]
        params: list[Any] = []

        if name:
            filters.append("name LIKE ?")
            params.append(f"%{name}%")
        if module:
            filters.append("module = ?")
            params.append(module)
        if view_id:
            filters.append("kind = 'view_id' AND name LIKE ?")
            params.append(f"%{view_id}%")

        where = "WHERE " + " AND ".join(filters)

        # 计数
        count_sql = f"SELECT COUNT(*) FROM symbols {where}"
        total = self.conn.execute(count_sql, params).fetchone()[0]

        # 查询
        sql = f"SELECT * FROM symbols {where} LIMIT ?"
        rows = self.conn.execute(sql, params + [limit]).fetchall()

        items = [_row_to_dict(r) for r in rows]
        return {"total": total, "items": items}

    def find_string(
        self,
        key: str | None = None,
        value: str | None = None,
        module: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        filters = ["kind = 'string_res'"]
        params: list[Any] = []

        if key:
            filters.append("name LIKE ?")
            params.append(f"%{key}%")
        if value:
            # 使用 idx_symbols_resource_value 索引
            filters.append("resource_value LIKE ?")
            params.append(f"%{value}%")
        if module:
            filters.append("module = ?")
            params.append(module)

        where = "WHERE " + " AND ".join(filters)

        # 计数
        count_sql = f"SELECT COUNT(*) FROM symbols {where}"
        total = self.conn.execute(count_sql, params).fetchone()[0]

        # 查询
        sql = f"SELECT * FROM symbols {where} LIMIT ?"
        rows = self.conn.execute(sql, params + [limit]).fetchall()

        items = [_row_to_dict(r) for r in rows]
        return {"total": total, "items": items}

    def find_manifest_component(
        self,
        name: str | None = None,
        component_type: str | None = None,
        module: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        filters = ["kind = 'manifest_component'"]
        params: list[Any] = []

        if name:
            filters.append("name LIKE ?")
            params.append(f"%{name}%")
        if component_type:
            # component_type 存在 annotations JSON 数组中，如 ["activity"]
            filters.append("annotations LIKE ?")
            params.append(f"%{component_type}%")
        if module:
            filters.append("module = ?")
            params.append(module)

        where = "WHERE " + " AND ".join(filters)

        # 计数
        count_sql = f"SELECT COUNT(*) FROM symbols {where}"
        total = self.conn.execute(count_sql, params).fetchone()[0]

        # 查询
        sql = f"SELECT * FROM symbols {where} LIMIT ?"
        rows = self.conn.execute(sql, params + [limit]).fetchall()

        items = [_row_to_dict(r) for r in rows]
        return {"total": total, "items": items}

    # ──────────────────────────────────────────────
    # 批次 3 (P2) 方法
    # ──────────────────────────────────────────────

    def find_module_deps(
        self,
        module: str,
        scope: str | None = None,
        syntax: str | None = None,
    ) -> dict[str, Any]:
        """
        查询模块的直接依赖和间接依赖。

        使用递归 CTE（SQLite >= 3.8.3）；版本过低时降级为 Python BFS。
        """
        filters = ["module = ?"]
        params: list[Any] = [module]

        if scope:
            filters.append("dependency_scope = ?")
            params.append(scope)
        if syntax:
            filters.append("syntax = ?")
            params.append(syntax)

        where = " AND ".join(filters)

        # 直接依赖
        direct_rows = self.conn.execute(
            f"SELECT * FROM module_dependencies WHERE {where}",
            params,
        ).fetchall()
        direct = [_row_to_dict(r) for r in direct_rows]

        # 间接依赖：尝试递归 CTE
        indirect: list[dict] = []
        try:
            cte_sql = f"""
                WITH RECURSIVE deps(depends_on, depth) AS (
                    SELECT depends_on, 1
                    FROM module_dependencies
                    WHERE {where}
                    UNION
                    SELECT md.depends_on, deps.depth + 1
                    FROM module_dependencies md
                    JOIN deps ON md.module = deps.depends_on
                    WHERE deps.depth < 10
                )
                SELECT DISTINCT depends_on, depth FROM deps
                ORDER BY depth
            """
            indirect_rows = self.conn.execute(cte_sql, params).fetchall()
            # 排除直接依赖
            direct_names = {r["depends_on"] for r in direct_rows}
            indirect = [
                {"depends_on": r["depends_on"], "depth": r["depth"]}
                for r in indirect_rows
                if r["depends_on"] not in direct_names
            ]
        except sqlite3.OperationalError:
            # 降级为 Python BFS + set
            visited: set[str] = {r["depends_on"] for r in direct_rows}
            queue = list(visited)
            depth = 2
            while queue and depth <= 10:
                next_queue = []
                for dep in queue:
                    rows = self.conn.execute(
                        "SELECT depends_on FROM module_dependencies WHERE module = ?",
                        (dep,),
                    ).fetchall()
                    for r in rows:
                        name = r["depends_on"]
                        if name not in visited:
                            visited.add(name)
                            next_queue.append(name)
                            indirect.append({"depends_on": name, "depth": depth})
                queue = next_queue
                depth += 1

        return {"direct": direct, "indirect": indirect}

    def find_style(
        self,
        name: str | None = None,
        module: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        filters = ["kind = 'style'"]
        params: list[Any] = []

        if name:
            filters.append("name LIKE ?")
            params.append(f"%{name}%")
        if module:
            filters.append("module = ?")
            params.append(module)

        where = "WHERE " + " AND ".join(filters)

        # 计数
        count_sql = f"SELECT COUNT(*) FROM symbols {where}"
        total = self.conn.execute(count_sql, params).fetchone()[0]

        # 查询
        sql = f"SELECT * FROM symbols {where} LIMIT ?"
        rows = self.conn.execute(sql, params + [limit]).fetchall()

        items = [_row_to_dict(r) for r in rows]
        return {"total": total, "items": items}

    def find_color(
        self,
        name: str | None = None,
        value: str | None = None,
        module: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        filters = ["kind = 'color_res'"]
        params: list[Any] = []

        if name:
            filters.append("name LIKE ?")
            params.append(f"%{name}%")
        if value:
            filters.append("resource_value LIKE ?")
            params.append(f"%{value}%")
        if module:
            filters.append("module = ?")
            params.append(module)

        where = "WHERE " + " AND ".join(filters)

        # 计数
        count_sql = f"SELECT COUNT(*) FROM symbols {where}"
        total = self.conn.execute(count_sql, params).fetchone()[0]

        # 查询
        sql = f"SELECT * FROM symbols {where} LIMIT ?"
        rows = self.conn.execute(sql, params + [limit]).fetchall()

        items = [_row_to_dict(r) for r in rows]
        return {"total": total, "items": items}

    # ──────────────────────────────────────────────
    # Vue UI 扩展方法 (Phase 0)
    # ──────────────────────────────────────────────

    def list_modules(self) -> list[dict]:
        """返回所有模块列表，含文件数/符号数/解析失败数，按 symbol_count 降序。"""
        sql = """
            SELECT
                module,
                COUNT(*) AS file_count,
                SUM(symbol_count) AS symbol_count,
                SUM(CASE WHEN parse_status = 'error' THEN 1 ELSE 0 END) AS parse_failures
            FROM files
            GROUP BY module
            ORDER BY symbol_count DESC
        """
        rows = self.conn.execute(sql).fetchall()
        return [dict(r) for r in rows]

    def stats_breakdown(self) -> dict[str, Any]:
        """返回按 kind / 语言 / 模块 分类的统计数据（供 Dashboard 图表使用）。"""
        by_kind: dict[str, int] = {}
        for row in self.conn.execute(
            "SELECT kind, COUNT(*) AS cnt FROM symbols GROUP BY kind"
        ).fetchall():
            by_kind[row["kind"]] = row["cnt"]

        by_language: dict[str, int] = {}
        for row in self.conn.execute(
            "SELECT file_type, COUNT(*) AS cnt FROM files GROUP BY file_type"
        ).fetchall():
            by_language[row["file_type"]] = row["cnt"]

        module_ranking = []
        for row in self.conn.execute(
            """
            SELECT module, SUM(symbol_count) AS symbol_count
            FROM files
            GROUP BY module
            ORDER BY symbol_count DESC
            LIMIT 10
            """
        ).fetchall():
            module_ranking.append({"module": row["module"], "symbol_count": row["symbol_count"]})

        return {
            "by_kind": by_kind,
            "by_language": by_language,
            "module_ranking": module_ranking,
        }

    def list_module_files(
        self, module: str, source_set: str | None = None
    ) -> list[dict]:
        """返回指定模块的文件列表，按目录分组。"""
        import os

        filters = ["module = ?"]
        params: list[Any] = [module]
        if source_set:
            filters.append("source_set = ?")
            params.append(source_set)

        where = "WHERE " + " AND ".join(filters)
        sql = f"""
            SELECT file_path, file_type, source_set, symbol_count
            FROM files
            {where}
            ORDER BY file_path
        """
        rows = self.conn.execute(sql, params).fetchall()

        # 按目录分组
        groups: dict[str, list[dict]] = {}
        for row in rows:
            d = dict(row)
            dir_path = os.path.dirname(d["file_path"])
            groups.setdefault(dir_path, []).append(d)

        return [
            {"dir_path": dir_path, "files": files}
            for dir_path, files in sorted(groups.items())
        ]

    def find_dimen(
        self,
        name: str | None = None,
        value: str | None = None,
        module: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        filters = ["kind = 'dimen_res'"]
        params: list[Any] = []

        if name:
            filters.append("name LIKE ?")
            params.append(f"%{name}%")
        if value:
            filters.append("resource_value LIKE ?")
            params.append(f"%{value}%")
        if module:
            filters.append("module = ?")
            params.append(module)

        where = "WHERE " + " AND ".join(filters)

        # 计数
        count_sql = f"SELECT COUNT(*) FROM symbols {where}"
        total = self.conn.execute(count_sql, params).fetchone()[0]

        # 查询
        sql = f"SELECT * FROM symbols {where} LIMIT ?"
        rows = self.conn.execute(sql, params + [limit]).fetchall()

        items = [_row_to_dict(r) for r in rows]
        return {"total": total, "items": items}

    def project_stats(self) -> dict[str, Any]:
        """返回整体项目统计信息。"""
        total_files = self.conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        total_symbols = self.conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
        modules = self.conn.execute("SELECT COUNT(DISTINCT module) FROM files").fetchone()[0]
        last_indexed_row = self.conn.execute(
            "SELECT MAX(indexed_at) FROM files"
        ).fetchone()
        last_indexed = last_indexed_row[0] if last_indexed_row else None
        if last_indexed:
            import datetime
            last_indexed = datetime.datetime.fromtimestamp(last_indexed).strftime("%Y-%m-%d %H:%M:%S")

        parse_failures = self.conn.execute(
            "SELECT COUNT(*) FROM files WHERE parse_status = 'error'"
        ).fetchone()[0]

        component_dep_count = self.conn.execute(
            "SELECT COUNT(*) FROM module_dependencies WHERE syntax = 'component'"
        ).fetchone()[0]
        project_dep_count = self.conn.execute(
            "SELECT COUNT(*) FROM module_dependencies WHERE syntax = 'project'"
        ).fetchone()[0]

        return {
            "total_files": total_files,
            "total_symbols": total_symbols,
            "modules": modules,
            "last_indexed": last_indexed,
            "parse_failures": parse_failures,
            "component_dep_count": component_dep_count,
            "project_dep_count": project_dep_count,
        }
