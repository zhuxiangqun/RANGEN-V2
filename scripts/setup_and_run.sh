#!/bin/bash

# RANGEN 一键安装和启动脚本

set -e

echo "🚀 RANGEN 一键安装和启动脚本"
echo "============================"
echo ""

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "📍 项目目录: $PROJECT_DIR"
echo ""

# 检查Python
echo "🐍 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 未找到"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ $PYTHON_VERSION"
echo ""

# 检查/创建虚拟环境
if [[ -d ".venv" ]]; then
    echo "✅ 虚拟环境已存在"
else
    echo "🔧 创建虚拟环境..."
    python3 -m venv .venv
    echo "✅ 虚拟环境创建完成"
fi
echo ""

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source .venv/bin/activate
echo "✅ 虚拟环境已激活"
echo ""

# 升级pip
echo "⬆️  升级pip..."
pip install --upgrade pip
echo "✅ pip升级完成"
echo ""

# 安装依赖
echo "📦 安装依赖包..."
pip install -r requirements.txt
echo "✅ 依赖包安装完成"
echo ""

# 验证安装
echo "🔍 验证安装..."

# 创建临时Python验证脚本
cat > verify_install.py << 'EOF'
# 检查正确的包导入名
deps = [
    ('fastapi', 'fastapi'),
    ('uvicorn', 'uvicorn'),
    ('python-dotenv', 'dotenv'),
    ('langgraph', 'langgraph')
]

all_ok = True

print('检查核心依赖:')
for pkg_name, import_name in deps:
    try:
        __import__(import_name)
        print(f'✅ {pkg_name}: 已安装')
    except ImportError as e:
        print(f'❌ {pkg_name}: 未安装 - {e}')
        all_ok = False

if all_ok:
    print('')
    print('🎉 所有依赖安装成功！')
else:
    print('')
    print('❌ 部分依赖安装失败')
    exit(1)
EOF

python3 verify_install.py
verification_result=$?

# 清理临时文件
rm verify_install.py

if [[ $verification_result -ne 0 ]]; then
    echo "❌ 依赖验证失败"
    exit 1
fi

echo ""

# 启动服务器
echo "🌐 启动RANGEN服务器..."
echo "按 Ctrl+C 可以停止服务器"
echo ""

./start_server.sh
