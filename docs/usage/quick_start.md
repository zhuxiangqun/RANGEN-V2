# RANGEN 快速开始指南

## 🎉 所有测试已通过，系统已就绪！

所有 29 个测试均已通过（100% 通过率），系统已准备就绪，可以开始使用！

## 🚀 三种使用方式

### 方式 1：浏览器可视化界面（最简单）⭐

**启动**：
```bash
python examples/start_visualization_server.py
```

**使用**：
1. 打开浏览器访问：`http://localhost:8080`
2. 在输入框中输入问题
3. 点击"执行查询"
4. 实时查看工作流执行过程

**特点**：
- ✅ 最直观的界面
- ✅ 实时查看执行状态
- ✅ 查看详细的工作流过程
- ✅ 无需编程知识

### 方式 2：REST API（适合集成）

**启动**：
```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

**使用**：
```bash
# 执行查询
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是人工智能？"}'
```

**API 文档**：
- 访问 `http://localhost:8000/docs` 查看完整的 API 文档

### 方式 3：Python 代码（最灵活）

**示例代码**：
```python
import asyncio
from src.unified_research_system import create_unified_research_system

async def main():
    # 创建系统
    system = await create_unified_research_system()
    
    # 执行查询
    result = await system.execute_research(
        query="什么是人工智能？",
        context={}
    )
    
    # 查看结果
    print(f"答案: {result.answer}")
    print(f"置信度: {result.confidence}")
    
    # 清理
    await system.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

## 📝 使用示例

### 简单查询（快速）
```python
result = await system.execute_research(
    query="什么是Python？",
    context={}
)
# 通常 < 10 秒完成
```

### 复杂查询（需要推理）
```python
result = await system.execute_research(
    query="比较深度学习和机器学习的区别",
    context={}
)
# 通常 30-120 秒完成
```

## ⚙️ 配置

### 环境变量（可选）

```bash
# LLM API 配置
export DEEPSEEK_API_KEY=your_api_key

# 可视化端口
export VISUALIZATION_PORT=8080

# 启用统一工作流
export ENABLE_UNIFIED_WORKFLOW=true
```

## 📚 更多信息

- **完整使用指南**：`docs/usage/system_usage_guide.md`
- **测试文档**：`tests/README_TEST_TOOLS.md`
- **API 文档**：启动 API 服务器后访问 `/docs`

## 🎯 开始使用

选择一种方式，开始您的第一个查询吧！

**推荐**：从浏览器可视化界面开始，这是最直观的方式。

