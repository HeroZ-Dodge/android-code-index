#!/usr/bin/env bash
# darwin_login_password.sh
# 通过账号+密码登录达尔文AB实验系统（网易SSO）
# 用法: ./darwin_login_password.sh [config.json路径]
#
# config.json 中需要有:
#   corp_id   - 企业账号（如 linzheng）
#   corp_pw   - OPHASH 密码哈希（如 OPHASH_786b17cbc88aa4c5b632f15b8b8325e0）
#
# 流程:
#   1. GET SSO 授权页 → 获取 csrftoken
#   2. POST 提交账号密码 → 302 拿到 code
#   3. GET 回调地址带 code → 302 拿到 go_session_id
#   4. 更新 config.json
#   5. 验证新 session

set -euo pipefail

CONFIG_FILE="${1:-$HOME/.config/darwin-ab-experiment/config.json}"

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

# 读取账号密码
CORP_ID=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('corp_id',''))")
CORP_PW=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('corp_pw',''))")

if [ -z "$CORP_ID" ] || [ -z "$CORP_PW" ]; then
  echo "ERROR: config.json 中缺少 corp_id 或 corp_pw"
  echo "请在 config.json 中添加:"
  echo '  "corp_id": "你的企业账号",'
  echo '  "corp_pw": "OPHASH_你的密码哈希"'
  exit 1
fi

CLIENT_ID="d4376efa03f311eca074246e965dfd84"
REDIRECT_URI="https%3A%2F%2Fdashen-admin.abtest-dev.cbg.163.com%2Fv1%2Fadmin_login%2Freturn_from_openid_server"
SCOPE="email+fullname+openid"
AUTH_URL="https://login.netease.com/connect/authorize?client_id=${CLIENT_ID}&redirect_uri=${REDIRECT_URI}&response_type=code&scope=${SCOPE}"

COOKIE_JAR="/tmp/darwin_login_cookies_$$.txt"
trap "rm -f $COOKIE_JAR" EXIT

echo ">>> 步骤1: 获取SSO登录页面 & csrftoken..."
# GET 授权页面，获取 csrftoken cookie
STEP1_HEADERS=$(curl -s -D - -o /dev/null \
  -c "$COOKIE_JAR" \
  "$AUTH_URL")

# 从 cookie jar 或 Set-Cookie header 中提取 csrftoken
CSRF_TOKEN=$(grep 'csrftoken' "$COOKIE_JAR" 2>/dev/null | awk '{print $NF}' || true)
if [ -z "$CSRF_TOKEN" ]; then
  # 尝试从 header 中提取
  CSRF_TOKEN=$(echo "$STEP1_HEADERS" | grep -i 'set-cookie.*csrftoken=' | sed 's/.*csrftoken=\([^;]*\).*/\1/' | head -1)
fi

if [ -z "$CSRF_TOKEN" ]; then
  echo "ERROR: 无法获取 csrftoken"
  echo "$STEP1_HEADERS"
  exit 2
fi
echo "    csrftoken: ${CSRF_TOKEN:0:16}..."

echo ">>> 步骤2: 提交账号密码登录..."
# POST 登录表单
STEP2_HEADERS=$(curl -s -D - -o /dev/null \
  -b "$COOKIE_JAR" -c "$COOKIE_JAR" \
  -X POST "$AUTH_URL" \
  -H 'content-type: application/x-www-form-urlencoded' \
  -H 'referer: https://login.netease.com/connect/authorize' \
  -d "csrfmiddlewaretoken=${CSRF_TOKEN}&authm=corp&client_id=${CLIENT_ID}&redirect_uri=${REDIRECT_URI}&response_type=code&scope=${SCOPE}&state=&corpid=${CORP_ID}&corppw=${CORP_PW}&remember=on&privacy=on&allow=submit")

# 提取重定向地址中的 code
REDIRECT_URL=$(echo "$STEP2_HEADERS" | grep -i '^location:' | tr -d '\r')
CODE=$(echo "$REDIRECT_URL" | grep -o 'code=[a-f0-9]*' | cut -d= -f2)

if [ -z "$CODE" ]; then
  echo "ERROR: 登录失败，未能获取授权码 (code)"
  echo "可能原因: 账号密码错误或密码哈希已过期"
  echo "响应头:"
  echo "$STEP2_HEADERS"
  exit 3
fi
echo "    授权码: ${CODE:0:8}..."

echo ">>> 步骤3: 用授权码换取 go_session_id..."
CALLBACK_URL="https://dashen-admin.abtest-dev.cbg.163.com/v1/admin_login/return_from_openid_server?state=&code=${CODE}"
STEP3_HEADERS=$(curl -s -D - -o /dev/null "$CALLBACK_URL")

# 提取新的 go_session_id
NEW_SESSION=$(echo "$STEP3_HEADERS" | grep -i 'set-cookie.*go_session_id=' | sed 's/.*go_session_id=\([^;]*\).*/\1/' | head -1)
if [ -z "$NEW_SESSION" ]; then
  echo "ERROR: 未能获取新的 go_session_id"
  echo "$STEP3_HEADERS"
  exit 4
fi
echo "    新 session: ${NEW_SESSION:0:20}..."

# 提取过期时间
EXPIRES=$(echo "$STEP3_HEADERS" | grep -i 'set-cookie.*go_session_id=' | grep -o 'Expires=[^;]*' | cut -d= -f2- | head -1)
echo "    过期时间: $EXPIRES"

# 同时提取 SSO 的新 cookie（如果有的话），用于后续 SSO session 刷新
NEW_SSO_CSRF=$(grep 'csrftoken' "$COOKIE_JAR" 2>/dev/null | awk '{print $NF}' || true)
NEW_SSO_SESSION=$(grep 'sessionid' "$COOKIE_JAR" 2>/dev/null | awk '{print $NF}' || true)

echo ">>> 步骤4: 更新配置文件..."
python3 -c "
import json

with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)

config['go_session_id'] = '$NEW_SESSION'

# 如果登录过程中拿到了新的 SSO cookie，也更新
new_csrf = '$NEW_SSO_CSRF'
new_session = '$NEW_SSO_SESSION'
if new_csrf:
    config['sso_csrftoken'] = new_csrf
if new_session:
    config['sso_sessionid'] = new_session

with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=2)
    f.write('\n')
print('配置文件已更新')
"

echo ">>> 步骤5: 验证新 session..."
VERIFY=$(curl -s -X POST 'https://dashen-admin.abtest-dev.cbg.163.com/v1/admin_account/my' \
  -H 'content-type: application/json;charset=UTF-8' \
  -H "cookie: go_session_id=${NEW_SESSION}" \
  -d '{"app_id":"DASHEN"}')

EMAIL=$(echo "$VERIFY" | python3 -c "import json,sys; print(json.load(sys.stdin).get('data',{}).get('email','FAILED'))" 2>/dev/null || echo "FAILED")

if [ "$EMAIL" = "FAILED" ]; then
  echo "ERROR: 新 session 验证失败"
  echo "$VERIFY"
  exit 5
fi

echo "✅ 登录成功！用户: $EMAIL"
