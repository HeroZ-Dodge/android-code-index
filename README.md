# Android Code Index

Android 项目代码结构化索引系统，提供高效的代码搜索和查询能力，支持 MCP Server 和 HTTP API 两种访问方式。

## 功能特性

- **全文搜索**：基于 FTS5 的全文搜索，支持多关键词、前缀匹配、精确匹配、驼峰分词
- **符号查询**：类、接口、函数、属性等符号的快速查找
- **关系分析**：继承链、子类、接口实现等关系查询
- **资源搜索**：布局、字符串、颜色、样式等 Android 资源查询
- **模块浏览**：模块统计、文件列表、依赖关系分析
- **实时监听**：文件变化自动触发增量索引更新

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户界面层                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐    │
│  │ Claude Code │  │  HTTP Client │  │   Vue 3 UI (可选)   │    │
│  │   (MCP)     │  │   (REST API) │  │                     │    │
│  └──────┬──────┘  └──────┬───────┘  └──────────┬──────────┘    │
└─────────┼────────────────┼─────────────────────┼────────────────┘
          │                │                     │
          ▼                ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                        服务层                                    │
│  ┌─────────────────────────┐  ┌─────────────────────────────┐  │
│  │    MCP Server           │  │      HTTP API (FastAPI)     │  │
│  │  (stdio transport)      │  │      (0.0.0.0:8000)         │  │
│  └───────────┬─────────────┘  └──────────────┬──────────────┘  │
└──────────────┼────────────────────────────────┼─────────────────┘
               │                                │
               └────────────┬───────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      查询引擎 (QueryEngine)                      │
│            封装所有 SQLite 查询逻辑，提供统一的查询接口                       │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      数据存储层                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    SQLite Database                         │  │
│  │  ┌────────────┐  ┌─────────────┐  ┌──────────────────┐   │  │
│  │  │  symbols   │  │    files    │  │  file_imports    │   │  │
│  │  ├────────────┤  ├─────────────┤  ├──────────────────┤   │  │
│  │  │ symbols_fts│  │module_deps  │  │  schema_version  │   │  │
│  │  └────────────┘  └─────────────┘  └──────────────────┘   │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             ▲
                             │
┌────────────────────────────┴─────────────────────────────────────┐
│                      索引层                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Indexer     │  │ ProjectWatcher │  │    Parsers          │  │
│  │ (全量/增量)  │  │  (文件监听)    │  │  Kotlin/Java/XML    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             ▲
                             │
┌────────────────────────────┴─────────────────────────────────────┐
│                      源码文件                                    │
│         Android 项目目录 (.kt / .java / .xml / .gradle)           │
└─────────────────────────────────────────────────────────────────┘
```

### 核心组件

| 组件 | 文件 | 说明 |
|------|------|------|
| **命令行入口** | `main.py` | 基于 Click 的 CLI，提供 index/serve/stats 等命令 |
| **索引器** | `src/indexer.py` | 全量索引和增量更新，批量写入优化 |
| **文件扫描器** | `src/file_scanner.py` | 扫描项目文件，识别模块和 source_set |
| **解析器** | `src/parsers/` | Kotlin/Java/XML/Gradle 解析，提取符号和依赖 |
| **查询引擎** | `src/query/query_engine.py` | 封装所有 SQLite 查询逻辑 |
| **数据库** | `src/database.py` | SQLite schema 初始化，FTS5 虚拟表和触发器 |
| **MCP Server** | `src/server/mcp_server.py` | 通过 MCP 协议暴露查询工具 |
| **HTTP API** | `src/server/http_api.py` | FastAPI REST 接口 |
| **文件监听** | `src/watcher.py` | 监听文件变化，自动触发增量更新 |

### 数据库结构

| 表名 | 说明 |
|------|------|
| `symbols` | 符号表：类、接口、函数、属性等 |
| `symbols_fts` | FTS5 全文搜索虚拟表 |
| `files` | 文件表：记录文件路径、模块、类型、索引状态 |
| `file_imports` | 文件导入表：记录每个文件的 import 全限定名 |
| `module_dependencies` | 模块依赖表：记录模块间的依赖关系 |
| `schema_version` | Schema 版本表 |

## 快速开始

### 安装依赖

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 代码索引

```bash
# 全量索引（首次使用）
python main.py index full /path/to/your/android/project

