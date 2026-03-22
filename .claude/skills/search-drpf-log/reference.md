# DRPF ELK 日志查询 API 参考文档

完整的 DRPF ELK 接口文档，包含字段说明、查询构造器、时间处理等。

---

## 接口信息

### 基础信息

- **接口地址**: `http://api.elk.x.netease.com:9550/a19_drpf_clientlog-*/_search`
- **请求方法**: `POST`
- **Content-Type**: `application/json`
- **认证方式**: Header 中的 `ELK-AUTH-TOKEN`

### 请求头

```
ELK-AUTH-TOKEN: 20b6e03e3f8a48c2b2019d7e47d286bb
Content-Type: application/json
```

### 完整请求示例

```bash
curl -s \
  -H "ELK-AUTH-TOKEN:20b6e03e3f8a48c2b2019d7e47d286bb" \
  -H "Content-Type:application/json" \
  -XPOST "http://api.elk.x.netease.com:9550/a19_drpf_clientlog-*/_search" \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"match_phrase": {"user_uid": {"query": "3ae65978401e4d84a0af7069fb075f76"}}},
          {"range": {"@timestamp": {"gte": 1767938400000, "lte": 1767941999999, "format": "epoch_millis"}}}
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
  "took": 1455,
  "timed_out": false,
  "num_reduce_phases": 3,
  "_shards": {
    "total": 3350,
    "successful": 3350,
    "skipped": 3305,
    "failed": 0
  },
  "_clusters": {
    "total": 2,
    "successful": 2,
    "details": {
      "cluster_3015": {
        "status": "successful",
        "took": 1454,
        "_shards": {...}
      },
      "cluster_4272": {...}
    }
  },
  "hits": {
    "total": {
      "value": 27,
      "relation": "eq"
    },
    "max_score": 20.195774,
    "hits": [
      {
        "_index": "cluster_3015:a19_drpf_clientlog-2026.01.09-006841",
        "_id": "ni59oZsBGEku-EibHfIK",
        "_score": 20.195774,
        "_source": {
          "user_uid": "3ae65978401e4d84a0af7069fb075f76",
          "@timestamp": "2026-01-09T06:34:10.939Z",
          "f": "log_in",
          "content": "{...}",
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
| `took` | 查询耗时（毫秒） | 1455 |
| `timed_out` | 是否超时 | false |
| `hits.total.value` | 匹配的总文档数 | 27 |
| `hits.total.relation` | 精确性（eq=精确，gte=大于等于） | "eq" |
| `hits.max_score` | 最高相关性得分 | 20.195774 |
| `hits.hits[]` | 结果数组 | [...] |
| `hits.hits[]._score` | 相关性得分 | 20.195774 |
| `hits.hits[]._source` | 实际日志数据 | {...} |

---

## 日志字段详解

### _source 顶层字段

| 字段名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| `user_uid` | string | **用户 UID**（32位，查询核心字段） | "3ae65978401e4d84a0af7069fb075f76" |
| `@timestamp` | ISO8601 | **日志时间戳**（UTC时间） | "2026-01-09T06:34:10.939Z" |
| `f` | string | **事件类型**（核心过滤字段） | "log_in", "page_view" |
| `content` | JSON string | **完整埋点数据**（包含所有详细信息） | "{\"f\":\"log_in\",...}" |
| `user_name` | string | 用户名 | "兰若地宫" |
| `role_name` | string | 角色名 | "Propofol白" |
| `gameid` | string | 游戏ID | "l10" |
| `channel` | string | 渠道 | "lite_mi" |
| `latest_channel` | string | 最新渠道 | "lite_mi" |
| `app_ver` | string | APP版本 | "4.10.0.100300" |
| `os_type` | string | 操作系统类型 | "Xiaomi" |
| `os_version` | string | 系统版本 | "15" |
| `platform` | string | 平台 | "Android" |
| `deviceid` | string | 设备ID（32位） | "45616efcac3f4958a47db6791db8439f" |
| `gameimei` | string | 游戏IMEI | "6a20dc07b6d3a071" |
| `msg_key` | string | 消息唯一键（13位时间戳） | "1767940450939" |
| `urs` | string | URS账号 | "15876722778" |
| `info_append_way` | string | 日志上报方式 | "immediately", "delayed" |
| `proxima_meta` | object | 元数据对象 | {"ip": "116.7.250.66", "time": 1767940888} |
| `proxima_meta.ip` | string | 用户IP地址 | "116.7.250.66" |
| `proxima_meta.time` | number | 接收时间戳（10位） | 1767940888 |
| `system` | string | 系统信息（详细） | "android#Xiaomi#24129PN74C#15#..." |
| `@version` | string | 日志格式版本 | "1" |

### content 字段内容（JSON解析后）

`content` 字段是一个 JSON 字符串，解析后包含：

| 字段名 | 说明 | 示例值 |
|--------|------|--------|
| `f` | 事件类型（与顶层 f 相同） | "log_in", "page_view" |
| `deviceid_v2` | 设备ID v2 | "6a20dc07b6d3a071,2cae80f999e8ffdf" |
| `gameid` | 游戏ID | "l10" |
| `game_group_id` | 游戏组ID | "l10_1217_1501221" |
| `user_sex` | 用户性别 | "2" |
| `user_account_type` | 账号类型 | "1" |
| `cguid` | 角色GUID | "1286601224" |
| `role_list` | 角色列表 | "l10.1286601224 l10.7217502069" |
| `role_server` | 角色服务器 | "百味斋-核桃仁" |
| `role_grade` | 角色等级 | "138" |
| `user_birth` | 用户生日 | "1900-01-01" |
| `user_location` | 用户位置 | "" |
| `timestamp` | 客户端时间戳（13位） | "1767940417346" |
| `sid` | 会话ID | "5d1f80c22d8793fc36a91b43a1d07c88" |
| `log_source` | 日志来源 | "1" |
| `log_token` | 日志令牌 | "8628e1c3344f77dc22c113f3267a8a36 0" |
| `is_mkey` | 是否主key | "0" |
| `network` | 网络类型 | "wifi", "4g", "5g" |
| `active_page_struc` | 当前页面结构 | "2" |
| `active_community_id` | 当前社区ID | "5bee2c28d545682b8bb8cc02" |
| `active_community_name` | 当前社区名称 | "倩女幽魂手游" |
| `log_sid` | 日志会话ID | "899b1f15526e2e613610b3a6d48c2c37" |

### page_view 事件特有字段（在 content 中）

| 字段名 | 说明 | 示例值 |
|--------|------|--------|
| `page_key` | 页面标识 | "1", "41", "58" |
| `page_on_time` | 页面停留时长（毫秒） | "294", "3236" |
| `session_id` | 页面会话ID | "1_1767940416394486" |
| `page_param` | 页面参数（JSON对象） | {"option": "1", "type": "5"} |
| `refer_page_key` | 来源页面标识 | "41" |
| `refer_session_id` | 来源会话ID | "41_1767941023422643" |
| `refer_action_id` | 来源操作ID | "click_pv_preview_1767940988739437" |
| `refer_page_param` | 来源页面参数 | {...} |

### 已知事件类型（f 字段）

| 事件类型 | 说明 | 典型用途 |
|---------|------|---------|
| `log_in` | 登录事件 | 追踪用户登录行为 |
| `page_view` | 页面浏览事件 | 追踪页面访问和停留时间 |
| `click_*` | 点击事件（推测） | 追踪用户点击行为 |
| `expose_*` | 曝光事件（推测） | 追踪内容曝光 |
| `dm_*` | DM埋点事件（推测） | 网易大神专用埋点 |

*注：带 * 的事件类型为推测，实际使用时可通过查询动态发现。*

---

## Elasticsearch DSL 查询构造器

### 基础查询模板

#### 1. 按 uid 查询

```json
{
  "query": {
    "bool": {
      "must": [
        {"match_phrase": {"user_uid": {"query": "USER_UID"}}}
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
              "gte": 1767938400000,
              "lte": 1767941999999,
              "format": "epoch_millis"
            }
          }
        }
      ]
    }
  }
}
```

#### 3. 按事件类型查询

```json
{
  "query": {
    "bool": {
      "must": [
        {"match_phrase": {"f": {"query": "log_in"}}}
      ]
    }
  }
}
```

#### 4. 按关键词搜索（全文搜索）

```json
{
  "query": {
    "bool": {
      "must": [
        {"match": {"content": "倩女幽魂"}}
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
        {"match_phrase": {"user_uid": {"query": "3ae..."}}},
        {"match_phrase": {"f": {"query": "log_in"}}},
        {"range": {"@timestamp": {"gte": 1767938400000, "lte": 1767941999999}}}
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
        {"match_phrase": {"f": "log_in"}},
        {"match_phrase": {"f": "page_view"}}
      ],
      "minimum_should_match": 1
    }
  }
}
```

#### NOT 条件（must_not）

排除特定条件：

```json
{
  "query": {
    "bool": {
      "must": [
        {"match_phrase": {"user_uid": {"query": "3ae..."}}}
      ],
      "must_not": [
        {"match_phrase": {"f": {"query": "page_view"}}}
      ]
    }
  }
}
```

#### 嵌套组合

```json
{
  "query": {
    "bool": {
      "must": [
        {"match_phrase": {"user_uid": {"query": "3ae..."}}},
        {
          "bool": {
            "should": [
              {"match_phrase": {"f": "log_in"}},
              {"match_phrase": {"f": "page_view"}}
            ],
            "minimum_should_match": 1
          }
        },
        {"range": {"@timestamp": {"gte": 1767938400000, "lte": 1767941999999}}}
      ]
    }
  }
}
```

### 查询参数

#### size（返回数量）

```json
{
  "query": {...},
  "size": 10
}
```

默认：10000
最大：10000（建议不超过100，性能考虑）

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

## 时间处理

### 时间戳格式

| 格式 | 说明 | 示例 | 位数 |
|------|------|------|------|
| epoch_millis | 毫秒时间戳（查询用） | 1767940450939 | 13位 |
| epoch_second | 秒时间戳 | 1767940450 | 10位 |
| ISO8601 | 响应中的时间格式 | "2026-01-09T06:34:10.939Z" | - |
| 本地时间 | 展示用（东八区） | "2026-01-09 14:34:10" | - |

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
date -j -f "%Y-%m-%d %H:%M:%S" "2026-01-09 14:34:10" "+%s"000

# 结果: 1767940450000
```

