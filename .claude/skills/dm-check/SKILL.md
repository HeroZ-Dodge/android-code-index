---
name: dm-check
description: 埋点验证工具 - 支持埋点文档(Excel)、POPO 文档链接、事件ID字符串等多种输入。自动解析文档要求（新增/修改埋点、预期字段值），通过 adb logcat 监听实际上报数据，生成 HTML 验证报告（含概览表格、JSON 详情、关注字段标红）。触发条件：(1) 用户提供 .xlsx 文件路径且内容包含埋点信息时自动激活；(2) 用户提供 docs.popo.netease.com 链接且涉及埋点文档时自动激活；(3) 用户提到"验证埋点"、"核对埋点"、"埋点校验"、"dm-check"、"check tracking"、"埋点是否齐全"、"对比埋点文档"时触发；(4) 斜杠命令 /dm-check。
allowed-tools: [Bash, Read, Grep, Glob, Write, AskUserQuestion]
user-invocable: true
---

# 埋点验证 Skill

根据埋点文档或事件ID，验证实际上报数据是否符合要求。输出 HTML 验证报告。

## 支持的输入类型

### 1. 埋点文档（Excel .xlsx）

用户提供 Excel 文件路径。流程：

1. 用脚本 `--parse-only --format json` 解析 Excel，输出结构化 JSON
2. Claude 阅读输出，理解文档要求：
   - 是新增埋点还是修改现有埋点（从 sheet 分区标题判断）
   - 每个字段的预期值（从备注/字段内容列提取，脚本会尝试自动提取 `extracted_values`）
   - 触发规则和触发行为
3. 生成完整 spec JSON 写入 `/tmp/dm-check-spec.json`

### 2. POPO 文档链接

用户提供 `docs.popo.netease.com` 链接（灵犀文档、灵犀表格、团队文档、团队表格均支持）。

流程：

1. 调用 `popo-doc-exporter` skill 导出文档（含登录态检查）
2. 根据导出文件类型分流：
   - **xlsx（表格文档）**：与 Excel 输入流程完全相同，用脚本 `--parse-only --format json` 解析，提取埋点 spec
   - **docx（文字文档）**：用 Read 工具读取文件内容，Claude 阅读理解后构建 spec JSON
3. 生成完整 spec JSON 写入 `/tmp/dm-check-spec.json`

### 3. 事件ID字符串

用户直接给出事件名，如 `clk_share_btn, page_view_detail`。

Claude 直接创建 spec JSON，events 中只包含事件名，fields 留空。

### 4. 其他文档或文字描述

Claude 阅读理解后创建 spec JSON。

## Spec JSON 格式

无论何种输入，最终都生成 `/tmp/dm-check-spec.json`：

```json
{
  "title": "验证描述",
  "events": {
    "clk_share_btn": {
      "cn_name": "点击分享按钮",
      "trigger_rule": "用户点击分享按钮时触发",
      "change_type": "new",
      "fields": {
        "page_id": {
          "name": "页面ID",
          "type": "string",
          "expected_values": ["home", "detail"],
          "description": "当前页面标识"
        },
        "column_info": {
          "name": "合集信息",
          "type": "json",
          "expected_values": [],
          "description": "合集卡片信息",
          "is_new": true,
          "sub_fields": {
            "column_type": {
              "name": "合集类型",
              "type": "string",
              "expected_values": ["DEFAULT", "COMIC"],
              "description": "合集类型枚举"
            },
            "column_theme": {
              "name": "漫剧主题",
              "type": "string",
              "expected_values": [],
              "description": "古代/仙侠/玄幻等",
              "is_new": true
            }
          }
        }
      }
    }
  }
}
```

字段说明：
- `cn_name`: 事件中文名
- `trigger_rule`: 触发规则描述（来自文档）
- `change_type`: `new`（新增）或 `modify`（修改），可省略
- `fields`: 需要验证的业务字段
  - `expected_values`: 预期取值列表（可为空数组）
  - `description`: 字段说明
  - `sub_fields`: （仅 json 类型字段）定义 JSON 对象内需要验证的子字段，结构同 `fields` 中的字段定义

## 工作流程

### Step 1: 分析输入，生成 Spec

#### Excel 输入

```bash
python3 <skill-dir>/scripts/verify_tracking.py \
  --excel "<excel_path>" --parse-only --format json
```

阅读 JSON 输出，理解每个事件、字段和预期值。对于脚本未能自动提取的预期值，Claude 应根据备注文本补充到 spec 中。

