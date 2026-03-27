"""Kotlin 源文件解析器：使用 tree-sitter 提取符号信息。"""

import json
import re
from pathlib import Path
from typing import Any

try:
    import tree_sitter_kotlin as tskotlin
    from tree_sitter import Language, Parser
    _KOTLIN_LANGUAGE = Language(tskotlin.language())
except Exception:
    try:
        from tree_sitter_languages import get_language, get_parser as _get_parser
        _KOTLIN_LANGUAGE = get_language("kotlin")
    except Exception as e:
        _KOTLIN_LANGUAGE = None
        _KOTLIN_LOAD_ERROR = str(e)


def _make_parser() -> Any:
    if _KOTLIN_LANGUAGE is None:
        raise RuntimeError(f"Kotlin grammar 未加载: {_KOTLIN_LOAD_ERROR}")
    from tree_sitter import Parser
    p = Parser(_KOTLIN_LANGUAGE)
    return p


# ──────────────────────────────────────────────
# 辅助：从 AST 节点取文本
# ──────────────────────────────────────────────

def _text(node, src: bytes) -> str:
    return src[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _child_text(node, field: str, src: bytes) -> str | None:
    c = node.child_by_field_name(field)
    return _text(c, src) if c else None


def _children_of_type(node, *types) -> list:
    return [c for c in node.children if c.type in types]


# ──────────────────────────────────────────────
# 提取包名
# ──────────────────────────────────────────────

def _extract_package(root, src: bytes) -> str:
    for child in root.children:
        if child.type == "package_header":
            # grammar v1: field name "identifier"
            id_node = child.child_by_field_name("identifier")
            if id_node:
                return _text(id_node, src)
            # grammar v2 (tree-sitter-kotlin 1.x): child type "qualified_identifier"
            for c in child.children:
                if c.type in ("qualified_identifier", "identifier"):
                    return _text(c, src)
    return ""


# ──────────────────────────────────────────────
# 提取 import 映射：简单名 → 全限定名
# ──────────────────────────────────────────────

def _extract_imports(root, src: bytes) -> dict[str, str]:
    """解析文件顶部的 import 语句，返回 {简单名: 全限定名} 映射。
    仅处理具名 import（不含 * 通配符导入）。
    """
    mapping: dict[str, str] = {}

    def _handle_import_node(imp) -> None:
        # 兼容 import_header（旧 grammar）和 import（新 grammar）
        id_node = imp.child_by_field_name("identifier")
        if not id_node:
            for c in imp.children:
                if c.type in ("qualified_identifier", "identifier"):
                    id_node = c
                    break
        if id_node:
            fqn = _text(id_node, src)
            if "*" not in fqn:
                simple = fqn.split(".")[-1]
                mapping[simple] = fqn

    for child in root.children:
        if child.type == "import_list":
            for imp in child.children:
                if imp.type in ("import_header", "import"):
                    _handle_import_node(imp)
        elif child.type in ("import_header", "import"):
            _handle_import_node(child)
    return mapping


def _resolve_name(simple: str, package: str, imports: dict[str, str]) -> str:
    """将简单类名解析为全限定名。
    优先级：import 表 > 同包推断（含包名时） > 原样返回。
    """
    if "." in simple:
        # 已经是全限定名（或带泛型如 Map.Entry），直接返回基础部分
        return simple.split("<")[0].strip()
    if simple in imports:
        return imports[simple]
    if package:
        return f"{package}.{simple}"
    return simple


# ──────────────────────────────────────────────
# 提取注解列表 → JSON 字符串
# ──────────────────────────────────────────────

def _extract_annotations(node, src: bytes) -> str | None:
    annots = []
    for c in node.children:
        if c.type in ("annotation", "multi_annotation"):
            annots.append(_text(c, src).strip())
    return json.dumps(annots, ensure_ascii=False) if annots else None


# ──────────────────────────────────────────────
# 提取函数参数列表 → "Type,Type,..." 字符串
# ──────────────────────────────────────────────

def _extract_params(fn_node, src: bytes) -> str:
    params_node = (fn_node.child_by_field_name("value_parameters")
                   or next((c for c in fn_node.children
                            if c.type in ("function_value_parameters",
                                          "value_parameters")), None))
    if not params_node:
        return ""
    types = []
    for c in params_node.children:
        if c.type == "function_value_parameter":
            type_node = (c.child_by_field_name("type")
                         or next((g for g in c.children
                                  if g.type not in ("identifier", ":", ",",
                                                    "parameter_modifiers")), None))
            if type_node:
                types.append(_text(type_node, src))
    return ",".join(types)


# ──────────────────────────────────────────────
# 提取可见性
# ──────────────────────────────────────────────

_VISIBILITY_KWS = {"public", "private", "protected", "internal"}


def _extract_visibility(node, src: bytes) -> str | None:
    for c in node.children:
        if c.type == "visibility_modifier":
            return _text(c, src)
    return "public"  # Kotlin 默认 public


# ──────────────────────────────────────────────
# 提取接口列表 → JSON 字符串
# ──────────────────────────────────────────────

def _extract_interfaces(delegation_specifiers_node, src: bytes) -> str | None:
    if not delegation_specifiers_node:
        return None
    names = []
    for c in delegation_specifiers_node.children:
        if c.type in ("delegation_specifier", "constructor_invocation",
                      "user_type", "explicit_delegation"):
            type_node = c.child_by_field_name("type") or c
            names.append(_text(type_node, src).strip().split("(")[0])
    return json.dumps(names, ensure_ascii=False) if names else None


# ──────────────────────────────────────────────
# 递归解析类体内的成员
# ──────────────────────────────────────────────

def _parse_class_body(body_node, src: bytes, package: str,
                      parent_qualified: str, module: str,
                      file_path: str, source_set: str,
                      imports: dict[str, str]) -> list[dict]:
    symbols = []

    def _process_node(child) -> None:
        # tree-sitter-kotlin wraps members:
        #   class_body → class_member_declarations → class_member_declaration → <decl>
        if child.type in ("class_member_declarations", "class_member_declaration"):
            for grandchild in child.children:
                _process_node(grandchild)
        elif child.type == "function_declaration":
            sym = _parse_function(child, src, package, parent_qualified,
                                  module, file_path, source_set)
            if sym:
                symbols.append(sym)
        elif child.type == "property_declaration":
            sym = _parse_property(child, src, package, parent_qualified,
                                  module, file_path, source_set)
            if sym:
                symbols.append(sym)
        elif child.type in ("class_declaration", "object_declaration",
                            "companion_object"):
            syms = _parse_class(child, src, package, parent_qualified,
                                module, file_path, source_set, imports)
            symbols.extend(syms)

    for child in body_node.children:
        _process_node(child)

    return symbols


# ──────────────────────────────────────────────
# 解析函数
# ──────────────────────────────────────────────

def _parse_function(node, src: bytes, package: str, parent_qualified: str,
                    module: str, file_path: str, source_set: str) -> dict | None:
    name_node = (node.child_by_field_name("name")
                 or node.child_by_field_name("simple_identifier")
                 or next((c for c in node.children if c.type == "identifier"), None))
    if not name_node:
        return None
    name = _text(name_node, src)

    params_str = _extract_params(node, src)
    ret_node = (node.child_by_field_name("return_type")
                or node.child_by_field_name("type"))
    if not ret_node:
        # return type follows ':' in children: fun foo(): RetType
        children = node.children
        for i, c in enumerate(children):
            if c.type == ":" and i + 1 < len(children):
                nxt = children[i + 1]
                if nxt.type not in ("function_body", "block"):
                    ret_node = nxt
                break
    return_type = _text(ret_node, src).lstrip(":").strip() if ret_node else None

    # qualified_name = "pkg.Class.method(Params):ReturnType"
    prefix = parent_qualified or package
    param_sig = f"({params_str})" if params_str is not None else "()"
    ret_sig = f":{return_type}" if return_type else ""
    qualified_name = f"{prefix}.{name}{param_sig}{ret_sig}" if prefix else f"{name}{param_sig}{ret_sig}"

    is_override = any(
        c.type == "modifier" and _text(c, src) == "override"
        for c in node.children
    )
    is_abstract = any(
        c.type == "modifier" and _text(c, src) == "abstract"
        for c in node.children
    )

    return {
        "name": name,
        "qualified_name": qualified_name,
        "kind": "function",
        "module": module,
        "file_path": file_path,
        "source_set": source_set,
        "line_number": node.start_point[0] + 1,
        "signature": f"fun {name}{param_sig}{ret_sig}",
        "visibility": _extract_visibility(node, src),
        "is_abstract": int(is_abstract),
        "is_override": int(is_override),
        "parent_class": parent_qualified or None,
        "annotations": _extract_annotations(node, src),
        "return_type": return_type,
        "parameters": params_str or None,
    }


# ──────────────────────────────────────────────
# 解析属性
# ──────────────────────────────────────────────

def _parse_property(node, src: bytes, package: str, parent_qualified: str,
                    module: str, file_path: str, source_set: str) -> dict | None:
    name_node = (node.child_by_field_name("name")
                 or node.child_by_field_name("simple_identifier"))
    if not name_node:
        # tree-sitter-kotlin puts name inside variable_declaration
        var_decl = next((c for c in node.children if c.type == "variable_declaration"), None)
        if var_decl:
            name_node = next((c for c in var_decl.children
                              if c.type == "identifier"), None)
    if not name_node:
        return None
    name = _text(name_node, src)

    prefix = parent_qualified or package
    qualified_name = f"{prefix}.{name}" if prefix else name

    type_node = node.child_by_field_name("type")
    if not type_node:
        # type is inside variable_declaration after the colon
        var_decl = next((c for c in node.children if c.type == "variable_declaration"), None)
        if var_decl:
            type_node = next((c for c in var_decl.children
                              if c.type not in ("identifier", ":", "val", "var")), None)
    return_type = _text(type_node, src) if type_node else None

    return {
        "name": name,
        "qualified_name": qualified_name,
        "kind": "property",
        "module": module,
        "file_path": file_path,
        "source_set": source_set,
        "line_number": node.start_point[0] + 1,
        "visibility": _extract_visibility(node, src),
        "is_abstract": 0,
        "is_override": 0,
        "parent_class": parent_qualified or None,
        "return_type": return_type,
    }


# ──────────────────────────────────────────────
# 解析类/接口/枚举/object
# ──────────────────────────────────────────────

_CLASS_NODE_TYPES = {
    "class_declaration",
    "interface_declaration",
    "object_declaration",
    "companion_object",
    "enum_class_body",
}

_KIND_MAP = {
    "class_declaration": "class",
    "interface_declaration": "interface",
    "object_declaration": "object",
    "companion_object": "class",
}


def _detect_class_kind(node, src: bytes) -> str:
    # tree-sitter-kotlin 将 interface 也解析为 class_declaration
    # 通过检查直接关键字子节点来区分
    for c in node.children:
        if c.type == "interface":
            return "interface"
        if c.type == "enum":
            return "class"   # enum class
    modifiers_text = " ".join(
        _text(c, src) for c in node.children if c.type == "modifier"
    )
    base = _KIND_MAP.get(node.type, "class")
    return base


def _delegation_fqn(spec_node, src: bytes, package: str,
                    imports: dict[str, str]) -> str:
    """从 delegation_specifier 节点提取全限定类名（剥掉泛型和构造参数后解析）。
    delegation_specifier → constructor_invocation → user_type → identifier
    delegation_specifier → user_type → identifier
    """
    # 找到 user_type 节点
    user_type = None
    for c in spec_node.children:
        if c.type == "constructor_invocation":
            user_type = next((g for g in c.children if g.type == "user_type"), None)
            break
        if c.type == "user_type":
            user_type = c
            break
    if user_type:
        # user_type 可能带泛型: Foo<T> → 取第一个 identifier/type_identifier
        id_node = next((g for g in user_type.children
                        if g.type in ("identifier", "type_identifier")), None)
        if id_node:
            simple = _text(id_node, src)
            return _resolve_name(simple, package, imports)
    # 兜底：取文本后剥掉 (<) 部分
    raw = _text(spec_node, src).strip().split("<")[0].split("(")[0].strip()
    return _resolve_name(raw, package, imports)


def _parse_class(node, src: bytes, package: str, parent_qualified: str,
                 module: str, file_path: str, source_set: str,
                 imports: dict[str, str] | None = None) -> list[dict]:
    if imports is None:
        imports = {}
    name_node = (node.child_by_field_name("name")
                 or node.child_by_field_name("simple_identifier")
                 or next((c for c in node.children if c.type == "identifier"), None))
    name = _text(name_node, src) if name_node else "companion"

    prefix = parent_qualified or package
    qualified_name = f"{prefix}.{name}" if prefix else name

    kind = _detect_class_kind(node, src)

    # delegation_specifiers：field name 在此 grammar 版本失效，按 type 查找
    delegation_node = (node.child_by_field_name("delegation_specifiers")
                       or next((c for c in node.children
                                 if c.type == "delegation_specifiers"), None))

    parent_class = None
    interfaces = []
    if delegation_node:
        specs = [c for c in delegation_node.children
                 if c.type == "delegation_specifier"]
        if specs:
            if node.type == "class_declaration" and kind == "class":
                # 第一个带构造调用的是父类，其余是接口
                first = specs[0]
                has_ctor = any(c.type == "constructor_invocation" for c in first.children)
                if has_ctor:
                    parent_class = _delegation_fqn(first, src, package, imports)
                    interfaces = [_delegation_fqn(s, src, package, imports) for s in specs[1:]]
                else:
                    # 没有构造调用，全部是接口实现（无父类）
                    interfaces = [_delegation_fqn(s, src, package, imports) for s in specs]
            else:
                # interface / object：所有 spec 都是扩展接口
                interfaces = [_delegation_fqn(s, src, package, imports) for s in specs]

    is_abstract = any(
        c.type == "modifier" and _text(c, src) == "abstract"
        for c in node.children
    )

    # 额外信息（data/sealed/enum/annotation 修饰符）
    modifiers_text = " ".join(
        _text(c, src) for c in node.children if c.type == "modifier"
    )
    extra = None
    for kw in ("data", "sealed", "enum", "annotation", "inner", "value"):
        if kw in modifiers_text:
            extra = json.dumps({"class_modifier": kw}, ensure_ascii=False)
            break

    sym: dict = {
        "name": name,
        "qualified_name": qualified_name,
        "kind": kind,
        "module": module,
        "file_path": file_path,
        "source_set": source_set,
        "line_number": node.start_point[0] + 1,
        "visibility": _extract_visibility(node, src),
        "is_abstract": int(is_abstract),
        "is_override": 0,
        "parent_class": parent_class,
        "interfaces": json.dumps(interfaces, ensure_ascii=False) if interfaces else None,
        "annotations": _extract_annotations(node, src),
        "extra": extra,
    }

    symbols = [sym]

    # 递归解析类体成员
    # child_by_field_name may return None for some grammar versions; fall back to type search
    body = (node.child_by_field_name("class_body")
            or node.child_by_field_name("enum_class_body")
            or next((c for c in node.children
                     if c.type in ("class_body", "enum_class_body")), None))
    if body:
        symbols.extend(
            _parse_class_body(body, src, package, qualified_name,
                              module, file_path, source_set, imports)
        )

    return symbols


# ──────────────────────────────────────────────
# 公开接口
# ──────────────────────────────────────────────

def parse_kotlin_file(
    file_path: Path,
    module: str,
    source_set: str,
) -> tuple[list[dict[str, Any]], str | None]:
    """
    解析 Kotlin 源文件，返回 (symbols, warning)。

    解析失败时返回 ([], error_message)，不抛异常。
    """
    try:
        src = file_path.read_bytes()
        parser = _make_parser()
        tree = parser.parse(src)
        root = tree.root_node

        package = _extract_package(root, src)
        imports = _extract_imports(root, src)
        symbols: list[dict] = []

        def _process_top_level(child) -> None:
            # tree-sitter-kotlin may wrap top-level decls in top_level_object
            if child.type == "top_level_object":
                for grandchild in child.children:
                    _process_top_level(grandchild)
            elif child.type in ("class_declaration", "interface_declaration",
                                "object_declaration"):
                symbols.extend(
                    _parse_class(child, src, package, "",
                                 module, str(file_path), source_set, imports)
                )
            elif child.type == "function_declaration":
                sym = _parse_function(child, src, package, "",
                                      module, str(file_path), source_set)
                if sym:
                    symbols.append(sym)
            elif child.type == "property_declaration":
                sym = _parse_property(child, src, package, "",
                                      module, str(file_path), source_set)
                if sym:
                    symbols.append(sym)

        for child in root.children:
            _process_top_level(child)

        return symbols, None

    except Exception as e:
        return [], f"{type(e).__name__}: {e}"
