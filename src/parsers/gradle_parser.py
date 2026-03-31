"""Gradle 依赖解析器：从 build.gradle / build.gradle.kts 提取模块依赖关系。
以及从 gradlescript/component.gradle 提取 SDK 层依赖关系。"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


# ──────────────────────────────────────────────
# 正则
# ──────────────────────────────────────────────

# component(':moduleName') — SDK 依赖（只依赖 sdk source set）
# Groovy：component(':x')  Kotlin DSL：component(":x")
_COMPONENT_RE = re.compile(
    r"""component\s*\(\s*['"](?P<module>:[^'"]+)['"]\s*\)"""
)

# project(':moduleName') — 传统全模块依赖
_PROJECT_RE = re.compile(
    r"""project\s*\(\s*['"](?P<module>:[^'"]+)['"]\s*\)"""
)

# 外部依赖（非 component/project）的依赖作用域关键词
_SCOPE_RE = re.compile(
    r"""(?P<scope>implementation|api|compileOnly|runtimeOnly|testImplementation|androidTestImplementation)\s*"""
    r"""(?:\(?\s*['"](?P<dep>[^'"]+)['"]\s*\)?)"""
)

# component.gradle DSL 中的模块块起始：'moduleName' { 或 "moduleName" {
_MODULE_BLOCK_RE = re.compile(
    r"""^\s*['"](?P<module>[\w\-]+)['"]\s*\{""",
    re.MULTILINE,
)


# ──────────────────────────────────────────────
# 解析单个 build.gradle（各模块自己的 Impl 层依赖）
# ──────────────────────────────────────────────

def _parse_build_gradle(
    text: str,
    module: str,
    source_file: str,
) -> list[dict[str, Any]]:
    """
    从 build.gradle / build.gradle.kts 文本中提取依赖。

    返回 module_dependencies 行列表（尚未写入 DB，仅数据）。
    所有记录 layer='impl'（Impl 层依赖）。
    """
    records: list[dict[str, Any]] = []
    seen: set[tuple] = set()   # 去重 (module, depends_on, scope, syntax)

    def _add(depends_on: str, dependency_type: str,
             dependency_scope: str, syntax: str, raw: str) -> None:
        key = (module, depends_on, dependency_scope, syntax)
        if key in seen:
            return
        seen.add(key)
        records.append({
            "module": module,
            "depends_on": depends_on,
            "dependency_type": dependency_type,
            "dependency_scope": dependency_scope,
            "syntax": syntax,
            "raw_declaration": raw.strip(),
            "source_file": source_file,
            "layer": "impl",
        })

    # component() 匹配 → impl 依赖另一个模块的 SDK（推荐写法）
    for m in _COMPONENT_RE.finditer(text):
        dep_module = m.group("module").lstrip(":")
        _add(dep_module, "module", "sdk", "component", m.group(0))

    # project() 匹配 → 全模块依赖（不推荐）
    for m in _PROJECT_RE.finditer(text):
        dep_module = m.group("module").lstrip(":")
        # 判断其所在行的依赖作用域
        line_start = text.rfind("\n", 0, m.start()) + 1
        line_end = text.find("\n", m.end())
        line = text[line_start:line_end if line_end != -1 else len(text)]
        scope = "implementation"  # 默认
        for kw in ("api", "compileOnly", "runtimeOnly",
                   "testImplementation", "androidTestImplementation", "implementation"):
            if kw in line:
                scope = kw
                break
        _add(dep_module, "module", scope, "project", m.group(0))

    # 外部依赖（字符串形式 "group:artifact:version"）
    for m in _SCOPE_RE.finditer(text):
        dep_str = m.group("dep")
        # 跳过已被 component/project 处理的
        if dep_str.startswith(":"):
            continue
        scope = m.group("scope")
        _add(dep_str, "external", scope, "external", m.group(0))

    return records


# ──────────────────────────────────────────────
# 解析 gradlescript/component.gradle（SDK 层依赖配置）
# ──────────────────────────────────────────────

def _parse_component_gradle(
    text: str,
    source_file: str,
) -> list[dict[str, Any]]:
    """
    解析 gradlescript/component.gradle 的 DSL 结构，提取每个模块的 SDK 层依赖。

    DSL 格式（Groovy）：
        'moduleName' {
            groupId 'com.example'
            artifactId 'name'
            dependencies {
                implementation component(':otherModule')
            }
        }

    所有记录 layer='sdk'（SDK 层接口依赖）。
    """
    records: list[dict[str, Any]] = []

    for m in _MODULE_BLOCK_RE.finditer(text):
        module_name = m.group("module")

        # 找到此模块块的大括号范围
        block_open = m.end() - 1   # '{' 位置
        depth = 0
        i = block_open
        while i < len(text):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1

        block_content = text[m.end():i]

        seen: set[str] = set()
        for cm in _COMPONENT_RE.finditer(block_content):
            dep_module = cm.group("module").lstrip(":")
            if dep_module in seen:
                continue
            seen.add(dep_module)
            records.append({
                "module": module_name,
                "depends_on": dep_module,
                "dependency_type": "module",
                "dependency_scope": "implementation",
                "syntax": "component",
                "raw_declaration": cm.group(0).strip(),
                "source_file": source_file,
                "layer": "sdk",
            })

    return records


# ──────────────────────────────────────────────
# 公开接口
# ──────────────────────────────────────────────

def parse_gradle_file(
    file_path: Path,
    module: str,
) -> tuple[list[dict[str, Any]], str | None]:
    """
    解析 build.gradle / build.gradle.kts / component.gradle，返回 (dep_records, warning)。

    - 如果文件名为 component.gradle，使用 SDK 层 DSL 解析（layer='sdk'）。
    - 否则按普通 build.gradle 处理（layer='impl'）。

    解析失败时返回 ([], error_message)，不抛异常。
    """
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
        source_file = str(file_path)

        if file_path.name == "component.gradle":
            records = _parse_component_gradle(text, source_file)
        else:
            records = _parse_build_gradle(text, module, source_file)

        return records, None
    except Exception as e:
        return [], f"{type(e).__name__}: {e}"
