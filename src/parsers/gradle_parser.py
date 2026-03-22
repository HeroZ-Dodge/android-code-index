"""Gradle 依赖解析器：从 build.gradle / build.gradle.kts 提取模块依赖关系。"""

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

# Gradle 脚本：apply from / apply plugin 中的 component 也可能出现在顶层脚本
_APPLY_COMPONENT_RE = re.compile(
    r"""component\s*\(\s*['"](?P<module>:[^'"]+)['"]\s*\)"""
)


# ──────────────────────────────────────────────
# 解析单个 build.gradle
# ──────────────────────────────────────────────

def _parse_build_gradle(
    text: str,
    module: str,
    source_file: str,
) -> list[dict[str, Any]]:
    """
    从 build.gradle / build.gradle.kts 文本中提取依赖。

    返回 module_dependencies 行列表（尚未写入 DB，仅数据）。
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
        })

    # component() 匹配 → sdk 依赖
    for m in _COMPONENT_RE.finditer(text):
        dep_module = m.group("module")
        _add(dep_module, "module", "sdk", "component", m.group(0))

    # project() 匹配 → 全模块依赖
    for m in _PROJECT_RE.finditer(text):
        dep_module = m.group("module")
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
# 公开接口
# ──────────────────────────────────────────────

def parse_gradle_file(
    file_path: Path,
    module: str,
) -> tuple[list[dict[str, Any]], str | None]:
    """
    解析 build.gradle / build.gradle.kts，返回 (dep_records, warning)。

    解析失败时返回 ([], error_message)，不抛异常。
    """
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
        records = _parse_build_gradle(text, module, str(file_path))
        return records, None
    except Exception as e:
        return [], f"{type(e).__name__}: {e}"
