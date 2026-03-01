# RANGEN 系统使用指南

## 🎉 恭喜！所有测试已通过

所有 29 个测试均已通过（100% 通过率），系统已准备就绪，可以开始使用！

## 🚀 快速开始

### 方式 1：浏览器可视化界面（推荐）⭐

这是最直观的使用方式，可以实时查看工作流执行过程。

```bash
# 启动可视化服务器
python examples/start_visualization_server.py
```

**使用步骤**：
1. 启动服务器后，在浏览器中打开：`http://localhost:8080`
2. 在输入框中输入您的问题
3. 点击"执行查询"按钮
4. 实时查看：
   - 工作流执行状态
   - 节点执行时间线
   - 编排过程详情
   - 最终答案

**功能特点**：
- ✅ 实时可视化工作流执行
- ✅ 查看每个节点的执行状态
- ✅ 查看详细的编排过程
- ✅ 查看最终答案和引用

### 方式 2：REST API 接口

适合集成到其他系统或应用程序中。

```bash
# 启动 API 服务器
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

**API 文档**：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

**主要接口**：

1. **健康检查**
   ```bash
   curl http://localhost:8000/health
   ```

2. **执行研究查询**
   ```bash
   curl -X POST http://localhost:8000/research \
     -H "Content-Type: application/json" \
     -d '{
       "query": "什么是人工智能？",
       "context": "请提供详细的解释",
       "priority": "normal"
     }'
   ```

3. **批量查询**
   ```bash
   curl -X POST http://localhost:8000/research/batch \
     -H "Content-Type: application/json" \
     -d '{
       "queries": ["什么是AI？", "什么是机器学习？"],
       "priority": "normal"
     }'
   ```

### 方式 3：Python 代码直接调用

适合在 Python 脚本或 Jupyter Notebook 中使用。

```python
import asyncio
from src.unified_research_system import create_unified_research_system

async def main():
    # 创建系统实例
    system = await create_unified_research_system()
    
    # 执行查询
    result = await system.execute_research(
        query="什么是人工智能？",
        context={}
    )
    
    # 查看结果
    if result.success:
        print(f"✅ 查询成功！")
        print(f"答案: {result.answer}")
        print(f"置信度: {result.confidence}")
        print(f"执行时间: {result.execution_time:.2f}秒")
    else:
        print(f"❌ 查询失败: {result.error}")
    
    # 清理资源
    await system.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

### 方式 4：使用 LangGraph 工作流（高级）

如果您想直接使用 LangGraph 工作流：

```python
import asyncio
from src.core.langgraph_unified_workflow import UnifiedResearchWorkflow
from src.unified_research_system import UnifiedResearchSystem

async def main():
    # 创建系统和工作流
    system = UnifiedResearchSystem()
    await system.initialize()
    
    workflow = UnifiedResearchWorkflow(system=system)
    
    # 执行查询
    result = await workflow.execute(
        query="什么是人工智能？",
        context={}
    )
    
    # 查看结果
    print(f"成功: {result.get('success')}")
    print(f"答案: {result.get('answer')}")
    print(f"路由路径: {result.get('route_path')}")
    print(f"执行时间: {result.get('execution_time')}秒")
    
    # 查看节点执行时间
    node_times = result.get('node_execution_times', {})
    for node, time in node_times.items():
        print(f"  {node}: {time:.2f}秒")

if __name__ == "__main__":
    asyncio.run(main())
```

## 📋 使用场景示例

### 场景 1：简单查询（快速回答）

```python
# 简单查询会直接使用知识检索，跳过复杂的推理流程
result = await system.execute_research(
    query="什么是Python？",
    context={}
)
# 执行时间：通常 < 10 秒
```

### 场景 2：复杂查询（需要推理）

```python
# 复杂查询会使用完整的推理链
result = await system.execute_research(
    query="比较深度学习和机器学习的区别，并解释它们在实际应用中的使用场景",
    context={}
)
# 执行时间：通常 30-120 秒
```

### 场景 3：多智能体协调查询

