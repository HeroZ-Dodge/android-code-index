# CMS AB 测试代码生成器 - 详细参考文档

## 用户输入示例

### 示例 1: 简单布尔判断
```
name: show_ai
分流描述: 是否展示AI相关功能
target: 1.开启; 0.关闭
byUser: false
```

### 示例 2: 带圈子维度的判断
```
name: circle_staggered
分流描述: 圈子瀑布流布局
target: 1.瀑布流; 0.列表流
byUser: true
needSquareId: true
```

### 示例 3: 获取字符串配置
```
name: launch_ad_button_color
分流描述: 启动页广告按钮颜色
target: #EC4747.红色; #1A203D.蓝色
byUser: false
methodType: string
defaultValue: #1A203D
```

---

## ABTestEntityV2.java 文件结构

### 目标值常量定义（通用）
```java
public class ABTestEntityV2 {
    // 布尔类型目标值
    public static final String TARGET_TRUE = "true";
    public static final String TARGET_FALSE = "false";
    public static final String TARGET_OPEN = "open";
    public static final String TARGET_CLOSE = "close";

    // 数字类型目标值
    public static final String TARGET_0 = "0";
    public static final String TARGET_1 = "1";
    public static final String TARGET_2 = "2";
    public static final String TARGET_3 = "3";
    public static final String TARGET_4 = "4";

    // 特殊类型目标值
    public static final String TARGET_NEW = "NEW";
    public static final String TARGET_KOL = "kol";
    public static final String TARGET_ANCHOR_DISCOVER = "anchor_discover";

    // 全局标识
    public static final String VALUE_TYPE_GLOBAL = "global";
}
```

### AB 测试名称常量（按功能分组）

**社区相关**:
```java
public static final String COMMUNITY_CHOICE_POPUPS = "community_choice_popups";
public static final String CIRCLE_STREAM_RECOMMEND_USER = "circle_stream_recommend_user";
public static final String NORMAL_SQUARE_BISERIAL_FEED = "normal_square_biserial_feed";
public static final String NORMAL_SQUARE_FEED_FRIEND_INTERACT = "normal_square_feed_friend_interact";
```

**红包相关**:
```java
public static final String RED_PACKET_SEND_ENTRANCE = "chatgroup_redpocket_sendentrance";
public static final String RED_PACKET_GET_ENTRANCE = "chatgroup_redpocket_getentrance";
```

**视频相关**:
```java
public static final String VIDEO_SLEEP_TASK = "video_sleep_task";
public static final String VIDEO_WELFARE_TO_TASK_LIST = "video_welfare_to_task_list";
public static final String VIDEO_DA_BING = "video_da_bing";
```

**启动页相关**:
```java
public static final String LAUNCH_AD_BUTTON_COLOR = "launch_ad_button_color";
public static final String LAUNCH_AD_BUTTON_RED_COLOR = "#EC4747";
public static final String LAUNCH_AD_BUTTON_BLUE_COLOR = "#1A203D";
```

**评论相关**:
```java
public static final String FEED_COMMENT_ACHIEVEMENT = "comment_active_chievements";
```

**福利相关**:
```java
public static final String WELFARE_VIP_GIFT_BUFF = "welfare_vip_gift_buff";
```

### 插入位置选择
1. 社区相关: 靠近 `COMMUNITY_CHOICE_POPUPS`
2. 视频相关: 靠近 `VIDEO_SLEEP_TASK`
3. 红包相关: 靠近 `RED_PACKET_SEND_ENTRANCE`
4. 启动页相关: 靠近 `LAUNCH_AD_BUTTON_COLOR`
5. 评论相关: 靠近 `FEED_COMMENT_ACHIEVEMENT`
6. 其他: 根据功能相似性选择或添加到文件末尾

---

## 真实项目案例深度解析

### 案例 1: 社区选择弹窗（简单全局布尔）

**配置**: name=`community_choice_popups`, target=NEW, byUser=true

**ABTestEntityV2.java**:
```java
public static final String COMMUNITY_CHOICE_POPUPS = "community_choice_popups";
```

**IAbTestHelper.java**:
```java
/**
 * 社区选择弹窗
 * @return 是否匹配AB测试
 */
@WorkerThread
boolean isCommunityChoicePopups();
```

**AbTestHelper.java**:
```java
@Override
@WorkerThread
public boolean isCommunityChoicePopups() {
    return isMatchABTest(true, ABTestEntityV2.COMMUNITY_CHOICE_POPUPS, ABTestEntityV2.TARGET_NEW);
}
```

**关键点**: 用户维度(byUser=true), 目标值TARGET_NEW, 全局方法添加@WorkerThread

---

### 案例 2: 圈子瀑布流（带 squareId）

**配置**: name=`normal_square_biserial_feed`, target=1, byUser=true, needSquareId=true, versionNote=3.83.0替换square_main_feed_flowStyle

