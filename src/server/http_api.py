"""HTTP API：基于 FastAPI，与 MCP Server 共享同一 QueryEngine。"""

from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from src.query.query_engine import QueryEngine

app = FastAPI(
    title="Android Code Index API",
    description="Android 项目代码知识库查询接口",
    version="1.0.0",
)

_engine: QueryEngine | None = None


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
# 搜索
# ──────────────────────────────────────────────

@app.get("/search")
def search(
    keyword: str,
    kind: str | None = None,
    module: str | None = None,
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Any:
    return _get_engine().search(keyword=keyword, kind=kind, module=module,
                                limit=limit, offset=offset)


# ──────────────────────────────────────────────
# 模块列表（Vue UI 扩展）
# ──────────────────────────────────────────────

@app.get("/modules")
def list_modules() -> Any:
    return _get_engine().list_modules()


# ──────────────────────────────────────────────
# 符号查询
# ──────────────────────────────────────────────

@app.get("/symbols/class")
def find_class(
    name: str | None = None,
    module: str | None = None,
    parent_class: str | None = None,
    annotation: str | None = None,
    source_set: str | None = None,
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Any:
    return _get_engine().find_class(
        name=name, module=module, parent_class=parent_class,
        annotation=annotation, source_set=source_set,
        limit=limit, offset=offset,
    )


@app.get("/symbols/function")
def find_function(
    name: str | None = None,
    module: str | None = None,
    return_type: str | None = None,
    visibility: str | None = None,
    annotation: str | None = None,
    source_set: str | None = None,
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Any:
    return _get_engine().find_function(
        name=name, module=module, return_type=return_type,
        visibility=visibility, annotation=annotation, source_set=source_set,
        limit=limit, offset=offset,
    )


@app.get("/symbols/interface")
def find_interface(
    name: str | None = None,
    module: str | None = None,
    source_set: str | None = None,
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Any:
    return _get_engine().find_interface(
        name=name, module=module, source_set=source_set,
        limit=limit, offset=offset,
    )


@app.get("/files/{file_path:path}/symbols")
def get_file_symbols(file_path: str) -> Any:
    # file_path 来自 URL，需要还原为绝对路径（调用方应以 /path/to/file 形式传入）
    return _get_engine().get_file_symbols(f"/{file_path}")


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


@app.get("/classes/{class_name}/api")
def get_class_api(
    class_name: str,
    include_private: bool = False,
) -> Any:
    return _get_engine().get_class_api(class_name=class_name,
                                       include_private=include_private)


# ──────────────────────────────────────────────
# 资源
# ──────────────────────────────────────────────

@app.get("/resources/layouts")
def find_layout(
    name: str | None = None,
    module: str | None = None,
    view_id: str | None = None,
    limit: int = Query(default=20, ge=1, le=200),
) -> Any:
    return _get_engine().find_layout(name=name, module=module,
                                     view_id=view_id, limit=limit)


@app.get("/resources/strings")
def find_string(
    key: str | None = None,
    value: str | None = None,
    module: str | None = None,
    limit: int = Query(default=20, ge=1, le=200),
) -> Any:
    return _get_engine().find_string(key=key, value=value,
                                     module=module, limit=limit)


@app.get("/resources/styles")
def find_style(
    name: str | None = None,
    module: str | None = None,
    limit: int = Query(default=20, ge=1, le=200),
) -> Any:
    return _get_engine().find_style(name=name, module=module, limit=limit)


@app.get("/resources/colors")
def find_color(
    name: str | None = None,
    value: str | None = None,
    module: str | None = None,
    limit: int = Query(default=20, ge=1, le=200),
) -> Any:
    return _get_engine().find_color(name=name, value=value,
                                    module=module, limit=limit)


@app.get("/resources/dimens")
def find_dimen(
    name: str | None = None,
    value: str | None = None,
    module: str | None = None,
    limit: int = Query(default=20, ge=1, le=200),
) -> Any:
    return _get_engine().find_dimen(name=name, value=value,
                                    module=module, limit=limit)


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


# ──────────────────────────────────────────────
# Web UI
# ──────────────────────────────────────────────

_UI_BASE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Android Code Index</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f5f7fa;color:#1a1a2e}
nav{background:#1a1a2e;padding:12px 24px;display:flex;gap:24px;align-items:center}
nav a{color:#a8b4d0;text-decoration:none;font-size:14px;padding:6px 12px;border-radius:6px;transition:all .2s}
nav a:hover,nav a.active{background:#2d3561;color:#fff}
nav .brand{color:#fff;font-weight:700;font-size:16px;margin-right:16px}
.container{max-width:1200px;margin:0 auto;padding:24px}
.card{background:#fff;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,.08);padding:24px;margin-bottom:20px}
.stat-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:16px;margin-bottom:24px}
.stat{background:#fff;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.08);text-align:center}
.stat .num{font-size:32px;font-weight:700;color:#2d3561}
.stat .label{font-size:13px;color:#6b7280;margin-top:4px}
input,select{width:100%;padding:10px 14px;border:1px solid #d1d5db;border-radius:8px;font-size:14px;outline:none;transition:border .2s}
input:focus,select:focus{border-color:#2d3561}
.row{display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap}
.row>*{flex:1;min-width:160px}
button{padding:10px 20px;background:#2d3561;color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:14px;transition:background .2s}
button:hover{background:#1a1a2e}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:#f8f9fc;padding:10px 14px;text-align:left;font-weight:600;color:#374151;border-bottom:2px solid #e5e7eb}
td{padding:10px 14px;border-bottom:1px solid #f0f0f0;word-break:break-all}
tr:hover td{background:#f8f9fc}
.tag{display:inline-block;padding:2px 8px;border-radius:99px;font-size:11px;font-weight:600}
.tag-class{background:#dbeafe;color:#1d4ed8}
.tag-interface{background:#d1fae5;color:#065f46}
.tag-function{background:#fef3c7;color:#92400e}
.tag-property{background:#ede9fe;color:#5b21b6}
.tag-layout{background:#fce7f3;color:#9d174d}
.tag-string_res{background:#e0f2fe;color:#0c4a6e}
.tag-color_res,.tag-dimen_res,.tag-style{background:#f0fdf4;color:#14532d}
.tag-manifest_component{background:#fef9c3;color:#713f12}
.tag-object{background:#f3e8ff;color:#6b21a8}
.empty{color:#9ca3af;font-style:italic;padding:32px;text-align:center}
h2{font-size:18px;font-weight:700;margin-bottom:16px;color:#1a1a2e}
.mod-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}
.mod-card{background:#f8f9fc;border-radius:8px;padding:16px;border:1px solid #e5e7eb;cursor:pointer;transition:all .2s}
.mod-card:hover{border-color:#2d3561;background:#eef2ff}
.mod-card .name{font-weight:600;font-size:14px;margin-bottom:8px;color:#2d3561}
.mod-card .meta{font-size:12px;color:#6b7280}
.loading{color:#6b7280;padding:16px;text-align:center}
</style>
</head>
<body>
<nav>
  <span class="brand">Android Code Index</span>
  <a href="/ui" id="nav-dashboard">仪表板</a>
  <a href="/ui/search" id="nav-search">全文搜索</a>
  <a href="/ui/modules" id="nav-modules">模块浏览</a>
  <a href="/ui/symbols" id="nav-symbols">符号列表</a>
</nav>
<div class="container" id="app">加载中...</div>
<script>
const BASE = '';
async function api(path){const r=await fetch(BASE+path);return r.json();}
function tag(kind){return `<span class="tag tag-${kind}">${kind}</span>`}
function esc(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;')}
function page(){return location.pathname}
document.querySelectorAll('nav a').forEach(a=>{
  if(a.getAttribute('href')===page()||
     (a.getAttribute('href')==='/ui'&&page()==='/ui/')){
    a.classList.add('active');
  }
});
</script>
"""


@app.get("/ui", response_class=HTMLResponse)
@app.get("/ui/", response_class=HTMLResponse)
async def ui_dashboard() -> str:
    return _UI_BASE + """
<script>
(async()=>{
  const s = await api('/stats');
  document.getElementById('app').innerHTML = `
    <div class="stat-grid">
      <div class="stat"><div class="num">${s.total_files}</div><div class="label">文件数</div></div>
      <div class="stat"><div class="num">${s.total_symbols}</div><div class="label">符号数</div></div>
      <div class="stat"><div class="num">${s.modules}</div><div class="label">模块数</div></div>
      <div class="stat"><div class="num">${s.parse_failures}</div><div class="label">解析失败</div></div>
      <div class="stat"><div class="num">${s.component_dep_count}</div><div class="label">component() 依赖</div></div>
      <div class="stat"><div class="num">${s.project_dep_count}</div><div class="label">project() 依赖</div></div>
    </div>
    <div class="card">
      <h2>最后索引时间</h2>
      <p style="color:#6b7280">${s.last_indexed || '—'}</p>
    </div>
  `;
})();
</script>
</body></html>
"""


@app.get("/ui/search", response_class=HTMLResponse)
async def ui_search() -> str:
    return _UI_BASE + """
<script>
async function doSearch(){
  const kw=document.getElementById('kw').value.trim();
  if(!kw)return;
  const kind=document.getElementById('kind').value;
  const mod=document.getElementById('mod').value.trim();
  const limit=document.getElementById('limit').value;
  let url=`/search?keyword=${encodeURIComponent(kw)}&limit=${limit}`;
  if(kind)url+=`&kind=${kind}`;
  if(mod)url+=`&module=${encodeURIComponent(mod)}`;
  document.getElementById('results').innerHTML='<div class="loading">搜索中...</div>';
  const data=await api(url);
  if(!data.items || !data.items.length){document.getElementById('results').innerHTML='<div class="empty">无结果</div>';return;}
  document.getElementById('results').innerHTML=`
    <p style="color:#6b7280;font-size:13px;margin-bottom:12px">共 ${data.total} 条结果</p>
    <table>
      <thead><tr><th>类型</th><th>名称</th><th>qualified_name</th><th>模块</th><th>行号</th></tr></thead>
      <tbody>${data.items.map(r=>`<tr>
        <td>${tag(r.kind)}</td>
        <td>${esc(r.name)}</td>
        <td style="font-family:monospace;font-size:12px">${esc(r.qualified_name)}</td>
        <td>${esc(r.module)}</td>
        <td>${r.line_number||'—'}</td>
      </tr>`).join('')}</tbody>
    </table>`;
}
document.getElementById('app').innerHTML=`
  <div class="card">
    <h2>全文搜索</h2>
    <div class="row">
      <input id="kw" placeholder="关键词" onkeydown="if(event.key==='Enter')doSearch()">
      <select id="kind" style="max-width:160px">
        <option value="">全部类型</option>
        <option>class</option><option>interface</option><option>function</option>
        <option>property</option><option>object</option><option>layout</option>
        <option>view_id</option><option>string_res</option><option>color_res</option>
        <option>dimen_res</option><option>style</option><option>manifest_component</option>
      </select>
    </div>
    <div class="row">
      <input id="mod" placeholder="模块过滤（如 :app）">
      <select id="limit" style="max-width:100px">
        <option>20</option><option>50</option><option>100</option><option>200</option>
      </select>
      <button onclick="doSearch()" style="max-width:100px">搜索</button>
    </div>
  </div>
  <div class="card"><div id="results"><div class="empty">输入关键词后按回车或点击搜索</div></div></div>
`;
</script></body></html>
"""


@app.get("/ui/modules", response_class=HTMLResponse)
async def ui_modules() -> str:
    return _UI_BASE + """
<script>
async function loadModuleDetail(mod){
  const o=await api(`/modules/${encodeURIComponent(mod)}/overview`);
  const deps=await api(`/modules/${encodeURIComponent(mod)}/dependencies`);
  document.getElementById('detail').innerHTML=`
    <div class="card">
      <h2>${esc(mod)}</h2>
      <div class="stat-grid" style="margin-bottom:16px">
        <div class="stat"><div class="num">${o.files}</div><div class="label">文件数</div></div>
        <div class="stat"><div class="num">${o.sdk_classes}</div><div class="label">SDK 类</div></div>
        <div class="stat"><div class="num">${o.impl_classes}</div><div class="label">impl 类</div></div>
        <div class="stat"><div class="num">${o.interfaces}</div><div class="label">接口</div></div>
        <div class="stat"><div class="num">${o.functions}</div><div class="label">函数</div></div>
      </div>
      <h2>直接依赖（${deps.direct.length} 个）</h2>
      ${deps.direct.length?`<table>
        <thead><tr><th>依赖模块</th><th>类型</th><th>scope</th></tr></thead>
        <tbody>${deps.direct.map(d=>`<tr>
          <td>${esc(d.depends_on)}</td>
          <td><span class="tag tag-${d.syntax==='component'?'class':'function'}">${esc(d.syntax)}</span></td>
          <td>${esc(d.dependency_scope)}</td>
        </tr>`).join('')}</tbody>
      </table>`:'<div class="empty">无直接依赖</div>'}
    </div>`;
}
(async()=>{
  const data=await api('/stats');
  // 获取所有模块
  const mods=await api('/symbols/class?limit=1&offset=0');
  const modSet=new Set();
  // 用 files 接口获取模块列表
  const files=await api('/symbols/class?limit=200');
  files.forEach(f=>modSet.add(f.module));
  // 也读 function
  const fns=await api('/symbols/function?limit=200');
  fns.forEach(f=>modSet.add(f.module));

  const modList=[...modSet].sort();
  document.getElementById('app').innerHTML=`
    <div style="display:flex;gap:20px;align-items:flex-start">
      <div style="width:260px;flex-shrink:0">
        <div class="card" style="padding:12px">
          <h2 style="margin-bottom:12px">模块列表</h2>
          <div class="mod-grid" style="grid-template-columns:1fr">
            ${modList.map(m=>`<div class="mod-card" onclick="loadModuleDetail('${esc(m)}')">
              <div class="name">${esc(m)}</div>
            </div>`).join('')}
          </div>
        </div>
      </div>
      <div style="flex:1" id="detail">
        <div class="card"><div class="empty">点击左侧模块查看详情</div></div>
      </div>
    </div>`;
})();
</script></body></html>
"""


@app.get("/ui/symbols", response_class=HTMLResponse)
async def ui_symbols() -> str:
    return _UI_BASE + """
<script>
let currentPage=0, currentKind='class', currentMod='', pageSize=50;
async function load(){
  const offset=currentPage*pageSize;
  let url=`/symbols/${currentKind}?limit=${pageSize}&offset=${offset}`;
  if(currentMod)url+=`&module=${encodeURIComponent(currentMod)}`;
  document.getElementById('tbody').innerHTML='<tr><td colspan="5" class="loading">加载中...</td></tr>';
  const data=await api(url);
  if(!data.length){
    document.getElementById('tbody').innerHTML='<tr><td colspan="5" class="empty">无数据</td></tr>';
    return;
  }
  document.getElementById('tbody').innerHTML=data.map(r=>`<tr>
    <td>${tag(r.kind)}</td>
    <td>${esc(r.name)}</td>
    <td style="font-family:monospace;font-size:11px;max-width:400px">${esc(r.qualified_name)}</td>
    <td>${esc(r.module)}</td>
    <td>${esc(r.visibility||'')}</td>
  </tr>`).join('');
  document.getElementById('pageinfo').textContent=`第 ${currentPage+1} 页`;
}
document.getElementById('app').innerHTML=`
  <div class="card">
    <h2>符号浏览</h2>
    <div class="row">
      <select id="kind-sel" style="max-width:160px" onchange="currentKind=this.value;currentPage=0;load()">
        <option value="class">类 (class)</option>
        <option value="interface">接口 (interface)</option>
        <option value="function">函数 (function)</option>
      </select>
      <input id="mod-input" placeholder="模块过滤（如 :app）" onkeydown="if(event.key==='Enter'){currentMod=this.value.trim();currentPage=0;load()}">
      <button onclick="currentMod=document.getElementById('mod-input').value.trim();currentPage=0;load()">过滤</button>
    </div>
  </div>
  <div class="card">
    <table>
      <thead><tr><th>类型</th><th>名称</th><th>qualified_name</th><th>模块</th><th>可见性</th></tr></thead>
      <tbody id="tbody"><tr><td colspan="5" class="loading">加载中...</td></tr></tbody>
    </table>
    <div style="margin-top:16px;display:flex;gap:12px;align-items:center">
      <button onclick="if(currentPage>0){currentPage--;load()}">上一页</button>
      <span id="pageinfo">第 1 页</span>
      <button onclick="currentPage++;load()">下一页</button>
    </div>
  </div>
`;
load();
</script></body></html>
"""


# ──────────────────────────────────────────────
# Vue SPA 静态文件服务（生产模式）
# ──────────────────────────────────────────────

_DIST_DIR = Path(__file__).parent.parent.parent / "ui" / "dist"

if _DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=_DIST_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> FileResponse:
        """SPA fallback：所有非 API 路径均返回 index.html。"""
        index = _DIST_DIR / "index.html"
        return FileResponse(index)
