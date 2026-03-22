---
description: 深度审核计划文档，检查 plan.md、data-model.md、quickstart.md、research.md 与需求 spec.md 的一致性，发现遗漏的细节和边界条件，输出审核报告和修改建议。
handoffs:
  - label: 优化计划
    agent: /speckit.refine
    prompt: 修复审核中发现的问题
    send: true
  - label: 生成任务
    agent: /speckit.tasks
    prompt: 从审核后的计划生成任务
    send: true
---

## 用户输入

```text
$ARGUMENTS
```

在继续之前, 你**必须**考虑用户输入(如果不为空).

## 目标

对计划文档进行深度审核, 确保所有设计文档与需求规格保持一致, 发现潜在问题、遗漏的细节和未考虑的边界条件.

## 审核思维

审核时带着以下问题:
1. 阅读 plan.md 后, 能否明确知道"下一步要做什么"?
2. 每个实施步骤是否都能在其他文档中找到支撑细节?
3. 仅凭这套文档, 能否独立完成实施?

## 执行步骤

### 步骤 1: 初始化

从仓库根目录运行 `.specify/scripts/bash/check-prerequisites.sh --json --paths-only` 获取路径. 解析 JSON 中的 FEATURE_DIR 字段.

定义路径:
- SPEC = FEATURE_DIR/spec.md
- PLAN = FEATURE_DIR/plan.md
- DATA_MODEL = FEATURE_DIR/data-model.md
- RESEARCH = FEATURE_DIR/research.md
- QUICKSTART = FEATURE_DIR/quickstart.md
- REVIEW_OUTPUT = FEATURE_DIR/checklists/plan_review.md

### 步骤 2: 检查现有报告

如果 `REVIEW_OUTPUT` 存在:
- 显示: "⚠️ 发现已存在的审核报告"
- 询问: 覆盖 / 备份 / 跳过
- 相应处理:
  - **覆盖**: 先使用 Bash 工具删除已存在的文件 `rm -f {REVIEW_OUTPUT}`, 然后继续执行步骤 3
  - **备份**: 将现有文件重命名为带时间戳的备份文件, 然后继续执行步骤 3
  - **跳过**: 跳过审核, 直接展示现有报告内容

### 步骤 3: 执行审核代理

**重要**: 使用 Task 代理工具来执行整个审核流程.

在启动之前, 用步骤 1 中的实际绝对路径替换占位符来构建提示词.

使用以下提示词启动 Task 代理(将所有路径替换为实际值):

```
你是计划文档审核专家. 请完成以下审核任务:

## 文档路径(使用这些实际路径读取文件)

- spec.md: {SPEC的实际绝对路径}
- plan.md: {PLAN的实际绝对路径}
- data-model.md: {DATA_MODEL的实际绝对路径}
- research.md: {RESEARCH的实际绝对路径}
- quickstart.md: {QUICKSTART的实际绝对路径}

## 输出路径(审核完成后写入报告到此路径)

{REVIEW_OUTPUT的实际绝对路径}

## 审核维度

A. 需求覆盖度 - spec 中的需求是否都有实现计划?
B. 数据模型一致性 - data-model 是否支撑所有需求?
C. 边界条件处理 - 边缘情况是否都有处理方案?
D. 实现细节完整性 - 任务是否清晰可执行?
E. 文档一致性 - 术语命名是否统一?

## 审核要点

1. 阅读 plan.md 后, 能否明确知道"下一步要做什么"?
2. 每个实施步骤是否都能在其他文档中找到支撑细节?
3. 仅凭这套文档, 能否独立完成实施?

## 问题分类

- 🔴 严重: 阻塞实施
- 🟡 中等: 可能导致问题
- 🟢 轻微: 优化建议

## 你必须执行的步骤

1. 使用 Read 工具读取上述所有文档
2. 对比 spec.md 执行审核检查
3. 生成 Markdown 格式的审核报告
4. 使用 Bash 工具创建目录: mkdir -p {checklists目录的实际路径}
5. 使用 Write 工具将报告写入到输出路径
6. 返回问题统计数量

## 报告必须包含

- 审核总览表(5个维度的状态)
- 🔴 严重问题列表(含文件位置和修复建议)
- 🟡 中等问题列表
- 🟢 轻微问题列表
- 修改建议(按优先级)
- 实施就绪度评估

## 限制

最多 20 个发现, 聚焦实质性问题.

## 完成后返回

返回格式: "完成: X个严重, Y个中等, Z个轻微"
```

等待代理完成并返回问题数量.

### 步骤 4: 报告完成

**代理完成后**, 立即向用户输出摘要:

```
✅ 审核报告已生成: {REVIEW_OUTPUT的实际路径}

发现问题: X 个严重, Y 个中等, Z 个轻微

下一步建议:
- /speckit.refine [问题描述] - 修复发现的问题
- /speckit.tasks - 生成实现任务
```

**注意**: 从代理的返回消息中提取问题数量. 如果代理返回"完成: 3个严重, 5个中等, 2个轻微", 在摘要中使用这些数字.

不要等待其他任何东西. 收到代理结果后立即输出摘要.

## 行为规则

- **只读**源文档(spec、plan、data-model、research、quickstart)
- **写入**报告到 checklists/plan_review.md
- 具体到行号
- 最多限制 20 个发现
- 聚焦实质性问题

## 上下文

$ARGUMENTS
