#!/usr/bin/env bash
# darwin_create_experiment.sh
# 在达尔文AB实验系统自动创建实验（创建模版 → 创建场景 → 创建实验）
#
# 用法:
#   ./darwin_create_experiment.sh --sn <SN> --name <名称> --version <版本号> [选项]
#
# 必选参数:
#   --sn            实验场景SN（支持多级，如 ranking|topic_sort）
#   --name          实验名称
#   --version       大神客户端版本号（如 4.14.0）
#
# 可选参数:
#   --desc          实验描述（默认同 name）
#   --field         模版字段类型: product 或 squareId（默认 product）
#   --field-value   字段值（product 默认 A19，squareId 需指定圈子ID）
#   --online-time   上线时间（默认次日 00:00:00）
#   --groups        实验分组，逗号分隔（默认 on,off）
#   --config        config.json 路径
#   --publish       创建后自动发布（审核+通过+上线）
#
# 示例:
#   ./darwin_create_experiment.sh --sn ad_popup --name "广告弹窗实验" --version 4.14.0
#   ./darwin_create_experiment.sh --sn "ranking|topic_sort" --name "话题排序实验" --version 4.14.0 --field squareId --field-value "5be96405f1aeb71ff0c6f0dd"
#   ./darwin_create_experiment.sh --sn test_exp --name "测试实验" --version 4.14.0 --groups "a,b,c" --publish

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE=""
APP_ID="DASHEN"
BASE_URL="https://dashen-admin.abtest-dev.cbg.163.com"

# 默认参数
SN=""
NAME=""
DESC=""
VERSION=""
FIELD_TYPE="product"
FIELD_VALUE="A19"
ONLINE_TIME=""
EXP_GROUPS="on,off"
AUTO_PUBLISH=true
PARENT_NAMES=""

# 解析参数
while [[ $# -gt 0 ]]; do
  case "$1" in
    --sn) SN="$2"; shift 2 ;;
    --name) NAME="$2"; shift 2 ;;
    --desc) DESC="$2"; shift 2 ;;
    --version) VERSION="$2"; shift 2 ;;
    --field) FIELD_TYPE="$2"; shift 2 ;;
    --field-value) FIELD_VALUE="$2"; shift 2 ;;
    --online-time) ONLINE_TIME="$2"; shift 2 ;;
    --groups) EXP_GROUPS="$2"; shift 2 ;;
    --config) CONFIG_FILE="$2"; shift 2 ;;
    --publish) AUTO_PUBLISH=true; shift ;;
    --parent-names) PARENT_NAMES="$2"; shift 2 ;;
    *) echo "未知参数: $1"; exit 1 ;;
  esac
done

# 默认配置文件路径（用户级目录）
if [ -z "$CONFIG_FILE" ]; then
  CONFIG_FILE="$HOME/.config/darwin-ab-experiment/config.json"
fi

# 参数校验
if [ -z "$SN" ]; then echo "ERROR: 必须指定 --sn"; exit 1; fi
if [ -z "$NAME" ]; then echo "ERROR: 必须指定 --name"; exit 1; fi
if [ -z "$VERSION" ]; then echo "ERROR: 必须指定 --version"; exit 1; fi
if [ -z "$DESC" ]; then DESC="$NAME"; fi

