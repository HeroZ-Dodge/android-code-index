# Report Template Reference

This document provides a reference template for the branch review verification report structure.

## Template Structure

```markdown
# 📋 [需求名称] - 分支验证报告

**分支**: `branch-name`
**开发者**: developer-name (git user.name)
**提交数量**: N commits（仅统计本开发者的提交）
**代码变更**: +XXX -YYY 行
**需求文档**:
  - 文档1: `/path/to/requirements.pdf`
  - 文档2: `/path/to/design.png`
  - 文档3: `/path/to/api-spec.pdf`

**涉及需求**（从提交信息提取，仅供参考）:
  - #265448, #265449（从 commit message 中提取）

---

## ⚠️ 重要说明

经过重新筛选，本报告**仅包含开发者 XXX 的提交**，不包括其他开发者的工作：

- ✅ **FileA.kt**（功能A）- 本人开发
- ✅ **FileB.kt**（功能B）- 本人开发
- ❌ **FileC.kt**（功能C）- 其他开发者 开发，已从报告中移除

---

## 一、本分支核心改动范围

根据 Git 提交历史（筛选作者为 XXX），本分支**主要负责实现**：

### ✅ **功能模块A**

涉及文件：

1. **`FileA.kt`** (XXX行)
   - 功能点1
   - 功能点2
   - 功能点3

2. **`HelperA.kt`** (新增)
   - 辅助功能

### ✅ **功能模块B**

涉及文件：

1. **`FileB.kt`**
   - 功能描述

---

## 二、详细功能验证

### ✅ **功能模块A** (FileA.kt)

#### 已实现功能清单

| 功能点 | 状态 | 代码位置 | 验证结果 |
|-------|------|---------|---------|
| 功能1 | ✅ | Line 100 | 实现细节 |
| 功能2 | ✅ | Line 200 | 实现细节 |
| 功能3 | ✅ | Line 300 | 实现细节 |

#### 提交历史追溯

从提交记录可以看到**逐步完善的过程**：

1. **初始实现**（commit hash）
   - 基础功能

2. **优化阶段**（commit hash）
   - Bug修复
   - 性能优化

#### 关键代码片段

**功能1实现**
```kotlin
// Line XXX-YYY
代码示例
```

---

## 三、代码质量评估

### ✅ 优点

1. **架构清晰**
   - 具体优点

2. **性能优化**
   - 具体优点

### ⚠️ 建议

1. **建议项1**
   - 具体建议

---

## 四、需求文档对照

### 本分支负责的需求

根据提交记录和代码改动，本分支**仅负责**：

✅ **需求A**（完整实现）
✅ **需求B**（完整实现）

### 不在本分支范围内的需求

以下需求**未出现在本开发者的改动中**，由其他开发者负责：

- ❌ 需求C（由 XXX 负责）
- ❌ 需求D（由 YYY 负责）

---

## 五、完成度总结

| 负责范围 | 完成度 | 代码量 | 质量评分 |
|---------|--------|--------|---------|
| 功能A | ✅ 100% | XXX行 | ⭐⭐⭐⭐⭐ |
| 功能B | ✅ 100% | YYY行 | ⭐⭐⭐⭐⭐ |
| **总计** | **100%** | **ZZZ行** | **优秀** |

---

## 六、关键提交记录

| 提交号 | 描述 | 影响 |
|-------|------|------|
| hash1 | 描述1 | 🎨 类型 |
| hash2 | 描述2 | 🐛 Bug修复 |
| hash3 | 描述3 | ✨ 新功能 |

---

## 七、最终结论

### ✅ 验证结果

本分支**完整实现**了分配给开发者 XXX 的需求：

- ✅ 功能A - 100%完成
- ✅ 功能B - 100%完成

### 📊 质量评价

- **功能完整性**: ⭐⭐⭐⭐⭐ (5/5)
- **代码质量**: ⭐⭐⭐⭐⭐ (5/5)
- **性能优化**: ⭐⭐⭐⭐⭐ (5/5)
- **可维护性**: ⭐⭐⭐⭐⭐ (5/5)

### 🎯 建议

1. **可以合并** - 代码质量优秀，功能完整
2. **回归测试重点**：
   - 测试点1
   - 测试点2
   - 测试点3

---

**报告生成时间**: YYYY-MM-DD
**验证范围**: `branch-name` 分支的 developer-name 提交
**验证方法**: Git提交历史筛选 + 代码文件深度审查
**作者筛选**: `git log --author="developer-name"`

---

## 🔍 下一步：深度代码审查

验证报告已生成！现在建议进行深度代码审查，结合需求文档检查：

### 建议使用 Code Review

基于需求文档的上下文，深度审查代码实现：

**审查重点**：
- ✅ **特殊情况处理**：空数据、网络异常、权限问题等
- ✅ **边界值检查**：数组越界、空值、极值、负数等
- ✅ **需求一致性**：实现是否完全符合需求文档的细节
- ✅ **用户体验**：加载状态、错误提示、交互反馈等
- ✅ **性能考量**：大数据量、频繁操作、内存使用等

**开始审查**：回复 "code review" 或 "审查代码" 即可启动

**审查范围建议**：
- 推荐选择"未推送的 commits"（选项 2）
- 或选择"所有待定文件"（选项 3）
```

## Key Elements

### Header Section
- Branch name and developer identity
- Commit count (author-filtered)
- Requirement IDs
- Lines of code summary

### Important Notice
- Clear scope definition
- Attribution of files to correct developers
- Explicit exclusions with reasons

### Scope of Work
- List of features/modules handled by this developer
- File-level breakdown with line counts
- Hierarchical organization (module → files → features)

### Detailed Verification
- Feature checklist tables with code locations
- Commit history showing evolution
- Code snippets with explanations
- Technical implementation details

### Code Quality Assessment
- Strengths (architecture, performance, memory, UX)
- Suggestions for improvement
- Evidence-based claims

### Requirements Mapping
- Requirements in scope (✅)
- Requirements out of scope (❌) with attribution

### Completion Summary
- Table format for quick overview
- Percentage completion
- Code volume metrics
- Quality ratings

### Key Commits
- Important commits with impact description
- Use emoji for categorization (🎨 UI, 🐛 Bug, ✨ Feature, etc.)

### Conclusion
- Clear verification result
- Multi-dimensional quality scores
- Specific testing recommendations

### Metadata
- Generation time
- Verification scope
- Methodology used
