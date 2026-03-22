# ABTestV2 代码生成规则详细参考

## 方法签名规则（重要）

### 规则 1: 接口方法 vs 实现方法

**接口方法（ABTestV2Sdk.kt）- 必须有默认值**:
```kotlin
// Boolean 判断方法
fun is[功能名](forceReq: Boolean = false): Observable<Boolean>

// String 获取方法
fun get[功能名](forceReq: Boolean = false): Observable<String>

// SquareId 维度方法
fun is[功能名]BySquare(squareId: String?, forceReq: Boolean = false): Observable<Boolean>
fun get[功能名]BySquare(squareId: String?, forceReq: Boolean = false): Observable<String>

// 批量判断方法
fun get[功能名]Features(forceReq: Boolean = false): Observable<List<String>>
```

**实现方法（ABTestV2SdkImp.kt）- override 不能有默认值**:
```kotlin
// Boolean 判断方法
override fun is[功能名](forceReq: Boolean): Observable<Boolean> {
    return isMatchABTest(true, ABTestType.XXX, "on", forceReq)
}

// String 获取方法
override fun get[功能名](forceReq: Boolean): Observable<String> {
    return getABTestTarget(true, ABTestType.XXX, forceReq)
}

// SquareId 维度方法
override fun is[功能名]BySquare(squareId: String?, forceReq: Boolean): Observable<Boolean> {
    return isMatchABTestBySquareId(true, squareId, ABTestType.XXX, "on", forceReq)
}

// 批量判断方法
override fun get[功能名]Features(forceReq: Boolean): Observable<List<String>> {
    return isMatchABTest(true, listOf(
        ABTestType.XXX_FEATURE1,
        ABTestType.XXX_FEATURE2
    ), "on", forceReq)
}
```

### 规则 2: 核心实现方法说明

**ABTestV2SdkImp 提供的基础方法**:
```kotlin
// 1. 判断是否匹配（单个）
isMatchABTest(
    byUser: Boolean,        // true=用户维度, false=设备维度
    type: ABTestType?,      // AB 测试类型
    target: String?,        // 目标值，通常是 "on"
    forceReq: Boolean       // 是否强制请求
): Observable<Boolean>

// 2. 获取配置值
getABTestTarget(
    byUser: Boolean,        // true=用户维度, false=设备维度
    type: ABTestType?,      // AB 测试类型
    forceReq: Boolean       // 是否强制请求
): Observable<String>

// 3. 基于 squareId 判断
isMatchABTestBySquareId(
    byUser: Boolean,        // true=用户维度, false=设备维度
    squareId: String?,      // 圈子 ID
    type: ABTestType?,      // AB 测试类型
    target: String?,        // 目标值，通常是 "on"
    forceReq: Boolean       // 是否强制请求
): Observable<Boolean>

// 4. 基于 squareId 获取
getABTestTargetBySquareId(
    byUser: Boolean,        // true=用户维度, false=设备维度
    squareId: String?,      // 圈子 ID
    type: ABTestType?,      // AB 测试类型
    forceReq: Boolean       // 是否强制请求
): Observable<String>

// 5. 批量判断（返回匹配的 sceneSn 列表）
isMatchABTest(
    byUser: Boolean,           // true=用户维度, false=设备维度
    typeList: List<ABTestType>?, // AB 测试类型列表
    target: String?,           // 目标值，通常是 "on"
    forceReq: Boolean          // 是否强制请求
): Observable<List<String>>
```

**参数说明**:
- `byUser`: 几乎总是使用 `true`（用户维度）
- `target`: 对于 Boolean 判断方法，通常使用 `"on"`
- `forceReq`: 直接传递用户提供的参数

## SceneSn.kt 生成规则

### 规则 1.1: 私有常量定义
将场景字符串的每个部分转换为私有常量：
```kotlin
private const val SCENE_[大写场景名] = "[原始场景名]"
```

**命名规则**:
- 使用全大写 + 下划线分隔
- 保持原始场景名不变
- 作为私有常量使用

**示例**:
```kotlin
private const val SCENE_VIDEO_PLAYER = "video_player"
private const val SCENE_PIP = "pip"
private const val SCENE_INCENTIVE = "incentive"
private const val SCENE_AI = "ai"
```

