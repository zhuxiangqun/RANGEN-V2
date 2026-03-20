#!/bin/bash
# RANGEN V2 一体化体验启动脚本
# =================================
# 一键启动RANGEN系统，在一个画面中体验所有功能
# 使用Mock配置避免DeepSeek API费用

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 变量定义
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend_monitor"
BACKEND_PID=""
FRONTEND_PID=""
CONFIG_FILE="config/environments/development.yaml"
API_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"
API_HEALTH_CHECK="$API_URL/autodiscovery/health"
FRONTEND_HEALTH_CHECK="$FRONTEND_URL"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 清理函数
cleanup() {
    log_info "正在停止服务..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        log_info "停止后端API服务器 (PID: $BACKEND_PID)"
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        log_info "停止前端监控界面 (PID: $FRONTEND_PID)"
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    log_success "服务已停止"
    exit 0
}

# 捕获退出信号
trap cleanup SIGINT SIGTERM EXIT

# 显示标题
echo -e "${GREEN}"
echo "================================================"
echo "      RANGEN V2 一体化体验系统"
echo "================================================"
echo -e "${NC}"
echo "  版本: 2.0.0 (真实模式 - 使用DeepSeek API)"
echo "  目标: 在一个画面中体验所有功能"
echo "  作者: RANGEN开发团队"
echo "  日期: $(date)"
echo ""

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3未找到，请先安装Python3"
        exit 1
    fi
    log_success "Python3已安装: $(python3 --version | cut -d' ' -f2)"
    
    # 检查Node.js (前端需要)
    if ! command -v node &> /dev/null; then
        log_warning "Node.js未找到，前端监控界面将无法启动"
        log_warning "请安装Node.js以使用完整功能"
        FRONTEND_ENABLED=false
    else
        log_success "Node.js已安装: v$(node --version)"
        FRONTEND_ENABLED=true
    fi
    
    # 检查npm
    if [ "$FRONTEND_ENABLED" = true ] && ! command -v npm &> /dev/null; then
        log_warning "npm未找到，前端监控界面将无法启动"
        FRONTEND_ENABLED=false
    elif [ "$FRONTEND_ENABLED" = true ]; then
        log_success "npm已安装: v$(npm --version)"
    fi
    
    # 检查配置文件
    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "配置文件不存在: $CONFIG_FILE"
        log_info "使用默认配置文件..."
        CONFIG_FILE="config/environments/development.yaml"
        if [ ! -f "$CONFIG_FILE" ]; then
            log_error "默认配置文件也不存在"
            exit 1
        fi
    fi
    log_success "使用配置文件: $CONFIG_FILE"
    
    # 检查DeepSeek API密钥（仅development模式）
    if [ "$CONFIG_FILE" = "config/environments/development.yaml" ]; then
        if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
            log_warning "DEEPSEEK_API_KEY环境变量未设置"
            log_warning "请设置DEEPSEEK_API_KEY环境变量以使用DeepSeek API"
            log_warning "示例: export DEEPSEEK_API_KEY=your_api_key_here"
            log_warning "系统将尝试从配置文件读取API密钥"
        else
            log_success "DeepSeek API密钥已设置"
        fi
    fi
}

# 启动后端API服务器
start_backend() {
    log_info "启动后端API服务器..."
    
    # 设置环境变量
    export RANGEN_ENV_CONFIG="$CONFIG_FILE"
    export RANGEN_USE_UNIFIED_RESEARCH=1
    
    # 切换到项目根目录
    cd "$PROJECT_ROOT"
    
    # 在后台启动服务器
    python3 -m src.api.server > backend.log 2>&1 &
    BACKEND_PID=$!
    
    log_info "后端服务器启动中 (PID: $BACKEND_PID)"
    log_info "日志文件: $PROJECT_ROOT/backend.log"
    
    # 等待服务器启动
    local max_attempts=30
    local attempt=1
    
    log_info "等待后端服务器启动..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s --max-time 2 "$API_HEALTH_CHECK" > /dev/null 2>&1; then
            log_success "后端API服务器启动成功!"
            log_success "API地址: $API_URL"
            log_success "API文档: $API_URL/docs"
            return 0
        fi
        
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            log_error "后端服务器进程已退出，请检查日志: $PROJECT_ROOT/backend.log"
            tail -20 "$PROJECT_ROOT/backend.log"
            exit 1
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    log_error "后端服务器启动超时"
    log_error "请检查日志: $PROJECT_ROOT/backend.log"
    tail -20 "$PROJECT_ROOT/backend.log"
    exit 1
}

