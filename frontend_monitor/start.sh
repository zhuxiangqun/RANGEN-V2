#!/bin/bash
set -euo pipefail

# RANGEN前端监控系统启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 🚀 新增：初始化变量，避免未定义变量错误
TENSORBOARD_PID=""

echo "🚀 启动RANGEN前端监控系统..."

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到Node.js，请先安装Node.js"
    exit 1
fi

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

# 🚀 修复：使用项目根目录的.venv，而不是backend/venv
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

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
    pip install -r backend/requirements.txt
fi

# 🚀 新增：检查 TensorBoard 是否已安装（用于推理过程可视化）
if ! python -c "import tensorboard" 2>/dev/null; then
    echo "📦 TensorBoard 未安装，正在安装..."
    pip install tensorboard==2.15.1
    echo "✅ TensorBoard 安装完成"
else
    echo "✅ TensorBoard 已安装（推理过程可视化功能可用）"
fi

# 🚀 新增：检查并停止已运行的后端服务
echo "🔍 检查已运行的后端服务..."
BACKEND_PIDS=$(ps aux | grep "[p]ython.*app.py" | grep -v grep | awk '{print $2}' || true)
if [ -n "$BACKEND_PIDS" ]; then
    echo "🛑 发现已运行的后端服务，正在停止..."
    echo "$BACKEND_PIDS" | xargs kill -9 2>/dev/null || true
    sleep 1
    echo "✅ 已停止旧的后端服务"
fi

# 🚀 新增：检查并停止已运行的前端服务（Vite）
echo "🔍 检查已运行的前端服务..."
# 方法1：通过端口检测
FRONTEND_PIDS_PORT=$(lsof -ti:3000 2>/dev/null || true)
# 方法2：通过进程名检测（更可靠）
FRONTEND_PIDS_PROC=$(ps aux | grep -E "[v]ite|[n]ode.*dev" | grep -v grep | awk '{print $2}' || true)
# 合并所有PID
FRONTEND_PIDS=$(echo "$FRONTEND_PIDS_PORT $FRONTEND_PIDS_PROC" | tr ' ' '\n' | sort -u | tr '\n' ' ')

if [ -n "$FRONTEND_PIDS" ]; then
    echo "🛑 发现已运行的前端服务，正在停止..."
    echo "$FRONTEND_PIDS" | xargs kill -9 2>/dev/null || true
    sleep 2  # 增加等待时间，确保进程完全停止
    echo "✅ 已停止旧的前端服务"
fi

# 🚀 新增：检查并停止已运行的 TensorBoard 服务（如果存在）
echo "🔍 检查已运行的 TensorBoard 服务..."
# 方法1：通过进程名检测
TENSORBOARD_PIDS_PROC=$(ps aux | grep "[t]ensorboard" | grep -v grep | awk '{print $2}' || true)
# 方法2：通过端口检测（TensorBoard 默认使用 6006 端口）
TENSORBOARD_PIDS_PORT=$(lsof -ti:6006 2>/dev/null || true)
# 合并所有PID
TENSORBOARD_PIDS=$(echo "$TENSORBOARD_PIDS_PROC $TENSORBOARD_PIDS_PORT" | tr ' ' '\n' | sort -u | tr '\n' ' ' | xargs)

if [ -n "$TENSORBOARD_PIDS" ]; then
    echo "🛑 发现已运行的 TensorBoard 服务（PID: $TENSORBOARD_PIDS），正在停止..."
    echo "$TENSORBOARD_PIDS" | xargs kill -9 2>/dev/null || true
    sleep 2  # 增加等待时间，确保进程完全停止
    echo "✅ 已停止旧的 TensorBoard 服务"
else
    echo "✅ 未发现运行中的 TensorBoard 服务"
fi

# 🚀 可选：自动启动 TensorBoard 服务（如果需要，取消下面的注释）
# AUTO_START_TENSORBOARD=${AUTO_START_TENSORBOARD:-false}
# if [ "$AUTO_START_TENSORBOARD" = "true" ]; then
#     echo "📊 启动 TensorBoard 服务..."
#     cd "${ROOT_DIR}"
#     tensorboard --logdir tensorboard_logs --port 6006 --host 0.0.0.0 > /dev/null 2>&1 &
#     TENSORBOARD_PID=$!
#     cd "$SCRIPT_DIR"
#     echo "✅ TensorBoard 服务已启动（PID: $TENSORBOARD_PID，端口: 6006）"
# fi

