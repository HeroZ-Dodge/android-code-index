---
name: search-drpf-log
description: DRPF 客户端日志查询工具 - 自动检测关键词，快速查询 ELK 埋点日志
---

# DRPF 客户端日志查询 Skill

这个 Skill 用于查询网易大神客户端的 DRPF ELK 日志，支持按 uid、时间范围、事件类型、关键词等条件查询。

## 重要约束

1. **TOKEN 配置**
   - AUTH-TOKEN 硬编码在此文件中：`20b6e03e3f8a48c2b2019d7e47d286bb`
   - 执行查询时直接在 curl 命令中使用

2. **时间处理规范**
   - 查询接口使用 epoch_millis 格式（13位时间戳）
   - 展示结果使用东八区本地时间（YYYY-MM-DD HH:mm:ss）
   - 支持相对时间（"昨天"、"今天"、"最近1小时"）

3. **查询限制**
   - **默认返回数量**: 10000 条（通过 size 参数控制）
   - 用户可明确指定其他数量（如：查询前100条）
   - 结果按时间倒序排列（最新的在前）
   - 单次查询时间范围建议不超过24小时

4. **输出规范**
   - 必须提供清晰的统计信息
   - 支持导出原始 JSON 数据
   - 输出原始日志内容，不做二次加工

## 触发条件

| 场景 | 触发词                               | 动作 |
|------|-----------------------------------|------|
| 斜杠命令 | `/search-drpf-log`                | 等待用户输入查询参数 |
| 关键词检测 | "elk"、"dm埋点"、"客户端日志"、"埋点日志" | 自动激活 skill |
| 用户主动说明 | "查询drpf日志"、"查看elk"                | 自动激活 skill |
| 统计数量 | "统计日志数量"、"有多少条日志"、"日志总数" | 使用数量统计功能（不返回详情） |

## 核心查询命令

### 1. 查询日志数量（不返回详情）

**场景**: 快速统计符合条件的日志总数，不返回具体日志内容

**方法一：使用 ES SQL API（推荐）**

```bash
curl -s \
  -H "ELK-AUTH-TOKEN:20b6e03e3f8a48c2b2019d7e47d286bb" \
  -H "Content-Type:application/json" \
  -XPOST "http://api.elk.x.netease.com:9550/_sql?format=json" \
  -d '{
    "query": "SELECT COUNT(*) as total FROM \"a19_drpf_clientlog-*\" WHERE user_uid = '\''USER_UID_HERE'\'' AND \"@timestamp\" >= CAST(START_TIME_MILLIS AS BIGINT) AND \"@timestamp\" <= CAST(END_TIME_MILLIS AS BIGINT)"
  }'
```

**方法二：使用 _search API 并设置 size=0**

```bash
curl -s \
  -H "ELK-AUTH-TOKEN:20b6e03e3f8a48c2b2019d7e47d286bb" \
  -H "Content-Type:application/json" \
  -XPOST "http://api.elk.x.netease.com:9550/a19_drpf_clientlog-*/_search" \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"match_phrase": {"user_uid": {"query": "USER_UID_HERE"}}},
          {"range": {"@timestamp": {"gte": START_TIME_MILLIS, "lte": END_TIME_MILLIS, "format": "epoch_millis"}}}
        ]
      }
    },
    "size": 0,
    "track_total_hits": true
  }'
```

**输出格式**:
```
📊 日志数量统计

查询条件: uid=3ae65978401e4d84a0af7069fb075f76
时间范围: 2026-01-09 00:00:00 ~ 2026-01-09 23:59:59

结果: 共找到 1,247 条日志

查询耗时: 245ms
```

**高级用法 - 按事件类型分组统计**:

