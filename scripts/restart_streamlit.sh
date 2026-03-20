#!/bin/bash
# 重启Streamlit应用的脚本

echo "🔄 重启Streamlit应用..."

# 终止现有进程
pkill -f streamlit
sleep 2

# 清理缓存
rm -f data/learning/llm_cache.json

# 启动新应用
cd /Users/syu/workdata/person/zy/RANGEN-main\(syu-python\)
python -m streamlit run src/apps/knowledge_query_app.py --server.headless true --server.port 8501

echo "✅ 应用重启完成"
