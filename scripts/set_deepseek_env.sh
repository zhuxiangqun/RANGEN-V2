#!/bin/bash
# DeepSeek环境变量设置脚本

echo "🚀 设置DeepSeek环境变量"

# 设置环境变量
export LLM_PROVIDER=deepseek
export DEEPSEEK_API_KEY="sk-0694f1e16d644c6db1b85b0d7e8a9d1a"
unset OPENAI_API_KEY 2>/dev/null || true

echo "✅ 环境变量已设置:"
echo "   LLM_PROVIDER=deepseek"
echo "   DEEPSEEK_API_KEY=已设置"
echo "   OPENAI_API_KEY=已清除"

# 验证设置
echo ""
echo "🔍 验证环境变量:"
python3 -c "
import os
print(f'LLM_PROVIDER: {os.getenv(\"LLM_PROVIDER\", \"未设置\")}')
print(f'DEEPSEEK_API_KEY: {\"已设置\" if os.getenv(\"DEEPSEEK_API_KEY\") else \"未设置\"}')
print(f'OPENAI_API_KEY: {\"已设置\" if os.getenv(\"OPENAI_API_KEY\") else \"未设置\"}')
"
