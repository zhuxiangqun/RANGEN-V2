#!/bin/bash
# 测试脚本：使用环境变量运行，避免.env文件访问问题

cd /Users/syu/workdata/person/zy/RANGEN-main\(syu-python\)

# 从.env文件读取API密钥（在沙箱外执行）
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✅ 已加载环境变量"
else
    echo "⚠️ .env文件不存在，请手动设置API密钥"
    # 或者在这里直接设置API密钥
    # export DEEPSEEK_API_KEY="your_api_key_here"
fi

# 激活虚拟环境
source .venv/bin/activate

# 运行对比测试矩阵
echo "🚀 运行对比测试矩阵..."
python diagnostics/contrast_test_matrix.py

# 运行RAGExpert诊断
echo "🔬 运行RAGExpert诊断..."
python diagnostics/rag_expert_diagnosis.py
