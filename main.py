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


# ──────────────────────────────────────────────
# serve 命令组
# ──────────────────────────────────────────────

@cli.group()
def serve() -> None:
    """启动服务"""


@serve.command("mcp")
@click.option(
    "--project", "-p",
    default=None,
    help="项目名称（对应 ~/.{project}/index.db）。"
         "不传时优先读取环境变量 ANDROID_INDEX_PROJECT，仍无则报错。",
)
def serve_mcp(project: str | None) -> None:
    """以 MCP Server（stdio transport）方式启动，供 Claude Code 调用。

    示例：\n
      main.py serve mcp --project xxx.android\n
      ANDROID_INDEX_PROJECT=xxx.android main.py serve mcp
    """
    import os
    project = project or os.environ.get("ANDROID_INDEX_PROJECT")
    if not project:
        raise click.UsageError(
            "必须通过 --project 或环境变量 ANDROID_INDEX_PROJECT 指定项目名称。\n"
            "示例：main.py serve mcp --project xxx.android"
        )
    from src.config import get_db_path
    db_path = get_db_path(project)
    if not db_path.exists():
        raise click.UsageError(
            f"项目 '{project}' 的数据库不存在：{db_path}\n"
            f"请先执行：main.py index full <project_path>"
        )
    from src.server.mcp_server import run_mcp_server
    run_mcp_server(db_path=db_path, project_name=project)


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
    import datetime

    console = Console()
    home = Path.home()

    # 已知系统/工具隐藏目录，排除
    _SKIP_DIRS = {"Trash", "android-code-index", "DS_Store"}

    projects = []
    for d in sorted(home.iterdir()):
        if not d.is_dir() or not d.name.startswith("."):
            continue
        project_name = d.name[1:]  # 去掉开头的 .
        if project_name in _SKIP_DIRS:
            continue
        db = d / "index.db"
        if db.exists():
            projects.append((project_name, db))

    if not projects:
        console.print("[yellow]暂无已索引的项目。[/yellow]")
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
    console.print(f"\n启动 MCP：[cyan]main.py serve mcp --project <项目名>[/cyan]")


if __name__ == "__main__":
    cli()