然后生成完整 spec JSON 写入 `/tmp/dm-check-spec.json`。

#### POPO 文档链接输入

检测到输入包含 `docs.popo.netease.com` 链接时：

1. **调用 popo-doc-exporter skill** 导出文档：
   - 执行登录态检查：`node .claude/skills/popo-doc-exporter/scripts/popo-doc.mjs check`
   - 若未登录，按 popo-doc-exporter 的登录流程引导用户完成登录
   - 导出文档：`node .claude/skills/popo-doc-exporter/scripts/popo-doc.mjs "<popo_url>" --output /tmp/dm-check-popo.docx`
   - 脚本会自动检测文档类型：表格文档输出为 `/tmp/dm-check-popo.xlsx`，文字文档输出为 `/tmp/dm-check-popo.docx`

2. **根据导出文件类型分流**：
   - **若输出为 `.xlsx`（表格文档）**：与 Excel 输入流程完全相同
     ```bash
     python3 <skill-dir>/scripts/verify_tracking.py \
       --excel "/tmp/dm-check-popo.xlsx" --parse-only --format json
     ```
     阅读 JSON 输出，补充脚本未能自动提取的预期值，生成完整 spec JSON。
   - **若输出为 `.docx`（文字文档）**：用 Read 工具读取文件内容
     ```
     Read /tmp/dm-check-popo.docx
     ```
     Claude 阅读文档内容，从中提取埋点事件名、字段定义和预期值，构建 spec JSON。

3. 生成完整 spec JSON 写入 `/tmp/dm-check-spec.json`。

#### 事件ID字符串输入

直接构建 spec JSON，events 包含用户指定的事件名，fields 为空对象 `{}`。

#### 其他输入

Claude 阅读并理解后创建 spec JSON。

### Step 2: 展示解析结果

向用户简要展示提取到的事件列表及关注字段，确认无误。

### Step 3: 选择数据来源

使用 AskUserQuestion 让用户选择日志来源：

> 请选择埋点数据的获取方式：

选项：
- **ELK 远端日志** — 从 ELK 拉取该账号最近 30 分钟的日志，无需连接设备，适合已在真机上操作过的场景
- **本地 adb 监听** — 实时监听当前连接设备的 logcat，适合边操作边验证的场景

#### 用户选择「ELK 远端日志」时

进入 **ELK 流程**（Step 4-ELK）。

#### 用户选择「本地 adb 监听」时

进入 **adb 流程**（Step 4-adb）。

---

### Step 4-ELK: ELK 远端日志流程

#### 4-ELK-1: 询问 UID

使用 AskUserQuestion 请用户提供 UID：

> 请在 Other 中输入要查询的用户 UID（数字）：

#### 4-ELK-2: 拉取日志并生成报告

```bash
python3 <skill-dir>/scripts/verify_tracking.py \
  --spec /tmp/dm-check-spec.json \
  --source elk --uid "<uid>" --time-range "last1h" \
  --output /tmp/dm-check-report.html
```

#### 4-ELK-3: 展示报告

```bash
open /tmp/dm-check-report.html
```

在对话中简要总结验证结论（通过/异常/未触发数量）。

若存在「未触发」的埋点，提示用户：可能是该时间窗口内未操作到对应场景，或选择切换到「本地 adb 监听」模式重新验证。

---

### Step 4-adb: 本地 adb 监听流程

#### 4-adb-1: 清空 logcat 并启动后台监听

```bash
adb logcat -c
adb logcat -v time "GLLogManager:D" "*:S" > /tmp/dm-check-listen.txt 2>&1 &
```

用 Bash 的 `run_in_background` 参数启动后台监听。

#### 4-adb-2: 提示用户操作（循环）

使用 AskUserQuestion 提示用户：

> logcat 监听已启动，请在设备上操作以触发以下埋点：
> [列出事件名及其触发行为]
> 操作完成后选择对应选项。

选项：
- **生成报告** — 不停止监听，基于当前已采集的日志生成报告
- **测试完成** — 停止监听并生成最终报告
- **取消** — 停止监听，不生成报告
- **重新启动** — 清空日志并重新启动监听

##### 用户选择「生成报告」时

不停止 adb 后台进程，直接读取当前 logcat 文件生成快照报告：

```bash
python3 <skill-dir>/scripts/verify_tracking.py \
  --spec /tmp/dm-check-spec.json \
  --source logcat-file --logcat-file /tmp/dm-check-listen.txt \
  --output /tmp/dm-check-report.html
```

```bash
open /tmp/dm-check-report.html
```

