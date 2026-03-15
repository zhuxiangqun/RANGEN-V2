#!/bin/bash

# RANGEN 修复脚本 - 解决 HuggingFace 连接问题
echo "🔧 Fixing RANGEN HuggingFace connection issues..."

# 设置环境变量以使用镜像
export HF_ENDPOINT="https://hf-mirror.com"
export DEEPSEEK_API_KEY="sk-0694fb514e114ababb5e0a737a0602a8"
export LLM_PROVIDER="deepseek"
export PYTHONPATH="/Users/apple/workdata/person/zy/RANGEN-main(syu-python)"
export LOG_LEVEL="DEBUG"

echo "✅ Environment configured with HF mirror"

# 停止现有服务器
ps aux | grep "server.py" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null

echo "🧹 Cleaning up any problematic model cache..."
# 删除可能损坏的模型缓存
rm -rf ~/.cache/huggingface/hub/models--facebook--bart-large-mnli 2>/dev/null
rm -rf ~/.cache/huggingface/hub/models--cross-encoder--ms-marco-MiniLM-L-6-v2 2>/dev/null

echo "✅ Cache cleaned"

# 启动修复后的服务器
echo "🚀 Starting fixed server..."
cd "/Users/apple/workdata/person/zy/RANGEN-main(syu-python)"
source .venv/bin/activate

# 使用 hf-mirror 启动
python src/api/server.py &

SERVER_PID=$!
echo "✅ Fixed server started with PID: $SERVER_PID"

# 等待启动
sleep 10

# 测试健康检查
echo "🔍 Testing health endpoint..."
curl -X GET "http://localhost:8000/health"

# 测试诊断端点
echo ""
echo "🔍 Testing diagnostic endpoint..."
curl -X GET "http://localhost:8000/diag" | python -m json.tool

# 测试简单查询
echo ""
echo "🧪 Testing simple query..."
curl -X POST "http://localhost:8000/chat" \
-H "Content-Type: application/json" \
-d '{"query": "What is 2+2?", "session_id": "test-fixed"}' \
--max-time 30

echo ""
echo "🎯 Fix script completed!"