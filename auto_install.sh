#!/bin/bash

# RANGEN V2 自动安装脚本
# 支持完整的依赖管理和可选功能安装

set -e  # 遇到错误立即退出

echo "🚀 RANGEN V2 自动安装脚本"
echo "=========================="
echo ""
echo "📋 安装选项:"
echo "  默认: 安装核心依赖 (必需)"
echo "  可选: -k 知识管理系统 (KMS)"
echo "       -r RPA系统"
echo "       -e 增强功能 (OpenTelemetry, ML等)"
echo "       -d 开发工具 (测试、代码质量)"
echo "       -a 安装所有功能"
echo "       -v 创建虚拟环境"
echo ""
echo "示例:"
echo "  $0           # 仅安装核心依赖"
echo "  $0 -k -e     # 安装核心 + KMS + 增强功能"
echo "  $0 -a        # 安装所有功能"
echo "  $0 -v        # 创建虚拟环境并安装核心依赖"
echo ""

# 默认参数
INSTALL_CORE=true
INSTALL_KMS=false
INSTALL_RPA=false
INSTALL_ENHANCED=false
INSTALL_DEV=false
CREATE_VENV=false
USE_MIRROR=true
MIRROR_URL="https://pypi.tuna.tsinghua.edu.cn/simple"

# 解析命令行参数
while getopts "kredavmh" opt; do
    case $opt in
        k) INSTALL_KMS=true ;;
        r) INSTALL_RPA=true ;;
        e) INSTALL_ENHANCED=true ;;
        d) INSTALL_DEV=true ;;
        a) 
            INSTALL_KMS=true
            INSTALL_RPA=true
            INSTALL_ENHANCED=true
            INSTALL_DEV=true
            ;;
        v) CREATE_VENV=true ;;
        m) USE_MIRROR=false ;;
        h)
            echo "使用方法: $0 [选项]"
            echo "选项:"
            echo "  -k  安装知识管理系统 (KMS)"
            echo "  -r  安装RPA系统"
            echo "  -e  安装增强功能"
            echo "  -d  安装开发工具"
            echo "  -a  安装所有功能"
            echo "  -v  创建虚拟环境"
            echo "  -m  不使用镜像源 (默认使用清华镜像)"
            echo "  -h  显示此帮助信息"
            exit 0
            ;;
        \?)
            echo "❌ 无效选项: -$OPTARG" >&2
            exit 1
            ;;
    esac
done

echo "🔍 环境检查..."
echo "=========================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 未找到，请先安装Python 3.9+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_PATH=$(which python3)
echo "✅ Python $PYTHON_VERSION 路径: $PYTHON_PATH"

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 未找到，尝试安装pip..."
    python3 -m ensurepip --upgrade
    if ! command -v pip3 &> /dev/null; then
        echo "❌ 无法安装pip，请手动安装pip"
        exit 1
    fi
fi

PIP_PATH=$(which pip3)
echo "✅ pip 路径: $PIP_PATH"
pip3 --version
echo ""

# 创建虚拟环境（如果指定）
if [ "$CREATE_VENV" = true ]; then
    echo "🏠 创建虚拟环境..."
    echo "=========================="
    
    if [ -d ".venv" ]; then
        echo "⚠️  虚拟环境已存在 (.venv)"
        read -p "是否重新创建？[y/N]: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf .venv
            python3 -m venv .venv
            echo "✅ 虚拟环境已重新创建"
        else
            echo "✅ 使用现有虚拟环境"
        fi
    else
        python3 -m venv .venv
        echo "✅ 虚拟环境已创建"
    fi
    
    # 激活虚拟环境
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        echo "✅ 虚拟环境已激活"
        PYTHON_PATH=$(which python)
        PIP_PATH=$(which pip)
        echo "更新Python路径: $PYTHON_PATH"
        echo "更新pip路径: $PIP_PATH"
    else
        echo "❌ 无法激活虚拟环境"
        exit 1
    fi
    echo ""
fi

# 检查pyproject.toml是否存在
if [ ! -f "pyproject.toml" ]; then
    echo "❌ pyproject.toml 未找到"
    echo "请确保在RANGEN项目根目录下运行此脚本"
    exit 1
fi

echo "📦 依赖安装..."
echo "=========================="

# 构建pip安装命令
PIP_CMD="pip3 install"
if [ "$USE_MIRROR" = true ]; then
    PIP_CMD="$PIP_CMD -i $MIRROR_URL"
fi

# 安装核心依赖
if [ "$INSTALL_CORE" = true ]; then
    echo "🔧 安装核心依赖..."
    if $PIP_CMD .; then
        echo "✅ 核心依赖安装成功"
    else
        echo "❌ 核心依赖安装失败"
        exit 1
    fi
    echo ""
