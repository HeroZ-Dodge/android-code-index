# JsonPolymorphicUtil API 参考

完整的 JsonPolymorphicUtil 和 JsonPolymorphicStructure API 文档。

## JsonPolymorphicUtil

### toJsonStr() - 序列化为 JSON 字符串

#### 方法 1: 使用对象类型推断

```kotlin
fun toJsonStr(
    data: Any,
    vararg polymorphicTypes: JsonPolymorphicStructure<*>
): String
```

**参数**:
- `data`: 待序列化的对象
- `polymorphicTypes`: 可变参数，一个或多个多态结构定义

**返回值**: JSON 字符串，序列化失败返回空字符串 `""`

**使用场景**: 序列化单个对象时使用

**示例**:
```kotlin
val card = VideoCard("1", 123456, "张三", "video.mp4", "cover.jpg", 120, 1000)
val json = JsonPolymorphicUtil.toJsonStr(card, FeedCardStructure)
```

---

#### 方法 2: 显式指定 Type

```kotlin
fun toJsonStr(
    data: Any,
    type: Type,
    vararg polymorphicTypes: JsonPolymorphicStructure<*>
): String
```

**参数**:
- `data`: 待序列化的对象
- `type`: 对象的 Java Type（通过 `object : TypeToken<T>() {}.type` 获取）
- `polymorphicTypes`: 可变参数，一个或多个多态结构定义

**返回值**: JSON 字符串，序列化失败返回空字符串 `""`

**使用场景**: 序列化泛型集合时使用，如 `List<FeedCard>`

**示例**:
```kotlin
val feedList = listOf(card1, card2, card3)
val type = object : TypeToken<List<FeedCard>>() {}.type
val json = JsonPolymorphicUtil.toJsonStr(feedList, type, FeedCardStructure)
```

---

#### 方法 3: 使用 TypeToken

```kotlin
fun <T> toJsonStr(
    data: Any,
    token: TypeToken<T>,
    vararg polymorphicTypes: JsonPolymorphicStructure<*>
): String
```

**参数**:
- `data`: 待序列化的对象
- `token`: TypeToken 对象
- `polymorphicTypes`: 可变参数，一个或多个多态结构定义

**返回值**: JSON 字符串，序列化失败返回空字符串 `""`

**使用场景**: 与方法 2 相同，推荐使用此方法（API 更简洁）

**示例**:
```kotlin
val feedList = listOf(card1, card2, card3)
val json = JsonPolymorphicUtil.toJsonStr(
    feedList,
    object : TypeToken<List<FeedCard>>() {},
    FeedCardStructure
)
```

---

### fromJson() - 反序列化 JSON

#### 方法 1: 使用 Class

```kotlin
fun <T> fromJson(
    jsonString: String?,
    clazz: Class<T>,
    vararg polymorphicTypes: JsonPolymorphicStructure<*>
): T?
```

**参数**:
- `jsonString`: JSON 字符串，可以为 null
- `clazz`: 目标类的 Class 对象（如 `FeedCard::class.java`）
- `polymorphicTypes`: 可变参数，一个或多个多态结构定义

**返回值**: 反序列化后的对象，失败或 jsonString 为 null 时返回 `null`

**使用场景**: 反序列化单个对象时使用

**示例**:
```kotlin
val json = """{"cardType":"VideoCard", "id":"1", ...}"""
val card = JsonPolymorphicUtil.fromJson(
    json,
    FeedCard::class.java,
    FeedCardStructure
)
```

---

#### 方法 2: 使用 Type

```kotlin
fun <T> fromJson(
    jsonString: String?,
    type: Type,
    vararg polymorphicTypes: JsonPolymorphicStructure<*>
): T?
```

**参数**:
- `jsonString`: JSON 字符串，可以为 null
- `type`: 目标类型的 Type 对象
- `polymorphicTypes`: 可变参数，一个或多个多态结构定义

**返回值**: 反序列化后的对象，失败或 jsonString 为 null 时返回 `null`

**使用场景**: 反序列化泛型集合时使用

**示例**:
```kotlin
val json = """[{"cardType":"VideoCard",...}, {...}]"""
val feedList = JsonPolymorphicUtil.fromJson<List<FeedCard>>(
    json,
    object : TypeToken<List<FeedCard>>() {}.type,
    FeedCardStructure
)
```

---

#### 方法 3: 使用 TypeToken

```kotlin
fun <T> fromJson(
    jsonString: String?,
    typeToken: TypeToken<T>,
    vararg polymorphicTypes: JsonPolymorphicStructure<*>
): T?
```

**参数**:
- `jsonString`: JSON 字符串，可以为 null
- `typeToken`: TypeToken 对象
- `polymorphicTypes`: 可变参数，一个或多个多态结构定义

**返回值**: 反序列化后的对象，失败或 jsonString 为 null 时返回 `null`

