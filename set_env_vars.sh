#!/bin/bash

# 设置环境变量脚本
# 从.env文件加载环境变量到当前shell会话

echo "🔧 设置环境变量..."

# DeepSeek API配置
export DEEPSEEK_API_KEY="sk-0694fb514e114ababb5e0a737a0602a8"
export DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"
export DEEPSEEK_MODEL="deepseek-chat"

# Python路径
export PYTHONPATH="."

echo "✅ 环境变量设置完成"
echo "   DEEPSEEK_API_KEY: ${DEEPSEEK_API_KEY:0:10}..."
echo "   DEEPSEEK_BASE_URL: $DEEPSEEK_BASE_URL"
echo "   DEEPSEEK_MODEL: $DEEPSEEK_MODEL"