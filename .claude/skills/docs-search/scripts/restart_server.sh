#!/bin/bash
# 重启文档服务器（同步最新文件并重启）

DOCS_SITE_DIR="$(dirname "$0")/../../../../docs-site"
PORT=${1:-3000}

cd "$DOCS_SITE_DIR" || exit 1

echo "[restart] Stopping existing server..."
pkill -f "vitepress" 2>/dev/null
pkill -f "watch.mjs" 2>/dev/null
lsof -ti :$PORT | xargs kill -9 2>/dev/null
sleep 1

echo "[restart] Syncing files from source directories..."
npm run sync

echo "[restart] Clearing cache..."
rm -rf .vitepress/cache

echo "[restart] Starting server on port $PORT..."
npm run dev -- --port $PORT &

sleep 5

if lsof -ti :$PORT > /dev/null 2>&1; then
    echo "[restart] Server restarted successfully!"
    echo "[restart] Access: http://localhost:$PORT/docs-site/"
    exit 0
else
    echo "[restart] Failed to restart server"
    exit 1
fi
