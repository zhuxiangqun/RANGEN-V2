#!/bin/bash
# 停止所有检测/监控程序

set -e

echo "=================================================================================="
echo "停止所有检测/监控程序"
echo "=================================================================================="
echo ""

# 定义PID文件列表
PID_FILES=(
    "logs/react_agent_replacement.pid"
    "logs/react_agent_replacement_pid.txt"
    "logs/replacement_pid.txt"
)

# 停止PID文件中记录的进程
stopped_count=0
for pid_file in "${PID_FILES[@]}"; do
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file" 2>/dev/null | tr -d '[:space:]')
        if [ -n "$pid" ] && [ "$pid" -gt 0 ] 2>/dev/null; then
            echo "🔍 发现PID文件: $pid_file (PID: $pid)"
            
            # 检查进程是否还在运行
            if ps -p "$pid" > /dev/null 2>&1; then
                echo "   🛑 正在停止进程 PID: $pid..."
                kill "$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null || true
                sleep 1
                
                # 再次检查
                if ! ps -p "$pid" > /dev/null 2>&1; then
                    echo "   ✅ 进程 $pid 已停止"
                    stopped_count=$((stopped_count + 1))
                else
                    echo "   ⚠️  进程 $pid 仍在运行，尝试强制终止..."
                    kill -9 "$pid" 2>/dev/null || true
                    sleep 1
                    if ! ps -p "$pid" > /dev/null 2>&1; then
                        echo "   ✅ 进程 $pid 已强制停止"
                        stopped_count=$((stopped_count + 1))
                    else
                        echo "   ❌ 无法停止进程 $pid"
                    fi
                fi
            else
                echo "   ℹ️  进程 $pid 已不存在"
            fi
            
            # 删除PID文件
            rm -f "$pid_file"
            echo "   🗑️  已删除PID文件: $pid_file"
        fi
    fi
done

# 查找并停止所有相关的Python监控进程
echo ""
echo "🔍 查找所有相关的监控进程..."
MONITORING_PIDS=$(ps aux | grep -E "start_gradual_replacement|gradual_replacement" | grep -v grep | awk '{print $2}' 2>/dev/null || true)

if [ -n "$MONITORING_PIDS" ]; then
    echo "   🛑 发现监控进程，正在停止..."
    for pid in $MONITORING_PIDS; do
        echo "   🛑 正在停止进程 PID: $pid..."
        kill "$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null || true
        sleep 1
        if ! ps -p "$pid" > /dev/null 2>&1; then
            echo "   ✅ 进程 $pid 已停止"
            stopped_count=$((stopped_count + 1))
        else
            echo "   ⚠️  进程 $pid 仍在运行，尝试强制终止..."
            kill -9 "$pid" 2>/dev/null || true
            sleep 1
            if ! ps -p "$pid" > /dev/null 2>&1; then
                echo "   ✅ 进程 $pid 已强制停止"
                stopped_count=$((stopped_count + 1))
            else
                echo "   ❌ 无法停止进程 $pid"
            fi
        fi
    done
else
    echo "   ℹ️  未发现运行中的监控进程"
fi

echo ""
echo "=================================================================================="
if [ $stopped_count -gt 0 ]; then
    echo "✅ 已停止 $stopped_count 个检测/监控进程"
else
    echo "ℹ️  未发现运行中的检测/监控进程"
fi
echo "=================================================================================="

