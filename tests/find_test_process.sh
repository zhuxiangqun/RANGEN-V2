#!/bin/bash
# 查找测试进程的简单脚本

echo "🔍 查找测试相关进程..."
echo ""

# 查找包含测试关键词的Python进程
ps aux | grep -i python | grep -E "test|run_optimization|run_all|run_tests|langgraph" | grep -v grep | while read line; do
    PID=$(echo $line | awk '{print $2}')
    CMD=$(echo $line | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
    TIME=$(echo $line | awk '{print $10}')
    echo "  PID: $PID"
    echo "  运行时间: $TIME"
    echo "  命令: $CMD"
    echo ""
done

if [ -z "$(ps aux | grep -i python | grep -E "test|run_optimization|run_all|run_tests|langgraph" | grep -v grep)" ]; then
    echo "✅ 没有发现测试进程"
    echo ""
    echo "💡 如果测试确实在运行，可能是："
    echo "  1. 测试在另一个终端窗口运行"
    echo "  2. 测试进程名称不匹配"
    echo "  3. 测试在后台运行"
    echo ""
    echo "请提供测试启动命令，我可以帮您检查"
fi

