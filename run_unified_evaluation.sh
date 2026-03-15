#!/bin/bash

# 统一异步评测启动脚本
# 使用新的异步架构，解决评测卡顿问题

echo "🚀 启动统一异步评测系统..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装或不在PATH中"
    exit 1
fi

# 检查虚拟环境
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  警告: 未检测到虚拟环境，建议在venv中运行"
    read -p "是否继续？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "退出"
        exit 1
    fi
fi

# 检查依赖
echo "🔍 检查系统依赖..."
python3 -c "
import asyncio
import logging
import json
import time
from pathlib import Path
print('✅ 基础依赖检查通过')
" 2>/dev/null || {
    echo "❌ 基础依赖检查失败"
    exit 1
}

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p logs
mkdir -p evaluation_results
mkdir -p data

# 设置环境变量
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export PYTHONUNBUFFERED=1

# 运行评测
echo "🎯 开始运行统一异步评测..."
echo "⏰ 开始时间: $(date)"

# 设置超时（防止无限运行）
TIMEOUT=300  # 5分钟超时

timeout $TIMEOUT python3 scripts/unified_async_evaluation.py

EXIT_CODE=$?

echo "⏰ 结束时间: $(date)"

# 检查结果
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ 评测成功完成"
    
    # 查找最新的结果文件
    LATEST_RESULT=$(find evaluation_results -name "unified_async_evaluation_*.json" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -f2- -d" ")
    
    if [ -n "$LATEST_RESULT" ]; then
        echo "📊 最新结果文件: $LATEST_RESULT"
        
        # 显示结果摘要
        echo "📈 结果摘要:"
        python3 -c "
import json
import sys
try:
    with open('$LATEST_RESULT', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f'   总查询数: {data.get(\"total_queries\", 0)}')
    print(f'   成功数: {data.get(\"total_successful\", 0)}')
    print(f'   成功率: {data.get(\"overall_success_rate\", 0):.2%}')
    print(f'   系统架构: {data.get(\"system_info\", {}).get(\"async_architecture\", \"unknown\")}')
except Exception as e:
    print(f'   无法读取结果文件: {e}')
"
    fi
    
elif [ $EXIT_CODE -eq 124 ]; then
    echo "⏰ 评测超时 (${TIMEOUT}秒)"
    echo "💡 建议: 检查是否有阻塞操作或增加超时时间"
elif [ $EXIT_CODE -eq 130 ]; then
    echo "⚠️  评测被用户中断"
else
    echo "❌ 评测失败 (退出码: $EXIT_CODE)"
    echo "💡 建议: 检查日志文件了解详细错误信息"
fi

# 显示日志文件
echo "📋 日志文件:"
find logs -name "unified_async_evaluation_*.log" -type f -printf '%T@ %p\n' | sort -n | tail -3 | cut -f2- -d" " | while read logfile; do
    echo "   $logfile"
done

echo "🎉 统一异步评测脚本执行完成"
