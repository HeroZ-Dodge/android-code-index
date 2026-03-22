---
name: speckit.split
description: 根据 feature.md 中的 spec 点或 plan.md 中的阶段计划在 PM 系统上批量创建子单，并回填子单号等信息。当用户提到"创建子单"、"创建PM子单"、"批量建单"、"feature建单"、"spec建单"、"plan建单"、"阶段建单"、"pm subtask"、"创建工单"或需要根据 feature.md/plan.md 在 PM 系统创建对应子单时触发。
---

# PM 子单批量创建器

根据 feature.md 中定义的 spec 点或 plan.md 中定义的实现阶段，在 PM 系统上批量创建子单并回填信息。

支持两种拆单模式：
- **Feature 模式**: 从 feature.md 的 SP 点拆单（原有能力）
- **Plan 模式**: 从 plan.md 的 Phase 阶段拆单（新增能力）

## 前置校验

### PM 单号驱动校验

**在执行任何拆单操作前，必须先校验当前 spec 是否由 PM 单号驱动**：

1. 解析当前 git 分支名称：
   ```bash
   source .specify/scripts/bash/common.sh
   CURRENT_BRANCH=$(get_current_branch)
   ```

2. 判断分支格式：
   - **新格式** `feature/{PM_PARENT_ID}_{PM_SPEC_ID}_{short-name}` → PM 单号驱动，可继续
   - **新格式（feature 级）** `feature/{PM_PARENT_ID}_{short-name}` → PM 单号驱动，可继续
   - **旧格式** `{NNN}-{short-name}`（如 `001-widget-collapse`）→ **非 PM 单号驱动，拒绝处理**

3. 若非 PM 单号驱动，输出提示并终止：
   ```
   当前分支 `{branch}` 不是以 PM 单号驱动的 spec，无法执行拆单操作。
   请使用 `feature/{PM_ID}_{short-name}` 格式的分支。
   ```

## 模式一：Feature 拆单（SP 点 → 子单）

### 1. 定位 feature.md

从当前 git 分支解析 PM 父单号和 feature 目录：

```bash
# 获取分支和目录信息
source .specify/scripts/bash/common.sh
CURRENT_BRANCH=$(get_current_branch)
```

分支格式 `feature/{PM_ID}_{short-name}` → 在 `specs/{PM_ID}_*/` 下查找 `feature.md`。

若用户指定了 feature.md 路径或 PM 父单号，直接使用。

### 2. 解析 spec 点

从 feature.md 中提取所有 `### SP-NNN:` 块，每个 spec 点需要以下字段：

| 字段 | 来源 | 示例 |
|------|------|------|
| SP 编号 | `### SP-001:` 标题 | `SP-001` |
| 子单标题 | `**PM 子单标题**:` 行 | `达尔文-视频播放器实验推全代码下线` |
| 子单号 | `**PM 子单号**:` 行 | 可能为空或占位符 |

**跳过条件**: 如果 `PM 子单号` 已经是真实的纯数字 ID（非占位符），跳过该 SP 点。

### 3. 创建子单

对每个需要创建的 SP 点，使用脚本创建子单：

```bash
node .claude/skills/speckit.split/scripts/create-pm-subtask.mjs <父单ID> <子单标题>
```

脚本返回 JSON: `{ "id": 2693820001, "subject": "...", "parent_id": "269382" }`

脚本会自动将 PM 系统上的 **"是否AI介入"** 自定义字段（ID: 2014）设置为 `true`。

**备选方案**: 若脚本执行失败（如 API 端点不支持），改用 `pm-netease:pm-skill` Skill 工具，请求格式：
`在父单 #<父单ID> 下创建子单，标题: <子单标题>`
使用备选方案后，需额外调用 `update_issue` API 设置 `custom_field: {"2014": "1"}` 以标记 AI 介入。

### 4. 回填 feature.md

用创建返回的子单号更新 feature.md 中对应 SP 点的字段：

```markdown
- **PM 子单号**: <返回的子单ID>
- **PM 子单标题**: <子单标题> (保持不变)
- **PM 子单链接**: https://a19.pm.netease.com/v6/issues/<返回的子单ID>
- **Spec 目录**: `<子单ID>_<清理后子标题>/`
- **Spec 分支**: `feature/<父单ID>_<子单ID>_<english-short-name>`
```

**字段生成规则**:
- `PM 子单链接`: `https://a19.pm.netease.com/v6/issues/{子单ID}`
- `Spec 目录`: 子单 ID + `_` + 中文标题去除括号/特殊字符（复用 `clean_title_for_naming` 逻辑）
- `Spec 分支`: `feature/{父单ID}_{子单ID}_{2-4个英文单词}`，英文 short-name 从 SP 标题或功能概述推导
- 使用 Edit 工具逐个替换对应行
- 若 feature.md 中原来没有 `PM 子单链接` 字段，在 `PM 子单标题` 行后插入新行

### 5. 更新拆分状态

所有子单创建并回填完成后，将 feature.md 头部的状态字段从 `待拆分` 更新为 `已拆分`：

```markdown
**状态**: 已拆分
```

若仅部分 SP 点完成创建（存在失败的），则更新为 `部分拆分`。

### 6. 输出汇总

完成后输出汇总表格：

