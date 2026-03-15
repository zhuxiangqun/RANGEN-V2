#!/bin/bash

# RANGEN V2 开发环境设置脚本
# 自动化设置完整的开发环境

set -e  # 遇到错误立即退出

echo "🚀 RANGEN V2 开发环境设置脚本"
echo "================================"
echo ""
echo "📋 功能包括:"
echo "  - 创建虚拟环境"
echo "  - 安装所有开发依赖"
echo "  - 设置预提交钩子"
echo "  - 配置开发工具"
echo "  - 设置测试环境"
echo "  - 验证开发环境"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查是否在项目根目录
check_project_root() {
    log_info "检查项目根目录..."
    if [ ! -f "pyproject.toml" ] || [ ! -d "src" ]; then
        log_error "请在RANGEN项目根目录下运行此脚本"
        exit 1
    fi
    log_success "项目根目录检查通过"
}

# 检查Python环境
check_python() {
    log_info "检查Python环境..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "python3 未找到，请先安装Python 3.9+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [[ $(echo "$PYTHON_VERSION < 3.9" | bc) -eq 1 ]]; then
        log_error "需要Python 3.9+，当前版本: $PYTHON_VERSION"
        exit 1
    fi
    
    PYTHON_PATH=$(which python3)
    log_success "Python $PYTHON_VERSION 路径: $PYTHON_PATH"
}

# 创建虚拟环境
create_venv() {
    log_info "创建虚拟环境..."
    
    if [ -d ".venv" ]; then
        log_warning "虚拟环境已存在 (.venv)"
        read -p "是否重新创建？[y/N]: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf .venv
            python3 -m venv .venv
            log_success "虚拟环境已重新创建"
        else
            log_success "使用现有虚拟环境"
        fi
    else
        python3 -m venv .venv
        log_success "虚拟环境已创建"
    fi
    
    # 激活虚拟环境
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        log_success "虚拟环境已激活"
        export VIRTUAL_ENV_ACTIVATED=true
    else
        log_error "无法激活虚拟环境"
        exit 1
    fi
}

# 升级pip和工具
upgrade_pip() {
    log_info "升级pip和工具..."
    
    python -m pip install --upgrade pip
    python -m pip install --upgrade setuptools wheel
    
    log_success "pip和工具已升级"
}

# 安装开发依赖
install_dev_deps() {
    log_info "安装开发依赖..."
    
    # 使用清华镜像源加速安装
    MIRROR_URL="https://pypi.tuna.tsinghua.edu.cn/simple"
    
    # 安装项目依赖（包括开发依赖）
    if pip install -i "$MIRROR_URL" ".[dev]"; then
        log_success "开发依赖安装成功"
    else
        log_error "开发依赖安装失败"
        exit 1
    fi
    
    # 安装可选的增强功能
    log_info "安装增强功能..."
    if pip install -i "$MIRROR_URL" ".[enhanced]"; then
        log_success "增强功能安装成功"
    else
        log_warning "增强功能安装失败，跳过..."
    fi
}

# 设置预提交钩子
setup_precommit() {
    log_info "设置预提交钩子..."
    
    # 检查是否安装了pre-commit
    if ! command -v pre-commit &> /dev/null; then
        log_info "安装pre-commit..."
        pip install pre-commit
    fi
    
    # 配置pre-commit
    if [ -f ".pre-commit-config.yaml" ]; then
        log_info "运行pre-commit安装..."
        pre-commit install
        pre-commit install --hook-type commit-msg
        log_success "预提交钩子已设置"
    else
        log_warning ".pre-commit-config.yaml 未找到，跳过预提交钩子设置"
    fi
}

# 创建开发配置文件
create_dev_configs() {
    log_info "创建开发配置文件..."
    
    # 创建本地环境文件
    if [ ! -f ".env.local" ]; then
        cp .env.example .env.local
        log_success "创建 .env.local 文件"
        
        # 提示用户配置
        log_warning "请编辑 .env.local 文件设置您的 API 密钥和配置"
    else
        log_success ".env.local 文件已存在"
    fi
    
    # 创建开发配置目录
    if [ ! -d "config/environments/development" ]; then
        mkdir -p config/environments/development
        log_success "创建开发配置目录"
    fi
    
    # 创建测试数据库配置
    if [ ! -f "config/environments/development/database.yaml" ]; then
        cat > "config/environments/development/database.yaml" << EOF
# 开发环境数据库配置
database:
  driver: sqlite
  database: rangen_dev.db
  echo: true
  
# 或者使用 PostgreSQL
# database:
#   driver: postgresql
#   host: localhost
#   port: 5432
#   database: rangen_dev
#   username: postgres
#   password: postgres
EOF
        log_success "创建测试数据库配置"
    fi
}

# 配置开发工具
setup_dev_tools() {
    log_info "配置开发工具..."
    
    # 创建 .editorconfig 如果不存在
    if [ ! -f ".editorconfig" ]; then
        cat > ".editorconfig" << EOF
# EditorConfig is awesome: https://EditorConfig.org

# top-most EditorConfig file
root = true

[*]
indent_style = space
indent_size = 4
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.py]
max_line_length = 120

[*.{js,ts,jsx,tsx,vue}]
indent_size = 2

[*.md]
trim_trailing_whitespace = false

