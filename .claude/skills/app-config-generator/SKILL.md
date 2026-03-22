---
name: app-config-generator
description: APP 配置代码生成器,专门用于自动生成 APP 配置相关代码。当用户提到"appconfig"、"APP配置"、"添加配置"、"ConfigKey"、"ENTITY_"开头的常量、"configName"、"saveAppSettingConfig"等配置相关方法、"增加一个 appconfig"、"新增配置"、"生成配置"、"创建配置"等关键词时自动触发。
---

# APP 配置代码生成器

根据用户提供的配置信息，自动生成对应的代码，**只修改 2 个文件**。

## 重要提示（必读）

### 核心限制
**你只会修改以下 2 个文件,请不要生成其他代码!!!**

1. **ConfigKey.java** - 配置键定义文件
   - 路径: `serviceconfig/src/main/java/com/netease/gl/serviceconfig/ConfigKey.java`
   - 作用: 定义所有配置项的整数常量
   - 大小: 约 300+ 行

2. **ConfigManager.java** - 配置管理器文件
   - 路径: `serviceconfig/src/main/java/com/netease/gl/service/config/config/ConfigManager.java`
   - 作用: 处理配置的解析和保存
   - 大小: 约 2000+ 行

### 严格遵守的规则
1. **只修改上述 2 个文件**
2. **ConfigKey 数字必须递增** (新数字 = 当前最大数字 + 1)
3. **needCleanSet 必须同步添加** (避免配置清理遗漏)
4. **配置 name 保持原样** (中文或英文直接用于字符串匹配)
5. **必须找对配置模块的处理方法** (不同 ConfigName 对应不同方法)
6. **不要修改 ConfigName.java** (这是只读的常量定义文件)
7. **不要创建新文件**
8. **不要修改其他任何文件**

详细的文件结构、命名规则、案例和工作流程请参考 reference.md。

---

## 完整工作流程

### 阶段 1-2: 输入分析和代码查找（委托 haiku）

**使用 Task 工具委托给 haiku 模型执行**：

Task(
  subagent_type="general-purpose",
  model="haiku",
  prompt="""
  执行以下操作并返回 JSON：
  1. 在 ConfigName.java 中搜索 "{ConfigName}" 确认常量存在
  2. 在 ConfigManager.java 中搜索对应的处理方法名
  3. 读取 ConfigKey.java，找到当前最大的常量数字值
  4. 检查是否已存在同名配置
  返回: {"configNameConst": "...", "saveMethod": "...", "maxKeyValue": N, "exists": true/false}
  """
)

### 阶段 3-4: 命名转换和代码生成（主模型执行）

修改 4 个位置:
1. ConfigKey.java - @IntDef 注解数组末尾添加新常量引用
2. ConfigKey.java - 常量定义区域末尾添加新常量
3. ConfigManager.java - needCleanSet 初始化添加新 key
4. ConfigManager.java - else if 处理链添加新逻辑

### 阶段 5: 验证检查（委托 haiku）

**使用 Task 工具委托给 haiku 模型执行**：

Task(
  subagent_type="general-purpose",
  model="haiku",
  prompt="""
  验证修改结果：
  1. 确认只修改了 ConfigKey.java 和 ConfigManager.java 两个文件
  2. 确认新常量数字值唯一
  3. 确认 needCleanSet 已添加
  返回 JSON: {"valid": true/false, "issues": [...]}
  """
)

---

## 配置模块映射表

| ConfigName (用户输入) | ConfigName 常量 | 处理方法 |
|---------------------|----------------|---------|
| APP设置 | MODULE_APP_SETTING | saveAppSettingConfig |
| 视频设置 | MODULE_VIDEO | saveVideoConfig |
| 聊天设置 | MODULE_CHAT | saveChatConfig |
| 圈子设置 | MODULE_CIRCLE | saveCircleConfig |
| 极速版 | MODULE_LITE_APP | saveLiteAppConfig |
| 游戏配置 | MODULE_GAME_CONFIG | saveGameConfig |
| 用户引导 | MODULE_USER_GUIDE | saveUserGuideConfig |
| 语音房 | MODULE_VOICE_ROOM | saveVoiceRoomConfig |
| 动态配置 | MODULE_FEED | saveFeedConfig |
| 更新配置 | MODULE_UPDATE | saveUpdateConfig |
| 内容配置 | MODULE_CONTENT | saveContentConfig |
| XYQ配置 | MODULE_XYQ | saveXyqConfig |
| 微社区配置 | MODULE_WC | saveWcConfig |
| 直播配置 | MODULE_LIVE | saveLiveConfig |
| 商城配置 | MODULE_SHOP | saveShopConfig |
| 任务配置 | MODULE_TASK | saveTaskConfig |
| 活动配置 | MODULE_ACTIVITY | saveActivityConfig |
| 消息配置 | MODULE_MESSAGE | saveMessageConfig |
| 搜索配置 | MODULE_SEARCH | saveSearchConfig |
| 推荐配置 | MODULE_RECOMMEND | saveRecommendConfig |

如果用户提供的 ConfigName 不在上表中，在 ConfigName.java 中搜索确认。

---

## 输入格式

```
ConfigName: [配置模块名称]
name: [具体配置项名称]
```

## 输出格式

生成代码后输出修改报告，包含：输入信息、各位置修改内容、命名转换说明、验证检查清单。

---

## 文件路径参考

- **ConfigKey.java**: `serviceconfig/src/main/java/com/netease/gl/serviceconfig/ConfigKey.java`
- **ConfigManager.java**: `serviceconfig/src/main/java/com/netease/gl/service/config/config/ConfigManager.java`
- **ConfigName.java**: `serviceconfig/src/main/java/com/netease/gl/serviceconfig/ConfigName.java`（只读）