```python
# 需要多个智能体协作的查询
result = await system.execute_research(
    query="分析2024年AI领域的主要突破，包括技术细节、应用场景和未来趋势",
    context={}
)
# 执行时间：通常 60-180 秒
```

## ⚙️ 配置选项

### 环境变量

您可以通过环境变量配置系统行为：

```bash
# 启用统一工作流（LangGraph）
export ENABLE_UNIFIED_WORKFLOW=true

# 启用浏览器可视化
export ENABLE_BROWSER_VISUALIZATION=true

# 可视化服务器端口
export VISUALIZATION_PORT=8080

# 快速测试模式（减少 ChiefAgent 迭代次数）
export FAST_TEST_MODE=false

# 启用子图封装
export USE_SUBGRAPH_ENCAPSULATION=false

# 启用并行执行
export ENABLE_PARALLEL_EXECUTION=false

# 启用备用路由
export ENABLE_FALLBACK_ROUTING=false
```

### LLM 配置

```bash
# DeepSeek API 配置
export DEEPSEEK_API_KEY=your_api_key
export DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 模型选择
export LLM_MODEL=deepseek-reasoner  # 推理模型
export FAST_LLM_MODEL=deepseek-chat  # 快速模型
```

## 📊 系统功能

### 核心功能

1. **智能路由**：根据查询复杂度自动选择执行路径
   - 简单查询 → 直接知识检索
   - 复杂查询 → 完整推理链
   - 多智能体查询 → 多智能体协调

2. **知识检索**：从多个知识源检索信息
   - 知识库管理系统（KMS）
   - FAISS 向量数据库
   - Wiki 检索
   - 自动回退机制

3. **推理引擎**：多步骤推理和答案生成
   - 步骤生成
   - 证据收集
   - 答案提取
   - 答案验证

4. **多智能体协调**：ChiefAgent 协调多个专家智能体
   - 任务分解
   - 团队组建
   - 任务分配
   - 执行协调

### 高级功能

1. **检查点恢复**：支持工作流状态保存和恢复
2. **错误恢复**：自动重试和备用路由
3. **性能优化**：缓存、LLM 批量调用
4. **状态版本管理**：支持状态版本保存和回滚
5. **动态工作流**：支持运行时修改工作流

## 🔍 监控和调试

### 查看日志

```bash
# 查看系统日志
tail -f logs/research_system.log

# 查看工作流日志
tail -f logs/langgraph_workflow.log
```

### 性能监控

系统会自动记录：
- 节点执行时间
- API 调用次数
- Token 使用情况
- 内存和 CPU 使用情况

在可视化界面中可以查看这些指标。

## 🛠️ 故障排除

### 问题 1：系统启动失败

**检查**：
1. 确保所有依赖已安装：`pip install -r requirements.txt`
2. 检查环境变量配置
3. 查看日志文件：`logs/research_system.log`

### 问题 2：查询超时

**解决方案**：
1. 增加超时时间（默认 600 秒）
2. 使用简单查询测试
3. 检查网络连接和 API 可用性

### 问题 3：知识检索失败

**解决方案**：
1. 系统会自动回退到 Wiki 检索
2. 检查知识库是否已初始化
3. 查看知识检索服务日志

## 📚 更多资源

- **测试工具文档**：`tests/README_TEST_TOOLS.md`
- **架构文档**：`docs/architecture/`
- **修复文档**：`docs/fixes/`
- **API 文档**：启动 API 服务器后访问 `/docs`

## 🎯 下一步

1. **开始使用**：选择一种使用方式，开始您的第一个查询
2. **探索功能**：尝试不同类型的查询，了解系统能力
3. **查看可视化**：使用浏览器可视化界面，深入了解系统工作流程
4. **集成应用**：使用 REST API 将系统集成到您的应用中

## 💡 提示

- **简单查询**：使用简短、直接的问题，系统会快速响应
- **复杂查询**：系统会自动识别并使用完整的推理链
- **批量查询**：使用批量接口可以提高效率
- **缓存**：重复查询会自动使用缓存，大幅提升速度

祝您使用愉快！🚀

