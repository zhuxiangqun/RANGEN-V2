#!/bin/bash
# 停止可视化服务器脚本

set -e

echo "=========================================="
echo "停止可视化服务器"
echo "=========================================="
echo ""

# 查找占用端口 8080 的进程
PORT=8080
PIDS=$(lsof -ti:$PORT 2>/dev/null || echo "")

if [ -z "$PIDS" ]; then
    echo "✅ 端口 $PORT 未被占用，没有需要停止的服务器"
else
    echo "找到占用端口 $PORT 的进程: $PIDS"
    echo "正在停止..."
    
    # 尝试优雅停止
    echo "$PIDS" | xargs kill -TERM 2>/dev/null || true
    sleep 2
    
    # 检查是否还在运行
    REMAINING=$(lsof -ti:$PORT 2>/dev/null || echo "")
    if [ ! -z "$REMAINING" ]; then
        echo "强制终止剩余进程..."
        echo "$REMAINING" | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
    
    # 再次检查
    FINAL_CHECK=$(lsof -ti:$PORT 2>/dev/null || echo "")
    if [ -z "$FINAL_CHECK" ]; then
        echo "✅ 端口 $PORT 已释放"
    else
        echo "⚠️  警告: 端口 $PORT 仍被占用，进程: $FINAL_CHECK"
        echo "   请手动停止: kill -9 $FINAL_CHECK"
    fi
fi

echo ""

