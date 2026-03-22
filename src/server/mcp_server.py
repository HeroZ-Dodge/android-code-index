"""MCP Server：通过 stdio transport 暴露 17 个查询工具，供 Claude Desktop 调用。"""

import json
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server

from src.query.query_engine import QueryEngine

_engine: QueryEngine | None = None


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
            name="search",
            description="全文搜索所有符号（类、函数、资源等）。keyword 为搜索关键词，kind/module 可选过滤。",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string"},
                    "kind": {"type": "string"},
                    "module": {"type": "string"},
                    "limit": {"type": "integer", "default": 20},
                    "offset": {"type": "integer", "default": 0},
                },
                "required": ["keyword"],
            },
        ),
        types.Tool(
            name="find_class",
            description="查找类、data class、sealed class、object、enum。支持按名称、模块、父类、注解过滤。",
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
            name="find_function",
            description="查找函数/方法。支持按名称、模块、返回类型、可见性、注解过滤。",
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
            name="find_interface",
            description="查找接口定义。支持按名称、模块过滤。",
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
            description="返回指定文件的所有符号列表。file_path 必须是绝对路径。",
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
            description="返回模块的统计概览：SDK 类数、impl 类数、接口数、函数数、文件数。",
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
            description="返回指定类从自身到根类的继承链。遇到未知父类时自动终止。",
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
            description="返回指定类的直接子类或所有子类。direct_only=true 时只返回直接子类。",
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
            description="返回实现了指定接口的所有类。",
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
            description="返回类的所有成员（方法、属性）。include_private=true 时包含私有成员。",
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
            name="find_layout",
            description="查找布局文件和 View ID。可按布局名称、模块、view_id 过滤。",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "module": {"type": "string"},
                    "view_id": {"type": "string"},
                    "limit": {"type": "integer", "default": 20},
                },
            },
        ),
        types.Tool(
            name="find_string",
            description="查找字符串资源。key 按 name 匹配，value 按字符串内容模糊匹配。",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "value": {"type": "string"},
                    "module": {"type": "string"},
                    "limit": {"type": "integer", "default": 20},
                },
            },
        ),
        types.Tool(
            name="find_manifest_component",
            description="查找 AndroidManifest.xml 中注册的组件（activity/service/receiver/provider）。",
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
                "查询模块的直接和间接依赖关系。"
                "syntax 可选 component（SDK 依赖）、project（全模块依赖）。"
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
            description="查找样式资源（styles.xml 中的 style 定义）。",
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
            name="find_color",
            description="查找颜色资源（colors.xml）。可按名称或颜色值（如 #FF0000）过滤。",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "value": {"type": "string"},
                    "module": {"type": "string"},
                    "limit": {"type": "integer", "default": 20},
                },
            },
        ),
        types.Tool(
            name="project_stats",
            description="返回当前数据库的整体统计信息：文件数、符号数、模块数、依赖数等。",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def call_tool(
    name: str, arguments: dict[str, Any]
) -> list[types.TextContent]:
    engine = _get_engine()
    result: Any

    if name == "search":
        result = engine.search(**arguments)
    elif name == "find_class":
        result = engine.find_class(**arguments)
    elif name == "find_function":
        result = engine.find_function(**arguments)
    elif name == "find_interface":
        result = engine.find_interface(**arguments)
    elif name == "get_file_symbols":
        result = engine.get_file_symbols(**arguments)
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
    elif name == "find_layout":
        result = engine.find_layout(**arguments)
    elif name == "find_string":
        result = engine.find_string(**arguments)
    elif name == "find_manifest_component":
        result = engine.find_manifest_component(**arguments)
    elif name == "find_module_deps":
        result = engine.find_module_deps(**arguments)
    elif name == "find_style":
        result = engine.find_style(**arguments)
    elif name == "find_color":
        result = engine.find_color(**arguments)
    elif name == "project_stats":
        result = engine.project_stats()
    else:
        result = {"error": f"未知工具: {name}"}

    return [types.TextContent(type="text", text=_json(result))]


def run_mcp_server() -> None:
    """以 stdio transport 启动 MCP Server（供 main.py 调用）。"""
    import asyncio

    async def _run() -> None:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    asyncio.run(_run())
