#!/bin/bash
# 自动评测脚本 - 等待测试完成后立即运行评测

echo "等待FRAMES测试完成..."
COUNTER=0
MAX_WAIT=3600  # 最多等待1小时

while [ $COUNTER -lt $MAX_WAIT ]; do
    SAMPLE_COUNT=$(grep "FRAMES sample=" research_system.log 2>/dev/null | wc -l | tr -d ' ')
    
    if [ "$SAMPLE_COUNT" = "50" ]; then
        echo "✅ 测试完成！共 $SAMPLE_COUNT 个样本"
        break
    fi
    
    if [ $((COUNTER % 60)) -eq 0 ] && [ $COUNTER -ne 0 ]; then
        echo "等待中... 已完成 $SAMPLE_COUNT/50 个样本 ($(date))"
    fi
    
    sleep 2
    COUNTER=$((COUNTER + 2))
done

if [ "$SAMPLE_COUNT" != "50" ]; then
    echo "⚠️ 超时或测试未完成（当前 $SAMPLE_COUNT/50）"
    exit 1
fi

echo "---"
echo "开始运行评测系统..."
echo "---"

# 运行评测系统
cd /Users/syu/workdata/person/zy/RANGEN-main\(syu-python\)
.venv/bin/python evaluation/run_frames_evaluation.py research_system.log 2>&1 | tee evaluation_result.log

echo "---"
echo "评测完成！结果保存在 evaluation_result.log"
echo "---"

