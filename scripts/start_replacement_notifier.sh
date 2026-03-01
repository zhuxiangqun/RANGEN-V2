#!/bin/bash
# 启动替换比例变化通知器

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT" || exit 1

# 日志目录
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

# PID文件
PID_FILE="$LOG_DIR/replacement_notifier.pid"

echo "=================================================================================="
echo "启动替换比例变化通知器"
echo "=================================================================================="
echo ""

# 检查是否已有通知器在运行
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️  通知器已在运行 (PID: $OLD_PID)"
        echo "   如需重启，请先停止现有进程: kill $OLD_PID"
        exit 1
    else
        echo "ℹ️  清理旧的PID文件"
        rm -f "$PID_FILE"
    fi
fi

# 启动通知器（后台运行）
echo "🚀 启动通知器..."
echo "   监控日志: logs/react_agent_replacement.log"
echo "   检查间隔: 10秒"
echo "   通知方式: 控制台输出"
echo ""

nohup python3 "$SCRIPT_DIR/replacement_rate_notifier.py" \
    --log-file "$LOG_DIR/react_agent_replacement.log" \
    --check-interval 10 \
    --method console \
    > "$LOG_DIR/replacement_notifier.log" 2>&1 &

# 保存PID
NOTIFIER_PID=$!
echo "$NOTIFIER_PID" > "$PID_FILE"

echo "✅ 通知器已启动 (PID: $NOTIFIER_PID)"
echo ""
echo "📊 监控命令:"
echo "   查看通知日志: tail -f $LOG_DIR/replacement_notifier.log"
echo "   检查状态: ps -p $NOTIFIER_PID"
echo "   停止通知器: kill $NOTIFIER_PID"
echo ""
echo "💡 提示:"
echo "   当替换比例增加时，通知器会自动在控制台输出通知"
echo "   你也可以查看日志文件: tail -f $LOG_DIR/replacement_notifier.log"
echo ""
echo "=================================================================================="

