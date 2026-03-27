"""全局配置：数据库路径、文件类型过滤规则。"""

import os
from pathlib import Path

# ──────────────────────────────────────────────
# 数据库路径
# ──────────────────────────────────────────────

def get_db_path(project_name: str) -> Path:
    """返回指定项目的数据库路径：~/.{project_name}/index.db。

    project_name 通常取 project_path 的目录名（basename），
    如 project_path=/Users/foo/xxx.android → ~/.xxx.android/index.db
    """
    db_path = Path.home() / f".{project_name}" / "index.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def db_path_from_project(project_path: Path) -> Path:
    """从项目路径推导数据库路径（取目录名作为 project_name）。"""
    return get_db_path(project_path.resolve().name)


# 兼容旧代码：默认 DB 路径（环境变量 ANDROID_INDEX_DB 优先，否则用旧路径）
_legacy_default = Path.home() / ".android-code-index" / "index.db"
DB_PATH = Path(os.environ.get("ANDROID_INDEX_DB", str(_legacy_default)))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# 支持索引的源码文件扩展名
SOURCE_EXTENSIONS = {
    "kotlin": {".kt"},
    "java": {".java"},
    "xml": {".xml"},
    "gradle": {".gradle", ".gradle.kts"},
}

# 所有支持的扩展名（扁平集合，用于快速过滤）
ALL_EXTENSIONS = {ext for exts in SOURCE_EXTENSIONS.values() for ext in exts}

# 需要跳过的目录名（构建产物、缓存等）
SKIP_DIRS = {
    "build", ".gradle", ".idea", "out", "intermediates",
    "generated", "__pycache__", ".git", "node_modules",
}