**使用场景**: 反序列化泛型集合时使用，推荐使用此方法

**示例**:
```kotlin
val json = """[{"cardType":"VideoCard",...}, {...}]"""
val feedList = JsonPolymorphicUtil.fromJson(
    json,
    object : TypeToken<List<FeedCard>>() {},
    FeedCardStructure
)
```

---

#### 方法 4: 从 JsonElement 反序列化

```kotlin
fun <T> fromJson(
    jsonElement: JsonElement?,
    clazz: Class<T>,
    vararg polymorphicTypes: JsonPolymorphicStructure<*>
): T?
```

**参数**:
- `jsonElement`: Gson 的 JsonElement 对象
- `clazz`: 目标类的 Class 对象
- `polymorphicTypes`: 可变参数，一个或多个多态结构定义

**返回值**: 反序列化后的对象，失败或 jsonElement 为 null 时返回 `null`

**使用场景**: 当你已经有 JsonElement 对象时使用（例如从网络响应中提取）

**示例**:
```kotlin
val jsonElement: JsonElement = // ... 从某处获取
val card = JsonPolymorphicUtil.fromJson(
    jsonElement,
    FeedCard::class.java,
    FeedCardStructure
)
```

---

## JsonPolymorphicStructure

定义多态数据结构的接口。

### 接口定义

```kotlin
interface JsonPolymorphicStructure<T> {
    fun baseType(): Class<T>
    fun typeFieldName(): String?
    fun subTypes(): List<Class<out T>>
    fun recognizeSubtypes(): Boolean = false
}
```

### 方法说明

#### baseType()

```kotlin
fun baseType(): Class<T>
```

**返回值**: 多态类型的基类 Class 对象

**说明**: 定义所有子类型共同继承的基类或接口

**示例**:
```kotlin
override fun baseType() = FeedCard::class.java
```

---

#### typeFieldName()

```kotlin
fun typeFieldName(): String?
```

**返回值**: JSON 中用于标识子类型的字段名，可以为 null（默认使用 `"type"`）

**说明**:
- 指定 JSON 中用于区分子类型的字段名
- 如果返回 null，默认使用 `"type"` 作为字段名
- ⚠️ **极其重要**: 该字段名**不能与基类或任何子类中的字段重名**，否则会导致序列化/反序列化崩溃或数据覆盖

**最佳实践 - 使用业务前缀避免冲突**:
- ❌ **高风险命名**: `"type"`, `"feedType"`, `"itemType"`, `"msgType"` 等常见业务字段名
- ✅ **推荐命名**: `"__gameTab_polyType__"`, `"_poly_type_"`, `"@polymorphicType"` 等
- 命名规则：
  - 使用双下划线前缀（`__`）明显区分业务字段
  - 包含业务模块标识（如 `gameTab`、`chatMsg`）
  - 包含多态标识（如 `polyType`、`polymorphic`）
  - 可选双下划线后缀进一步降低冲突概率

**真实案例 - 字段冲突问题**:
```kotlin
// 业务类定义
class DiscoveryGameLibWrapper(
    val config: AppConfigEntity,
    val feedType: Int,  // ⚠️ 业务字段：表示 Feed 的 ViewType
    val gameList: List<GameInfoEntity>
) : AppConfigWrapData(config, feedType)

// ❌ 错误：使用 "feedType" 作为 typeFieldName 会冲突
object GameTabFeedStructure : JsonPolymorphicStructure<IFeed> {
    override fun typeFieldName() = "feedType"  // 与 DiscoveryGameLibWrapper.feedType 冲突！
    override fun subTypes() = listOf(DiscoveryGameLibWrapper::class.java, ...)
}

// ✅ 正确：使用带前缀的字段名避免冲突
object GameTabFeedStructure : JsonPolymorphicStructure<IFeed> {
    override fun typeFieldName() = "__gameTab_polyType__"  // 不与任何业务字段冲突
    override fun subTypes() = listOf(DiscoveryGameLibWrapper::class.java, ...)
}
```

**字段名冲突检查步骤**:
1. 读取基类的所有字段（包括继承的字段）
2. 读取 `subTypes()` 中列出的所有子类的字段
3. 确保 `typeFieldName()` 返回的名称与这些字段都不重名
4. **建议直接使用带业务前缀的命名**，无需逐个检查

**示例**:
```kotlin
// ❌ 错误示例：字段名冲突
data class VideoCard(
    val type: String,  // 业务字段
    val url: String
) : FeedCard()

object FeedCardStructure : JsonPolymorphicStructure<FeedCard> {
    override fun typeFieldName() = "type"  // ❌ 与 VideoCard.type 冲突，会崩溃
    ...
}

// ✅ 正确示例：使用不冲突的字段名
object FeedCardStructure : JsonPolymorphicStructure<FeedCard> {
    override fun typeFieldName() = "cardType"  // ✅ JSON 中会有 "cardType": "com.example.VideoCard"
    ...
}
```

