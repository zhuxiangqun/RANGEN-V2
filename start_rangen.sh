#!/bin/bash
# ============================================================
# RANGEN 启动脚本 - 分离 AI 基座与应用
# ============================================================
#
# 架构说明:
#   - RANGEN AI 基座: 仅包含 API 服务
#   - 管理应用: 独立的 Streamlit 应用，通过 API 调用基座
#
# 使用方式:
#   ./start_rangen.sh base         - 启动基座 (仅 API)
#   ./start_rangen.sh app         - 启动管理应用
#   ./start_rangen.sh all         - 启动全部
#   ./start_rangen.sh stop        - 停止所有服务
#   ./start_rangen.sh status      - 查看服务状态

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"

# Ports
PORT_API=8000
PORT_ENTRY=8500   # 统一入口
PORT_CHAT=8501    # 聊天
PORT_ADMIN=8502   # 管理平台
PORT_GOV=8503     # 治理仪表盘

# ============================================================

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_base() { echo -e "${BLUE}[基座]${NC} $1"; }
log_app() { echo -e "${CYAN}[应用]${NC} $1"; }

is_port_in_use() { lsof -i :$1 >/dev/null 2>&1; }
get_pid_by_port() { lsof -ti :$1 2>/dev/null | head -1; }

kill_port() {
    local port=$1
    local pid=$(get_pid_by_port $port)
    if [ -n "$pid" ]; then
        log_info "Stopping process on port $port (PID: $pid)..."
        kill -9 $pid 2>/dev/null || true
        sleep 0.5
    fi
}

# ============================================================

start_base() {
    log_base "Starting RANGEN AI 基座..."
    
    if is_port_in_use $PORT_API; then
        log_warn "Port $PORT_API is already in use!"
        return 0
    fi
    
    cd "$SCRIPT_DIR"
    export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
    
    log_base "Starting API server on port $PORT_API..."
    
    nohup $VENV_PYTHON src/api/server.py > /dev/null 2>&1 &
    API_PID=$!
    
    for i in {1..15}; do
        sleep 1
        if is_port_in_use $PORT_API; then
            log_base "✅ API server started on http://localhost:$PORT_API"
            log_base "   - API Docs: http://localhost:$PORT_API/docs"
            log_base "   - ReDoc:    http://localhost:$PORT_API/redoc"
            return 0
        fi
    done
    
    log_error "❌ Failed to start API server"
    return 1
}

start_entry() {
    log_app "Starting RANGEN 统一入口..."
    if is_port_in_use $PORT_ENTRY; then
        log_warn "Port $PORT_ENTRY is already in use!"
        return 0
    fi
    cd "$SCRIPT_DIR"
    nohup streamlit run apps/entry_app/app.py --server.port $PORT_ENTRY --server.headless true > /dev/null 2>&1 &
    for i in {1..10}; do
        sleep 1
        if is_port_in_use $PORT_ENTRY; then
            log_app "✅ Entry app started on http://localhost:$PORT_ENTRY"
            return 0
        fi
    done
    log_error "❌ Failed to start entry app"
    return 1
}

start_chat() {
    log_app "Starting RANGEN 聊天..."
    if is_port_in_use $PORT_CHAT; then
        log_warn "Port $PORT_CHAT is already in use!"
        return 0
    fi
    cd "$SCRIPT_DIR"
    nohup streamlit run apps/chat_app/app.py --server.port $PORT_CHAT --server.headless true > /dev/null 2>&1 &
    for i in {1..10}; do
        sleep 1
        if is_port_in_use $PORT_CHAT; then
            log_app "✅ Chat app started on http://localhost:$PORT_CHAT"
            return 0
        fi
    done
    log_error "❌ Failed to start chat app"
    return 1
}

start_admin() {
    log_app "Starting RANGEN 管理平台..."
    if is_port_in_use $PORT_ADMIN; then
        log_warn "Port $PORT_ADMIN is already in use!"
        return 0
    fi
    cd "$SCRIPT_DIR"
    nohup streamlit run apps/management_app/app.py --server.port $PORT_ADMIN --server.headless true > /dev/null 2>&1 &
    for i in {1..10}; do
        sleep 1
        if is_port_in_use $PORT_ADMIN; then
            log_app "✅ Admin app started on http://localhost:$PORT_ADMIN"
            return 0
        fi
    done
    log_error "❌ Failed to start admin app"
    return 1
}

start_gov() {
    log_app "Starting RANGEN 治理仪表盘..."
    if is_port_in_use $PORT_GOV; then
        log_warn "Port $PORT_GOV is already in use!"
        return 0
    fi
    cd "$SCRIPT_DIR"
    nohup streamlit run apps/governance_app/app.py --server.port $PORT_GOV --server.headless true > /dev/null 2>&1 &
    for i in {1..10}; do
        sleep 1
        if is_port_in_use $PORT_GOV; then
            log_app "✅ Governance app started on http://localhost:$PORT_GOV"
            return 0
        fi
    done
    log_error "❌ Failed to start governance app"
    return 1
}

start_all_apps() {
    start_entry
    echo ""
    start_chat
    echo ""
    start_admin
    echo ""
    start_gov
}

