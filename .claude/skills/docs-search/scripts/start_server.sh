#!/bin/bash
# 启动文档服务器（带自动同步）

DOCS_SITE_DIR="$(dirname "$0")/../../../../docs-site"
PORT=${1:-3000}

cd "$DOCS_SITE_DIR" || exit 1

# 先杀掉已有进程
pkill -f "vitepress" 2>/dev/null
lsof -ti :$PORT | xargs kill -9 2>/dev/null
sleep 1

# 清理缓存并启动
rm -rf .vitepress/cache
npm run dev:watch -- --port $PORT &

echo "Server starting on port $PORT..."
sleep 3

if lsof -ti :$PORT > /dev/null 2>&1; then
    echo "Server started successfully at http://localhost:$PORT/docs-site/"
    exit 0
else
    echo "Failed to start server"
    exit 1
fi
