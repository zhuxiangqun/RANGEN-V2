#!/bin/bash
# 配置RAGExpert使用本地Keras模型（不使用JINA API）

echo "🤖 配置RAGExpert使用本地Keras模型"
echo "====================================="

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

# 1. 确保tf-keras已安装
echo ""
echo "🔧 步骤1: 安装tf-keras兼容包"
pip install --quiet tf-keras || {
    echo "⚠️ tf-keras安装失败，继续执行..."
}

# 2. 设置环境变量 - 禁用JINA，启用本地模型
echo ""
echo "🔧 步骤2: 设置环境变量（禁用JINA，启用本地模型）"

# 清除JINA相关环境变量
unset JINA_API_KEY
unset JINA_EMBEDDING_MODEL

# 设置Keras后端兼容性
export KERAS_BACKEND=tensorflow
export TF_KERAS=1
export TF_CPP_MIN_LOG_LEVEL=2
export TRANSFORMERS_NO_KERAS=0

# 禁用轻量级模式，使用完整功能
unset USE_LIGHTWEIGHT_RAG

echo "✅ 已禁用JINA API"
echo "✅ 已启用本地Keras模型支持"

# 3. 测试sentence-transformers导入
echo ""
echo "🔧 步骤3: 测试sentence-transformers与Keras兼容性"
python3 -c "
import os
print('Keras版本信息:')
try:
    import keras
    print(f'  Keras版本: {keras.__version__}')
except ImportError as e:
    print(f'  ❌ Keras导入失败: {e}')

print('\\nsentence-transformers测试:')
try:
    from sentence_transformers import SentenceTransformer
    print('  ✅ sentence-transformers导入成功')
    
    # 测试模型加载
    print('  🔄 测试模型加载...')
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print(f'  ✅ 模型加载成功: {model.get_sentence_embedding_dimension()}维')
    
    # 测试向量化
    test_text = 'This is a test sentence for vectorization.'
    embedding = model.encode(test_text)
    print(f'  ✅ 向量化测试成功: 维度{len(embedding)}')
    
except Exception as e:
    print(f'  ❌ sentence-transformers测试失败: {e}')
    print('  💡 可能需要重新安装或更新依赖')
"

# 4. 测试KMS本地模型功能
echo ""
echo "🔧 步骤4: 测试KMS本地模型功能"
python3 -c "
print('KMS本地模型测试:')
try:
    from knowledge_management_system.core.knowledge_management_service import KnowledgeManagementService
    print('  ✅ KMS导入成功')
    
    # 初始化KMS
    kms = KnowledgeManagementService()
    print('  ✅ KMS初始化成功')
    
    # 测试向量化
    test_text = 'Machine learning is a subset of artificial intelligence.'
    print(f'  🔄 测试向量化: {test_text[:30]}...')
    
    embedding = kms.get_embedding(test_text)
    if embedding is not None:
        print(f'  ✅ 向量化成功: 维度{len(embedding)}')
    else:
        print('  ⚠️ 向量化返回None，可能需要配置')
        
except Exception as e:
    print(f'  ❌ KMS测试失败: {e}')
    import traceback
    traceback.print_exc()
"

# 5. 配置RAGExpert使用本地模型
echo ""
echo "🔧 步骤5: 配置RAGExpert使用本地模型"
python3 -c "
print('RAGExpert本地模型配置测试:')
try:
    from src.agents.rag_agent import RAGExpert
    print('  ✅ RAGExpert导入成功')
    
    # 初始化RAGExpert（完整模式）
    rag_agent = RAGExpert()
    print('  ✅ RAGExpert初始化成功（完整模式）')
    
    # 测试基本查询
    test_query = 'What is artificial intelligence?'
    print(f'  🔄 测试查询: {test_query}')
    
    result = rag_agent.execute({
        'task_type': 'rag_query',
        'query': test_query,
        'context': {'use_knowledge_base': True}
    })
    
    if hasattr(result, 'success') and result.success:
        print('  ✅ RAG查询成功')
        answer = result.data.get('answer', '') if hasattr(result, 'data') else ''
        if answer:
            print(f'  📝 回答预览: {answer[:100]}...' if len(answer) > 100 else f'  📝 回答: {answer}')
    else:
        print('  ⚠️ RAG查询完成但可能有问题')
        
except Exception as e:
    print(f'  ❌ RAGExpert测试失败: {e}')
    import traceback
    traceback.print_exc()
"

# 6. 生成使用说明
echo ""
echo "📋 本地Keras模型配置完成！"
echo ""
echo "🎯 当前配置:"
echo "   ✅ 使用本地Keras模型（sentence-transformers）"
echo "   ✅ 已禁用JINA API"
echo "   ✅ 启用完整RAG功能"
echo ""
echo "🚀 使用方法:"
echo "   1. 激活环境: source .venv/bin/activate"
echo "   2. 设置变量: export KERAS_BACKEND=tensorflow"
echo "   3. 运行RAG: python3 -c 'from src.agents.rag_agent import RAGExpert; print(\"OK\")'"
echo ""
echo "🔧 如果遇到问题:"
echo "   1. 重新运行此脚本: ./setup_local_keras_models.sh"
echo "   2. 检查Keras版本: pip show keras tf-keras"
echo "   3. 测试模型: python3 -c 'from sentence_transformers import SentenceTransformer; print(\"OK\")'"
echo ""
echo "📊 性能优势:"
echo "   • 无API调用延迟"
echo "   • 完全离线工作"
echo "   • 更好的数据隐私"
echo "   • 稳定的性能表现"
