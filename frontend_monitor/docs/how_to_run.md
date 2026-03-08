# 前端系统运行指南

## 🚀 快速启动（推荐）

### 方法1: 一键启动脚本（最简单）

```bash
cd frontend_monitor
chmod +x start.sh
./start.sh
```

脚本会自动：
1. ✅ 检查Node.js和Python环境
2. ✅ 安装前端依赖（如需要）
3. ✅ 创建Python虚拟环境并安装后端依赖（如需要）
4. ✅ 启动后端服务（端口5000或5001）
5. ✅ 启动前端服务（端口3000）

启动成功后：
- 📱 前端地址: http://localhost:3000
- 🔧 后端地址: http://localhost:5000 或 http://localhost:5001

按 `Ctrl+C` 停止服务。

---

## 📋 手动启动（分步执行）

### 步骤1: 安装前端依赖

```bash
cd frontend_monitor
npm install
```

**注意**: 如果遇到Vue语言服务器警告，请：
1. 确保已运行 `npm install`
2. 在VS Code中执行：`Vue: Restart Vue server`（`Cmd+Shift+P` 或 `Ctrl+Shift+P`）

### 步骤2: 确保项目根目录的.venv已安装后端依赖

**🚀 重要**: 前端后端现在使用项目根目录的 `.venv`，而不是独立的 `backend/venv`。

```bash
# 确保在项目根目录
cd /path/to/RANGEN-main(syu-python)

# 激活.venv（如果还没有激活）
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate     # Windows

# 安装后端依赖（如果还没有安装）
pip install -r frontend_monitor/backend/requirements.txt
```

### 步骤3: 启动后端服务

**方法A: 使用启动脚本（推荐）**
```bash
cd frontend_monitor
chmod +x start_backend.sh
./start_backend.sh
```

**方法B: 手动启动**
```bash
# 在项目根目录
cd /path/to/RANGEN-main(syu-python)
source .venv/bin/activate  # macOS/Linux
cd frontend_monitor/backend
python app.py
```

后端将在以下端口之一启动：
- `http://localhost:5000`（默认）
- `http://localhost:5001`（如果5000被占用，如macOS AirPlay）

### 步骤4: 启动前端服务

**在新的终端窗口中**：

```bash
cd frontend_monitor
npm run dev
```

前端将在 `http://localhost:3000` 启动。

---

## 🌐 访问系统

1. 打开浏览器访问：**http://localhost:3000**
2. 系统会自动连接到后端服务
3. 如果后端运行在5001端口，前端会自动适配

---

## 📊 功能使用

### 1. 查看推理过程
- 在"推理过程"标签页中查看所有样本的推理步骤
- 自动刷新（默认开启），可手动关闭

### 2. 查看智能体调用关系
- 在"智能体调用关系"标签页中查看智能体调用图
- 可视化展示智能体之间的调用链

### 3. 运行核心系统
- 设置样本数量（1-1000）
- 点击"运行核心系统"按钮
- 系统会异步执行，不阻塞界面
- 可以随时点击"取消"按钮停止执行

### 4. 运行评测系统
- 点击"运行评测系统"按钮
- 系统会执行评测脚本并显示结果
- 可以随时点击"取消"按钮停止执行

---

## ⚠️ 前置要求

### 必需环境
- **Node.js** (v16+)
- **Python 3** (v3.8+)
- **npm** 或 **yarn**

### 检查环境
```bash
# 检查Node.js
node --version

# 检查Python
python3 --version

# 检查npm
npm --version
```

---

## 🔧 故障排除

### 问题1: 后端无法启动

**症状**: 端口被占用或启动失败

**解决方案**:
```bash
# 检查端口占用
lsof -i :5000  # macOS/Linux
netstat -ano | findstr :5000  # Windows

# 如果5000被占用，后端会自动切换到5001
# 前端会自动适配新端口
```

**查看日志**:
```bash
cat frontend_monitor/backend.log
```

### 问题2: 前端无法连接后端

