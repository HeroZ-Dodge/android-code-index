"""Android 项目文件扫描：发现模块、扫描源文件。"""

import re
from pathlib import Path
from dataclasses import dataclass

from src.config import ALL_EXTENSIONS, SKIP_DIRS


@dataclass
class SourceFile:
    file_path: Path
    module: str
    file_type: str        # kotlin / java / xml / gradle
    source_set: str       # sdk / impl / resource / config


# ──────────────────────────────────────────────
# settings.gradle 解析
# ──────────────────────────────────────────────

# 标准写法：include ':moduleName' 或 include(":moduleName")
_INCLUDE_RE = re.compile(r"""include\s*[(\s]['"](:[\w\-/]+)['"]\s*\)?""")

# 自定义路径：project(':x').projectDir = new File('path')  (Groovy)
#             project(":x").projectDir = File("path")       (Kotlin DSL)
#             project(':x').projectDir = file('path')       (Groovy built-in)
_CUSTOM_PATH_RE = re.compile(
    r"""project\s*\(\s*['"](?P<module>:[^'"]+)['"]\s*\)\s*\.projectDir\s*=\s*"""
    r"""(?:new\s+)?[Ff]ile\s*\(\s*['"](?P<path>[^'"]+)['"]\s*\)"""
)


def _find_settings_gradle(project_root: Path) -> Path | None:
    for name in ("settings.gradle", "settings.gradle.kts"):
        p = project_root / name
        if p.is_file():
            return p
    return None


def discover_modules(project_root: Path) -> dict[str, Path]:
    """
    解析 settings.gradle，返回 {模块名: 模块根目录} 映射。

    模块名使用 Gradle 风格（如 ":app"、":core:network"）。
    """
    settings = _find_settings_gradle(project_root)
    if settings is None:
        return {}

    text = settings.read_text(encoding="utf-8", errors="replace")

    # 先收集标准 include 声明
    modules: dict[str, Path] = {}
    for m in _INCLUDE_RE.finditer(text):
        module_name = m.group(1).lstrip(":")         # e.g. "app"
        # 推断默认路径："core:network" → project_root/core/network
        rel = module_name.replace(":", "/")
        modules[module_name] = project_root / rel

    # 再处理自定义 projectDir
    for m in _CUSTOM_PATH_RE.finditer(text):
        module_name = m.group("module").lstrip(":")  # e.g. "libs:foo"
        custom_path = m.group("path")
        # 相对路径相对于 project_root
        resolved = (project_root / custom_path).resolve()
        modules[module_name] = resolved

    return modules


# ──────────────────────────────────────────────
# 模块内文件扫描
# ──────────────────────────────────────────────

def _file_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".kt":
        return "kotlin"
    if suffix == ".java":
        return "java"
    if suffix == ".xml":
        return "xml"
    if suffix in (".gradle", ".kts"):
        return "gradle"
    return "unknown"


def _should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def scan_module(module_name: str, module_root: Path) -> list[SourceFile]:
    """
    扫描单个模块目录，返回该模块下所有源文件列表。

    source_set 规则：
      src/main/sdk/          → sdk
      src/main/java/
      src/main/kotlin/       → impl
      res/                   → resource
      AndroidManifest.xml
      build.gradle(.kts)     → config
    """
    if not module_root.is_dir():
        return []

    files: list[SourceFile] = []

    def add(path: Path, source_set: str) -> None:
        if path.suffix.lower() not in ALL_EXTENSIONS:
            return
        ft = _file_type(path)
        if ft == "unknown":
            return
        files.append(SourceFile(
            file_path=path.resolve(),
            module=module_name,
            file_type=ft,
            source_set=source_set,
        ))

    def walk(directory: Path, source_set: str) -> None:
        if not directory.is_dir():
            return
        for item in directory.iterdir():
            if item.is_dir():
                if item.name in SKIP_DIRS:
                    continue
                walk(item, source_set)
            elif item.is_file():
                add(item, source_set)

    # sdk 源码（公共接口）
    walk(module_root / "src" / "main" / "sdk", "sdk")

    # impl 源码（Java + Kotlin）
    walk(module_root / "src" / "main" / "java", "impl")
    walk(module_root / "src" / "main" / "kotlin", "impl")

    # 资源文件
    walk(module_root / "res", "resource")
    # res 通常在 src/main/res
    walk(module_root / "src" / "main" / "res", "resource")

    # config 文件
    for manifest_name in ("AndroidManifest.xml",):
        for candidate in (
            module_root / "src" / "main" / manifest_name,
            module_root / manifest_name,
        ):
            if candidate.is_file():
                add(candidate, "config")

    for gradle_name in ("build.gradle", "build.gradle.kts"):
        p = module_root / gradle_name
        if p.is_file():
            add(p, "config")

    return files


def scan_project(project_root: Path) -> list[SourceFile]:
    """
    扫描整个 Android 项目，返回所有模块的源文件列表。

    额外包含 gradlescript/component.gradle（SDK 层依赖配置文件）。
    """
    modules = discover_modules(project_root)
    all_files: list[SourceFile] = []
    for module_name, module_root in modules.items():
        all_files.extend(scan_module(module_name, module_root))

    # SDK 层依赖配置文件：gradlescript/component.gradle
    # 使用 '_component_gradle' 作为占位模块名，解析器内部会正确设置每条记录的 module 字段
    component_gradle = project_root / "gradlescript" / "component.gradle"
    if component_gradle.is_file():
        all_files.append(SourceFile(
            file_path=component_gradle.resolve(),
            module="_component_gradle",
            file_type="gradle",
            source_set="config",
        ))

    return all_files
