#!/bin/bash
# DeepSeek专用配置脚本
# 确保系统只使用DeepSeek，不使用OpenAI

echo "🚀 配置系统为仅使用DeepSeek"
echo "=============================="

# 设置环境变量
export LLM_PROVIDER=deepseek
export DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-"your_deepseek_api_key_here"}"
unset OPENAI_API_KEY 2>/dev/null || true

echo "✅ LLM_PROVIDER=deepseek"
echo "✅ DEEPSEEK_API_KEY=已设置"
echo "✅ OPENAI_API_KEY=已清除"

echo ""
echo "🧪 验证配置:"
source .venv/bin/activate && python3 -c "
import os
import sys
sys.path.insert(0, '.')

print('🔍 DeepSeek专用配置验证:')
llm_provider = os.getenv('LLM_PROVIDER', 'deepseek')
deepseek_key = os.getenv('DEEPSEEK_API_KEY')
openai_key = os.getenv('OPENAI_API_KEY')

print(f'LLM提供商: {llm_provider}')
print(f'DeepSeek密钥: {\"已设置\" if deepseek_key and deepseek_key != \"your_deepseek_api_key_here\" else \"需要真实密钥\"}')
print(f'OpenAI密钥: {\"已清除\" if not openai_key else \"仍存在\"}')

if llm_provider == 'deepseek':
    print('✅ 配置正确：系统将仅使用DeepSeek')
else:
    print('❌ 配置错误：请检查LLM_PROVIDER设置')
"