**症状**: 浏览器控制台显示连接错误

**解决方案**:
1. 确认后端服务正在运行
2. 检查后端端口（5000或5001）
3. 检查 `vite.config.js` 中的代理配置
4. 查看浏览器控制台的错误信息

### 问题3: 没有数据显示

**症状**: 界面显示空数据

**解决方案**:
1. 确认 `research_system.log` 文件存在（在项目根目录）
2. 确认日志文件路径正确（相对于backend目录）
3. 检查日志文件格式是否符合解析规则
4. 尝试点击"刷新日志"按钮

### 问题4: Vue语言服务器警告

**症状**: VS Code显示"Failed to write the global types file"

**解决方案**:
1. 确保已运行 `npm install`
2. 在VS Code中执行：`Vue: Restart Vue server`
3. 重启VS Code

### 问题5: 权限错误

**症状**: 脚本无法执行

**解决方案**:
```bash
# 添加执行权限
chmod +x frontend_monitor/start.sh
chmod +x frontend_monitor/start_backend.sh
```

---

## 📁 项目结构

```
frontend_monitor/
├── backend/              # 后端API服务
│   ├── app.py           # Flask应用主文件
│   ├── requirements.txt # Python依赖
│   └── venv/            # Python虚拟环境（自动创建）
├── src/                 # 前端源码
│   ├── components/      # Vue组件
│   ├── services/        # API服务
│   └── App.vue          # 主应用组件
├── docs/                # 文档
├── start.sh             # 一键启动脚本
├── start_backend.sh     # 后端启动脚本
├── package.json         # 前端依赖配置
└── vite.config.js       # Vite构建配置
```

---

## 🔄 开发模式

### 前端热重载
- 修改前端代码后，浏览器会自动刷新
- 无需手动重启

### 后端调试
- 修改 `backend/app.py` 后需要重启后端
- 可以设置 `debug=True` 启用详细错误信息

### 查看日志
- 后端日志：`frontend_monitor/backend.log`
- 核心系统日志：`research_system.log`（项目根目录）

---

## 📝 注意事项

1. **端口占用**: 
   - macOS的AirPlay服务可能占用5000端口
   - 系统会自动检测并切换到5001端口

2. **虚拟环境**: 
   - **所有系统统一使用**: 项目根目录的虚拟环境 `.venv`
   - 前端后端、核心系统、评测系统都在同一个 `.venv` 中运行
   - 确保项目根目录的 `.venv` 已安装所有依赖（包括Flask等后端依赖）

3. **日志文件**: 
   - 确保核心系统已运行并生成日志
   - 日志文件路径：`../research_system.log`（相对于backend目录）

4. **脚本权限**: 
   - 确保评测脚本有执行权限
   - 运行 `chmod +x scripts/run_evaluation.sh`

5. **环境变量**: 
   - 所有系统（前端后端、核心系统、评测系统）都在项目根目录的 `.venv` 中运行
   - 确保项目根目录的 `.venv` 已正确安装所有依赖
   - 包括：核心系统依赖、评测系统依赖、Flask等后端依赖

---

## 🎯 快速检查清单

启动前确认：
- [ ] Node.js已安装
- [ ] Python3已安装
- [ ] 项目根目录的 `.venv` 已创建并安装所有依赖
- [ ] 已运行 `npm install`（首次运行，在frontend_monitor目录）
- [ ] 后端依赖已安装到 `.venv`（`pip install -r frontend_monitor/backend/requirements.txt`）

启动后确认：
- [ ] 后端服务正在运行（检查端口5000或5001）
- [ ] 前端服务正在运行（检查端口3000）
- [ ] 浏览器可以访问 http://localhost:3000
- [ ] 界面正常显示，无错误信息

---

## 💡 提示

- 使用 `./start.sh` 一键启动最简单
- 后端和前端需要在不同的终端窗口运行（手动启动时）
- 前端会自动适配后端端口变化
- 系统支持实时日志流（SSE）和轮询两种模式

