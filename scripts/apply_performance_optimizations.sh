#!/bin/bash

# 核心系统性能优化脚本（不修改代码）
# 使用方法: source apply_performance_optimizations.sh

echo "🚀 开始应用性能优化配置..."

# ============================================
# 第一步：创建必要的目录
# ============================================
echo ""
echo "📁 创建缓存目录..."
mkdir -p data/learning
chmod 755 data/learning
echo "✅ 缓存目录已创建"

# ============================================
# 第二步：设置环境变量（P0优化）
# ============================================
echo ""
echo "⚙️  设置环境变量（P0优化）..."

# 模型配置
export DEEPSEEK_FAST_MODEL="deepseek-chat"
export DEEPSEEK_MODEL="deepseek-reasoner"

# 并发控制
export MAX_CONCURRENT_QUERIES="1"

# 线程控制
export OMP_NUM_THREADS="1"
export MKL_NUM_THREADS="1"
export NUMEXPR_NUM_THREADS="1"
export JOBLIB_MULTIPROCESSING="0"
export JOBLIB_START_METHOD="threading"

# API调用优化
export LLM_TIMEOUT="30"
export LLM_MAX_RETRIES="2"
export LLM_RETRY_DELAY="1"

# 缓存配置
export EMBEDDING_CACHE_TTL="86400"
export LLM_CACHE_TTL="86400"

# 性能监控
export ENABLE_PERFORMANCE_LOGGING="true"
export LOG_LEVEL="INFO"

echo "✅ 环境变量已设置"

# ============================================
# 第三步：检查缓存文件
# ============================================
echo ""
echo "🔍 检查缓存文件..."
if [ -f "data/learning/llm_cache.json" ]; then
    CACHE_SIZE=$(python3 -c "import json; data=json.load(open('data/learning/llm_cache.json')); print(len(data))" 2>/dev/null || echo "0")
    echo "✅ 缓存文件存在，包含 $CACHE_SIZE 个条目"
else
    echo "⚠️  缓存文件不存在，首次运行时会自动创建"
    echo "   建议先运行一次评估以生成缓存："
    echo "   python -m evaluation.run_unified_evaluation --samples 10"
fi

# ============================================
# 第四步：清理过期缓存（可选）
# ============================================
echo ""
echo "🧹 清理过期缓存..."
python3 << 'EOF'
import json
import time
from pathlib import Path

cache_file = Path('data/learning/llm_cache.json')
if cache_file.exists():
    try:
        with open(cache_file) as f:
            cache = json.load(f)
        
        current_time = time.time()
        ttl = 86400  # 24小时
        valid_cache = {
            k: v for k, v in cache.items()
            if current_time - v.get('timestamp', 0) < ttl
        }
        
        removed = len(cache) - len(valid_cache)
        if removed > 0:
            with open(cache_file, 'w') as f:
                json.dump(valid_cache, f, indent=2)
            print(f"✅ 清理了 {removed} 个过期缓存条目")
            print(f"   剩余缓存条目: {len(valid_cache)}")
        else:
            print(f"✅ 缓存文件有效，包含 {len(valid_cache)} 个条目")
    except Exception as e:
        print(f"⚠️  清理缓存时出错: {e}")
else:
    print("ℹ️  缓存文件不存在，跳过清理")
EOF

# ============================================
# 第五步：检查知识库索引
# ============================================
echo ""
echo "📚 检查知识库索引..."
if [ -f "data/knowledge_graph.db" ]; then
    echo "✅ 知识图谱数据库存在"
else
    echo "⚠️  知识图谱数据库不存在，建议运行："
    echo "   python -m knowledge_management_system.scripts.build_knowledge_graph"
fi

if [ -f "data/vector_knowledge_index.bin" ]; then
    echo "✅ 向量知识库索引存在"
else
    echo "⚠️  向量知识库索引不存在，建议运行："
    echo "   python -m knowledge_management_system.scripts.build_vector_knowledge_base"
fi

# ============================================
# 第六步：显示当前配置
# ============================================
echo ""
echo "📋 当前优化配置："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "模型配置:"
echo "  DEEPSEEK_FAST_MODEL=$DEEPSEEK_FAST_MODEL"
echo "  DEEPSEEK_MODEL=$DEEPSEEK_MODEL"
echo ""
echo "并发控制:"
echo "  MAX_CONCURRENT_QUERIES=$MAX_CONCURRENT_QUERIES"
echo ""
echo "线程控制:"
echo "  OMP_NUM_THREADS=$OMP_NUM_THREADS"
echo "  MKL_NUM_THREADS=$MKL_NUM_THREADS"
echo "  NUMEXPR_NUM_THREADS=$NUMEXPR_NUM_THREADS"
echo ""
echo "API调用:"
echo "  LLM_TIMEOUT=$LLM_TIMEOUT"
echo "  LLM_MAX_RETRIES=$LLM_MAX_RETRIES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ============================================
# 完成
# ============================================
echo ""
echo "✅ 性能优化配置已应用！"
echo ""
echo "📝 下一步："
echo "   1. 如果缓存文件不存在，先运行一次评估以生成缓存："
echo "      python -m evaluation.run_unified_evaluation --samples 10"
echo ""
echo "   2. 运行评估验证性能提升："
echo "      python -m evaluation.run_unified_evaluation --samples 10"
echo ""
echo "   3. 查看性能报告："
echo "      cat evaluation_results/latest_performance_report.json | python3 -m json.tool"
echo ""
echo "📚 详细优化方案请参考："
echo "   comprehensive_eval_results/performance_optimization_without_code_changes.md"
echo ""

