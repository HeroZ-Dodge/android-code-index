# ELK 接口埋点日志查询 API 参考文档

完整的 god-dm-log ELK 接口文档，包含字段说明、查询构造器、时间处理等。

---

## 接口信息

### 基础信息

- **接口地址**: `http://api.elk.x.netease.com:9550/a19_opd_god_dm_log-*/_search`
- **SQL 接口地址**: `http://api.elk.x.netease.com:9550/_sql?format=json`
- **请求方法**: `POST`
- **Content-Type**: `application/json`
- **认证方式**: Header 中的 `ELK-AUTH-TOKEN`

### 请求头

```bash
# 优先从环境变量读取,提供默认值作为后备
ELK-AUTH-TOKEN: c628b49cecb042c997f2c0b973cf2561
Content-Type: application/json
```

**TOKEN 配置**:

```bash
# 方式1: 环境变量（推荐）

# 方式2: 配置文件
TOKEN=$(cat ~/.config/elk/token 2>/dev/null || echo "c628b49cecb042c997f2c0b973cf2561")
```

### 完整请求示例

```bash
curl -s \
  -H "ELK-AUTH-TOKEN:c628b49cecb042c997f2c0b973cf2561" \
  -H "Content-Type:application/json" \
  -XPOST "http://api.elk.x.netease.com:9550/a19_opd_god_dm_log-*/_search" \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"match_phrase": {"uid": {"query": "bf34a282f48f4d80b9c7c3aade998f72"}}},
          {"range": {"@timestamp": {"gte": 1768466558944, "lte": 1768467458944, "format": "epoch_millis"}}}
        ]
      }
    },
    "size": 10000,
    "sort": [{"@timestamp": {"order": "desc"}}]
  }'
```

---

## 响应结构

### 标准响应格式

```json
{
  "took": 50,
  "timed_out": false,
  "num_reduce_phases": 4,
  "_shards": {
    "total": 164,
    "successful": 164,
    "skipped": 137,
    "failed": 0
  },
  "_clusters": {
    "total": 3,
    "successful": 3,
    "details": {
      "cluster_4126": {
        "status": "successful",
        "took": 40,
        "_shards": {...}
      },
      "cluster_3015": {...},
      "cluster_4052": {...}
    }
  },
  "hits": {
    "total": {
      "value": 25,
      "relation": "eq"
    },
    "max_score": 17.4596,
    "hits": [
      {
        "_index": "cluster_4052:a19_opd_god_dm_log-2026.01.15-005324",
        "_id": "iFndwJsBZhfXdgiPfoEu",
        "_score": 17.4596,
        "_source": {
          "deviceId": "60364eb52b334e98a264a826e1f8140e",
          "clientType": "50",
          "uid": "bf34a282f48f4d80b9c7c3aade998f72",
          "path": "/v1/app/recommend/feed/game-dual",
          "code": 200,
          "spendTime": 1519,
          "payLoad": "{...}",
          "@timestamp": "2026-01-15T08:54:51.271Z",
          ...
        }
      }
    ]
  }
}
```

### 响应字段说明

| 字段路径 | 说明 | 示例 |
|---------|------|------|
| `took` | 查询耗时（毫秒） | 50 |
| `timed_out` | 是否超时 | false |
| `hits.total.value` | 匹配的总文档数 | 25 |
| `hits.total.relation` | 精确性（eq=精确，gte=大于等于） | "eq" |
| `hits.max_score` | 最高相关性得分 | 17.4596 |
| `hits.hits[]` | 结果数组 | [...] |
| `hits.hits[]._score` | 相关性得分 | 17.4596 |
| `hits.hits[]._source` | 实际日志数据 | {...} |

---

## 日志字段详解

### _source 顶层字段

