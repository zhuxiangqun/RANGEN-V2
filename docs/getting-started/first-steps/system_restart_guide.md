# 系统重启指南

## 一、如何重启系统

### 方法1：如果系统正在运行（通过终端启动）

#### 步骤1：停止当前系统

```bash
# 在运行系统的终端窗口中按 Ctrl+C
# 或找到进程并终止
ps aux | grep python | grep unified_research_system
kill <PID>
```

#### 步骤2：重新启动

```bash
# 使用你的启动脚本
python examples/simple_langgraph_example.py

# 或使用其他启动方式
python your_startup_script.py
```

### 方法2：如果系统作为服务运行

```bash
# 停止服务
systemctl stop your-service-name  # Linux systemd
# 或
service your-service-name stop     # Linux service

# 启动服务
systemctl start your-service-name
# 或
service your-service-name start
```

### 方法3：如果使用 Docker

```bash
# 重启容器
docker restart <container-name>

# 或停止后重新启动
docker stop <container-name>
docker start <container-name>
```

## 二、验证重启后工作流状态

### 步骤1：运行诊断脚本

```bash
python3 scripts/diagnose_workflow.py
```

应该看到：
```
✅ LangGraph 已安装: x.x.x
✅ 工作流模块可用
✅ 工作流初始化成功
```

### 步骤2：运行系统初始化测试

```bash
python3 scripts/test_workflow_initialization.py
```

这会验证：
- 系统能否正常初始化
- 工作流是否在系统初始化时创建
- 可视化服务器是否能获取工作流

### 步骤3：检查初始化日志

```bash
# 查看系统日志
tail -f research_system.log | grep -i "工作流\|workflow"

# 应该看到：
# ✅ [初始化] 统一工作流（MVP）初始化完成
```

### 步骤4：访问可视化界面

打开浏览器访问：`http://localhost:8080`

应该能看到：
- 工作流图正常显示
- 不再出现 "No workflow available" 错误

## 三、快速重启脚本

### 创建重启脚本

```bash
# scripts/restart_system.sh
#!/bin/bash

echo "正在停止系统..."
pkill -f "unified_research_system" || pkill -f "simple_langgraph_example" || echo "没有找到运行中的进程"

sleep 2

echo "正在启动系统..."
python examples/simple_langgraph_example.py &
```

使用：

```bash
chmod +x scripts/restart_system.sh
bash scripts/restart_system.sh
```

## 四、常见问题

### Q1: 如何知道系统是否在运行？

**A**: 检查进程：

```bash
ps aux | grep python | grep -E "unified_research_system|simple_langgraph"
```

### Q2: 重启后工作流仍然不可用？

**A**: 检查：

1. **环境变量是否生效**：
   ```bash
   python3 -c "import os; print('ENABLE_UNIFIED_WORKFLOW:', os.getenv('ENABLE_UNIFIED_WORKFLOW', 'not set'))"
   ```

2. **LangGraph 是否安装**：
   ```bash
   python3 -c "import langgraph; print('✅ LangGraph 已安装')"
   ```

3. **查看初始化日志**：
   ```bash
   grep -i "统一工作流" research_system.log
   ```

### Q3: 如何确保环境变量生效？

**A**: 

```bash
# 方法1：在启动前设置
export ENABLE_UNIFIED_WORKFLOW=true
python your_script.py

# 方法2：在 .env 文件中设置（推荐）
echo "ENABLE_UNIFIED_WORKFLOW=true" >> .env

# 方法3：在启动脚本中设置
python -c "
import os
os.environ['ENABLE_UNIFIED_WORKFLOW'] = 'true'
# 然后导入和启动系统
"
```

## 五、最佳实践

### 1. 使用启动脚本

创建一个启动脚本，确保环境变量正确设置：

```python
# examples/start_system.py
import os
import asyncio
from dotenv import load_dotenv
from pathlib import Path

# 加载 .env 文件
project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env')

# 确保环境变量设置
os.environ.setdefault('ENABLE_UNIFIED_WORKFLOW', 'true')
os.environ.setdefault('ENABLE_BROWSER_VISUALIZATION', 'true')

async def main():
    from src.unified_research_system import create_unified_research_system
    
    system = await create_unified_research_system()
    
    # 测试查询
    from src.unified_research_system import ResearchRequest
    request = ResearchRequest(query="What is the capital of France?")
    result = await system.execute_research(request)
    print(f"结果: {result.answer}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. 验证启动

每次启动后运行验证：

```bash
# 快速验证
python3 scripts/test_workflow_initialization.py
```

### 3. 监控日志

```bash
# 实时查看日志
tail -f research_system.log | grep -E "工作流|workflow|初始化"
```

## 六、故障排除

如果重启后仍然有问题：

1. **运行完整诊断**：
   ```bash
   python3 scripts/diagnose_workflow.py
   ```

2. **检查系统状态**：
   ```bash
   python3 scripts/test_workflow_initialization.py
   ```

3. **查看详细日志**：
   ```bash
   tail -100 research_system.log
   ```

4. **参考故障排除指南**：
   - [工作流初始化问题排查](./troubleshooting/workflow_initialization.md)
   - [工作流快速修复](./troubleshooting/workflow_quick_fix.md)

