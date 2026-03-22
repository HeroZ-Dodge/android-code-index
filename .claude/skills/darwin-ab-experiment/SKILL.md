---
name: darwin-ab-experiment
description: >
  在达尔文AB实验系统（测试服）中通过API接口自动创建AB实验。
  仅通过斜杠命令触发：/darwin-ab-experiment，不响应关键词触发，
  避免与 abtest-generator、abtestv2-generator 等 skill 冲突。
  功能：创建表达式模版、实验场景、功能实验，支持自动发布（审核+上线）。
---

# 达尔文AB实验自动创建 & 发布（API版）

通过接口调用在达尔文AB实验系统（测试服）自动完成AB实验的创建、审核、上线全流程。

## 基础信息

- **API Base URL**: `https://dashen-admin.abtest-dev.cbg.163.com`
- **认证方式**: Cookie `go_session_id`
- **认证配置文件**: `~/.config/darwin-ab-experiment/config.json`（用户级，不随项目分发）

## 认证配置

配置文件位于用户目录，**不包含在 skill 目录中**。首次使用时需手动创建：

```bash
mkdir -p ~/.config/darwin-ab-experiment
```

然后创建 `~/.config/darwin-ab-experiment/config.json`，格式如下：

```json
{
  "go_session_id": "xxx.yyy",
  "sso_csrftoken": "xxx",
  "sso_sessionid": "xxx",
  "corp_id": "你的企业账号（如 linzheng）",
  "corp_pw": "OPHASH_你的密码哈希"
}
```

> 如果配置文件不存在，脚本会自动打印以上格式提示。

### 三层认证降级策略

认证失败时按以下顺序自动降级，无需用户干预（前提是 config.json 中配置了账号密码）：

**第1层：go_session_id（有效期约7天）**
- 直接用 cookie 调用 API
- 失败时进入第2层

**第2层：SSO Session 刷新（sso_csrftoken + sso_sessionid）**
- 运行 `scripts/darwin_refresh_session.sh`，利用 SSO session 走 OAuth2 流程刷新 `go_session_id`
- 失败时进入第3层

**第3层：账号密码登录（corp_id + corp_pw）**
- 运行 `scripts/darwin_login_password.sh`，通过账号+密码哈希重新走完整登录流程
- 自动获取新的 `go_session_id` 和 SSO cookie 并写入 config.json
- 如果这也失败（密码哈希过期等），提示用户更新密码哈希

### 刷新脚本

**方式1：SSO Session 刷新**
```bash
bash <skill_dir>/scripts/darwin_refresh_session.sh [config.json路径]
```

**方式2：账号密码登录（完整登录流程）**
```bash
bash <skill_dir>/scripts/darwin_login_password.sh [config.json路径]
```

账号密码登录流程：
1. GET SSO 授权页 → 获取 csrftoken cookie
2. POST 提交 corp_id + corp_pw（OPHASH 密码哈希） → 302 拿到授权码 code
3. GET 达尔文回调地址带 code → 302 拿到新 go_session_id（Set-Cookie）
4. 更新 config.json（go_session_id + SSO cookie）
5. 验证新 session

### 密码哈希说明

`corp_pw` 字段存储的是 OPHASH 格式的密码哈希（如 `OPHASH_786b17cbc88aa4c5b632f15b8b8325e0`），不是明文密码。这个哈希由网易 SSO 登录页的前端 JS 生成。获取方式：
1. 在浏览器登录 dashen-admin.abtest-dev.cbg.163.com
2. 打开开发者工具（F12）→ Network
3. 找到 POST 到 `login.netease.com/connect/authorize` 的请求
4. 在 Form Data 中找到 `corppw` 字段的值（以 `OPHASH_` 开头）
5. 复制到 config.json 的 `corp_pw` 字段

### 执行 API 调用前的认证检查流程

