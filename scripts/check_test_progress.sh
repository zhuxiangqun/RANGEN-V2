#!/bin/bash
# 检查测试进度脚本

LOG_FILE="research_system.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "⚠️ 日志文件不存在: $LOG_FILE"
    exit 1
fi

# 检查已完成的样本数
COMPLETED=$(grep -c "FRAMES sample=.*success=" "$LOG_FILE" 2>/dev/null || echo "0")
TOTAL=$(grep -o "FRAMES sample=[0-9]*/[0-9]*" "$LOG_FILE" 2>/dev/null | tail -1 | grep -o "/[0-9]*" | tr -d "/" || echo "10")

echo "📊 测试进度: $COMPLETED / $TOTAL 个样本已完成"

# 检查是否有"Jane Ballou"错误
JANE_COUNT=$(grep -c "Jane Ballou" "$LOG_FILE" 2>/dev/null || echo "0")
echo "🔍 日志中出现\"Jane Ballou\"的次数: $JANE_COUNT"

# 显示最新的5条日志
echo ""
echo "📝 最新日志（最后5条）:"
tail -5 "$LOG_FILE" | sed 's/^/  /'