| 字段名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| `uid` | string | **用户 UID**（32位，查询核心字段） | "bf34a282f48f4d80b9c7c3aade998f72" |
| `@timestamp` | ISO8601 | **日志时间戳**（UTC时间） | "2026-01-15T08:54:51.271Z" |
| `path` | string | **接口路径**（核心过滤字段） | "/v1/app/recommend/feed/game-dual" |
| `urlPath` | string | URL 路径（与 path 相同） | "/v1/app/recommend/feed/game-dual" |
| `code` | number | **HTTP 状态码**（核心过滤字段） | 200, 401, 500 |
| `spendTime` | number | **接口耗时（毫秒）**（性能分析核心字段） | 1519 |
| `payLoad` | JSON string | **请求参数**（JSON字符串） | "{\"squareId\":\"5bed6...\"}" |
| `result` | string | 响应结果（部分接口有） | "[]" |
| `ext` | object | 扩展字段（部分接口有） | {"RecommendDataCount":12} |
| `ip` | string | 客户端IP | "115.236.116.69" |
| `version` | string | APP版本 | "4.11.0" |
| `clientType` | string | 客户端类型（50=安卓，51=iOS） | "50" |
| `deviceId` | string | 设备ID（32位） | "60364eb52b334e98a264a826e1f8140e" |
| `account` | string | 用户账号（部分接口有） | "xuanmenymu56936@163.com" |
| `activeSquareId` | string | 活跃社区ID | "5bed6281d545682b8bb8a761" |
| `trace_id` | string | 链路追踪ID | "ff8dd984ec6f9568" |
| `span_id` | string | Span ID | "ff8dd984ec6f9568" |
| `system` | string | 系统标识 | "god-dm-log" |
| `format` | string | 日志格式 | "dm-log" |
| `@version` | string | 日志格式版本 | "1" |

### payLoad 字段内容（JSON解析后）

`payLoad` 字段是一个 JSON 字符串，不同接口包含不同的参数。

**常见参数示例**:

| 接口路径 | payLoad 示例 |
|---------|-------------|
| `/v1/app/recommend/feed/game-dual` | `{"squareId":"5bed6281d545682b8bb8a761","tags":["5af7dbbbd54568048c609f3b"],"action":"DOWN","personalized":true,"liveCoverStyle":"DUAL"}` |
| `/v1/log/sdc/log` | `{"logName":"DSLogoutRole"}` |
| `/v1/exp/platform-rights/my-detail` | `{"ab":["9d2aa20c..."],"ef":[...],"uf":[],"ts":["1768467291"]}` |
| `/v1/cps/game/updatable` | `{"appKeyList":["cc"]}` |
| `/v1/ad/serving/common` | `{"adResourceTypeList":["MY_PAGE_ALERT_AD"]}` |

### ext 字段内容（部分接口有）

`ext` 字段是一个对象，包含接口特定的扩展信息。

**示例**:

| 接口路径 | ext 示例 |
|---------|---------|
| `/v1/app/recommend/feed/game-dual` | `{"RecommendDataList":["6945681..."],"RecommendDataCount":12,"AdvertCardDataCount":0,"RecommendSpendTime":1252,"AdvertCardSpendTime":43}` |
| `/v1/ad/serving/common` | `{"totalResult":[],"recommend_MY_PAGE_ALERT_AD":[]}` |

### 常见接口路径

| 接口路径 | 说明 | 典型用途 |
|---------|------|---------|
| `/v1/log/sdc/log` | SDK日志上报 | 上报用户行为日志 |
| `/v1/log/sdc/market-log` | 应用市场日志上报 | 上报应用激活、登录等事件 |
| `/v1/app/recommend/feed/game-dual` | 游戏流推荐 | 获取推荐内容 |
| `/v1/exp/platform-rights/my-detail` | 用户权益详情 | 获取用户权益信息 |
| `/v1/cps/game/updatable` | 游戏更新检查 | 检查游戏是否有更新 |
| `/v1/ad/serving/common` | 广告请求 | 获取广告数据 |
| `/v1/app/conf/get` | 获取应用配置 | 获取客户端配置 |
| `/v1/app/ranking/square/chatGroup/weekList` | 社区聊天群周榜 | 获取社区排行榜 |

---

## Elasticsearch DSL 查询构造器

### 基础查询模板

#### 1. 按 uid 查询

