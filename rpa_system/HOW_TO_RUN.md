# RPA系统运行指南

## 📋 前置条件

### 1. 安装Python依赖

```bash
# 进入项目根目录
cd /Users/syu/workdata/person/zy/RANGEN-main(syu-python)

# 激活虚拟环境（如果使用）
source .venv/bin/activate

# 安装RPA系统依赖
pip install -r rpa_system/requirements.txt
```

### 2. 安装浏览器驱动（如果使用浏览器自动化）

```bash
# macOS
brew install chromedriver

# 或手动下载Chrome驱动
# https://chromedriver.chromium.org/downloads
# 确保Chrome驱动版本与Chrome浏览器版本匹配
```

### 3. 启动前端系统（可选，如果使用前端自动化）

**终端1 - 启动前端后端**：
```bash
cd frontend_monitor/backend
python app.py
```

**终端2 - 启动前端前端**：
```bash
cd frontend_monitor
npm run dev
```

前端系统应该运行在：http://localhost:5173

---

## 🚀 运行方式

### 方式1: Web UI模式（推荐）⭐

**优点**：
- 可视化界面，操作简单
- 实时查看运行状态和日志
- 支持动态调整参数
- 支持查看历史报告

**启动命令**：
```bash
# 方式1: 使用模块方式运行
python -m rpa_system.main --mode web

# 方式2: 直接运行主程序
python rpa_system/main.py

# 方式3: 指定端口（如果需要）
RPA_UI_PORT=9999 python -m rpa_system.main --mode web
```

**访问地址**：
- 默认：http://localhost:8888
- 或：http://127.0.0.1:8888

**使用步骤**：
1. 打开浏览器访问 http://localhost:8888
2. 在Web界面中：
   - 设置样本数量（如10）
   - 设置超时时间（如1800秒）
   - 勾选"使用前端自动化"（如果需要）
   - 勾选"无头模式"（如果不显示浏览器窗口）
3. 点击"开始运行"按钮
4. 等待运行完成
5. 查看报告和结果

### 方式2: CLI模式（命令行）

**优点**：
- 适合脚本化和自动化
- 适合批量测试
- 资源占用更少

**启动命令**：
```bash
# 基本用法
python -m rpa_system.main --mode cli --sample-count 10 --timeout 1800

# 参数说明
# --mode cli: 使用命令行模式
# --sample-count 10: 样本数量为10
# --timeout 1800: 超时时间为1800秒（30分钟）

# 示例：运行20个样本，超时1小时
python -m rpa_system.main --mode cli --sample-count 20 --timeout 3600
```

**输出**：
- 运行过程会输出到控制台
- 报告保存在 `rpa_system/reports/` 目录
- 日志保存在 `rpa_system/logs/rpa_system.log`

---

## 🔄 运行流程

无论使用哪种模式，RPA系统都会自动执行以下步骤：

```
1. 检查前端系统 ✅
   ├── 检查目录和文件是否存在
   ├── 检查Python语法错误
   ├── 检查依赖是否安装
   ├── 检查服务是否运行
   └── 深度页面检查（如果启用）

2. 自动修复问题 🔧
   ├── 自动安装缺失的依赖
   └── 提供修复建议

3. 运行核心系统 🚀
   ├── 方式A: 通过前端自动化（如果启用）
   │   ├── 自动打开前端页面
   │   ├── 自动设置样本数量
   │   ├── 自动点击"运行核心系统"按钮
   │   └── 等待执行完成
   └── 方式B: 直接运行（如果不使用前端自动化）
       └── 直接调用核心系统脚本

4. 运行评测 📊
   ├── 方式A: 通过前端自动化（如果启用）
   │   ├── 自动点击"运行评测系统"按钮
   │   └── 等待评测完成
   └── 方式B: 直接运行（如果不使用前端自动化）
       └── 直接调用评测系统脚本

5. 分析问题 🔍
   ├── 分析日志中的错误
   ├── 分析评测结果
   ├── 分析性能问题
   └── 生成解决方案

6. 生成改进方案 🔧
   ├── 根据分析结果生成改进建议
   └── 提供具体的改进方案

7. 生成报告 📝
   ├── 生成Markdown格式报告
   ├── 生成JSON格式报告
   └── 保存到 reports 目录
```

---

## 📁 输出文件

运行完成后，会在以下位置生成文件：

### 报告文件
- **Markdown报告**: `rpa_system/reports/rpa_report_<run_id>.md`
- **JSON报告**: `rpa_system/reports/rpa_report_<run_id>.json`

### 日志文件
- **系统日志**: `rpa_system/logs/rpa_system.log`

### 状态文件
- **运行状态**: `rpa_system/state.json`

### 截图文件（如果使用前端自动化）
- **截图目录**: `rpa_system/work/screenshots/`

---

## ⚙️ 配置选项

### 环境变量

```bash
# 前端系统URL
export FRONTEND_URL=http://localhost:5173

# 后端系统URL
export BACKEND_URL=http://localhost:5001

# Web UI端口
export RPA_UI_PORT=8888

# Web UI主机
export RPA_UI_HOST=0.0.0.0

# 调试模式
export RPA_UI_DEBUG=true
```

