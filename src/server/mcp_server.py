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
    # ── 使用规则 ──────────────────────────────────────────────────────────────
    # 本 MCP 是 Android 项目代码符号索引，与 read/grep 互补而非替代：
    #
    # 优先用 MCP 的场景：
    #   • 已知类名/方法名，需要快速定位 → search_code / search_class / search_function 等
    #   • 需要分析继承、接口、子类等跨文件关系 → get_inheritance / get_subclasses / get_class_interfaces
    #   • 需要查看类的公开 API 摘要（方法签名、返回值）→ get_class_api
    #   • 不知道文件路径，只知道符号名 → search_code 先拿 qualified_name、file_path
    #
    # 继续用 read/grep 的场景：
    #   • 读取配置文件、build.gradle、XML 布局内容
    #   • 需要深度分析代码逻辑时
    #   • 需要看方法的上下文（前后几十行）→ 用 get_symbol_source 拿到 file_path+line_number 再 read
    #   • 符号未被索引（第三方库、生成代码）
    #
    # 核心工作流（减少 token 消耗）：
    #   1. search_code / search_class → 拿到 qualified_name
    #   2. get_class_api(qualified_name) → 查看成员摘要，找到目标方法的 id
    #   3. get_symbol_source(id) → 按需获取单个方法源码
    #   避免在不确定目标前就调用 get_class_api_full（token 消耗高 ~10x）
    #
    # class_name / interface_name 参数解析规则（所有 get_xxx 均适用）：
    #   优先传 qualified_name（如 'com.example.feed.FeedFragment'），精确无歧义；
    #   若只知道简单名（如 'FeedFragment'），当项目中只有一个同名类时可以直接传；
    #   若返回 {error: 'ambiguous', candidates: [...]}, 说明存在同名类，
    #   应从 candidates 中选出正确的 qualified_name 重新调用，不要再传简单名重试。
    # ─────────────────────────────────────────────────────────────────────────
    return [
        # ── 搜索 ─────────────────────────────────────────────────────────────
        types.Tool(
            name="search_class",
            description=(
                "按条件结构化查找 class / object，适合已知父类、注解等元数据的精准过滤场景。"
                "与 search_code 的区别：search_code 是关键词全文搜索，此工具是字段过滤查询。\n"
                "\n"
                "参数语义：\n"
                "  name        → FTS 前缀匹配（同 search_code 的 use_tokens=false 模式）\n"
                "  parent_class→ LIKE '%value%' 部分匹配，如 'BaseFragment' 可匹配含此字符串的父类\n"
                "  annotation  → LIKE '%value%' 部分匹配，如 'HiltViewModel'\n"
                "  module      → 精确匹配，格式如 'compfeed'\n"
                "  source_set  → 精确匹配：sdk（对外接口层）| impl（实现层）\n"
                "\n"
                "所有参数均可选，全不传时返回全部 class/object（建议同时传 module 或 limit）。\n"
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
                "按条件结构化查找函数/方法，适合按返回值、注解、可见性等元数据过滤的场景。\n"
                "\n"
                "参数语义：\n"
                "  name       → FTS 前缀匹配\n"
                "  return_type→ LIKE '%value%' 部分匹配，如 'LiveData' 匹配所有返回 LiveData 的方法\n"
                "  visibility → 精确匹配：public | private | protected | internal | package\n"
                "  annotation → LIKE '%value%' 部分匹配，如 'Override'、'GET'\n"
                "  module     → 精确匹配，格式如 'compfeed'\n"
                "  source_set → 精确匹配：sdk | impl\n"
                "\n"
                "注意：此工具只搜索顶层/成员 function，不含 constructor；"
                "搜索构造器请用 search_code(kind='constructor')。\n"
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
                "按条件结构化查找接口定义（kind=interface）。\n"
                "\n"
                "参数语义：\n"
                "  name      → FTS 前缀匹配\n"
                "  module    → 精确匹配，格式如 'service-feed'\n"
                "  source_set→ 精确匹配：sdk | impl\n"
                "\n"
                "查找接口的实现类请用 get_implementations。\n"
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
            name="search_code",
            description=(
                "【入口工具】全文搜索源码符号，返回 qualified_name / file_path / module 等定位信息。"
                "搜索范围：class | interface | object | function | property（kind 不传时搜全部）。"
                "\n"
                "use_tokens（默认 true）控制搜索模式：\n"
                "  true  → 每个词同时匹配「name 前缀」和「驼峰拆分词」，\n"
                "          例：'FeedFrag' 匹配 FeedFragment；'feed frag' 同时含 feed 和 frag 的符号；\n"
                "          'feed' 可匹配 FeedFragment（因其 name_tokens='feed fragment'）。\n"
                "  false → 仅匹配 name 前缀，等同于 SQL LIKE 'keyword%'，结果更精确但不支持驼峰。\n"
                "          已知精确名称时传 false，避免驼峰分词引入干扰结果。\n"
                "\n"
                "keyword 语法：\n"
                "  前缀搜索：FeedFrag（匹配所有以 FeedFrag 开头或 name_tokens 含 feedfrag 的符号）\n"
                "  多词 AND：'Base Fragment'（同时包含 Base 和 Fragment 的符号）\n"
                "  精确匹配：'\"FeedFragment\"'（name 或 name_tokens 完全等于 FeedFragment）\n"
                "\n"
                "module 为精确匹配，格式如 'compfeed'。\n"
                "返回格式：{total, items: [{id, name, qualified_name, kind, module, file_path, "
                "line_number, visibility, parent_class, interfaces, ...}], search_time_ms}"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string"},
                    "kind": {
                        "type": "string",
                        "description": "可选过滤：class | interface | object | function | property",
                    },
                    "module": {
                        "type": "string",
                        "description": "精确匹配模块名，格式如 'compfeed'",
                    },
                    "use_tokens": {
                        "type": "boolean",
                        "default": True,
                        "description": "true=驼峰分词搜索（默认）；false=仅 name 前缀匹配",
                    },
                    "limit": {"type": "integer", "default": 20},
                    "offset": {"type": "integer", "default": 0},
                },
                "required": ["keyword"],
            },
        ),
        types.Tool(
            name="search_resource",
            description=(
                "全文搜索 Android 资源符号（layout / style / drawable / manifest_component）。"
                "kind 不传时搜索所有资源类型。"
                "use_tokens 含义同 search_code：true 启用驼峰分词，false 仅 name 前缀匹配。"
                "module 为精确匹配，格式如 'compfeed'。"
                "返回格式：{total, items: [...], search_time_ms}"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string"},
                    "kind": {
                        "type": "string",
                        "description": "可选过滤：layout | style | drawable | manifest_component",
                    },
                    "module": {"type": "string"},
                    "use_tokens": {"type": "boolean", "default": True},
                    "limit": {"type": "integer", "default": 20},
                    "offset": {"type": "integer", "default": 0},
                },
                "required": ["keyword"],
            },
        ),
        # ── 文件级查询 ────────────────────────────────────────────────────────
        types.Tool(
            name="get_file_symbols",
            description=(
                "返回指定文件内所有符号，按行号升序排列。"
                "适合已知文件路径时快速了解文件结构（类/方法/属性列表），"
                "对比直接 read 整个文件，没有节省 token的优势，因为会返回方法的源码。\n"
                "\n"
                "file_path 为项目根目录下的相对路径，有无开头 / 均可（自动补全）。"
                "路径来源：search_code / search_class 等结果中的 file_path 字段。\n"
                "示例：'/compfeed/src/main/java/com/example/FeedFragment.kt'\n"
                "返回格式：[{id, name, kind, line_number, visibility, ...}, ...]"
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
                "返回指定文件所有 import 语句的全限定名列表。"
                "适合判断该文件依赖了哪些外部类/接口，"
                "辅助理解类的依赖上下文，比 read 文件后手动筛选 import 更高效。\n"
                "\n"
                "file_path 同 get_file_symbols，路径可从其他工具结果的 file_path 字段获取。\n"
                "返回格式：['com.example.Foo', 'android.os.Bundle', ...]"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                },
                "required": ["file_path"],
            },
        ),
        # ── 模块 ─────────────────────────────────────────────────────────────
        types.Tool(
            name="get_module_overview",
            description=(
                "返回指定模块的统计概览：sdk_classes、impl_classes、interfaces、functions、files 数量。"
                "适合快速了解一个模块的规模和代码分层情况（sdk/impl 分离）。"
                "module 格式为模块名，如 'compfeed'、'service-im'；"
                "可从 search_code 结果的 module 字段或 project_stats 获取模块名列表。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "module": {"type": "string"},
                },
                "required": ["module"],
            },
        ),
        # ── 类关系分析 ────────────────────────────────────────────────────────
        types.Tool(
            name="get_inheritance",
            description=(
                "返回指定类从自身到根类的完整继承链（含自身），以 qualified_name 字符串列表表示。"
                "链中父类若未被索引（如 Android SDK 基类），仍会加入列表但不再继续向上追溯。\n"
                "\n"
                "class_name 解析规则：\n"
                "  1. 优先精确匹配 qualified_name（推荐），如 'com.example.FeedFragment'\n"
                "  2. 其次精确匹配 name，项目中唯一时自动解析\n"
                "  3. 若存在多个同名类，返回 {error: 'ambiguous', candidates: [{id, qualified_name, module}]}\n"
                "     → 从 candidates 取正确 qualified_name 重新调用\n"
                "\n"
                "返回格式：['com.example.FeedFragment', 'com.example.BaseFragment', 'androidx.fragment.app.Fragment', ...]"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "优先传 qualified_name，其次传简单类名",
                    },
                },
                "required": ["class_name"],
            },
        ),
        types.Tool(
            name="get_subclasses",
            description=(
                "返回指定类的子类列表。\n"
                "  direct_only=false（默认）→ BFS 遍历所有层级子类，受 limit 限制\n"
                "  direct_only=true → 只返回直接子类（parent_class 字段精确等于目标类 qualified_name）\n"
                "\n"
                "class_name 解析规则同 get_inheritance（优先 qualified_name，歧义时返回 candidates）。\n"
                "返回格式：[{id, name, qualified_name, module, file_path, ...}, ...]"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "优先传 qualified_name，其次传简单类名",
                    },
                    "direct_only": {"type": "boolean", "default": False},
                    "limit": {"type": "integer", "default": 50},
                },
                "required": ["class_name"],
            },
        ),
        types.Tool(
            name="get_class_interfaces",
            description=(
                "返回指定类（含所有祖先类）实现的全部接口，沿继承链逐层汇总去重。\n"
                "\n"
                "使用场景：当一个类本身 interfaces 字段为空，但其父类实现了接口时，"
                "用此工具可以获取完整的接口实现集合，避免只看子类信息而遗漏继承来的接口。\n"
                "\n"
                "class_name 解析规则同 get_inheritance（优先 qualified_name，歧义时返回 candidates）。\n"
                "返回格式：{\n"
                "  all_interfaces: ['Parcelable', 'IFoo'],   // 汇总去重的全部接口\n"
                "  per_class: [                               // 按继承层级拆分的来源\n"
                "    {class: 'FavoFeedEntity', qualified_name: '...', interfaces: []},\n"
                "    {class: 'FeedEntity', qualified_name: '...', interfaces: ['Parcelable']}\n"
                "  ]\n"
                "}"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "优先传 qualified_name，其次传简单类名",
                    },
                },
                "required": ["class_name"],
            },
        ),
        types.Tool(
            name="get_implementations",
            description=(
                "返回实现了指定接口的所有类。\n"
                "\n"
                "匹配逻辑：在各类的 interfaces JSON 数组中，同时用接口的 qualified_name 和简单名"
                "（取最后一个 '.' 之后的部分）进行匹配，因此部分代码中用简单名声明接口的也能被命中。\n"
                "\n"
                "interface_name 解析规则同 get_inheritance（优先 qualified_name，歧义时返回 candidates）。\n"
                "module 为精确匹配，可用于限定查找范围，减少跨模块干扰。\n"
                "返回格式：[{id, name, qualified_name, module, file_path, interfaces, ...}, ...]"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "interface_name": {
                        "type": "string",
                        "description": "优先传 qualified_name，其次传简单接口名",
                    },
                    "module": {"type": "string"},
                    "limit": {"type": "integer", "default": 50},
                },
                "required": ["interface_name"],
            },
        ),
        # ── 类成员查询（分层按需加载）────────────────────────────────────────
        types.Tool(
            name="get_class_api",
            description=(
                "【推荐】返回类的成员摘要列表（不含源码），token 消耗约为 get_class_api_full 的 1/10。\n"
                "\n"
                "返回字段：id、name、kind、visibility、is_abstract、is_override、"
                "return_type、parameters、signature、annotations、line_number（null 值自动过滤）。\n"
                "\n"
                "include_private（默认 false）：\n"
                "  false → 只返回 public / protected / internal 成员\n"
                "  true  → 包含 private 成员；类的属性/字段通常是 private，需要查看时传 true\n"
                "\n"
                "推荐工作流（最小化 token）：\n"
                "  1. get_class_api → 查看方法列表，定位目标方法，记下其 id\n"
                "  2. get_symbol_source(id) → 按需获取单个方法源码\n"
                "  仅在需要同时分析多个方法实现时才使用 get_class_api_full\n"
                "\n"
                "class_name 解析规则同 get_inheritance（优先 qualified_name，歧义时返回 candidates）。\n"
                "注意：此接口返回的是该类自身定义的成员，不包含继承来的方法。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "优先传 qualified_name，其次传简单类名",
                    },
                    "include_private": {"type": "boolean", "default": False},
                },
                "required": ["class_name"],
            },
        ),
        types.Tool(
            name="get_class_api_full",
            description=(
                "返回类的完整成员列表（含每个 function/constructor 的 src_code）"
                "以及该文件所有 import 全限定名。\n"
                "\n"
                "⚠️ token 消耗高，约为 get_class_api 的 10 倍。\n"
                "仅在以下场景使用：\n"
                "  • 需要同时分析该类多个方法的源码实现\n"
                "  • 需要同时拿到成员列表和 import 依赖做综合分析\n"
                "  单个方法源码请用 get_class_api + get_symbol_source(id) 组合\n"
                "\n"
                "include_private 同 get_class_api。\n"
                "class_name 解析规则同 get_inheritance（优先 qualified_name，歧义时返回 candidates）。\n"
                "返回格式：{members: [{...全字段含 src_code...}], file_imports: ['com.example.Foo', ...]}"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "优先传 qualified_name，其次传简单类名",
                    },
                    "include_private": {"type": "boolean", "default": False},
                },
                "required": ["class_name"],
            },
        ),
        types.Tool(
            name="get_symbol_source",
            description=(
                "按符号 id 获取单个 function 或 constructor 的完整源码。\n"
                "\n"
                "配合 get_class_api 使用：先获取成员摘要列表拿到目标方法的 id，"
                "再调用此接口按需加载源码，避免一次性加载整个类的所有源码。\n"
                "\n"
                "注意：property 类型符号无 src_code，返回 null。"
                "function/constructor 有源码时才返回有效结果。\n"
                "返回格式：{id, name, kind, file_path, line_number, src_code}"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol_id": {
                        "type": "integer",
                        "description": "从 get_class_api 返回的成员 id 字段获取",
                    },
                },
                "required": ["symbol_id"],
            },
        ),
        # ── 资源查询 ─────────────────────────────────────────────────────────
        types.Tool(
            name="find_layout",
            description=(
                "查找布局资源文件（res/layout 目录下的 XML）。\n"
                "name 为 LIKE '%value%' 部分匹配，如 'fragment_feed' 可匹配 'fragment_feed_list'。\n"
                "module 为精确匹配，格式如 'compfeed'。\n"
                "返回格式：{total, items: [{name, file_path, module, ...}]}"
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
                "查找 drawable 资源（shape / selector / vector / layer-list XML 及图片资源）。\n"
                "name 为 LIKE '%value%' 部分匹配。\n"
                "module 为精确匹配，格式如 'compfeed'。\n"
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
                "查找 AndroidManifest.xml 中注册的四大组件（Activity / Service / BroadcastReceiver / ContentProvider）。\n"
                "name 为 LIKE '%value%' 部分匹配，如 'FeedActivity'。\n"
                "component_type 为精确匹配：activity | service | receiver | provider。\n"
                "module 为精确匹配，格式如 'compfeed'。\n"
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
        types.Tool(
            name="find_style",
            description=(
                "查找样式资源（res/values/styles.xml 中的 style 定义）。\n"
                "name 为 LIKE '%value%' 部分匹配，如 'AppTheme' 可匹配 'AppTheme.NoActionBar'。\n"
                "module 为精确匹配，格式如 'compfeed'。\n"
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
        # ── 模块依赖 ─────────────────────────────────────────────────────────
        types.Tool(
            name="find_module_deps",
            description=(
                "查询模块的直接依赖关系（仅模块间依赖，不含外部 aar/jar）。\n"
                "\n"
                "module 为精确匹配，格式如 'compfeed'。\n"
                "scope 为精确匹配：api | implementation | compileOnly | runtimeOnly 等。\n"
                "syntax 为精确匹配：component（SDK 接口依赖，推荐）| project（源码依赖，不推荐）。\n"
                "\n"
                "返回格式：{\n"
                "  sdk_deps:  [{depends_on, syntax, scope}],  // SDK 层依赖（来自 component.gradle，接口间依赖）\n"
                "  impl_deps: [{depends_on, syntax, scope}],  // Impl 层依赖（来自模块 build.gradle，实现代码依赖）\n"
                "}\n"
                "\n"
                "impl_deps 中 syntax='project' 的条目表示违反 SDK/Impl 分离规范，建议改为 component()。"
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
        # ── 统计与维护 ───────────────────────────────────────────────────────
        types.Tool(
            name="project_stats",
            description=(
                "返回当前索引库的整体统计：总文件数、总符号数、模块数、"
                "最后索引时间、解析失败数、依赖记录数。\n"
                "无需参数。适合在开始分析前先了解项目规模，"
                "或判断索引是否过期（对比 last_indexed 时间）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="update_index",
            description=(
                "对指定项目执行增量索引更新：只重新解析新增或修改过的文件，删除已消失文件的记录。\n"
                "\n"
                "何时调用：\n"
                "  • 用户告知刚修改了代码文件\n"
                "  • 搜索结果与用户描述的代码不一致，怀疑索引过期\n"
                "  • project_stats 显示 last_indexed 时间明显滞后\n"
                "\n"
                "project_path 为 Android 项目的绝对路径，如 '/Users/foo/MyApp.android'。\n"
                "返回格式：{status, elapsed_seconds, symbols_before, symbols_after, files_after}"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Android 项目根目录的绝对路径",
                    },
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
    elif name == "get_class_interfaces":
        result = engine.get_class_interfaces(**arguments)
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