```bash
curl -s \
  -H "ELK-AUTH-TOKEN:20b6e03e3f8a48c2b2019d7e47d286bb" \
  -H "Content-Type:application/json" \
  -XPOST "http://api.elk.x.netease.com:9550/_sql?format=json" \
  -d '{
    "query": "SELECT f as event_type, COUNT(*) as count FROM \"a19_drpf_clientlog-*\" WHERE user_uid = '\''USER_UID_HERE'\'' AND \"@timestamp\" >= CAST(START_TIME_MILLIS AS BIGINT) AND \"@timestamp\" <= CAST(END_TIME_MILLIS AS BIGINT) GROUP BY f ORDER BY count DESC"
  }'
```

**输出格式（分组统计）**:
```
📊 日志数量统计（按事件类型）

查询条件: uid=3ae65978401e4d84a0af7069fb075f76
时间范围: 2026-01-09 00:00:00 ~ 2026-01-09 23:59:59

事件类型分布:
  log_in       : 456 条 (36.6%)
  page_view    : 623 条 (49.9%)
  click        : 168 条 (13.5%)
─────────────────────────────
  总计         : 1,247 条

查询耗时: 312ms
```

### 2. 按 uid + 时间范围查询

**场景**: 查询指定用户在特定时间段的所有日志

**curl 命令**:
```bash
curl -s \
  -H "ELK-AUTH-TOKEN:20b6e03e3f8a48c2b2019d7e47d286bb" \
  -H "Content-Type:application/json" \
  -XPOST "http://api.elk.x.netease.com:9550/a19_drpf_clientlog-*/_search" \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"match_phrase": {"user_uid": {"query": "USER_UID_HERE"}}},
          {"range": {"@timestamp": {"gte": START_TIME_MILLIS, "lte": END_TIME_MILLIS, "format": "epoch_millis"}}}
        ]
      }
    },
    "size": 10000,
    "sort": [{"@timestamp": {"order": "desc"}}]
  }'
```

**参数说明**:
- `USER_UID_HERE`: 用户 UID（32位字符串）
- `START_TIME_MILLIS`: 开始时间（13位 epoch_millis）
- `END_TIME_MILLIS`: 结束时间（13位 epoch_millis）
- `size`: 返回条数，默认 10000

### 3. 按事件类型过滤

**场景**: 查询指定用户的特定事件类型日志

**curl 命令**:
```bash
curl -s \
  -H "ELK-AUTH-TOKEN:20b6e03e3f8a48c2b2019d7e47d286bb" \
  -H "Content-Type:application/json" \
  -XPOST "http://api.elk.x.netease.com:9550/a19_drpf_clientlog-*/_search" \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"match_phrase": {"user_uid": {"query": "USER_UID_HERE"}}},
          {"match_phrase": {"f": {"query": "EVENT_TYPE_HERE"}}},
          {"range": {"@timestamp": {"gte": START_TIME_MILLIS, "lte": END_TIME_MILLIS, "format": "epoch_millis"}}}
        ]
      }
    },
    "size": 10000,
    "sort": [{"@timestamp": {"order": "desc"}}]
  }'
```

**已知事件类型**（`f` 字段）:
- `log_in` - 登录事件
- `page_view` - 页面浏览事件
- 其他事件类型可在运行时动态发现

### 4. 组合多个事件类型

**场景**: 查询多种事件类型（使用 OR 逻辑）

**curl 命令**:
```bash
curl -s \
  -H "ELK-AUTH-TOKEN:20b6e03e3f8a48c2b2019d7e47d286bb" \
  -H "Content-Type:application/json" \
  -XPOST "http://api.elk.x.netease.com:9550/a19_drpf_clientlog-*/_search" \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"match_phrase": {"user_uid": {"query": "USER_UID_HERE"}}},
          {
            "bool": {
              "should": [
                {"match_phrase": {"f": "log_in"}},
                {"match_phrase": {"f": "page_view"}}
              ],
              "minimum_should_match": 1
            }
          },
          {"range": {"@timestamp": {"gte": START_TIME_MILLIS, "lte": END_TIME_MILLIS, "format": "epoch_millis"}}}
        ]
      }
    },
    "size": 10000,
    "sort": [{"@timestamp": {"order": "desc"}}]
  }'
```

