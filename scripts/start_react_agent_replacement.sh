#!/bin/bash
# 启动ReActAgent逐步替换

set -e

echo "=================================================================================="
echo "ReActAgent逐步替换启动脚本"
echo "=================================================================================="
echo ""

# 步骤1：应用代码替换
echo "步骤1: 应用代码替换（使用包装器）"
echo "--------------------------------------------------------------------------------"
python3 scripts/apply_react_agent_replacement.py --dry-run=false

if [ $? -ne 0 ]; then
    echo "❌ 代码替换失败"
    exit 1
fi

echo ""
echo "✅ 代码替换完成"
echo ""

# 步骤2：启动逐步替换监控
echo "步骤2: 启动逐步替换监控"
echo "--------------------------------------------------------------------------------"
echo "初始替换比例: 1%"
echo "增加步长: 10%"
echo "检查间隔: 2分钟"
echo ""

# 创建日志目录
mkdir -p logs

# 启动监控（后台运行）
# 检查间隔：120秒（2分钟）- 更频繁的检查以便及时发现问题
python3 scripts/start_gradual_replacement.py \
    --source ReActAgent \
    --initial-rate 0.01 \
    --increase-step 0.1 \
    --check-interval 120 > logs/react_agent_replacement.log 2>&1 &

REPLACEMENT_PID=$!
echo "✅ 逐步替换监控已启动 (PID: $REPLACEMENT_PID)"
echo "$REPLACEMENT_PID" > logs/react_agent_replacement_pid.txt
echo ""

# 步骤3：显示监控命令
echo "=================================================================================="
echo "监控命令"
echo "=================================================================================="
echo ""
echo "查看替换统计:"
echo "  python3 scripts/check_replacement_stats.py --agent ReActAgent"
echo ""
echo "查看替换日志:"
echo "  tail -f logs/replacement_progress_ReActAgent.log"
echo ""
echo "查看监控日志:"
echo "  tail -f logs/react_agent_replacement.log"
echo ""
echo "停止监控:"
echo "  kill \$(cat logs/react_agent_replacement_pid.txt)"
echo ""
echo "=================================================================================="
echo "✅ ReActAgent逐步替换已启动"
echo "=================================================================================="

