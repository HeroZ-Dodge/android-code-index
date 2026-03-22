---
name: jenkins-test
description: |
  通过 Jenkins CLI 复制 Job 用于提测打包。当用户提到"提测"、"打提测包"、"jenkins 提测"、"复制 Jenkins job"或输入 /jenkins-test 时自动触发。支持指定 Job 名称或从 commit 历史智能推荐。
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
---

# Jenkins 提测打包

通过 Jenkins CLI 复制 Job 用于提测。

## 参数

- `$ARGUMENTS`: 可选的 Job 名称。未提供时从 commit 智能提取

## 配置

```bash
# 查找 SKILL_DIR
SKILL_DIR=".claude/skills/jenkins-test"
[ -f "$SKILL_DIR/lib/jenkins-cli.jar" ] || SKILL_DIR="$HOME/.claude/skills/jenkins-test"

# Jenkins CLI 函数
jenkins_cli() {
    java -jar "${SKILL_DIR}/lib/jenkins-cli.jar" \
        -s http://10.0.9.238:8080/jenkins/ \
        -auth lianghanguang:11712f96945ee628b3b843842129a84bc2 \
        -http "$@"
}

SOURCE_JOB="网易大神-ForCopyDocker"
```

## Job 名称规范

- 禁止: `< > & " ' / \ ? * : | #`，不能以 `.` 或空格开头/结尾
- 自动修正: `/` → `-`，空格 → `_`

## 执行流程

### 1. 信息收集

```bash
BRANCH=$(git branch --show-current)
GIT_USER_EMAIL=$(git config user.email)
git log develop..HEAD --oneline --author="$GIT_USER_EMAIL"
```

### 2. 本地工作区与远程分支一致性检查

```bash
git status --short
git fetch origin "${BRANCH}" 2>/dev/null
LOCAL_HEAD=$(git rev-parse HEAD)
REMOTE_HEAD=$(git rev-parse "origin/${BRANCH}" 2>/dev/null)
```

- **有未提交的修改** (`git status --short` 非空): **AskUserQuestion** 展示未提交文件列表，提示这些修改不会包含在 Jenkins 构建中。选项: 1) 继续（忽略未提交修改） 2) 中止（用户自行提交后重试）
- **远程分支不存在** (`REMOTE_HEAD` 为空): **AskUserQuestion** 提示本地分支未推送到远程，Jenkins 无法拉取代码。建议先 `git push -u origin ${BRANCH}`
- **本地有未推送的提交** (`git log origin/${BRANCH}..HEAD --oneline` 非空): **AskUserQuestion** 提示有未推送的提交，Jenkins 构建不会包含这些代码。展示未推送提交列表，建议先 `git push`
- **本地落后于远程** (`git log HEAD..origin/${BRANCH} --oneline` 非空): **AskUserQuestion** 提示本地落后于远程。选项: 1) merge 远程到本地 (推荐，执行 `git merge origin/${BRANCH}`) 2) force push 覆盖远程 (不推荐) 3) 继续（Jenkins 用远程代码）
- **本地与远程分叉** (既有未推送提交，又落后于远程): **AskUserQuestion** 提示分叉。选项: 1) merge 远程到本地 (推荐，执行 `git merge origin/${BRANCH}` 后再 push) 2) force push 覆盖远程 (不推荐) 3) 中止
- **一致**: 继续

### 3. 确定 Job 名称

- **有 $ARGUMENTS**: 校验名称规范，添加 `网易大神-` 前缀
- **无参数**: 从 commits 提取 `#(\d+)\s*(.+?)` 模式，取出现最多的需求号+描述
  - **AskUserQuestion** 确认推荐名称

**示例**: `#253400 [会员生日礼权益]` → `网易大神-253400-会员生日礼权益`

### 4. 分支冲突检查

```bash
node ${SKILL_DIR}/scripts/check_branch_conflict.mjs "${BRANCH}"
```

发现冲突时 **AskUserQuestion**：使用现有 Job 或创建新 Job

### 5. 同名检查

```bash
jenkins_cli get-job "$NEW_JOB" > /dev/null 2>&1
```

存在同名时 **AskUserQuestion**：是否删除重建？

### 6. 复制并配置 Job

```bash
bash ${SKILL_DIR}/scripts/copy_and_configure_job.sh "${SKILL_DIR}" "${SOURCE_JOB}" "${NEW_JOB}" "${BRANCH}" [--delete-existing]
```

### 7. 触发构建

**AskUserQuestion**: 是否立即触发构建？

```bash
jenkins_cli build "$NEW_JOB" -p GIT_BRANCH="$BRANCH" -p UPLOAD_BRANCH="$BRANCH"
```

### 8. 更新易协作单状态

**步骤 1: 预览变更（--dry-run）**

**必须**先用 `--dry-run` 展示将要执行的变更，**禁止**跳过此步直接执行：

```bash
node ${SKILL_DIR}/scripts/update_pm_issue.mjs "${单号}" "${NEW_JOB}" "${BRANCH}" --dry-run
```

将脚本输出的变更预览展示给用户。

**步骤 2: 确认是否执行**

**AskUserQuestion**（**必须**调用，不可跳过）: 是否执行以上变更，将单据状态更新为「开发完成」？
- 选项 1: 是，执行更新
- 选项 2: 否，跳过

**步骤 3: 执行更新**

仅在用户选择「是」后执行（不带 `--dry-run`）：

```bash
node ${SKILL_DIR}/scripts/update_pm_issue.mjs "${单号}" "${NEW_JOB}" "${BRANCH}"
```

**功能**: 在父单 description 追加打包信息（含 Jenkins 链接），更新父单和子单状态为「开发完成」

### 9. 发送提测通知

**步骤 1: 获取通知人员列表**

```bash
node ${SKILL_DIR}/scripts/notify_developers.mjs --list "${单号}"
```

脚本会从 Android 子单提取：
- **开发人员**：子单负责人邮箱
- **QA**：子单 `跟进QA` 字段

**步骤 2: 展示人员列表并确认**

**AskUserQuestion**（**必须**调用，不可跳过，即使人员列表为空也要询问）：是否发送提测通知？
- 选项 1: 是，通知以上人员
- 选项 2: 否，跳过通知
- 选项 3: 手动输入（用户自定义邮箱，逗号分隔）

**⚠️ 严禁**在用户确认前直接执行发送命令。

**步骤 3: 根据用户选择发送**

```bash
# 选项 1: 使用子单获取的邮箱（开发 + QA）
node ${SKILL_DIR}/scripts/notify_developers.mjs "${单号}" "${NEW_JOB}" "${BRANCH}"

# 选项 3: 使用用户自定义邮箱
node ${SKILL_DIR}/scripts/notify_developers.mjs "${单号}" "${NEW_JOB}" "${BRANCH}" "a@corp.netease.com,b@corp.netease.com"
```

**功能**: 通过 POPO 机器人发送提测通知给开发人员和 QA，包含需求单标题、Jenkins 链接和需求单链接

## 常见错误

| 错误 | 解决 |
|------|------|
| `No such job` | 检查源 Job 名称 |
| `already exists` | 询问用户是否删除 |
| `Authentication required` | 检查 Token |
| `Handshake error` | 确保用 `-http` 模式 |
