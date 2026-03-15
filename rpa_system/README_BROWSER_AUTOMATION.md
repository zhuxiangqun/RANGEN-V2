# RPA系统浏览器自动化功能

## 📋 功能概述

RPA系统现在支持**浏览器自动化**，可以：
1. 自动打开前端系统页面
2. 自动设置样本数量
3. 自动点击"运行核心系统"按钮
4. 自动点击"运行评测系统"按钮
5. 监控执行状态
6. 获取执行结果
7. 根据结果分析和改进核心系统

## 🚀 使用方法

### 1. 安装依赖

```bash
# 安装Selenium
pip install selenium

# 安装Chrome驱动（macOS）
brew install chromedriver

# 或下载Chrome驱动
# https://chromedriver.chromium.org/downloads
```

### 2. 启动前端系统

确保前端系统正在运行：
```bash
# 启动前端后端
cd frontend_monitor/backend
python app.py

# 启动前端前端（另一个终端）
cd frontend_monitor
npm run dev
```

### 3. 使用浏览器自动化

#### 方式1: 通过RPA Web UI

1. 启动RPA系统Web UI：
```bash
python -m rpa_system.main --mode web
```

2. 访问 http://localhost:8888

3. 勾选"使用前端自动化"选项

4. 设置样本数量和其他参数

5. 点击"开始运行"

#### 方式2: 通过CLI

```bash
python -m rpa_system.main --mode cli --sample-count 10 --use-frontend-automation
```

#### 方式3: 直接使用Python API

```python
from rpa_system.frontend_automation import FrontendAutomation

async def main():
    automation = FrontendAutomation(
        frontend_url="http://localhost:5173",
        headless=False  # 显示浏览器窗口
    )
    
    results = await automation.run_full_automation_cycle(
        sample_count=10,
        wait_for_completion=True,
        run_evaluation=True
    )
    
    print(f"执行结果: {results}")
    automation.close()

import asyncio
asyncio.run(main())
```

## 🔧 配置

### 前端URL配置

默认前端URL：`http://localhost:5173`

可以通过环境变量配置：
```bash
export FRONTEND_URL=http://localhost:5173
```

### 浏览器选项

- **headless模式**：不显示浏览器窗口（适合服务器环境）
- **窗口大小**：默认1920x1080
- **超时时间**：默认30秒

## 📊 自动化流程

```
1. 启动浏览器
   ↓
2. 打开前端页面
   ↓
3. 设置样本数量
   ↓
4. 点击"运行核心系统"按钮
   ↓
5. 等待任务完成（监控按钮状态、进度等）
   ↓
6. 点击"运行评测系统"按钮（可选）
   ↓
7. 等待评测完成
   ↓
8. 获取评测结果
   ↓
9. 分析结果并生成改进方案
   ↓
10. 生成报告
```

## 🎯 功能特点

### 1. 智能元素定位

支持多种选择器策略：
- CSS选择器
- XPath选择器
- 文本内容匹配
- 自动重试机制

### 2. 状态监控

- 监控按钮状态（运行中/空闲）
- 监控任务进度
- 检测完成/失败状态

### 3. 截图记录

自动截图记录关键步骤：
- 页面加载完成
- 按钮点击
- 任务完成

### 4. 错误处理

- 自动重试
- 超时处理
- 异常捕获和记录

## 🔍 调试

### 查看浏览器操作

设置`headless=False`可以看到浏览器操作过程。

### 查看日志

```bash
tail -f rpa_system/logs/rpa_system.log
```

### 查看截图

截图保存在：`rpa_system/work/screenshots/`

## ⚠️ 注意事项

1. **Chrome驱动版本**：确保Chrome驱动版本与Chrome浏览器版本匹配
2. **前端系统运行**：确保前端系统已启动并可以访问
3. **网络延迟**：如果网络较慢，可能需要增加等待时间
4. **浏览器资源**：浏览器自动化会消耗系统资源，建议在性能较好的机器上运行

## 🐛 故障排除

### Chrome驱动问题

```bash
# 检查Chrome版本
google-chrome --version

# 下载对应版本的Chrome驱动
# https://chromedriver.chromium.org/downloads
```

### 元素找不到

- 检查前端页面是否正常加载
- 检查元素选择器是否正确
- 增加等待时间

### 浏览器无法启动

- 检查是否安装了Chrome/Firefox
- 检查驱动是否正确安装
- 尝试使用headless模式

## 📚 更多信息

详细文档请参考：`rpa_system/README.md`

