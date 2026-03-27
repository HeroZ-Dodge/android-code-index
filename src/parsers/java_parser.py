"""Java 源文件解析器：使用 tree-sitter-java 提取符号信息。"""

import json
from pathlib import Path
from typing import Any

try:
    import tree_sitter_java as tsjava
    from tree_sitter import Language, Parser
    _JAVA_LANGUAGE = Language(tsjava.language())
except Exception as e:
    _JAVA_LANGUAGE = None
    _JAVA_LOAD_ERROR = str(e)


def _make_parser() -> Any:
    if _JAVA_LANGUAGE is None:
        raise RuntimeError(f"Java grammar 未加载: {_JAVA_LOAD_ERROR}")
    from tree_sitter import Parser
    return Parser(_JAVA_LANGUAGE)


# ──────────────────────────────────────────────
# 辅助
# ──────────────────────────────────────────────

def _text(node, src: bytes) -> str:
    return src[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _simple_name(node, src: bytes) -> str:
    """从类型节点提取简单类名，剥掉泛型参数。
    generic_type → type_identifier 子节点；其他直接取 identifier/type_identifier。
    """
    if node.type == "generic_type":
        id_node = next((c for c in node.children
                        if c.type in ("type_identifier", "identifier")), None)
        return _text(id_node, src) if id_node else _text(node, src).split("<")[0]
    # scoped_identifier: com.foo.Bar → 取最后段
    raw = _text(node, src).split("<")[0].strip()
    return raw.split(".")[-1]


def _extract_package(root, src: bytes) -> str:
    for child in root.children:
        if child.type == "package_declaration":
            # package com.example → 取最后的 identifier
            for c in reversed(child.children):
                if c.type in ("scoped_identifier", "identifier"):
                    return _text(c, src)
    return ""


def _extract_imports(root, src: bytes) -> dict[str, str]:
    """解析文件顶部的 import 语句，返回 {简单名: 全限定名} 映射。
    仅处理具名 import（不含 * 通配符导入）。
    """
    mapping: dict[str, str] = {}
    for child in root.children:
        if child.type == "import_declaration":
            # import com.foo.Bar; → 取 scoped_identifier 或 identifier
            for c in child.children:
                if c.type in ("scoped_identifier", "identifier"):
                    fqn = _text(c, src)
                    if "*" not in fqn:
                        simple = fqn.split(".")[-1]
                        mapping[simple] = fqn
                    break
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


def _extract_annotations(node, src: bytes) -> str | None:
    annots = []
    for c in node.children:
        if c.type == "modifiers":
            for mc in c.children:
                if mc.type == "marker_annotation" or mc.type == "annotation":
                    annots.append(_text(mc, src))
    return json.dumps(annots, ensure_ascii=False) if annots else None


def _extract_visibility(node, src: bytes) -> str:
    modifiers_node = next(
        (c for c in node.children if c.type == "modifiers"), None
    )
    if modifiers_node:
        for c in modifiers_node.children:
            if c.type in ("public", "private", "protected"):
                return c.type
    return "package"  # Java 默认包级可见


def _extract_params(node, src: bytes) -> str:
    params_node = next(
        (c for c in node.children if c.type == "formal_parameters"), None
    )
    if not params_node:
        return ""
    types = []
    for c in params_node.children:
        if c.type == "formal_parameter":
            type_node = c.child_by_field_name("type") or (
                c.children[0] if c.children else None
            )
            if type_node:
                types.append(_text(type_node, src))
    return ",".join(types)


def _has_modifier(node, src: bytes, modifier: str) -> bool:
    modifiers_node = next(
        (c for c in node.children if c.type == "modifiers"), None
    )
    if modifiers_node:
        return any(
            _text(c, src) == modifier
            for c in modifiers_node.children
        )
    return False


# ──────────────────────────────────────────────
# 解析方法
# ──────────────────────────────────────────────

def _parse_method(node, src: bytes, package: str, parent_qualified: str,
                  module: str, file_path: str, source_set: str) -> dict | None:
    name_node = node.child_by_field_name("name")
    if not name_node:
        return None
    name = _text(name_node, src)

    params_str = _extract_params(node, src)
    ret_node = node.child_by_field_name("type")
    return_type = _text(ret_node, src) if ret_node else None

    prefix = parent_qualified or package
    param_sig = f"({params_str})"
    ret_sig = f":{return_type}" if return_type else ""
    qualified_name = f"{prefix}.{name}{param_sig}{ret_sig}" if prefix else f"{name}{param_sig}{ret_sig}"

    is_abstract = int(_has_modifier(node, src, "abstract"))
    is_override = 0  # Java 中 @Override 是注解，不是修饰符，此处简化

    return {
        "name": name,
        "qualified_name": qualified_name,
        "kind": "function",
        "module": module,
        "file_path": file_path,
        "source_set": source_set,
        "line_number": node.start_point[0] + 1,
        "signature": f"{return_type or 'void'} {name}{param_sig}",
        "visibility": _extract_visibility(node, src),
        "is_abstract": is_abstract,
        "is_override": is_override,
        "parent_class": parent_qualified or None,
        "annotations": _extract_annotations(node, src),
        "return_type": return_type,
        "parameters": params_str or None,
    }


# ──────────────────────────────────────────────
# 解析字段
# ──────────────────────────────────────────────

def _parse_field(node, src: bytes, package: str, parent_qualified: str,
                 module: str, file_path: str, source_set: str) -> list[dict]:
    type_node = node.child_by_field_name("type")
    return_type = _text(type_node, src) if type_node else None
    results = []
    for c in node.children:
        if c.type == "variable_declarator":
            name_node = c.child_by_field_name("name")
            if not name_node:
                continue
            name = _text(name_node, src)
            prefix = parent_qualified or package
            qualified_name = f"{prefix}.{name}" if prefix else name
            results.append({
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
            })
    return results


# ──────────────────────────────────────────────
# 解析类/接口/枚举
# ──────────────────────────────────────────────

def _parse_class(node, src: bytes, package: str, parent_qualified: str,
                 module: str, file_path: str, source_set: str,
                 imports: dict[str, str] | None = None) -> list[dict]:
    if imports is None:
        imports = {}
    name_node = node.child_by_field_name("name")
    if not name_node:
        return []
    name = _text(name_node, src)

    prefix = parent_qualified or package
    qualified_name = f"{prefix}.{name}" if prefix else name

    # 类型判断
    kind_map = {
        "class_declaration": "class",
        "interface_declaration": "interface",
        "enum_declaration": "class",
        "annotation_type_declaration": "class",
    }
    kind = kind_map.get(node.type, "class")

    # 父类：superclass 节点的子节点中跳过 'extends' 关键字取类型节点
    parent_class = None
    superclass_node = node.child_by_field_name("superclass")
    if superclass_node:
        type_node = next((c for c in superclass_node.children
                          if c.type not in ("extends",)), None)
        if type_node:
            parent_class = _resolve_name(_simple_name(type_node, src), package, imports)

    # 接口列表：child_by_field_name("interfaces") 实际返回 super_interfaces 节点
    interfaces = []
    interfaces_node = node.child_by_field_name("interfaces")
    if interfaces_node:
        type_list = next((c for c in interfaces_node.children
                          if c.type == "type_list"), None)
        if type_list:
            for tc in type_list.children:
                if tc.type != ",":
                    interfaces.append(_resolve_name(_simple_name(tc, src), package, imports))

    is_abstract = int(_has_modifier(node, src, "abstract"))
    extra = None
    if node.type == "enum_declaration":
        extra = json.dumps({"class_modifier": "enum"}, ensure_ascii=False)

    sym = {
        "name": name,
        "qualified_name": qualified_name,
        "kind": kind,
        "module": module,
        "file_path": file_path,
        "source_set": source_set,
        "line_number": node.start_point[0] + 1,
        "visibility": _extract_visibility(node, src),
        "is_abstract": is_abstract,
        "is_override": 0,
        "parent_class": parent_class,
        "interfaces": json.dumps(interfaces, ensure_ascii=False) if interfaces else None,
        "annotations": _extract_annotations(node, src),
        "extra": extra,
    }

    symbols = [sym]

    # 类体成员
    body = node.child_by_field_name("body")
    if body:
        for child in body.children:
            if child.type == "method_declaration":
                m = _parse_method(child, src, package, qualified_name,
                                  module, file_path, source_set)
                if m:
                    symbols.append(m)
            elif child.type == "field_declaration":
                symbols.extend(
                    _parse_field(child, src, package, qualified_name,
                                 module, file_path, source_set)
                )
            elif child.type in ("class_declaration", "interface_declaration",
                                "enum_declaration"):
                symbols.extend(
                    _parse_class(child, src, package, qualified_name,
                                 module, file_path, source_set, imports)
                )

    return symbols


# ──────────────────────────────────────────────
# 公开接口
# ──────────────────────────────────────────────

def parse_java_file(
    file_path: Path,
    module: str,
    source_set: str,
) -> tuple[list[dict[str, Any]], str | None]:
    """
    解析 Java 源文件，返回 (symbols, warning)。

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

        for child in root.children:
            if child.type in ("class_declaration", "interface_declaration",
                              "enum_declaration", "annotation_type_declaration"):
                symbols.extend(
                    _parse_class(child, src, package, "",
                                 module, str(file_path), source_set, imports)
                )

        return symbols, None

    except Exception as e:
        return [], f"{type(e).__name__}: {e}"