### 5. 按关键词搜索

**场景**: 在日志内容中搜索关键词

**curl 命令**:
```bash
curl -s \
  -H "ELK-AUTH-TOKEN:20b6e03e3f8a48c2b2019d7e47d286bb" \
  -H "Content-Type:application/json" \
  -XPOST "http://api.elk.x.netease.com:9550/a19_drpf_clientlog-*/_search" \
  -d '{
    "query": {
      "bool": {
        "must": [
          {"match": {"content": "KEYWORD_HERE"}},
          {"range": {"@timestamp": {"gte": START_TIME_MILLIS, "lte": END_TIME_MILLIS, "format": "epoch_millis"}}}
        ]
      }
    },
    "size": 10000,
    "sort": [{"@timestamp": {"order": "desc"}}]
  }'
```

**说明**:
- `content` 字段是 JSON 字符串，包含完整的埋点数据
- 使用 `match` 进行全文搜索，支持中文
- 可搜索社区名称、页面信息、用户名等

## 时间处理

### 相对时间转换（macOS）

```bash
# 昨天 00:00:00 ~ 23:59:59
start=$(date -v-1d -j -f "%Y-%m-%d %H:%M:%S" "$(date +%Y-%m-%d) 00:00:00" "+%s")000
end=$(date -v-1d -j -f "%Y-%m-%d %H:%M:%S" "$(date +%Y-%m-%d) 23:59:59" "+%s")000

# 今天 00:00:00 ~ 当前时间
start=$(date -j -f "%Y-%m-%d %H:%M:%S" "$(date +%Y-%m-%d) 00:00:00" "+%s")000
end=$(date +%s)000

# 最近1小时
end=$(date +%s)000
start=$((end - 3600000))

# 最近24小时
end=$(date +%s)000
start=$((end - 86400000))
```

### 时间戳转换

⚠️ **重要**: 所有时间戳格式化输出必须使用**东八区（UTC+8，北京时间）**

```bash
# epoch_millis (13位) 转东八区时间
# macOS date 命令默认使用系统时区，需确保系统时区为 Asia/Shanghai
timestamp_millis=1767940450939
timestamp_sec=$((timestamp_millis / 1000))
date -r $timestamp_sec "+%Y-%m-%d %H:%M:%S"

# 东八区本地时间转 epoch_millis
date -j -f "%Y-%m-%d %H:%M:%S" "2026-01-09 14:34:10" "+%s"000

# 使用 Python 确保东八区时间（推荐）
python3 -c "
from datetime import datetime, timezone, timedelta
ts_ms = 1767940450939
tz_east8 = timezone(timedelta(hours=8))
dt = datetime.fromtimestamp(ts_ms / 1000, tz=tz_east8)
print(dt.strftime('%Y-%m-%d %H:%M:%S'))
"
```

## 输出格式规范

### 自动保存查询结果

**重要**：每次查询都必须自动将结果保存到文件，避免大量数据输出到终端。

**文件命名规则**：
```
/tmp/drpf-log-{timestamp}-{uid_suffix}.json
```

**命名说明**：
- `{timestamp}`: 查询时间戳，格式 `YYYYMMDD-HHmmss`（如：20260112-143052）
- `{uid_suffix}`: 用户 UID 后8位（如：fb075f76）
- 示例：`/tmp/drpf-log-20260112-143052-fb075f76.json`

**文件内容**：
- 保存 ELK 接口返回的完整原始 JSON 数据
- 包含所有字段，不做裁剪或转换
- 便于后续使用 jq 等工具进一步分析

### 基础输出格式