### 配置文件

编辑 `rpa_system/config.py` 可以修改：
- 核心系统脚本路径
- 评测系统脚本路径
- 前端系统路径和URL
- Web UI端口和主机
- 工作目录和报告目录

---

## 🎯 使用场景

### 场景1: 持续改进核心系统

```bash
# 1. 启动Web UI
python -m rpa_system.main --mode web

# 2. 在浏览器中访问 http://localhost:8888
# 3. 设置样本数量（如10）
# 4. 点击"开始运行"
# 5. 等待运行完成
# 6. 查看报告，了解问题和解决方案
# 7. 根据报告调整参数或修复问题
# 8. 重复步骤4-7，持续改进
```

### 场景2: 批量测试

```bash
# 使用CLI模式批量运行不同参数
for count in 10 20 50; do
    python -m rpa_system.main --mode cli --sample-count $count --timeout 1800
done
```

### 场景3: 自动化测试（使用前端自动化）

```bash
# 1. 确保前端系统正在运行
# 2. 启动RPA系统
python -m rpa_system.main --mode web

# 3. 在Web界面中：
#    - 勾选"使用前端自动化"
#    - 勾选"无头模式"（可选）
#    - 设置样本数量
#    - 点击"开始运行"
```

---

## 🔧 故障排除

### 问题1: Web UI无法访问

**症状**：浏览器无法访问 http://localhost:8888

**解决方案**：
```bash
# 1. 检查端口是否被占用
lsof -i :8888

# 2. 如果被占用，使用其他端口
RPA_UI_PORT=9999 python -m rpa_system.main --mode web

# 3. 检查防火墙设置
# 4. 查看日志文件
tail -f rpa_system/logs/rpa_system.log
```

### 问题2: Flask未安装

**症状**：提示 "Flask未安装，无法启动Web UI"

**解决方案**：
```bash
pip install flask flask-cors
```

### 问题3: Selenium未安装

**症状**：提示 "Selenium未安装，浏览器自动化功能不可用"

**解决方案**：
```bash
pip install selenium
```

### 问题4: Chrome驱动问题

**症状**：浏览器自动化失败，提示驱动相关错误

**解决方案**：
```bash
# 1. 检查Chrome版本
google-chrome --version

# 2. 下载对应版本的Chrome驱动
# https://chromedriver.chromium.org/downloads

# 3. 确保驱动在PATH中
which chromedriver
```

### 问题5: 前端系统未运行

**症状**：前端自动化失败，提示无法连接

**解决方案**：
```bash
# 1. 检查前端系统是否运行
curl http://localhost:5173

# 2. 启动前端系统
cd frontend_monitor/backend && python app.py
cd frontend_monitor && npm run dev

# 3. 或使用环境变量指定URL
export FRONTEND_URL=http://localhost:5173
```

### 问题6: 运行失败

**症状**：运行过程中出现错误

**解决方案**：
```bash
# 1. 查看详细日志
tail -f rpa_system/logs/rpa_system.log

# 2. 检查核心系统脚本路径
ls -la scripts/run_core_with_frames.py

# 3. 检查评测系统脚本路径
ls -la evaluation_system/comprehensive_evaluation.py

# 4. 确保有足够的系统资源
```

---

## 📊 查看结果

### Web UI模式

1. 在Web界面中点击"查看报告"
2. 选择要查看的运行ID
3. 查看详细的报告内容

### CLI模式

```bash
# 查看最新报告
ls -lt rpa_system/reports/ | head -5

# 查看报告内容
cat rpa_system/reports/rpa_report_*.md | less

# 查看JSON报告
cat rpa_system/reports/rpa_report_*.json | jq .
```

---

## 💡 最佳实践

1. **首次运行**：
   - 使用小样本数量（如10）测试
   - 使用Web UI模式，便于观察
   - 不勾选"无头模式"，可以看到浏览器操作

2. **持续运行**：
   - 使用Web UI模式，便于管理
   - 勾选"无头模式"，节省资源
   - 定期查看报告，持续改进

3. **批量测试**：
   - 使用CLI模式，便于脚本化
   - 使用不同的参数组合
   - 对比不同运行的结果

4. **生产环境**：
   - 使用无头模式
   - 设置合理的超时时间
   - 定期清理日志和报告文件

---

## 📚 相关文档

- `rpa_system/README.md` - 完整系统文档
- `rpa_system/QUICKSTART.md` - 快速开始指南
- `rpa_system/FRONTEND_MONITORING.md` - 前端监控功能说明
- `rpa_system/FRONTEND_DEEP_CHECK.md` - 前端深度检查功能说明
- `rpa_system/README_BROWSER_AUTOMATION.md` - 浏览器自动化详细文档

---

## 🆘 获取帮助

如果遇到问题：

1. 查看日志文件：`rpa_system/logs/rpa_system.log`
2. 查看报告文件：`rpa_system/reports/`
3. 检查配置文件：`rpa_system/config.py`
4. 查看相关文档

