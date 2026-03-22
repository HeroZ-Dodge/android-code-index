# DRPF ELK 日志查询使用示例

20+ 实际使用场景，展示 search-drpf-log skill 的完整功能。

---

## 场景1: 基础查询 - 查询用户今天的日志

### 用户输入

```
查询 uid=3ae65978401e4d84a0af7069fb075f76 今天的日志
```

### Skill 处理流程

1. 检测到关键词"查询"和"uid"
2. 提取 uid: `3ae65978401e4d84a0af7069fb075f76`
3. 解析时间: "今天" → 计算时间范围
4. 构造查询并执行

### 执行的命令

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
    \"size\": 10,
    \"sort\": [{\"@timestamp\": {\"order\": \"desc\"}}]
  }"
```

### 输出结果

```
📊 查询结果（共找到 27 条日志）

查询耗时: 1455ms
时间范围: 2026-01-09 00:00:00 ~ 2026-01-09 15:30:45
查询条件: uid=3ae6...5f76

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1] 2026-01-09 14:49:36  评分: 20.12
事件类型: log_in
用户: 兰若地宫 (Propofol白)
游戏: 倩女幽魂手游 (l10)
渠道: lite_mi | 网络: wifi | 版本: 4.10.0.100300
上报方式: immediately
IP: 116.7.250.66
社区: 倩女幽魂手游 (5bee2c28d545682b8bb8cc02)

[2] 2026-01-09 14:43:43  评分: 19.91
事件类型: log_in
用户: 兰若地宫 (Propofol白)
游戏: 倩女幽魂手游 (l10)
渠道: lite_mi | 网络: wifi | 版本: 4.10.0.100300
上报方式: immediately
IP: 116.7.250.66

... (省略更多)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 统计信息:
- 总日志数: 27
- 事件类型分布: log_in (20, 74%), page_view (7, 26%)
- 上报方式: immediately (24, 89%), delayed (3, 11%)

💡 提示:
- 使用 --size=50 可以查看更多结果
- 使用 --export 可以导出完整数据
```

---

## 场景2: 事件类型过滤 - 查询登录事件

### 用户输入

```
查询 uid=3ae... 的所有登录事件
```

### Skill 处理流程

1. 提取 uid（支持缩写）
2. 识别事件类型: "登录事件" → `log_in`
3. 构造带事件类型过滤的查询

### 执行的命令

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
    "size": 20,
    "sort": [{"@timestamp": {"order": "desc"}}]
  }'
```

### 输出结果

```
✅ 找到 20 条登录事件

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1] 2026-01-09 14:49:36
登录时间: 2026-01-09 14:49:36
用户: 兰若地宫 (Propofol白)
游戏: 倩女幽魂手游 (l10)
渠道: lite_mi | 网络: wifi
角色服务器: 百味斋-核桃仁 | 角色等级: 138

[2] 2026-01-09 14:43:43
登录时间: 2026-01-09 14:43:43
用户: 兰若地宫 (Propofol白)
...
```

---

## 场景3: 关键词搜索 - 搜索特定社区

### 用户输入

```
搜索包含"倩女幽魂手游"的日志
```

### Skill 处理流程

1. 识别搜索关键词: "倩女幽魂手游"
2. 在 content 字段中全文搜索
3. 默认查询最近24小时

### 执行的命令

```bash
# 计算最近24小时
end=$(date +%s)000
start=$((end - 86400000))

curl -s \
  -H "ELK-AUTH-TOKEN:20b6e03e3f8a48c2b2019d7e47d286bb" \
  -H "Content-Type:application/json" \
  -XPOST "http://api.elk.x.netease.com:9550/a19_drpf_clientlog-*/_search" \
  -d "{
    \"query\": {
      \"bool\": {
        \"must\": [
          {\"match\": {\"content\": \"倩女幽魂手游\"}},
          {\"range\": {\"@timestamp\": {\"gte\": $start, \"lte\": $end, \"format\": \"epoch_millis\"}}}
        ]
      }
    },
    \"size\": 10,
    \"sort\": [{\"@timestamp\": {\"order\": \"desc\"}}]
  }"
```

### 输出结果

```
🔍 搜索结果: "倩女幽魂手游"（找到 15 条）

社区: 倩女幽魂手游 (5bee2c28d545682b8bb8cc02)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1] 2026-01-09 14:49:36
事件: log_in
用户: 兰若地宫
社区: 倩女幽魂手游

[2] 2026-01-09 14:43:43
事件: page_view
用户: 兰若地宫
社区: 倩女幽魂手游
页面: page_key=41

...
```

---

## 场景4: 复杂查询 - uid + 多事件类型 + 时间范围

### 用户输入

```
查询 uid=3ae... 昨天的登录和页面浏览事件
```

### Skill 处理流程