---

#### subTypes()

```kotlin
fun subTypes(): List<Class<out T>>
```

**返回值**: 所有子类型的 Class 对象列表

**说明**: 注册所有可能出现的子类型。未注册的子类型会导致序列化/反序列化失败

**示例**:
```kotlin
override fun subTypes() = listOf(
    VideoCard::class.java,
    ImageTextCard::class.java,
    LiveCard::class.java
)
```

---

#### recognizeSubtypes()

```kotlin
fun recognizeSubtypes(): Boolean = false
```

**返回值**: 是否识别子类型本身（而非仅基类型），默认 `false`

**说明**:
- `false` (默认): 仅当字段声明为基类型时，才使用多态适配器
- `true`: 即使字段声明为具体的子类型，也使用多态适配器（会添加 type 字段）

**具体行为**:

假设有以下多态结构：
```kotlin
sealed class Animal
data class Cat(...) : Animal()
data class Dog(...) : Animal()

object AnimalStructure : JsonPolymorphicStructure<Animal> {
    override fun baseType() = Animal::class.java
    override fun typeFieldName() = "animal_type"
    override fun subTypes() = listOf(Cat::class.java, Dog::class.java)
    override fun recognizeSubtypes() = false  // 或 true
}
```

当 `recognizeSubtypes = false` 时：
```kotlin
data class Zoo(
    val animal: Animal,  // ✅ 会使用多态序列化，JSON 中有 "animal_type" 字段
    val cat: Cat         // ❌ 不会使用多态序列化，JSON 中没有 "animal_type" 字段
)
```

当 `recognizeSubtypes = true` 时：
```kotlin
data class Zoo(
    val animal: Animal,  // ✅ 会使用多态序列化，JSON 中有 "animal_type" 字段
    val cat: Cat         // ✅ 也会使用多态序列化，JSON 中有 "animal_type" 字段
)
```

**建议**: 通常保持默认值 `false`，除非你确实需要在子类型字段上也添加 type 标识

---

## 常见用法模式

### 模式 1: 单个多态结构

```kotlin
// 定义结构
object FeedCardStructure : JsonPolymorphicStructure<FeedCard> {
    override fun baseType() = FeedCard::class.java
    override fun typeFieldName() = "cardType"
    override fun subTypes() = listOf(
        VideoCard::class.java,
        ImageTextCard::class.java
    )
}

// 序列化
val json = JsonPolymorphicUtil.toJsonStr(
    feedList,
    object : TypeToken<List<FeedCard>>() {},
    FeedCardStructure  // 一个结构
)

// 反序列化
val list = JsonPolymorphicUtil.fromJson(
    json,
    object : TypeToken<List<FeedCard>>() {},
    FeedCardStructure  // 一个结构
)
```

### 模式 2: 多个多态结构（嵌套多态）

```kotlin
// 定义两个结构
object FeedCardStructure : JsonPolymorphicStructure<FeedCard> { ... }
object CardContentStructure : JsonPolymorphicStructure<CardContent> { ... }

// 序列化时传入所有结构
val json = JsonPolymorphicUtil.toJsonStr(
    feedList,
    object : TypeToken<List<FeedCard>>() {},
    FeedCardStructure,       // 外层结构
    CardContentStructure     // 内层嵌套结构
)

// 反序列化时也传入所有结构
val list = JsonPolymorphicUtil.fromJson(
    json,
    object : TypeToken<List<FeedCard>>() {},
    FeedCardStructure,
    CardContentStructure
)
```

### 模式 3: 使用 when 表达式处理多态数据

```kotlin
val feedList = JsonPolymorphicUtil.fromJson<List<FeedCard>>(...)

feedList?.forEach { card ->
    when (card) {
        is VideoCard -> {
            // 处理视频卡片
            playVideo(card.videoUrl)
        }
        is ImageTextCard -> {
            // 处理图文卡片
            showImageText(card.title, card.images)
        }
        is LiveCard -> {
            // 处理直播卡片
            joinLive(card.liveUrl)
        }
    }
}
```

---

## 注意事项

1. **异常处理**: `toJsonStr()` 和 `fromJson()` 内部已捕获异常，失败时返回空字符串或 null
2. **Null 安全**: `fromJson()` 的 jsonString 参数可以为 null，返回值也可能为 null，务必进行 null check
3. **TypeToken 创建**: 必须使用 `object : TypeToken<T>() {}` 匿名对象形式，不能直接实例化
4. **子类型注册**: 所有可能出现的子类型都必须在 `subTypes()` 中注册，否则会序列化/反序列化失败
5. **字段名冲突**: 如果业务数据中有 `type` 字段，务必在 `typeFieldName()` 中使用其他名称
