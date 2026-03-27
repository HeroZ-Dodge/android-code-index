"""Android 代码知识库索引系统 - 命令行入口。"""

import click
from pathlib import Path


@click.group()
def cli() -> None:
    """Android 代码知识库索引系统"""


# ──────────────────────────────────────────────
# index 命令组
# ──────────────────────────────────────────────

@cli.group()
def index() -> None:
    """索引操作"""


@index.command("full")
@click.argument("project_path", type=click.Path(exists=True, file_okay=False))
def index_full(project_path: str) -> None:
    """对 PROJECT_PATH 执行全量索引。DB 路径自动推导为 ~/.{项目名}/index.db。"""
    from src.indexer import Indexer
    root = Path(project_path)
    indexer = Indexer.for_project(root)
    click.echo(f"DB: {indexer.db_path}")
    indexer.index_full(root)


@index.command("update")
@click.argument("project_path", type=click.Path(exists=True, file_okay=False))
def index_update(project_path: str) -> None:
    """对 PROJECT_PATH 执行增量更新索引。DB 路径自动推导为 ~/.{项目名}/index.db。"""
    from src.indexer import Indexer
    root = Path(project_path)
    indexer = Indexer.for_project(root)
    click.echo(f"DB: {indexer.db_path}")
    indexer.index_update(root)


@index.command("watch")
@click.argument("project_path", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--debounce", "-d",
    default=10.0,
    show_default=True,
    help="文件停止变化后等待多少秒再触发更新（debounce）。",
)
def index_watch(project_path: str, debounce: float) -> None:
    """监听 PROJECT_PATH 的文件变化，自动触发增量索引更新（前台运行，Ctrl-C 停止）。

    只关注 .kt / .java / .xml / .gradle / .kts 文件的新增、修改、删除。\n
    单文件 parse 失败时会跳过并保留旧索引，不影响其他文件。\n
    示例：\n
      main.py index watch /path/to/xxx.android\n
      main.py index watch /path/to/xxx.android --debounce 5
    """
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%H:%M:%S",
    )

    from src.indexer import Indexer
    from src.watcher import ProjectWatcher

    root = Path(project_path)
    indexer = Indexer.for_project(root)
    click.echo(f"DB: {indexer.db_path}")
    click.echo(f"监听目录: {root}  debounce={debounce}s")
    click.echo("按 Ctrl-C 停止...")

    watcher = ProjectWatcher(root, indexer, debounce_seconds=debounce, verbose=True)
    watcher.start()
    watcher.join()


# ──────────────────────────────────────────────
# serve 命令组
# ──────────────────────────────────────────────

@cli.group()
def serve() -> None:
    """启动服务"""


@serve.command("mcp")
@click.option(
    "--watch", "-w",
    is_flag=True,
    default=False,
    help="启动时同时开启后台文件监听，自动增量更新索引。项目路径取自 $PWD，项目名从路径末尾推导。",
)
@click.option(
    "--debounce",
    default=10.0,
    show_default=True,
    help="--watch 模式下的 debounce 秒数。",
)
def serve_mcp(watch: bool, debounce: float) -> None:
    """以 MCP Server（stdio transport）方式启动，供 Claude Code 调用。

    项目名从 $PWD 末尾自动推导（如 /path/to/xxx.android → xxx.android）。\n
    示例：\n
      main.py serve mcp\n
      main.py serve mcp --watch
    """
    import os
    project_root = Path(os.environ.get("PWD", os.getcwd()))
    project = project_root.name

    from src.config import get_db_path
    db_path = get_db_path(project)
    if not db_path.exists():
        raise click.UsageError(
            f"项目 '{project}' 的数据库不存在：{db_path}\n"
            f"请先执行：main.py index full {project_root}"
        )
    from src.server.mcp_server import run_mcp_server

    watcher_root = project_root if watch else None
    run_mcp_server(db_path=db_path, project_name=project,
                   watch_root=watcher_root, debounce_seconds=debounce)


@serve.command("http")
@click.option("--port", default=8000, show_default=True, help="监听端口")
@click.option(
    "--project", "-p",
    default=None,
    help="项目名称（对应 ~/.{project}/index.db）。不传则使用默认 DB。",
)
def serve_http(port: int, project: str | None) -> None:
    """以 HTTP API（FastAPI）方式启动。"""
    import os
    import uvicorn
    from src.server.http_api import app, set_engine
    from src.query.query_engine import QueryEngine

    project = project or os.environ.get("ANDROID_INDEX_PROJECT")
    if project:
        from src.config import get_db_path
        db_path = get_db_path(project)
        set_engine(QueryEngine(db_path=db_path))
        click.echo(f"DB: {db_path}")
    uvicorn.run(app, host="0.0.0.0", port=port)


# ──────────────────────────────────────────────
# stats 命令
# ──────────────────────────────────────────────

@cli.command("stats")
@click.option(
    "--project", "-p",
    default=None,
    help="项目名称（对应 ~/.{project}/index.db）。",
)
def stats(project: str | None) -> None:
    """显示当前数据库的索引统计信息。"""
    import os
    from src.query.query_engine import QueryEngine
    from rich.console import Console
    from rich.table import Table

    project = project or os.environ.get("ANDROID_INDEX_PROJECT")
    if project:
        from src.config import get_db_path
        db_path = get_db_path(project)
        qe = QueryEngine(db_path=db_path)
    else:
        qe = QueryEngine()

    console = Console()
    s = qe.project_stats()

    console.print(f"\n[bold]索引统计[/bold]" + (f" — {project}" if project else ""))
    console.print(f"  总文件数:    {s['total_files']}")
    console.print(f"  总符号数:    {s['total_symbols']}")
    console.print(f"  模块数:      {s['modules']}")
    console.print(f"  解析失败:    {s['parse_failures']}")
    console.print(f"  最后索引时间: {s['last_indexed'] or '—'}")

    dep_table = Table(title="模块依赖分布", show_header=True)
    dep_table.add_column("依赖类型")
    dep_table.add_column("数量", justify="right")
    dep_table.add_row("component() 依赖", str(s.get("component_dep_count", 0)))
    dep_table.add_row("project() 依赖",   str(s.get("project_dep_count", 0)))
    console.print(dep_table)


# ──────────────────────────────────────────────
# projects 命令：列出所有已索引的项目
# ──────────────────────────────────────────────

@cli.command("projects")
def list_projects() -> None:
    """列出所有已建立索引的项目。"""
    from rich.console import Console
    from rich.table import Table
    from src.config import _INDEX_ROOT
    import datetime

    console = Console()

    projects = []
    if _INDEX_ROOT.is_dir():
        for d in sorted(_INDEX_ROOT.iterdir()):
            if not d.is_dir():
                continue
            db = d / "index.db"
            if db.exists():
                projects.append((d.name, db))

    if not projects:
        console.print("[yellow]暂无已索引的项目。[/yellow]")
        console.print(f"索引目录：{_INDEX_ROOT}")
        return

    table = Table(title="已索引项目", show_header=True)
    table.add_column("项目名")
    table.add_column("DB 路径")
    table.add_column("大小")
    table.add_column("修改时间")

    for name, db in projects:
        size_mb = db.stat().st_size / 1024 / 1024
        mtime = datetime.datetime.fromtimestamp(db.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        table.add_row(name, str(db), f"{size_mb:.1f} MB", mtime)

    console.print(table)
    console.print(f"\n启动 MCP：[cyan]main.py serve mcp[/cyan]（在项目目录下执行）")


if __name__ == "__main__":
    cli()
