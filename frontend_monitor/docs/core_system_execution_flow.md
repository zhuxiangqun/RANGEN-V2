# 前端系统运行核心系统的完整流程

## 📋 执行流程图

```
用户点击按钮
    ↓
前端 Vue 组件 (App.vue)
    ↓
API 服务 (api.js)
    ↓
后端 Flask API (app.py)
    ↓
后台线程执行
    ↓
Bash 脚本 (run_core_with_frames.sh)
    ↓
Python 脚本 (run_core_with_frames.py)
    ↓
统一研究系统 (unified_research_system.py)
    ↓
核心推理引擎 (real_reasoning_engine.py)
    ↓
生成日志 (research_system.log)
```

## 🔍 详细步骤

### 步骤1: 用户操作（前端界面）

**位置**: `frontend_monitor/src/App.vue`

用户在前端界面：
1. 设置样本数量（默认10，可调整1-1000）
2. 点击"运行核心系统"按钮

**代码**:
```vue
<el-button type="success" @click="runCoreSystem" :loading="coreSystemRunning">
  运行核心系统
</el-button>
```

### 步骤2: 前端调用API

**位置**: `frontend_monitor/src/App.vue` → `runCoreSystem()` 函数

**执行流程**:
```javascript
const runCoreSystem = async () => {
  coreSystemRunning.value = true
  try {
    // 调用API服务
    const result = await apiService.runCoreSystem(sampleCount.value)
    // 保存任务ID，开始轮询状态
    currentCoreTaskId.value = result.task_id
    startTaskStatusPolling(result.task_id, 'core')
  } catch (error) {
    // 错误处理
  }
}
```

**API调用**: `frontend_monitor/src/services/api.js`
```javascript
async runCoreSystem(sampleCount = 10) {
  const response = await api.post('/core-system/run', {
    sample_count: sampleCount
  })
  return response.data
}
```

**HTTP请求**:
- **方法**: POST
- **URL**: `/api/core-system/run`
- **请求体**: `{ "sample_count": 10 }`
- **代理**: Vite开发服务器代理到 `http://localhost:5001`

### 步骤3: 后端接收请求

**位置**: `frontend_monitor/backend/app.py` → `run_core_system()` 函数

**执行流程**:
1. 接收POST请求，解析JSON数据
2. 获取 `sample_count` 参数（默认10）
3. 检查脚本文件是否存在
4. 生成唯一任务ID
5. 创建后台线程执行脚本

**关键代码**:
```python
@app.route('/api/core-system/run', methods=['POST'])
def run_core_system():
    data = request.get_json() or {}
    sample_count = data.get('sample_count', 10)
    
    # 检查脚本
    core_system_script = ROOT_DIR / "scripts" / "run_core_with_frames.sh"
    
    # 生成任务ID
    task_id = f"core_{task_counter}_{int(time.time())}"
    
    # 后台线程执行
    thread = threading.Thread(target=run_script, daemon=True)
    thread.start()
    
    # 立即返回任务ID（不等待执行完成）
    return jsonify({
        "success": True,
        "task_id": task_id,
        "message": f"核心系统已启动，正在处理 {sample_count} 个样本"
    })
```

### 步骤4: 后台线程执行脚本

**位置**: `frontend_monitor/backend/app.py` → `run_script()` 内部函数

**执行命令**:
```bash
bash scripts/run_core_with_frames.sh \
  --sample-count 10 \
  --data-path data/frames_dataset.json
```

**执行方式**:
- 使用 `subprocess.Popen()` 创建子进程
- **🚀 重要**: 确保使用项目根目录的 `.venv` 环境
  - 设置工作目录为项目根目录（`cwd=str(ROOT_DIR)`）
  - 确保PATH包含 `.venv/bin`（如果存在）
  - bash脚本会自动激活 `.venv`（见步骤5）
- 实时捕获标准输出和错误输出
- 在后台线程中运行，不阻塞API响应

**环境说明**:
- **所有系统统一使用**: 项目根目录的虚拟环境 `.venv`
- 前端后端、核心系统、评测系统都在同一个 `.venv` 中运行
- 确保 `.venv` 已安装所有依赖（包括Flask等后端依赖）

**关键代码**:
```python
process = subprocess.Popen(
    ["bash", str(core_system_script), 
     "--sample-count", str(sample_count),
     "--data-path", "data/frames_dataset.json"],
    cwd=str(ROOT_DIR),
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

# 实时读取输出
for line in iter(process.stdout.readline, ''):
    if line:
        running_tasks[task_id]["output"] += line
```

### 步骤5: Bash脚本执行