#### 3. 时间戳转本地时间

```bash
# 13位时间戳转本地时间
timestamp_millis=1767940450939
timestamp_sec=$((timestamp_millis / 1000))
date -r $timestamp_sec "+%Y-%m-%d %H:%M:%S"

# 结果: 2026-01-09 14:34:10
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

### 1. 查询用户今天的所有日志

```bash
# 计算今天的时间范围
start=$(date -j -f "%Y-%m-%d %H:%M:%S" "$(date +%Y-%m-%d) 00:00:00" "+%s")000
end=$(date +%s)000

# 执行查询
curl -s \
  -H "ELK-AUTH-TOKEN:20b6e03e3f8a48c2b2019d7e47d286bb" \
  -H "Content-Type:application/json" \
  -XPOST "http://api.elk.x.netease.com:9550/a19_drpf_clientlog-*/_search" \
  -d "{
    \"query\": {
      \"bool\": {
        \"must\": [
          {\"match_phrase\": {\"user_uid\": {\"query\": \"3ae65978401e4d84a0af7069fb075f76\"}}},
          {\"range\": {\"@timestamp\": {\"gte\": $start, \"lte\": $end, \"format\": \"epoch_millis\"}}}
        ]
      }
    },
    \"size\": 10000,
    \"sort\": [{\"@timestamp\": {\"order\": \"desc\"}}]
  }"
