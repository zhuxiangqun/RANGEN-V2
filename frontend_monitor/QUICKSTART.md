# 快速开始指南

## 前置要求

1. **Node.js** (v16+)
2. **Python 3** (v3.8+)
3. **npm** 或 **yarn**

## 一键启动

```bash
cd frontend_monitor
./start.sh
```

脚本会自动：
1. 检查依赖
2. 安装前端依赖（如需要）
3. 创建Python虚拟环境并安装后端依赖（如需要）
4. 启动后端服务（端口5000）
5. 启动前端服务（端口3000）

## 手动启动

### 1. 安装依赖

**前端依赖:**
```bash
cd frontend_monitor
npm install
```

**后端依赖:**
```bash
cd frontend_monitor/backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 启动后端

```bash
cd frontend_monitor/backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python app.py
```

后端将在 `http://localhost:5000` 启动。

### 3. 启动前端

```bash
cd frontend_monitor
npm run dev
```

前端将在 `http://localhost:3000` 启动。

## 使用说明

1. 打开浏览器访问 `http://localhost:3000`
2. 确保核心系统已经运行并生成了 `research_system.log` 文件
3. 在界面上可以：
   - 查看推理过程（自动刷新）
   - 查看智能体调用关系图
   - 点击"运行评测"按钮执行评测

## 故障排除

### 后端无法启动

- 检查端口5000是否被占用
- 检查Python虚拟环境是否正确激活
- 查看 `backend.log` 文件中的错误信息

### 前端无法连接后端

- 确认后端服务正在运行
- 检查 `vite.config.js` 中的代理配置
- 检查浏览器控制台的错误信息

### 没有数据显示

- 确认 `research_system.log` 文件存在
- 确认日志文件路径正确（相对于backend目录）
- 检查日志文件格式是否符合解析规则

## 开发模式

前端支持热重载，修改代码后会自动刷新。

后端支持调试模式，修改 `app.py` 中的 `debug=True` 可以启用详细错误信息。