1. 读取 config.json 获取 `go_session_id`
2. 执行第一个 API 调用
3. 如果返回认证失败（code 100012 或 401）：
   a. 先尝试 `scripts/darwin_refresh_session.sh` → 重新读取 config.json → 重试
   b. 如果刷新失败，且 config.json 有 corp_id + corp_pw → 尝试 `scripts/darwin_login_password.sh` → 重新读取 config.json → 重试
   c. 如果都失败 → 提示用户更新密码哈希或手动登录

## 用户输入参数

| 参数 | 类型 | 必填 | 描述 | 示例 |
|------|------|------|------|------|
| SN | String | 是 | 实验场景命名（英文+下划线） | `ad_test` |
| Name | String | 是 | 实验名称（中文或英文） | `广告弹窗实验` |
| Desc | String | 否 | 实验描述，为空时取 Name 的值 | `广告弹窗实验` |
| ds_app_version | String | 是 | 大神客户端版本号 | `4.14.0` |
| item_list | Array | 否 | 实验分组，默认两组 on/off | 见下方说明 |
| online_time | String | 否 | 上线时间，默认次日 00:00:00 | `2026-03-06 00:00:00` |

### 实验分组（item_list）

默认分组（无特殊说明时使用）：
- **基准组**：algorithm_name = `on`，流量 100%，标记为 is_base
- **实验组1**：algorithm_name = `off`，流量 0%

用户指定自定义分组时，按用户要求生成。例如用户说"分3组：1/2/3"：
- 基准组：algorithm_name = `1`，流量 100%，is_base
- 实验组1：algorithm_name = `2`，流量 0%
- 实验组2：algorithm_name = `3`，流量 0%

## API 调用流程（创建：6步 + 发布：5步）

### 创建脚本

```bash
bash <skill_dir>/scripts/darwin_create_experiment.sh --sn <SN> --name <名称> --version <版本号> [选项]
```

必选参数:
- `--sn` 实验场景SN（支持多级，如 `ranking|topic_sort`）
- `--name` 实验名称
- `--version` 大神客户端版本号

可选参数:
- `--desc` 实验描述（默认同 name，至少5个字符）
- `--field` 模版字段类型: `product`（默认）或 `squareId`
- `--field-value` 字段值（product 默认 `A19`，squareId 需指定圈子ID）
- `--online-time` 上线时间（默认次日 00:00:00）
- `--groups` 实验分组算法名，逗号分隔（默认 `on,off`）
- `--parent-names` 前置场景命名，用 `|` 分隔（当多级 SN 的前置场景不存在时需要提供）
- `--config` config.json 路径
- `--publish` 创建后自动发布（审核+通过+上线）

### 创建流程（脚本自动执行）

1. **检查场景拓扑**：GET `/v1/abtest_scene/list_topology` 确认 SN 是否已存在
2. **创建表达式模版**：POST `/v1/expr_template/add`（用实验名称作为模版名称）
3. **查询 field_id**：POST `/v1/expr_template/list`
4. **创建实验场景**：POST `/v1/abtest_scene/new`（支持多级 SN）
5. **生成实验 SN**：POST `/v1/abtest_step/gen_rand_sn`
6. **创建功能实验**：POST `/v1/abtest/algorithm/new`

### 模版字段类型

- **product**（默认）：关联项目ID，固定值 `A19`
- **squareId**：关联圈子ID，需指定具体的圈子ID

### 场景 SN 层级结构

SN 用 `|` 分隔层级：
- depth=1: `ranking`（parent_sn=""，parent_scene_sn=""）
- depth=2: `ranking|ranking_card`（parent_sn="ranking"，parent_scene_sn="ranking"）
- depth=3: `ranking|ranksquare|topic_sort`（parent_sn="ranking,ranking|ranksquare"，parent_scene_sn="ranking|ranksquare"）

创建前自动检查：
- 完整 SN 已存在 → 跳过创建模版和场景，直接查找已有模版
- 前置层级不存在且提供了 `--parent-names` → 自动逐级创建前置场景（含各自的模版）
- 前置层级不存在且未提供 `--parent-names` → 报错提示格式，如 `--parent-names "一级场景命名|二级场景命名"`

所有接口使用 `exec` 执行 `curl` 命令，Header 只需：
```
Content-Type: application/json;charset=UTF-8
Cookie: go_session_id=<从配置文件读取>
```

