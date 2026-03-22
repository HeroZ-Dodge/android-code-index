---
name: api-mock-generator
description: Generate mock JSON data for Android Proto API classes. Use when user asks to "generate mock data", "create mock", "add mock", or provides a Proto class file path (.kt file inheriting from GLApiProto) and wants to create test data. Automatically analyzes API structure, generates realistic mock JSON, updates mock files (like FeedMockJson.kt), and modifies the Proto class's unpackResults method to use mock data.
---

# API Mock 数据生成器

为网易大神 Android 项目的 Proto API 类自动生成 mock 测试数据。

## 快速开始

基本用法：

1. 用户提供 Proto 类文件路径
2. 分析接口结构
3. 生成 mock JSON 数据
4. 更新 mock 文件和 Proto 类

## 工作流程

### 1. 分析 Proto 类

使用 `scripts/analyze_proto.py` 提取接口信息：

```bash
python3 scripts/analyze_proto.py <proto_file_path>
```

输出示例：
```json
{
  "class_name": "GetRecommentRankingAndItemsProto",
  "api_path": "/game-creation/game-ranking/recommend/getRankingAndItems",
  "result_type": "SquareRankingTabResult",
  "package": "com.netease.gl.servicefeed.feed.proto.creation",
  "params": ["colorConfig", "count", "page"]
}
```

### 2. 生成 Mock JSON

使用 `scripts/generate_mock_json.py` 生成基础 mock 数据：

```bash
python3 scripts/generate_mock_json.py <result_type> [api_path]
```

**重要特性：**
- **强制使用**真实数据：所有图片、视频、uid、feedId 必须从 `scripts/real_data_samples.py` 中选择，禁止随机生成
- 使用 `scripts/real_data_samples.py` 中提取自 FeedMockJson.kt 的**真实数据样本**
- 自动识别数据类型（用户、Feed、直播、媒体等）并使用对应的真实数据
- 生成的 mock 数据包含真实有效的图片链接、视频URL、用户ID、Feed ID等

**真实数据样本包括：**
- 图片链接：10+ 个真实的图片 URL
- 视频链接：多个真实的视频 URL
- Feed ID：14+ 个真实的 Feed ID
- 用户 UID：8+ 个真实的用户 ID
- 用户信息：5 个完整的真实用户对象
- Feed 实体：3 个完整的真实 Feed 对象
- 直播间信息：2 个真实的直播间数据
- 媒体信息：真实的媒体对象（含视频、封面等）
- 话题信息：6 个真实的话题数据

这会生成标准的响应结构，数据内容基于真实样本，但你仍需根据实际业务需求调整。

参考 `references/mock_examples.md` 查看不同数据类型的示例。

### 3. 生成 Mock 常量名

从类名生成 mock 常量名：

- 移除 `Proto` 后缀
- 移除 `Get` 前缀（如果有）
- 转换为 UPPER_SNAKE_CASE
- 添加 `_MOCK_JSON` 后缀

示例：
- `GetRecommentRankingAndItemsProto` → `RANKING_ITEMS_MOCK_JSON`
- `GetUserProfileProto` → `USER_PROFILE_MOCK_JSON`
- `SchemeAccountBySquareProto` → `SCHEME_ACCOUNT_BY_SQUARE_MOCK_JSON`

### 4. 创建独立的 Mock 文件

**重要变更：在 Proto 类同一目录下创建独立的 mock 文件**

文件命名规则：`{ClassName}MockJson.kt`

例如：
- `SchemeAccountBySquareProto.kt` → `SchemeAccountBySquareProtoMockJson.kt`
- `GetRecommentRankingAndItemsProto.kt` → `GetRecommentRankingAndItemsProtoMockJson.kt`

文件位置：与 Proto 类在同一文件夹

### 5. Mock 文件内容结构

#### 5.1 标准情况：unpackResults 接收 JsonObject

当 Proto 类的 `unpackResults` 方法签名是 `unpackResults(results: JsonObject?)` 时：

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

**关键点：**
- JSON 必须包含外层的 `result` 字段包裹实际数据（result 是对象）
- 必须包含 `code: 200` 和 `errmsg: "OK"` 字段
- 使用 `trimIndent()` 保持格式整洁

#### 5.2 特殊情况：unpackResults 接收 JsonArray

当 Proto 类的 `unpackResults` 方法签名是 `unpackResults(results: JsonArray?)` 时：

```kotlin
package com.netease.gl.servicemusic.music.proto

import com.google.gson.Gson
import com.google.gson.JsonArray

val BGM_LIST_MOCK_JSON = """
{
  "result": [
    {
      "id": "663df65719ad834e551fc840",
      "name": "热门音乐1",
      "singer": "歌手A",
      "duration": "180000",
      "url": "https://vod.cc.163.com/file/67bd98e167f6763753179515.mp4",
      "cover": "https://ok.166.net/reunionpub/3_20190909_16d14a2ef2d502024.png"
    },
    {
      "id": "67bd9c3cc2c28b7eee504ff1",
      "name": "热门音乐2",
      "singer": "歌手B",
      "duration": "210000",
      "url": "https://vod.cc.163.com/file/67bfa05e67f676375319d33a.mp4",
      "cover": "https://ok.166.net/reunionpub/3_20201209_17647756d4a543831.png"
    }
  ],
  "code": 200,
  "errmsg": "OK"
}
""".trimIndent()

val BGM_LIST_MOCK_JSON_ARRAY = Gson().fromJson(BGM_LIST_MOCK_JSON, JsonObject::class.java).getAsJsonArray("result")
```