在对话中简要总结验证结论（通过/异常/未触发数量）。然后**再次回到 4-adb-2**，使用 AskUserQuestion 提示用户继续操作或结束：

> 报告已生成：通过 X / 异常 Y / 未触发 Z
> 监听仍在继续，可以继续在设备上操作以补充缺失的埋点。

选项同上。

##### 用户选择「测试完成」时

进入 Step 5-adb。

### Step 5-adb: 停止监听，生成最终报告

```bash
kill <pid>

python3 <skill-dir>/scripts/verify_tracking.py \
  --spec /tmp/dm-check-spec.json \
  --source logcat-file --logcat-file /tmp/dm-check-listen.txt \
  --output /tmp/dm-check-report.html
```

### Step 6: 展示报告

打开 HTML 报告：

```bash
open /tmp/dm-check-report.html
```

在对话中简要总结验证结论（通过/异常/未触发数量），提示用户查看 HTML 报告了解详情。

## 其他数据来源

### ELK 模式

```bash
python3 <skill-dir>/scripts/verify_tracking.py \
  --spec /tmp/dm-check-spec.json \
  --source elk --uid "<uid>" --time-range "today" \
  --output /tmp/dm-check-report.html
```

### logcat 文件模式

```bash
python3 <skill-dir>/scripts/verify_tracking.py \
  --spec /tmp/dm-check-spec.json \
  --source logcat-file --logcat-file <path> \
  --output /tmp/dm-check-report.html
```

## 预期值提取指南

备注/字段内容列中常见的预期值格式，Claude 应识别并填入 `expected_values`：

| 格式 | 示例 | 提取结果 |
|------|------|---------|
| 预计记录 + 数字:描述 | `预计记录：\n259：漫剧tab\n249：广场tab` | ["259", "249"] |
| 枚举值（中文括号） | `枚举值（看过、收藏、点赞）` | ["看过", "收藏", "点赞"] |
| 枚举值：列举 | `枚举值：全部、已看完、未看完` | ["全部", "已看完", "未看完"] |
| 类型枚举（KEY-描述） | `合集类型（DEFAULT-默认，COMIC-漫剧）` | ["DEFAULT", "COMIC"] |
| 取值: a/b/c | `取值: home/detail/profile` | ["home", "detail", "profile"] |
| 数字: 描述 | `1: 是, 0: 否` | ["1", "0"] |
| 固定值 | `固定值: share` | ["share"] |
| 纯描述 | `页面对应的id` | []（无法提取具体值） |

### 特殊标记

- **「本期新增」**: 修改埋点中字段名带 `（本期新增）` 后缀的字段是本次重点验证对象，spec 中应标记 `"is_new": true`
- **跨事件引用**: 如 `记录方式同page_view埋点的page_param字段`，Claude 应找到被引用事件的字段定义，复制其 expected_values
- **JSON 子字段**: 当字段类型为 json 时，备注中描述的子字段及其枚举值应通过 `sub_fields` 定义到 spec 中，脚本会自动验证子字段的存在性和取值。每个子字段结构同顶层字段（含 name、type、expected_values、description、is_new）

## 触发行为推断

| 事件名前缀 | 推断触发行为 |
|-----------|------------|
| `clk_` | 用户点击 |
| `exp_` | 元素曝光（元素可见时） |
| `page_` / `page_view` | 页面曝光（页面可见时） |
| 其他 | 参考 trigger_rule 字段 |

## logcat 解析说明

脚本使用 `-v time` 格式抓取 logcat（级别 D），匹配 `GLLogManager` tag 中的 `数字/send: {...}` 行。
日志中的 JSON 业务字段在顶层，`column_info` 等 json 类型字段直接是 JSON 对象（非字符串包裹）。
时间戳用于辅助判断触发时序。

## Excel 解析规则

详见 [references/excel-formats.md](references/excel-formats.md)

## ELK 查询说明

- 接口: `http://api.elk.x.netease.com:9550/a19_drpf_clientlog-*/_search`
- TOKEN: `20b6e03e3f8a48c2b2019d7e47d286bb`
- 时间范围支持: today/yesterday/last1h/last24h/last3d/last7d/YYYY-MM-DD
- **默认使用 `last1h`（最近 1 小时）**

## 常用公共字段（不参与验证）

```
f, msg_key, log_sid, platform, f_ver, info_append_way,
user_uid, user_name, role_name, gameid, gameimei, deviceid,
app_ver, system, channel, urs, network,
active_community_id, active_community_name, active_page_struc,
session_id, refer_action_id, refer_action_param
```
