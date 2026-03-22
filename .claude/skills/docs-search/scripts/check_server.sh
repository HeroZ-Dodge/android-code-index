#!/bin/bash
# 检查文档服务器是否运行

PORT=${1:-3000}

if lsof -ti :$PORT > /dev/null 2>&1; then
    echo "running"
    exit 0
else
    echo "stopped"
    exit 1
fi
