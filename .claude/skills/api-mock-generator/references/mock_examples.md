# Mock 数据示例

## 基础数据类型

### 用户数据
```json
{
  "uid": "test_user_123",
  "nick": "测试用户",
  "icon": "https://ok.166.net/reunionpub/test_icon.png",
  "intro": "这是测试简介",
  "gender": 1,
  "birth": "1990-01-01",
  "deleteTime": 0,
  "createTime": 1234567890,
  "updateTime": 1234567890
}
```

### 动态/Feed 数据
```json
{
  "id": "test_feed_123",
  "uid": "test_user_123",
  "type": 3,
  "content": "{\"type\":3,\"body\":{\"text\":\"测试内容\"}}",
  "deleteTime": 0,
  "createTime": 1234567890,
  "updateTime": 1234567890,
  "squareId": "test_square_123"
}
```

### 统计数据
```json
{
  "id": "test_id",
  "repostCount": 10,
  "commentCount": 50,
  "likeCount": 200,
  "shareCount": 5,
  "favCount": 15,
  "createTime": 1234567890
}
```

### 列表结构
```json
{
  "result": {
    "items": [
      {"id": "1", "name": "item1"},
      {"id": "2", "name": "item2"}
    ],
    "total": 2,
    "hasMore": false
  },
  "code": 200,
  "errmsg": "OK"
}
```

## 复杂结构示例

### 榜单数据
```json
{
  "result": {
    "rankingList": [
      {
        "id": "ranking_1",
        "name": "热门榜单",
        "icon": "https://example.com/icon.png",
        "items": [
          {
            "id": "item_1",
            "title": "标题1",
            "score": 1000
          }
        ]
      }
    ],
    "total": 1
  },
  "code": 200,
  "errmsg": "OK"
}
```

### 直播数据
```json
{
  "result": {
    "ccLiveInfo": {
      "roomType": "1",
      "ccId": "123456",
      "roomId": "789",
      "channelId": "456",
      "title": "测试直播间",
      "cover": "https://example.com/cover.jpg",
      "hotScore": "10000",
      "ccUid": "123",
      "nickname": "主播昵称"
    }
  },
  "code": 200,
  "errmsg": "OK"
}
```

## 响应码说明

### 标准响应结构

#### JsonObject 响应（标准情况）

当 Proto 类的 `unpackResults` 接收 `JsonObject?` 参数时：

```json
{
  "result": { /* 数据内容 */ },
  "code": 200,        // 200 表示成功
  "errmsg": "OK"      // 错误信息
}
```

#### JsonArray 响应（特殊情况）

当 Proto 类的 `unpackResults` 接收 `JsonArray?` 参数时：

```json
{
  "result": [ /* 数据内容数组 */ ],
  "code": 200,        // 200 表示成功
  "errmsg": "OK"      // 错误信息
}
```

**示例：**
```json
{
  "result": [
    {
      "id": "663df65719ad834e551fc840",
      "name": "音乐1",
      "singer": "歌手A"
    },
    {
      "id": "67bd9c3cc2c28b7eee504ff1",
      "name": "音乐2",
      "singer": "歌手B"
    }
  ],
  "code": 200,
  "errmsg": "OK"
}
```

### 错误码说明
- `200`: 成功
- `400`: 参数错误
- `401`: 未授权
- `404`: 资源不存在
- `500`: 服务器错误