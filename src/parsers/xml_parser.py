"""Android XML 资源文件解析器：使用标准库 xml.etree.ElementTree。"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


# ──────────────────────────────────────────────
# 辅助
# ──────────────────────────────────────────────

_ANDROID_NS = "http://schemas.android.com/apk/res/android"
_ANDROID_PREFIX = f"{{{_ANDROID_NS}}}"


def _android_attr(element, attr: str) -> str | None:
    return element.get(f"{_ANDROID_PREFIX}{attr}")


def _strip_id_prefix(value: str | None) -> str | None:
    """去掉 @+id/ 或 @id/ 前缀，返回纯 id 名称。"""
    if value is None:
        return None
    for prefix in ("@+id/", "@id/"):
        if value.startswith(prefix):
            return value[len(prefix):]
    return value


# ──────────────────────────────────────────────
# 布局文件解析
# ──────────────────────────────────────────────

def _parse_layout(root_element, file_path: str, module: str,
                  source_set: str) -> list[dict]:
    """提取根布局类型和所有 android:id View。"""
    symbols = []
    file_name = Path(file_path).stem

    # 根布局符号
    root_tag = root_element.tag.split("}")[-1] if "}" in root_element.tag else root_element.tag
    symbols.append({
        "name": file_name,
        "qualified_name": f"{module}.layout.{file_name}",
        "kind": "layout",
        "module": module,
        "file_path": file_path,
        "source_set": source_set,
        "line_number": 1,
        "extra": json.dumps({"root_view": root_tag}, ensure_ascii=False),
    })

    # 遍历所有节点，提取 android:id
    for elem in root_element.iter():
        view_id = _strip_id_prefix(_android_attr(elem, "id"))
        if not view_id:
            continue
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        symbols.append({
            "name": view_id,
            "qualified_name": f"{module}.layout.{file_name}.{view_id}",
            "kind": "view_id",
            "module": module,
            "file_path": file_path,
            "source_set": source_set,
            "line_number": None,
            "extra": json.dumps({"view_type": tag}, ensure_ascii=False),
        })

    return symbols


# ──────────────────────────────────────────────
# strings.xml 解析
# ──────────────────────────────────────────────

def _parse_strings(root_element, file_path: str, module: str,
                   source_set: str) -> list[dict]:
    symbols = []
    for elem in root_element.iter("string"):
        name = elem.get("name")
        if not name:
            continue
        value = "".join(elem.itertext())
        symbols.append({
            "name": name,
            "qualified_name": f"{module}.string.{name}",
            "kind": "string_res",
            "module": module,
            "file_path": file_path,
            "source_set": source_set,
            "line_number": None,
            "resource_value": value,
        })
    return symbols


# ──────────────────────────────────────────────
# colors.xml 解析
# ──────────────────────────────────────────────

def _parse_colors(root_element, file_path: str, module: str,
                  source_set: str) -> list[dict]:
    symbols = []
    for elem in root_element.iter("color"):
        name = elem.get("name")
        if not name:
            continue
        value = (elem.text or "").strip()
        symbols.append({
            "name": name,
            "qualified_name": f"{module}.color.{name}",
            "kind": "color_res",
            "module": module,
            "file_path": file_path,
            "source_set": source_set,
            "line_number": None,
            "resource_value": value,
        })
    return symbols


# ──────────────────────────────────────────────
# dimens.xml 解析
# ──────────────────────────────────────────────

def _parse_dimens(root_element, file_path: str, module: str,
                  source_set: str) -> list[dict]:
    symbols = []
    for elem in root_element.iter("dimen"):
        name = elem.get("name")
        if not name:
            continue
        value = (elem.text or "").strip()
        symbols.append({
            "name": name,
            "qualified_name": f"{module}.dimen.{name}",
            "kind": "dimen_res",
            "module": module,
            "file_path": file_path,
            "source_set": source_set,
            "line_number": None,
            "resource_value": value,
        })
    return symbols


# ──────────────────────────────────────────────
# styles.xml 解析
# ──────────────────────────────────────────────

def _parse_styles(root_element, file_path: str, module: str,
                  source_set: str) -> list[dict]:
    symbols = []
    for elem in root_element.iter("style"):
        name = elem.get("name")
        if not name:
            continue
        parent = elem.get("parent") or None
        symbols.append({
            "name": name,
            "qualified_name": f"{module}.style.{name}",
            "kind": "style",
            "module": module,
            "file_path": file_path,
            "source_set": source_set,
            "line_number": None,
            "parent_class": parent,
        })
    return symbols


# ──────────────────────────────────────────────
# AndroidManifest.xml 解析
# ──────────────────────────────────────────────

_COMPONENT_TAGS = {"activity", "service", "receiver", "provider"}


def _parse_manifest(root_element, file_path: str, module: str,
                    source_set: str) -> list[dict]:
    symbols = []
    for elem in root_element.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag not in _COMPONENT_TAGS:
            continue
        name = _android_attr(elem, "name")
        if not name:
            continue

        exported = _android_attr(elem, "exported")
        intent_filters = [
            _android_attr(action, "name")
            for action_parent in elem.iter("intent-filter")
            for action in action_parent.iter("action")
            if _android_attr(action, "name")
        ]

        extra = json.dumps({
            "exported": exported,
            "intent_filters": intent_filters,
        }, ensure_ascii=False)

        symbols.append({
            "name": name.split(".")[-1],
            "qualified_name": f"{module}.manifest.{name}",
            "kind": "manifest_component",
            "module": module,
            "file_path": file_path,
            "source_set": source_set,
            "line_number": None,
            "extra": extra,
            "annotations": json.dumps([tag], ensure_ascii=False),
        })

    return symbols


# ──────────────────────────────────────────────
# 公开接口
# ──────────────────────────────────────────────

def _classify_xml(file_path: Path) -> str:
    """根据文件路径和文件名判断 XML 类型。"""
    name = file_path.stem.lower()
    parent = file_path.parent.name.lower()

    if file_path.name == "AndroidManifest.xml":
        return "manifest"
    if parent.startswith("layout"):
        return "layout"
    if name == "strings":
        return "strings"
    if name == "colors":
        return "colors"
    if name == "dimens":
        return "dimens"
    if name == "styles":
        return "styles"
    if parent.startswith("values"):
        # values/ 目录下的其他文件，按根元素判断
        return "values"
    return "unknown"


def parse_xml_file(
    file_path: Path,
    module: str,
    source_set: str,
) -> tuple[list[dict[str, Any]], str | None]:
    """
    解析 Android XML 资源文件，返回 (symbols, warning)。

    解析失败时返回 ([], error_message)，不抛异常。
    """
    try:
        tree = ET.parse(str(file_path))
        root_element = tree.getroot()
        xml_type = _classify_xml(file_path)

        fp = str(file_path)

        if xml_type == "manifest":
            return _parse_manifest(root_element, fp, module, source_set), None
        if xml_type == "layout":
            return _parse_layout(root_element, fp, module, source_set), None
        if xml_type == "strings":
            return _parse_strings(root_element, fp, module, source_set), None
        if xml_type == "colors":
            return _parse_colors(root_element, fp, module, source_set), None
        if xml_type == "dimens":
            return _parse_dimens(root_element, fp, module, source_set), None
        if xml_type == "styles":
            return _parse_styles(root_element, fp, module, source_set), None
        if xml_type == "values":
            # 通用 values 文件：合并解析
            syms = (
                _parse_strings(root_element, fp, module, source_set)
                + _parse_colors(root_element, fp, module, source_set)
                + _parse_dimens(root_element, fp, module, source_set)
                + _parse_styles(root_element, fp, module, source_set)
            )
            return syms, None

        return [], None   # unknown 类型，跳过

    except Exception as e:
        return [], f"{type(e).__name__}: {e}"
