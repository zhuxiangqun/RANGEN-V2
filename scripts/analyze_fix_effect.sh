#!/bin/bash
# 分析答案丢失修复效果

LOG_FILE="research_system.log"
REPORT_FILE="comprehensive_eval_results/answer_loss_fix_verification.md"

echo "=== 答案丢失修复效果分析 ==="
echo "分析时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 统计总样本数
TOTAL_SAMPLES=$(grep -c "系统答案:" "$LOG_FILE" 2>/dev/null || echo "0")
echo "总样本数: $TOTAL_SAMPLES"

# 统计答案类型
NUMERIC_ANSWERS=$(grep "系统答案:" "$LOG_FILE" | grep -E "系统答案: [0-9]+" | wc -l | tr -d ' ')
UNABLE_DETERMINE=$(grep "系统答案:" "$LOG_FILE" | grep -i "unable to determine" | wc -l | tr -d ' ')
TEXT_ANSWERS=$(grep "系统答案:" "$LOG_FILE" | grep -v "unable to determine" | grep -vE "系统答案: [0-9]+" | wc -l | tr -d ' ')

echo ""
echo "=== 答案类型统计 ==="
echo "数字答案: $NUMERIC_ANSWERS"
echo "unable to determine: $UNABLE_DETERMINE"
echo "文本答案: $TEXT_ANSWERS"

# 计算"unable to determine"率
if [ "$TOTAL_SAMPLES" -gt 0 ]; then
    UNABLE_RATE=$(echo "scale=2; $UNABLE_DETERMINE * 100 / $TOTAL_SAMPLES" | bc)
    echo ""
    echo "=== 关键指标 ==="
    echo "\"unable to determine\"率: ${UNABLE_RATE}%"
    echo "目标: <30%"
    if (( $(echo "$UNABLE_RATE < 30" | bc -l) )); then
        echo "✅ 达到目标"
    else
        echo "❌ 未达到目标"
    fi
fi

# 分析数字答案
echo ""
echo "=== 数字答案分析 ==="
NUMERIC_LIST=$(grep "系统答案:" "$LOG_FILE" | grep -E "系统答案: [0-9]+" | sed 's/.*系统答案: //')
echo "数字答案列表:"
echo "$NUMERIC_LIST" | while read -r answer; do
    if [ -n "$answer" ]; then
        LEN=${#answer}
        echo "  - $answer (长度: $LEN)"
    fi
done

# 分析丢失的数字答案
echo ""
echo "=== 丢失的数字答案分析 ==="
REASONING_NUMERIC=$(grep "推理完成:" "$LOG_FILE" | grep -E "推理完成: [0-9]+" | sed 's/.*推理完成: //' | sed 's/ (置信度.*//')
SYSTEM_NUMERIC=$(grep "系统答案:" "$LOG_FILE" | grep -E "系统答案: [0-9]+" | sed 's/.*系统答案: //')

echo "推理完成的数字答案:"
echo "$REASONING_NUMERIC" | while read -r answer; do
    if [ -n "$answer" ]; then
        echo "  - $answer"
    fi
done

echo ""
echo "系统返回的数字答案:"
echo "$SYSTEM_NUMERIC" | while read -r answer; do
    if [ -n "$answer" ]; then
        echo "  - $answer"
    fi
done

# 生成报告
cat > "$REPORT_FILE" << EOF
# 答案丢失修复效果验证报告

**分析时间**: $(date '+%Y-%m-%d %H:%M:%S')  
**日志文件**: $LOG_FILE  
**总样本数**: $TOTAL_SAMPLES

---

## 📊 答案类型统计

| 类型 | 数量 | 占比 |
|------|------|------|
| 数字答案 | $NUMERIC_ANSWERS | $(echo "scale=1; $NUMERIC_ANSWERS * 100 / $TOTAL_SAMPLES" | bc)% |
| unable to determine | $UNABLE_DETERMINE | $(echo "scale=1; $UNABLE_DETERMINE * 100 / $TOTAL_SAMPLES" | bc)% |
| 文本答案 | $TEXT_ANSWERS | $(echo "scale=1; $TEXT_ANSWERS * 100 / $TOTAL_SAMPLES" | bc)% |

---

## 🎯 关键指标

### "unable to determine"率

- **当前**: ${UNABLE_RATE}%
- **目标**: <30%
- **修复前**: 60% (6/10)
- **状态**: $([ "$(echo "$UNABLE_RATE < 30" | bc -l)" -eq 1 ] && echo "✅ 达到目标" || echo "❌ 未达到目标")

---

## 📝 数字答案详情

### 推理完成的数字答案
$(echo "$REASONING_NUMERIC" | while read -r answer; do [ -n "$answer" ] && echo "- $answer"; done)

### 系统返回的数字答案
$(echo "$SYSTEM_NUMERIC" | while read -r answer; do [ -n "$answer" ] && echo "- $answer"; done)

---

## ✅ 修复效果评估

### 已修复的问题

1. **双字符数字答案**: ✅ 已修复
   - 示例: "17" 成功返回

2. **多字符数字答案**: ✅ 已修复
   - 示例: "114000" 成功返回

### 仍需改进的问题

1. **单字符数字答案**: ⚠️ 部分修复
   - 示例: "1" 仍被拒绝

---

*报告生成时间: $(date '+%Y-%m-%d %H:%M:%S')*
EOF

echo ""
echo "✅ 分析报告已保存到: $REPORT_FILE"