start_all() {
    log_info "Starting RANGEN (基座 + 全部应用)..."
    echo ""
    start_base
    echo ""
    start_all_apps
    echo ""
    log_info "============================================"
    log_info "🎉 RANGEN 启动完成!"
    log_info "============================================"
    log_info ""
    log_info "访问地址:"
    log_info "  🚪 统一入口:  http://localhost:$PORT_ENTRY"
    log_info "  💬 聊天:      http://localhost:$PORT_CHAT"
    log_info "  🔧 管理:      http://localhost:$PORT_ADMIN"
    log_info "  📊 治理:      http://localhost:$PORT_GOV"
    log_info "  📚 API:       http://localhost:$PORT_API/docs"
    log_info ""
}

stop_all() {
    log_info "Stopping all RANGEN services..."
    kill_port $PORT_API
    kill_port $PORT_ENTRY
    kill_port $PORT_CHAT
    kill_port $PORT_ADMIN
    kill_port $PORT_GOV
    
    pkill -f "streamlit.*entry_app" 2>/dev/null || true
    pkill -f "streamlit.*chat_app" 2>/dev/null || true
    pkill -f "streamlit.*management_app" 2>/dev/null || true
    pkill -f "streamlit.*governance_app" 2>/dev/null || true
    pkill -f "python.*src/api/server.py" 2>/dev/null || true
    
    log_info "✅ All services stopped"
}

stop_base() {
    log_base "Stopping RANGEN AI 基座..."
    kill_port $PORT_API
    pkill -f "python.*src/api/server.py" 2>/dev/null || true
    log_base "✅ API 基座已停止"
}

stop_app() {
    log_app "Stopping RANGEN 所有应用..."
    kill_port $PORT_ENTRY
    kill_port $PORT_CHAT
    kill_port $PORT_ADMIN
    kill_port $PORT_GOV
    pkill -f "streamlit.*entry_app" 2>/dev/null || true
    pkill -f "streamlit.*chat_app" 2>/dev/null || true
    pkill -f "streamlit.*management_app" 2>/dev/null || true
    pkill -f "streamlit.*governance_app" 2>/dev/null || true
    log_app "✅ 所有应用已停止"
}

show_status() {
    echo ""
    echo "============================================"
    echo "         RANGEN 服务状态"
    echo "============================================"
    echo ""
    
    printf "  ${BLUE}●${NC} API 基座 (port $PORT_API): "
    if is_port_in_use $PORT_API; then
        echo -e "${GREEN}运行中${NC} (PID: $(get_pid_by_port $PORT_API))"
    else
        echo -e "${RED}未运行${NC}"
    fi
    
    printf "  ${CYAN}●${NC} 统一入口 (port $PORT_ENTRY): "
    if is_port_in_use $PORT_ENTRY; then
        echo -e "${GREEN}运行中${NC} (PID: $(get_pid_by_port $PORT_ENTRY))"
    else
        echo -e "${RED}未运行${NC}"
    fi
    
    printf "  ${CYAN}●${NC} 聊天 (port $PORT_CHAT): "
    if is_port_in_use $PORT_CHAT; then
        echo -e "${GREEN}运行中${NC} (PID: $(get_pid_by_port $PORT_CHAT))"
    else
        echo -e "${RED}未运行${NC}"
    fi
    
    printf "  ${CYAN}●${NC} 管理平台 (port $PORT_ADMIN): "
    if is_port_in_use $PORT_ADMIN; then
        echo -e "${GREEN}运行中${NC} (PID: $(get_pid_by_port $PORT_ADMIN))"
    else
        echo -e "${RED}未运行${NC}"
    fi
    
    printf "  ${CYAN}●${NC} 治理仪表盘 (port $PORT_GOV): "
    if is_port_in_use $PORT_GOV; then
        echo -e "${GREEN}运行中${NC} (PID: $(get_pid_by_port $PORT_GOV))"
    else
        echo -e "${RED}未运行${NC}"
    fi
    
    echo ""
}

show_help() {
    echo ""
    echo "============================================"
    echo "    RANGEN 启动脚本"
    echo "============================================"
    echo ""
    echo "用法: $0 <命令>"
    echo ""
    echo "启动命令:"
    echo "  start       - 启动全部 (基座 + 所有应用)"
    echo "  start-base  - 启动 AI 基座"
    echo "  start-app   - 启动所有应用"
    echo ""
    echo "停止命令:"
    echo "  stop        - 停止所有服务"
    echo "  stop-base   - 停止 AI 基座"
    echo "  stop-app    - 停止所有应用"
    echo ""
    echo "其他命令:"
    echo "  status      - 查看服务状态"
    echo "  help        - 显示帮助"
    echo ""
    echo "示例:"
    echo "  $0 start       # 启动全部"
    echo "  $0 start-base  # 启动基座"
    echo "  $0 start-app   # 启动应用"
    echo "  $0 stop        # 停止全部"
    echo "  $0 status      # 查看状态"
    echo ""
}

# ============================================================

case "$1" in
    start)
        start_all
        ;;
    start-base)
        start_base
        ;;
    start-app)
        start_app
        ;;
    stop)
        stop_all
        ;;
    stop-base)
        stop_base
        ;;
    stop-app)
        stop_app
        ;;
    status)
        show_status
        ;;
    help|--help|-h)
        show_help
        ;;
esac
