---
name: popo-doc-exporter
description: 导出 POPO 文档（团队空间、灵犀文档）为 docx 或 xlsx 文件。当用户消息中出现 docs.popo.netease.com 链接、popo 文档链接、POPO 文档、popo文档、团队空间文档、灵犀文档时自动激活。也可由其他 skill（如 speckit.requirements）调用以解析 POPO 文档内容。用户使用 /popo-doc-exporter 命令时触发。
allowed-tools: Bash, Read, Write, Task, Glob
---

# POPO 文档导出器

将 POPO 文档链接导出为 docx 或 xlsx 文件，由 Claude Code 直接读取。支持 4 种文档类型：团队文档、团队表格、灵犀文档、灵犀表格。所有类型均通过 API 导出，无需 pandoc 等外部依赖。

Open API 凭据（appId/appSecret）已内置，团队成员开箱即用，只需登录个人 accessToken。

## 工作流程

### 1. 检查登录状态

```bash
node .claude/skills/popo-doc-exporter/scripts/popo-doc.mjs check
```

如果登录正常（exit code 0），直接跳到第 2 步。

如果未登录或 token 过期（exit code 1），执行登录流程：

#### 登录流程

使用 AskUserQuestion 一步完成，用户在 "Other" 中输入凭据：

- **question**: "POPO 文档需要登录，支持两种方式：\n\n**方式一：邮箱密码登录**\n需要安装 Playwright（详见 README.md：`npx playwright install chromium`）\n\n**方式二：Token 登录**\n从浏览器 Cookie 中获取 accessToken 和 refreshToken（获取方式详见 README.md）\n\n请在下方输入凭据（以空格分隔）：\n- 邮箱登录：`邮箱 密码`\n- Token登录：`accessToken refreshToken`"
- **header**: "POPO登录"
- **options**:
  - label: "邮箱密码登录", description: "需要 Playwright 依赖，通过自动化浏览器登录"
  - label: "Token 登录", description: "从浏览器 Cookie 获取 accessToken + refreshToken"

**解析用户输入**：

- 如果用户选择了选项但未在 Other 中提供实际凭据，则再次用 AskUserQuestion 请求输入对应凭据
- 如果输入包含 `@`：按空格拆分为 `邮箱` 和 `密码`，执行邮箱登录
- 否则：按空格拆分为 `accessToken` 和 `refreshToken`，执行 Token 登录

**邮箱密码登录**（通过 Playwright 自动化浏览器）：
```bash
node .claude/skills/popo-doc-exporter/scripts/popo-doc.mjs login --email "<邮箱>" --password "<密码>"
```

如果执行失败且错误信息包含 `Cannot find` 或 `playwright`（说明未安装 Playwright），向用户提示：
1. 告知需要先安装 Playwright：`npx playwright install chromium`
2. 询问用户是否要自动安装，或改用 Token 方式登录

**Token 登录**：
```bash
node .claude/skills/popo-doc-exporter/scripts/popo-doc.mjs login --token --access-token "<accessToken>" --refresh-token "<refreshToken>"
```

如果 Token 登录失败（check 仍返回 exit code 1，或导出时报未登录/token无效），向用户展示 Token 获取教程：
1. 浏览器打开 https://docs.popo.netease.com 并登录
2. 按 `F12` → `Application` → `Cookies` → `docs.popo.netease.com`
3. 分别复制 `accessToken` 和 `refreshToken` 的值
4. 重新输入给 Claude（以空格分隔）

登录成功后继续第 2 步。

### 2. 导出文档

```bash
node .claude/skills/popo-doc-exporter/scripts/popo-doc.mjs "<popo_url>" --output /tmp/popo-doc-output.docx
```

脚本会自动检测文档类型并选择正确的导出格式：

- **普通文档**（团队文档、灵犀文档 type=1）：导出为 `/tmp/popo-doc-output.docx`
- **表格文档**（团队表格、灵犀表格 type=2）：导出为 `/tmp/popo-doc-output.xlsx`（自动替换扩展名）

### 3. 读取结果

用 Read 工具直接读取导出的文件（Claude Code 可直接读取 docx 和 xlsx）：

- **普通文档**：`Read /tmp/popo-doc-output.docx`
- **表格文档**：`Read /tmp/popo-doc-output.xlsx`

无需额外下载图片或转换格式，docx/xlsx 文件已包含完整内容。

## 4 种文档类型的导出方式

| 类型 | URL 特征 | 检测方式 | 导出 API | 输出格式 |
|------|----------|----------|----------|----------|
| 团队文档 | `/team/pc/{key}/pageDetail/{id}` | pageType != 2 | Open API `/open-apis/drive-space/v1/page/export` | docx |
| 团队表格 | `/team/pc/{key}/pageDetail/{id}` | pageType=2, externalType=1 | 团队空间 API `/api/bs-team-space/web/v1/page/export?exportType=2` | xlsx |
| 灵犀文档 | `/lingxi/{docId}` | detail.type=1 | bs-doc API `/api/bs-doc/v1/document/lingxi/export/new?exportType=1` | docx |
| 灵犀表格 | `/lingxi/{docId}` | detail.type=2 | bs-doc API `/api/bs-doc/v1/document/lingxi/export/new?exportType=2` | xlsx |

## 支持的链接格式

- `https://docs.popo.netease.com/team/pc/{teamSpaceKey}/pageDetail/{pageId}` — 团队空间（文档或表格，自动检测）
- `https://docs.popo.netease.com/doc/pageDetail/{pageId}` — 文档空间
- `https://docs.popo.netease.com/lingxi/{docId}` — 灵犀文档（文档或表格，自动检测）
- 带查询参数的变体（`?appVersion=...` 等自动忽略）

## 错误处理

| 错误 | 处理 |
|------|------|
| 未登录 / token 过期 | 走登录流程 |
| Playwright 未安装 | 提示安装命令 `npx playwright install chromium`，询问是否自动安装或改用 Token 方式 |
| Token 无效 / 登录失败 | 展示 Token 获取教程（F12 → Application → Cookies → 复制 accessToken 和 refreshToken） |
| 浏览器登录失败（其他原因） | 提示用户改用 Token 方式 |
| 链接格式无效 | 提示正确格式 |
| 导出超时 | 60s 超时，建议重试 |

## 前置依赖

- **Playwright + Chromium**：仅邮箱密码登录需要（`npx playwright install chromium`）
