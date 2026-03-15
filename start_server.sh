#!/bin/bash

# RANGEN 统一服务器启动脚本
# 用于在本地环境中启动完整的可视化服务器

echo "🚀 启动 RANGEN 统一服务器..."
echo "=================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未找到，请先安装Python3"
    exit 1
fi

# 检查是否在正确的目录
if [ ! -f "scripts/start_unified_server.py" ]; then
    echo "❌ 请在RANGEN项目根目录下运行此脚本"
    echo "   正确的路径应该是: /Users/syu/workdata/person/zy/RANGEN-main(syu-python)/"
    exit 1
fi

# 检查端口是否被占用
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  端口8080已被占用，尝试使用端口8081..."
    PORT=8081
else
    PORT=8080
fi

echo "📍 项目目录: $(pwd)"
echo "🔌 使用端口: $PORT"
echo ""

# 启动服务器
echo "🌐 正在启动服务器..."

# 检查并激活虚拟环境
if [ -d ".venv" ]; then
    echo "🔄 激活虚拟环境..."
    source .venv/bin/activate
    PYTHON_CMD="python3"
else
    echo "⚠️  虚拟环境不存在，使用系统Python"
    PYTHON_CMD="/opt/homebrew/bin/python3"
fi

$PYTHON_CMD scripts/start_unified_server.py --port $PORT

echo ""
echo "✅ 服务器已停止"