```json
{
  "query": {
    "bool": {
      "must": [
        {"match_phrase": {"uid": {"query": "USER_UID"}}}
      ]
    }
  }
}
```

#### 2. 按时间范围查询

```json
{
  "query": {
    "bool": {
      "must": [
        {
          "range": {
            "@timestamp": {
              "gte": 1768466558944,
              "lte": 1768467458944,
              "format": "epoch_millis"
            }
          }
        }
      ]
    }
  }
}
```

#### 3. 按接口路径查询

```json
{
  "query": {
    "bool": {
      "must": [
        {"match_phrase": {"path": {"query": "/v1/app/recommend/feed/game-dual"}}}
      ]
    }
  }
}
```

#### 4. 按状态码查询

```json
{
  "query": {
    "bool": {
      "must": [
        {"match": {"code": 200}}
      ]
    }
  }
}
```

#### 5. 按关键词搜索（全文搜索）

```json
{
  "query": {
    "bool": {
      "must": [
        {"match": {"payLoad": "DSLogoutRole"}}
      ]
    }
  }
}
```

### 组合查询

#### AND 条件（must）

所有条件必须同时满足：

```json
{
  "query": {
    "bool": {
      "must": [
        {"match_phrase": {"uid": {"query": "bf34a282f48f4d80b9c7c3aade998f72"}}},
        {"match_phrase": {"path": {"query": "/v1/app/recommend/feed/game-dual"}}},
        {"range": {"@timestamp": {"gte": 1768466558944, "lte": 1768467458944}}}
      ]
    }
  }
}
```

#### NOT 条件（must_not）

排除特定条件（如排除成功的接口调用，只查错误）：

```json
{
  "query": {
    "bool": {
      "must": [
        {"match_phrase": {"uid": {"query": "bf34a282f48f4d80b9c7c3aade998f72"}}}
      ],
      "must_not": [
        {"match": {"code": 200}}
      ]
    }
  }
}
```

#### OR 条件（should）

至少满足一个条件：

```json
{
  "query": {
    "bool": {
      "should": [
        {"match": {"code": 401}},
        {"match": {"code": 500}}
      ],
      "minimum_should_match": 1
    }
  }
}
```

### 查询参数

#### size（返回数量）

```json
{
  "query": {...},
  "size": 10000
}
```

默认：10000
最大：10000（建议不超过10000，性能考虑）

#### sort（排序）

```json
{
  "query": {...},
  "sort": [
    {"@timestamp": {"order": "desc"}}
  ]
}
```

- `desc`: 降序（最新的在前）
- `asc`: 升序（最旧的在前）

### ES SQL 聚合查询

#### 统计接口调用频率

```sql
SELECT path, COUNT(*) as count
FROM "a19_opd_god_dm_log-*"
WHERE uid = 'bf34a282f48f4d80b9c7c3aade998f72'
  AND "@timestamp" >= CAST(1768466558944 AS BIGINT)
  AND "@timestamp" <= CAST(1768467458944 AS BIGINT)
GROUP BY path
ORDER BY count DESC
LIMIT 20
```

#### 统计状态码分布

```sql
SELECT code, COUNT(*) as count
FROM "a19_opd_god_dm_log-*"
WHERE uid = 'bf34a282f48f4d80b9c7c3aade998f72'
  AND "@timestamp" >= CAST(1768466558944 AS BIGINT)
  AND "@timestamp" <= CAST(1768467458944 AS BIGINT)
GROUP BY code
ORDER BY count DESC
```

#### 统计接口性能（平均耗时）

```sql
SELECT path,
       COUNT(*) as count,
       AVG(spendTime) as avg_time,
       MAX(spendTime) as max_time,
       MIN(spendTime) as min_time
FROM "a19_opd_god_dm_log-*"
WHERE uid = 'bf34a282f48f4d80b9c7c3aade998f72'
  AND "@timestamp" >= CAST(1768466558944 AS BIGINT)
  AND "@timestamp" <= CAST(1768467458944 AS BIGINT)
GROUP BY path
ORDER BY avg_time DESC
LIMIT 20
```

