# RPA系统 - 自动化运行、评测、修复和改进核心系统

## 📋 功能概述

RPA系统是一个独立的自动化系统，主要实现以下功能：

1. **自动运行和评测核心系统**：
   - 通过浏览器自动化自动打开前端系统页面
   - 自动点击前端系统页面的按钮执行
   - 自动运行核心系统和评测系统

2. **自动修复前端程序问题**：
   - 检测前端系统问题（语法错误、缺失依赖等）
   - 自动修复可修复的问题

3. **自动分析核心系统问题**：
   - 分析日志中的错误
   - 分析评测结果
   - 分析性能问题
   - 生成解决方案

4. **自动改进核心系统**：
   - 根据执行情况生成改进方案
   - 提供具体的改进建议和代码修改建议

5. **通过UI调整运行参数**：
   - 提供Web界面，支持动态调整运行参数
   - 支持持续运行持续改进

6. **等待用户命令**：
   - 每次运行结束后等待用户命令进行下一轮运行

## 🏗️ 系统架构

```
RPA系统
├── core_controller.py      # 核心控制器（协调各个模块）
├── browser_automation.py   # 浏览器自动化（Selenium）
├── frontend_automation.py  # 前端自动化（整合浏览器自动化）
├── frontend_monitor.py     # 前端监控和修复模块
├── core_analyzer.py        # 核心系统分析模块
├── system_improver.py      # 系统改进模块
├── report_generator.py     # 报告生成模块
├── web_ui.py              # Web UI界面
├── config.py              # 配置管理
└── main.py                # 主程序入口
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装Python依赖
pip install -r rpa_system/requirements.txt

# 安装Chrome驱动（macOS）
brew install chromedriver

# 或手动下载Chrome驱动
# https://chromedriver.chromium.org/downloads
```

### 2. 启动前端系统

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

### 3. 启动RPA系统

**终端3 - 启动RPA系统**：
```bash
python -m rpa_system.main --mode web
```

RPA系统应该运行在：http://localhost:8888

### 4. 使用浏览器自动化

1. 访问 http://localhost:8888
2. 勾选"使用前端自动化"选项
3. 设置样本数量（如10）
4. 选择是否使用无头模式
5. 点击"开始运行"

## 📖 使用方法

### Web UI模式（推荐）

```bash
# 启动Web界面
python -m rpa_system.main --mode web

# 或直接运行
python rpa_system/main.py
```

然后访问：http://localhost:8888

**Web界面功能**：
- ✅ 调整运行参数（样本数量、超时时间）
- ✅ 选择是否使用前端自动化
- ✅ 选择是否使用无头模式
- ✅ 启动/停止运行
- ✅ 实时查看运行状态和日志
- ✅ 查看历史运行报告
- ✅ 查看详细报告内容

### CLI模式

```bash
# 命令行模式运行（不使用前端自动化）
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

3. **浏览器自动化** 🌐（如果启用）
   - 自动打开前端系统页面
   - 自动设置样本数量
   - 自动点击"运行核心系统"按钮
   - 等待执行完成
   - 自动点击"运行评测系统"按钮

4. **运行核心系统** 🚀（如果不使用前端自动化）
   - 使用配置的参数运行核心系统
   - 监控运行状态和日志

5. **运行评测** 📊（如果不使用前端自动化）
   - 执行评测系统
   - 收集评测结果

6. **分析问题** 🔍
   - 分析日志中的错误
   - 分析评测结果
   - 分析性能问题
   - 生成解决方案

7. **生成改进方案** 🔧
   - 根据分析结果生成改进方案
   - 提供具体的改进建议

8. **生成报告** 📝
   - 生成Markdown格式报告
   - 生成JSON格式报告
   - 保存到reports目录

## 📁 目录结构

```
rpa_system/
├── __init__.py
├── main.py                 # 主程序入口
├── config.py              # 配置管理
├── core_controller.py     # 核心控制器
├── browser_automation.py  # 浏览器自动化
├── frontend_automation.py # 前端自动化
├── frontend_monitor.py    # 前端监控
├── core_analyzer.py       # 核心分析
├── system_improver.py     # 系统改进
├── report_generator.py    # 报告生成
├── web_ui.py             # Web UI
├── templates/            # HTML模板
│   └── index.html
├── static/               # 静态文件
├── work/                 # 工作目录
│   └── screenshots/      # 截图目录
├── reports/              # 报告目录
└── logs/                 # 日志目录
```

## ⚙️ 配置

配置文件：`rpa_system/config.py`

主要配置项：
- 核心系统脚本路径
- 评测系统脚本路径
- 前端系统路径和URL
- Web UI端口和主机
- 工作目录和报告目录

## 🔧 扩展功能

### 添加新的检查项

在 `frontend_monitor.py` 的 `check_and_fix()` 方法中添加新的检查逻辑。

### 添加新的分析项

在 `core_analyzer.py` 的 `analyze()` 方法中添加新的分析逻辑。

### 添加新的改进方案

在 `system_improver.py` 的 `_generate_improvement()` 方法中添加新的改进逻辑。

### 自定义报告格式

修改 `report_generator.py` 的 `_generate_markdown_report()` 方法。

## 📝 注意事项

1. 确保核心系统和评测系统可以正常运行
2. 确保前端系统已启动并可以访问
3. 确保有足够的权限访问相关目录和文件
4. Web UI模式需要安装Flask和Flask-CORS
5. 浏览器自动化需要安装Selenium和Chrome驱动
6. 建议在生产环境中使用反向代理（如Nginx）

## 🐛 故障排除

### Web UI无法访问

- 检查端口是否被占用
- 检查防火墙设置
- 查看日志文件：`rpa_system/logs/rpa_system.log`

### 浏览器自动化失败

- 检查Chrome驱动是否正确安装
- 检查前端系统是否正在运行
- 检查前端URL是否正确
- 查看日志文件获取详细错误信息

### 运行失败

- 检查核心系统脚本路径是否正确
- 检查日志文件查看详细错误信息
- 确保有足够的系统资源

## 📚 相关文档

- `rpa_system/QUICKSTART.md` - 快速开始指南
- `rpa_system/README_BROWSER_AUTOMATION.md` - 浏览器自动化详细文档
- `rpa_system/QUICKSTART_BROWSER_AUTOMATION.md` - 浏览器自动化快速开始

## 📄 许可证

与主项目保持一致