# desc 至少5个字符（服务端按字符数检查，非字节数）
DESC=$(python3 -c "
s = '${DESC}'
if len(s) < 5:
    s = s + '实验'
print(s)
")

# 默认上线时间为次日 00:00:00
if [ -z "$ONLINE_TIME" ]; then
  ONLINE_TIME=$(python3 -c "from datetime import datetime,timedelta; print((datetime.now()+timedelta(days=1)).strftime('%Y-%m-%d 00:00:00'))")
fi

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
  local method="$1"
  local endpoint="$2"
  local body="${3:-}"
  local session_id
  session_id=$(get_session)

  local response
  if [ "$method" = "GET" ]; then
    response=$(curl -s "$endpoint" \
      -H 'accept: application/json' \
      -H "cookie: go_session_id=${session_id}")
  else
    response=$(curl -s -X POST "${BASE_URL}${endpoint}" \
      -H 'content-type: application/json;charset=UTF-8' \
      -H "cookie: go_session_id=${session_id}" \
      -d "$body")
  fi

  local code
  code=$(echo "$response" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('code',''))" 2>/dev/null || echo "")

  # 认证失败，尝试重新登录
  if [ "$code" = "100012" ] || [ "$code" = "100010" ]; then
    echo "    ⚠️  认证失败，尝试重新登录..." >&2
    if bash "$SKILL_DIR/darwin_refresh_session.sh" "$CONFIG_FILE" >/dev/null 2>&1; then
      session_id=$(get_session)
    elif bash "$SKILL_DIR/darwin_login_password.sh" "$CONFIG_FILE" >/dev/null 2>&1; then
      session_id=$(get_session)
    else
      echo "ERROR: 无法重新登录" >&2
      echo "$response"
      return 1
    fi

    if [ "$method" = "GET" ]; then
      response=$(curl -s "$endpoint" \
        -H 'accept: application/json' \
        -H "cookie: go_session_id=${session_id}")
    else
      response=$(curl -s -X POST "${BASE_URL}${endpoint}" \
        -H 'content-type: application/json;charset=UTF-8' \
        -H "cookie: go_session_id=${session_id}" \
        -d "$body")
    fi
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

  if [ "$code" = "100000" ] || [ -z "$code" ]; then
    return 0
  fi
  echo "ERROR: ${step_name}失败 [code=$code] $message"
  return 1
}

echo "=== 达尔文实验创建流程 ==="
echo "SN:       $SN"
echo "名称:     $NAME"
echo "描述:     $DESC"
echo "版本:     $VERSION"
echo "字段:     $FIELD_TYPE = $FIELD_VALUE"
echo "上线时间: $ONLINE_TIME"
echo "分组:     $EXP_GROUPS"
echo ""

