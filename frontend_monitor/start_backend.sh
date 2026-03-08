#!/bin/bash
# 启动后端服务的独立脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

echo "🚀 启动后端服务..."

# 🚀 修复：使用项目根目录的.venv，而不是backend/venv
if [ ! -d "${VENV_DIR}" ]; then
    echo "❌ 错误: 未找到项目根目录的.venv虚拟环境"
    echo "   请先创建并安装依赖: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 激活项目根目录的.venv
echo "🔧 使用项目根目录的.venv虚拟环境..."
source "${VENV_DIR}/bin/activate"

# 检查后端依赖是否已安装
if ! python -c "import flask" 2>/dev/null; then
    echo "📦 安装后端依赖到.venv..."
    pip install -r "${SCRIPT_DIR}/backend/requirements.txt"
fi

# 启动后端
cd "${SCRIPT_DIR}/backend"
echo "🔧 启动Flask后端..."
python app.py