**关键点：**
- JSON 的 `result` 字段是**数组**而不是对象
- 仍然需要包含 `code: 200` 和 `errmsg: "OK"` 字段
- Mock 常量名使用 `_MOCK_JSON_ARRAY` 后缀
- 使用 `getAsJsonArray("result")` 提取数组部分

### 6. 修改 Proto 类

#### 6.1 JsonObject 响应的修改

在 `unpackResults` 方法开头添加一行：

**原始代码：**
```kotlin
override fun unpackResults(results: JsonObject?) {
    super.unpackResults(results)
    accountList = JsonUtil.fromJson(results?.get("schemeAccountList")?.asJsonArray, SchemeAccount.listTypeToken)?.filterNotNull()
}
```

**修改后：**
```kotlin
override fun unpackResults(results: JsonObject?) {
    val results = SCHEME_ACCOUNT_BY_SQUARE_MOCK_JSON_OBJECT.getAsJsonObject("result")
    super.unpackResults(results)
    accountList = JsonUtil.fromJson(results?.get("schemeAccountList")?.asJsonArray, SchemeAccount.listTypeToken)?.filterNotNull()
}
```

#### 6.2 JsonArray 响应的修改

在 `unpackResults` 方法开头添加一行：

**原始代码：**
```java
@Override
protected void unpackResults(JsonArray results) {
    listMusic = JsonUtil.fromJson(results, MusicEntity.LIST_TYPE_TOKEN);
}
```

**修改后：**
```java
@Override
protected void unpackResults(JsonArray results) {
    JsonArray results = BGM_LIST_MOCK_JSON_ARRAY;
    listMusic = JsonUtil.fromJson(results, MusicEntity.LIST_TYPE_TOKEN);
}
```

或者 Kotlin 版本：

**原始代码：**
```kotlin
override fun unpackResults(results: JsonArray?) {
    super.unpackResults(results)
    tabList = JsonUtil.fromJson(results, object : TypeToken<List<GameTabEntity>>() {})
}
```

**修改后：**
```kotlin
override fun unpackResults(results: JsonArray?) {
    val results = GAME_TAB_LIST_MOCK_JSON_ARRAY
    super.unpackResults(results)
    tabList = JsonUtil.fromJson(results, object : TypeToken<List<GameTabEntity>>() {})
}
```

### 7. 添加 Import 语句

确保在 Proto 类文件顶部添加：

**JsonObject 响应：**
```kotlin
import com.netease.gl.servicefeed.feed.proto.creation.SCHEME_ACCOUNT_BY_SQUARE_MOCK_JSON_OBJECT
```

**JsonArray 响应：**
```kotlin
import com.netease.gl.servicefeed.feed.proto.discovery.GAME_TAB_LIST_MOCK_JSON_ARRAY
```

（根据实际的包名调整）

## 注意事项

1. **强制使用真实数据**：
   - 图片 URL、视频 URL、用户 UID、Feed ID 必须从 `scripts/real_data_samples.py` 中选择
   - 禁止随机生成或编造这些关键数据
   - 确保所有 mock 数据的真实性和有效性
2. **URL 字段兜底规则**：
   - 当需要生成 `url` 字段但没有合适的真实数据时，使用兜底值：`https://ds.163.com`
   - 这适用于 H5 页面链接、外部跳转链接等场景
3. **数据真实性**：生成的 mock 数据应该符合业务逻辑，仔细检查并调整数据内容
4. **类型匹配**：确保 mock JSON 的字段类型与数据模型类匹配
5. **列表数据**：列表类型建议生成 2-3 条测试数据
6. **可选字段**：参考现有接口数据，决定哪些字段是必需的
7. **重名检查**：如果 mock 常量已存在，询问用户是否覆盖

## 详细参考

- **Proto 类模式**：参见 `references/proto_patterns.md`
- **Mock 数据示例**：参见 `references/mock_examples.md`

## 示例

用户输入：
```
为 @services/content/feed/src/main/java/com/netease/gl/servicefeed/feed/proto/creation/SchemeAccountBySquareProto.kt 生成 mock 数据
```

执行步骤：
1. 读取并分析 Proto 类（SchemeAccountBySquareProto）
2. 查找数据模型类（SchemeAccount）了解字段结构
3. 生成 `SCHEME_ACCOUNT_BY_SQUARE_MOCK_JSON` 常量
4. 在同一目录创建 `SchemeAccountBySquareProtoMockJson.kt` 文件
5. 写入 mock 数据（包含 result、code、errmsg）
6. 修改 `SchemeAccountBySquareProto.kt` 的 `unpackResults` 方法
7. 添加必要的 import
8. 向用户展示修改内容