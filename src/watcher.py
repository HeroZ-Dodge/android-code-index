"""文件系统监听器：debounce + watchdog，自动触发增量索引更新。

设计原则：
- debounce：文件停止变化 N 秒后触发（默认 10s），避免编辑中途频繁更新
- 单文件 parse 失败只记录 warning，不影响其他文件（由 Indexer.index_update 保证）
- 监听只关心 .kt / .java / .xml / .gradle / .kts 文件
- 可作为独立前台进程运行，也可在 MCP server 内作为后台线程运行
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)

# 监听的文件后缀
_WATCHED_SUFFIXES = {".kt", ".java", ".xml", ".gradle", ".kts"}


class _DebouncedHandler(FileSystemEventHandler):
    """收到文件变化事件后，debounce N 秒再触发回调。"""

    def __init__(
        self,
        callback: Callable[[], None],
        debounce_seconds: float = 10.0,
    ) -> None:
        super().__init__()
        self._callback = callback
        self._debounce = debounce_seconds
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def _is_relevant(self, path: str) -> bool:
        return Path(path).suffix in _WATCHED_SUFFIXES

    def _schedule(self) -> None:
        """重置 debounce 计时器。"""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce, self._fire)
            self._timer.daemon = True
            self._timer.start()

    def _fire(self) -> None:
        with self._lock:
            self._timer = None
        try:
            self._callback()
        except Exception:
            logger.exception("索引更新回调失败")

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self._is_relevant(event.src_path):
            self._schedule()

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self._is_relevant(event.src_path):
            self._schedule()

    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self._is_relevant(event.src_path):
            self._schedule()

    def on_moved(self, event: FileSystemEvent) -> None:
        # 移动/重命名：src 或 dest 任一符合条件即触发
        src_ok = self._is_relevant(event.src_path)
        dest_ok = hasattr(event, "dest_path") and self._is_relevant(event.dest_path)
        if not event.is_directory and (src_ok or dest_ok):
            self._schedule()

    def cancel(self) -> None:
        """停止正在等待的 debounce 计时器。"""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None


class ProjectWatcher:
    """监听 Android 项目目录，自动触发增量索引更新。

    用法（独立前台运行）：
        watcher = ProjectWatcher(project_root, indexer, debounce_seconds=3.0)
        watcher.start()   # 启动后台 Observer 线程
        watcher.join()    # 阻塞直到 KeyboardInterrupt / stop()

    用法（MCP server 内后台运行）：
        watcher = ProjectWatcher(project_root, indexer, on_updated=reload_engine)
        watcher.start()
        # ... MCP server 正常运行
        watcher.stop()
    """

    def __init__(
        self,
        project_root: Path,
        indexer,                          # src.indexer.Indexer
        debounce_seconds: float = 10.0,
        on_updated: Callable[[], None] | None = None,
        verbose: bool = True,
    ) -> None:
        self._project_root = project_root
        self._indexer = indexer
        self._on_updated = on_updated
        self._verbose = verbose

        self._observer = Observer()
        self._handler = _DebouncedHandler(
            callback=self._do_update,
            debounce_seconds=debounce_seconds,
        )
        self._observer.schedule(self._handler, str(project_root), recursive=True)

    def _do_update(self) -> None:
        t0 = time.perf_counter()
        if self._verbose:
            logger.info("[watcher] 检测到文件变化，开始增量更新…")
        try:
            result = self._indexer.index_update(self._project_root, silent=not self._verbose)
            elapsed = round(time.perf_counter() - t0, 2)
            if self._verbose:
                updated = result.get("updated_files", 0)
                deleted = result.get("deleted_files", 0)
                skipped = result.get("skipped", 0)
                logger.info(
                    f"[watcher] 更新完成：{updated} 个文件已重索引，"
                    f"{deleted} 个已删除，{skipped} 个跳过（parse 失败），耗时 {elapsed}s"
                )
        except Exception:
            logger.exception("[watcher] 增量更新异常")
            return

        # 通知外部（如 MCP server 重载 QueryEngine）
        if self._on_updated:
            try:
                self._on_updated()
            except Exception:
                logger.exception("[watcher] on_updated 回调异常")

    def start(self) -> None:
        """启动后台监听线程（非阻塞）。"""
        self._observer.start()
        if self._verbose:
            logger.info(f"[watcher] 开始监听：{self._project_root}  debounce={self._handler._debounce}s")

    def stop(self) -> None:
        """停止监听。"""
        self._handler.cancel()
        self._observer.stop()
        self._observer.join()
        if self._verbose:
            logger.info("[watcher] 已停止")

    def join(self) -> None:
        """阻塞当前线程，直到收到 KeyboardInterrupt 后优雅退出。"""
        try:
            while self._observer.is_alive():
                self._observer.join(timeout=1.0)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