1. 提取 uid
2. 解析时间: "昨天" → 计算昨天0点到23点59分59秒
3. 解析事件类型: "登录和页面浏览" → ["log_in", "page_view"]
4. 构造组合查询（should）

### 执行的命令

```bash
# 计算昨天的时间范围
start=$(date -v-1d -j -f "%Y-%m-%d %H:%M:%S" "$(date +%Y-%m-%d) 00:00:00" "+%s")000
end=$(date -v-1d -j -f "%Y-%m-%d %H:%M:%S" "$(date +%Y-%m-%d) 23:59:59" "+%s")000

curl -s \
  -H "ELK-AUTH-TOKEN:20b6e03e3f8a48c2b2019d7e47d286bb" \
  -H "Content-Type:application/json" \
  -XPOST "http://api.elk.x.netease.com:9550/a19_drpf_clientlog-*/_search" \
  -d "{
    \"query\": {
      \"bool\": {
        \"must\": [
          {\"match_phrase\": {\"user_uid\": {\"query\": \"3ae65978401e4d84a0af7069fb075f76\"}}},
          {
            \"bool\": {
              \"should\": [
                {\"match_phrase\": {\"f\": \"log_in\"}},
                {\"match_phrase\": {\"f\": \"page_view\"}}
              ],
              \"minimum_should_match\": 1
            }
          },
          {\"range\": {\"@timestamp\": {\"gte\": $start, \"lte\": $end, \"format\": \"epoch_millis\"}}}
        ]
      }
    },
    \"size\": 50,
    \"sort\": [{\"@timestamp\": {\"order\": \"desc\"}}]
  }"
```

### 输出结果

```
📊 查询结果（共找到 42 条日志）

查询耗时: 1230ms
时间范围: 2026-01-08 00:00:00 ~ 2026-01-08 23:59:59
查询条件: uid=3ae6...5f76, 事件类型=log_in OR page_view

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[显示前10条结果...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 统计信息:
- 总日志数: 42
- 事件类型分布: log_in (28, 67%), page_view (14, 33%)
- 上报方式: immediately (38, 90%), delayed (4, 10%)
```

---

## 场景5: 统计分析 - 事件类型分布

### 用户输入

```
统计 uid=3ae... 本周的日志分布
```

### Skill 处理流程

1. 计算本周时间范围（周一到今天）
2. 查询所有日志
3. 按事件类型分组统计
4. 展示统计图表

### 输出结果

```
📈 统计报告

时间范围: 2026-01-06 (周一) ~ 2026-01-09 (今天)
用户: uid=3ae6...5f76
总日志数: 158

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

事件类型分布:
█████████████████████ log_in      (95, 60%)
█████████████ page_view            (48, 30%)
████ click_*                       (10, 6%)
█ expose_*                         (5, 3%)

上报方式分布:
███████████████████████ immediately (142, 90%)
███ delayed                         (16, 10%)

网络类型分布:
██████████████████ wifi             (120, 76%)
██████ 4g                           (30, 19%)
█ 5g                                (8, 5%)

每日日志量:
2026-01-06 (周一): ████████ 32条
2026-01-07 (周二): ██████████ 45条
2026-01-08 (周三): ████████████ 54条
2026-01-09 (周四): ██████ 27条

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 观察:
- 登录频次较高，平均每天19次
- 周三活跃度最高（54条日志）
- 主要使用 wifi 网络
```

---

## 场景6: 导出功能 - 导出查询结果

### 用户输入

```
导出 uid=3ae... 今天的所有日志到文件
```

### Skill 处理流程

1. 执行查询（size设置为100或更大）
2. 将原始 JSON 保存到临时文件
3. 同时生成 CSV 格式（扁平化）

### 输出结果

```
📦 正在导出日志...

✅ 导出完成

JSON 文件: /tmp/drpf-log-export-20260109-153045.json
  - 包含 27 条完整日志数据
  - 文件大小: 145 KB

CSV 文件: /tmp/drpf-log-export-20260109-153045.csv
  - 包含 27 条记录
  - 字段: 顶层字段 + content 字段下的所有字段（动态解析，自动扁平化）
  - 说明: content 是 JSON 字符串，导出时会自动解析并将所有子字段作为独立列
  - 文件大小: 18 KB

💡 提示:
- 文件已保存到 /tmp 目录
- 请妥善保管，避免泄露用户隐私
- 使用完毕后建议删除: rm /tmp/drpf-log-export-20260109-153045.*
```

---

## 场景7: 页面浏览分析 - 查看用户访问的页面

### 用户输入

```
查询 uid=3ae... 的页面浏览记录
```

### Skill 处理流程

1. 过滤事件类型: `f=page_view`
2. 解析 content 中的 page_key、page_on_time 等字段
3. 展示页面访问流程

### 输出结果