# 增量更新索引
python main.py index update /path/to/your/android/project

# 监听文件变化，自动更新索引（前台运行，Ctrl-C 停止）
python main.py index watch /path/to/your/android/project
python main.py index watch /path/to/your/android/project --debounce 5
```

数据库路径规则：`~/.android-code-index/{项目名}/index.db`

### 启动服务

```bash
# 启动 MCP Server（供 Claude Code 调用）
python main.py serve mcp

# 启动 MCP Server（带后台文件监听，自动更新索引）
python main.py serve mcp --watch

# 启动 HTTP API 服务
python main.py serve http --port 8000

# 指定项目启动 HTTP API
python main.py serve http --project my-android-project
```

### 查看统计

```bash
# 显示当前索引统计信息
python main.py stats

# 指定项目
python main.py stats --project my-android-project

# 列出所有已索引的项目
python main.py projects
```

## 命令行接口 (CLI)

### index 命令组

| 命令 | 说明 | 示例 |
|------|------|------|
| `index full <project_path>` | 全量索引 | `main.py index full /path/to/project` |
| `index update <project_path>` | 增量更新 | `main.py index update /path/to/project` |
| `index watch <project_path>` | 监听变化 | `main.py index watch /path/to/project -d 5` |

### serve 命令组

| 命令 | 说明 | 示例 |
|------|------|------|
| `serve mcp` | 启动 MCP Server | `main.py serve mcp --watch` |
| `serve http` | 启动 HTTP API | `main.py serve http --port 8000` |

### 其他命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `stats` | 显示统计 | `main.py stats --project xxx` |
| `projects` | 列出项目 | `main.py projects` |

## HTTP API 接口说明

### 搜索接口

| 端点 | 说明 | 参数 |
|------|------|------|
| `GET /search/code` | 搜索代码符号 | `keyword`, `kind`, `module`, `limit`, `use_tokens` |
| `GET /search/resource` | 搜索资源 | `keyword`, `kind`, `module`, `limit` |

### 符号查询

| 端点 | 说明 |
|------|------|
| `GET /symbols/search/class` | 查找类（支持 name, parent_class, annotation 过滤） |
| `GET /symbols/search/function` | 查找函数（支持 name, return_type, visibility 过滤） |
| `GET /symbols/search/interface` | 查找接口 |
| `GET /files/{file_path}/symbols` | 获取文件的所有符号 |
| `GET /files/{file_path}/imports` | 获取文件的所有 import |

### 类关系

| 端点 | 说明 |
|------|------|
| `GET /classes/{class_name}/inheritance` | 获取继承链 |
| `GET /classes/{class_name}/subclasses` | 获取子类（`direct_only` 参数控制是否递归） |
| `GET /interfaces/{interface_name}/implementations` | 获取接口实现类 |
| `GET /classes/{class_name}/api` | 获取类成员摘要（精简版） |
| `GET /classes/{class_name}/api/full` | 获取类成员完整信息（含源码） |
| `GET /symbols/{symbol_id}/source` | 获取单个符号的源码 |

### 资源查询

| 端点 | 说明 |
|------|------|
| `GET /resources/layouts` | 查找布局文件 |
| `GET /resources/styles` | 查找样式资源 |
| `GET /resources/drawables` | 查找 drawable 资源 |

### 模块接口

| 端点 | 说明 |
|------|------|
| `GET /modules` | 列出所有模块 |
| `GET /modules/{module}/overview` | 获取模块统计概览 |
| `GET /modules/{module}/files` | 获取模块文件列表 |
| `GET /modules/{module}/dependencies` | 获取模块依赖（直接 + 间接） |

### Manifest

| 端点 | 说明 |
|------|------|
| `GET /manifest/components` | 查找四大组件（activity/service/receiver/provider） |

### 统计

| 端点 | 说明 |
|------|------|
| `GET /stats` | 获取项目整体统计 |
| `GET /stats/breakdown` | 获取分类统计（按 kind/语言/模块排名） |

### 使用示例

```bash
# 全文搜索
curl "http://localhost:8000/search/code?keyword=FeedFragment&limit=20"

