#!/bin/bash
# 监控测试运行并自动验证优化效果

echo "📊 监控测试运行并验证优化效果..."
echo ""

# 等待测试完成
echo "⏳ 等待测试完成..."
while ps aux | grep -E "run_core_with_frames|python.*run_core" | grep -v grep > /dev/null; do
    echo "⏳ 测试进行中... ($(date +%H:%M:%S))"
    sleep 30
done

echo ""
echo "✅ 测试完成！开始验证..."
echo ""

# 激活虚拟环境
source .venv/bin/activate

# 1. 重新生成评测报告
echo "📊 重新生成评测报告..."
cd evaluation_system
python comprehensive_evaluation.py > /dev/null 2>&1
cd ..

# 2. 检查系统健康指标
echo ""
echo "📊 系统健康指标验证："
grep -E "内存使用率|CPU使用率|活跃连接数" comprehensive_eval_results/evaluation_report.md | head -3

# 3. 检查缓存命中率
echo ""
echo "📊 缓存命中率验证："
grep "缓存命中率" comprehensive_eval_results/evaluation_report.md | head -1

# 4. 检查知识检索耗时日志
echo ""
echo "📊 知识检索耗时日志（最新5条）："
grep "知识检索耗时" research_system.log | tail -5 | sed 's/^/  /'

# 5. 检查推理时间
echo ""
echo "📊 推理时间对比："
echo "  当前平均推理时间："
grep "平均推理时间" comprehensive_eval_results/evaluation_report.md | head -1

# 6. 检查缓存文件
echo ""
echo "📊 缓存文件状态："
ls -lh data/learning/*cache.json 2>/dev/null | awk '{print "  "$9": "$5" ("$6" "$7" "$8")"}'

# 7. 检查缓存条目数
echo ""
echo "📊 缓存条目数："
python3 -c "
import json
try:
    with open('data/learning/llm_cache.json') as f:
        llm_cache = json.load(f)
        print(f'  LLM缓存: {len(llm_cache)} 条')
except:
    print('  LLM缓存: 无法读取')

try:
    with open('data/learning/kms_embedding_cache.json') as f:
        kms_cache = json.load(f)
        print(f'  KMS Embedding缓存: {len(kms_cache)} 条')
except:
    print('  KMS Embedding缓存: 无法读取')
"

echo ""
echo "✅ 验证完成！"

