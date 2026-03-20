#!/bin/bash
# 监控答案传递链路修复效果的脚本

echo "=== 监控答案传递链路修复效果 ==="
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

# 分析结果
echo "=== 修复效果分析 ==="
echo ""

# 1. 准确率对比
echo "1. 准确率对比:"
if [ -f "evaluation_results.json" ]; then
    python3 << 'EOF'
import json
import sys

try:
    with open('evaluation_results.json', 'r') as f:
        data = json.load(f)
    
    if 'frames_accuracy' in data:
        acc = data['frames_accuracy']
        accuracy = acc.get('real_accuracy', 0) * 100
        correct = acc.get('correct_count', 0)
        total = acc.get('total_comparisons', 0)
        
        print(f"  当前准确率: {accuracy:.1f}% ({correct}/{total})")
        print(f"  修复前: 30.0% (3/10)")
        print(f"  变化: {accuracy - 30.0:+.1f}%")
        
        if accuracy > 30.0:
            print(f"  ✅ 准确率提升 {accuracy - 30.0:.1f}%")
        elif accuracy == 30.0:
            print(f"  ⚠️ 准确率未变化")
        else:
            print(f"  ❌ 准确率下降 {30.0 - accuracy:.1f}%")
    
    # 2. unable to determine率
    print("\n2. 'unable to determine'率对比:")
    actual_answers = acc.get('actual_answers', [])
    unable_count = sum(1 for a in actual_answers if 'unable' in str(a).lower())
    unable_rate = unable_count / len(actual_answers) * 100 if actual_answers else 0
    
    print(f"  当前: {unable_rate:.1f}% ({unable_count}/{len(actual_answers)})")
    print(f"  修复前: 10.0% (1/10)")
    print(f"  变化: {unable_rate - 10.0:+.1f}%")
    
    if unable_rate < 10.0:
        print(f"  ✅ unable率降低 {10.0 - unable_rate:.1f}%")
    elif unable_rate == 10.0:
        print(f"  ⚠️ unable率未变化")
    else:
        print(f"  ❌ unable率增加 {unable_rate - 10.0:.1f}%")
    
    # 3. 答案对比
    print("\n3. 答案对比:")
    expected = acc.get('expected_answers', [])
    actual = acc.get('actual_answers', [])
    
    print("  正确答案:")
    correct_count = 0
    for i, (exp, act) in enumerate(zip(expected, actual), 1):
        if exp.lower() == act.lower() or exp.lower() in act.lower() or act.lower() in exp.lower():
            correct_count += 1
            print(f"    {i}. ✅ {exp[:50]} → {act[:50]}")
    
    print(f"\n  错误答案:")
    for i, (exp, act) in enumerate(zip(expected, actual), 1):
        if not (exp.lower() == act.lower() or exp.lower() in act.lower() or act.lower() in exp.lower()):
            status = "❌"
            if 'unable' in str(act).lower():
                status = "⚠️"
            print(f"    {i}. {status} {exp[:50]} → {act[:50]}")
    
    # 4. 检查答案传递链路
    print("\n4. 答案传递链路检查:")
    print("  检查日志中是否有'优先使用推理答案'的记录...")
    
except Exception as e:
    print(f"分析失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF
fi

echo ""
echo "分析完成时间: $(date '+%Y-%m-%d %H:%M:%S')"