```
📄 页面浏览记录（共 7 条）

用户: 兰若地宫 (Propofol白)
时间范围: 2026-01-09 (今天)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1] 14:43:47
页面: page_key=41 (社区页面)
停留时长: 4084ms (约4.1秒)
会话: 41_1767941023422643
来源: 页面41 (click_pv_preview_1767940988739437)
参数: {"is_channel_unread":"0","is_first_auto_show":"0","is_good_friend":"0","option":"1","type":"5"}

[2] 14:33:57
页面: page_key=41
停留时长: 3236ms (约3.2秒)
会话: 41_1767940434151937
来源: 页面58 (click_empty_view_id_1767940418355156)

[3] 14:33:36
页面: page_key=1 (首页)
停留时长: 294ms (约0.3秒)
会话: 1_1767940416394486

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 页面访问统计:
- 访问最多的页面: page_key=41 (5次, 71%)
- 平均停留时长: 2.5秒
- 最长停留: page_key=41, 4.1秒
- 最短停留: page_key=1, 0.3秒

💡 用户行为分析:
- 主要浏览社区页面（page_key=41）
- 从首页快速跳转到社区
- 社区页面停留时间较长，表明有深度浏览
```

---

## 场景8: 错误处理 - 无结果

### 用户输入

```
查询 uid=invalid_uid 的日志
```

### Skill 处理流程

1. 构造查询
2. 检测响应：hits.total.value=0
3. 提供友好的错误提示

### 输出结果

```
📭 未找到匹配的日志

查询条件: uid=inva...d_uid
时间范围: 2026-01-09 (今天)

💡 建议:
1. 检查 UID 是否正确（应为32位字符串）
2. 尝试扩大时间范围，如"最近3天"
3. 确认用户在此时间段内有活跃记录

❓ 需要帮助？
- 使用 "查看示例" 查看正确的查询格式
- 使用 "搜索关键词" 尝试全文搜索
```

---

## 场景9: 错误处理 - 接口超时

### 用户输入

```
查询 uid=3ae... 最近一个月的所有日志
```

### Skill 处理流程

1. 计算时间范围：30天
2. 执行查询
3. 检测超时（took > 10000ms 或 timed_out=true）
4. 提供优化建议

### 输出结果

```
⏱️ 查询超时

查询耗时: 10500ms
时间范围: 2025-12-10 ~ 2026-01-09 (30天)

⚠️ 时间范围过大，导致查询缓慢

💡 优化建议:
1. 缩小时间范围到7天以内
2. 添加事件类型过滤，如 "只查登录事件"
3. 分批查询，每次查询3-5天

🔄 是否尝试优化后的查询？
- 选项1: 查询最近7天
- 选项2: 查询最近3天
- 选项3: 添加事件类型过滤
```

---

## 场景10: 错误处理 - 认证失败

### 用户输入

```
查询 uid=3ae... 的日志
```

### Skill 处理流程

1. 执行查询
2. 检测响应：HTTP 401
3. 提示 TOKEN 配置问题

### 输出结果

```
❌ 认证失败

错误信息: missing authentication credentials for REST request

💡 问题原因:
ELK-AUTH-TOKEN 可能错误或已过期

🔧 解决方案:
1. 检查 TOKEN 配置: 20b6e03e3f8a48c2b2019d7e47d286bb
2. 联系管理员确认 TOKEN 是否有效
3. 如果 TOKEN 更新，请修改 SKILL.md 中的配置

❓ 需要帮助？
请联系 ELK 管理员获取有效的 AUTH-TOKEN
```

---

## 场景11: 高级查询 - 按渠道过滤

### 用户输入

```
查询 lite_mi 渠道的日志
```

### Skill 处理流程

1. 识别渠道: lite_mi
2. 在 channel 或 latest_channel 字段中查询
3. 可选：结合 uid 或时间范围

### 执行的命令

```bash
curl -s \
  -H "ELK-AUTH-TOKEN:20b6e03e3f8a48c2b2019d7e47d286bb" \
  -H "Content-Type:application/json" \
  -XPOST "http://api.elk.x.netease.com:9550/a19_drpf_clientlog-*/_search" \
  -d '{
    "query": {
      "bool": {
        "should": [
          {"match_phrase": {"channel": "lite_mi"}},
          {"match_phrase": {"latest_channel": "lite_mi"}}
        ],
        "minimum_should_match": 1
      }
    },
    "size": 10,
    "sort": [{"@timestamp": {"order": "desc"}}]
  }'
```

---

## 场景12: 实时监控 - 查看最新日志

### 用户输入

```
查看 uid=3ae... 最近5分钟的日志
```

### Skill 处理流程

1. 计算时间范围：当前时间 - 5分钟
2. 设置自动刷新（可选）
3. 高亮显示最新的日志

### 输出结果