### 步骤1：创建表达式模版

```
POST /v1/expr_template/add
```

Request Body:
```json
{
  "app_id": "DASHEN",
  "template_name": "<SN>",
  "fields": [{
    "name": "product",
    "enabled": true,
    "type": "string",
    "operators": ["==", "in"],
    "rich_options": [],
    "options": null
  }]
}
```

Response 中提取 `data.id` → 保存为 `template_id`

### 步骤2：查询模版详情获取 field_id

```
POST /v1/expr_template/list
```

Request Body:
```json
{
  "app_id": "DASHEN"
}
```

Response 是 `data.rows` 或 `data` 字典包含列表。在列表中找到 `id == template_id` 的模版，提取 `fields[0].field_id` → 保存为 `expr_template_field_id`

### 步骤3：创建实验场景

```
POST /v1/abtest_scene/new
```

Request Body:
```json
{
  "abtest_type": "ALGORITHM_ABTEST",
  "app_id": "DASHEN",
  "parent_sn": "",
  "depth": 1,
  "parent_scene_sn": "",
  "hash_type": 0,
  "name": "<Name>",
  "sn": "<SN>",
  "desc": "<Desc>",
  "template_id": <template_id>,
  "mutex_id": null
}
```

### 步骤4：生成实验SN

```
POST /v1/abtest_step/gen_rand_sn
```

Request Body:
```json
{
  "app_id": "DASHEN"
}
```

Response 中提取 `data` → 保存为 `experiment_sn`

### 步骤5：创建功能实验

```
POST /v1/abtest/algorithm/new
```

Request Body:
```json
{
  "is_salt": true,
  "fill_mode": "old",
  "user_group_info": {"group_type": "RANDOM"},
  "is_long_term": false,
  "is_buyer_abtest": true,
  "is_rotate": false,
  "sn": "<experiment_sn>",
  "abtest_name": "<Name>",
  "desc": "<Desc>",
  "scene_sn": "<SN>",
  "expr_fields": [{
    "value": ["A19"],
    "expr_template_field_id": <expr_template_field_id>,
    "operator": "==",
    "field_name": "product"
  }],
  "ds_app_version": "<ds_app_version>",
  "ds_scene_sn": "大神整体",
  "ds_recommend_flow": "整体",
  "flow_rate": "100.0",
  "item_list": <item_list>,
  "standard_list": "TEST",
  "online_time": "<online_time>",
  "app_id": "DASHEN",
  "indicators": {"standard_list": ["TEST"]}
}
```

## 默认 item_list 生成

```json
[
  {
    "flow_rate": "100.0",
    "is_base": true,
    "name": "基准组",
    "config_list": [{"value": "on", "key": "algorithm_name", "value_type": "string"}],
    "indicators": null
  },
  {
    "flow_rate": "0.0",
    "name": "实验组1",
    "config_list": [{"value": "off", "key": "algorithm_name", "value_type": "string"}],
    "indicators": null
  }
]
```

## 固定参数汇总

| 参数 | 固定值 | 说明 |
|------|--------|------|
| app_id | `DASHEN` | 应用ID |
| abtest_type | `ALGORITHM_ABTEST` | 实验类型 |
| hash_type | `0` | 先urs后设备id |
| depth | `1` | 顶级场景 |
| expr_fields[0].value | `["A19"]` | 项目ID，固定 |
| expr_fields[0].field_name | `product` | 字段名，固定 |
| expr_fields[0].operator | `==` | 操作符，固定 |
| ds_scene_sn | `大神整体` | 固定 |
| ds_recommend_flow | `整体` | 固定 |
| is_salt | `true` | 加盐 |
| is_rotate | `false` | 不按月轮转 |
| standard_list | `TEST` | 测试指标 |
| fill_mode | `old` | 推荐算法模式 |
| online_time 默认 | 次日 00:00:00 | 可覆盖 |

## 错误处理

