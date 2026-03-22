---
name: appdump-tools
description: "AppDump 崩溃记录查询与管理工具。查询项目 a19 的 crash 上报记录，支持按时间范围、平台(os_type)、错误类型(error_type)、用户ID(uid)、设备ID(device_id)、渠道(channel)等条件过滤，对结果进行汇总分析。还支持：获取 issue 的易协作工单和 Tag 信息、查询首次出现时间、给 issue 打 Tag、关联易协作工单、生成 AppDump 控制台链接。触发词：appdump、crash查询、crash记录、崩溃查询、崩溃记录、appdump-tools、crash统计、崩溃统计、issue标签、issue工单。"
---

# AppDump Crash 查询与管理

查询和管理 AppDump 平台 crash 上报记录。

## 查询引导流程

当用户触发查询类操作时，按以下流程处理：

### 1. 判断用户意图是否明确

**意图明确** — 直接执行，无需引导：
- 提供了具体的 identify、uid、device_id 等精确值
- 明确指定了平台、错误类型、时间范围等过滤条件
- 示例："查一下最近24小时 Android 的 JAVA_CRASH"、"查 identify xxx 的详情"

**意图模糊** — 需要引导：
- 仅说"查一下 crash"、"看看崩溃情况"等笼统描述
- 描述中的关键词无法直接映射为过滤参数（如"性能问题"、"闪退"等非标准字段值）
- 未指定任何过滤条件

### 2. 模糊意图引导

分析用户描述，用 `AskUserQuestion` 提供推荐查询选项。根据描述推测最可能的查询意图，生成 2-3 个推荐选项，**最后一项固定为"查阅全部支持的条件参数"**。

示例 — 用户说"看看最近的崩溃情况"：

```
options:
  - label: "全平台 Top 20 (最近24h)"
    description: "查询最近24小时所有平台的 crash，按数量排序"
  - label: "仅 Android (最近24h)"
    description: "仅查 Android 平台的 crash 汇总"
  - label: "仅 iOS (最近24h)"
    description: "仅查 iOS 平台的 crash 汇总"
  - label: "查阅全部支持的条件参数"
    description: "列出所有可用的过滤字段和操作符"
```

示例 — 用户说"最近 ANR 多不多"：

```
options:
  - label: "Android ANR (最近24h)"
    description: "查询 error_type=ANR 的 crash 汇总"
  - label: "Android ANR (最近3天)"
    description: "查询最近3天 error_type=ANR 的趋势"
  - label: "查阅全部支持的条件参数"
    description: "列出所有可用的过滤字段和操作符"
```

### 3. 全部条件参数展示

当用户选择"查阅全部支持的条件参数"时，输出以下分类列表：

---

**过滤条件（filters）** 格式：`[{"field":"<字段>","operate":"<操作符>","value":["<值>"]}]`

**操作符：**
| 操作符 | 含义 | 示例 |
|--------|------|------|
| `terms` | IN（多值匹配） | `{"field":"os_type","operate":"terms","value":["android","ios"]}` |
| `term` | =（精确匹配） | `{"field":"uid","operate":"term","value":["12345"]}` |
| `gte` | >= | `{"field":"crash_time","operate":"gte","value":[1700000000000]}` |
| `lte` | <= | `{"field":"crash_time","operate":"lte","value":[1700000000000]}` |
| `range` | BETWEEN | `{"field":"crash_time","operate":"range","value":[1700000000000,1700100000000]}` |

**常用字段：**
| 字段 | 说明 | 常见值 |
|------|------|--------|
| `os_type` | 平台 | `android`, `ios`, `windesktop` |
| `error_type` | 错误类型 | `ANDROID_JAVA_EXCEPTION`, `ANDROID_NATIVE_CRASH`, `ANDROID_ANR`, `OTHER`, `SCRIPT_ERROR` |
| `uid` | 用户ID | |
| `device_id` | 设备ID | |
| `channel` | 渠道 | |
| `model` | 设备代号 | |

**用户字段：**
| 字段 | 说明 |
|------|------|
| `uid` | 用户ID |
| `urs` | 玩家URS |
| `username` | 用户名 |
| `server_name` | 服务器名 |
| `server_v` | 服务器版本 |

