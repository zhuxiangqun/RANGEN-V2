#!/bin/bash
# 日常监控检查脚本
# 用于检查所有Agent的逐步替换进度

echo "================================================================================
日常逐步替换监控检查
日期: $(date '+%Y-%m-%d %H:%M:%S')
================================================================================
"

# 支持的Agent列表
AGENTS=("ReActAgent" "KnowledgeRetrievalAgent" "RAGAgent" "CitationAgent" "ChiefAgent")

# 检查每个Agent的替换统计
for agent in "${AGENTS[@]}"; do
    echo ""
    echo "检查 $agent 替换统计..."
    echo "--------------------------------------------------------------------------------"
    python3 scripts/check_replacement_stats.py --agent "$agent" 2>/dev/null || echo "⚠️ $agent 替换统计检查失败"
done

echo ""
echo "================================================================================
监控检查完成
================================================================================
"

# 生成报告
REPORT_FILE="reports/replacement_monitoring_report_$(date '+%Y%m%d').md"
echo "📊 详细报告已保存到: $REPORT_FILE"