```
📊 查询结果（共找到 27 条日志）

查询耗时: 1455ms
时间范围: 2026-01-09 06:33:36 ~ 2026-01-09 06:49:36
查询条件: uid=3ae65978401e4d84a0af7069fb075f76, 事件类型=log_in,page_view
结果已保存: /tmp/drpf-log-20260109-063456-fb075f76.json

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1] 2026-01-09 06:34:10  评分: 20.20
事件类型: log_in
用户: 兰若地宫 (Propofol白)
游戏: 倩女幽魂手游 (l10)
渠道: lite_mi | 网络: wifi | 版本: 4.10.0.100300
上报方式: immediately
IP: 116.7.250.66
社区: 倩女幽魂手游 (5bee2c28d545682b8bb8cc02)

[2] 2026-01-09 06:49:36  评分: 20.12
事件类型: log_in
用户: 兰若地宫 (Propofol白)
游戏: 倩女幽魂手游 (l10)
渠道: lite_mi | 网络: wifi | 版本: 4.10.0.100300
上报方式: immediately
IP: 116.7.250.66

[3] 2026-01-09 06:33:36  评分: 18.69
事件类型: page_view
用户: 兰若地宫 (Propofol白)
页面: page_key=1, 停留时长=294ms
会话: 1_1767940416394486
上报方式: delayed

... (省略更多)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 统计信息:
- 总日志数: 27
- 事件类型分布: log_in (20, 74%), page_view (7, 26%)
- 上报方式: immediately (24, 89%), delayed (3, 11%)
- 查询集群: cluster_3015, cluster_4272

💡 提示:
- 如需限制返回数量，用户可明确指定 size 参数（如：查询前100条）
- 完整数据已保存到文件，可使用 jq 等工具进一步分析
- content 字段包含完整的埋点数据（JSON格式）
```

### page_view 事件特殊字段

当事件类型为 `page_view` 时，额外展示：
- `page_key`: 页面标识
- `page_on_time`: 页面停留时长（毫秒）
- `session_id`: 会话ID
- `refer_page_key`: 来源页面
- `refer_action_id`: 来源操作

## 错误处理

| 错误特征 | 处理方式 | 示例输出 |
|---------|---------|---------|
| 接口返回 401 | 检查 AUTH-TOKEN 是否正确 | "❌ 认证失败：请检查 ELK-AUTH-TOKEN 配置" |
| 接口超时 | **仅建议用户分页，不要自作主张执行** | "⏱️ 查询超时：建议缩小时间范围或使用分页参数（如 size=100）" |
| 无结果（hits.total.value=0） | 友好提示调整查询条件 | "📭 未找到匹配的日志，建议：<br>1. 扩大时间范围<br>2. 检查 uid 是否正确<br>3. 尝试移除事件类型过滤" |
| 时间范围过大 | 警告并建议缩小 | "⚠️ 时间范围过大（超过24小时），可能导致查询缓慢" |
| 缺少必要参数 | 明确提示需要哪些参数 | "❌ 缺少必要参数：uid<br>请提供用户 UID，例如：<br>查询 uid=3ae... 今天的日志" |
| JSON 解析错误 | 展示原始错误信息 | "❌ 响应解析失败：<原始错误信息>" |

## 高级功能

### 导出功能

支持导出查询结果到文件：

```bash
# 导出为 JSON（包含完整原始数据）
/tmp/drpf-log-export-20260109-143456.json

# 导出为 CSV（扁平化关键字段）
/tmp/drpf-log-export-20260109-143456.csv
```

**导出后操作**：
- 导出完成后，**主动询问**用户是否用 Excel 打开 CSV 文件
- 提供打开命令：`open -a "Microsoft Excel" /path/to/file.csv`
- 如用户确认，立即执行打开操作

CSV 字段说明：
- **字段顺序规则**：
  1. `deviceid` (did) - 第1列
  2. `user_uid` (uid) - 第2列
  3. `msg_key` - 第3列
  4. `f` (事件类型) - 第4列
  5. 其他所有字段按**首字母 a-z 排序**
