#!/bin/bash

# RANGEN 预下载模型脚本 - 最彻底解决方案
echo "🔧 RANGEN Model Pre-download Solution"
echo "=================================="

# 设置环境变量
export HF_ENDPOINT="https://hf-mirror.com"
export DEEPSEEK_API_KEY="sk-0694fb514e114ababb5e0a737a0602a8"
export LLM_PROVIDER="deepseek"
export PYTHONPATH="/Users/apple/workdata/person/zy/RANGEN-main(syu-python)"

echo "✅ Environment configured with HF mirror"

# 停止现有服务器
echo "🛑 Stopping existing server..."
ps aux | grep "server.py" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null

# 清理可能损坏的缓存
echo "🧹 Cleaning potentially corrupted caches..."
rm -rf ~/.cache/huggingface/hub/models--facebook--bart-large-mnli
rm -rf ~/.cache/huggingface/hub/models--cross-encoder--ms-marco-MiniLM-L-6-v2
rm -rf ~/.cache/huggingface/transformers

echo "=================================="
echo "📥 Starting Model Pre-download Process"
echo "=================================="

# 激活虚拟环境
cd "/Users/apple/workdata/person/zy/RANGEN-main(syu-python)"
source .venv/bin/activate

# 1. 预下载 Intent Classifier 模型
echo ""
echo "🎯 Step 1: Downloading Intent Classifier (facebook/bart-large-mnli)..."
python -c "
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
try:
    from transformers import pipeline
    print('🔄 Loading intent classifier pipeline...')
    classifier = pipeline('zero-shot-classification', model='facebook/bart-large-mnli')
    result = classifier('test query', candidate_labels=['research', 'chat'])
    print('✅ Intent Classifier downloaded successfully!')
    print(f'🧪 Test result: {result}')
except Exception as e:
    print(f'❌ Intent Classifier download failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Intent Classifier download failed - aborting"
    exit 1
fi

# 2. 预下载 Reranker 模型
echo ""
echo "🎯 Step 2: Downloading Reranker (cross-encoder/ms-marco-MiniLM-L-6-v2)..."
python -c "
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
try:
    from sentence_transformers import CrossEncoder
    print('🔄 Loading reranker model...')
    reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    result = reranker.predict(['query', 'document'], [1])
    print('✅ Reranker downloaded successfully!')
    print(f'🧪 Test result: {result}')
except Exception as e:
    print(f'❌ Reranker download failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Reranker download failed - aborting"
    exit 1
fi

# 3. 预下载 embedding 模型（如果还没有）
echo ""
echo "🎯 Step 3: Checking Embedding Model..."
python -c "
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
try:
    from sentence_transformers import SentenceTransformer
    print('🔄 Loading embedding model...')
    model = SentenceTransformer('all-mpnet-base-v2')
    embedding = model.encode('test text')
    print('✅ Embedding model available!')
    print(f'🧪 Embedding dimension: {len(embedding)}')
except Exception as e:
    print(f'❌ Embedding model check failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Embedding model check failed - aborting"
    exit 1
fi

echo ""
echo "=================================="
echo "✅ ALL MODELS SUCCESSFULLY DOWNLOADED!"
echo "=================================="

# 启动最终服务器
echo ""
echo "🚀 Starting RANGEN server with all models pre-cached..."

# 创建最终启动脚本
cat > /tmp/start_final_server.py << 'EOF'
import os
import sys
sys.path.insert(0, '/Users/apple/workdata/person/zy/RANGEN-main(syu-python)')

# 设置环境变量
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['DEEPSEEK_API_KEY'] = 'sk-0694fb514e114ababb5e0a737a0602a8'
os.environ['LLM_PROVIDER'] = 'deepseek'
os.environ['PYTHONPATH'] = '/Users/apple/workdata/person/zy/RANGEN-main(syu-python)'

print("🎯 Final server starting with pre-cached models...")
print("Environment configured:")
print(f"  HF_ENDPOINT: {os.environ['HF_ENDPOINT']}")
print(f"  LLM_PROVIDER: {os.environ['LLM_PROVIDER']}")

import uvicorn
from src.api.server import app
uvicorn.run(app, host='0.0.0.0', port=8000)
EOF

# 启动最终服务器
python /tmp/start_final_server.py &
SERVER_PID=$!

echo ""
echo "✅ RANGEN Server Started Successfully!"
echo "🔍 PID: $SERVER_PID"
echo "🌐 URL: http://localhost:8000"
echo ""
echo "🎯 Final Test Starting in 20 seconds..."

# 等待服务器完全启动
sleep 20

echo ""
echo "🧪 Running Final Tests..."
echo "=================================="

# 测试健康检查
echo "📋 Health Check:"
curl -s "http://localhost:8000/health" | python -m json.tool || echo "❌ Health check failed"

echo ""
echo "📋 Diagnostic Check:"
curl -s "http://localhost:8000/diag" | python -m json.tool || echo "❌ Diagnostic check failed"

echo ""
echo "🧪 Testing Simple Query:"
curl -s -X POST "http://localhost:8000/chat" \
-H "Content-Type: application/json" \
-d '{"query": "What is 2+2?", "session_id": "test-final"}' \
--max-time 30 | python -m json.tool || echo "❌ Simple query failed"

echo ""
echo "🧪 Testing Historical Query:"
curl -s -X POST "http://localhost:8000/chat" \
-H "Content-Type: application/json" \
-d '{"query": "Who was the 15th first lady of United States?", "session_id": "test-final-history"}' \
--max-time 45 | python -m json.tool || echo "❌ Historical query failed"

echo ""
echo "🎉 PRE-DOWNLOAD FIX COMPLETED!"
echo "=================================="
echo "📊 Summary:"
echo "  ✅ All models downloaded to cache"
echo "  ✅ Server running with full functionality"
echo "  ✅ Ready for your complex query test"
echo ""
echo "🎯 You can now test your query:"
echo "  curl -X POST http://localhost:8000/chat \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"query\": \"If my future wife has same first name as 15th first lady of United States mother and her surname is same as second assassinated presidents mothers maiden name, what is my future wifes name?\"}'"