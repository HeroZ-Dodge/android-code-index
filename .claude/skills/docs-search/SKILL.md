---
name: docs-search
description: |
  项目文档搜索和查看助手。当用户想要查看项目文档、模块文档、组件说明、架构设计、开发规范等内容时自动触发。
  触发关键词：查看文档、文档在哪、怎么使用、组件文档、模块文档、架构文档、开发规范、服务文档、
  share文档、account文档、IM文档、分享组件、账号组件、services文档、查看xxx的文档。
  重启/刷新触发词：重启文档服务、刷新文档、更新文档网站、reload docs、restart docs、文档没更新。
  功能：(1) 确保文档网站服务已启动 (2) 搜索匹配的文档 (3) 返回推荐的 URL 链接供用户查阅 (4) 支持重启服务同步最新文件。
---

# 文档搜索助手

帮助用户快速查找和访问项目文档。

## 工作流程

### 1. 检查文档服务器状态

运行检查脚本确认服务器是否运行：

```bash
bash scripts/check_server.sh 3000
```

- 输出 `running`：服务器已启动
- 输出 `stopped`：需要启动服务器

### 2. 启动文档服务器（如果未运行）

```bash
bash scripts/start_server.sh 3000
```

该脚本会：
- 同步源目录文件到 docs-site
- 启动 VitePress 开发服务器
- 默认端口 3000

### 2.5 重启/刷新文档服务（当用户修改了文件后需要更新）

当用户说"重启文档服务"、"刷新文档"、"文档没更新"等时，运行：

```bash
bash scripts/restart_server.sh 3000
```

该脚本会：
- 停止现有服务器
- 从源目录重新同步所有 md 文件
- 清理缓存
- 重新启动服务器

**触发场景：**
- 用户修改了源文件后刷新网页看不到更新
- 用户说"重启文档"、"刷新文档服务"、"reload docs"
- 用户说"文档没更新"、"网页内容没变"

### 3. 搜索文档

根据用户查询的关键词搜索文档：

```bash
python3 scripts/search_docs.py <关键词1> [关键词2] ... [--port 3000]
```

**示例：**
```bash
# 搜索分享相关文档
python3 scripts/search_docs.py 分享 share

# 搜索账号组件文档
python3 scripts/search_docs.py account 账号

# 搜索架构设计文档
python3 scripts/search_docs.py 架构 architecture
```

**输出格式（JSON）：**
```json
[
  {
    "file": "services/content/share/README.md",
    "title": "分享组件",
    "score": 12,
    "path_matches": 1,
    "content_matches": 2,
    "url": "http://localhost:3000/docs-site/services/content/share/README.html"
  }
]
```

**评分规则：**
- 路径/文件名匹配：每个关键词 +10 分
- 内容匹配：每个关键词 +1 分
- 结果按总分降序排列，路径匹配优先

### 4. 返回结果给用户

将搜索结果以友好的格式展示：

```
找到以下相关文档：

1. **分享组件**
   - 路径: services/content/share/README.md
   - 链接: http://localhost:3000/docs-site/services/content/share/README.html

2. **xxx文档**
   ...

文档网站首页: http://localhost:3000/docs-site/
```

## 文档目录结构

| 目录 | 内容 |
|------|------|
| `AI/` | 项目文档（.AI 目录） |
| `services/` | 组件/模块文档 |
| `claude/` | Claude 相关配置 |
| `specify/` | SDD 规范文档 |
| `docs/` | 其他资源文档 |

## 常用搜索关键词

| 用户意图 | 推荐关键词 |
|----------|------------|
| 分享组件 | share, 分享 |
| 账号组件 | account, 账号, 登录 |
| IM/聊天 | im, 聊天, 消息 |
| 网络请求 | net, 网络, http |
| 架构设计 | architecture, 架构 |
| 推送 | push, 推送 |
| 日志 | log, 日志 |
| 皮肤 | skin, 皮肤, 主题 |
| 钱包 | wallet, 钱包, 支付 |

## 注意事项

- 文档服务默认运行在 3000 端口
- 修改源文件后需要**重启服务**才能看到最新内容（说"刷新文档"或"重启文档服务"）
- 源文件位置：`services/`、`.AI/`、`.claude/`、`.specify/`、`docs/`
