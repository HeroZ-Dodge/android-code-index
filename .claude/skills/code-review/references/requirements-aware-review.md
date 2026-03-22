# Requirements-Aware Code Review Guide

当代码审查的上下文中包含需求文档时，需要进行更全面的审查。本指南说明如何结合需求文档进行深度审查。

## 识别需求文档上下文

检查对话历史中是否包含以下内容：
- 用户提供的需求文档（PDF 或图片）
- branch-review skill 的输出（包含需求文档分析）
- 用户明确提到的需求点

如果有需求文档上下文，进入**需求感知审查模式**。

## 需求感知审查 Checklist

### 1. 功能完整性检查

从需求文档中提取功能点，逐项检查代码实现：

**检查项**：
- [ ] 所有必需功能是否都已实现？
- [ ] UI 元素是否完全符合设计稿？
- [ ] 交互流程是否符合需求描述？
- [ ] 数据格式是否匹配接口文档？

**示例**：

需求文档说明：
> "评分人数展示：<10000 展示实际人数，>=10000 按万单位展示，保留一位小数"

代码检查：
```kotlin
// ✅ 正确实现
fun formatCount(count: Int): String {
    return if (count < 10000) {
        count.toString()
    } else {
        String.format("%.1f万", count / 10000f)
    }
}

// ❌ 未按需求实现
fun formatCount(count: Int): String {
    return count.toString()  // 没有处理 >=10000 的情况
}
```

### 2. 边界值验证

需求文档中明确或隐含的边界值必须验证：

**常见边界值场景**：

| 需求描述 | 边界值 | 代码检查点 |
|---------|--------|-----------|
| "评分范围 0-10" | 0, 10, -1, 11 | 是否有范围校验？ |
| "最多显示 3 个头像" | 0, 1, 2, 3, 4+ | 是否用 `take(3)`？ |
| "支持 1-100 个字符" | 0, 1, 100, 101 | 是否有长度检查？ |
| "列表分页，每页 20 条" | 第 0 页, 最后一页 | 是否处理边界？ |

**检查示例**：

需求：评分范围 0-10

```kotlin
// ❌ 缺少边界值检查
fun submitScore(score: Float) {
    api.submitScore(score)  // 用户可能输入 -1 或 15
}

// ✅ 添加边界值校验
fun submitScore(score: Float) {
    if (score < 0 || score > 10) {
        showError("评分必须在 0-10 之间")
        return
    }
    api.submitScore(score)
}
```

### 3. 特殊情况处理

需求文档中可能提到或隐含的特殊情况：

#### 3.1 空状态

**需求文档提及**：
- "列表为空时显示空状态提示"
- "无数据时显示引导文案"

**代码检查**：
```kotlin
// ❌ 没有空状态处理
fun loadData(data: List<Item>) {
    adapter.setData(data)  // 空列表时显示空白页面
}

// ✅ 处理空状态
fun loadData(data: List<Item>) {
    if (data.isEmpty()) {
        showEmptyView()
    } else {
        hideEmptyView()
        adapter.setData(data)
    }
}
```

#### 3.2 加载状态

**需求文档提及**：
- "数据加载时显示 loading 动画"
- "首次加载显示骨架屏"

**代码检查**：
```kotlin
// ❌ 没有加载状态
fun fetchData() {
    api.getData { result ->
        showData(result)
    }
}

// ✅ 显示加载状态
fun fetchData() {
    showLoading()
    api.getData { result ->
        hideLoading()
        showData(result)
    }
}
```

#### 3.3 错误处理

**需求文档提及**：
- "网络错误时显示友好提示"
- "权限被拒绝时引导用户开启"

**代码检查**：
```kotlin
// ❌ 错误处理不友好
api.getData().subscribe(
    { data -> showData(data) },
    { error -> error.printStackTrace() }  // 用户看不到任何提示
)

// ✅ 友好的错误处理
api.getData().subscribe(
    { data -> showData(data) },
    { error ->
        when (error) {
            is NetworkException -> showError("网络连接失败，请检查网络设置")
            is PermissionException -> showPermissionDialog()
            else -> showError("加载失败，请稍后重试")
        }
    }
)
```

### 4. UI 规范检查

需求文档中的 UI 设计稿规范：

**检查项**：
- [ ] 间距（margin, padding）是否符合设计稿？
- [ ] 字体大小、颜色是否匹配？
- [ ] 图标尺寸是否正确？
- [ ] 动画效果是否符合要求？

