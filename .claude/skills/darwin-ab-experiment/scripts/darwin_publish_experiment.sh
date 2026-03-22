#!/usr/bin/env bash
# darwin_publish_experiment.sh
# 对已创建的达尔文AB实验执行：提交审核 → 通过审核 → 上线
# 用法: ./darwin_publish_experiment.sh <experiment_id> [config.json路径]
#
# experiment_id: 实验ID（创建实验后返回的 id，如 90125）
#
# 流程:
#   1. 检查实验状态，如果上线时间已过期则自动更新
#   2. 提交审核 (submit_audit)
#   3. 查询审核记录获取 audit_id
#   4. 通过审核 (audit/pass)
#   5. 上线实验 (abtest/online)

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "用法: $0 <experiment_id> [config.json路径]"
  echo "  experiment_id: 实验ID（如 90125）"
  exit 1
fi

EXPERIMENT_ID="$1"
CONFIG_FILE="${2:-$HOME/.config/darwin-ab-experiment/config.json}"
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_ID="DASHEN"
BASE_URL="https://dashen-admin.abtest-dev.cbg.163.com"

if [ ! -f "$CONFIG_FILE" ]; then
  echo "ERROR: 配置文件不存在: $CONFIG_FILE"
  echo ""
  echo "请创建配置文件："
  echo "  mkdir -p ~/.config/darwin-ab-experiment"
  echo "  然后创建 $CONFIG_FILE，内容格式如下："
  echo '  {'
  echo '    "go_session_id": "xxx.yyy",'
  echo '    "sso_csrftoken": "xxx",'
  echo '    "sso_sessionid": "xxx",'
  echo '    "corp_id": "你的企业账号（如 linzheng）",'
  echo '    "corp_pw": "OPHASH_你的密码哈希"'
  echo '  }'
  exit 1
fi

get_session() {
  python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['go_session_id'])"
}

# 通用 API 调用函数，支持认证失败时自动重新登录
api_call() {
  local endpoint="$1"
  local body="$2"
  local session_id
  session_id=$(get_session)

  local response
  response=$(curl -s -X POST "${BASE_URL}${endpoint}" \
    -H 'content-type: application/json;charset=UTF-8' \
    -H "cookie: go_session_id=${session_id}" \
    -d "$body")

  local code
  code=$(echo "$response" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('code',''))" 2>/dev/null || echo "")

  # 认证失败，尝试重新登录
  if [ "$code" = "100012" ]; then
    echo "    ⚠️  认证失败，尝试重新登录..."
    # 第1层：SSO session 刷新
    if bash "$SKILL_DIR/darwin_refresh_session.sh" "$CONFIG_FILE" 2>/dev/null; then
      session_id=$(get_session)
    else
      # 第2层：账号密码登录
      if bash "$SKILL_DIR/darwin_login_password.sh" "$CONFIG_FILE" 2>/dev/null; then
        session_id=$(get_session)
      else
        echo "ERROR: 无法重新登录，请手动更新认证信息"
        echo "$response"
        exit 10
      fi
    fi

    # 重试
    response=$(curl -s -X POST "${BASE_URL}${endpoint}" \
      -H 'content-type: application/json;charset=UTF-8' \
      -H "cookie: go_session_id=${session_id}" \
      -d "$body")
  fi

  echo "$response"
}

check_response() {
  local response="$1"
  local step_name="$2"
  local code
  code=$(echo "$response" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('code',''))" 2>/dev/null || echo "")
  local message
  message=$(echo "$response" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('message','') + (': ' + d['detail'] if d.get('detail') else ''))" 2>/dev/null || echo "")

  # 成功：code 为 100000 或者没有 code 字段（某些接口成功时不返回 code）
  if [ "$code" = "100000" ] || [ -z "$code" ]; then
    return 0
  fi
  echo "ERROR: ${step_name}失败 [code=$code] $message"
  return 1
}

echo "=== 达尔文实验发布流程 ==="
echo "实验ID: $EXPERIMENT_ID"
echo ""

# ─── 步骤0: 查询实验当前状态 ───────────────────────
echo ">>> 步骤0: 查询实验状态..."
EXPERIMENT_INFO=$(api_call "/v1/abtest/algorithm/list" \
  "{\"app_id\":\"${APP_ID}\",\"query_type\":\"MY_ABTEST\",\"page\":1,\"page_size\":100}")