```

### 2. 查询用户的登录事件

```bash
curl -s \
  -H "ELK-AUTH-TOKEN:20b6e03e3f8a48c2b2019d7e47d286bb" \
  -H "Content-Type:application/json" \
  -XPOST "http://api.elk.x.netease.com:9550/a19_drpf_clientlog-*/_search" \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"match_phrase": {"user_uid": {"query": "3ae65978401e4d84a0af7069fb075f76"}}},
          {"match_phrase": {"f": {"query": "log_in"}}}
        ]
      }
    },
    "size": 10000,
    "sort": [{"@timestamp": {"order": "desc"}}]
  }'
```

### 3. 搜索包含特定社区的日志

```bash
curl -s \
  -H "ELK-AUTH-TOKEN:20b6e03e3f8a48c2b2019d7e47d286bb" \
  -H "Content-Type:application/json" \
  -XPOST "http://api.elk.x.netease.com:9550/a19_drpf_clientlog-*/_search" \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"match": {"content": "倩女幽魂手游"}}
        ]
      }
    },
    "size": 10000,
    "sort": [{"@timestamp": {"order": "desc"}}]
  }'
```

### 4. 组合查询（uid + 多事件类型 + 时间）

```bash
curl -s \
  -H "ELK-AUTH-TOKEN:20b6e03e3f8a48c2b2019d7e47d286bb" \
  -H "Content-Type:application/json" \
  -XPOST "http://api.elk.x.netease.com:9550/a19_drpf_clientlog-*/_search" \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"match_phrase": {"user_uid": {"query": "3ae65978401e4d84a0af7069fb075f76"}}},
          {
            "bool": {
              "should": [
                {"match_phrase": {"f": "log_in"}},
                {"match_phrase": {"f": "page_view"}}
              ],
              "minimum_should_match": 1
            }
          },
          {"range": {"@timestamp": {"gte": 1767938400000, "lte": 1767941999999, "format": "epoch_millis"}}}
        ]
      }
    },
    "size": 10000,
    "sort": [{"@timestamp": {"order": "desc"}}]
  }'
