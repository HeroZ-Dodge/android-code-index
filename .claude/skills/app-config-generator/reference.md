# APP 配置代码生成器 - 详细参考文档

## 文件结构详解

### ConfigKey.java 完整结构

这个文件包含 **2 个关键部分**，都需要修改：

#### 部分 1: @IntDef 注解数组（约 30 行）

```java
@IntDef({
    ConfigKey.ENTITY_UPDATE_INFO,
    ConfigKey.ENTITY_RECOMMEND_ENTER_CONTENT,
    ConfigKey.ENTITY_FEED_POST_MUSIC,
    ConfigKey.ENTITY_XYQ_VOICE_URL,
    ConfigKey.ENTITY_GAME_ICON,
    // ... 200+ 个常量引用
    ConfigKey.ENTITY_LITE_CPS_DOWNLOAD,
    ConfigKey.ENTITY_VIDEO_PRELOAD,
    ConfigKey.ENTITY_FEED_QUICK_COMMENT,
    ConfigKey.SQUARE_RANKING_LIST_WHITELIST,  // 最后一个
})
@Retention(RetentionPolicy.SOURCE)
@Target({ElementType.FIELD, ElementType.PARAMETER})
public @interface ConfigKey {
```

**修改位置**: 在数组末尾（最后一个常量后）添加新的常量引用

#### 部分 2: 常量定义区域（约 270 行）

```java
// 更新信息
int ENTITY_UPDATE_INFO = 0;

// 推荐内容入口
int ENTITY_RECOMMEND_ENTER_CONTENT = 1;

// ... 中间省略 260+ 个常量

// 广场排行榜白名单
int SQUARE_RANKING_LIST_WHITELIST = 287;  // 当前最大值
```

**命名规则**:
- 全大写英文，使用下划线连接单词
- 常见前缀: `ENTITY_`, `LITE_`, `VIDEO_`, `FEED_` 等
- 注释使用中文说明配置含义

**数字分配**:
- 从 0 开始递增，必须唯一
- 新常量数字 = 当前最大数字 + 1

---

### ConfigManager.java 完整结构

这个文件包含 **1 个主入口方法** 和 **30+ 个配置模块处理方法**。

#### 主入口方法 parseConfigs()

```java
public static void parseConfigs(@Nullable List<AppConfigProtoResult> list) {
    if (CollectionUtil.isEmpty(list)) {
        return;
    }
    Map<String, AppConfigProtoResult> configMap = new HashMap<>();
    for (AppConfigProtoResult result : list) {
        if (result != null && !TextUtils.isEmpty(result.moduleName)) {
            configMap.put(result.moduleName, result);
        }
    }
    saveUpdateConfig(configMap);
    saveContentConfig(configMap);
    saveFeedConfig(configMap);
    saveXyqConfig(configMap);
    saveAppSettingConfig(configMap);
    saveWcConfig(configMap);
    saveGameConfig(configMap);
    saveLiteAppConfig(configMap);
    saveVideoConfig(configMap);
    saveChatConfig(configMap);
    saveCircleConfig(configMap);
    saveUserGuideConfig(configMap);
    saveVoiceRoomConfig(configMap);
    // ... 更多模块（约 30+ 个）
}
```

#### 配置模块处理方法结构（以 saveLiteAppConfig 为例）

```java
private static void saveLiteAppConfig(Map<String, AppConfigProtoResult> configMap) {
    AppConfigProtoResult result = configMap.get(ConfigName.MODULE_LITE_APP);

    Set<Integer> needCleanSet = new HashSet<>();
    needCleanSet.add(ConfigKey.ENTITY_LITE_CPS_DOWNLOAD);
    needCleanSet.add(ConfigKey.ENTITY_LITE_U5_CLOUD_PLAY);
    // ... 更多配置

    if (result != null && !CollectionUtil.isEmpty(result.itemList)) {
        for (AppConfigEntity configEntity : result.itemList) {
            if (!configEntity.isOsValid() || configEntity.hidden) {
                continue;
            }
            final String configName = configEntity.name;

            if ("下载兜底拦截".equals(configName)) {
                needCleanSet.remove(ConfigKey.ENTITY_LITE_CPS_DOWNLOAD);
                ConfigManager.saveConfigEntity(AppProfile.getContext(), configEntity, ConfigKey.ENTITY_LITE_CPS_DOWNLOAD);
            } else if ("蛋仔地图试玩".equals(configName)) {
                needCleanSet.remove(ConfigKey.ENTITY_LITE_U5_CLOUD_PLAY);
                ConfigManager.saveConfigEntity(AppProfile.getContext(), configEntity, ConfigKey.ENTITY_LITE_U5_CLOUD_PLAY);
            }
            // ... 更多 else if
        }
    }

    for (Integer key : needCleanSet) {
        ConfigManager.saveConfigEntity(AppProfile.getContext(), null, key);
    }
}
```

**needCleanSet 的作用**:
- 记录所有需要处理的配置 key
- 如果配置在服务器数据中存在，从 set 中移除
- 最后剩余的 key 表示服务器已删除该配置，需要清理本地缓存

