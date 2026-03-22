#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# POPO 通知脚本 - 上传审查报告并发送 POPO 消息
# 用法: bash notify-popo.sh <report_path> <branch_name> [popo_receiver]
# =============================================================================

REPORT_PATH="${1:-}"
BRANCH_NAME="${2:-}"
POPO_RECEIVER="${3:-1394405}"

# 内置凭证（环境变量优先）
POPO_APP_KEY="${POPO_APP_KEY:-MqsoQxR0lzVRDs0SSim5}"
POPO_APP_SECRET="${POPO_APP_SECRET:-1hkDgKG6MwV0T0vo2mG3FUOqJjCb2Qvzr8Y19niKcVc2e6XMnMN5uUHsC01hyc40}"
FILE_UPLOAD_TOKEN="${FILE_UPLOAD_TOKEN:-ljX5gyDoqDJrMJKqn3JSP9xMUTGZP9vCnVULfj59R68=}"

if [[ -z "$REPORT_PATH" || -z "$BRANCH_NAME" ]]; then
    echo "用法: bash notify-popo.sh <report_path> <branch_name> [popo_receiver]"
    exit 1
fi

if [[ ! -f "$REPORT_PATH" ]]; then
    echo "[ERROR] 报告文件不存在: $REPORT_PATH"
    exit 1
fi

# 上传文件
echo "[INFO] 上传报告: $REPORT_PATH"
upload_response=$(curl -s -X POST \
    -F "file=@${REPORT_PATH}" \
    "https://audiosdk.cc.163.com/n8n?token=${FILE_UPLOAD_TOKEN}")

upload_success=$(echo "$upload_response" | jq -r '.success // false' 2>/dev/null)
if [[ "$upload_success" != "true" ]]; then
    echo "[ERROR] 文件上传失败: $upload_response"
    exit 1
fi

report_filename=$(basename "$REPORT_PATH")
report_url="https://audiosdk.cc.163.com/n8n/${report_filename}"
echo "[INFO] 报告已上传: $report_url"

# 获取 POPO Token
echo "[INFO] 获取 POPO Token..."
token_response=$(curl -s -X POST \
    "https://open.popo.netease.com/open-apis/robots/v1/token" \
    -H "Content-Type: application/json" \
    -d "{\"appKey\":\"${POPO_APP_KEY}\",\"appSecret\":\"${POPO_APP_SECRET}\"}")

token_errcode=$(echo "$token_response" | jq -r '.errcode // empty' 2>/dev/null)
if [[ "$token_errcode" != "0" ]]; then
    echo "[ERROR] 获取 POPO Token 失败: $token_response"
    exit 1
fi

popo_token=$(echo "$token_response" | jq -r '.data.accessToken' 2>/dev/null)
echo "[INFO] POPO Token 获取成功"

# 发送消息
date_str=$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M' 2>/dev/null || date '+%Y-%m-%d %H:%M')
message="[AI 代码审查] ${date_str}\\n分支: ${BRANCH_NAME}\\n审查报告: ${report_url}"

echo "[INFO] 发送 POPO 消息 -> $POPO_RECEIVER"
msg_response=$(curl -s -X POST \
    "https://open.popo.netease.com/open-apis/robots/v1/im/send-msg" \
    -H "Content-Type: application/json" \
    -H "Open-Access-Token: ${popo_token}" \
    -d "{
        \"receiver\": \"${POPO_RECEIVER}\",
        \"msgType\": \"text\",
        \"message\": {
            \"content\": \"${message}\"
        }
    }")

msg_errcode=$(echo "$msg_response" | jq -r '.errcode // empty' 2>/dev/null)
if [[ "$msg_errcode" != "0" ]]; then
    echo "[ERROR] POPO 消息发送失败: $msg_response"
    exit 1
fi

echo "[INFO] POPO 消息发送成功"
echo "[INFO] 报告链接: $report_url"