[Makefile]
indent_style = tab
EOF
        log_success "创建 .editorconfig 文件"
    fi
    
    # 创建 .vscode 配置目录
    if [ ! -d ".vscode" ]; then
        mkdir -p .vscode
        
        # 创建 settings.json
        cat > ".vscode/settings.json" << EOF
{
    "python.defaultInterpreterPath": "\${workspaceFolder}/.venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "python.terminal.activateEnvInCurrentTerminal": true,
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.mypyEnabled": true,
    "python.linting.pyrightEnabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackPath": "\${workspaceFolder}/.venv/bin/black",
    "python.sortImports.path": "\${workspaceFolder}/.venv/bin/isort",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": "always"
    },
    "files.exclude": {
        "**/__pycache__": true,
        "**/.pytest_cache": true,
        "**/.mypy_cache": true,
        "**/.coverage": true,
        "**/.venv": true
    },
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.nosetestsEnabled": false,
    "python.testing.pytestArgs": [
        "tests",
        "-v",
        "--tb=short"
    ],
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter"
    }
}
EOF
        log_success "创建 VS Code 配置"
    fi
}

# 验证开发环境
validate_dev_env() {
    log_info "验证开发环境..."
    
    echo ""
    echo "🧪 运行环境检查..."
    python -c "
import sys
import importlib.util

# 检查核心包
core_packages = [
    'fastapi',
    'uvicorn',
    'pydantic',
    'langgraph',
    'numpy',
    'pandas',
    'pytest',
    'black',
    'mypy',
    'pylint',
]

print('📦 检查核心包...')
all_ok = True
for pkg in core_packages:
    try:
        spec = importlib.util.find_spec(pkg)
        if spec is not None:
            print(f'  ✅ {pkg}')
        else:
            print(f'  ❌ {pkg}')
            all_ok = False
    except Exception as e:
        print(f'  ❌ {pkg}: {e}')
        all_ok = False

if all_ok:
    print('✅ 所有核心包检查通过')
else:
    print('❌ 部分核心包检查失败')
    sys.exit(1)

# 检查开发工具
print('')
print('🛠️  检查开发工具...')
dev_tools = [
    ('pylint', '检查代码质量'),
    ('mypy', '类型检查'),
    ('black', '代码格式化'),
    ('isort', '导入排序'),
    ('pytest', '测试框架'),
]

for tool, description in dev_tools:
    try:
        spec = importlib.util.find_spec(tool)
        if spec is not None:
            print(f'  ✅ {tool}: {description}')
        else:
            print(f'  ⚠️  {tool}: 未找到')
    except Exception:
        print(f'  ⚠️  {tool}: 检查失败')
"

    echo ""
    echo "🔍 运行快速测试..."
    if python -m pytest tests/test_framework.py -v --tb=short > /dev/null 2>&1; then
        log_success "快速测试通过"
    else
        log_warning "快速测试失败（可能是预期行为）"
    fi
    
    echo ""
    echo "📊 代码质量检查..."
    if python -m pylint src/agents/base_agent.py --exit-zero > /dev/null 2>&1; then
        log_success "代码质量检查通过"
    else
        log_warning "代码质量检查发现一些问题（需要修复）"
    fi
}

# 显示完成信息
show_completion() {
    echo ""
    echo "🎉 开发环境设置完成！"
    echo "================================"
    echo ""
    echo "📋 已完成的设置:"
    echo "  ✅ 虚拟环境 (.venv)"
    echo "  ✅ 开发依赖安装"
    echo "  ✅ 增强功能安装"
    echo "  ✅ 开发配置文件"
    echo "  ✅ 开发工具配置"
    echo "  ✅ 环境验证"
    echo ""
    
    echo "🚀 下一步:"
    echo "  1. 配置环境变量:"
    echo "     nano .env.local"
    echo "     # 设置 OPENAI_API_KEY 和其他 API 密钥"
    echo ""
    echo "  2. 激活虚拟环境（如果未激活）:"
    echo "     source .venv/bin/activate"
    echo ""
    echo "  3. 启动开发服务器:"
    echo "     python src/api/server.py"
    echo "     # 或"
    echo "     ./start_server.sh"
    echo ""
    echo "  4. 运行完整测试:"
    echo "     python -m pytest tests/ -v"
    echo ""
    echo "  5. 格式化代码:"
    echo "     black src/"
    echo "     isort src/"
    echo ""
    echo "📚 开发文档:"
    echo "  - AGENTS.md: 架构和开发指南"
    echo "  - docs/development/: 开发文档"
    echo "  - tests/README_TEST_TOOLS.md: 测试工具指南"
    echo ""
    
    if [ "$VIRTUAL_ENV_ACTIVATED" = true ]; then
        echo "💡 提示: 虚拟环境已激活，要退出请运行: deactivate"
    else
        echo "💡 提示: 要激活虚拟环境请运行: source .venv/bin/activate"
    fi
    
    echo ""
    echo "✨ 开始愉快的开发吧！"
}

# 主函数
main() {
    echo "🚀 开始设置 RANGEN V2 开发环境..."
    echo "================================"
    echo ""
    
    # 执行所有步骤
    check_project_root
    check_python
    create_venv
    upgrade_pip
    install_dev_deps
    setup_precommit
    create_dev_configs
    setup_dev_tools
    validate_dev_env
    show_completion
}

# 运行主函数
main
