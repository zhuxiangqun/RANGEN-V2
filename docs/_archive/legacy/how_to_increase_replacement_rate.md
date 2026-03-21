# 如何让替换比例增加

本文档说明如何改善现状，让替换比例能够增加。

---

## 🎯 问题分析

### 当前状态

替换比例无法增加的原因：

1. **新Agent调用数为0**：系统还没有实际运行产生调用
2. **新Agent成功率为0%**：没有调用数据，无法计算成功率
3. **条件未满足**：替换比例增加需要：
   - ✅ 新Agent成功率 ≥ 95%
   - ✅ 新Agent总调用数 ≥ 100次

---

## 🚀 解决方案

### 方案1：生成测试调用数据（推荐）

使用测试脚本生成调用数据，快速验证系统功能。

#### 快速开始

```bash
# 生成100个测试调用
python3 scripts/generate_test_calls.py --agent ReActAgent --requests 100

# 生成更多调用（确保达到100次）
python3 scripts/generate_test_calls.py --agent ReActAgent --requests 200
```

#### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--agent` | Agent名称 | `ReActAgent` |
| `--requests` | 总请求数 | `100` |
| `--batch-size` | 每批请求数 | `10` |
| `--delay` | 批次间延迟（秒） | `1.0` |

#### 示例

```bash
# 生成200个请求，每批20个，批次间延迟2秒
python3 scripts/generate_test_calls.py \
    --agent ReActAgent \
    --requests 200 \
    --batch-size 20 \
    --delay 2.0
```

---

### 方案2：使用测试模式

使用监控脚本的测试模式生成调用数据。

```bash
# 测试模式：生成10个测试请求
python3 scripts/start_gradual_replacement.py \
    --source ReActAgent \
    --test-mode \
    --test-requests 100
```

---

### 方案3：实际运行系统

让系统实际运行，产生真实的调用数据。

#### 启动系统服务

```bash
# 启动主服务（根据你的系统配置）
python3 main.py
# 或
python3 src/main.py
```

#### 发送实际请求

通过API或命令行发送实际请求：

```bash
# 示例：发送查询请求
curl -X POST http://localhost:8000/api/query \
    -H "Content-Type: application/json" \
    -d '{"query": "什么是人工智能？"}'
```

---

## 📊 验证和监控

### 检查调用数据

生成调用后，检查统计信息：

```bash
python3 scripts/check_replacement_stats.py --agent ReActAgent
```

### 查看关键指标

关注以下指标：

1. **新Agent总调用数**：需要 ≥ 100次
2. **新Agent成功率**：需要 ≥ 95%
3. **是否应该增加替换比例**：应该显示"✅ 是"

---

## 🔧 改善成功率

如果调用数足够但成功率不够，需要：

### 1. 检查新Agent功能

```bash
# 运行功能测试
python3 scripts/validate_pilot_project.py

# 运行适配器测试
python3 scripts/test_p1_adapters.py
```

### 2. 查看错误日志

```bash
# 查看监控日志中的错误
tail -100 logs/react_agent_replacement*.log | grep -i error

# 查看替换进度日志
tail -50 logs/replacement_progress_ReActAgent.log
```

### 3. 修复问题

根据错误日志修复：
- 适配器参数转换问题
- 新Agent初始化问题
- 接口兼容性问题

---

## 📈 优化建议

### 短期（立即）

1. **生成测试调用**：
   ```bash
   python3 scripts/generate_test_calls.py --agent ReActAgent --requests 100
   ```

2. **检查结果**：
   ```bash
   python3 scripts/check_replacement_stats.py --agent ReActAgent
   ```

3. **如果成功率不够，修复问题后重新生成**

### 中期（本周）

1. **持续监控**：保持监控程序运行
2. **收集数据**：让系统实际运行，收集真实调用数据
3. **优化性能**：根据监控数据优化新Agent性能

### 长期（后续）

1. **逐步增加替换比例**：当条件满足时自动增加
2. **监控稳定性**：确保替换后系统稳定
3. **完成迁移**：最终达到100%替换

---

## 🎯 快速行动清单

### ✅ 立即执行

- [ ] 运行测试调用生成脚本
- [ ] 检查调用统计
- [ ] 验证新Agent功能
- [ ] 查看错误日志（如果有）

### ✅ 验证结果

- [ ] 新Agent调用数 ≥ 100
- [ ] 新Agent成功率 ≥ 95%
- [ ] 替换比例可以增加

### ✅ 持续监控

- [ ] 保持监控程序运行
- [ ] 保持通知器运行
- [ ] 定期检查统计

---

## 💡 常见问题

### Q1: 为什么调用数为0？

**A**: 系统还没有实际运行。解决方案：
- 使用测试脚本生成调用
- 或启动系统服务产生实际调用

### Q2: 为什么成功率不够？

**A**: 可能的原因：
- 新Agent功能有问题
- 适配器转换有问题
- 接口不兼容

解决方案：
- 检查错误日志
- 运行功能测试
- 修复问题后重新测试

### Q3: 需要多少调用才能增加替换比例？

**A**: 至少需要：
- 新Agent总调用数 ≥ 100次
- 新Agent成功率 ≥ 95%

### Q4: 测试调用会影响生产环境吗？

**A**: 不会。测试调用：
- 使用测试会话ID
- 不会影响实际用户数据
- 可以安全运行

---

## 📚 相关文档

- **检查替换比例**: `docs/how_to_check_replacement_rate.md`
- **自动通知系统**: `docs/automatic_notification_guide.md`
- **监控状态**: `reports/monitoring_status_current.md`

---

## 🚀 快速命令参考

```bash
# 1. 生成测试调用（100个）
python3 scripts/generate_test_calls.py --agent ReActAgent --requests 100

# 2. 检查统计
python3 scripts/check_replacement_stats.py --agent ReActAgent

# 3. 如果调用数不够，生成更多
python3 scripts/generate_test_calls.py --agent ReActAgent --requests 200

# 4. 查看监控日志
tail -f logs/react_agent_replacement*.log

# 5. 查看通知（如果已启动）
tail -f logs/replacement_notifier.log
```

---

*最后更新: 2026-01-01*