# 启动前端监控界面
start_frontend() {
    if [ "$FRONTEND_ENABLED" = false ]; then
        log_warning "跳过前端监控界面启动 (依赖缺失)"
        return 0
    fi
    
    log_info "启动前端监控界面..."
    
    # 检查前端目录
    if [ ! -d "$FRONTEND_DIR" ]; then
        log_error "前端目录不存在: $FRONTEND_DIR"
        return 1
    fi
    
    # 检查package.json
    if [ ! -f "$FRONTEND_DIR/package.json" ]; then
        log_error "前端package.json不存在"
        return 1
    fi
    
    # 安装依赖（如果需要）
    if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
        log_info "安装前端依赖..."
        cd "$FRONTEND_DIR"
        npm install --silent
        if [ $? -ne 0 ]; then
            log_error "前端依赖安装失败"
            return 1
        fi
        cd "$PROJECT_ROOT"
    fi
    
    # 在后台启动前端开发服务器
    cd "$FRONTEND_DIR"
    npm run dev > frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd "$PROJECT_ROOT"
    
    log_info "前端监控界面启动中 (PID: $FRONTEND_PID)"
    log_info "日志文件: $PROJECT_ROOT/frontend.log"
    
    # 等待前端启动
    local max_attempts=30
    local attempt=1
    
    log_info "等待前端监控界面启动..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s --max-time 2 "$FRONTEND_HEALTH_CHECK" > /dev/null 2>&1; then
            log_success "前端监控界面启动成功!"
            log_success "访问地址: $FRONTEND_URL"
            log_success "路由监控: $FRONTEND_URL/#/routing"
            return 0
        fi
        
        if ! kill -0 $FRONTEND_PID 2>/dev/null; then
            log_error "前端进程已退出，请检查日志: $PROJECT_ROOT/frontend.log"
            tail -20 "$PROJECT_ROOT/frontend.log"
            return 1
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    log_error "前端监控界面启动超时"
    log_error "请检查日志: $PROJECT_ROOT/frontend.log"
    tail -20 "$PROJECT_ROOT/frontend.log"
    return 1
}

# 显示系统状态
show_system_status() {
    echo ""
    echo -e "${GREEN}================================================"
    echo "         系统启动完成!"
    echo "================================================"
    echo -e "${NC}"
    
    # 后端状态
    if curl -s --max-time 2 "$API_HEALTH_CHECK" > /dev/null 2>&1; then
        echo -e "✅ ${GREEN}后端API服务器${NC}: 运行中"
        echo "   - API地址: $API_URL"
        echo "   - 文档地址: $API_URL/docs"
        
        # 测试自动发现API
        echo "   - 自动发现API: $API_URL/autodiscovery/health"
    else
        echo -e "❌ ${RED}后端API服务器${NC}: 未运行"
    fi
    
    # 前端状态
    if [ "$FRONTEND_ENABLED" = true ]; then
        if curl -s --max-time 2 "$FRONTEND_HEALTH_CHECK" > /dev/null 2>&1; then
            echo -e "✅ ${GREEN}前端监控界面${NC}: 运行中"
            echo "   - 访问地址: $FRONTEND_URL"
            echo "   - 路由监控: $FRONTEND_URL/#/routing"
        else
            echo -e "❌ ${RED}前端监控界面${NC}: 未运行"
        fi
    else
        echo -e "⚠️  ${YELLOW}前端监控界面${NC}: 未启用 (缺少Node.js/npm)"
    fi
    
    echo ""
    echo -e "${GREEN}================================================"
    echo "         快速测试命令"
    echo "================================================"
    echo -e "${NC}"
    echo "1. 健康检查:"
    echo "   curl $API_URL/autodiscovery/health"
    echo ""
    echo "2. 自动发现状态:"
    echo "   curl $API_URL/autodiscovery/status"
    echo ""
    echo "3. 启动自动发现扫描:"
    echo "   curl -X POST $API_URL/autodiscovery/scan"
    echo ""
    echo "4. 测试Agent需求触发:"
    echo "   curl -X POST '$API_URL/autodiscovery/trigger/agent-demand?query=help%20me%20write%20python%20code'"
    echo ""
    echo "5. 一键集成所有资源:"
    echo "   curl -X POST $API_URL/autodiscovery/auto-integrate"
    echo ""
    echo "6. 查看路由统计:"
    echo "   curl $API_URL/api/routing/statistics"
    echo ""
    echo -e "${GREEN}================================================"
    echo "         使用说明"
    echo "================================================"
    echo -e "${NC}"
    echo "• 系统运行在真实模式下，使用DeepSeek API (需要API密钥)"
    echo "• 按Ctrl+C可停止所有服务"
    echo "• 查看后端日志: tail -f $PROJECT_ROOT/backend.log"
    if [ "$FRONTEND_ENABLED" = true ]; then
        echo "• 查看前端日志: tail -f $PROJECT_ROOT/frontend.log"
    fi
    echo "• 访问前端界面体验所有功能: $FRONTEND_URL"
    echo ""
    echo -e "${GREEN}================================================"
    echo "         一体化体验功能"
    echo "================================================"
    echo -e "${NC}"
    echo "1. 📊 路由监控 - 实时查看智能路由决策"
    echo "2. 🔍 自动发现 - 智能发现MCP服务器和外部资源"
    echo "3. 🤖 Agent管理 - 查看和管理智能体"
    echo "4. 🔧 工具管理 - 管理和调用可用工具"
    echo "5. 🌐 外部集成 - 集成外部服务和API"
    echo "6. 📈 系统统计 - 查看系统性能和状态"
    echo ""
}

# 主函数
main() {
    check_dependencies
    start_backend
    start_frontend
    show_system_status
    
    # 等待用户中断
    echo -e "${YELLOW}系统正在运行中... 按Ctrl+C停止服务${NC}"
    echo ""
    
    # 保持脚本运行
    wait
}

# 运行主函数
main