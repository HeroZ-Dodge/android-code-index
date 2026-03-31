"""HTTP API：基于 FastAPI，与 MCP Server 共享同一 QueryEngine。"""

from typing import Any

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from src.query.query_engine import QueryEngine

app = FastAPI(
    title="Android Code Index API",
    description="Android 项目代码知识库查询接口",
    version="1.0.0",
)

_engine: QueryEngine | None = None


def set_engine(engine: QueryEngine) -> None:
    """外部注入 QueryEngine（用于多项目支持）。"""
    global _engine
    _engine = engine


def _get_engine() -> QueryEngine:
    global _engine
    if _engine is None:
        _engine = QueryEngine()
    return _engine


# ──────────────────────────────────────────────
# 统一错误处理
# ──────────────────────────────────────────────

@app.exception_handler(Exception)
async def _global_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": type(exc).__name__, "message": str(exc)},
    )


# ──────────────────────────────────────────────
# 搜索（拆分为源码搜索 / 资源搜索）
# ──────────────────────────────────────────────

@app.get("/search/code")
def search_code(
    keyword: str,
    kind: str | None = None,
    module: str | None = None,
    use_tokens: bool = True,
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Any:
    return _get_engine().search_code(keyword=keyword, kind=kind, module=module,
                                     limit=limit, offset=offset, use_tokens=use_tokens)


@app.get("/search/resource")
def search_resource(
    keyword: str,
    kind: str | None = None,
    module: str | None = None,
    use_tokens: bool = True,
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Any:
    return _get_engine().search_resource(keyword=keyword, kind=kind, module=module,
                                         limit=limit, offset=offset, use_tokens=use_tokens)


# ──────────────────────────────────────────────
# 模块列表
# ──────────────────────────────────────────────

@app.get("/modules")
def list_modules() -> Any:
    return _get_engine().list_modules()


# ──────────────────────────────────────────────
# 符号查询
# ──────────────────────────────────────────────

@app.get("/symbols/search/class")
def search_class(
    name: str | None = None,
    module: str | None = None,
    parent_class: str | None = None,
    annotation: str | None = None,
    source_set: str | None = None,
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Any:
    return _get_engine().search_class(
        name=name, module=module, parent_class=parent_class,
        annotation=annotation, source_set=source_set,
        limit=limit, offset=offset,
    )


@app.get("/symbols/search/function")
def search_function(
    name: str | None = None,
    module: str | None = None,
    return_type: str | None = None,
    visibility: str | None = None,
    annotation: str | None = None,
    source_set: str | None = None,
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Any:
    return _get_engine().search_function(
        name=name, module=module, return_type=return_type,
        visibility=visibility, annotation=annotation, source_set=source_set,
        limit=limit, offset=offset,
    )


@app.get("/symbols/search/interface")
def search_interface(
    name: str | None = None,
    module: str | None = None,
    source_set: str | None = None,
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Any:
    return _get_engine().search_interface(
        name=name, module=module, source_set=source_set,
        limit=limit, offset=offset,
    )


@app.get("/files/{file_path:path}/symbols")
def get_file_symbols(file_path: str) -> Any:
    return _get_engine().get_file_symbols(f"/{file_path}")


@app.get("/files/{file_path:path}/imports")
def get_file_imports(file_path: str) -> Any:
    return _get_engine().get_file_imports(f"/{file_path}")


# ──────────────────────────────────────────────
# 模块
# ──────────────────────────────────────────────

@app.get("/modules/{module}/overview")
def get_module_overview(module: str) -> Any:
    return _get_engine().get_module_overview(module)


@app.get("/modules/{module}/files")
def list_module_files(
    module: str,
    source_set: str | None = None,
) -> Any:
    return _get_engine().list_module_files(module=module, source_set=source_set)


@app.get("/modules/{module}/dependencies")
def find_module_deps(
    module: str,
    scope: str | None = None,
    syntax: str | None = None,
) -> Any:
    return _get_engine().find_module_deps(module=module, scope=scope, syntax=syntax)


# ──────────────────────────────────────────────
# 类关系
# ──────────────────────────────────────────────

@app.get("/classes/{class_name}/inheritance")
def get_inheritance(class_name: str) -> Any:
    return _get_engine().get_inheritance(class_name)


@app.get("/classes/{class_name}/subclasses")
def get_subclasses(
    class_name: str,
    direct_only: bool = False,
    limit: int = Query(default=50, ge=1, le=200),
) -> Any:
    return _get_engine().get_subclasses(class_name=class_name,
                                        direct_only=direct_only, limit=limit)


@app.get("/interfaces/{interface_name}/implementations")
def get_implementations(
    interface_name: str,
    module: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
) -> Any:
    return _get_engine().get_implementations(interface_name=interface_name,
                                             module=module, limit=limit)


@app.get("/classes/{class_name}/interfaces")
def get_class_interfaces(class_name: str) -> Any:
    return _get_engine().get_class_interfaces(class_name)


@app.get("/classes/{class_name}/api")
def get_class_api(
    class_name: str,
    include_private: bool = False,
) -> Any:
    return _get_engine().get_class_api(class_name=class_name,
                                       include_private=include_private)


@app.get("/classes/{class_name}/api/full")
def get_class_api_full(
    class_name: str,
    include_private: bool = False,
) -> Any:
    return _get_engine().get_class_api_full(class_name=class_name,
                                            include_private=include_private)


@app.get("/symbols/{symbol_id}/source")
def get_symbol_source(symbol_id: int) -> Any:
    result = _get_engine().get_symbol_source(symbol_id)
    if result is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Symbol not found or has no source code")
    return result


# ──────────────────────────────────────────────
# 资源
# ──────────────────────────────────────────────

@app.get("/resources/layouts")
def find_layout(
    name: str | None = None,
    module: str | None = None,
    limit: int = Query(default=20, ge=1, le=200),
) -> Any:
    return _get_engine().find_layout(name=name, module=module, limit=limit)


@app.get("/resources/styles")
def find_style(
    name: str | None = None,
    module: str | None = None,
    limit: int = Query(default=20, ge=1, le=200),
) -> Any:
    return _get_engine().find_style(name=name, module=module, limit=limit)


@app.get("/resources/drawables")
def find_drawable(
    name: str | None = None,
    module: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
) -> Any:
    return _get_engine().find_drawable(name=name, module=module, limit=limit)


# ──────────────────────────────────────────────
# Manifest
# ──────────────────────────────────────────────

@app.get("/manifest/components")
def find_manifest_component(
    name: str | None = None,
    component_type: str | None = None,
    module: str | None = None,
    limit: int = Query(default=20, ge=1, le=200),
) -> Any:
    return _get_engine().find_manifest_component(
        name=name, component_type=component_type,
        module=module, limit=limit,
    )


# ──────────────────────────────────────────────
# 统计
# ──────────────────────────────────────────────

@app.get("/stats")
def stats() -> Any:
    return _get_engine().project_stats()


@app.get("/stats/breakdown")
def stats_breakdown() -> Any:
    return _get_engine().stats_breakdown()
