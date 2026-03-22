# Polymorphic Cache Skill - 使用反馈

记录实际使用中遇到的问题和改进建议。

## 反馈模板

### 测试场景 1: [场景描述]
**日期**: YYYY-MM-DD
**触发方式**: [用户的提问或命令]
**期望行为**: [期望 Claude 做什么]
**实际行为**: [Claude 实际做了什么]
**问题**: [哪里不符合预期]
**改进建议**: [如何改进 SKILL.md]

---

## 已记录的反馈

### 示例 1: 未能识别触发词
**日期**: 2026-01-21
**触发方式**: "帮我缓存页面数据"
**期望行为**: 触发 polymorphic-cache skill
**实际行为**: 使用了普通的 JSON 序列化方案
**问题**: "缓存页面数据" 没有包含在触发词中
**改进建议**: 在 description 中添加 "缓存页面"、"页面数据缓存" 等触发词

### 示例 2: 直接创建模型而非分析
**日期**: 2026-01-21
**触发方式**: "帮我实现消息列表的多态缓存"
**期望行为**: 先询问用户现有的数据模型是什么
**实际行为**: 直接创建了 Message、TextMessage、ImageMessage 等类
**问题**: 没有遵循"先分析再实现"的流程
**改进建议**: 在 SKILL.md 开头强调"首先询问用户是否已有数据模型"

---

### 反馈 1: typeFieldName 字段冲突问题 ⚠️ 严重
**日期**: 2026-01-22
**测试者**: dodge
**触发方式**: "帮我测试 游戏Tab 这个页面，为这个页面添加 页面缓存"
**期望行为**:
- 分析页面数据结构，识别多态类型
- 实现 JsonPolymorphicStructure，使用安全的 typeFieldName
- 生成可正常工作的缓存代码

**实际行为**:
- ✅ 正确分析了数据结构（6个 IFeed 子类）
- ✅ 正确实现了 JsonPolymorphicStructure
- ❌ 使用了 `typeFieldName = "feedType"`，与 DiscoveryGameLibWrapper 的业务字段冲突
- ❌ 虽然在注释中提到"检查字段冲突"，但实际检查不够充分

**问题详情**:
```kotlin
// 业务类中已有 feedType 字段
class DiscoveryGameLibWrapper(
    val config: AppConfigEntity,
    val feedType: Int,  // 业务字段
    val gameList: List<GameInfoEntity>
) : AppConfigWrapData(config, feedType)

// 生成的代码使用了相同的名称
object GameTabFeedStructure : JsonPolymorphicStructure<IFeed> {
    override fun typeFieldName() = "feedType"  // ❌ 冲突！
}
```

**根本原因**:
1. SKILL.md 示例使用了常见的业务字段名（`feedType`、`type`）
2. 注释中建议"检查字段是否重名"，但依赖人工检查容易遗漏
3. 没有提供明确的安全命名规范
4. 模板默认值是 `"type"`，风险很高

**改进措施**:
1. ✅ 更新 SKILL.md - 使用 `__gameTab_polyType__` 作为示例
2. ✅ 强化 api-reference.md - 添加真实冲突案例和最佳实践章节
3. ✅ 更新模板 - 默认值改为 `__moduleName_polyType__`
4. ✅ 建立命名规范 - 强制使用业务前缀避免冲突
5. ✅ 创建修复报告 - BUGFIX_typeFieldName_conflict.md

**改进建议**:
- **核心原则**: 不要依赖人工检查字段冲突，直接使用安全命名
- **强制规范**: typeFieldName 必须使用 `__<businessModule>_polyType__` 格式
- **文档更新**: 在多处重复强调，提供真实案例警告
- **模板优化**: 默认值应该是安全的，而非需要修改的

**用户反馈原文**:
> "反馈skill测试结果，GameTabFeedStructure.kt 中定义的 feedType 已经在 DiscoveryGameLibWrapper 中定义了，以后 typeFieldName 应该加上业务模块前缀，避免自动命名冲突"

**影响范围**: 🔴 高 - 会导致序列化/反序列化崩溃或数据覆盖

**修复状态**: ✅ 已修复并更新所有相关文档

---

## 待测试场景

- [x] ~~字段名冲突场景~~ - 已测试，发现问题并修复
- [x] ~~Feed 流列表场景~~ - 已测试（游戏Tab场景）
- [ ] 消息列表场景
- [ ] 配置项场景
- [ ] 嵌套多态数据场景
- [ ] 反序列化失败降级场景
- [ ] 大数据量性能测试（1000+ 条）
- [ ] 跨版本兼容性测试