### 规则 1.2: 公开常量定义

**单场景常量**（不需要组合）:
```kotlin
const val SCENE_[功能描述大写] = "[场景字符串]"
```

**组合场景常量**（使用 buildSceneSn）:
```kotlin
val SCENE_[功能描述大写]: String = buildSceneSn(SCENE_常量1, "片段2", ...)
```

**示例**:
```kotlin
// 两个常量组合
val SCENE_VIDEO_PLAYER_PIP: String = buildSceneSn(SCENE_VIDEO_PLAYER, "pip")

// 常量 + 字符串组合
val SCENE_VIDEO_NEXT_GUIDE: String = buildSceneSn(SCENE_VIDEO_PLAYER, "video_next_guide")

// 多个常量组合
val SCENE_FOLLOW_LIVE_KANDIAN_TAB: String = buildSceneSn(SCENE_FOLLOW_LIVE, SCENE_KANDIAN, "tab")
```

### 规则 1.3: 场景分组注释

**有分类的场景**（使用 buildSceneSn 组合）应该分组并添加注释：
```kotlin
// [功能模块名] - start
private const val SCENE_VIDEO_PLAYER = "video_player"
val SCENE_VIDEO_PLAYER_PIP = buildSceneSn(SCENE_VIDEO_PLAYER, "pip")
val SCENE_VIDEO_PLAYER_AUTO_PLAY = buildSceneSn(SCENE_VIDEO_PLAYER, "auto_play_next")
// [功能模块名] - end
```

### 规则 1.4: 独立场景的位置

**无分类的独立场景**（单独定义的常量）应该放在**文件最后**，在 `buildSceneSn` 方法之前：

```kotlin
// 独立场景放在这里（文件最后）
const val SCENE_SIDEBAR_AI = "ai_sidebar"  // 侧边栏是否展示ai玩法
const val SCENE_GLOBAL_PLAZA = "global_plaza"  // 公域新首页实验配置

@JvmStatic
fun buildSceneSn(vararg scenes: String): String {
    return scenes.joinToString(SCENE_SEPARATOR)
}
```

**判断标准**：
- 使用 `buildSceneSn()` 组合的场景 -> 放在对应的分组中
- 独立定义的常量（不使用 buildSceneSn） -> 放在文件最后
- 如果独立场景有明确的分组归属，可以放在分组中，但要使用 `buildSceneSn` 保持一致性

## ABTestType.kt 生成规则

### 规则 2.1: 枚举项定义
```kotlin
[枚举名](
    sceneSn: String,    // 场景 sn，引用 SceneSn 常量
    key: String,        // 实验 key
    default: String     // 默认值
)
```

**命名规则**:
- 枚举名：全大写 + 下划线分隔
- 与 SceneSn 常量名保持对应关系（去掉 SCENE_ 前缀）

**示例**:
```kotlin
VIDEO_PIP(SceneSn.SCENE_VIDEO_PIP, "algorithm_name", "off"),
VIDEO_NEXT_GUIDE(SceneSn.SCENE_VIDEO_NEXT_GUIDE, "algorithm_name", "0"),
INCENTIVE_WELFARE_CARD(SceneSn.SCENE_WELFARE_CARD, "algorithm_name", "off"),
```

### 规则 2.2: 参数说明

**key 参数**: 通常固定为 `"algorithm_name"`

**default 参数的常见值**:
| 默认值 | 使用场景 | 说明 |
|--------|----------|------|
| `"off"` | 功能开关 | 最常见，表示默认关闭 |
| `"on"` | 功能开关 | 默认开启 |
| `"0"` | 数值配置 | 数字配置，表示默认值为 0 |
| `"1"`, `"2"`, `"3"` | 数值配置 | 其他数字默认值 |
| `"default"` | 字符串配置 | 使用默认配置 |

**选择默认值的原则**:
- 功能开关类：优先使用 `"off"`
- 数值配置类：使用具体数字（如 `"0"`, `"1"`）
- 字符串配置类：使用 `"default"` 或空字符串

## 命名转换规则详解

### 转换规则 1: 场景字符串 -> 常量名