**示例**：

设计稿：神评图标 46dp × 18dp

```kotlin
// ❌ 尺寸不符
val iconWidth = DisplayUtil.dip2px(context, 40f)  // 应该是 46dp
val iconHeight = DisplayUtil.dip2px(context, 20f)  // 应该是 18dp

// ✅ 符合设计稿
val iconWidth = DisplayUtil.dip2px(context, 46f)
val iconHeight = DisplayUtil.dip2px(context, 18f)
```

### 5. 业务逻辑验证

需求文档中的业务规则：

**常见业务规则**：
- 优先级：神评 > 官方回复 > 游戏好友 > 副标题
- 展示规则：未读消息置顶 > 时间倒序
- 权限规则：VIP 用户可见，普通用户不可见

**检查示例**：

需求：优先级 神评 > 官方回复 > 游戏好友

```kotlin
// ❌ 优先级错误
when {
    gameFriends.isNotEmpty() -> showGameFriends()  // 好友优先级太高
    excellentComment != null -> showExcellent()
    officialComment != null -> showOfficial()
}

// ✅ 正确的优先级
when {
    excellentComment != null -> showExcellent()
    officialComment != null -> showOfficial()
    gameFriends.isNotEmpty() -> showGameFriends()
}
```

### 6. 交互反馈检查

需求文档中的用户体验要求：

**检查项**：
- [ ] 点击反馈：按钮点击有视觉反馈（ripple, state）
- [ ] 操作提示：成功/失败有 Toast 或 Dialog
- [ ] 防重复：提交按钮防止重复点击
- [ ] 确认操作：删除等危险操作有二次确认

**示例**：

需求：点赞操作需要防抖，避免重复提交

```kotlin
// ❌ 没有防抖
likeButton.setOnClickListener {
    submitLike()  // 用户可能快速点击多次
}

// ✅ 添加防抖
likeButton.setOnDebounceClickListener(500) {
    submitLike()
}
```

## 审查报告模板（需求感知模式）

当检测到需求文档上下文时，使用以下扩展的报告格式：

```markdown
# Code Review Report (Requirements-Aware)

## 📊 Overview
- **File**: [filename]
- **Lines of Code**: XXX lines
- **Issue Statistics**: 🔴 X critical | ⚠️ Y suggestions | 📋 Z requirements-related
- **Review Mode**: 📋 Requirements-aware review
- **Requirements Source**: [需求文档名称]

---

## 🔴 Critical Issues
[标准的关键问题]

---

## 📋 Requirements-Related Issues

### 功能完整性
| # | Location | Issue | Requirement |
|---|----------|-------|-------------|
| R1 | :245 | 缺少空状态处理 | 需求文档 Page 3: "列表为空时显示空状态" |

### 边界值问题
| # | Location | Issue | Expected |
|---|----------|-------|----------|
| R2 | :378 | 未校验负数 | 需求文档: "评分范围 0-10" |

### 特殊情况
| # | Location | Issue | Requirement |
|---|----------|-------|-------------|
| R3 | :512 | 缺少加载状态 | 需求文档 Page 5: "数据加载时显示动画" |

### UI 规范
| # | Location | Issue | Design Spec |
|---|----------|-------|-------------|
| R4 | :622 | 图标尺寸不符 | 设计稿: 46dp×18dp，实际: 40dp×20dp |

---

## 🎯 Fix Priority

### 🚨 立即修复（功能缺失）
- [ ] #R1: 添加空状态布局和逻辑
- [ ] #R2: 添加评分范围校验 (0-10)

### ⚠️ 重要修复（用户体验）
- [ ] #R3: 实现加载状态 UI
- [ ] #R4: 修正图标尺寸为 46dp×18dp

---

**所有修复完成后，建议进行以下测试**：
- [ ] 空列表场景测试
- [ ] 边界值测试（-1, 0, 10, 11）
- [ ] 网络异常测试
- [ ] UI 视觉走查
```

## 关键提示

1. **总是参考需求文档**：不要仅凭经验判断，要对照需求文档的具体描述
2. **检查隐含需求**：设计稿中的细节、用户体验的常识都是需求
3. **优先级清晰**：功能缺失 > 边界值 > 特殊情况 > UI 规范
4. **给出具体修复建议**：不只是指出问题，要给出代码示例
5. **标注需求来源**：每个问题都标注对应的需求文档位置
