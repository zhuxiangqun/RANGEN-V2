#!/bin/bash
# ReActAgent逐步替换监控启动脚本

# 设置脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT" || exit 1

# 日志目录
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

# 日志文件
LOG_FILE="$LOG_DIR/react_agent_replacement_$(date +%Y%m%d_%H%M%S).log"
PID_FILE="$LOG_DIR/react_agent_replacement.pid"

echo "=================================================================================="
echo "ReActAgent逐步替换监控启动"
echo "=================================================================================="
echo "项目根目录: $PROJECT_ROOT"
echo "日志文件: $LOG_FILE"
echo "PID文件: $PID_FILE"
echo "=================================================================================="

# 检查是否已有监控进程在运行
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️  监控进程已在运行 (PID: $OLD_PID)"
        echo "   如需重启，请先停止现有进程: kill $OLD_PID"
        exit 1
    else
        echo "ℹ️  清理旧的PID文件"
        rm -f "$PID_FILE"
    fi
fi

# 启动监控（后台运行）
echo "🚀 启动逐步替换监控..."
# 检查间隔：120秒（2分钟）- 更频繁的检查以便及时发现问题
nohup python3 "$SCRIPT_DIR/start_gradual_replacement.py" \
    --source ReActAgent \
    --initial-rate 0.01 \
    --increase-step 0.1 \
    --check-interval 120 \
    > "$LOG_FILE" 2>&1 &

# 保存PID
MONITOR_PID=$!
echo "$MONITOR_PID" > "$PID_FILE"

echo "✅ 监控进程已启动 (PID: $MONITOR_PID)"
echo ""
echo "📊 监控命令:"
echo "   查看日志: tail -f $LOG_FILE"
echo "   检查状态: ps -p $MONITOR_PID"
echo "   停止监控: kill $MONITOR_PID"
echo "   查看统计: python3 scripts/check_replacement_stats.py --agent ReActAgent"
echo ""
echo "📝 日志文件: $LOG_FILE"
echo "=================================================================================="

