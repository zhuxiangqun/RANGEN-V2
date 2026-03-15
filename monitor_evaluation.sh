#!/bin/bash
# 监控评测进度和答案流程

LOG_FILE="research_system.log"

echo "=== 评测进度监控 ==="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 统计已完成样本数
COMPLETED=$(grep -c "系统答案" "$LOG_FILE" 2>/dev/null || echo "0")
echo "已完成样本数: $COMPLETED / 20"

# 统计答案类型
echo ""
echo "=== 答案类型统计 ==="
NUMERIC_ANSWERS=$(grep "系统答案:" "$LOG_FILE" | grep -E "系统答案: [0-9]+" | wc -l | tr -d ' ')
UNABLE_DETERMINE=$(grep "系统答案:" "$LOG_FILE" | grep -i "unable to determine" | wc -l | tr -d ' ')
TEXT_ANSWERS=$(grep "系统答案:" "$LOG_FILE" | grep -v "unable to determine" | grep -vE "系统答案: [0-9]+" | wc -l | tr -d ' ')

echo "数字答案: $NUMERIC_ANSWERS"
echo "unable to determine: $UNABLE_DETERMINE"
echo "文本答案: $TEXT_ANSWERS"

# 显示最近的答案
echo ""
echo "=== 最近的答案 ==="
grep "系统答案:" "$LOG_FILE" | tail -5

# 显示数字答案检测日志
echo ""
echo "=== 数字答案检测日志 ==="
grep "检测到数字答案" "$LOG_FILE" | tail -5

# 显示答案返回日志
echo ""
echo "=== 答案返回日志 ==="
grep "返回最终答案" "$LOG_FILE" | tail -5

echo ""
echo "=== 评测状态 ==="
if pgrep -f "run_core_with_frames" > /dev/null; then
    echo "✅ 评测正在运行中"
else
    echo "⏹️  评测已完成或未运行"
fi

