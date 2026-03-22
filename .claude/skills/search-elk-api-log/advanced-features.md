# 高级功能与常见问题

---

## 1. 导出功能

### 导出为 CSV

```bash
# 从查询结果导出为 CSV（推荐方式）
curl -s ... > /tmp/elk_result.json && python3 << 'EOF'
import json, csv
from datetime import datetime

with open('/tmp/elk_result.json', 'r') as f:
    data = json.load(f)

writer = csv.writer(open('export.csv', 'w'))
writer.writerow(['UID', '接口路径', '状态码', '耗时(ms)', '时间', '请求参数'])

for hit in data['hits']['hits']:
    s = hit['_source']
    dt = datetime.fromisoformat(s['@timestamp'].replace('Z', '+00:00'))
    writer.writerow([
        s.get('uid', ''),
        s.get('path', ''),
        s.get('code', ''),
        s.get('spendTime', ''),
        dt.strftime('%Y-%m-%d %H:%M:%S'),
        s.get('payLoad', '')
    ])
print("导出完成: export.csv")
EOF
```

---

## 2. 统计聚合

### 接口调用频率

```bash
curl -s \
  -H "ELK-AUTH-TOKEN:c628b49cecb042c997f2c0b973cf2561" \
  -XPOST "http://api.elk.x.netease.com:9550/_sql?format=json" \
  -d '{
    "query": "SELECT path, COUNT(*) as count FROM \"a19_opd_god_dm_log-*\" WHERE uid = '\''USER_UID'\'' GROUP BY path ORDER BY count DESC"
  }'
```

### 接口性能统计

```bash
curl -s \
  -H "ELK-AUTH-TOKEN:c628b49cecb042c997f2c0b973cf2561" \
  -XPOST "http://api.elk.x.netease.com:9550/_sql?format=json" \
  -d '{
    "query": "SELECT path, COUNT(*) as count, AVG(spendTime) as avg_time, MAX(spendTime) as max_time FROM \"a19_opd_god_dm_log-*\" WHERE uid = '\''USER_UID'\'' GROUP BY path ORDER BY avg_time DESC"
  }'
```

### 唯一用户数

```json
{
  "query": {
    "bool": {
      "must": [
        {"match_phrase": {"path": "/v1/incentive/task/list/info"}}
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
}
```

---

## 3. 高级查询

### 多接口 OR 查询

```json
{
  "query": {
    "bool": {
      "must": [
        {"match_phrase": {"uid": "USER_UID"}}
      ],
      "should": [
        {"match_phrase": {"path": "/v1/incentive/task/do-and-grant"}},
        {"match_phrase": {"path": "/v1/incentive/task/info"}}
      ],
      "minimum_should_match": 1
    }
  }
}
```

### 通配符查询

```json
{
  "query": {
    "bool": {
      "must": [
        {"wildcard": {"path": "*incentive*"}}
      ]
    }
  }
}
```

---

## 4. 常见问题

### Q: 聚合查询返回 0 或空结果?

**A**: 字段名错误。使用 `uid`、`version`、`clientType`,不要使用 `.keyword` 后缀。

```json
// ❌ 错误
{"cardinality": {"field": "uid.keyword"}}

// ✅ 正确
{"cardinality": {"field": "uid", "precision_threshold": 10000}}
```

### Q: API 地址错误?

**A**: 使用 HTTP (不是 HTTPS):

```
http://api.elk.x.netease.com:9550
```

### Q: 时间计算问题?

**A**: 使用 Python 计算时间戳（跨平台）:

```bash
# 今天 00:00:00
python3 -c "import datetime; print(int(datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000))"

# 指定日期
python3 -c "import datetime; print(int(datetime.datetime(2026, 1, 16, 0, 0, 0).timestamp() * 1000))"

# 当前时间
python3 -c "import time; print(int(time.time() * 1000))"

# 1小时前
python3 -c "import time; print(int((time.time() - 3600) * 1000))"
```

### Q: 查询超时?

**A**: 采取以下措施:

- 缩小时间范围(不超过24小时)
- 添加更精确的过滤条件
- 使用 `size: 0` 时不返回文档
- 设置 curl 超时: `--max-time 30`

### Q: 如何提高 cardinality 准确性?

**A**: 设置 precision_threshold:

```json
{
  "cardinality": {
    "field": "uid",
    "precision_threshold": 10000
  }
}
```

---

## 5. 性能优化

- 限制时间范围(不超过24小时)
- 使用精确匹配(`match_phrase`)而不是 `match`
- 明确指定size(不超过10000)
- 添加必要过滤条件