- **字段命名规则**：
  - 保持 ELK 日志原始字段名，不做转换（如 `f` 不转为 `event_type`）
  - content 字段自动解析并扁平化为独立列
  - 时间字段 `@timestamp` 转换为东八区本地时间（YYYY-MM-DD HH:MM:SS）
- **数据顺序**：
  - 表格行顺序与 ELK 接口返回顺序一致（默认按时间倒序）
  - 不同事件类型的字段差异已处理，缺失值留空

### 统计聚合

提供以下统计信息：
1. **事件类型分布**: 各事件类型的数量和占比
2. **上报方式分布**: immediately vs delayed
3. **时间分布**: 按小时统计日志量
4. **渠道分布**: 各渠道的日志量
5. **网络类型分布**: wifi vs 4g/5g

### 实时查询优化

1. **增量查询**: 自动记录上次查询时间，支持"查看新日志"
2. **查询缓存**: 相同查询条件在5分钟内返回缓存结果
3. **分页建议**: 如果查询超时或结果过多，建议用户指定较小的 size 参数，但**不要自作主张添加**

## 日志字段参考

详见 [reference.md](./reference.md) 中的完整字段说明。

核心字段速查：
- `user_uid`: 用户 UID（查询核心字段）
- `@timestamp`: 日志时间戳（ISO8601格式）
- `f`: 事件类型（log_in, page_view等）
- `content`: 完整埋点数据（JSON字符串）
- `user_name`: 用户名
- `role_name`: 角色名
- `gameid`: 游戏ID
- `channel`: 渠道
- `app_ver`: APP版本
- `platform`: 平台（Android/iOS）
- `deviceid`: 设备ID
- `proxima_meta.ip`: 用户IP

## 使用示例

详见 [examples.md](./examples.md) 中的完整使用场景。

快速示例：

**示例1：查询日志详情**
```
用户: 查询 uid=3ae65978401e4d84a0af7069fb075f76 今天的日志

Skill: 正在查询 DRPF ELK 日志...

[执行查询并展示格式化结果]

📊 查询结果（共找到 27 条日志）
...
```

**示例2：仅统计日志数量**
```
用户: 统计 uid=3ae65978401e4d84a0af7069fb075f76 昨天的日志数量

Skill: 正在统计日志数量...

📊 日志数量统计

查询条件: uid=3ae65978401e4d84a0af7069fb075f76
时间范围: 2026-01-11 00:00:00 ~ 2026-01-11 23:59:59

结果: 共找到 1,247 条日志

查询耗时: 245ms
```

**示例3：按事件类型分组统计**
```
用户: 统计 uid=3ae65978401e4d84a0af7069fb075f76 今天各事件类型的日志数量

Skill: 正在统计日志数量（按事件类型分组）...

📊 日志数量统计（按事件类型）

查询条件: uid=3ae65978401e4d84a0af7069fb075f76
时间范围: 2026-01-12 00:00:00 ~ 2026-01-12 14:30:00

事件类型分布:
  page_view    : 623 条 (49.9%)
  log_in       : 456 条 (36.6%)
  click        : 168 条 (13.5%)
─────────────────────────────
  总计         : 1,247 条

查询耗时: 312ms
```

## 依赖

- **curl**: 用于调用 ELK API
- **jq**: 用于解析 JSON 响应（可选，用于复杂统计）
- **date**: 用于时间转换（macOS 自带）

## 参考文档

- [ELK API 官方文档](https://sa.nie.netease.com/docs/elk/%E8%BF%90%E7%BB%B4%E6%94%AF%E6%92%91/ELK/06-%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C/01-ELK/09-FAQ/11-API.md) - 网易 ELK 平台 API 使用指南

## 安全注意事项

1. **导出文件需要提示用户妥善保管**
2. **删除导出文件时要确认**