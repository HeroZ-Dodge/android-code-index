# POPO 文档导出器 使用说明

将 POPO 文档链接导出为 docx 或 xlsx 文件，由 Claude Code 直接读取。支持 4 种文档类型，所有类型均通过 API 导出

## 前置依赖

```bash
# 可选安装（仅邮箱密码登录方式需要）
npx playwright install chromium
```

> **注意**：不再需要安装 pandoc。所有文档类型均通过 API 直接导出为 docx/xlsx 二进制文件。

## 首次使用：登录

Open API 凭据（appId/appSecret）已内置，**无需额外配置**。只需登录个人账号获取 accessToken。

### 方式一：邮箱密码登录（推荐）

在对话中直接输入邮箱和密码，Claude 会通过 Playwright 自动化浏览器完成登录。

### 方式二：手动 Token 登录

1. 浏览器打开 [docs.popo.netease.com](https://docs.popo.netease.com) 并登录
2. 按 `F12` → `Application` → `Cookies` → `docs.popo.netease.com`
3. 复制 `accessToken` 和 `refreshToken` 的值
4. 在对话中提供给 Claude

## 触发方式

### 1. 自动触发

在对话中直接粘贴 POPO 文档链接，Claude 会自动识别并导出：

```
https://docs.popo.netease.com/team/pc/android/pageDetail/xxxxxxxx
https://docs.popo.netease.com/lingxi/xxxxxxxx
```

### 2. 手动触发

在对话中输入 `/popo-doc-exporter`，然后提供文档链接。

## 支持的 4 种文档类型

| 类型 | 链接格式 | 检测方式 | 导出 API | 输出格式 |
|------|----------|----------|----------|----------|
| 团队文档 | `/team/pc/{key}/pageDetail/{id}` | pageType != 2 | Open API 导出 | docx |
| 团队表格 | `/team/pc/{key}/pageDetail/{id}` | pageType=2, externalType=1 | 团队空间 API (exportType=2) | xlsx |
| 灵犀文档 | `/lingxi/{id}` | detail.type=1 | bs-doc API (exportType=1) | docx |
| 灵犀表格 | `/lingxi/{id}` | detail.type=2 | bs-doc API (exportType=2) | xlsx |

链接中的查询参数（如 `?appVersion=...&deviceType=...`）会自动忽略，直接粘贴完整链接即可。

## 导出流程

所有文档类型采用统一的导出模式：

1. **创建导出任务** — 调用对应的导出 API，获取 taskId
2. **轮询任务状态** — 每 2 秒查询一次，最长等待 60 秒
3. **下载文件** — 任务完成后从 taskExtra 链接下载 docx/xlsx 文件
4. **Claude Code 直接读取** — docx 和 xlsx 均可被 Claude Code 原生读取，无需额外转换

## 使用案例

### 案例一：读取团队空间文档

直接粘贴链接，Claude 自动导出并读取内容：

```
用户：帮我看一下这个文档
https://docs.popo.netease.com/team/pc/android/pageDetail/b618801587484b56acf9ff7836b872ea
```

Claude 会自动：检查登录 → 导出 docx → 读取 docx 文件 → 展示内容。

### 案例二：读取灵犀表格

```
用户：分析这个表格的数据
https://docs.popo.netease.com/lingxi/893464c94c2d4fa0b304375abe89f1e3
```

Claude 会自动：检测到表格类型 (type=2) → 导出 xlsx → 读取 Excel 内容 → 按需分析。

### 案例三：需求分析中引用 POPO 文档

在使用 speckit.requirements 等需求分析 skill 时，提供 POPO 文档链接作为需求来源：

```
用户：需求分析
PRD：https://docs.popo.netease.com/lingxi/xxxxxxxxx
UX稿：https://docs.popo.netease.com/team/pc/android/pageDetail/xxxxxxxxx
```

speckit.requirements 会自动调用 popo-doc-exporter 解析文档内容，无需手动导出。

### 案例四：首次登录的完整流程

```
用户：https://docs.popo.netease.com/team/pc/android/pageDetail/xxxxxxxxx

Claude：POPO 文档需要登录，请提供凭据...

用户：（输入邮箱和密码，或 accessToken 和 refreshToken）

Claude：登录成功！正在导出文档...
       文档已导出为 docx: /tmp/popo-doc-output.docx
       （展示文档内容）
```

登录成功后 Token 会保存到本地（`~/.config/popo-doc-cli/config.json`），后续使用无需重复登录，直到 Token 过期。

## 技术架构

```
┌─────────────────────────────────────────────────┐
│                  POPO 文档导出器                   │
├─────────────────────────────────────────────────┤
│  输入: POPO 文档 URL                              │
│  ↓                                               │
│  URL 解析 → 判断文档类型 (team/lingxi)             │
│  ↓                                               │
│  ┌─── team 文档 ───────────────────────────┐      │
│  │ getPageDetail → pageType 判断            │      │
│  │ ├─ pageType=2 → 团队表格 → xlsx          │      │
│  │ └─ 其他       → 团队文档 → docx          │      │
│  └─────────────────────────────────────────┘      │
│  ┌─── lingxi 文档 ─────────────────────────┐      │
│  │ getDocDetail → type 判断                 │      │
│  │ ├─ type=2 → 灵犀表格 → xlsx              │      │
│  │ └─ type=1 → 灵犀文档 → docx              │      │
│  └─────────────────────────────────────────┘      │
│  ↓                                               │
│  创建导出任务 → 轮询状态 → 下载文件               │
│  ↓                                               │
│  输出: docx 或 xlsx 文件                          │
│  ↓                                               │
│  Claude Code 直接读取                             │
└─────────────────────────────────────────────────┘
```

## 常见问题

**Q: Token 过期了怎么办？**
A: 重新提供文档链接，Claude 会检测到 Token 过期并引导重新登录。

**Q: 其他团队成员需要配置 appId/appSecret 吗？**
A: 不需要，已内置到脚本中，pull 代码后直接可用。

**Q: 还需要安装 pandoc 吗？**
A: 不需要了。之前版本需要 pandoc 将 docx 转 Markdown，现在所有文档直接导出为 docx/xlsx 二进制文件，由 Claude Code 原生读取。

**Q: 灵犀文档和灵犀表格怎么区分？**
A: 脚本通过 `getDocDetail` API 获取文档元数据，`type=1` 为普通文档（导出 docx），`type=2` 为表格（导出 xlsx），自动判断无需手动指定。

**Q: 团队表格和普通团队文档怎么区分？**
A: 脚本通过 `getPageDetail` API 获取页面详情，`pageType=2 && externalType=1` 为嵌入的灵犀表格（导出 xlsx），其他为普通文档（导出 docx）。
