#!/bin/bash
# 监控测试进度

LOG_FILE="research_system.log"
MAX_WAIT=3600  # 最大等待时间（秒）
CHECK_INTERVAL=30  # 检查间隔（秒）
ELAPSED=0

echo "开始监控测试进度..."
echo "日志文件: $LOG_FILE"
echo "检查间隔: ${CHECK_INTERVAL}秒"
echo ""

while [ $ELAPSED -lt $MAX_WAIT ]; do
    if [ -f "$LOG_FILE" ]; then
        # 统计已完成的样本
        COMPLETED=$(grep -c "FRAMES sample=.*success=" "$LOG_FILE" 2>/dev/null || echo "0")
        
        # 查找当前处理的样本
        CURRENT=$(grep "FRAMES sample=" "$LOG_FILE" | tail -1 | grep -o "sample=[0-9]*" | cut -d= -f2 || echo "0")
        
        # 查找两阶段流水线日志
        TWO_STAGE_COUNT=$(grep -c "\[两阶段流水线\]" "$LOG_FILE" 2>/dev/null || echo "0")
        
        echo "[$(date +%H:%M:%S)] 已完成: $COMPLETED/10 | 当前: $CURRENT/10 | 两阶段流水线日志: $TWO_STAGE_COUNT"
        
        if [ "$COMPLETED" -ge 10 ]; then
            echo ""
            echo "✅ 所有样本已完成！"
            break
        fi
    fi
    
    sleep $CHECK_INTERVAL
    ELAPSED=$((ELAPSED + CHECK_INTERVAL))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo ""
    echo "⏰ 达到最大等待时间，停止监控"
fi

