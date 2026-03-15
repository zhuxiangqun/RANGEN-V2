#!/bin/bash

# RANGEN Server 启动脚本 - 确保环境变量正确加载
echo "🔧 Starting RANGEN Server with explicit environment setup..."

# 设置关键环境变量
export DEEPSEEK_API_KEY="sk-0694fb514e114ababb5e0a737a0602a8"
export LLM_PROVIDER="deepseek"
export PYTHONPATH="/Users/apple/workdata/person/zy/RANGEN-main(syu-python)"
export LOG_LEVEL="DEBUG"

echo "🔍 Environment Variables Set:"
echo "  DEEPSEEK_API_KEY: ${DEEPSEEK_API_KEY:0:10}..."
echo "  LLM_PROVIDER: $LLM_PROVIDER"
echo "  PYTHONPATH: $PYTHONPATH"
echo "  LOG_LEVEL: $LOG_LEVEL"

echo ""
echo "🚀 Starting server..."

# 启动服务器
cd "/Users/apple/workdata/person/zy/RANGEN-main(syu-python)"
source .venv/bin/activate

# 记录启动过程
echo "📝 Server startup log:"
python src/api/server.py 2>&1 | tee server_startup.log &

SERVER_PID=$!
echo "✅ Server started with PID: $SERVER_PID"
echo "📋 Logs will be saved to: server_startup.log"

# 等待服务器启动
sleep 20

echo ""
echo "🔍 Checking server health..."
curl -X GET "http://localhost:8000/health" || echo "❌ Health check failed"

echo ""
echo "🏁 Startup script completed. Server PID: $SERVER_PID"