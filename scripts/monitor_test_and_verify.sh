#!/bin/bash
# 监控测试进度并在完成后验证结果

echo "⏳ 等待测试完成..."
echo ""

# 等待测试完成
while ps aux | grep -E "run_core_with_frames|python.*run_core" | grep -v grep > /dev/null; do
    echo "⏳ 测试进行中... ($(date +%H:%M:%S))"
    sleep 15
done

echo ""
echo "✅ 测试完成！"
echo ""
echo "📊 开始验证Embedding缓存优化效果..."
echo ""

# 运行验证脚本
cd /Users/syu/workdata/person/zy/RANGEN-main\(syu-python\)
source .venv/bin/activate
python scripts/verify_embedding_cache.py

echo ""
echo "📊 检查评测报告..."
if [ -f "comprehensive_eval_results/evaluation_report.md" ]; then
    echo "✅ 评测报告已生成"
    echo ""
    echo "关键指标："
    grep -E "平均推理时间|缓存命中率|证据收集" comprehensive_eval_results/evaluation_report.md | head -5
else
    echo "⏸️  评测报告尚未生成"
fi

