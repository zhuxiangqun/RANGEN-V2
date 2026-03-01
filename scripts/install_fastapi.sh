#!/bin/bash

# FastAPI 依赖安装脚本
# 用于安装浏览器可视化服务器所需的依赖

echo "🚀 安装 FastAPI 和相关依赖..."
echo "=================================="

# 检查 Python 环境
python3 --version || {
    echo "❌ Python3 未找到，请确保 Python3 已安装"
    exit 1
}

# 检查 pip
python3 -m pip --version || {
    echo "❌ pip 未找到，请确保 pip 已安装"
    exit 1
}

echo "📦 安装 FastAPI 核心依赖..."
python3 -m pip install "fastapi>=0.104.0" "uvicorn[standard]>=0.24.0" "websockets>=12.0"

if [ $? -eq 0 ]; then
    echo "✅ FastAPI 依赖安装成功！"
    echo ""
    echo "🔍 验证安装..."
    python3 -c "import fastapi; print(f'FastAPI version: {fastapi.__version__}')" || {
        echo "❌ FastAPI 导入失败"
        exit 1
    }

    python3 -c "import uvicorn; print('Uvicorn available')" || {
        echo "❌ Uvicorn 导入失败"
        exit 1
    }

    echo ""
    echo "🎉 所有依赖安装完成！"
    echo ""
    echo "🚀 现在可以启动统一服务器："
    echo "python scripts/start_unified_server.py --port 8080"
    echo ""
    echo "🌐 访问地址："
    echo "http://localhost:8080/          # 主页"
    echo "http://localhost:8080/config    # 配置管理"
    echo "http://localhost:8080/api/config # API端点"

else
    echo "❌ 安装失败，请检查错误信息"
    exit 1
fi