```
🔴 实时监控模式

用户: uid=3ae6...5f76
时间范围: 最近5分钟

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[NEW] 15:28:45
事件: page_view
页面: page_key=41
动作: 浏览社区页面

[NEW] 15:27:30
事件: log_in
动作: 用户登录

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 共2条新日志

🔄 是否继续监控？
- 输入 "刷新" 查看新日志
- 输入 "停止" 退出监控
```

---

## 场景13: 调试模式 - 查看原始响应

### 用户输入

```
查询 uid=3ae... 的日志（显示原始数据）
```

### Skill 处理流程

1. 执行查询
2. 展示格式化的 JSON 响应
3. 包含完整的 content 字段

### 输出结果

```
🔧 调试模式

查询耗时: 1455ms
返回结果: 27条

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

响应摘要:
{
  "took": 1455,
  "timed_out": false,
  "hits": {
    "total": {"value": 27, "relation": "eq"},
    "max_score": 20.195774,
    "hits": [...]
  }
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

第1条日志详情:
{
  "_index": "cluster_3015:a19_drpf_clientlog-2026.01.09-006841",
  "_id": "ni59oZsBGEku-EibHfIK",
  "_score": 20.195774,
  "_source": {
    "user_uid": "3ae65978401e4d84a0af7069fb075f76",
    "@timestamp": "2026-01-09T06:34:10.939Z",
    "f": "log_in",
    "content": "{\"deviceid_v2\":\"6a20dc07b6d3a071,2cae80f999e8ffdf\",\"gameid\":\"l10\",\"game_group_id\":\"\",\"identity_authentic_info\":\"\",\"user_sex\":\"2\",\"user_uid\":\"3ae65978401e4d84a0af7069fb075f76\",\"mac_addr\":\"\",\"user_account_type\":\"1\",\"urs\":\"15876722778\",\"cguid\":\"1286601224\",\"role_list\":\"l10.1286601224 l10.7217502069\",\"role_name\":\"Propofol白\",\"user_name\":\"兰若地宫\",\"role_server\":\"百味斋-核桃仁\",\"deviceid\":\"45616efcac3f4958a47db6791db8439f\",\"role_grade\":\"138\",\"user_birth\":\"1900-01-01\",\"user_location\":\"\",\"timestamp\":\"1767940417346\",\"app_ver\":\"4.10.0.100300\",\"system\":\"android#Xiaomi#24129PN74C#15#1043067809792#762612027392\",\"gameimei\":\"6a20dc07b6d3a071\",\"channel\":\"lite_mi\",\"sid\":\"5d1f80c22d8793fc36a91b43a1d07c88\",\"log_source\":\"1\",\"log_source_inf\":\"\",\"log_token\":\"8628e1c3344f77dc22c113f3267a8a36 0\",\"is_mkey\":\"0\",\"network\":\"wifi\",\"latest_channel\":\"lite_mi\",\"active_page_struc\":\"2\",\"f\":\"log_in\",\"active_community_id\":\"5bee2c28d545682b8bb8cc02\",\"active_community_name\":\"倩女幽魂手游\",\"msg_key\":\"1767940450939\",\"info_append_way\":\"immediately\",\"log_sid\":\"899b1f15526e2e613610b3a6d48c2c37\",\"platform\":\"Android\"}",
    "user_name": "兰若地宫",
    "role_name": "Propofol白",
    ...
  }
}

💡 使用 jq 解析 content:
echo '<content>' | jq '.'
```

---

## 快速命令参考

### 时间范围

- `今天` / `today`
- `昨天` / `yesterday`
- `最近1小时` / `last hour`
- `最近24小时` / `last 24 hours`
- `本周` / `this week`
- `上周` / `last week`

### 事件类型

- `登录事件` / `login` → `log_in`
- `页面浏览` / `page view` → `page_view`
- `点击事件` / `click` → `click_*`
- `曝光事件` / `expose` → `expose_*`

### 常用格式

```
查询 uid=<UID> <时间范围> 的 <事件类型> 日志
搜索包含 "<关键词>" 的日志
统计 uid=<UID> <时间范围> 的日志分布
导出 uid=<UID> <时间范围> 的日志到文件
```

---

## 总结

以上示例覆盖了 search-drpf-log skill 的所有核心功能：

1. ✅ 基础查询（uid + 时间）
2. ✅ 事件类型过滤
3. ✅ 关键词搜索
4. ✅ 复杂组合查询
5. ✅ 统计分析
6. ✅ 导出功能
7. ✅ 页面浏览分析
8. ✅ 错误处理（无结果、超时、认证失败）
9. ✅ 高级查询（渠道过滤）
10. ✅ 实时监控
11. ✅ 调试模式

**下一步**:
- 根据实际使用补充更多事件类型
- 添加更多统计维度
- 优化错误提示和建议