**位置**: `scripts/run_core_with_frames.sh`

**执行流程**:
1. **🚀 重要**: 自动激活项目根目录的虚拟环境（`.venv`）
   ```bash
   if [[ -d "${ROOT_DIR}/.venv" ]]; then
     source "${ROOT_DIR}/.venv/bin/activate"
   fi
   ```
   - 这确保了核心系统在正确的虚拟环境中运行
   - 使用项目根目录的 `.venv`，而不是 `frontend_monitor/backend/venv`
2. 解析命令行参数（`--sample-count`, `--data-path`）
3. 调用Python脚本

**关键代码**:
```bash
# 激活虚拟环境
if [[ -d "${ROOT_DIR}/.venv" ]]; then
  source "${ROOT_DIR}/.venv/bin/activate"
fi

# 调用Python脚本
python scripts/run_core_with_frames.py \
  --sample-count 10 \
  --data-path data/frames_dataset.json
```

### 步骤6: Python脚本执行

**位置**: `scripts/run_core_with_frames.py`

**执行流程**:
1. 加载环境变量（`.env`文件）
2. 加载FRAMES数据集
3. 创建统一研究系统实例
4. 遍历样本，逐个处理
5. 调用核心系统处理每个查询
6. 记录日志到 `research_system.log`

**关键代码**:
```python
# 加载数据集
samples = load_frames_dataset(data_path, sample_count)

# 创建研究系统
research_system = create_unified_research_system()

# 处理每个样本
for idx, item in enumerate(samples, 1):
    query = item.get('Prompt', '')
    expected_answer = item.get('Expected Answer', '')
    
    # 创建请求
    request = ResearchRequest(
        query=query,
        context={"sample_id": idx, "expected_answer": expected_answer}
    )
    
    # 执行研究（调用核心系统）
    result = await research_system.execute_research(request)
    
    # 记录日志
    log_info(f"FRAMES sample={idx}/{sample_count} ...")
```

### 步骤7: 核心系统处理

**位置**: `src/unified_research_system.py` → `execute_research()`

**执行流程**:
1. 接收研究请求
2. 调用推理引擎 (`RealReasoningEngine`)
3. 执行推理过程（证据收集、推理、答案生成）
4. 返回结果

**关键代码**:
```python
def execute_research(self, request: ResearchRequest):
    # 调用推理引擎
    result = self.reasoning_engine.reason(
        query=request.query,
        context=request.context
    )
    return result
```

### 步骤8: 日志生成

**位置**: `evaluation_system/research_logger.py`

**日志文件**: `research_system.log`

**日志内容**:
- 查询接收
- 推理过程
- 证据收集
- 答案生成
- 查询完成

**日志格式示例**:
```
查询接收: How many years earlier..., 样本ID=1
推理过程: 3个推理步骤
证据收集: 6条证据
查询完成: success=True, 样本ID=1
```

## 🔄 状态跟踪

### 任务状态轮询

前端每2秒轮询一次任务状态：

```javascript
// 轮询任务状态
setInterval(() => {
  pollTaskStatus(taskId, 'core')
}, 2000)
```

**状态查询API**: `GET /api/tasks/<task_id>`

**返回状态**:
- `starting`: 任务启动中
- `running`: 任务运行中
- `completed`: 任务完成
- `failed`: 任务失败
- `cancelled`: 任务已取消

## 📊 数据流向

```
前端界面
  ↓ (HTTP POST)
后端API (Flask)
  ↓ (subprocess.Popen)
Bash脚本
  ↓ (python命令)
Python脚本
  ↓ (import/调用)
核心系统模块
  ↓ (日志记录)
research_system.log
  ↓ (SSE/轮询)
前端实时显示
```

## 🎯 关键特性

1. **异步执行**: 不阻塞前端，立即返回任务ID
2. **状态跟踪**: 实时查询任务执行状态
3. **输出捕获**: 实时捕获脚本执行输出
4. **任务管理**: 支持取消正在运行的任务
5. **错误处理**: 完善的错误捕获和报告机制

## 🔧 配置参数

- **样本数量**: 前端可配置（1-1000）
- **数据路径**: 固定为 `data/frames_dataset.json`
- **工作目录**: 项目根目录
- **虚拟环境**: 自动激活 `.venv`（如果存在）

## 📝 注意事项

1. **虚拟环境**: Bash脚本会自动激活虚拟环境
2. **工作目录**: 所有脚本在项目根目录执行
3. **环境变量**: Python脚本会加载 `.env` 文件
4. **日志文件**: 所有日志写入 `research_system.log`
5. **任务隔离**: 每个任务有独立的ID和状态