---

## 时间处理

### 时间戳格式

| 格式 | 说明 | 示例 | 位数 |
|------|------|------|------|
| epoch_millis | 毫秒时间戳（查询用） | 1768467658944 | 13位 |
| epoch_second | 秒时间戳 | 1768467658 | 10位 |
| ISO8601 | 响应中的时间格式 | "2026-01-15T08:54:51.271Z" | - |
| 本地时间 | 展示用（东八区） | "2026-01-15 16:54:51" | - |

### macOS 时间转换命令

#### 1. 当前时间戳（13位）

```bash
echo $(($(date +%s) * 1000))
# 或
date +%s000
```

#### 2. 指定时间转时间戳

```bash
# 转换为秒时间戳，然后添加3个0
date -j -f "%Y-%m-%d %H:%M:%S" "2026-01-15 16:54:18" "+%s"000

# 结果: 1768467658000
```

#### 3. 时间戳转本地时间

```bash
# 13位时间戳转本地时间
timestamp_millis=1768467658944
timestamp_sec=$((timestamp_millis / 1000))
date -r $timestamp_sec "+%Y-%m-%d %H:%M:%S"

# 结果: 2026-01-15 16:54:18
```

#### 4. 相对时间计算

```bash
# 昨天 00:00:00
date -v-1d -j -f "%Y-%m-%d %H:%M:%S" "$(date +%Y-%m-%d) 00:00:00" "+%s"000

# 昨天 23:59:59
date -v-1d -j -f "%Y-%m-%d %H:%M:%S" "$(date +%Y-%m-%d) 23:59:59" "+%s"000

# 今天 00:00:00
date -j -f "%Y-%m-%d %H:%M:%S" "$(date +%Y-%m-%d) 00:00:00" "+%s"000

# 当前时间
date +%s000

# 1小时前
echo $(($(date +%s) * 1000 - 3600000))

# 24小时前
echo $(($(date +%s) * 1000 - 86400000))

# 7天前
echo $(($(date +%s) * 1000 - 604800000))
```

### 时区处理

- ELK 存储的时间戳是 UTC 时间（@timestamp）
- 展示时需要转换为东八区（UTC+8）
- macOS 的 `date -r` 命令会自动使用系统时区

---

## 常见查询场景

### 1. 查询用户今天的所有接口调用

```bash
# 计算今天的时间范围
start=$(date -j -f "%Y-%m-%d %H:%M:%S" "$(date +%Y-%m-%d) 00:00:00" "+%s")000
end=$(date +%s)000

# 执行查询
curl -s \
  -H "ELK-AUTH-TOKEN:c628b49cecb042c997f2c0b973cf2561" \
  -H "Content-Type:application/json" \
  -XPOST "http://api.elk.x.netease.com:9550/a19_opd_god_dm_log-*/_search" \
  -d "{
    \"query\": {
      \"bool\": {
        \"must\": [
          {\"match_phrase\": {\"uid\": {\"query\": \"bf34a282f48f4d80b9c7c3aade998f72\"}}},
          {\"range\": {\"@timestamp\": {\"gte\": $start, \"lte\": $end, \"format\": \"epoch_millis\"}}}
        ]
      }
    },
    \"size\": 10000,
    \"sort\": [{\"@timestamp\": {\"order\": \"desc\"}}]
  }"
```

### 2. 查询用户的接口错误

```bash
curl -s \
  -H "ELK-AUTH-TOKEN:c628b49cecb042c997f2c0b973cf2561" \
  -H "Content-Type:application/json" \
  -XPOST "http://api.elk.x.netease.com:9550/a19_opd_god_dm_log-*/_search" \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"match_phrase": {"uid": {"query": "bf34a282f48f4d80b9c7c3aade998f72"}}}
        ],
        "must_not": [
          {"match": {"code": 200}}
        ]
      }
    },
    "size": 10000,
    "sort": [{"@timestamp": {"order": "desc"}}]
  }'
```

### 3. 查询特定接口的调用记录

