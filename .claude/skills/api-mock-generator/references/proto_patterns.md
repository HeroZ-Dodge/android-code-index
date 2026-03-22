# Proto 类模式参考

## 标准 Proto 类结构

网易大神项目中的 Proto 类通常继承自 `GLApiProto`，遵循以下模式：

```kotlin
package com.netease.gl.service.proto

class ExampleProto(
    private val param1: String,
    private val param2: Int,
    private val param3: String?
) : GLApiProto() {

    private var result: ResultType? = null

    fun getResult() = result

    override fun api(): String {
        return "/api/path/endpoint"
    }

    override fun packParams(params: JsonObject?) {
        super.packParams(params)
        params?.addProperty("param1", param1)
        params?.addProperty("param2", param2)
        param3?.let {
            params?.addProperty("param3", it)
        }
    }

    override fun unpackResults(results: JsonObject?) {
        super.unpackResults(results)
        result = JsonUtil.fromJson(results, ResultType::class.java)
    }
}
```

## Mock 数据集成模式

在 `unpackResults` 方法开头添加 mock 数据：

```kotlin
override fun unpackResults(results: JsonObject?) {
    val results = MOCK_JSON_OBJECT.getAsJsonObject("result")
    super.unpackResults(results)
    result = JsonUtil.fromJson(results, ResultType::class.java)
}
```

## Mock 文件位置和命名

**重要变更：Mock 文件与 Proto 类放在同一目录**

文件命名规则：`{ProtoClassName}MockJson.kt`

示例：
```
services/content/feed/src/main/java/com/netease/gl/servicefeed/feed/proto/creation/
├── SchemeAccountBySquareProto.kt              # Proto 类
└── SchemeAccountBySquareProtoMockJson.kt      # Mock 文件（新创建）
```

## Mock 文件结构

```kotlin
package com.netease.gl.servicefeed.feed.proto.creation

import com.google.gson.Gson
import com.google.gson.JsonObject

val SCHEME_ACCOUNT_BY_SQUARE_MOCK_JSON = """
{
  "result": {
    "schemeAccountList": [
      {
        "accountUid": "66cda0a2b40346108cda1f3b77384a86",
        "active": true,
        "id": "67bd9c3cc2c28b7eee504ff1",
        "label": "官方账号",
        "squareId": "5bed7223d545682b8bb8b732"
      }
    ]
  },
  "code": 200,
  "errmsg": "OK"
}
""".trimIndent()

val SCHEME_ACCOUNT_BY_SQUARE_MOCK_JSON_OBJECT = Gson().fromJson(SCHEME_ACCOUNT_BY_SQUARE_MOCK_JSON, JsonObject::class.java)
```

**必需字段：**
- `result`: 包裹实际数据的外层对象
- `code`: HTTP 状态码（通常是 200）
- `errmsg`: 错误消息（成功时为 "OK"）

## Mock 常量命名规范

Mock 常量名基于类名生成：

- `SchemeAccountBySquareProto` → `SCHEME_ACCOUNT_BY_SQUARE_MOCK_JSON`
- `GetRecommentRankingAndItemsProto` → `RANKING_ITEMS_MOCK_JSON`
- `GetUserProfileProto` → `USER_PROFILE_MOCK_JSON`
- `GetFeedListProto` → `FEED_LIST_MOCK_JSON`

规则：
1. 移除 `Proto` 后缀
2. 移除 `Get` 前缀（如果有）
3. 转换为 UPPER_SNAKE_CASE
4. 添加 `_MOCK_JSON` 后缀
5. 对应的 JsonObject 常量添加 `_OBJECT` 后缀