```

---

## 性能优化建议

### 1. 查询优化

- **限制时间范围**: 建议不超过24小时
- **使用精确匹配**: 优先使用 `match_phrase` 而不是 `match`
- **限制返回数量**: 默认size = 10000，明确指定size（不超过10000）
- **添加必要过滤**: 尽可能多地添加精确条件

### 2. 结果处理

- **使用 jq 解析**: `curl ... | jq '.hits.hits[]._source'`
- **只提取需要的字段**: 减少数据传输量
- **分页查询**: 大数据量时使用提醒增加查询条件或减少时间范围大小

### 3. 错误处理

- **超时设置**: curl 添加 `--max-time 30`
- **重试机制**: 失败时重试1-2次
- **降级策略**: 超时时缩小时间范围

---

## 故障排除

### 常见错误

#### 401 Unauthorized

```
{"error":{"root_cause":[{"type":"security_exception","reason":"missing authentication credentials for REST request"}]}}
```

**原因**: AUTH-TOKEN 错误或缺失
**解决**: 检查请求头中的 `ELK-AUTH-TOKEN`

#### 查询超时

```
{"timed_out": true, ...}
```

**原因**: 时间范围过大或查询条件过于宽泛
**解决**: 缩小时间范围，添加更多过滤条件

#### 无结果

```
{"hits":{"total":{"value":0,"relation":"eq"},"hits":[]}}
```

**原因**: 查询条件不匹配或uid错误
**解决**: 检查uid、时间范围、事件类型等条件

---

## 参考资料

- [Elasticsearch Query DSL](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html)
- [Elasticsearch Bool Query](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-bool-query.html)
- [Elasticsearch Range Query](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-range-query.html)