EXPERIMENT_DATA=$(echo "$EXPERIMENT_INFO" | python3 -c "
import json, sys
d = json.load(sys.stdin)
# 有些接口成功时没有 code 字段，直接返回 data；失败时有 code != 100000
code = d.get('code')
if code is not None and code != 100000:
    print('ERROR')
    sys.exit(0)
rows = d.get('data',{}).get('rows',[])
for r in rows:
    if r['id'] == ${EXPERIMENT_ID}:
        print(json.dumps(r, ensure_ascii=False))
        sys.exit(0)
print('NOT_FOUND')
" 2>/dev/null)

if [ "$EXPERIMENT_DATA" = "ERROR" ]; then
  echo "ERROR: 查询实验列表失败"
  exit 2
fi

if [ "$EXPERIMENT_DATA" = "NOT_FOUND" ]; then
  echo "ERROR: 未找到实验ID=${EXPERIMENT_ID}，请确认ID是否正确"
  exit 2
fi

STATUS=$(echo "$EXPERIMENT_DATA" | python3 -c "import json,sys; print(json.load(sys.stdin)['status'])")
STATUS_DESC=$(echo "$EXPERIMENT_DATA" | python3 -c "import json,sys; print(json.load(sys.stdin)['status_desc'])")
ONLINE_TIME=$(echo "$EXPERIMENT_DATA" | python3 -c "import json,sys; print(json.load(sys.stdin)['online_time'])")
EXPERIMENT_NAME=$(echo "$EXPERIMENT_DATA" | python3 -c "import json,sys; print(json.load(sys.stdin)['abtest_name'])")

echo "    实验名称: $EXPERIMENT_NAME"
echo "    当前状态: $STATUS ($STATUS_DESC)"
echo "    上线时间: $ONLINE_TIME"

# 如果已经上线，直接退出
if [ "$STATUS" = "ONLINE" ]; then
  echo ""
  echo "✅ 实验已经在上线中，无需重复操作"
  exit 0
fi

# ─── 步骤1: 检查并更新上线时间 ───────────────────────
# 如果上线时间已过期，更新为明天 00:00:00
CURRENT_TS=$(date +%s)
ONLINE_TS=$(python3 -c "
from datetime import datetime
try:
    dt = datetime.strptime('${ONLINE_TIME}', '%Y-%m-%d %H:%M:%S')
    print(int(dt.timestamp()))
except:
    print(0)
")

if [ "$ONLINE_TS" -lt "$CURRENT_TS" ]; then
  echo ""
  echo ">>> 步骤1: 上线时间已过期，更新为 5 分钟后..."
  NEW_ONLINE_TIME=$(python3 -c "
from datetime import datetime, timedelta
t = datetime.now() + timedelta(minutes=5)
print(t.strftime('%Y-%m-%d %H:%M:%S'))
")
  echo "    新上线时间: $NEW_ONLINE_TIME"

  # 构造更新请求体（基于当前实验数据，只修改 online_time）
  UPDATE_BODY=$(echo "$EXPERIMENT_DATA" | python3 -c "
import json, sys
data = json.load(sys.stdin)
data['online_time'] = '${NEW_ONLINE_TIME}'
# 确保必要字段
data['app_id'] = '${APP_ID}'
data['standard_list'] = 'TEST'
data['origin_flow_rate'] = str(data.get('flow_rate', '100'))
data['enable_global_group'] = False
print(json.dumps(data, ensure_ascii=False))
")

  UPDATE_RESP=$(api_call "/v1/abtest/algorithm/update" "$UPDATE_BODY")
  if ! check_response "$UPDATE_RESP" "更新实验"; then
    echo "    尝试继续提交审核..."
  else
    echo "    ✅ 上线时间已更新"
  fi
else
  echo "    上线时间未过期，无需更新"
fi

# ─── 步骤2: 提交审核 ───────────────────────
echo ""
echo ">>> 步骤2: 提交审核..."
SUBMIT_BODY="{\"id\":${EXPERIMENT_ID},\"app_id\":\"${APP_ID}\"}"
SUBMIT_RESP=$(api_call "/v1/abtest/submit_audit" "$SUBMIT_BODY")

if ! check_response "$SUBMIT_RESP" "提交审核"; then
  # 检查是否因为上线时间过期
  DETAIL=$(echo "$SUBMIT_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin).get('detail',''))" 2>/dev/null || echo "")
  if echo "$DETAIL" | grep -q "上线时间已过期"; then
    echo "    上线时间仍然过期，请手动检查"
  fi
  exit 3
fi
echo "    ✅ 审核已提交"

# ─── 步骤3: 查询审核记录获取 audit_id ───────────────────────
echo ""
echo ">>> 步骤3: 查询审核记录..."
sleep 1  # 等待审核记录生成

AUDIT_RESP=$(api_call "/v1/abtest_audit/list" \
  "{\"app_id\":\"${APP_ID}\",\"abtest_type\":\"ALGORITHM_ABTEST\",\"status\":\"INIT\",\"abtest_id\":${EXPERIMENT_ID},\"page\":1,\"page_size\":1}")

AUDIT_ID=$(echo "$AUDIT_RESP" | python3 -c "
import json, sys
d = json.load(sys.stdin)
code = d.get('code')
if code is not None and code != 100000:
    print('')
    sys.exit(0)
rows = d.get('data',{}).get('rows',[])
if rows:
    print(rows[0]['id'])
else:
    print('')
" 2>/dev/null)

if [ -z "$AUDIT_ID" ]; then
  echo "ERROR: 未找到审核记录"
  exit 4
fi
echo "    审核记录ID: $AUDIT_ID"

# ─── 步骤4: 通过审核 ───────────────────────
echo ""
echo ">>> 步骤4: 通过审核..."
PASS_BODY="{\"app_id\":\"${APP_ID}\",\"id\":${AUDIT_ID}}"
PASS_RESP=$(api_call "/v1/abtest_audit/pass" "$PASS_BODY")

if ! check_response "$PASS_RESP" "通过审核"; then
  exit 5
fi
echo "    ✅ 审核已通过"

# ─── 步骤5: 上线实验 ───────────────────────
echo ""
echo ">>> 步骤5: 上线实验..."
ONLINE_BODY="{\"id\":${EXPERIMENT_ID},\"app_id\":\"${APP_ID}\"}"
ONLINE_RESP=$(api_call "/v1/abtest/online" "$ONLINE_BODY")

if ! check_response "$ONLINE_RESP" "上线实验"; then
  exit 6
fi
echo "    ✅ 实验已上线"

echo ""
echo "========================================="
echo "✅ 发布完成！"
echo "    实验: $EXPERIMENT_NAME (ID: $EXPERIMENT_ID)"
echo "    状态: 上线中"
echo "========================================="