# 查找类
curl "http://localhost:8000/symbols/search/class?name=BaseActivity&module=:app"

# 查找函数
curl "http://localhost:8000/symbols/search/function?name=onCreate&visibility=public"

# 获取继承链
curl "http://localhost:8000/classes/Activity/inheritance"

# 获取子类
curl "http://localhost:8000/classes/BaseFragment/subclasses?direct_only=false"

# 获取类成员 API（精简版）
curl "http://localhost:8000/classes/FeedViewModel/api"

# 获取单个方法源码（先用上一个接口获取 symbol_id）
curl "http://localhost:8000/symbols/123/source"

# 获取模块依赖
curl "http://localhost:8000/modules/:compfeed/dependencies"
```

## MCP Server 使用指南

### 在 Claude Code 中注册 MCP Server

#### 方法 1：临时启动（当前会话）

```bash
# 在项目目录下执行
cd /path/to/android-project
python /path/to/android-code-index/main.py serve mcp
```

然后在另一个终端启动 Claude Code：

```bash
claude
```

#### 方法 2：在 Claude Code 中配置 MCP Server

编辑 `~/.claude/settings.json`，添加 MCP 服务器配置：

```json
{
  "mcpServers": {
    "android-index": {
      "command": "python",
      "args": [
        "/path/to/android-code-index/main.py",
        "serve",
        "mcp"
      ],
      "cwd": "/path/to/android-project"
    }
  }
}
```

#### 方法 3：在项目内配置（推荐团队使用）

在项目根目录创建 `.claude/settings.json`：

```json
{
  "mcpServers": {
    "android-index": {
      "command": "python",
      "args": [
        "/path/to/android-code-index/main.py",
        "serve",
        "mcp"
      ],
      "cwd": "$workspaceFolder"
    }
  }
}
```

### MCP 工具列表

| 工具名 | 说明 |
|--------|------|
| `search_code` | 全文搜索代码符号 |
| `search_resource` | 全文搜索资源 |
| `search_class` | 按条件查找类 |
| `search_function` | 按条件查找函数 |
| `search_interface` | 按条件查找接口 |
| `get_file_symbols` | 获取文件的所有符号 |
| `get_file_imports` | 获取文件的所有 import |
| `get_module_overview` | 获取模块统计概览 |
| `get_inheritance` | 获取继承链 |
| `get_subclasses` | 获取子类 |
| `get_implementations` | 获取接口实现类 |
| `get_class_api` | 获取类成员摘要（推荐优先使用） |
| `get_class_api_full` | 获取类成员完整信息 |
| `get_symbol_source` | 获取单个符号源码 |
| `find_layout` | 查找布局文件 |
| `find_drawable` | 查找 drawable 资源 |
| `find_manifest_component` | 查找四大组件 |
| `find_module_deps` | 查询模块依赖 |
| `find_style` | 查找样式资源 |
| `project_stats` | 获取项目统计 |
| `update_index` | 增量更新索引 |

### 使用示例（Claude Code 对话）

```
用户：帮我找一下 FeedFragment 的继承关系

Claude: 我来帮你查询 FeedFragment 的继承链。
（调用 get_inheritance 工具）
FeedFragment 的继承链如下：
- com.example.feed.FeedFragment
- androidx.fragment.app.Fragment
- androidx.fragment.app.Fragment 的父类...

用户：查找所有继承自 BaseActivity 的类

