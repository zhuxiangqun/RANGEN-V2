# RPA系统浏览器自动化快速开始

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装Python依赖
pip install -r rpa_system/requirements.txt

# 安装Chrome驱动（macOS）
brew install chromedriver

# 或手动下载Chrome驱动
# https://chromedriver.chromium.org/downloads
# 确保Chrome驱动版本与Chrome浏览器版本匹配
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
4. 选择是否使用无头模式（不显示浏览器窗口）
5. 点击"开始运行"

RPA系统将：
- ✅ 自动打开前端系统页面
- ✅ 自动设置样本数量
- ✅ 自动点击"运行核心系统"按钮
- ✅ 等待执行完成
- ✅ 自动点击"运行评测系统"按钮
- ✅ 分析结果并生成改进方案
- ✅ 生成完整报告

## 📊 自动化流程

```
1. 启动浏览器（Chrome/Firefox）
   ↓
2. 打开前端页面（http://localhost:5173）
   ↓
3. 设置样本数量（在输入框中输入）
   ↓
4. 点击"运行核心系统"按钮
   ↓
5. 监控执行状态（检查按钮状态、进度等）
   ↓
6. 等待任务完成
   ↓
7. 点击"运行评测系统"按钮
   ↓
8. 等待评测完成
   ↓
9. 获取评测结果
   ↓
10. 分析结果并生成改进方案
   ↓
11. 生成完整报告
```

## 🎯 功能特点

### 1. 智能元素定位

- 支持多种选择器（CSS、XPath、文本匹配）
- 自动重试机制
- 超时处理

### 2. 状态监控

- 监控按钮状态（运行中/空闲）
- 监控任务进度
- 检测完成/失败状态

### 3. 截图记录

自动截图记录关键步骤，保存在：`rpa_system/work/screenshots/`

### 4. 错误处理

- 自动重试
- 超时处理
- 异常捕获和记录

## ⚙️ 配置选项

### 前端URL

默认：`http://localhost:5173`

可以通过环境变量配置：
```bash
export FRONTEND_URL=http://localhost:5173
```

### 无头模式

- **headless=False**：显示浏览器窗口（默认，便于调试）
- **headless=True**：不显示浏览器窗口（适合服务器环境）

### 超时时间

- 任务完成等待：默认3600秒（1小时）
- 评测完成等待：默认600秒（10分钟）
- 元素等待：默认30秒

## 🔍 调试

### 查看浏览器操作

设置`headless=False`可以看到浏览器操作过程。

### 查看日志

```bash
tail -f rpa_system/logs/rpa_system.log
```

### 查看截图

```bash
ls -la rpa_system/work/screenshots/
```

## ⚠️ 注意事项

1. **Chrome驱动版本**：确保Chrome驱动版本与Chrome浏览器版本匹配
2. **前端系统运行**：确保前端系统已启动并可以访问
3. **网络延迟**：如果网络较慢，可能需要增加等待时间
4. **浏览器资源**：浏览器自动化会消耗系统资源

## 🐛 故障排除

### Chrome驱动问题

```bash
# 检查Chrome版本
google-chrome --version
# 或
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version

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

详细文档请参考：
- `rpa_system/README.md` - 完整文档
- `rpa_system/README_BROWSER_AUTOMATION.md` - 浏览器自动化详细文档