| SP | PM 子单号 | 子单链接 | 子单标题 | Spec 目录 | Spec 分支 | 状态 |
|----|----------|---------|---------|-----------|----------|------|
| SP-001 | 2693820001 | [链接](https://a19.pm.netease.com/v6/issues/2693820001) | ... | ... | ... | 已创建 |
| SP-002 | 2693820002 | [链接](https://a19.pm.netease.com/v6/issues/2693820002) | ... | ... | ... | 已创建 |

---

## 模式二：Plan 拆单（Phase 阶段 → 子单）

将 plan.md 中的每个实现阶段（Phase）创建为独立的 PM 子单，父单为当前分支对应的 spec 单号。

### 1. 确定父单号和定位 plan.md

从当前 git 分支解析信息：

```bash
source .specify/scripts/bash/common.sh
CURRENT_BRANCH=$(get_current_branch)
```

- **分支格式** `feature/{PM_PARENT_ID}_{PM_SPEC_ID}_{short-name}` → 父单 ID 为 `PM_SPEC_ID`（即当前 spec 的单号）
- **分支格式** `feature/{PM_PARENT_ID}_{short-name}` → 父单 ID 为 `PM_PARENT_ID`
- 在对应 spec 目录下查找 `plan.md`

若用户指定了 plan.md 路径或父单号，直接使用。

### 2. 解析 Phase 阶段

从 plan.md 中提取所有阶段标题，支持以下格式：

| 匹配模式 | 示例 |
|----------|------|
| `### Phase N: 标题` | `### Phase 1: 收起态 UI 基础` |
| `### 第N阶段: 标题` | `### 第一阶段: 基础设施准备` |
| `**第N阶段: 标题**` | `**第一阶段: 核心功能**` |
| `## Phase N: 标题` | `## Phase 2: 收起态动画` |

每个阶段需要以下字段：

| 字段 | 来源 | 示例 |
|------|------|------|
| 阶段编号 | 标题中的数字 | `Phase 1` / `第一阶段` |
| 子单标题 | 阶段的完整章节名称 | `Phase 1: 收起态 UI 基础` |
| PM 子单号 | 阶段内 `**PM 子单号**:` 行 | 可能不存在或为空 |

**跳过条件**: 如果阶段内已存在 `**PM 子单号**:` 且值为真实的纯数字 ID，跳过该阶段。

### 3. 创建子单

对每个需要创建的阶段，使用脚本创建子单：

```bash
node .claude/skills/speckit.split/scripts/create-pm-subtask.mjs <父单ID> <子单标题>
```

- `<父单ID>`: 当前 spec 的 PM 单号（从分支解析的 `PM_SPEC_ID` 或 `PM_PARENT_ID`）
- `<子单标题>`: 阶段的完整章节名称，如 `Phase 1: 收起态 UI 基础`

脚本返回 JSON: `{ "id": 2693820001, "subject": "...", "parent_id": "270281" }`

脚本会自动将 PM 系统上的 **"是否AI介入"** 自定义字段（ID: 2014）设置为 `true`。

**备选方案**: 若脚本执行失败，改用 `pm-netease:pm-skill` Skill 工具，请求格式：
`在父单 #<父单ID> 下创建子单，标题: <子单标题>`
使用备选方案后，需额外调用 `update_issue` API 设置 `custom_field: {"2014": "1"}` 以标记 AI 介入。

### 4. 回填 plan.md

在每个阶段标题行的**下方**插入 PM 单号信息块。使用 Edit 工具在阶段标题后插入：

```markdown
### Phase 1: 收起态 UI 基础

> **PM 子单号**: 2693820001 | **PM 子单链接**: [#2693820001](https://a19.pm.netease.com/v6/issues/2693820001)

| 任务 | 说明 | 优先级 |
...
```

**回填规则**:
- 在阶段标题（`### Phase N: ...`）的下一行插入引用块（`> `）
- 引用块格式: `> **PM 子单号**: {子单ID} | **PM 子单链接**: [#{子单ID}](https://a19.pm.netease.com/v6/issues/{子单ID})`
- 若标题和内容之间已有空行，在空行后插入引用块
- 使用 Edit 工具逐个阶段回填，每个成功后立即更新（防止中途失败丢失已创建结果）
- 若阶段内已有 `**PM 子单号**` 行，替换更新而非插入新行

### 5. 输出汇总

完成后输出汇总表格：

| Phase | PM 子单号 | 子单链接 | 子单标题 | 状态 |
|-------|----------|---------|---------|------|
| Phase 1 | 2693820001 | [链接](https://a19.pm.netease.com/v6/issues/2693820001) | Phase 1: 收起态 UI 基础 | 已创建 |
| Phase 2 | 2693820002 | [链接](https://a19.pm.netease.com/v6/issues/2693820002) | Phase 2: 收起态动画 | 已创建 |
| Phase 3 | 2693820003 | [链接](https://a19.pm.netease.com/v6/issues/2693820003) | Phase 3: 状态同步与持久化 | 已创建 |
| Phase 4 | 2693820004 | [链接](https://a19.pm.netease.com/v6/issues/2693820004) | Phase 4: 测试与验收 | 已创建 |

---

## 模式选择

当用户触发拆单时，根据以下规则自动判断模式：

1. 若用户明确提及 "plan"、"阶段"、"phase" → **Plan 模式**
2. 若用户明确提及 "feature"、"spec"、"SP" → **Feature 模式**
3. 若当前 spec 目录下存在 feature.md 且包含 `### SP-` 块 → **Feature 模式**
4. 若当前 spec 目录下存在 plan.md 且包含 Phase 阶段 → 询问用户选择模式
5. 若两者都存在 → 询问用户选择模式

## 注意事项

- 创建前确认用户同意，展示待创建的子单列表
- 逐个创建，每个成功后立即更新对应文档（防止中途失败丢失已创建结果）
- 若部分点/阶段已有子单号，仅处理缺失的
- PM API 凭据从 `~/.config/pm-cli/config.json` 读取
- **非 PM 单号驱动的 spec（旧格式分支）不予处理**，需提示用户使用新格式分支
