"""全局配置：数据库路径、文件类型过滤规则。"""

import os
from pathlib import Path

# 数据库路径：优先读取环境变量，默认 ~/.android-code-index/index.db
_default_db = Path.home() / ".android-code-index" / "index.db"
DB_PATH = Path(os.environ.get("ANDROID_INDEX_DB", str(_default_db)))

# 确保数据库目录存在
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
