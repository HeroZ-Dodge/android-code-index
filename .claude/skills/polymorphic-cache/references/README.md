# Polymorphic Cache - 参考文档

本目录包含 polymorphic-cache skill 的详细参考文档和实战案例。

## 文档列表

### 📚 API 参考
- **[api-reference.md](api-reference.md)** - JsonPolymorphicUtil 和 JsonPolymorphicStructure 的完整 API 文档
  - 序列化/反序列化方法详解
  - typeFieldName 字段名冲突问题
  - 常见用法模式和最佳实践

### 📖 使用示例
- **[examples.md](examples.md)** - 各种场景的代码示例
  - Feed 流场景（视频卡片、图文卡片、直播卡片）
  - 聊天/消息列表场景（文本、图片、语音消息）
  - 游戏Tab场景
  - 嵌套多态数据处理

### ⭐ 实战案例

我们提供了两个完整的生产环境案例，涵盖不同的应用场景：

| 特性 | 案例1：消息Tab | 案例2：游戏Tab |
|------|--------------|--------------|
| **文档** | [case-message-tab.md](case-message-tab.md) | [case-game-tab.md](case-game-tab.md) |
| **场景** | IM消息、聊天列表 | Feed流、动态列表 |
| **数据类型** | 11种（RecentContact子类） | 6种（IFeed子类） |
| **核心亮点** | 数据类型深度分析 | Feed流兼容性设计 |
| **适合人群** | 首次使用、复杂数据分析 | Feed场景、兼容升级 |
| **特色内容** | 错误修复过程记录 | 嵌套多态 + 大小控制 |

#### 案例1：消息Tab页面缓存（复杂数据类型分析）
- **[case-message-tab.md](case-message-tab.md)** - 消息列表页面的完整实战案例
  - **数据类型分析**：如何发现所有11种RecentContact子类型
  - **多维度验证**：ViewModel分析 + DataSource分析 + Grep搜索
  - **架构设计**：ViewModel层缓存 + UInfoRepo用户隔离
  - **错误修复**：遗漏类型的错误、根本原因、修复过程
  - **经验总结**：错误 vs 正确的分析方法对比
  - **适合场景**：IM消息、聊天列表、复杂业务数据

#### 案例2：游戏Tab页面缓存（Feed流场景）
- **[case-game-tab.md](case-game-tab.md)** - Feed流列表页面的集成方案
  - **Feed流场景**：多种卡片类型混合展示（配置、广告、推荐、实体）
  - **兼容性设计**：新旧缓存方案平滑过渡
  - **嵌套多态**：处理 sealed class 的嵌套多态序列化
  - **大小控制**：缓存数据量控制策略（限制前50条）
  - **故障排查**：常见问题和解决方案
  - **适合场景**：Feed流、动态列表、内容聚合页面

## 推荐阅读顺序

### 新手入门
1. 先阅读 **[examples.md](examples.md)** 了解基本用法
2. 遇到问题查阅 **[api-reference.md](api-reference.md)**
3. 实际项目中参考对应的实战案例：
   - IM/聊天场景 → **[case-message-tab.md](case-message-tab.md)**
   - Feed/列表场景 → **[case-game-tab.md](case-game-tab.md)**

### 复杂场景

#### 数据类型复杂（多数据源、DataSource准备）
→ 参考 **[case-message-tab.md](case-message-tab.md)** 的数据类型分析流程

#### Feed流混合卡片场景
→ 参考 **[case-game-tab.md](case-game-tab.md)** 的实现方案

#### 需要兼容旧版本缓存
→ 参考 **[case-game-tab.md](case-game-tab.md)** 的兼容性设计

#### 嵌套多态数据
→ 参考 **[case-game-tab.md](case-game-tab.md)** 的嵌套结构处理

### 遇到问题时
1. 查看对应案例的"故障排查"章节
2. 查阅 **[api-reference.md](api-reference.md)** 了解 API 细节
3. 对照 **[examples.md](examples.md)** 检查代码

## 快速查找

### 按场景查找

**IM/聊天/消息场景**
→ [case-message-tab.md](case-message-tab.md)

**Feed流/动态/内容聚合**
→ [case-game-tab.md](case-game-tab.md)

### 按问题查找

**数据类型分析**
→ [case-message-tab.md - 数据类型分析过程](case-message-tab.md#数据类型分析过程)

**架构设计决策**
→ [case-message-tab.md - 架构设计](case-message-tab.md#架构设计)

**兼容性升级方案**
→ [case-game-tab.md - loadCacheData 方法](case-game-tab.md#修改点-3-修改-loadcachedata-方法加载多态缓存)

**嵌套多态处理**
→ [case-game-tab.md - 嵌套多态数据](case-game-tab.md#3-嵌套多态数据)

**常见错误和修复**
→ [case-message-tab.md - 注意事项](case-message-tab.md#注意事项)
→ [case-game-tab.md - 故障排查](case-game-tab.md#故障排查)

**typeFieldName 冲突**
→ [api-reference.md](api-reference.md)
→ [case-game-tab.md - typeFieldName 冲突检查](case-game-tab.md#1-️-typefieldname-冲突检查)

**缓存大小控制**
→ [case-game-tab.md - 缓存大小控制](case-game-tab.md#4-缓存大小控制)

## 贡献案例

如果你在项目中成功使用了 polymorphic-cache，欢迎分享你的实战案例：

**案例应包含**：
1. 业务场景描述
2. 数据类型分析过程
3. 实现代码和关键文件
4. 遇到的问题和解决方法
5. 性能优化效果
6. 经验教训总结

将案例文档放在本目录，并更新此 README 的文档列表。