**ABTestEntityV2.java**:
```java
public static final String NORMAL_SQUARE_BISERIAL_FEED = "normal_square_biserial_feed";
```

**IAbTestHelper.java**:
```java
/**
 * 圈子瀑布流布局
 * @param squareId 圈子ID
 * @return 是否匹配AB测试
 */
boolean isCircleStaggered(String squareId);
```

**AbTestHelper.java**:
```java
@Override
public boolean isCircleStaggered(String squareId) {
    // 3.83.0，替换square_main_feed_flowStyle
    return isMatchABTest(true, ABTestEntityV2.NORMAL_SQUARE_BISERIAL_FEED, ABTestEntityV2.TARGET_1, squareId);
}
```

**关键点**: 带squareId不添加@WorkerThread, 带版本和功能替换注释

---

### 案例 3: 启动页广告按钮颜色（字符串配置）

**配置**: name=`launch_ad_button_color`, target=#EC4747.红色;#1A203D.蓝色, byUser=false, methodType=string, defaultValue=#1A203D

**ABTestEntityV2.java**:
```java
public static final String LAUNCH_AD_BUTTON_COLOR = "launch_ad_button_color";
public static final String LAUNCH_AD_BUTTON_RED_COLOR = "#EC4747";
public static final String LAUNCH_AD_BUTTON_BLUE_COLOR = "#1A203D";
```

**IAbTestHelper.java**:
```java
/**
 * 获取启动页广告按钮颜色
 * @return 颜色值
 */
@WorkerThread
String getLaunchAdButtonColor();
```

**AbTestHelper.java**:
```java
@Override
@WorkerThread
public String getLaunchAdButtonColor() {
    return getABTestTarget(false, ABTestEntityV2.LAUNCH_AD_BUTTON_COLOR, "", ABTestEntityV2.LAUNCH_AD_BUTTON_BLUE_COLOR);
}
```

**关键点**: String返回类型, 特定颜色值常量, squareId传空字符串""

---

### 案例 4: 评论成就（多目标值）

**配置**: name=`comment_active_chievements`, target=1.启用;2.仅首评, byUser=true, 一个AB测试对应两个方法

**ABTestEntityV2.java**:
```java
public static final String FEED_COMMENT_ACHIEVEMENT = "comment_active_chievements";
```

**IAbTestHelper.java**:
```java
boolean isMatchCommentAchievement();
boolean isMatchCommentAchievementOnlyFirstComment();
```

**AbTestHelper.java**:
```java
@Override
public boolean isMatchCommentAchievement() {
    return isMatchABTest(true, ABTestEntityV2.FEED_COMMENT_ACHIEVEMENT, ABTestEntityV2.TARGET_1);
}

@Override
public boolean isMatchCommentAchievementOnlyFirstComment() {
    return isMatchABTest(true, ABTestEntityV2.FEED_COMMENT_ACHIEVEMENT, ABTestEntityV2.TARGET_2);
}
```

---

### 案例 5: 视频达冰（特殊 squareId 处理）

**配置**: name=`video_da_bing`, target=1, byUser=true, needSquareId=true, 特殊说明: global_video_tab映射为global

**AbTestHelper.java**:
```java
@Override
public boolean isMatchVideoDaBing(String squareId) {
    // 视频推荐tab 和 ABTest 指向的圈子id不一致
    String targetSquareId = TextUtils.equals(squareId, "global_video_tab") ? ABTestEntityV2.VALUE_TYPE_GLOBAL : squareId;
    if (TextUtils.equals(targetSquareId, ABTestEntityV2.VALUE_TYPE_GLOBAL)) {
        return isMatchABTest(true, ABTestEntityV2.VIDEO_DA_BING, ABTestEntityV2.TARGET_1, targetSquareId, true);
    } else {
        return isMatchABTest(true, ABTestEntityV2.VIDEO_DA_BING, ABTestEntityV2.TARGET_1, targetSquareId);
    }
}
```

---

### 案例 6: 福利 VIP 礼物增益（字符串+squareId）

**配置**: name=`welfare_vip_gift_buff`, target=0.关闭;1.开启;2.双倍, byUser=true, needSquareId=true, methodType=string, defaultValue=0

**AbTestHelper.java**:
```java
@Override
public String getWelfareVipGiftBuff(String squareId) {
    return getABTestTarget(true, ABTestEntityV2.WELFARE_VIP_GIFT_BUFF, squareId, ABTestEntityV2.TARGET_0);
}
```

**使用示例**:
```java
String buff = AbTestHelper.getInstance().getWelfareVipGiftBuff(squareId);
if ("1".equals(buff)) {
    // 开启增益
} else if ("2".equals(buff)) {
    // 双倍增益
} else {
    // 关闭
}
```

---

### 案例 7: 圈子好友互动标签（squareId + isGlobal）