fi

# 安装可选依赖组
install_optional_deps() {
    local group_name=$1
    local display_name=$2
    
    echo "🔧 安装 $display_name..."
    if $PIP_CMD ".[$group_name]"; then
        echo "✅ $display_name 安装成功"
    else
        echo "⚠️  $display_name 安装失败，跳过..."
    fi
    echo ""
}

if [ "$INSTALL_KMS" = true ]; then
    install_optional_deps "kms" "知识管理系统 (KMS)"
fi

if [ "$INSTALL_RPA" = true ]; then
    install_optional_deps "rpa" "RPA系统"
fi

if [ "$INSTALL_ENHANCED" = true ]; then
    install_optional_deps "enhanced" "增强功能"
fi

if [ "$INSTALL_DEV" = true ]; then
    install_optional_deps "dev" "开发工具"
fi

echo "🔍 验证安装..."
echo "=========================="

# 验证核心包
echo "检查核心包..."
python3 -c "
import sys
import importlib.util

core_packages = [
    'fastapi',
    'uvicorn',
    'pydantic',
    'langgraph',
    'numpy',
    'pandas',
]

all_ok = True
for pkg in core_packages:
    try:
        spec = importlib.util.find_spec(pkg)
        if spec is not None:
            print(f'✅ {pkg}: 导入成功')
        else:
            print(f'❌ {pkg}: 未找到')
            all_ok = False
    except Exception as e:
        print(f'❌ {pkg}: 导入失败 - {e}')
        all_ok = False

if all_ok:
    print('✅ 所有核心包验证成功')
else:
    print('❌ 部分核心包验证失败')
    sys.exit(1)
"

# 验证可选包（如果安装了）
echo ""
echo "检查可选包..."
python3 -c "
import sys
import importlib.util

optional_packages = []
if $INSTALL_KMS:
    optional_packages.extend(['faiss', 'sentence_transformers', 'sqlalchemy'])
if $INSTALL_ENHANCED:
    optional_packages.extend(['opentelemetry', 'scikit_learn'])
if $INSTALL_DEV:
    optional_packages.extend(['pytest', 'black', 'mypy'])

for pkg in optional_packages:
    try:
        spec = importlib.util.find_spec(pkg)
        if spec is not None:
            print(f'✅ {pkg}: 导入成功')
        else:
            print(f'⚠️  {pkg}: 未找到 (可能未安装或安装失败)')
    except Exception as e:
        print(f'⚠️  {pkg}: 检查失败 - {e}')
"

echo ""
echo "🎉 安装完成！"
echo "=========================="
echo ""
echo "📋 安装摘要:"
echo "  - 核心依赖: ✅ 已安装"
if [ "$INSTALL_KMS" = true ]; then echo "  - 知识管理系统 (KMS): ✅ 已安装"; fi
if [ "$INSTALL_RPA" = true ]; then echo "  - RPA系统: ✅ 已安装"; fi
if [ "$INSTALL_ENHANCED" = true ]; then echo "  - 增强功能: ✅ 已安装"; fi
if [ "$INSTALL_DEV" = true ]; then echo "  - 开发工具: ✅ 已安装"; fi
if [ "$CREATE_VENV" = true ]; then echo "  - 虚拟环境: ✅ 已创建 (.venv)"; fi
echo ""

echo "🚀 下一步:"
echo "  1. 配置环境变量:"
echo "     cp .env.example .env"
echo "     # 编辑 .env 文件设置您的 API 密钥"
echo ""
echo "  2. 启动系统:"
if [ "$CREATE_VENV" = true ]; then
    echo "     source .venv/bin/activate"
fi
echo "     # 启动 API 服务器: python src/api/server.py"
echo "     # 启动聊天界面: streamlit run src/ui/app.py"
echo "     # 启动统一服务器: ./start_server.sh"
echo ""
echo "  3. 运行测试:"
if [ "$INSTALL_DEV" = true ]; then
    echo "     python -m pytest tests/ -v"
else
    echo "     # 需要先安装开发工具: $0 -d"
fi
echo ""
echo "📚 更多信息请查看:"
echo "  - README.md: 项目概述"
echo "  - docs/usage/quick_start.md: 快速开始指南"
echo "  - AGENTS.md: 架构和开发指南"
echo ""

if [ "$CREATE_VENV" = true ]; then
    echo "💡 提示: 虚拟环境已激活，要退出虚拟环境请运行: deactivate"
fi

echo "✨ 祝您使用愉快！"
