#!/bin/bash

# 快速启动脚本 - 自动解决端口冲突并启动服务器

echo "🚀 RANGEN 统一服务器快速启动"
echo "=================================="

# 检查参数
if [ $# -eq 0 ]; then
    BASE_PORT=9000
else
    BASE_PORT=$1
fi

echo "🎯 统一端口: $BASE_PORT (可视化 + 配置管理)"

# 检查端口是否可用
check_port() {
    if lsof -i :$1 > /dev/null 2>&1; then
        return 0  # 端口被占用
    else
        return 1  # 端口可用
    fi
}

kill_process_on_port() {
    local port=$1
    echo "🔪 清理端口 $port 的进程..."

    # 获取占用端口的进程PID
    local pids=$(lsof -ti :$port 2>/dev/null)

    if [ ! -z "$pids" ]; then
        echo "发现进程: $pids"
        for pid in $pids; do
            echo "终止进程 $pid..."
            kill -9 $pid 2>/dev/null
            sleep 1
        done
        return 0
    else
        echo "端口 $port 未被占用"
        return 1
    fi
}

# 主端口检查和清理
echo "🔍 检查端口可用性..."
if check_port $BASE_PORT; then
    echo "⚠️  端口 $BASE_PORT 被占用，尝试清理..."
    kill_process_on_port $BASE_PORT
fi

# 最终检查，如果仍有冲突则寻找替代端口
if check_port $BASE_PORT; then
    echo "❌ 端口清理失败，寻找替代端口..."
    for alt_port in 8080 8082 3000 5000 7000 9000 4000 6000; do
        if ! check_port $alt_port; then
            echo "✅ 找到可用端口: $alt_port"
            BASE_PORT=$alt_port
            break
        fi
    done
fi

# 再次验证端口可用性
sleep 1
if check_port $BASE_PORT; then
    echo "❌ 最终端口检查失败，使用智能启动器..."
    python scripts/smart_server_launcher.py
    exit $?
fi

echo "✅ 使用端口: $BASE_PORT (统一服务)"
echo ""
echo "🚀 启动统一服务器..."

# 启动服务器
python scripts/start_unified_server.py --port $BASE_PORT

echo ""
echo "🎉 启动完成！"
echo "   🌐 统一服务: http://localhost:$BASE_PORT"
echo "   📊 可视化: http://localhost:$BASE_PORT/"
echo "   ⚙️ 配置管理: http://localhost:$BASE_PORT/config"
echo "   🔗 API端点: http://localhost:$BASE_PORT/api/*"