Claude: 我来查找 BaseActivity 的所有子类。
（调用 get_subclasses 工具）
找到以下子类：
1. com.example.feed.FeedActivity
2. com.example.detail.DetailActivity
...
```

## 搜索语法

### FTS5 全文搜索

| 语法 | 示例 | 说明 |
|------|------|------|
| 前缀搜索 | `Activity` | 匹配 Activity, ActivityManager |
| 精确搜索 | `"Activity"` | 仅匹配 Activity |
| 多词搜索 | `Base Activity` | 同时包含 Base 和 Activity |
| 驼峰分词 | `FeedFrag` | 可匹配 FeedFragment（自动分词） |

### 过滤条件

所有搜索方法支持以下过滤条件：

- `kind` - 符号类型（class, interface, function, property 等）
- `module` - 模块名称（如 `:app`, `:lib-network`，**需要带冒号前缀**）
- `source_set` - 源码集（`sdk` 或 `impl`）
- `limit` - 返回数量限制（默认 20，最大 200）
- `offset` - 分页偏移量

## 项目结构

```
android-code-index/
├── main.py                 # 命令行入口（Click CLI）
├── requirements.txt        # Python 依赖
├── src/
│   ├── __init__.py
│   ├── config.py          # 配置：数据库路径、文件类型过滤
│   ├── database.py        # SQLite schema 初始化，FTS5 触发器
│   ├── file_scanner.py    # 文件扫描：识别模块和 source_set
│   ├── indexer.py         # 索引器：全量/增量索引逻辑
│   ├── watcher.py         # 文件监听：watchdog 实现
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── kotlin_parser.py  # tree-sitter-kotlin 解析
│   │   ├── java_parser.py    # tree-sitter-java 解析
│   │   ├── xml_parser.py     # XML 解析（布局/资源）
│   │   └── gradle_parser.py  # Gradle 依赖解析
│   ├── query/
│   │   ├── __init__.py
│   │   └── query_engine.py   # 查询引擎：所有 SQL 查询封装
│   ├── server/
│   │   ├── __init__.py
│   │   ├── mcp_server.py     # MCP Server（stdio）
│   │   └── http_api.py       # HTTP API（FastAPI）
│   └── utils/
│       ├── __init__.py
│       └── tokenize.py       # 标识符分词（驼峰拆分）
└── ui/                    # Vue 3 前端（可选）
    ├── src/
    │   ├── api/           # API 客户端
    │   ├── components/    # 组件
    │   ├── pages/         # 页面
    │   └── stores/        # Pinia 状态管理
    └── package.json
```

## 技术栈

| 层级 | 技术 |
|------|------|
| **语言** | Python 3.10+ |
| **数据库** | SQLite 3 + FTS5 全文搜索 |
| **代码解析** | tree-sitter（Kotlin/Java） |
| **Web 框架** | FastAPI + Uvicorn |
| **协议** | MCP (Model Context Protocol) |
| **CLI** | Click |
| **文件监听** | watchdog |
| **UI（可选）** | Vue 3 + Vite + Pinia |

## 索引性能优化

- **批量写入**：每 200 个文件提交一次 transaction
- **WAL 模式**：SQLite WAL 模式提升并发性能
- **索引覆盖**：关键字段建立复合索引
- **增量更新**：只重新解析变更文件
- **FTS5 触发器**：自动同步 symbols 表变更

## 常见问题

### Q: 数据库路径在哪里？

A: 默认在 `~/.android-code-index/{项目名}/index.db`。可通过 `main.py projects` 查看所有已索引项目的数据库位置。

### Q: 如何删除某个项目的索引？

A: 直接删除对应的数据库文件即可：
```bash
rm ~/.android-code-index/{项目名}/index.db
```

### Q: 索引速度慢怎么办？

A:
1. 首次全量索引正常需要数分钟到数十分钟（取决于项目规模）
2. 增量更新应该非常快（通常几秒内）
3. 使用 `--watch` 模式可以保持后台自动更新

### Q: MCP Server 连接失败？

A:
1. 确认数据库文件存在：`main.py projects`
2. 确认 Python 环境已激活
3. 检查 `main.py serve mcp` 是否有错误输出

## License

MIT