```
下划线分隔 -> 全大写 + 下划线分隔
video_player -> SCENE_VIDEO_PLAYER
pip -> SCENE_PIP
```

**组合场景转换**:
```
video_player|pip -> SCENE_VIDEO_PLAYER_PIP
follow_live|kandian_tab -> SCENE_FOLLOW_LIVE_KANDIAN_TAB
```

**单场景转换**（没有 | 分隔符）:
```
ai_sidebar -> SCENE_SIDEBAR_AI (可以重新组织单词顺序以提高可读性)
fulikapian -> SCENE_WELFARE_CARD (可以使用更有意义的英文名)
```

### 转换规则 2: 场景字符串 -> 枚举名

**规则**: 与常量名类似，但去掉 `SCENE_` 前缀

```
SCENE_VIDEO_PLAYER_PIP -> VIDEO_PIP (简化，去掉重复部分)
SCENE_VIDEO_NEXT_GUIDE -> VIDEO_NEXT_GUIDE
SCENE_WELFARE_CARD -> INCENTIVE_WELFARE_CARD (添加上下文前缀)
```

### 转换规则 3: 场景字符串 -> 方法名

**转换步骤**:
1. 将下划线转换为驼峰命名
2. 首字母小写
3. 添加方法前缀（is/get）

**示例**:
```
video_player|pip -> isVideoPip() / getVideoPip()
video_next_guide -> isVideoNextGuide() / getVideoNextGuide()
follow_live|kandian_tab -> isFollowLiveKandianTab() / getFollowLiveKandianTab()
```

**特殊情况处理**:
- 连续的大写字母：`ai_sidebar` -> `isAISidebar()` 或 `isAiSidebar()`
- 数字：`video2` -> `isVideo2()`
- 单字母：`a_b_test` -> `isABTest()`

## 常见错误和避免方法

### 错误 1: 接口方法缺少默认值
```kotlin
// ABTestV2Sdk.kt
fun isVideoPip(forceReq: Boolean): Observable<Boolean>  // 缺少默认值 -> 错误
fun isVideoPip(forceReq: Boolean = false): Observable<Boolean>  // 有默认值 -> 正确
```

### 错误 2: 实现方法添加了默认值
```kotlin
// ABTestV2SdkImp.kt
override fun isVideoPip(forceReq: Boolean = false): Observable<Boolean> // override 不能有默认值 -> 错误
override fun isVideoPip(forceReq: Boolean): Observable<Boolean> // 无默认值 -> 正确
```

### 错误 3: target 参数错误
```kotlin
// Boolean 判断用 "on"，不是 "off"
return isMatchABTest(true, ABTestType.VIDEO_PIP, "on", forceReq)  // 正确
```

### 错误 4: 场景常量直接使用字符串
```kotlin
val SCENE_VIDEO_PIP = buildSceneSn("video_player", "pip")  // 错误：直接使用字符串
val SCENE_VIDEO_PIP = buildSceneSn(SCENE_VIDEO_PLAYER, "pip")  // 正确：使用常量
```

## 完整示例

### 示例 1: 简单的功能开关

**输入**: `video_player|pip` (小窗播放)

**1. SceneSn.kt**:
```kotlin
// 视频播放器 - start
private const val SCENE_VIDEO_PLAYER = "video_player"
val SCENE_VIDEO_PIP = buildSceneSn(SCENE_VIDEO_PLAYER, "pip")
// 视频播放器 - end
```

**2. ABTestType.kt**:
```kotlin
VIDEO_PIP(SceneSn.SCENE_VIDEO_PIP, "algorithm_name", "off"),
```

**3. ABTestV2Sdk.kt**:
```kotlin
/**
 * 视频小窗播放是否启用
 * @param forceReq 是否强制请求
 * @return 布尔值 Observable
 */
fun isVideoPip(forceReq: Boolean = false): Observable<Boolean>

/**
 * 获取视频小窗播放配置值
 * @param forceReq 是否强制请求
 * @return 配置值字符串 Observable
 */
fun getVideoPipConfig(forceReq: Boolean = false): Observable<String>
```

