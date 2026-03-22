"""环境验证脚本：逐项检查运行依赖，输出 [OK]/[FAIL]，退出码 0=全通过，1=任意失败。"""

import sys


def check(label: str, fn) -> bool:
    try:
        fn()
        print(f"[OK]   {label}")
        return True
    except Exception as e:
        print(f"[FAIL] {label}: {e}")
        return False


def _check_python_version() -> None:
    major, minor = sys.version_info[:2]
    if (major, minor) < (3, 11):
        raise RuntimeError(f"需要 Python >= 3.11，当前 {major}.{minor}")


def _check_tree_sitter() -> None:
    import tree_sitter  # noqa: F401


def _check_kotlin_grammar() -> None:
    """优先尝试 tree_sitter_kotlin，失败则尝试 tree_sitter_languages。"""
    try:
        import tree_sitter_kotlin  # noqa: F401
        return
    except ImportError:
        pass
    # 降级方案
    from tree_sitter_languages import get_language  # noqa: F401
    get_language("kotlin")


def _check_fts5() -> None:
    import sqlite3
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute(
            "CREATE VIRTUAL TABLE t USING fts5(content)"
        )
    finally:
        conn.close()


def _check_mcp() -> None:
    import mcp  # noqa: F401


def _check_fastapi() -> None:
    import fastapi  # noqa: F401


def main() -> None:
    results = [
        check("Python >= 3.11",          _check_python_version),
        check("tree_sitter 可 import",   _check_tree_sitter),
        check("Kotlin grammar 可加载",   _check_kotlin_grammar),
        check("SQLite FTS5 可用",        _check_fts5),
        check("mcp 可 import",           _check_mcp),
        check("fastapi 可 import",       _check_fastapi),
    ]
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