```bash
curl -s \
  -H "ELK-AUTH-TOKEN:c628b49cecb042c997f2c0b973cf2561" \
  -H "Content-Type:application/json" \
  -XPOST "http://api.elk.x.netease.com:9550/a19_opd_god_dm_log-*/_search" \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"match_phrase": {"uid": {"query": "bf34a282f48f4d80b9c7c3aade998f72"}}},
          {"match_phrase": {"path": {"query": "/v1/app/recommend/feed/game-dual"}}}
        ]
      }
    },
    "size": 10000,
    "sort": [{"@timestamp": {"order": "desc"}}]
  }'
```

### 4. 搜索包含特定参数的接口调用

```bash
curl -s \
  -H "ELK-AUTH-TOKEN:c628b49cecb042c997f2c0b973cf2561" \
  -H "Content-Type:application/json" \
  -XPOST "http://api.elk.x.netease.com:9550/a19_opd_god_dm_log-*/_search" \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"match": {"payLoad": "DSLogoutRole"}}
        ]
      }
    },
    "size": 10000,
    "sort": [{"@timestamp": {"order": "desc"}}]
  }'
```

### 5. 统计接口调用频率

```bash
curl -s \
  -H "ELK-AUTH-TOKEN:c628b49cecb042c997f2c0b973cf2561" \
  -H "Content-Type:application/json" \
  -XPOST "http://api.elk.x.netease.com:9550/_sql?format=json" \
  -d '{
    "query": "SELECT path, COUNT(*) as count FROM \"a19_opd_god_dm_log-*\" WHERE uid = '\''bf34a282f48f4d80b9c7c3aade998f72'\'' AND \"@timestamp\" >= CAST(1768466558944 AS BIGINT) AND \"@timestamp\" <= CAST(1768467458944 AS BIGINT) GROUP BY path ORDER BY count DESC LIMIT 20"
  }'
```

---

## 性能优化建议

### 1. 查询优化

- **限制时间范围**: 建议不超过24小时
- **使用精确匹配**: 优先使用 `match_phrase` 而不是 `match`
- **限制返回数量**: 明确指定size（不超过10000）
- **添加必要过滤**: 尽可能多地添加精确条件

### 2. 结果处理

- **使用文件中转处理大数据**（推荐）:
  ```bash
  curl -s ... > /tmp/elk_result.json && python3 << 'EOF'
  import json
  with open('/tmp/elk_result.json', 'r') as f:
      data = json.load(f)
  # 处理数据...
  EOF
  ```
- **只提取需要的字段**: 在查询时使用 `_source` 参数减少数据传输量
- **分页查询**: 大数据量时使用提醒增加查询条件或减少时间范围大小

### 3. 错误处理

- **超时设置**: curl 添加 `--max-time 30`
- **重试机制**: 失败时重试1-2次
- **降级策略**: 超时时缩小时间范围

---

## 故障排除

### 常见错误

#### 401 Unauthorized

```json
{"error":{"root_cause":[{"type":"security_exception","reason":"missing authentication credentials for REST request"}]}}
```

**原因**: AUTH-TOKEN 错误或缺失
**解决**: 检查请求头中的 `ELK-AUTH-TOKEN`

#### 查询超时

```json
{"timed_out": true, ...}
```

**原因**: 时间范围过大或查询条件过于宽泛
**解决**: 缩小时间范围，添加更多过滤条件

#### 无结果

```json
{"hits":{"total":{"value":0,"relation":"eq"},"hits":[]}}
```

**原因**: 查询条件不匹配或uid错误
**解决**: 检查uid、时间范围、接口路径等条件

#### JSON 解析错误

**原因**: 响应格式异常或网络问题
**解决**: 检查网络连接，重试查询

---

## 参考资料

- [Elasticsearch Query DSL](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html)
- [Elasticsearch Bool Query](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-bool-query.html)
- [Elasticsearch Range Query](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-range-query.html)
- [Elasticsearch SQL](https://www.elastic.co/guide/en/elasticsearch/reference/current/sql-getting-started.html)