# 启动后端服务（后台运行）
echo "🔧 启动后端服务..."
cd backend
python app.py > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 3

# 检查后端是否启动成功（尝试5000和5001端口）
# 🚀 修复：优先检查5001（避免AirPlay冲突），然后检查5000
BACKEND_PORT=5001
MAX_RETRIES=5
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    # 优先检查5001端口（避免AirPlay冲突）
    if curl -s http://localhost:5001/api/logs > /dev/null 2>&1; then
        BACKEND_PORT=5001
        echo "✅ 后端服务运行在端口 5001"
        break
    elif curl -s http://localhost:5000/api/logs > /dev/null 2>&1; then
        # 检查5000端口是否真的是后端（不是AirPlay）
        RESPONSE=$(curl -s -I http://localhost:5000/api/logs 2>&1 | head -1)
        if echo "$RESPONSE" | grep -q "200 OK"; then
            BACKEND_PORT=5000
            echo "✅ 后端服务运行在端口 5000"
            break
        else
            # 5000端口被AirPlay占用，继续检查5001
            echo "⚠️  端口 5000 被 AirPlay 占用，继续检查 5001..."
        fi
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
        echo "⏳ 等待后端启动... ($RETRY_COUNT/$MAX_RETRIES)"
        sleep 1
    else
        echo "⚠️  警告: 后端服务可能未正常启动，请检查backend.log"
        echo "   将使用默认端口 5001（避免AirPlay冲突）"
        BACKEND_PORT=5001
    fi
done

# 🚀 修复：设置环境变量，让Vite知道后端实际运行的端口
export VITE_API_URL="http://localhost:${BACKEND_PORT}"
echo "🔧 设置前端代理目标: ${VITE_API_URL}"

# 🚀 新增：创建或更新 .env 文件，确保 Vite 能读取到正确的端口
ENV_FILE="${SCRIPT_DIR}/.env"
echo "VITE_API_URL=${VITE_API_URL}" > "${ENV_FILE}"
echo "✅ 已更新 .env 文件: ${VITE_API_URL}"

# 启动前端服务
echo "🎨 启动前端服务..."
echo ""
echo "✅ 系统启动完成！"
echo "📱 前端地址: http://localhost:3000"
echo "🔧 后端地址: http://localhost:${BACKEND_PORT}"
echo "🔗 前端代理: ${VITE_API_URL}"
echo "📊 TensorBoard: 将在生成推理日志时自动启动（端口 6006）"
if [ -n "$TENSORBOARD_PID" ]; then
    echo "📊 TensorBoard: 已自动启动（端口 6006）"
fi
echo ""
echo "💡 提示: 在前端界面中，可以切换到 'TensorBoard' 视图来可视化推理过程"
echo "💡 提示: 如需自动启动 TensorBoard，设置环境变量: export AUTO_START_TENSORBOARD=true"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 🚀 新增：清理函数，确保所有进程都被正确停止
cleanup() {
    echo ""
    echo "🛑 正在停止服务..."
    
    # 停止后端服务
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo "✅ 已停止后端服务"
    fi
    
    # 停止 TensorBoard 服务（包括自动启动的和后端启动的）
    TENSORBOARD_PIDS=$(ps aux | grep "[t]ensorboard" | grep -v grep | awk '{print $2}' || true)
    if [ -n "$TENSORBOARD_PIDS" ]; then
        echo "$TENSORBOARD_PIDS" | xargs kill -9 2>/dev/null || true
        echo "✅ 已停止 TensorBoard 服务"
    fi
    
    # 如果自动启动了 TensorBoard，也停止它
    if [ -n "$TENSORBOARD_PID" ]; then
        kill $TENSORBOARD_PID 2>/dev/null || true
    fi
    
    # 清理临时文件
    rm -f "${ENV_FILE}"
    
    echo "✅ 清理完成"
    exit 0
}

# 捕获退出信号，清理后台进程
trap cleanup INT TERM

# 🚀 修复：确保环境变量传递给 npm（在命令前显式设置）
VITE_API_URL="${VITE_API_URL}" npm run dev