**4. ABTestV2SdkImp.kt**:
```kotlin
override fun isVideoPip(forceReq: Boolean): Observable<Boolean> {
    return isMatchABTest(true, ABTestType.VIDEO_PIP, "on", forceReq)
}

override fun getVideoPipConfig(forceReq: Boolean): Observable<String> {
    return getABTestTarget(true, ABTestType.VIDEO_PIP, forceReq)
}
```

### 示例 2: 带数值配置的功能

**输入**: `video_player|video_next_guide` (视频下一个引导，默认值0)

**说明**: 数值配置类通常只生成 get 方法，不生成 is 方法。

**ABTestType.kt**:
```kotlin
VIDEO_NEXT_GUIDE(SceneSn.SCENE_VIDEO_NEXT_GUIDE, "algorithm_name", "0"),
```

**ABTestV2Sdk.kt**:
```kotlin
fun getVideoNextGuideCount(forceReq: Boolean = false): Observable<String>
```

**ABTestV2SdkImp.kt**:
```kotlin
override fun getVideoNextGuideCount(forceReq: Boolean): Observable<String> {
    return getABTestTarget(true, ABTestType.VIDEO_NEXT_GUIDE, forceReq)
}
```

### 示例 3: 基于圈子维度的功能

**输入**: `incentive|fulikapian` (福利卡片，基于圈子维度)

**ABTestV2Sdk.kt**:
```kotlin
fun isIncentiveNewWelfareCard(squareId: String?, forceReq: Boolean = false): Observable<String>
```

**ABTestV2SdkImp.kt**:
```kotlin
override fun isIncentiveNewWelfareCard(squareId: String?, forceReq: Boolean): Observable<String> {
    return getABTestTargetBySquareId(true, squareId, ABTestType.INCENTIVE_WELFARE_CARD, forceReq)
}
```

### 示例 4: 批量判断方法

**输入**: 批量获取视频播放器特性

**ABTestV2Sdk.kt**:
```kotlin
fun getVideoPlayer(forceReq: Boolean = false): Observable<List<String>>
```

**ABTestV2SdkImp.kt**:
```kotlin
override fun getVideoPlayer(forceReq: Boolean): Observable<List<String>> {
    return isMatchABTest(true, listOf(
        ABTestType.VIDEO_PLAYER_ANDROID_SCROLL_SPEED_UP,
        ABTestType.VIDEO_PLAYER_AUTO_PLAY_NEXT,
        ABTestType.VIDEO_PIP
    ), "on", forceReq)
}
```

## 特殊场景处理

### 场景 1: 只需要 get 方法（数值配置）
当默认值是数字时，通常只需要 get 方法。

### 场景 2: 返回类型是 String 的 is 方法
某些特殊情况下，is 方法返回 String（分组标识）。

### 场景 3: 单场景定义
没有 | 分隔符的场景，直接定义，不使用 buildSceneSn：
```kotlin
const val SCENE_SIDEBAR_AI = "ai_sidebar"
```

### 场景 4: 已存在私有常量
如果私有常量已存在，直接使用，不要重复定义。

## 注意事项

### 代码风格
1. 所有代码和注释使用中文
2. 严格遵循 Kotlin 编码规范
3. 保持与项目现有代码风格一致
4. 使用有意义的命名，避免缩写（除非是通用缩写）

### 方法签名
5. 接口方法必须有默认值 (`forceReq: Boolean = false`)
6. 实现方法不能有默认值 (`forceReq: Boolean`)
7. 确保接口和实现的方法签名匹配

### 命名规范
8. 场景常量使用全大写 + 下划线
9. 方法名使用小驼峰命名
10. 枚举项使用全大写 + 下划线

### 代码组织
11. 相关场景应该分组并添加注释
12. 新代码应插入到合适的分组中，而不是文件末尾
13. 保持代码的逻辑分组和可读性

### 注释规范
14. 方法注释要清晰说明功能
15. 使用 KDoc 格式
16. 包含参数说明和返回值说明

### 代码质量
17. 生成的代码必须能直接应用到项目中
18. 不要遗漏任何一个文件的修改
19. 确保引用关系正确（SceneSn -> ABTestType -> ABTestV2Sdk -> ABTestV2SdkImp）
20. 避免重复定义已存在的常量

---

**版本**: 2.0
**最后更新**: 2025-11-03
