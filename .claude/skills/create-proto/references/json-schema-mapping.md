# JSON Schema 类型映射参考

## JSON Schema 到 Java 类型映射

### 基础类型映射

| JSON Schema Type | Java Type | 解包方法 | 默认值 |
|-----------------|-----------|---------|--------|
| `string` | `String` | `.getAsString()` | `""` |
| `integer` | `int` | `.getAsInt()` | `0` |
| `integer` (long) | `long` | `.getAsLong()` | `0L` |
| `number` (float) | `float` | `.getAsFloat()` | `0f` |
| `number` (double) | `double` | `.getAsDouble()` | `0.0` |
| `boolean` | `boolean` | `.getAsBoolean()` | `false` |
| `object` | 自定义类 | `new Gson().fromJson(...)` | `null` |
| `array` | `List<T>` | `new Gson().fromJson(..., new TypeToken<List<T>>(){}.getType())` | `null` |

### 可选类型处理

对于可能为 null 的字段，使用包装类型：

| 基础类型 | 包装类型 |
|---------|---------|
| `int` | `Integer` |
| `long` | `Long` |
| `float` | `Float` |
| `double` | `Double` |
| `boolean` | `Boolean` |

### 枚举类型

JSON Schema 中定义的 `enum` 可以映射为 Java 枚举类或字符串：

```java
// 方式1：使用 String（推荐，灵活性更高）
public String roomType = "";  // 可能的值："LIVE", "AUDIO"

// 方式2：使用枚举
public enum RoomType {
    LIVE,
    AUDIO,
    UNKNOWN
}
public RoomType roomType = RoomType.UNKNOWN;
```

## 解包示例

### 基础类型解包

```java
@Override
protected void unpackResults(JsonObject results) {
    super.unpackResults(results);
    if (results != null) {
        try {
            // String
            if (results.has("name")) {
                name = results.get("name").getAsString();
            }

            // int
            if (results.has("age")) {
                age = results.get("age").getAsInt();
            }

            // long
            if (results.has("timestamp")) {
                timestamp = results.get("timestamp").getAsLong();
            }

            // boolean
            if (results.has("isVip")) {
                isVip = results.get("isVip").getAsBoolean();
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```

### 对象类型解包

```java
// 响应字段
public UserInfo userInfo = null;

// 解包
if (results.has("userInfo")) {
    userInfo = new Gson().fromJson(
        results.get("userInfo"),
        UserInfo.class
    );
}
```

### 数组类型解包

```java
import com.google.gson.reflect.TypeToken;
import java.util.List;

// 响应字段
public List<FeedItem> feedList = null;

// 解包
if (results.has("feedList")) {
    feedList = new Gson().fromJson(
        results.get("feedList"),
        new TypeToken<List<FeedItem>>(){}.getType()
    );
}
```

### 嵌套对象解包

```java
// 响应字段
public Map<String, Object> metadata = null;

// 解包
if (results.has("metadata")) {
    metadata = new Gson().fromJson(
        results.get("metadata"),
        new TypeToken<Map<String, Object>>(){}.getType()
    );
}
```

## 请求参数打包

### 基础类型打包

```java
@Override
protected void packParams(JsonObject params) {
    super.packParams(params);

    // String
    params.addProperty("name", name);

    // int
    params.addProperty("age", age);

    // boolean
    params.addProperty("isVip", isVip);
}
```

### 对象类型打包

```java
import com.google.gson.Gson;

@Override
protected void packParams(JsonObject params) {
    super.packParams(params);

    // 对象
    if (userInfo != null) {
        params.add("userInfo", new Gson().toJsonTree(userInfo));
    }

    // 数组
    if (feedList != null) {
        params.add("feedList", new Gson().toJsonTree(feedList));
    }
}
```

## JSON Schema 字段说明解析

JSON Schema 中的字段说明（`description`、`example`）应该转换为 JavaDoc 注释：

```java
/**
 * ccId（对应直播间的ccid）
 */
public String ccId = "";

/**
 * 房间类型
 * 可能的值：LIVE, AUDIO
 */
public String roomType = "";

/**
 * cc唯一定位的用户id
 * 示例：21313159
 */
public String ccUid = "";
```

## 必填字段处理

JSON Schema 中的 `required` 字段应该：
1. 在构造函数中作为必需参数
2. 标记为 `final` 以确保不可变性

```java
// ccId 是必填字段
private final String ccId;

public CCRoomInfoProto(String ccId) {
    this.ccId = ccId;
}
```

## 特殊类型处理

### 时间戳
```java
// Unix 时间戳（秒）
public long timestamp = 0L;

// Unix 时间戳（毫秒）
public long timestampMillis = 0L;

// ISO 8601 字符串
public String createdAt = "";
```

### 金额
```java
// 使用 long 表示分（推荐）
public long amountInCents = 0L;

// 或使用 double（注意精度问题）
public double amount = 0.0;
```

### ID 字段
```java
// 优先使用 String（更灵活）
public String userId = "";

// 确定为数字时使用 long
public long roomId = 0L;
```