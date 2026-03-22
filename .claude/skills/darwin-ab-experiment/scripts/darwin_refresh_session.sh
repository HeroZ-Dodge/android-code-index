#!/usr/bin/env bash
# darwin_refresh_session.sh
# 用网易SSO的session自动刷新达尔文的go_session_id
# 用法: ./darwin_refresh_session.sh [config.json路径]

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

SSO_CSRF=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['sso_csrftoken'])")
SSO_SESSION=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['sso_sessionid'])")

if [ -z "$SSO_CSRF" ] || [ -z "$SSO_SESSION" ]; then
  echo "ERROR: config.json 中缺少 sso_csrftoken 或 sso_sessionid"
  exit 1
fi

echo ">>> 步骤1: 获取SSO授权页面..."
AUTH_PAGE=$(curl -s \
  'https://login.netease.com/connect/authorize?client_id=d4376efa03f311eca074246e965dfd84&redirect_uri=https%3A%2F%2Fdashen-admin.abtest-dev.cbg.163.com%2Fv1%2Fadmin_login%2Freturn_from_openid_server&response_type=code&scope=email+fullname+openid' \
  -H "cookie: csrftoken=${SSO_CSRF}; sessionid=${SSO_SESSION}" \
  -D /tmp/darwin_sso_step1_headers.txt)

# 检查是否有新的 csrftoken
NEW_CSRF=$(grep -i 'set-cookie.*csrftoken=' /tmp/darwin_sso_step1_headers.txt 2>/dev/null | sed 's/.*csrftoken=\([^;]*\).*/\1/' || true)
if [ -n "$NEW_CSRF" ]; then
  SSO_CSRF="$NEW_CSRF"
fi

# 检查是否是授权确认页（包含"登录并授权"）
if ! echo "$AUTH_PAGE" | grep -q '登录并授权'; then
  echo "ERROR: SSO session已过期，需要重新在浏览器登录 login.netease.com"
  echo "登录后更新 config.json 中的 sso_csrftoken 和 sso_sessionid"
  exit 2
fi

echo ">>> 步骤2: 提交授权表单..."
REDIRECT_HEADERS=$(curl -s -D - -o /dev/null \
  -X POST 'https://login.netease.com/connect/authorize' \
  -H 'content-type: application/x-www-form-urlencoded' \
  -H "cookie: csrftoken=${SSO_CSRF}; sessionid=${SSO_SESSION}" \
  -H 'referer: https://login.netease.com/connect/authorize' \
  -d "csrfmiddlewaretoken=${SSO_CSRF}&client_id=d4376efa03f311eca074246e965dfd84&redirect_uri=https%3A%2F%2Fdashen-admin.abtest-dev.cbg.163.com%2Fv1%2Fadmin_login%2Freturn_from_openid_server&response_type=code&scope=email+fullname+openid&state=&allow=%E7%99%BB%E5%BD%95%E5%B9%B6%E6%8E%88%E6%9D%83")

# 提取 code
CODE=$(echo "$REDIRECT_HEADERS" | grep -i 'location:' | grep -o 'code=[a-f0-9]*' | cut -d= -f2)
if [ -z "$CODE" ]; then
  echo "ERROR: 未能获取授权码 (code)"
  echo "$REDIRECT_HEADERS"
  exit 3
fi
echo "    授权码: ${CODE:0:8}..."

echo ">>> 步骤3: 用授权码换取 go_session_id..."
CALLBACK_HEADERS=$(curl -s -D - -o /dev/null \
  "https://dashen-admin.abtest-dev.cbg.163.com/v1/admin_login/return_from_openid_server?state=&code=${CODE}")

# 提取新的 go_session_id
NEW_SESSION=$(echo "$CALLBACK_HEADERS" | grep -i 'set-cookie.*go_session_id=' | sed 's/.*go_session_id=\([^;]*\).*/\1/')
if [ -z "$NEW_SESSION" ]; then
  echo "ERROR: 未能获取新的 go_session_id"
  echo "$CALLBACK_HEADERS"
  exit 4
fi

echo "    新 session: ${NEW_SESSION:0:20}..."

# 提取过期时间
EXPIRES=$(echo "$CALLBACK_HEADERS" | grep -i 'set-cookie.*go_session_id=' | grep -o 'Expires=[^;]*' | cut -d= -f2-)
echo "    过期时间: $EXPIRES"

echo ">>> 步骤4: 更新配置文件..."
python3 -c "
import json
with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)
config['go_session_id'] = '$NEW_SESSION'
config['sso_csrftoken'] = '$SSO_CSRF'
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
  exit 5
fi

echo "✅ 刷新成功！登录用户: $EMAIL"