**设备字段：**
| 字段 | 说明 |
|------|------|
| `device_name` | 设备名 |
| `model` / `model_gen` | 设备代号 / 型号 |
| `brand` / `mfr` | 系统定制商 / 设备厂商 |
| `cpu` / `gpu` | CPU型号 / GPU型号 |
| `system_version` | 系统版本 |
| `system_api_level` | SDK版本 |
| `net_type` | 网络类型 |
| `screen_resolution` | 分辨率 |
| `is_emulator` | 是否模拟器 |
| `is_rooted` | 是否root/越狱 |
| `arch` | 应用架构 |

**地理信息字段：**
| 字段 | 说明 |
|------|------|
| `district.country_cn` | 国家/地区 |
| `district.city_cn` | 城市 |
| `district.subdivision_cn` | 省份 |
| `ip` | IP地址 |

**其他字段：**
| 字段 | 说明 |
|------|------|
| `info` | 透传信息 |
| `timestamp` | 上报时间 |
| `crash_time` | 异常时间 |
| `transid` | 事务ID |
| `stack_trace` | Crash日志 |
| `package_fingerprint` | 包体签名 |

展示后提示用户选择需要的字段组合，或直接用自然语言描述查询需求。

---

## 命令一览

| 命令 | 用途 | 时间单位 |
|------|------|----------|
| `issues` | 查询 issue 列表并汇总 | 毫秒，最大3天 |
| `hit` | 获取单个 issue 上报详情 | 毫秒，最大3天 |
| `info` | 获取 issue 的工单和 Tag 信息 | 秒，最大90天 |
| `firsttime` | 查询 issue 首次出现时间 | 秒，最大2个月 |
| `tag` | 给 issue 打 Tag | - |
| `link` | 关联易协作工单 | - |
| `url` | 生成 AppDump 控制台链接 | - |

脚本路径: `scripts/appdump.mjs`（基于 skill 目录 `.claude/skills/appdump-tools/`）

## 查询类

### 查询 Issue 列表

```bash
node scripts/appdump.mjs issues [--hours <n>] [--filters '<json>'] [--top <n>]
```

- `--hours`: 最近 N 小时（默认 24，最大 72）
- `--from <ms> --to <ms>`: 精确时间范围（毫秒时间戳）
- `--filters`: 过滤条件 JSON，格式: `[{"field":"os_type","operate":"terms","value":["android"]}]`
- `--top`: Top N issue（默认 20）

### 获取 Issue 详情

```bash
node scripts/appdump.mjs hit --identify <id> [--hours <n>] [--filters '<json>']
```

### 获取 Issue 工单和 Tag 信息

```bash
# 按时间范围查询（秒级时间戳）
node scripts/appdump.mjs info --days 7
# 按 identify 精准查询（最多10个，逗号分隔）
node scripts/appdump.mjs info --identifys <id1>,<id2>
```

返回 identify 关联的易协作工单号、jira 工单、标签列表。

### 查询 Issue 首次出现时间

```bash
# 按时间范围查询
node scripts/appdump.mjs firsttime --days 7 [--order asc|desc] [--oversea]
# 按 identify 精准查询
node scripts/appdump.mjs firsttime --identifys <id1>,<id2>
```

## 操作类

### 给 Issue 打 Tag

```bash
# 追加 tag
node scripts/appdump.mjs tag --identify <id> --tags "tag1,tag2"
# 替换所有 tag
node scripts/appdump.mjs tag --identify <id> --tags "tag1,tag2" --mode set
# 清除所有 tag
node scripts/appdump.mjs tag --identify <id> --tags "" --mode set
```

### 关联易协作工单

```bash
node scripts/appdump.mjs link --identify <id> --issue-id <pmIssueId>
```

### 生成 AppDump 控制台链接

```bash
node scripts/appdump.mjs url --field transid --value <transid> [--time last_1_hour]
node scripts/appdump.mjs url --field device_id --value <deviceId>
```

根据 transid/device_id/timestamp 拼接 AppDump 控制台查询链接，可直接在浏览器打开。

## 汇总输出

查询 issues 后，输出结构化汇总：
1. **概览**: 时间范围、总 crash 数、总影响用户数、issue 总数
2. **Top Issues**: 排名、identify、crash 次数、影响用户数
3. 可进一步用 `hit` 获取 Top issue 的堆栈详情
4. 可用 `info` 查看 issue 是否已关联工单或标签
