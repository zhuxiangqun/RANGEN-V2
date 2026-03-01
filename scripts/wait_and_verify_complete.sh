#!/bin/bash
# 等待测试完成并运行完整验证

echo "⏳ 等待当前测试完成..."
echo ""

# 等待测试完成
while ps aux | grep -E "run_core_with_frames|python.*run_core" | grep -v grep > /dev/null; do
    echo "⏳ 测试进行中... ($(date +%H:%M:%S))"
    sleep 15
done

echo ""
echo "✅ 测试完成！"
echo ""
echo "📊 开始完整验证..."
echo ""

cd /Users/syu/workdata/person/zy/RANGEN-main\(syu-python\)
source .venv/bin/activate

# 1. 验证Embedding缓存
echo "=" * 60
echo "1. Embedding缓存验证"
echo "=" * 60
python scripts/verify_embedding_cache.py

echo ""
echo "=" * 60
echo "2. 检查缓存文件"
echo "=" * 60
if [ -f "data/learning/embedding_cache.json" ]; then
    echo "✅ Embedding缓存文件存在"
    ls -lh data/learning/embedding_cache.json
    echo ""
    echo "缓存条目数:"
    python3 -c "import json; data = json.load(open('data/learning/embedding_cache.json')); print(f'  {len(data)} 条')"
else
    echo "⏸️  Embedding缓存文件尚未创建（首次运行正常）"
fi

if [ -f "data/learning/llm_cache.json" ]; then
    echo ""
    echo "✅ LLM缓存文件存在"
    ls -lh data/learning/llm_cache.json
    echo ""
    echo "缓存条目数:"
    python3 -c "import json; data = json.load(open('data/learning/llm_cache.json')); print(f'  {len(data)} 条')"
else
    echo ""
    echo "⏸️  LLM缓存文件尚未创建"
fi

echo ""
echo "=" * 60
echo "3. 检查日志中的关键信息"
echo "=" * 60
echo ""
echo "缓存相关日志（最后20条）:"
grep -E "缓存|Embedding缓存|证据收集" research_system.log | tail -20 || echo "未找到相关日志"

echo ""
echo "=" * 60
echo "4. 检查评测报告"
echo "=" * 60
if [ -f "comprehensive_eval_results/evaluation_report.md" ]; then
    echo "✅ 评测报告已生成"
    echo ""
    echo "关键指标："
    grep -E "平均推理时间|缓存命中率|证据收集|平均处理时间" comprehensive_eval_results/evaluation_report.md | head -10
else
    echo "⏸️  评测报告尚未生成"
fi

echo ""
echo "=" * 60
echo "验证完成"
echo "=" * 60