- **认证失败**（code 100012 或 401）：自动触发三层认证降级（go_session_id → SSO 刷新 → 账号密码登录）
- **模版名重复**：提示用户换一个 SN
- **模版已被场景使用**：正常，一个模版只能关联一个场景
- **场景SN重复**：提示用户换一个 SN
- **上线时间已过期**（提交审核时）：自动更新 online_time 为 5 分钟后再重新提交
- 每步调用后检查返回的 `code`，`100000` 为成功，其他值打印 `message` 和 `detail`

## 实验发布流程（审核 + 通过 + 上线）

创建实验后，需要经过「提交审核 → 通过审核 → 上线」三步才能生效。

### 一键发布脚本

```bash
bash <skill_dir>/scripts/darwin_publish_experiment.sh <experiment_id> [config.json路径]
```

脚本自动执行以下流程：

### 步骤6：检查实验状态 & 更新上线时间

```
POST /v1/abtest/algorithm/list
```
查询实验当前状态。如果上线时间已过期，自动调用更新接口修改 `online_time`。

```
POST /v1/abtest/algorithm/update
```
Request Body: 完整的实验数据（同创建时的结构），修改 `online_time` 字段。

### 步骤7：提交审核

```
POST /v1/abtest/submit_audit
```
Request Body:
```json
{
  "id": <experiment_id>,
  "app_id": "DASHEN"
}
```

### 步骤8：查询待审核记录获取 audit_id

```
POST /v1/abtest_audit/list
```
Request Body:
```json
{
  "app_id": "DASHEN",
  "abtest_type": "ALGORITHM_ABTEST",
  "status": "INIT",
  "abtest_id": <experiment_id>,
  "page": 1,
  "page_size": 1
}
```
通过 `abtest_id` + `status=INIT`（待审核）精确查询，从返回的 `data.rows[0].id` 提取 `audit_id`。

> 注意：`audit_id`（审核记录ID）与 `experiment_id`（实验ID）是不同的！

### 步骤9：通过审核

```
POST /v1/abtest_audit/pass
```
Request Body:
```json
{
  "app_id": "DASHEN",
  "id": <audit_id>
}
```

### 步骤10：上线实验

```
POST /v1/abtest/online
```
Request Body:
```json
{
  "id": <experiment_id>,
  "app_id": "DASHEN"
}
```

## 完整执行示例（创建 + 发布）

### 方式1：使用脚本（推荐）

```bash
# 基本创建 + 自动发布
bash <skill_dir>/scripts/darwin_create_experiment.sh \
  --sn ad_popup --name "广告弹窗实验" --version 4.14.0 --publish

# 关联圈子ID
bash <skill_dir>/scripts/darwin_create_experiment.sh \
  --sn "square|widget|hot_board" --name "热门榜单实验" --version 4.14.0 \
  --field squareId --field-value "5be96405f1aeb71ff0c6f0dd" --publish

# 自定义3组分组
bash <skill_dir>/scripts/darwin_create_experiment.sh \
  --sn test_exp --name "测试实验" --version 4.14.0 \
  --groups "on,off,control" --publish

# 三级 SN，前置场景不存在时自动创建
bash <skill_dir>/scripts/darwin_create_experiment.sh \
  --sn "a|b|c" --name "三级实验" --version 4.14.0 \
  --parent-names "一级场景|二级场景" --publish
```

### 方式2：手动调用 API

1. 检查 config.json 是否存在且有 go_session_id
2. 设定参数：SN=ad_popup, Name=广告弹窗实验, Desc=广告弹窗实验, ds_app_version=4.14.0
3. 依次执行步骤1-6（创建实验），拿到 `experiment_id`
4. 执行发布脚本 `scripts/darwin_publish_experiment.sh <experiment_id>`
5. 最终汇总输出创建 + 上线结果

### 仅发布已有实验

```bash
bash <skill_dir>/scripts/darwin_publish_experiment.sh <experiment_id>
```

## 缺少 ds_app_version 时

如果用户没有提供版本号（ds_app_version），**必须询问用户补充**，不能使用默认值。提示：
> 请提供大神客户端版本号（如 4.14.0），用于关联实验。
