#!/bin/bash
# 监控长文本答案修复效果的脚本

echo "=== 监控长文本答案修复效果 ==="
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 等待评测完成
while pgrep -f "run_core_with_frames" > /dev/null; do
    echo "等待评测完成... ($(date '+%H:%M:%S'))"
    sleep 60
done

echo ""
echo "评测完成！开始分析..."
echo ""

# 分析长文本答案
echo "=== 长文本答案分析 ==="
echo ""

# 查找长文本答案（长度>20字符）
echo "1. 长文本答案（长度>20字符）:"
grep -E "系统答案: " research_system.log | grep -v "unable to determine" | awk -F"系统答案: " '{print $2}' | awk 'length($0) > 20' | head -10

echo ""
echo "2. 长文本答案丢失情况:"
grep -E "期望答案:.*[A-Z].*\." evaluation_results.json 2>/dev/null | head -5
grep -E "系统答案: unable" research_system.log | wc -l | xargs echo "unable to determine 数量:"

echo ""
echo "3. 关键指标:"
if [ -f "evaluation_results.json" ]; then
    python3 << 'EOF'
import json
import sys

try:
    with open('evaluation_results.json', 'r') as f:
        data = json.load(f)
    
    # 提取关键指标
    if 'frames_accuracy' in data:
        acc = data['frames_accuracy']
        print(f"准确率: {acc.get('real_accuracy', 0) * 100:.1f}%")
        print(f"正确数量: {acc.get('correct_count', 0)}/{acc.get('total_comparisons', 0)}")
        
        # 统计unable to determine
        actual_answers = acc.get('actual_answers', [])
        unable_count = sum(1 for a in actual_answers if 'unable' in str(a).lower())
        print(f"unable to determine 数量: {unable_count}/{len(actual_answers)}")
        print(f"unable to determine 率: {unable_count/len(actual_answers)*100:.1f}%")
    
    if 'reasoning_efficiency' in data:
        eff = data['reasoning_efficiency']
        time_stats = eff.get('time_stats', {})
        print(f"平均推理时间: {time_stats.get('average', 0):.2f}秒")
        
except Exception as e:
    print(f"分析失败: {e}")
    sys.exit(1)
EOF
fi

echo ""
echo "分析完成时间: $(date '+%Y-%m-%d %H:%M:%S')"

