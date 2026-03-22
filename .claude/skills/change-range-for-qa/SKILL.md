---
name: change-range-for-qa
description: 代码变更影响范围生成器。当用户提到"影响范围"、"测试范围"、"QA测试"、"change range"、"test scope"或需要生成代码改动的测试清单时使用。支持指定提交或分支生成。
---

# 代码变更影响范围生成器

根据 Git 提交或分支的代码变更，自动生成影响范围和重点测试范围清单，供 QA 测试使用。

## 使用方式

```bash
/change-range-for-qa                        # 当前分支 vs develop
/change-range-for-qa branch:feature/xxx     # 指定分支 vs develop
/change-range-for-qa commit:abc1234         # 指定提交
/change-range-for-qa commit:abc1234..def5678  # 提交范围
```

## 执行步骤

### 1. 获取变更信息

使用 `scripts/get_branch_changes.sh` 或以下命令获取本分支原创提交（排除 develop 的合并提交）：

```bash
MERGE_BASE=$(git merge-base HEAD develop)
git log ${MERGE_BASE}..HEAD --oneline --no-merges --first-parent
git diff ${MERGE_BASE}..HEAD --name-only
```

### 2. 识别核心需求

从 commit message 中提取需求号（如 `#261921`），按需求号分组识别主要功能点。

### 3. 分析变更代码（关键步骤）

**必须读取所有变更文件的 diff，不能遗漏任何一个业务相关文件**：

```bash
git diff ${MERGE_BASE}..HEAD -- <file_path>
```

#### 分析优先级（必须全部覆盖）：

1. **ViewModel/Helper/Manager**：核心业务逻辑（排序、过滤、条件判断）
2. **Entity/Bean**：数据模型变化（新增字段、新增实体类）
3. **Activity/Fragment**：页面结构变化（新增页面、Tab变化）
4. **Adapter/ViewHolder**：列表展示逻辑
5. **ABTest 相关**：ABTestEntityV2、AbTestHelper（实验分组）
6. **红点/通知**：RedDotHelper、Manager（红点显示条件）
7. **路由/跳转**：Router、Jump、Handler（入口变化）
8. **静态配置**：StaticConfigModuleName（渠道包配置等）

#### 必须提取的逻辑类型：

- **数据匹配规则**：官服包/渠道包如何匹配、去重
- **排序规则**：按什么字段排序、优先级
- **过滤规则**：什么数据会被过滤掉
- **分组规则**：数据如何分组展示
- **红点规则**：什么条件显示红点、何时消失
- **跳转规则**：各入口跳转到哪个页面/Tab

**详细分析指南见**：[references/analysis-guide.md](references/analysis-guide.md)

### 4. 生成影响范围报告

```markdown
## 代码变更影响范围

**分支**：feature/xxx
**对比基线**：develop
**核心需求**：#需求号 需求描述

---

### 一、修改范围

按功能模块列出改动，以业务语言描述：

#### [功能模块1]
- 新增xxx页面，包含xxx、xxx、xxx三个Tab
- xxx列表新增xxx分组
- 新增ABTest实验：xxx（基准组：xxx，实验组：xxx）

---

### 二、关键业务逻辑

提取代码中的核心业务规则：

- xxx显示条件：条件A OR 条件B
- xxx列表排序：按xxx倒序，xxx置顶
- 多个xxx同时存在时：优先级 A > B > C

---

### 三、重点测试范围

#### [功能1]
- [ ] 测试点1
- [ ] 测试点2

---

### 四、边界场景

- 边界场景1
- 边界场景2
```

## 输出原则

1. **完整覆盖**：必须覆盖所有变更文件的功能点，可以简洁但不能遗漏
2. **过滤非本分支提交**：使用 merge-base 确保只分析本分支原创代码
3. **业务语言描述**：不列代码文件和方法名，用业务能理解的语言
4. **提取关键逻辑**：深入分析业务规则（条件、排序、优先级、匹配规则等）
5. **可执行**：测试点直接可作为测试用例执行
6. **分模块**：按功能模块组织，便于 QA 分工

## 常见遗漏检查清单

生成报告后，必须检查以下内容是否遗漏：

- [ ] 渠道包匹配逻辑（官服包 vs 渠道包的匹配、去重规则）
- [ ] 首页模块变化（游戏 Tab 新增模块、模块点击跳转）
- [ ] 红点联动逻辑（多个红点来源的优先级、消除条件）
- [ ] ABTest 分流逻辑（实验组/基准组的功能差异）
- [ ] 各入口跳转目标（不同入口跳转到不同 Tab/页面）
- [ ] 数据缓存策略（有缓存/无缓存的不同行为）
- [ ] 好友在玩/游戏事件等附加信息的展示
