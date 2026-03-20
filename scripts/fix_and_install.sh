#!/bin/bash

# RANGEN 权限修复和安装脚本
# 在本地终端中运行此脚本

set -e

echo "🔧 RANGEN 环境修复脚本"
echo "======================="
echo ""

# 检查是否在正确的目录
if [[ ! -f "scripts/start_unified_server.py" ]]; then
    echo "❌ 请在RANGEN项目根目录运行此脚本"
    echo "cd /Users/syu/workdata/person/zy/RANGEN-main\\(syu-python\\)"
    exit 1
fi

echo "📍 当前目录: $(pwd)"
echo ""

# 步骤1: 修复homebrew权限
echo "🔑 步骤1: 修复homebrew权限..."
if sudo chown -R "$(whoami)" /opt/homebrew 2>/dev/null; then
    echo "✅ homebrew权限修复成功"
else
    echo "⚠️  homebrew权限修复失败，继续尝试..."
fi
echo ""

# 步骤2: 验证Python环境
echo "🐍 步骤2: 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 未找到"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ $PYTHON_VERSION"

if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 未找到"
    exit 1
fi

PIP_VERSION=$(pip3 --version)
echo "✅ $PIP_VERSION"
echo ""

# 步骤3: 安装依赖包
echo "📦 步骤3: 安装核心依赖包..."
PACKAGES=("fastapi" "uvicorn" "python-dotenv" "langgraph")

for package in "${PACKAGES[@]}"; do
    echo "⬇️  安装 $package..."
    if pip3 install --user "$package"; then
        echo "✅ $package 安装成功"
    else
        echo "❌ $package 安装失败，尝试使用国内镜像..."
        if pip3 install --user -i https://pypi.tuna.tsinghua.edu.cn/simple "$package"; then
            echo "✅ $package 使用国内镜像安装成功"
        else
            echo "❌ $package 安装失败"
            exit 1
        fi
    fi
done
echo ""

# 步骤4: 验证安装
echo "🔍 步骤4: 验证安装..."
python3 -c "
import sys
packages = ['fastapi', 'uvicorn', 'dotenv', 'langgraph']
all_ok = True

print('测试包导入:')
for pkg in packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg}: 导入成功')
    except ImportError as e:
        print(f'❌ {pkg}: 导入失败 - {e}')
        all_ok = False

if all_ok:
    print('')
    print('🎉 所有依赖包安装成功！')
    print('')
    print('🚀 启动服务器:')
    print('cd /Users/syu/workdata/person/zy/RANGEN-main\\(syu-python\\)')
    print('./start_server.sh')
    print('')
    print('🌐 访问地址:')
    print('http://localhost:8080/visualization/')
else:
    print('')
    print('❌ 部分包安装失败')
    exit 1
"
