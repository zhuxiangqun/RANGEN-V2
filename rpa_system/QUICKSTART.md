# RPA系统快速开始指南

## 🚀 快速开始（3步）

### 步骤1: 安装依赖

```bash
# 进入项目根目录
cd /Users/syu/workdata/person/zy/RANGEN-main(syu-python)

# 激活虚拟环境（如果使用）
source .venv/bin/activate

# 安装RPA系统依赖
pip install -r rpa_system/requirements.txt

# 安装浏览器驱动（如果使用浏览器自动化）
brew install chromedriver  # macOS
```

### 步骤2: 启动RPA系统

```bash
# 方式1: Web UI模式（推荐）
python -m rpa_system.main --mode web

# 方式2: CLI模式
python -m rpa_system.main --mode cli --sample-count 10 --timeout 1800
```

### 步骤3: 使用RPA系统

**Web UI模式**：
1. 打开浏览器访问：http://localhost:8888
2. 设置参数（样本数量、超时时间等）
3. 点击"开始运行"
4. 查看报告和结果

**CLI模式**：
- 运行完成后查看报告：`rpa_system/reports/`
- 查看日志：`rpa_system/logs/rpa_system.log`

---

## 📖 详细使用方法

### 方式1: Web UI模式（推荐）⭐

```bash
# 启动Web界面
python -m rpa_system.main --mode web

# 或
python rpa_system/main.py
```

然后打开浏览器访问：http://localhost:8888

**Web界面功能**：
- ✅ 调整运行参数（样本数量、超时时间）
- ✅ 启动/停止运行
- ✅ 实时查看运行状态和日志
- ✅ 查看历史运行报告
- ✅ 查看详细报告内容

### 方式2: CLI模式

```bash
# 命令行模式运行
python -m rpa_system.main --mode cli --sample-count 10 --timeout 1800
```

## 🔄 自动化流程

每次运行会自动执行以下步骤：

1. **检查前端系统** ✅
   - 检查前端目录和文件是否存在
   - 检查Python语法错误
   - 检查依赖是否安装

2. **自动修复问题** 🔧
   - 自动修复语法错误（如果可修复）
   - 自动安装缺失的依赖

3. **运行核心系统** 🚀
   - 使用配置的参数运行核心系统
   - 监控运行状态和日志

4. **运行评测** 📊
   - 执行评测系统
   - 收集评测结果

5. **分析问题** 🔍
   - 分析日志中的错误
   - 分析评测结果
   - 分析性能问题
   - 生成解决方案

6. **生成报告** 📝
   - 生成Markdown格式报告
   - 生成JSON格式报告
   - 保存到 `rpa_system/reports/` 目录

## 📁 输出文件

- **报告文件**: `rpa_system/reports/rpa_report_<run_id>.md`
- **JSON报告**: `rpa_system/reports/rpa_report_<run_id>.json`
- **日志文件**: `rpa_system/logs/rpa_system.log`
- **状态文件**: `rpa_system/state.json`

## ⚙️ 配置

配置文件：`rpa_system/config.py`

主要配置项：
- 核心系统脚本路径
- 评测系统脚本路径
- 前端系统路径
- Web UI端口（默认8888）
- 工作目录和报告目录

## 🎯 使用场景

### 场景1: 持续改进核心系统

1. 启动Web UI
2. 设置样本数量（如10个）
3. 点击"开始运行"
4. 等待运行完成
5. 查看报告，了解问题和解决方案
6. 根据报告调整参数或修复问题
7. 重复步骤3-6，持续改进

### 场景2: 批量测试

1. 使用CLI模式
2. 设置不同的参数组合
3. 批量运行多个测试
4. 对比不同运行的结果

## 🔧 故障排除

### Web UI无法访问

- 检查端口8888是否被占用
- 检查防火墙设置
- 查看日志：`rpa_system/logs/rpa_system.log`

### 运行失败

- 检查核心系统脚本路径是否正确
- 检查日志文件查看详细错误
- 确保有足够的系统资源

### Flask未安装

```bash
pip install flask flask-cors
```

## 📚 更多信息

- **完整运行指南**: `rpa_system/HOW_TO_RUN.md` ⭐ 推荐
- **完整系统文档**: `rpa_system/README.md`
- **前端监控功能**: `rpa_system/FRONTEND_MONITORING.md`
- **前端深度检查**: `rpa_system/FRONTEND_DEEP_CHECK.md`
- **浏览器自动化**: `rpa_system/README_BROWSER_AUTOMATION.md`

