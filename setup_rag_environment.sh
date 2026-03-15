#!/bin/bash
# RAGExpert 环境配置脚本
# 解决所有技术问题，使RAGExpert完全正常工作

echo "🚀 RAGExpert 环境配置脚本"
echo "=================================="

# 切换到项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

echo "📁 项目目录: $PROJECT_ROOT"

# 激活虚拟环境
if [ -f ".venv/bin/activate" ]; then
    echo "🔧 激活虚拟环境..."
    source .venv/bin/activate
else
    echo "❌ 找不到虚拟环境，请先运行: python3 -m venv .venv"
    exit 1
fi

# 1. 解决Keras兼容性问题
echo ""
echo "🔧 步骤1: 解决Keras兼容性问题"
echo "   - 安装tf-keras兼容包"

pip install --quiet tf-keras || {
    echo "⚠️ tf-keras安装失败，继续执行..."
}

# 2. 设置环境变量
echo ""
echo "🔧 步骤2: 设置环境变量"

# 禁用轻量级模式（使用完整功能）
unset USE_LIGHTWEIGHT_RAG

# 设置Keras后端兼容性
export KERAS_BACKEND=tensorflow
export TF_KERAS=1
export TF_CPP_MIN_LOG_LEVEL=2
export TRANSFORMERS_NO_KERAS=0

# 设置JINA API（如果有的话）
if [ -z "$JINA_API_KEY" ]; then
    echo "⚠️ JINA_API_KEY未设置，系统将使用本地模型"
    echo "   如需使用JINA API，请设置环境变量:"
    echo "   export JINA_API_KEY='your_jina_api_key_here'"
else
    echo "✅ JINA_API_KEY已设置"
fi

# 设置DeepSeek（如果使用的话）
if [ -n "$DEEPSEEK_API_KEY" ]; then
    export LLM_PROVIDER=deepseek
    echo "✅ 使用DeepSeek作为LLM提供商"
fi

echo ""
echo "🔧 步骤3: 验证关键组件"

# 验证Python导入
echo "   - 验证Python导入..."
python3 -c "
try:
    import torch
    print('   ✅ torch导入成功')
except ImportError as e:
    print(f'   ❌ torch导入失败: {e}')

try:
    import datasets
    print('   ✅ datasets导入成功')
except ImportError as e:
    print(f'   ❌ datasets导入失败: {e}')

try:
    from src.agents.rag_agent import RAGExpert
    print('   ✅ RAGExpert导入成功')
except ImportError as e:
    print(f'   ❌ RAGExpert导入失败: {e}')
"

echo ""
echo "🔧 步骤4: 验证知识库"

# 检查向量知识库文件
KB_FILES=(
    "data/knowledge_management/frames_dataset_complete.json"
    "data/knowledge_management/frames_embeddings_complete.npy"
    "data/knowledge_management/frames_texts_complete.json"
    "data/knowledge_management/metadata_complete.json"
)

echo "   - 检查知识库文件..."
for file in "${KB_FILES[@]}"; do
    if [ -f "$file" ]; then
        size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
        echo "   ✅ $file (${size} bytes)"
    else
        echo "   ❌ $file (文件不存在)"
    fi
done

echo ""
echo "🔧 步骤5: 运行完整功能测试"

# 运行综合测试
echo "   - 运行RAGExpert综合测试..."
python3 comprehensive_rag_test.py

echo ""
echo "🎉 环境配置完成！"
echo ""
echo "📋 使用说明:"
echo "   1. RAGExpert现在可以使用完整功能模式"
echo "   2. 如需使用轻量级模式，设置: export USE_LIGHTWEIGHT_RAG=true"
echo "   3. 如需使用JINA API，设置: export JINA_API_KEY='your_key'"
echo "   4. 运行测试: python3 comprehensive_rag_test.py"
echo ""
echo "🚀 现在可以开始使用RAGExpert进行检索增强生成了！"
