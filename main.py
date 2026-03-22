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
    """对 PROJECT_PATH 执行全量索引。"""
    from src.indexer import Indexer
    indexer = Indexer()
    indexer.index_full(Path(project_path))


@index.command("update")
@click.argument("project_path", type=click.Path(exists=True, file_okay=False))
def index_update(project_path: str) -> None:
    """对 PROJECT_PATH 执行增量更新索引。"""
    from src.indexer import Indexer
    indexer = Indexer()
    indexer.index_update(Path(project_path))


# ──────────────────────────────────────────────
# serve 命令组
# ──────────────────────────────────────────────

@cli.group()
def serve() -> None:
    """启动服务"""


@serve.command("mcp")
def serve_mcp() -> None:
    """以 MCP Server（stdio transport）方式启动，供 Claude Desktop 调用。"""
    from src.server.mcp_server import run_mcp_server
    run_mcp_server()


@serve.command("http")
@click.option("--port", default=8000, show_default=True, help="监听端口")
def serve_http(port: int) -> None:
    """以 HTTP API（FastAPI）方式启动。"""
    import uvicorn
    from src.server.http_api import app
    uvicorn.run(app, host="0.0.0.0", port=port)


# ──────────────────────────────────────────────
# stats 命令
# ──────────────────────────────────────────────

@cli.command("stats")
def stats() -> None:
    """显示当前数据库的索引统计信息。"""
    from src.query.query_engine import QueryEngine
    from rich.console import Console
    from rich.table import Table

    console = Console()
    qe = QueryEngine()
    s = qe.project_stats()

    console.print(f"\n[bold]索引统计[/bold]")
    console.print(f"  总文件数:    {s['total_files']}")
    console.print(f"  总符号数:    {s['total_symbols']}")
    console.print(f"  模块数:      {s['modules']}")
    console.print(f"  解析失败:    {s['parse_failures']}")
    console.print(f"  最后索引时间: {s['last_indexed'] or '—'}")

    # 依赖分布
    dep_table = Table(title="模块依赖分布", show_header=True)
    dep_table.add_column("依赖类型")
    dep_table.add_column("数量", justify="right")
    dep_table.add_row("component() 依赖", str(s.get("component_dep_count", 0)))
    dep_table.add_row("project() 依赖",   str(s.get("project_dep_count", 0)))
    console.print(dep_table)


if __name__ == "__main__":
    cli()
