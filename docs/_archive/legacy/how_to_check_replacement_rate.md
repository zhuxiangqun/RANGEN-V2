# 如何检查替换比例是否已增加

本文档说明如何检查逐步替换监控中的替换比例是否已经增加。

---

## 🔍 方法1：查看监控日志（推荐）

监控日志会明确记录替换比例的变化。

### 查看最新日志

```bash
# 查看监控日志的最后50行
tail -50 logs/react_agent_replacement*.log

# 实时监控日志（推荐）
tail -f logs/react_agent_replacement*.log
```

### 查找替换比例增加的关键信息

在日志中查找以下关键词：

1. **替换比例增加**：
   ```
   ✅ 替换比例已增加: 1% → 11%
   ```

2. **每次检查的替换比例**：
   ```
   第 X 次检查 (替换比例: 11%)
   ```

3. **当前统计中的替换比例**：
   ```
   📊 当前统计:
      替换比例: 11%
   ```

### 示例日志输出

```
2026-01-01 12:14:14 - 第 1 次检查 (替换比例: 1%)
2026-01-01 12:14:14 - ⏸️  暂不增加替换比例 (需要成功率≥95%且至少100次调用)

2026-01-01 12:16:14 - 第 2 次检查 (替换比例: 1%)
2026-01-01 12:16:14 - ⏸️  暂不增加替换比例 (需要成功率≥95%且至少100次调用)

# 当条件满足时：
2026-01-01 12:18:14 - 第 3 次检查 (替换比例: 1%)
2026-01-01 12:18:14 - ✅ 替换比例已增加: 1% → 11%

2026-01-01 12:20:14 - 第 4 次检查 (替换比例: 11%)
```

---

## 📊 方法2：使用检查脚本

使用专门的检查脚本查看当前替换比例。

### 运行检查命令

```bash
python3 scripts/check_replacement_stats.py --agent ReActAgent
```

### 查看输出中的关键信息

```bash
📊 替换统计:
   当前替换比例: 11%  # ← 这里显示当前替换比例

🎯 建议:
   是否应该增加替换比例: ✅ 是  # ← 如果显示"是"，说明条件满足
```

### 完整输出示例

```
================================================================================
逐步替换统计信息: ReActAgent
================================================================================

📊 替换统计:
   源Agent: ReActAgent
   目标Agent: ReasoningExpert
   当前替换比例: 11%  # ← 如果从1%变成了11%，说明已经增加了

📈 成功率:
   新Agent成功率: 96.50%
   旧Agent成功率: 98.20%

📞 调用统计:
   新Agent总调用数: 150
   旧Agent总调用数: 1350

🎯 建议:
   是否应该增加替换比例: ✅ 是
   是否应该完成替换: ❌ 否
```

---

## 🔎 方法3：查看替换进度日志

替换比例变化会记录在专门的进度日志文件中。

### 查看进度日志

```bash
# 查看替换进度日志
cat logs/replacement_progress_ReActAgent.log

# 或查看最后几行
tail -20 logs/replacement_progress_ReActAgent.log
```

### 日志格式

进度日志是JSON格式，每行一条记录：

```json
{"timestamp": "2026-01-01T12:18:14.123456", "old_agent": "ReActAgent", "new_agent": "ReasoningExpert", "old_rate": 0.01, "new_rate": 0.11, "success_rate": 0.965}
```

### 提取替换比例变化

```bash
# 查看所有替换比例变化
grep "new_rate" logs/replacement_progress_ReActAgent.log | tail -5

# 或使用jq（如果安装了）
cat logs/replacement_progress_ReActAgent.log | jq -r '"\(.timestamp) - 替换比例: \(.old_rate*100)% → \(.new_rate*100)%"'
```

---

## 📈 方法4：对比历史记录

通过对比不同时间的检查结果来判断替换比例是否增加。

### 记录初始状态

```bash
# 第一次检查时记录
python3 scripts/check_replacement_stats.py --agent ReActAgent > initial_state.txt
```

### 后续检查时对比

```bash
# 后续检查
python3 scripts/check_replacement_stats.py --agent ReActAgent > current_state.txt

# 对比替换比例
grep "当前替换比例" initial_state.txt current_state.txt
```

---

## 🎯 替换比例增加的条件

替换比例会在满足以下**所有**条件时自动增加：

1. ✅ **新Agent成功率 ≥ 95%**
2. ✅ **新Agent总调用数 ≥ 100次**
3. ✅ **当前替换比例 < 100%**

### 如何知道条件是否满足

查看监控日志中的提示信息：

- **条件不满足**：
  ```
  ⏸️  暂不增加替换比例 (需要成功率≥95%且至少100次调用)
  ```

- **条件满足，已增加**：
  ```
  ✅ 替换比例已增加: 1% → 11%
  ```

---

## 📝 快速检查命令

创建一个快速检查脚本：

```bash
#!/bin/bash
# 快速检查替换比例

AGENT="ReActAgent"

echo "=========================================="
echo "检查 $AGENT 的替换比例"
echo "=========================================="
echo ""

# 方法1：从监控日志中提取最新替换比例
echo "📊 方法1：从监控日志查看"
LATEST_RATE=$(tail -100 logs/react_agent_replacement*.log 2>/dev/null | grep "替换比例:" | tail -1 | grep -oP '\d+%' | head -1)
if [ -n "$LATEST_RATE" ]; then
    echo "   最新替换比例: $LATEST_RATE"
else
    echo "   未找到替换比例信息"
fi
echo ""

# 方法2：检查是否有替换比例增加的记录
echo "📈 方法2：检查替换比例变化"
RATE_INCREASE=$(tail -100 logs/react_agent_replacement*.log 2>/dev/null | grep "替换比例已增加" | tail -1)
if [ -n "$RATE_INCREASE" ]; then
    echo "   ✅ 发现替换比例增加记录:"
    echo "   $RATE_INCREASE"
else
    echo "   ⏸️  暂无替换比例增加记录"
fi
echo ""

# 方法3：使用检查脚本
echo "🔍 方法3：使用检查脚本"
python3 scripts/check_replacement_stats.py --agent $AGENT 2>/dev/null | grep -A 1 "当前替换比例"
```

---

## ⚠️ 注意事项

1. **替换比例不会立即增加**：需要满足条件后才会增加
2. **检查间隔**：每2分钟检查一次，但替换比例可能不会每次都增加
3. **需要实际调用**：如果系统没有实际运行，不会有调用数据，替换比例不会增加
4. **日志文件位置**：
   - 监控日志：`logs/react_agent_replacement*.log`
   - 进度日志：`logs/replacement_progress_ReActAgent.log`

---

## 🎯 总结

**最简单的方法**：

```bash
# 查看监控日志，查找"替换比例已增加"
tail -50 logs/react_agent_replacement*.log | grep "替换比例已增加"

# 或使用检查脚本查看当前替换比例
python3 scripts/check_replacement_stats.py --agent ReActAgent | grep "当前替换比例"
```

如果看到：
- `✅ 替换比例已增加: X% → Y%` → **已增加**
- `当前替换比例: Y%`（比之前大）→ **已增加**
- `⏸️  暂不增加替换比例` → **尚未增加**（条件未满足）

---

*最后更新: 2026-01-01*