**配置**: name=`normal_square_feed_friend_interact`, target=1, byUser=true, needSquareId=true, isGlobal=true

**AbTestHelper.java**:
```java
@Override
public boolean isSquareShowFriendInteractTagStaggered(String squareId) {
    return isMatchABTest(true, ABTestEntityV2.NORMAL_SQUARE_FEED_FRIEND_INTERACT, ABTestEntityV2.TARGET_1, squareId, true);
}
```

**关键点**: 使用5参数版本isMatchABTest，最后一个参数true表示支持全局

---

## 特殊场景处理

### 场景: 更新现有的 AB 测试

**输入**:
```
操作: 更新
name: show_ai（已存在）
新增 target: 3.测试模式
新增方法: isShowAiTestMode()
```

**处理**: 不修改常量定义（已存在），只添加新的接口方法和实现方法。

---

## 常见错误详解

### 错误 1: squareId 传 null
```java
// 错误
return getABTestTarget(false, ABTestEntityV2.LAUNCH_AD_BUTTON_COLOR, null, ...);
// 正确
return getABTestTarget(false, ABTestEntityV2.LAUNCH_AD_BUTTON_COLOR, "", ...);
```

### 错误 2: 目标值用字符串字面量
```java
// 错误
return isMatchABTest(true, ABTestEntityV2.SHOW_AI, "1");
// 正确
return isMatchABTest(true, ABTestEntityV2.SHOW_AI, ABTestEntityV2.TARGET_1);
```

### 错误 3: @WorkerThread 使用错误
```java
// 全局方法 - 添加 @WorkerThread
@Override
@WorkerThread
public boolean isCommunityChoicePopups() { ... }

// 带参数方法 - 不添加 @WorkerThread
@Override
public boolean isCircleStaggered(String squareId) { ... }
```

### 错误 4: 接口和实现签名不一致
参数类型必须完全一致，squareId 始终用 String 类型。

### 错误 5: 缺少 @Override 注解
所有实现类方法都必须添加 `@Override`。

### 错误 6: 常量命名格式错误
```java
// 错误
public static final String showAi = "show_ai";
// 正确
public static final String SHOW_AI = "show_ai";
```

---

## 方法模式对比表

| 模式 | byUser | squareId | isGlobal | 返回类型 | @WorkerThread | 使用场景 |
|------|--------|----------|----------|---------|---------------|---------|
| 模式 1 | true | 无 | 无 | boolean | 有 | 用户维度全局开关 |
| 模式 2 | false | 无 | 无 | boolean | 有 | 设备维度全局开关 |
| 模式 3 | true/false | 有 | 无 | boolean | 无 | 圈子维度开关 |
| 模式 4 | true/false | 有 | true | boolean | 无 | 圈子+全局开关 |
| 模式 5 | true/false | 无 | 无 | String | 有 | 全局字符串配置 |
| 模式 6 | true/false | 有 | 无 | String | 无 | 圈子字符串配置 |
| 模式 7 | true/false | 有(特殊) | 条件 | boolean | 无 | 特殊逻辑处理 |

---

## 参数说明

### byUser 参数
- **true**: 基于用户 ID 分桶（同一用户在不同设备上看到相同配置）
- **false**: 基于设备 ID 分桶（同一用户在不同设备上可能不同）

### squareId 参数
- 圈子维度的分桶标识
- 特殊值: `"global"` 或 `ABTestEntityV2.VALUE_TYPE_GLOBAL` 表示全局配置
- 不需要时传 `""` 空字符串（不是 null）

### isGlobal 参数
- **true**: 支持全局配置，squareId="global" 时生效
- **false**: 仅圈子维度生效

### defaultValue 参数
- 未命中 AB 测试时的默认返回值
- 选择最保守、最稳定的配置值

---

## 命名转换详细对照表

### 常量名转换
| 输入 (name) | 输出 (常量名) |
|------------|-------------|
| show_ai | SHOW_AI |
| circle_staggered | CIRCLE_STAGGERED |
| video_auto_play | VIDEO_AUTO_PLAY |
| launch_ad_button_color | LAUNCH_AD_BUTTON_COLOR |
| normal_square_biserial_feed | NORMAL_SQUARE_BISERIAL_FEED |

### 方法名转换
| 输入 (name) | Boolean 方法 | String 方法 |
|------------|-------------|------------|
| show_ai | isShowAi() | getShowAi() |
| circle_staggered | isCircleStaggered() | getCircleStaggered() |
| launch_ad_button_color | isLaunchAdButtonColor() | getLaunchAdButtonColor() |

### 多目标值方法命名
| AB 测试名 | Target | 方法名 |
|----------|--------|-------|
| feed_comment_achievement | 1 | isMatchCommentAchievement() |
| feed_comment_achievement | 2 | isMatchCommentAchievementOnlyFirstComment() |