#### 配置模块处理方法需要修改的 2 个位置

**位置 1: needCleanSet 初始化**
```java
Set<Integer> needCleanSet = new HashSet<>();
needCleanSet.add(ConfigKey.ENTITY_EXISTING_CONFIG);
needCleanSet.add(ConfigKey.ENTITY_NEW_CONFIG);  // <- 添加新配置 key
```

**位置 2: else if 处理链**
```java
} else if ("新配置名".equals(configName)) {  // <- 添加新的处理逻辑
    needCleanSet.remove(ConfigKey.ENTITY_NEW_CONFIG);
    ConfigManager.saveConfigEntity(AppProfile.getContext(), configEntity, ConfigKey.ENTITY_NEW_CONFIG);
}
```

---

## 命名转换规则详解

### 配置 name（configName）

**规则**: **保持原样，直接用于字符串匹配**

### ConfigKey 常量命名

**规则**: 必须转换为**全大写英文 + 下划线**格式

#### 命名转换步骤

1. **理解配置的业务含义** - 分析配置名的中文/英文含义
2. **识别关键词和专有名词** - 技术术语: U5, CPS, AI, H5, WebRTC 等
3. **选择合适的前缀**:
   - `ENTITY_` - 最常用的通用前缀
   - `ENTITY_LITE_` - 极速版专用配置
   - `ENTITY_VIDEO_` - 视频模块配置
   - `ENTITY_FEED_` - 动态模块配置
   - `ENTITY_LIVE_` - 直播模块配置
   - `ENTITY_CHAT_` - 聊天模块配置
4. **翻译并组合** - 将中文翻译为英文，使用下划线连接，全部大写
5. **验证命名规范** - 全大写、下划线连接、语义清晰、长度适中（建议 30 字符以内）

#### 中文配置名转换示例

| 中文配置名 | 常量名 | 转换逻辑 |
|-----------|--------|---------|
| 下载兜底拦截 | ENTITY_LITE_CPS_DOWNLOAD | 识别业务场景(CPS下载) |
| 蛋仔地图试玩 | ENTITY_LITE_U5_CLOUD_PLAY | 识别技术关键词(U5/云玩) |
| 圈子新框架 | ENTITY_LITE_CIRCLE_TAB | 识别功能模块(圈子Tab) |
| 激励视频组件 | ENTITY_LITE_VIDEO_COMPONENT | 直接翻译 |
| 点卡微信支付 | ENTITY_LITE_WECHAT_PAY | 识别专有名词(WeChat) |
| AI功能开关 | ENTITY_AI_FEATURE_SWITCH | 保留缩写(AI) |
| 广场排行榜白名单 | SQUARE_RANKING_LIST_WHITELIST | 无ENTITY前缀 |

#### 特殊情况处理

- **包含数字**: 数字保持不变，如 `H5页面跳转` -> `ENTITY_H5_PAGE_JUMP`
- **包含缩写**: 缩写全大写，如 `WebRTC配置` -> `ENTITY_WEBRTC_CONFIG`
- **包含特殊符号**: 替换为下划线
- **过长配置名**: 提取核心关键词，避免过长
- **歧义配置名**: 根据 ConfigName 模块添加适当前缀区分

---

## 常见错误示例

1. **ConfigKey 数字重复** - 新常量数字必须唯一递增
2. **忘记在 @IntDef 数组中添加引用** - 两个位置都必须修改
3. **忘记在 needCleanSet 中添加** - 会导致配置清理遗漏
4. **配置 name 字符串不匹配** - 必须完全匹配用户输入
5. **找错了配置模块处理方法** - 参考配置模块映射表
6. **常量命名不符合规范** - 全大写+下划线
7. **修改了 ConfigName.java** - 这是只读文件
8. **忘记调用 saveConfigEntity** - else if 中必须调用
9. **注释格式不规范** - 行尾中文注释
10. **常量前缀选择不当** - 根据模块选择
11. **创建了新文件** - 只修改已有的 2 个文件
12. **特殊字符未转义** - 引号等需要转义

---

## 查找未知 ConfigName 的方法

```bash
# 1. 在 ConfigName.java 中搜索常量定义
grep -i "关键词" serviceconfig/src/main/java/com/netease/gl/serviceconfig/ConfigName.java

# 2. 根据常量名在 ConfigManager.java 中搜索使用位置
grep -r "MODULE_XXX" serviceconfig/src/main/java/com/netease/gl/service/config/config/ConfigManager.java

# 3. 查找最大数字
grep -oE "= [0-9]+" ConfigKey.java | grep -oE "[0-9]+" | sort -n | tail -1
```

---

## 注释规范

### ConfigKey.java 注释格式

```java
int CONSTANT_NAME = NUMBER;  // 中文描述
```

- 使用行尾注释（`//`），注释内容为中文，注释前有两个空格
- 不要使用块注释、上方注释或英文注释

### ConfigManager.java 注释格式

一般不需要添加注释，代码结构本身已经很清晰。
