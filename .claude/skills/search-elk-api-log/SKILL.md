---
name: search-elk-api-log
description: 查询网易大神接口埋点日志(god-dm-log)。支持按 uid、时间范围、接口路径、状态码查询,可统计调用频率、分析错误。当用户提到"接口日志"、"API日志"、"god-dm-log"、"接口埋点"、"查询接口"时使用。
allowed-tools: [Bash, Read, Grep, Glob]
user-invocable: true
---

# ELK 接口埋点日志查询

查询网易大神的接口埋点日志(god-dm-log)。

---

## 快速开始

直接使用 curl 调用 ELK API 查询。

### 基础查询示例

```bash
# 查询用户今天的接口日志
curl -s -X POST \
  -H "ELK-AUTH-TOKEN: c628b49cecb042c997f2c0b973cf2561" \
  -H "Content-Type: application/json" \
  "http://api.elk.x.netease.com:9550/a19_opd_god_dm_log-*/_search" \
  -d '{
    "size": 100,
    "query": {
      "bool": {
        "must": [
          {"match_phrase": {"uid": "<UID>"}},
          {"range": {"@timestamp": {"gte": "now/d", "lte": "now"}}}
        ]
      }
    },
    "sort": [{"@timestamp": {"order": "desc"}}],
    "_source": ["@timestamp", "path", "code", "spendTime"]
  }'
```

---

## 核心配置

**TOKEN**:

```bash
ELK-AUTH-TOKEN: c628b49cecb042c997f2c0b973cf2561
```

**API 地址**:

```
http://api.elk.x.netease.com:9550/a19_opd_god_dm_log-*/_search
```

**关键规则**:

- 查询时使用 13 位 epoch_millis 格式（如 1768467658000）
- 响应中的 `@timestamp` 是 ISO 8601 字符串格式（如 "2026-01-16T08:10:51.998Z"）
- 使用 Python 的 `datetime.fromisoformat()` 处理时间戳，自动处理时区转换
- 查询返回最多 10000 条,按时间倒序
- 聚合查询使用 `uid`、`version`、`clientType` 字段(不要用 `.keyword` 后缀)
- 精确匹配用 `match_phrase`,模糊匹配用 `match`
- 查询`did`时，应该替换为`deviceId`
- **字段匹配规则**: 只有 `payLoad` 字段支持模糊匹配(`match`),其他字段(`uid`、`path`、`deviceId` 等)只支持完全匹配(`match_phrase`)

---

## 常见查询

```bash
# 查询用户今天的日志
curl -s -X POST \
  -H "ELK-AUTH-TOKEN: c628b49cecb042c997f2c0b973cf2561" \
  -H "Content-Type: application/json" \
  "http://api.elk.x.netease.com:9550/a19_opd_god_dm_log-*/_search" \
  -d '{
    "size": 100,
    "query": {
      "bool": {
        "must": [
          {"match_phrase": {"uid": "<UID>"}},
          {"range": {"@timestamp": {"gte": "now/d", "lte": "now"}}}
        ]
      }
    },
    "sort": [{"@timestamp": {"order": "desc"}}]
  }'

# 查询接口错误(code != 200)
curl -s -X POST \
  -H "ELK-AUTH-TOKEN: c628b49cecb042c997f2c0b973cf2561" \
  -H "Content-Type: application/json" \
  "http://api.elk.x.netease.com:9550/a19_opd_god_dm_log-*/_search" \
  -d '{
    "size": 100,
    "query": {
      "bool": {
        "must": [
          {"match_phrase": {"uid": "<UID>"}},
          {"range": {"@timestamp": {"gte": "now/d", "lte": "now"}}}
        ],
        "must_not": [
          {"match": {"code": 200}}
        ]
      }
    },
    "sort": [{"@timestamp": {"order": "desc"}}]
  }'
```

详细示例见 [examples.md](./examples.md)

---

## 数据处理

使用 Python 处理返回的 JSON 数据。

**推荐方式**（使用文件中转，更稳定可靠）:

```bash
# 格式化输出：时间、状态码、路径
curl -s ... > /tmp/elk_result.json && python3 << 'EOF'
import json
from datetime import datetime

with open('/tmp/elk_result.json', 'r') as f:
    data = json.load(f)

for hit in data['hits']['hits']:
    source = hit['_source']
    dt = datetime.fromisoformat(source['@timestamp'].replace('Z', '+00:00'))
    time_str = dt.strftime('%H:%M:%S')
    print(f"{time_str} | {source['code']} | {source['path']}")
EOF

# 统计接口调用次数
curl -s ... > /tmp/elk_result.json && python3 << 'EOF'
import json

with open('/tmp/elk_result.json', 'r') as f:
    data = json.load(f)
print(data['hits']['total']['value'])
EOF
```

**备用方式**（管道方式，简洁但可能不稳定）:

```bash
# 注意：在某些环境下管道方式可能因引号解析问题失败
# 格式化输出
curl -s ... | python3 -c '
import json, sys
from datetime import datetime
data = json.load(sys.stdin)
for hit in data["hits"]["hits"]:
    source = hit["_source"]
    dt = datetime.fromisoformat(source["@timestamp"].replace("Z", "+00:00"))
    print(f"{dt.strftime(\"%H:%M:%S\")} | {source[\"code\"]} | {source[\"path\"]}")
'
```

---

## 输出示例

```
16:55:29 | 200 | /v1/log/sdc/log
16:54:51 | 200 | /v1/app/recommend/feed/game-dual
16:53:12 | 500 | /v1/user/profile
```

---

## 核心字段

- `uid` - 用户 UID
- `@timestamp` - 日志时间戳
- `path` - 接口路径
- `code` - HTTP 状态码
- `spendTime` - 接口耗时(ms)
- `payLoad` - 请求参数(JSON)
- `ext` - 扩展字段
- `version` - APP 版本
- `clientType` - 50=安卓, 51=iOS

完整字段说明见 [reference.md](./reference.md)

---

## 扩展功能

- 高级查询 - 详见 [advanced-features.md](./advanced-features.md)
- 统计聚合 - 接口频率、性能分析、唯一用户数
- 导出功能 - JSON/CSV 导出

---

## 相关文档

- [examples.md](./examples.md) - 20+ 使用场景示例
- [reference.md](./reference.md) - 完整 API 参考
- [advanced-features.md](./advanced-features.md) - 高级功能与 FAQ