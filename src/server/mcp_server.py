"""MCP Server：通过 stdio transport 暴露查询工具，供 Claude Code 调用。"""

import json
from pathlib import Path
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server

from src.query.query_engine import QueryEngine

_engine: QueryEngine | None = None
_project_name: str = "unknown"


def _get_engine() -> QueryEngine:
    global _engine
    if _engine is None:
        _engine = QueryEngine()
    return _engine


def _json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, default=str)


# ──────────────────────────────────────────────
# 创建 MCP Server
# ──────────────────────────────────────────────

server = Server("android-code-index")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        # 批次 1
        types.Tool(
            name="search_code",
            description=(
                "全文搜索源码符号（class/interface/object/function/property/constructor）。"
                "keyword 支持驼峰分词（如 'FeedFrag' 可匹配 'FeedFragment'）和多词（如 'base fragment'）。"
                "kind 可选：class | interface | object | function | property | constructor。"
                "module 格式如 ':compfeed'（带冒号前缀）。"
                "use_tokens=false 时仅按名称前缀匹配，不启用驼峰分词。"
                "返回格式：{total, items: [...], search_time_ms}"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string"},
                    "kind": {"type": "string"},
                    "module": {"type": "string"},
                    "use_tokens": {"type": "boolean", "default": True},
                    "limit": {"type": "integer", "default": 20},
                    "offset": {"type": "integer", "default": 0},
                },
                "required": ["keyword"],
            },
        ),
        types.Tool(
            name="search_resource",
            description=(
                "全文搜索资源符号（layout/style/manifest_component/drawable）。"
                "keyword 支持分词匹配。"
                "kind 可选：layout | style | manifest_component | drawable。"
                "module 格式如 ':compfeed'。"
                "返回格式：{total, items: [...], search_time_ms}"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string"},
                    "kind": {"type": "string"},
                    "module": {"type": "string"},
                    "use_tokens": {"type": "boolean", "default": True},
                    "limit": {"type": "integer", "default": 20},
                    "offset": {"type": "integer", "default": 0},
                },
                "required": ["keyword"],
            },
        ),
        types.Tool(
            name="search_class",
            description=(
                "按条件过滤查找类（class/object）。所有参数均可选，全不传时返回所有类。"
                "name 支持前缀模糊匹配。"
                "parent_class 支持部分匹配（如 'BaseFragment'）。"
                "annotation 支持部分匹配（如 'HiltViewModel'）。"
                "source_set 可选：sdk | impl。"
                "module 格式如 ':compfeed'。"
                "返回格式：{total, items: [...]}"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "module": {"type": "string"},
                    "parent_class": {"type": "string"},
                    "annotation": {"type": "string"},
                    "source_set": {"type": "string"},
                    "limit": {"type": "integer", "default": 20},
                    "offset": {"type": "integer", "default": 0},
                },
            },
        ),
        types.Tool(
            name="search_function",
            description=(
                "按条件过滤查找函数/方法。所有参数均可选。"
                "name 支持前缀模糊匹配。"
                "return_type 支持部分匹配（如 'Boolean'）。"
                "visibility 可选：public | private | protected | internal | package。"
                "annotation 支持部分匹配（如 'Override'）。"
                "source_set 可选：sdk | impl。"
                "module 格式如 ':compfeed'。"
                "返回格式：{total, items: [...]}"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "module": {"type": "string"},
                    "return_type": {"type": "string"},
                    "visibility": {"type": "string"},
                    "annotation": {"type": "string"},
                    "source_set": {"type": "string"},
                    "limit": {"type": "integer", "default": 20},
                    "offset": {"type": "integer", "default": 0},
                },
            },
        ),
        types.Tool(
            name="search_interface",
            description=(
                "按条件过滤查找接口定义。所有参数均可选。"
                "name 支持前缀模糊匹配。"
                "source_set 可选：sdk | impl。"
                "module 格式如 ':compfeed'。"
                "返回格式：{total, items: [...]}"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "module": {"type": "string"},
                    "source_set": {"type": "string"},
                    "limit": {"type": "integer", "default": 20},
                    "offset": {"type": "integer", "default": 0},
                },
            },
        ),
        types.Tool(
            name="get_file_symbols",
            description=(
                "返回指定文件的所有符号列表，按行号排序。"
                "file_path 为项目根目录下的相对路径，有无开头 / 均可，"
                "如 '/compfeed/src/main/java/com/example/Foo.kt' 或 "
                "'compfeed/src/main/java/com/example/Foo.kt'。"
                "路径可从其他接口返回的 file_path 字段直接获取。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                },
                "required": ["file_path"],
            },
        ),
        types.Tool(
            name="get_file_imports",
            description=(
                "返回指定文件的所有 import 全限定名列表，用于理解该文件的依赖上下文。"
                "file_path 为项目根目录下的相对路径，有无开头 / 均可，"
                "如 '/compfeed/src/main/java/com/example/Foo.kt' 或 "
                "'compfeed/src/main/java/com/example/Foo.kt'。"
                "路径可从其他接口返回的 file_path 字段直接获取。"
                "返回格式：[\"com.example.Foo\", ...]"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                },
                "required": ["file_path"],
            },
        ),
        types.Tool(
            name="get_module_overview",
            description=(
                "返回指定模块的统计概览：SDK 类数、impl 类数、接口数、函数数、文件数。"
                "module 格式为带冒号前缀的模块名，如 ':compfeed'、':service-im'。"
                "可先通过 project_stats 或 search_code 结果中的 module 字段获取模块名。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "module": {"type": "string"},
                },
                "required": ["module"],
            },
        ),
        # 批次 2
        types.Tool(
            name="get_inheritance",
            description=(
                "返回指定类从自身到根类的完整继承链（含自身），遇到未索引的父类时自动终止。"
                "class_name 优先精确匹配 qualified_name（如 'com.example.FeedFragment'），"
                "其次匹配 name（如 'FeedFragment'）。"
                "若 name 存在多个同名类，返回 {error: 'ambiguous', candidates: [{id, qualified_name, module}]}，"
                "此时应从 candidates 中选取正确的 qualified_name 重新调用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {"type": "string"},
                },
                "required": ["class_name"],
            },
        ),
        types.Tool(
            name="get_subclasses",
            description=(
                "返回指定类的子类列表。direct_only=true 时只返回直接子类，默认返回所有层级子类（BFS）。"
                "class_name 优先精确匹配 qualified_name，其次匹配 name。"
                "若 name 存在歧义，返回 {error: 'ambiguous', candidates: [...]}。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {"type": "string"},
                    "direct_only": {"type": "boolean", "default": False},
                    "limit": {"type": "integer", "default": 50},
                },
                "required": ["class_name"],
            },
        ),
        types.Tool(
            name="get_implementations",
            description=(
                "返回实现了指定接口的所有类。"
                "interface_name 优先精确匹配 qualified_name，其次匹配 name。"
                "若 name 存在歧义，返回 {error: 'ambiguous', candidates: [...]}。"
                "可用 module 参数限定查找范围。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "interface_name": {"type": "string"},
                    "module": {"type": "string"},
                    "limit": {"type": "integer", "default": 50},
                },
                "required": ["interface_name"],
            },
        ),
        types.Tool(
            name="get_class_api",
            description=(
                "返回类的成员摘要列表（精简版，不含源码）。"
                "每个成员只包含 id、name、kind、visibility、return_type、"
                "parameters、signature、annotations、line_number 等核心字段，过滤掉 null 值。"
                "token 消耗约为完整版的 1/10，推荐优先使用此接口。"
                "include_private 默认 false，只返回非 private 成员（public/protected/internal）；"
                "若需要查看字段（field/property）通常需要传 include_private=true，因为字段多为 private。"
                "class_name 优先精确匹配 qualified_name，其次匹配 name。"
                "若 name 存在歧义，返回 {error: 'ambiguous', candidates: [...]}，应取 qualified_name 重新调用。"
                "需要查看某个方法/构造器的完整源码，请用 get_symbol_source(symbol_id)。"
                "需要完整成员数据（含 src_code）请用 get_class_api_full。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {"type": "string"},
                    "include_private": {"type": "boolean", "default": False},
                },
                "required": ["class_name"],
            },
        ),
        types.Tool(
            name="get_class_api_full",
            description=(
                "返回类的完整成员列表（含每个 function/constructor 的 src_code）"
                "以及该文件所有 import 的全限定名。"
                "适合需要深入分析整个类实现的场景，token 消耗较高。"
                "include_private 默认 false，只返回非 private 成员；"
                "需要查看 private 字段时传 include_private=true。"
                "class_name 优先精确匹配 qualified_name，其次匹配 name。"
                "若 name 存在歧义，返回 {error: 'ambiguous', candidates: [...]}。"
                "返回格式：{members: [...], file_imports: ['com.example.Foo', ...]}"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {"type": "string"},
                    "include_private": {"type": "boolean", "default": False},
                },
                "required": ["class_name"],
            },
        ),
        types.Tool(
            name="get_symbol_source",
            description=(
                "按符号 id 返回单个 function 或 constructor 的完整源码。"
                "推荐用法：先调用 get_class_api 获取成员摘要列表拿到目标方法的 id，"
                "再按需调用此接口获取源码，避免一次性加载所有成员源码。"
                "若符号不存在或该符号类型无源码（如 property），返回 null。"
                "返回格式：{id, name, kind, file_path, line_number, src_code}"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol_id": {"type": "integer"},
                },
                "required": ["symbol_id"],
            },
        ),
        types.Tool(
            name="find_layout",
            description=(
                "查找布局资源文件（res/layout 目录下的 XML）。"
                "name 支持部分匹配（如 'fragment_feed' 可匹配 'fragment_feed_list'）。"
                "module 格式如 ':compfeed'。"
                "返回格式：{total, items: [...]}"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "module": {"type": "string"},
                    "limit": {"type": "integer", "default": 20},
                },
            },
        ),
        types.Tool(
            name="find_drawable",
            description=(
                "查找 drawable 资源（shape/selector/vector/layer-list 等 XML 及图片资源）。"
                "name 支持部分匹配。"
                "module 格式如 ':compfeed'。"
                "返回格式：{total, items: [...]}"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "module": {"type": "string"},
                    "limit": {"type": "integer", "default": 50},
                },
            },
        ),
        types.Tool(
            name="find_manifest_component",
            description=(
                "查找 AndroidManifest.xml 中注册的四大组件。"
                "name 支持部分匹配（如 'FeedActivity'）。"
                "component_type 可选：activity | service | receiver | provider。"
                "module 格式如 ':compfeed'。"
                "返回格式：{total, items: [...]}"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "component_type": {"type": "string"},
                    "module": {"type": "string"},
                    "limit": {"type": "integer", "default": 20},
                },
            },
        ),
        # 批次 3
        types.Tool(
            name="find_module_deps",
            description=(
                "查询模块的直接依赖和间接依赖（递归，最深 10 层）。"
                "module 格式如 ':compfeed'。"
                "scope 可选：api | implementation | compileOnly | runtimeOnly 等 Gradle 依赖配置名。"
                "syntax 可选：component（SDK 组件依赖）| project（本地模块依赖）。"
                "返回格式：{direct: [...], indirect: [{depends_on, depth}]}"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "module": {"type": "string"},
                    "scope": {"type": "string"},
                    "syntax": {"type": "string"},
                },
                "required": ["module"],
            },
        ),
        types.Tool(
            name="find_style",
            description=(
                "查找样式资源（res/values/styles.xml 中的 style 定义）。"
                "name 支持部分匹配（如 'AppTheme'）。"
                "module 格式如 ':compfeed'。"
                "返回格式：{total, items: [...]}"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "module": {"type": "string"},
                    "limit": {"type": "integer", "default": 20},
                },
            },
        ),
        types.Tool(
            name="project_stats",
            description=(
                "返回整个索引库的统计概览：总文件数、总符号数、模块数、"
                "最后索引时间、解析失败数、组件依赖数、模块依赖数。"
                "无需参数，适合在开始分析前先了解项目规模。"
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="update_index",
            description=(
                "对当前项目执行增量索引更新：只重新解析新增或修改过的文件，删除已消失文件的记录。"
                "project_path 为 Android 项目的绝对路径，如 '/Users/foo/xxx.android'。"
                "当你发现代码与索引不一致，或用户告知刚修改了文件时，主动调用此工具更新索引。"
                "返回格式：{updated_files, deleted_files, failures, elapsed_seconds}"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string"},
                },
                "required": ["project_path"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(
    name: str, arguments: dict[str, Any]
) -> list[types.TextContent]:
    engine = _get_engine()
    result: Any

    if name == "search_code":
        result = engine.search_code(**arguments)
    elif name == "search_resource":
        result = engine.search_resource(**arguments)
    elif name == "search_class":
        result = engine.search_class(**arguments)
    elif name == "search_function":
        result = engine.search_function(**arguments)
    elif name == "search_interface":
        result = engine.search_interface(**arguments)
    elif name == "get_file_symbols":
        result = engine.get_file_symbols(**arguments)
    elif name == "get_file_imports":
        result = engine.get_file_imports(**arguments)
    elif name == "get_module_overview":
        result = engine.get_module_overview(**arguments)
    elif name == "get_inheritance":
        result = engine.get_inheritance(**arguments)
    elif name == "get_subclasses":
        result = engine.get_subclasses(**arguments)
    elif name == "get_implementations":
        result = engine.get_implementations(**arguments)
    elif name == "get_class_api":
        result = engine.get_class_api(**arguments)
    elif name == "get_class_api_full":
        result = engine.get_class_api_full(**arguments)
    elif name == "get_symbol_source":
        result = engine.get_symbol_source(**arguments)
    elif name == "find_layout":
        result = engine.find_layout(**arguments)
    elif name == "find_drawable":
        result = engine.find_drawable(**arguments)
    elif name == "find_manifest_component":
        result = engine.find_manifest_component(**arguments)
    elif name == "find_module_deps":
        result = engine.find_module_deps(**arguments)
    elif name == "find_style":
        result = engine.find_style(**arguments)
    elif name == "project_stats":
        result = engine.project_stats()
    elif name == "update_index":
        import time as _time
        from pathlib import Path as _Path
        from src.indexer import Indexer
        project_path = _Path(arguments["project_path"])
        t0 = _time.perf_counter()
        # 使用与当前 MCP 绑定的同一 DB
        indexer = Indexer(db_path=_get_engine().db_path)
        stats_before = _get_engine().project_stats()
        indexer.index_update(project_path)
        # 重新加载 engine（让新索引立即生效）
        global _engine
        _engine = QueryEngine(db_path=indexer.db_path)
        stats_after = _engine.project_stats()
        elapsed = round(_time.perf_counter() - t0, 2)
        result = {
            "status": "ok",
            "elapsed_seconds": elapsed,
            "symbols_before": stats_before["total_symbols"],
            "symbols_after": stats_after["total_symbols"],
            "files_after": stats_after["total_files"],
        }
    else:
        result = {"error": f"未知工具: {name}"}

    return [types.TextContent(type="text", text=_json(result))]


def run_mcp_server(
    db_path: Path | None = None,
    project_name: str = "unknown",
    watch_root: Path | None = None,
    debounce_seconds: float = 3.0,
) -> None:
    """以 stdio transport 启动 MCP Server（供 main.py 调用）。

    db_path          → 指定要加载的数据库路径（由 --project 参数推导而来）
    project_name     → 项目名称，用于日志和工具描述
    watch_root       → 若不为 None，则在后台启动 ProjectWatcher 自动更新索引
    debounce_seconds → 文件监听的 debounce 秒数
    """
    global _engine, _project_name
    if db_path:
        _engine = QueryEngine(db_path=db_path)
        _project_name = project_name

    # 后台文件监听
    _watcher = None
    if watch_root is not None:
        import logging
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
        from src.indexer import Indexer
        from src.watcher import ProjectWatcher

        _indexer = Indexer(db_path=db_path)

        def _reload_engine() -> None:
            global _engine
            _engine = QueryEngine(db_path=db_path)

        _watcher = ProjectWatcher(
            project_root=watch_root,
            indexer=_indexer,
            debounce_seconds=debounce_seconds,
            on_updated=_reload_engine,
            verbose=True,
        )
        _watcher.start()

    import asyncio

    async def _run() -> None:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    try:
        asyncio.run(_run())
    finally:
        if _watcher is not None:
            _watcher.stop()
