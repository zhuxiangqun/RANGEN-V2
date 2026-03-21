# 自动通知系统使用指南

本文档说明如何使用自动通知系统来接收替换比例变化的通知。

---

## 🎯 功能说明

自动通知系统会：
- ✅ 自动监控替换比例变化
- ✅ 当替换比例增加时自动发送通知
- ✅ 实时显示当前替换比例
- ✅ 记录所有通知历史

---

## 🚀 快速开始

### 启动通知器

```bash
# 方法1：使用启动脚本（推荐）
bash scripts/start_replacement_notifier.sh

# 方法2：直接运行Python脚本
python3 scripts/replacement_rate_notifier.py
```

### 查看通知

通知器会在控制台输出通知信息，例如：

```
============================================================
🎉 替换比例已增加！
============================================================
Agent: ReActAgent → ReasoningExpert
替换比例: 1% → 11%
时间: 2026-01-01 12:20:14
============================================================
```

---

## 📋 使用方法

### 基本用法

```bash
# 使用默认配置（监控 logs/react_agent_replacement.log，每10秒检查一次）
python3 scripts/replacement_rate_notifier.py
```

### 自定义配置

```bash
# 指定日志文件
python3 scripts/replacement_rate_notifier.py \
    --log-file logs/react_agent_replacement.log

# 自定义检查间隔（秒）
python3 scripts/replacement_rate_notifier.py \
    --check-interval 5

# 将通知保存到文件
python3 scripts/replacement_rate_notifier.py \
    --method file
```

### 完整参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--log-file` | 监控日志文件路径 | `logs/react_agent_replacement.log` |
| `--check-interval` | 检查间隔（秒） | `10` |
| `--method` | 通知方式（console/file） | `console` |

---

## 🔧 后台运行

### 使用启动脚本（推荐）

```bash
bash scripts/start_replacement_notifier.sh
```

启动脚本会：
- ✅ 自动检查是否已有通知器运行
- ✅ 在后台启动通知器
- ✅ 保存PID到文件
- ✅ 提供管理命令

### 手动后台运行

```bash
# 后台运行并保存输出到日志
nohup python3 scripts/replacement_rate_notifier.py \
    > logs/replacement_notifier.log 2>&1 &

# 保存PID
echo $! > logs/replacement_notifier.pid
```

---

## 📊 监控命令

### 查看通知器状态

```bash
# 检查进程是否运行
ps aux | grep replacement_rate_notifier | grep -v grep

# 或使用PID文件
ps -p $(cat logs/replacement_notifier.pid)
```

### 查看通知日志

```bash
# 实时查看通知日志
tail -f logs/replacement_notifier.log

# 查看所有通知记录
cat logs/replacement_notifications.log
```

### 停止通知器

```bash
# 方法1：使用PID文件
kill $(cat logs/replacement_notifier.pid)

# 方法2：查找进程并停止
pkill -f replacement_rate_notifier.py
```

---

## 🎨 通知示例

### 控制台通知（console）

当替换比例增加时，会在控制台显示：

```
============================================================
🎉 替换比例已增加！
============================================================
Agent: ReActAgent → ReasoningExpert
替换比例: 1% → 11%
时间: 2026-01-01 12:20:14
============================================================
```

### 文件通知（file）

通知会保存到 `logs/replacement_notifications.log`：

```
============================================================
🎉 替换比例已增加！
============================================================
Agent: ReActAgent → ReasoningExpert
替换比例: 1% → 11%
时间: 2026-01-01 12:20:14
============================================================
```

---

## 🔍 工作原理

1. **监控日志文件**：通知器持续监控监控日志文件的新内容
2. **检测变化**：查找日志中的"替换比例已增加"记录
3. **发送通知**：当检测到变化时，立即发送通知
4. **记录历史**：所有通知都会记录到日志文件

---

## ⚙️ 高级配置

### 与监控程序一起启动

创建一个启动脚本，同时启动监控和通知器：

```bash
#!/bin/bash
# 同时启动监控和通知器

# 启动监控
bash scripts/start_react_agent_monitoring.sh

# 等待2秒
sleep 2

# 启动通知器
bash scripts/start_replacement_notifier.sh

echo "✅ 监控和通知器已启动"
```

### 集成到系统服务

可以将通知器配置为系统服务（systemd），实现开机自启动。

---

## 📝 注意事项

1. **日志文件路径**：确保监控日志文件路径正确
2. **检查间隔**：建议设置为10秒，不要太频繁
3. **后台运行**：如果要在后台运行，使用启动脚本或nohup
4. **日志轮转**：如果日志文件被轮转，通知器会自动适应

---

## 🐛 故障排除

### 问题1：通知器无法启动

**症状**：启动失败或立即退出

**解决方案**：
1. 检查Python版本：`python3 --version`
2. 检查日志文件是否存在
3. 查看错误日志：`cat logs/replacement_notifier.log`

### 问题2：收不到通知

**症状**：替换比例已增加但没有通知

**解决方案**：
1. 检查通知器是否运行：`ps aux | grep replacement_rate_notifier`
2. 检查日志文件路径是否正确
3. 查看通知器日志：`tail -f logs/replacement_notifier.log`

### 问题3：通知延迟

**症状**：替换比例增加后很久才收到通知

**解决方案**：
1. 减小检查间隔：`--check-interval 5`
2. 检查系统负载
3. 确保日志文件可读

---

## 📚 相关文档

- **检查替换比例指南**: `docs/how_to_check_replacement_rate.md`
- **监控状态报告**: `reports/monitoring_status_current.md`
- **迁移实施日志**: `docs/migration_implementation_log.md`

---

*最后更新: 2026-01-01*

