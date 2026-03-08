# RANGEN 前端监控系统

独立的Vue3前端系统，用于可视化RANGEN核心系统的运行过程。

## 功能特性

1. **动态显示推理过程**: 实时展示每个样本的推理步骤、耗时、置信度等信息
2. **智能体调用关系图**: 可视化展示智能体之间的调用关系和调用链
3. **评测系统集成**: 一键运行评测脚本，并展示评测结果
4. **独立运行**: 不与其他系统耦合，通过读取日志文件和调用脚本实现

## 技术栈

- **前端**: Vue3 + Element Plus + ECharts
- **后端**: Flask (Python)
- **构建工具**: Vite

## 项目结构

```
frontend_monitor/
├── backend/              # 后端API服务
│   ├── app.py           # Flask应用
│   └── requirements.txt # Python依赖
├── src/                 # 前端源码
│   ├── components/      # Vue组件
│   │   ├── ReasoningProcess.vue    # 推理过程组件
│   │   ├── AgentCallGraph.vue      # 智能体调用图组件
│   │   └── EvaluationResults.vue   # 评测结果组件
│   ├── services/        # API服务
│   │   └── api.js       # API调用封装
│   ├── App.vue          # 主应用组件
│   └── main.js          # 入口文件
├── package.json         # 前端依赖
├── vite.config.js       # Vite配置
└── README.md           # 说明文档
```

## 安装和运行

### 1. 安装前端依赖（必须）

**重要**: 在运行前端系统之前，必须先安装依赖，否则会出现Vue语言服务器错误。

```bash
cd frontend_monitor
npm install
```

如果遇到Vue语言服务器警告（"Failed to write the global types file"），请：
1. 确保已运行 `npm install` 安装所有依赖
2. 在VS Code中执行命令：`Vue: Restart Vue server`（按 `Cmd+Shift+P` 或 `Ctrl+Shift+P`，然后输入该命令）

### 2. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 启动后端服务

```bash
cd backend
python app.py
```

后端服务将在 `http://localhost:5000` 启动。

### 4. 启动前端开发服务器

```bash
cd frontend_monitor
npm run dev
```

前端应用将在 `http://localhost:3000` 启动。

## 使用说明

1. **查看推理过程**: 在"推理过程"标签页中，可以看到所有样本的推理步骤、耗时、置信度等信息
2. **查看智能体调用关系**: 在"智能体调用关系"标签页中，可以看到智能体之间的调用关系图
3. **运行评测**: 点击"运行评测"按钮，系统会执行评测脚本并显示结果

## 配置说明

后端API会从以下位置读取数据：

- **日志文件**: `../research_system.log` (相对于backend目录)
- **评测脚本**: `../scripts/run_evaluation.sh`
- **评测报告**: `../comprehensive_eval_results/evaluation_report.md`

如果需要修改这些路径，请编辑 `backend/app.py` 中的相关变量。

## 注意事项

1. 确保核心系统已经运行并生成了日志文件
2. 确保评测脚本有执行权限
3. 前端会自动刷新日志数据（默认每2秒），可以在界面上关闭自动刷新

## 开发说明

### 添加新的可视化组件

1. 在 `src/components/` 目录下创建新的Vue组件
2. 在 `src/App.vue` 中添加新的标签页
3. 在 `backend/app.py` 中添加相应的API端点（如需要）

### 自定义日志解析

修改 `backend/app.py` 中的 `parse_log_file()` 函数，根据实际的日志格式调整解析逻辑。

## 许可证

与RANGEN主项目保持一致。

