# 📖 RANGEN 用户指南

欢迎使用RANGEN系统的用户指南。本文档提供系统的全面使用说明，帮助您充分利用RANGEN的各项功能。

## 📋 目录

1. [快速开始](#快速开始)
2. [系统概述](#系统概述)
3. [核心功能使用](#核心功能使用)
4. [配置管理](#配置管理)
5. [监控和调试](#监控和调试)
6. [最佳实践](#最佳实践)
7. [故障排除](#故障排除)

## 🚀 快速开始

### 系统要求

- **Python**: 3.8 或更高版本
- **内存**: 至少 4GB RAM（推荐 8GB+）
- **磁盘空间**: 至少 2GB 可用空间
- **网络**: 互联网连接（用于访问外部API）

### 安装步骤

1. **克隆仓库**:
```bash
git clone https://github.com/your-repo/RANGEN.git
cd RANGEN
```

2. **安装依赖**:
```bash
pip install -r requirements.txt
```

3. **环境配置**:
```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑.env文件，添加您的API密钥
# DEEPSEEK_API_KEY=your_api_key_here
# STEPFLASH_API_KEY=your_stepflash_api_key_here
```

4. **启动系统**:
```bash
# 启动完整系统
python scripts/start_unified_server.py --port 8080

# 或者只启动API服务器
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

5. **验证安装**:
打开浏览器访问 `http://localhost:8080` 或 `http://localhost:8000/docs`。

## 📊 系统概述

### RANGEN 是什么？

RANGEN是一个先进的多智能体研究系统，具有以下核心特点：

- **多模型架构**: 支持多种LLM提供商，智能路由请求
- **反思型架构**: 基于Reflexion/LATS框架的自我优化能力
- **知识检索**: 集成了RAG（检索增强生成）能力
- **工作流可视化**: 实时查看LangGraph工作流执行过程
- **动态配置**: 运行时配置管理和热更新

### 系统组件

1. **智能体系统**: 14个专业智能体，覆盖不同领域
2. **路由引擎**: 智能模型选择和请求路由
3. **知识管理系统**: 向量数据库和文档检索
4. **监控系统**: 性能监控和可观测性
5. **训练框架**: LLM训练和优化能力

## 🎯 核心功能使用

### 基本查询

#### 通过Web界面
1. 访问 `http://localhost:8080`
2. 在输入框中输入您的问题
3. 点击"执行查询"按钮
4. 实时查看工作流执行过程和结果

#### 通过API
```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什么是人工智能？",
    "context": "请提供详细的解释",
    "priority": "normal"
  }'
```

#### 通过Python代码
```python
import asyncio
from src.unified_research_system import create_unified_research_system

async def main():
    system = await create_unified_research_system()
    result = await system.execute_research(
        query="什么是人工智能？",
        context={}
    )
    
    if result.success:
        print(f"答案: {result.answer}")
        print(f"置信度: {result.confidence}")
    await system.cleanup()

asyncio.run(main())
```

### 高级功能

#### 批量查询
```bash
curl -X POST http://localhost:8000/research/batch \
  -H "Content-Type: application/json" \
  -d '{
    "queries": ["什么是AI？", "什么是机器学习？"],
    "priority": "normal"
  }'
```

#### 自定义工作流
```python
from src.core.langgraph_unified_workflow import UnifiedResearchWorkflow

# 自定义工作流配置
workflow = UnifiedResearchWorkflow(
    system=system,
    config={
        "enable_parallel_execution": True,
        "max_iterations": 3,
        "enable_reflection": True
    }
)
```

## ⚙️ 配置管理

RANGEN提供强大的动态配置管理系统，允许运行时调整系统行为。

### 启动配置系统

```python
from src.core.intelligent_router import IntelligentRouter

# 创建智能路由器实例
router = IntelligentRouter(enable_advanced_features=True)

# 系统自动启动：
# - 配置API服务器 (http://localhost:8080)
# - Web管理界面 (http://localhost:8081)
```

### 基本配置操作

#### 更新路由阈值
```python
# 调整简单查询的最大复杂度阈值
router.update_routing_threshold('simple_max_complexity', 0.08)

# 调整复杂查询的最小置信度阈值
router.update_routing_threshold('complex_min_confidence', 0.75)
```

#### 管理关键词
```python
# 添加路由关键词
router.add_routing_keyword('question_words', 'what')
router.add_routing_keyword('question_words', 'how')
router.add_routing_keyword('question_words', 'why')

# 移除关键词
router.remove_routing_keyword('question_words', 'what')
```

#### 应用配置模板
```python
# 应用保守模板（更倾向于使用本地模型）
router.apply_config_template('conservative')

# 应用激进模板（更倾向于使用付费模型）
router.apply_config_template('aggressive')

# 应用平衡模板（默认）
router.apply_config_template('balanced')
```

### 高级配置管理

#### 导入/导出配置
```python
# 导出当前配置到文件
router.export_config('backup_config.json')

# 从文件导入配置
router.import_config('custom_config.json')

# 导出为环境变量格式
router.export_as_env_vars('config.env')
```

#### 配置验证
```python
# 验证配置有效性
validation_result = router.validate_config()

if validation_result.is_valid:
    print("✅ 配置有效")
else:
    print(f"❌ 配置问题: {validation_result.issues}")
```

#### 配置监控
```python
# 获取配置使用统计
stats = router.get_config_statistics()
print(f"配置更新次数: {stats['update_count']}")
print(f"最后更新时间: {stats['last_updated']}")
```

## 🔍 监控和调试

### 系统监控

#### 查看日志
```bash
# 查看系统日志
tail -f logs/research_system.log

# 查看工作流日志
tail -f logs/langgraph_workflow.log

# 查看配置系统日志
tail -f logs/dynamic_config.log
```

#### 性能指标
系统自动记录以下指标：
- **节点执行时间**: 每个LangGraph节点的执行时间
- **API调用统计**: 各LLM提供商的调用次数和成功率
- **Token使用**: 各模型的Token消耗
- **内存使用**: 系统内存和CPU使用情况

访问 `http://localhost:8080/metrics` 查看实时指标。

### 调试工具

#### 工作流可视化
访问 `http://localhost:8080` 查看实时工作流执行过程。

#### 调试模式
```bash
# 启用详细调试日志
export DEBUG_MODE=true
export LOG_LEVEL=DEBUG

# 启动系统
python scripts/start_unified_server.py --port 8080
```

#### 性能分析
```python
from src.services.performance_analyzer import PerformanceAnalyzer

analyzer = PerformanceAnalyzer()
report = analyzer.generate_performance_report()

print(f"平均响应时间: {report.avg_response_time:.2f}秒")
print(f"成功率: {report.success_rate:.1%}")
print(f"最慢的节点: {report.slowest_node}")
```

## 💡 最佳实践

### 查询优化

1. **明确的问题**: 提供清晰、具体的问题描述
2. **适当的上下文**: 提供相关背景信息
3. **分步查询**: 复杂问题分解为多个简单查询
4. **使用批量接口**: 多个相关查询使用批量接口

### 成本控制

1. **模型选择**: 简单问题使用本地模型或成本效益模型
2. **缓存利用**: 重复查询会自动使用缓存
3. **请求合并**: 相关请求合并为批量请求
4. **监控使用量**: 定期检查API使用统计

### 性能调优

1. **并行执行**: 启用并行处理提高响应速度
2. **缓存配置**: 调整缓存策略优化性能
3. **超时设置**: 根据网络状况调整超时时间
4. **资源管理**: 合理分配内存和CPU资源

## 🛠️ 故障排除

### 常见问题

#### 问题1: 系统启动失败

**可能原因**:
1. 端口被占用
2. 依赖包缺失
3. 环境变量未配置
4. 权限不足

**解决方案**:
```bash
# 检查端口占用
lsof -i :8080
lsof -i :8000

# 安装缺失的依赖
pip install -r requirements.txt

# 检查环境变量
cat .env | grep API_KEY

# 查看详细错误日志
tail -f logs/research_system.log
```

#### 问题2: 查询超时

**可能原因**:
1. 网络连接问题
2. API服务不可用
3. 查询过于复杂
4. 系统资源不足

**解决方案**:
1. 检查网络连接
2. 验证API密钥有效性
3. 简化查询或分步执行
4. 增加系统资源或超时时间

#### 问题3: 知识检索失败

**可能原因**:
1. 知识库未初始化
2. 向量数据库错误
3. 检索服务未启动

**解决方案**:
```bash
# 初始化知识库
python scripts/init_knowledge_base.py

# 重启检索服务
python scripts/restart_retrieval_service.py

# 检查检索服务状态
curl http://localhost:8000/api/v1/retrieval/health
```

#### 问题4: 配置更新不生效

**可能原因**:
1. 配置缓存未刷新
2. 权限问题
3. 配置格式错误

**解决方案**:
```python
# 强制刷新配置缓存
router.refresh_config_cache()

# 验证配置权限
router.check_config_permissions()

# 重新加载配置
router.reload_config()
```

### 获取帮助

1. **查看日志**: 详细错误信息在日志文件中
2. **社区支持**: 访问GitHub Discussions获取社区帮助
3. **文档参考**: 查看[完整文档](../README.md)
4. **问题报告**: 在GitHub Issues中报告问题

## 📚 进阶资源

- **架构设计**: [架构文档](../architecture/README.md)
- **开发指南**: [开发文档](../development/README.md)
- **API参考**: [API文档](../development/api-reference/)
- **最佳实践**: [优化指南](../best-practices/README.md)
- **训练框架**: [模型训练指南](../reference/models/training-framework.md)

## 🎯 下一步

1. **探索功能**: 尝试系统的各项高级功能
2. **定制配置**: 根据您的需求调整系统配置
3. **集成开发**: 将RANGEN集成到您的应用中
4. **贡献代码**: 参与开源社区，改进系统

祝您使用愉快！🚀