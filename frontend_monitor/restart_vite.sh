#!/bin/bash

# 快速重启 Vite 服务脚本
# 用于在修改配置后重启前端服务

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔄 重启 Vite 服务..."

# 停止现有的 Vite 进程
VITE_PIDS=$(ps aux | grep -E "vite|node.*dev" | grep -v grep | awk '{print $2}')
if [ -n "$VITE_PIDS" ]; then
    echo "🛑 停止现有的 Vite 进程..."
    echo "$VITE_PIDS" | xargs kill -9 2>/dev/null || true
    sleep 1
    echo "✅ 已停止 Vite 进程"
fi

# 检查 .env 文件
if [ -f ".env" ]; then
    echo "📄 当前 .env 配置:"
    cat .env
else
    echo "⚠️  未找到 .env 文件，将使用默认配置（端口 5001）"
fi

# 检查后端端口
BACKEND_PORT=5001
if curl -s http://localhost:5001/api/logs > /dev/null 2>&1; then
    BACKEND_PORT=5001
    echo "✅ 检测到后端运行在端口 5001"
elif curl -s http://localhost:5000/api/logs > /dev/null 2>&1; then
    RESPONSE=$(curl -s -I http://localhost:5000/api/logs 2>&1 | head -1)
    if echo "$RESPONSE" | grep -q "200 OK"; then
        BACKEND_PORT=5000
        echo "✅ 检测到后端运行在端口 5000"
    fi
else
    echo "⚠️  无法检测后端端口，使用默认端口 5001"
fi

# 更新 .env 文件
export VITE_API_URL="http://localhost:${BACKEND_PORT}"
echo "VITE_API_URL=${VITE_API_URL}" > .env
echo "✅ 已更新 .env 文件: ${VITE_API_URL}"

# 启动 Vite
echo ""
echo "🚀 启动 Vite 服务..."
echo "📱 前端地址: http://localhost:3000"
echo "🔗 代理目标: ${VITE_API_URL}"
echo ""

VITE_API_URL="${VITE_API_URL}" npm run dev