# ─── 解析多级 SN ───────────────────────
# SN 格式: "a|b|c"，表示 depth=3，parent_scene_sn="a|b"
IFS='|' read -ra SN_PARTS <<< "$SN"
SN_DEPTH=${#SN_PARTS[@]}
LEAF_SN="${SN_PARTS[$((SN_DEPTH-1))]}"

echo ">>> SN 层级深度: $SN_DEPTH"

# ─── 步骤1: 检查场景拓扑，确认 SN 是否已存在 ───────────────────────
echo ""
echo ">>> 步骤1: 检查场景拓扑..."
TOPO_RESP=$(api_call "GET" "${BASE_URL}/v1/abtest_scene/list_topology?abtest_type=ALGORITHM_ABTEST&app_id=${APP_ID}")

SCENE_CHECK=$(echo "$TOPO_RESP" | python3 -c "
import json, sys

d = json.load(sys.stdin)
topo = d.get('data', {}).get('scene_topo', [])

sn_parts = '${SN}'.split('|')
depth = len(sn_parts)

def find_sn(nodes, target_sn):
    \"\"\"递归查找 SN 是否存在\"\"\"
    for node in nodes:
        if node.get('sn') == target_sn:
            return True
        children = node.get('sub_scene', []) or node.get('children', []) or []
        if find_sn(children, target_sn):
            return True
    return False

# 检查完整 SN 是否已存在
full_sn = '|'.join(sn_parts)
if find_sn(topo, full_sn):
    print('EXISTS')
    sys.exit(0)

# 检查各级前置 SN 是否存在
missing = []
for i in range(depth - 1):
    parent_sn = '|'.join(sn_parts[:i+1])
    if not find_sn(topo, parent_sn):
        missing.append(parent_sn)

if missing:
    print('MISSING:' + ','.join(missing))
else:
    print('OK')
" 2>/dev/null)

if [ "$SCENE_CHECK" = "EXISTS" ]; then
  echo "    场景 SN=$SN 已存在，跳过创建模版和场景"
  SKIP_SCENE=true

  # 但还是需要找到 template_id 和 field_id
  TEMPLATE_INFO=$(echo "$TOPO_RESP" | python3 -c "
import json, sys
# 场景已存在时，从模版列表中查找
print('NEED_TEMPLATE_LOOKUP')
" 2>/dev/null)
elif echo "$SCENE_CHECK" | grep -q "^MISSING:"; then
  MISSING_SNS=$(echo "$SCENE_CHECK" | cut -d: -f2)
  echo "    ⚠️  以下前置场景 SN 不存在: $MISSING_SNS"

  if [ -z "$PARENT_NAMES" ]; then
    # 没有传 --parent-names，生成提示信息
    MISSING_HINT=$(python3 -c "
missing = '${MISSING_SNS}'.split(',')
hints = []
for m in missing:
    parts = m.split('|')
    level = len(parts)
    hints.append(f'{level}级场景命名')
print('|'.join(hints))
")
    echo ""
    echo "ERROR: 需要提供前置场景的命名"
    echo "请添加参数 --parent-names \"${MISSING_HINT}\""
    echo ""
    echo "示例: --parent-names \"${MISSING_HINT}\""
    exit 2
  fi

  # 解析 parent-names，用 | 分隔
  IFS='|' read -ra PARENT_NAME_LIST <<< "$PARENT_NAMES"
  IFS=',' read -ra MISSING_SN_LIST <<< "$MISSING_SNS"

  if [ ${#PARENT_NAME_LIST[@]} -ne ${#MISSING_SN_LIST[@]} ]; then
    echo "ERROR: --parent-names 数量(${#PARENT_NAME_LIST[@]})与缺失场景数量(${#MISSING_SN_LIST[@]})不匹配"
    echo "缺失场景: $MISSING_SNS"
    echo "请提供格式: --parent-names \"名称1|名称2\""
    exit 2
  fi

  echo "    将自动创建前置场景..."
  echo ""

  # 逐个创建缺失的前置场景（每个都需要先创建模版）
  for i in "${!MISSING_SN_LIST[@]}"; do
    PARENT_SN_FULL="${MISSING_SN_LIST[$i]}"
    PARENT_NAME="${PARENT_NAME_LIST[$i]}"
    # 去掉首尾空格
    PARENT_NAME=$(echo "$PARENT_NAME" | xargs)

    # 确保 desc 至少5个字符（服务端按字符数检查，非字节数）
    PARENT_DESC="$PARENT_NAME"
    PARENT_DESC=$(python3 -c "
s = '${PARENT_NAME}'
if len(s) < 5:
    s = s + '场景描述'
print(s)
")

    IFS='|' read -ra PARENT_SN_PARTS <<< "$PARENT_SN_FULL"
    PARENT_DEPTH=${#PARENT_SN_PARTS[@]}
    PARENT_LEAF_SN="${PARENT_SN_PARTS[$((PARENT_DEPTH-1))]}"

    echo ">>> 创建前置场景 [$((i+1))/${#MISSING_SN_LIST[@]}]: $PARENT_SN_FULL ($PARENT_NAME)"

    # 创建模版（用场景名称作为模版名称）
    echo "    创建模版: $PARENT_NAME"
    P_TEMPLATE_BODY=$(python3 -c "
import json
body = {
    'app_id': '${APP_ID}',
    'template_name': '${PARENT_NAME}',
    'fields': [{
        'name': '${FIELD_TYPE}',
        'enabled': True,
        'type': 'string',
        'operators': ['==', 'in'],
        'options': None
    }]
}
print(json.dumps(body, ensure_ascii=False))
")
    P_TEMPLATE_RESP=$(api_call "POST" "/v1/expr_template/add" "$P_TEMPLATE_BODY")
    if ! check_response "$P_TEMPLATE_RESP" "创建前置模版($PARENT_NAME)"; then
      exit 3
    fi
    P_TEMPLATE_ID=$(echo "$P_TEMPLATE_RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('data',{}).get('id',''))" 2>/dev/null)
    echo "    ✅ 模版已创建, template_id=$P_TEMPLATE_ID"

    # 创建场景
    P_SCENE_BODY=$(python3 -c "
import json

sn_parts = '${PARENT_SN_FULL}'.split('|')
depth = len(sn_parts)
leaf_sn = sn_parts[-1]

if depth == 1:
    parent_sn = ''
    parent_scene_sn = ''
else:
    ancestors = []
    for i in range(1, depth):
        ancestors.append('|'.join(sn_parts[:i]))
    parent_sn = ','.join(ancestors)
    parent_scene_sn = '|'.join(sn_parts[:-1])

body = {
    'abtest_type': 'ALGORITHM_ABTEST',
    'app_id': '${APP_ID}',
    'parent_sn': parent_sn,
    'depth': depth,
    'parent_scene_sn': parent_scene_sn,
    'hash_type': 0,
    'name': '${PARENT_NAME}',
    'sn': leaf_sn,
    'desc': '${PARENT_DESC}',
    'template_id': ${P_TEMPLATE_ID},
    'mutex_id': None
}
print(json.dumps(body, ensure_ascii=False))
")
    P_SCENE_RESP=$(api_call "POST" "/v1/abtest_scene/new" "$P_SCENE_BODY")
    if ! check_response "$P_SCENE_RESP" "创建前置场景($PARENT_SN_FULL)"; then
      exit 5
    fi
    echo "    ✅ 场景已创建, SN=$PARENT_SN_FULL (depth=$PARENT_DEPTH)"
    echo ""
  done

  echo "    所有前置场景创建完成，继续创建目标场景..."
  SKIP_SCENE=false
else
  echo "    场景 SN=$SN 不存在，将创建"
  SKIP_SCENE=false
fi

# ─── 步骤2: 创建表达式模版 ───────────────────────
if [ "$SKIP_SCENE" = true ]; then
  echo ""
  echo ">>> 步骤2: 查找已有模版..."
  TEMPLATE_LIST_RESP=$(api_call "POST" "/v1/expr_template/list" "{\"app_id\":\"${APP_ID}\"}")

  TEMPLATE_IDS=$(echo "$TEMPLATE_LIST_RESP" | python3 -c "
import json, sys
d = json.load(sys.stdin)
data = d.get('data', {})
rows = data.get('rows', data) if isinstance(data, dict) else data
if isinstance(rows, list):
    target_sn = '${SN}'
    for r in rows:
        scene_infos = r.get('scene_infos') or []
        for si in scene_infos:
            # 场景 SN 可能是完整路径
            if si.get('sn') == target_sn:
                fields = r.get('fields', []) or []
                for f in fields:
                    if f.get('enabled'):
                        print(f'{r[\"id\"]}|{f[\"field_id\"]}|{f[\"name\"]}')
                        sys.exit(0)
    # 没找到关联到此场景的模版
    print('NOT_FOUND')
" 2>/dev/null)

  if [ "$TEMPLATE_IDS" = "NOT_FOUND" ]; then
    echo "    WARNING: 未找到关联到 SN=$SN 的模版，将创建新模版"
    SKIP_SCENE=false
  else
    TEMPLATE_ID=$(echo "$TEMPLATE_IDS" | cut -d'|' -f1)
    FIELD_ID=$(echo "$TEMPLATE_IDS" | cut -d'|' -f2)
    FIELD_NAME=$(echo "$TEMPLATE_IDS" | cut -d'|' -f3)
    echo "    找到模版: template_id=$TEMPLATE_ID, field_id=$FIELD_ID, field=$FIELD_NAME"
    # 如果字段类型不匹配，给个警告
    if [ "$FIELD_NAME" != "$FIELD_TYPE" ]; then
      echo "    ⚠️  注意：已有模版使用字段 $FIELD_NAME，而非 $FIELD_TYPE"
      FIELD_TYPE="$FIELD_NAME"
    fi
  fi
fi

if [ "$SKIP_SCENE" = false ]; then
  echo ""
  echo ">>> 步骤2: 创建表达式模版..."
  echo "    模版名称: $NAME"
  echo "    字段类型: $FIELD_TYPE"

  TEMPLATE_BODY=$(python3 -c "
import json
body = {
    'app_id': '${APP_ID}',
    'template_name': '${NAME}',
    'fields': [{
        'name': '${FIELD_TYPE}',
        'enabled': True,
        'type': 'string',
        'operators': ['==', 'in'],
        'options': None
    }]
}
print(json.dumps(body, ensure_ascii=False))
")

  TEMPLATE_RESP=$(api_call "POST" "/v1/expr_template/add" "$TEMPLATE_BODY")
  if ! check_response "$TEMPLATE_RESP" "创建表达式模版"; then
    exit 3
  fi

  TEMPLATE_ID=$(echo "$TEMPLATE_RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('data',{}).get('id',''))" 2>/dev/null)
  echo "    ✅ 模版已创建, template_id=$TEMPLATE_ID"

  # ─── 步骤3: 查询 field_id ───────────────────────
  echo ""
  echo ">>> 步骤3: 查询 field_id..."
  FIELD_LIST_RESP=$(api_call "POST" "/v1/expr_template/list" "{\"app_id\":\"${APP_ID}\"}")

  FIELD_ID=$(echo "$FIELD_LIST_RESP" | python3 -c "
import json, sys
d = json.load(sys.stdin)
data = d.get('data', {})
rows = data.get('rows', data) if isinstance(data, dict) else data
if isinstance(rows, list):
    for r in rows:
        if r.get('id') == ${TEMPLATE_ID}:
            fields = r.get('fields', []) or []
            for f in fields:
                if f.get('enabled') and f.get('name') == '${FIELD_TYPE}':
                    print(f['field_id'])
                    sys.exit(0)
print('')
" 2>/dev/null)

  if [ -z "$FIELD_ID" ]; then
    echo "ERROR: 无法获取 field_id"
    exit 4
  fi
  echo "    field_id=$FIELD_ID"

  # ─── 步骤4: 创建实验场景 ───────────────────────
  echo ""
  echo ">>> 步骤4: 创建实验场景..."

  # 构造场景创建参数
  SCENE_BODY=$(python3 -c "
import json

sn_parts = '${SN}'.split('|')
depth = len(sn_parts)
leaf_sn = sn_parts[-1]

if depth == 1:
    parent_sn = ''
    parent_scene_sn = ''
else:
    # parent_sn: 逗号分隔的所有祖先完整路径
    ancestors = []
    for i in range(1, depth):
        ancestors.append('|'.join(sn_parts[:i]))
    parent_sn = ','.join(ancestors)
    # parent_scene_sn: 直接父级的完整路径
    parent_scene_sn = '|'.join(sn_parts[:-1])

body = {
    'abtest_type': 'ALGORITHM_ABTEST',
    'app_id': '${APP_ID}',
    'parent_sn': parent_sn,
    'depth': depth,
    'parent_scene_sn': parent_scene_sn,
    'hash_type': 0,
    'name': '${NAME}',
    'sn': leaf_sn,
    'desc': '${DESC}',
    'template_id': ${TEMPLATE_ID},
    'mutex_id': None
}
print(json.dumps(body, ensure_ascii=False))
")

  SCENE_RESP=$(api_call "POST" "/v1/abtest_scene/new" "$SCENE_BODY")
  if ! check_response "$SCENE_RESP" "创建实验场景"; then
    exit 5
  fi
  echo "    ✅ 场景已创建, SN=$SN (depth=$SN_DEPTH)"
fi

# ─── 步骤5: 生成实验 SN ───────────────────────
echo ""
echo ">>> 步骤5: 生成实验 SN..."
SN_RESP=$(api_call "POST" "/v1/abtest_step/gen_rand_sn" "{\"app_id\":\"${APP_ID}\"}")
EXPERIMENT_SN=$(echo "$SN_RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('data',''))" 2>/dev/null)

if [ -z "$EXPERIMENT_SN" ]; then
  echo "ERROR: 无法生成实验 SN"
  exit 6
fi
echo "    experiment_sn=$EXPERIMENT_SN"

# ─── 步骤6: 创建功能实验 ───────────────────────
echo ""
echo ">>> 步骤6: 创建功能实验..."

# 构造完整的实验创建请求体（在单个 Python 脚本中完成，避免 JSON null 与 shell 变量冲突）
EXPERIMENT_BODY=$(python3 -c "
import json

# 构造 item_list
groups = '${EXP_GROUPS}'.split(',')
items = []
for i, g in enumerate(groups):
    item = {
        'flow_rate': '100.0' if i == 0 else '0.0',
        'name': '基准组' if i == 0 else f'实验组{i}',
        'config_list': [{'value': g.strip(), 'key': 'algorithm_name', 'value_type': 'string'}],
        'indicators': None
    }
    if i == 0:
        item['is_base'] = True
    items.append(item)

# 构造 expr_fields
field_value = '${FIELD_VALUE}'
values = [v.strip() for v in field_value.split(',')]
expr_fields = [{
    'value': values,
    'expr_template_field_id': ${FIELD_ID},
    'operator': '==',
    'field_name': '${FIELD_TYPE}'
}]

body = {
    'is_salt': True,
    'fill_mode': 'old',
    'user_group_info': {'group_type': 'RANDOM'},
    'is_long_term': False,
    'is_buyer_abtest': True,
    'is_rotate': False,
    'sn': '${EXPERIMENT_SN}',
    'abtest_name': '${NAME}',
    'desc': '${DESC}',
    'scene_sn': '${SN}',
    'expr_fields': expr_fields,
    'ds_app_version': '${VERSION}',
    'ds_scene_sn': '大神整体',
    'ds_recommend_flow': '整体',
    'flow_rate': '100.0',
    'item_list': items,
    'standard_list': 'TEST',
    'online_time': '${ONLINE_TIME}',
    'app_id': '${APP_ID}',
    'indicators': {'standard_list': ['TEST']}
}

field_type = '${FIELD_TYPE}'
if field_type == 'squareId':
    body['ds_square_id'] = field_value

print(json.dumps(body, ensure_ascii=False))
")

EXPERIMENT_RESP=$(api_call "POST" "/v1/abtest/algorithm/new" "$EXPERIMENT_BODY")
if ! check_response "$EXPERIMENT_RESP" "创建功能实验"; then
  exit 7
fi

EXPERIMENT_ID=$(echo "$EXPERIMENT_RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('data',{}).get('id',''))" 2>/dev/null)
echo "    ✅ 实验已创建, experiment_id=$EXPERIMENT_ID"

echo ""
echo "========================================="
echo "✅ 实验创建完成！"
echo "    实验名称: $NAME"
echo "    实验ID:   $EXPERIMENT_ID"
echo "    实验SN:   $EXPERIMENT_SN"
echo "    场景SN:   $SN"
echo "    状态:     草稿"
echo "========================================="

# ─── 自动发布 ───────────────────────
if [ "$AUTO_PUBLISH" = true ]; then
  echo ""
  echo ">>> 自动发布实验..."
  bash "$SKILL_DIR/darwin_publish_experiment.sh" "$EXPERIMENT_ID" "$CONFIG_FILE"
fi
