# ELK 接口日志查询示例

常见使用场景示例，使用 curl 直接调用 ELK API。

---

## 1. 查询用户今天的日志

```bash
curl -s -X POST \
  -H "ELK-AUTH-TOKEN: c628b49cecb042c997f2c0b973cf2561" \
  -H "Content-Type: application/json" \
  "http://api.elk.x.netease.com:9550/a19_opd_god_dm_log-*/_search" \
  -d '{
    "size": 100,
    "query": {
      "bool": {
        "must": [
          {"match_phrase": {"uid": "bf34a282f48f4d80b9c7c3aade998f72"}},
          {"range": {"@timestamp": {"gte": "now/d", "lte": "now"}}}
        ]
      }
    },
    "sort": [{"@timestamp": {"order": "desc"}}]
  }'
```

## 2. 查询接口错误(code != 200)

```bash
curl -s -X POST \
  -H "ELK-AUTH-TOKEN: c628b49cecb042c997f2c0b973cf2561" \
  -H "Content-Type: application/json" \
  "http://api.elk.x.netease.com:9550/a19_opd_god_dm_log-*/_search" \
  -d '{
    "size": 100,
    "query": {
      "bool": {
        "must": [
          {"match_phrase": {"uid": "bf34a282f48f4d80b9c7c3aade998f72"}},
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

## 3. 统计接口调用频率(使用聚合)

```bash
curl -s -X POST \
  -H "ELK-AUTH-TOKEN: c628b49cecb042c997f2c0b973cf2561" \
  -H "Content-Type: application/json" \
  "http://api.elk.x.netease.com:9550/a19_opd_god_dm_log-*/_search" \
  -d '{
    "size": 0,
    "query": {
      "bool": {
        "must": [
          {"match_phrase": {"uid": "bf34a282f48f4d80b9c7c3aade998f72"}},
          {"range": {"@timestamp": {"gte": "now/d", "lte": "now"}}}
        ]
      }
    },
    "aggs": {
      "api_frequency": {
        "terms": {
          "field": "path",
          "size": 20
        }
      }
    }
  }'
```

---

## 4. 查询特定接口

```bash
curl -s \
  -H "ELK-AUTH-TOKEN:c628b49cecb042c997f2c0b973cf2561" \
  -H "Content-Type:application/json" \
  -XPOST "http://api.elk.x.netease.com:9550/a19_opd_god_dm_log-*/_search" \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"match_phrase": {"uid": "bf34a282f48f4d80b9c7c3aade998f72"}},
          {"match_phrase": {"path": "/v1/app/recommend/feed/game-dual"}}
        ]
      }
    },
    "size": 10000,
    "sort": [{"@timestamp": {"order": "desc"}}]
  }'
```

## 5. 搜索包含特定参数

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

---

## 6. 统计接口调用频率

```bash
curl -s \
  -H "ELK-AUTH-TOKEN:c628b49cecb042c997f2c0b973cf2561" \
  -H "Content-Type:application/json" \
  -XPOST "http://api.elk.x.netease.com:9550/_sql?format=json" \
  -d '{
    "query": "SELECT path, COUNT(*) as count FROM \"a19_opd_god_dm_log-*\" WHERE uid = '\''bf34a282f48f4d80b9c7c3aade998f72'\'' AND \"@timestamp\" >= CAST(1768381200000 AS BIGINT) AND \"@timestamp\" <= CAST(1768467600000 AS BIGINT) GROUP BY path ORDER BY count DESC LIMIT 20"
  }'
```

## 7. 统计唯一用户数

```bash
curl -s \
  -H "ELK-AUTH-TOKEN:c628b49cecb042c997f2c0b973cf2561" \
  -H "Content-Type:application/json" \
  -XPOST "http://api.elk.x.netease.com:9550/a19_opd_god_dm_log-*/_search" \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"match_phrase": {"path": "/v1/incentive/task/list/info"}},
          {"range": {"@timestamp": {"gte": 1768381200000, "lte": 1768467600000, "format": "epoch_millis"}}}
        ]
      }
    },
    "size": 0,
    "track_total_hits": true,
    "aggs": {
      "unique_users": {
        "cardinality": {
          "field": "uid",
          "precision_threshold": 10000
        }
      }
    }
  }'
```

---

## 时间范围参考

```bash
# 今天 00:00:00
date -j -f "%Y-%m-%d %H:%M:%S" "$(date +%Y-%m-%d) 00:00:00" "+%s"000

# 昨天 00:00:00
date -v-1d -j -f "%Y-%m-%d %H:%M:%S" "$(date +%Y-%m-%d) 00:00:00" "+%s"000

# 当前时间
date +%s000

# 1小时前
echo $(($(date +%s) * 1000 - 3600000))
```

---

## 常用查询模板

### 错误查询(code != 200)

```json
{
  "query": {
    "bool": {
      "must": [
        {"match_phrase": {"uid": "USER_UID"}}
      ],
      "must_not": [
        {"match": {"code": 200}}
      ]
    }
  }
}
```

### 时间范围查询

```json
{
  "query": {
    "bool": {
      "must": [
        {"range": {"@timestamp": {"gte": START_TIMESTAMP, "lte": END_TIMESTAMP, "format": "epoch_millis"}}}
      ]
    }
  }
}
```

### 多条件 AND 查询

```json
{
  "query": {
    "bool": {
      "must": [
        {"match_phrase": {"uid": "USER_UID"}},
        {"match_phrase": {"path": "API_PATH"}},
        {"range": {"@timestamp": {...}}}
      ]
    }
  }
}
```