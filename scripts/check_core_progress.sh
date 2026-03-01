#!/bin/bash
# 检查核心系统运行进度

LOG_FILE="research_system.log"
TOTAL_SAMPLES=824

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ 未找到日志文件: $LOG_FILE"
    exit 1
fi

echo "📊 核心系统运行进度统计"
echo "================================"
echo ""

# 统计成功完成的样本
SUCCESS_SAMPLES=$(grep "查询完成.*success=True.*样本ID=" "$LOG_FILE" 2>/dev/null | sed -n 's/.*样本ID=\([0-9]*\).*/\1/p' | sort -n -u)

if [ -n "$SUCCESS_SAMPLES" ]; then
    SUCCESS_COUNT=$(echo "$SUCCESS_SAMPLES" | wc -l | tr -d ' ')
    MAX_SUCCESS_ID=$(echo "$SUCCESS_SAMPLES" | tail -1)
    PERCENTAGE=$(echo "scale=2; $SUCCESS_COUNT * 100 / $TOTAL_SAMPLES" | bc 2>/dev/null || echo "0")
    REMAINING=$((TOTAL_SAMPLES - SUCCESS_COUNT))
    
    echo "✅ 成功完成: $SUCCESS_COUNT / $TOTAL_SAMPLES (${PERCENTAGE}%)"
    echo "📈 最大样本ID: $MAX_SUCCESS_ID"
    echo "⏳ 剩余样本: $REMAINING"
    echo ""
    
    # 计算预计剩余时间（如果可能）
    if [ "$SUCCESS_COUNT" -gt 0 ]; then
        # 获取第一个和最后一个样本的处理时间
        FIRST_TIME=$(grep "查询完成.*success=True.*样本ID=" "$LOG_FILE" | head -1 | grep -oE "[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}" | head -1)
        LAST_TIME=$(grep "查询完成.*success=True.*样本ID=" "$LOG_FILE" | tail -1 | grep -oE "[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}" | head -1)
        
        if [ -n "$FIRST_TIME" ] && [ -n "$LAST_TIME" ]; then
            echo "🕐 第一个样本完成时间: $FIRST_TIME"
            echo "🕐 最后一个样本完成时间: $LAST_TIME"
        fi
    fi
    
    echo ""
    echo "最后10个完成的样本ID:"
    echo "$SUCCESS_SAMPLES" | tail -10
else
    echo "⚠️ 未找到成功完成的样本记录"
fi

echo ""
echo "=== 所有处理的样本（包括失败）==="
ALL_SAMPLES=$(grep "样本ID=" "$LOG_FILE" 2>/dev/null | sed -n 's/.*样本ID=\([0-9]*\).*/\1/p' | sort -n -u)

if [ -n "$ALL_SAMPLES" ]; then
    ALL_COUNT=$(echo "$ALL_SAMPLES" | wc -l | tr -d ' ')
    MAX_ALL_ID=$(echo "$ALL_SAMPLES" | tail -1)
    echo "📊 已处理样本数: $ALL_COUNT"
    echo "📈 最大样本ID: $MAX_ALL_ID"
fi

echo ""
echo "=== 运行状态 ==="
if pgrep -f "run_core_with_frames" > /dev/null; then
    echo "✅ 核心系统正在运行中"
    echo ""
    echo "进程信息:"
    ps aux | grep "run_core_with_frames" | grep -v grep | head -1 | awk '{print "   PID: "$2", CPU: "$3"%, MEM: "$4"%"}'
else
    echo "⏹️  核心系统当前未运行"
fi

echo ""
echo "📅 日志最后更新: $(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$LOG_FILE" 2>/dev/null || stat -c "%y" "$LOG_FILE" 2>/dev/null | cut -d'.' -f1)"
echo "📁 日志文件大小: $(ls -lh "$LOG_FILE" | awk '{print $5}')"

echo ""
echo "=== 最近的查询记录 ==="
tail -5 "$LOG_FILE" | grep -E "查询完成|样本ID" | head -5

