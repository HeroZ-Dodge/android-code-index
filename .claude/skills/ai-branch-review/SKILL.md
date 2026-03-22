---
name: ai-branch-review
description: |
  AI 分支代码审查 - 对指定远程分支在指定时间范围内的提交进行全面代码质量审查，生成 HTML 审查报告，并可选发送 POPO 通知。
  替代 GitLab CI 的 ai-manual-review 任务，在本地完成相同功能。
  触发词："审查分支"、"review branch"、"ai review"、"分支审查"、"AI 分支审查"、"ai-branch-review"。
  当用户需要对远程分支的近期提交进行批量代码审查并生成 HTML 报告时使用。
  与 code-review 的区别：code-review 用于审查本地代码改动，ai-branch-review 用于审查远程分支的时间范围内提交并生成 HTML 报告。
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
  - Bash(git:*)
  - Bash(date:*)
  - Bash(wc:*)
  - Bash(mkdir:*)
  - Bash(bash:*)
  - AskUserQuestion
---

# AI 分支代码审查

对指定远程分支在指定时间范围内的代码提交进行全面审查，生成 HTML 报告并可选发送 POPO 通知。

## 参数解析

从 `$ARGUMENTS` 中解析以下参数（支持 `--key=value` 格式或自然语言）：

| 参数 | 必选 | 默认值 | 说明 |
|------|------|--------|------|
| `branch` | 是 | - | 要审查的远程分支名（如 `feature/xxx`） |
| `hours` | 否 | `24` | 审查过去多少小时内的提交 |
| `receiver` | 否 | `1394405` | POPO 通知接收者 ID |
| `notify` | 否 | `false` | 是否发送 POPO 通知 |

**解析示例**：
- `--branch=feature/xxx --hours=48` → branch=feature/xxx, hours=48
- `feature/xxx` → branch=feature/xxx, hours=24
- `feature/xxx 48小时` → branch=feature/xxx, hours=48
- `--branch=feature/xxx --notify --receiver=12345` → 发送 POPO 通知

如果 `$ARGUMENTS` 为空或缺少 branch，使用 AskUserQuestion 询问。

## 执行流程

### 1. 准备工作

```bash
# 确保远程分支数据最新
git fetch --all

# 计算时间范围
since_epoch=$(($(date +%s) - hours * 3600))
# macOS:
since_time=$(date -u -r "$since_epoch" '+%Y-%m-%d %H:%M:%S')
# Linux:
since_time=$(date -u -d "@$since_epoch" '+%Y-%m-%d %H:%M:%S')
```

### 2. 检查分支提交

```bash
# 检查分支是否有提交
commit_count=$(git log --since="$since_time" --oneline "origin/$branch" | wc -l | tr -d ' ')
```

如果 `commit_count == 0`，通知用户该分支在时间范围内没有新提交，直接结束。

### 3. 获取变更概览

```bash
# 提交列表
git log --since="$since_time" --oneline "origin/$branch"

# 变更统计：找到时间范围内最早的 commit
earliest=$(git log --since="$since_time" --format="%H" "origin/$branch" | tail -1)
git diff "${earliest}^..origin/$branch" --stat
```

### 4. 逐文件深度审查

对每个变更的源码文件（`.kt`, `.java`, `.xml` 等，排除 `.gradle`, `.properties`, 测试文件）：

1. 使用 Read 工具读取完整文件内容理解上下文
2. 按照 `.claude/skills/code-review/review-prompt.md` 中的审查规则进行检查
3. 使用 P0(严重)/P1(重要)/P2(一般)/P3(建议) 分级

### 5. 生成 HTML 报告

报告输出路径：`build/reports/ai-review/review_{branch_safe}_{datetime}.html`

```bash
mkdir -p build/reports/ai-review
```

**报告结构**（参考 `assets/review-report-template.html` 的 CSS 样式）：

- **A. 概览**：提交数、变更文件数、新增/删除行数
- **B. 变更文件列表**：按模块分组的文件变更表格
- **C. 问题发现**：P0/P1/P2/P3 分级，每个问题包含文件路径、行号、问题描述和修复建议
- **D. 审查覆盖项**：review-prompt.md 中的 checklist 执行结果（PASS/WARN/N/A）
- **E. 修复建议**：行动项表格（优先级、文件、问题、建议操作）
- **页脚**：生成时间、分支名

使用 Write 工具将 HTML 保存到 `build/reports/ai-review/` 目录。

**CSS 样式**：读取 `assets/review-report-template.html`（位于本 skill 目录下）获取完整 CSS（暗色主题），直接内联到生成的 HTML 中。

### 6. 可选通知

当 `notify=true` 时，执行 POPO 通知脚本：

```bash
bash .claude/skills/ai-branch-review/scripts/notify-popo.sh \
  "build/reports/ai-review/review_{branch_safe}_{datetime}.html" \
  "$branch" \
  "$receiver"
```

### 7. 输出结果

向用户输出：
- 报告文件路径
- 问题统计（P0/P1/P2/P3 数量）
- 如果发送了通知，显示报告链接

## 示例

### 示例 1：基本用法

用户输入：`/ai-branch-review feature/4.12.0_comic_filter`

执行：审查 feature/4.12.0_comic_filter 分支过去 24 小时内的提交，生成 HTML 报告到 `build/reports/ai-review/`。

### 示例 2：指定时间范围

用户输入：`/ai-branch-review --branch=develop --hours=48`

执行：审查 develop 分支过去 48 小时内的提交。

### 示例 3：带通知

用户输入：`/ai-branch-review --branch=feature/xxx --notify --receiver=12345`

执行：审查并生成报告，上传报告并发送 POPO 通知到指定接收者。