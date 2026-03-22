---
name: find-skills
description: 帮助用户发现和安装 Agent 技能。当用户提出"怎么做X"、"找一个做X的技能"、"有没有能做...的技能"等问题，或表达出扩展能力的兴趣时使用此技能。当用户在寻找可能作为可安装技能存在的功能时，应使用此技能。
---

# 查找技能

此技能帮助你从开放的 Agent 技能生态系统中发现和安装技能。

## 何时使用此技能

当用户出现以下情况时使用此技能：

- 问"怎么做X"，且X可能是一个已有现成技能的常见任务
- 说"帮我找一个做X的技能"或"有没有做X的技能"
- 问"你能做X吗"，且X是一项专业能力
- 表达出扩展 Agent 能力的兴趣
- 想搜索工具、模板或工作流
- 提到希望在某个特定领域（设计、测试、部署等）获得帮助

## 什么是 Skills CLI？

Skills CLI（`npx skills`）是开放 Agent 技能生态系统的包管理器。技能是模块化的包，通过专业知识、工作流和工具来扩展 Agent 的能力。

**核心命令：**

- `npx skills find [查询词]` - 交互式搜索或按关键词搜索技能
- `npx skills add <包名>` - 从 GitHub 或其他来源安装技能
- `npx skills check` - 检查技能更新
- `npx skills update` - 更新所有已安装的技能

**浏览技能：** https://skills.sh/

## 如何帮助用户查找技能

### 第一步：理解用户需求

当用户寻求帮助时，识别以下信息：

1. 所属领域（例如：React、测试、设计、部署）
2. 具体任务（例如：编写测试、创建动画、审查 PR）
3. 这是否是一个足够常见的任务，以至于可能已有相应技能

### 第二步：搜索技能

使用相关查询词运行搜索命令：

```bash
npx skills find [查询词]
```

例如：

- 用户问"怎么让我的 React 应用更快？" → `npx skills find react performance`
- 用户问"你能帮我做 PR 审查吗？" → `npx skills find pr review`
- 用户问"我需要创建变更日志" → `npx skills find changelog`

命令将返回如下结果：

```
Install with npx skills add <owner/repo@skill>

vercel-labs/agent-skills@vercel-react-best-practices
└ https://skills.sh/vercel-labs/agent-skills/vercel-react-best-practices
```

### 第三步：向用户展示选项

找到相关技能后，向用户展示以下信息：

1. 技能名称及其功能
2. 可运行的安装命令
3. 在 skills.sh 上了解更多的链接

示例回复：

```
我找到了一个可能有帮助的技能！"vercel-react-best-practices"技能提供了
来自 Vercel 工程团队的 React 和 Next.js 性能优化指南。

安装方式：
npx skills add vercel-labs/agent-skills@vercel-react-best-practices

了解更多：https://skills.sh/vercel-labs/agent-skills/vercel-react-best-practices
```

### 第四步：提供安装服务

如果用户想要继续，请遵循智能安装策略：

#### 4a：检测 `.claude` 目录

安装前，检查项目是否有 `.claude` 目录：

```bash
ls -d .claude 2>/dev/null
```

#### 4b：根据检测结果安装

**如果 `.claude` 目录存在** — 使用 `--copy` 标志直接安装到 `.claude/skills/`，避免创建 `.agents/` 中间目录：

```bash
npx skills add <owner/repo@skill> -y --copy --agent claude-code
```

`--copy` 标志直接复制文件（而非符号链接），`--agent claude-code` 将安装限制为仅 Claude Code 使用，避免创建额外的 `.agents/` 目录。

**如果 `.claude` 目录不存在** — 不要自动安装。而是使用 AskUserQuestion 询问用户希望在哪里安装技能，提供以下选项：

1. **项目级别（推荐）** — 在当前项目中创建 `.claude/skills/`。运行：
   ```bash
   mkdir -p .claude/skills && npx skills add <owner/repo@skill> -y --copy --agent claude-code
   ```
2. **全局级别** — 安装到用户级别范围，可在所有项目中使用。运行：
   ```bash
   npx skills add <owner/repo@skill> -y -g
   ```

不要默认使用 `-g` 标志 — 技能应安装在项目级别，以便将其限定在当前项目范围内。

### 第五步：中文本地化

安装成功后，读取目标技能的 SKILL.md 文件内容，判断其说明内容是否为非中文。

#### 5a：判断语言

读取安装后的 SKILL.md 文件，检查其正文内容（不含 frontmatter 中的 name 字段）是否主要为非中文语言。

#### 5b：询问用户

如果 SKILL.md 内容为非中文，使用 AskUserQuestion 询问用户：

```
已安装的技能文档为英文（或其他非中文语言），是否需要将其转化为中文？
```

提供选项：
1. **转化为中文（推荐）** — 将文档说明内容翻译为中文，保持技术术语和代码块不变
2. **保持原文** — 不做任何修改

#### 5c：执行翻译

如果用户同意转化，按以下原则处理 SKILL.md：

- **翻译范围**：所有自然语言说明内容（标题、段落、列表文字、表格文字等）
- **保持不变**：frontmatter 中的 `name` 字段、代码块内容、命令示例、URL 链接、技术专有名词（如工具名、库名）
- **翻译质量**：语句通顺自然，符合中文技术文档的表达习惯，不要生硬直译
- `description` 字段需要翻译

翻译完成后，将翻译结果展示给用户review，而不是直接写入文件。

#### 5d：确认并写入

用户确认翻译内容无误后，再将最终内容写入 SKILL.md 文件完成更新。如果用户提出修改意见，根据反馈调整后再次展示，直到用户满意为止。

## 常见技能分类

搜索时，可参考以下常见分类：

| 分类         | 示例查询词                               |
| ------------ | ---------------------------------------- |
| Web 开发     | react, nextjs, typescript, css, tailwind |
| 测试         | testing, jest, playwright, e2e           |
| DevOps       | deploy, docker, kubernetes, ci-cd        |
| 文档         | docs, readme, changelog, api-docs        |
| 代码质量     | review, lint, refactor, best-practices   |
| 设计         | ui, ux, design-system, accessibility     |
| 生产力       | workflow, automation, git                |

## 有效搜索的技巧

1. **使用具体关键词**："react testing" 比单独的 "testing" 效果更好
2. **尝试替代词**：如果 "deploy" 没有结果，试试 "deployment" 或 "ci-cd"
3. **查看热门来源**：许多技能来自 `vercel-labs/agent-skills` 或 `ComposioHQ/awesome-claude-skills`

## 未找到技能时

如果没有找到相关技能：

1. 告知用户未找到现有技能
2. 主动提出使用通用能力直接帮助完成任务

示例：

```
我搜索了与"xyz"相关的技能，但没有找到匹配项。
不过我仍然可以直接帮你完成这个任务！你想让我继续吗？

如果这是你经常做的事情，你可以通过`skill-creator`创建自己的技能
```
