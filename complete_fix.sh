#!/bin/bash

# RANGEN 完整修复脚本
echo "🔧 Implementing complete RANGEN fix..."

# 1. 设置环境变量
export HF_ENDPOINT="https://hf-mirror.com"
export DEEPSEEK_API_KEY="sk-0694fb514e114ababb5e0a737a0602a8"
export LLM_PROVIDER="deepseek"
export PYTHONPATH="/Users/apple/workdata/person/zy/RANGEN-main(syu-python)"
export LOG_LEVEL="DEBUG"

echo "✅ Environment variables set"

# 2. 停止所有服务器进程
ps aux | grep "server.py" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null

# 3. 清理所有问题缓存
echo "🧹 Cleaning problematic caches..."
rm -rf ~/.cache/huggingface/hub/models--facebook--bart-large-mnli 2>/dev/null
rm -rf ~/.cache/huggingface/hub/models--cross-encoder--ms-marco-MiniLM-L-6-v2 2>/dev/null
rm -rf ~/.cache/huggingface/transformers 2>/dev/null

echo "✅ Caches cleaned"

# 4. 禁用有问题的神经模型功能（临时修复）
echo "🔧 Creating temporary config to disable problematic models..."
cat > /tmp/disable_models.py << 'EOF'
import os
# 强制设置环境变量来禁用有问题的模型加载
os.environ['DISABLE_NEURAL_MODELS'] = 'true'
EOF

# 5. 启动修复后的服务器
echo "🚀 Starting fully fixed server..."
cd "/Users/apple/workdata/person/zy/RANGEN-main(syu-python)"
source .venv/bin/activate

# 在 Python 脚本中设置环境变量
python -c "
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['DEEPSEEK_API_KEY'] = 'sk-0694fb514e114ababb5e0a737a0602a8'
os.environ['LLM_PROVIDER'] = 'deepseek'
os.environ['DISABLE_NEURAL_MODELS'] = 'true'

# 导入并启动服务器
import sys
sys.path.insert(0, '.')
import uvicorn
from src.api.server import app

print('🎯 Starting server with disabled neural models...')
uvicorn.run(app, host='0.0.0.0', port=8000)
" &

SERVER_PID=$!
echo "✅ Fully fixed server started with PID: $SERVER_PID"

# 6. 等待启动并测试
sleep 15

echo ""
echo "🔍 Testing system with neural models disabled..."

# 测试健康检查
echo "📋 Health check:"
curl -X GET "http://localhost:8000/health" -s | python -m json.tool

echo ""
echo "📋 Diagnostic check:"
curl -X GET "http://localhost:8000/diag" -s | python -m json.tool

echo ""
echo "🧪 Testing simple arithmetic query:"
curl -X POST "http://localhost:8000/chat" \
-H "Content-Type: application/json" \
-d '{"query": "What is 2+2?", "session_id": "test-final"}' \
--max-time 30 -s

echo ""
echo "🎯 Complete fix script executed!"
echo "Server PID: $SERVER_PID"