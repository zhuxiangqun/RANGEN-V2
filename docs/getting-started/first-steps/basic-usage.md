# 📚 RANGEN 基本使用指南

本文档介绍RANGEN系统的基本使用方法，包括系统启动、核心功能操作和日常维护。

## 📋 目录

1. [系统概述](#系统概述)
2. [快速启动](#快速启动)
3. [核心功能使用](#核心功能使用)
4. [配置管理](#配置管理)
5. [监控和诊断](#监控和诊断)
6. [常见操作](#常见操作)
7. [故障处理](#故障处理)

## 📊 系统概述

### 什么是RANGEN？

RANGEN是一个基于动态难度加载（DDL）和分级智能策略的多智能体研究系统。系统采用双轨制分层架构，包含：

- **前端大脑（本地）**：处理简单查询、路由和预处理
- **后端大脑（云端）**：处理复杂推理、决策和综合
- **19个智能体体系**：支撑95%以上的业务功能
- **DDL-RAG混合架构**：动态适应查询复杂度

### 核心特性

1. **智能路由**：根据查询复杂度自动选择执行路径
2. **多模型支持**：支持DeepSeek、Step-3.5-Flash、本地模型等
3. **知识检索**：集成RAG（检索增强生成）能力
4. **反思型架构**：基于Reflexion/LATS框架的自我优化
5. **工作流可视化**：实时查看LangGraph工作流执行过程

## 🚀 快速启动

### 启动方式选择

RANGEN提供多种启动方式，适应不同使用场景：

#### 方式1：统一服务器（推荐）

启动包含所有功能的统一服务器：

```bash
# 启动统一服务器（包含可视化和配置管理）
python scripts/start_unified_server.py --port 8080

# 或者使用智能启动器（自动处理端口冲突）
python scripts/smart_server_launcher.py
```

**访问地址**：
- Web界面：`http://localhost:8080`
- API文档：`http://localhost:8080/docs`

#### 方式2：单独组件启动

如果需要单独启动特定组件：

```bash
# 启动API服务器
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# 启动可视化服务器
python examples/start_visualization_server.py --port 8081
```

#### 方式3：开发模式启动

启用详细日志和调试功能：

```bash
# 设置开发环境变量
export DEBUG_MODE=true
export LOG_LEVEL=DEBUG

# 启动开发服务器
python scripts/start_unified_server.py --port 8080 --dev
```

### 验证安装

启动后验证系统正常运行：

```bash
# API健康检查
curl http://localhost:8080/health

# 或者通过Python验证
python -c "
import requests
response = requests.get('http://localhost:8080/health')
print(f'健康状态: {response.json()}')
"
```

## 🎯 核心功能使用

### 执行查询

#### 通过Web界面查询

1. 访问 `http://localhost:8080`
2. 在输入框中输入问题
3. 点击"执行查询"按钮
4. 实时查看工作流执行过程和结果

**界面功能**：
- **查询输入**：输入自然语言问题
- **执行控制**：开始、暂停、停止查询
- **工作流可视化**：查看LangGraph节点执行状态
- **结果展示**：查看答案、置信度和执行详情

#### 通过API查询

```bash
# 基本查询
curl -X POST http://localhost:8080/research \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什么是人工智能？",
    "context": "请提供详细的解释",
    "priority": "normal"
  }'

# 批量查询
curl -X POST http://localhost:8080/research/batch \
  -H "Content-Type: application/json" \
  -d '{
    "queries": ["什么是机器学习？", "什么是深度学习？"],
    "priority": "normal"
  }'
```

#### 通过Python代码查询

```python
import asyncio
from src.unified_research_system import create_unified_research_system

async def main():
    # 创建系统实例
    system = await create_unified_research_system()
    
    try:
        # 执行简单查询
        result = await system.execute_research(
            query="什么是人工智能？",
            context={"detail_level": "basic"},
            priority="normal"
        )
        
        # 处理结果
        if result.success:
            print(f"✅ 查询成功！")
            print(f"答案: {result.answer}")
            print(f"置信度: {result.confidence}")
            print(f"执行时间: {result.execution_time:.2f}秒")
            print(f"使用的模型: {result.model_used}")
            
            # 查看执行详情
            if hasattr(result, 'execution_details'):
                print(f"路由路径: {result.execution_details.get('route_path')}")
                print(f"节点执行时间: {result.execution_details.get('node_times')}")
        else:
            print(f"❌ 查询失败: {result.error}")
            print(f"错误详情: {result.error_details}")
            
    finally:
        # 清理资源
        await system.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

### 使用场景示例

#### 场景1：简单事实查询

```python
# 简单事实查询会使用直接检索策略
result = await system.execute_research(
    query="Python是什么？",
    context={},
    priority="fast"  # 使用快速模式
)
# 预计执行时间：< 5秒
```

#### 场景2：复杂推理查询

```python
# 复杂推理查询会使用完整推理链
result = await system.execute_research(
    query="比较深度学习和机器学习的区别，并解释它们在实际应用中的使用场景",
    context={"format": "structured", "detail_level": "comprehensive"},
    priority="normal"
)
# 预计执行时间：30-120秒
```

#### 场景3：多智能体协作查询

```python
# 需要多智能体协作的复杂查询
result = await system.execute_research(
    query="分析2024年AI领域的主要突破，包括技术细节、应用场景和未来趋势",
    context={
        "format": "report",
        "sections": ["技术突破", "应用场景", "未来趋势"],
        "sources": ["学术论文", "技术报告", "行业分析"]
    },
    priority="high"  # 使用高优先级模式
)
# 预计执行时间：60-180秒
```

## ⚙️ 配置管理

### 环境变量配置

系统支持通过环境变量配置：

```bash
# 核心配置
export RANGEN_ENVIRONMENT="production"
export RANGEN_LOG_LEVEL="INFO"
export RANGEN_API_KEY="your-api-key"

# 模型配置
export DEEPSEEK_API_KEY="sk-..."
export STEPFLASH_API_KEY="sk-..."
export LOCAL_MODEL_ENABLED="true"

# 性能配置
export MAX_WORKERS=4
export REQUEST_TIMEOUT=30
export CACHE_SIZE=1000

# 监控配置
export ENABLE_OPENTELEMETRY="true"
export ENABLE_METRICS="true"
```

### 配置文件管理

系统支持YAML格式配置文件：

```yaml
# config/rangen.yaml
version: "3.0"
environment: "development"

models:
  enabled:
    - "deepseek-chat"
    - "step-3.5-flash"
    - "local-llama"
  
  routing:
    strategy: "adaptive"
    enable_reflection: true
    fallback_enabled: true

routing:
  thresholds:
    simple_max_complexity: 0.08
    complex_min_confidence: 0.75
  keywords:
    question_words: ["what", "how", "why", "explain", "compare"]

monitoring:
  enabled: true
  metrics:
    - "latency"
    - "success_rate"
    - "cost"
    - "quality"
  alerting:
    enabled: true
    channels:
      - "console"
      - "file"
```

### 动态配置更新

系统支持运行时配置更新：

```python
from src.core.intelligent_router import IntelligentRouter

# 创建路由器实例
router = IntelligentRouter()

# 更新路由阈值
router.update_routing_threshold('simple_max_complexity', 0.08)

# 添加关键词
router.add_routing_keyword('question_words', 'what')

# 应用配置模板
router.apply_config_template('balanced')  # balanced, conservative, aggressive

# 获取当前配置
config = router.get_routing_config()
print(f"当前配置: {config}")
```

## 🔍 监控和诊断

### 系统监控

#### 查看日志

```bash
# 查看系统日志
tail -f logs/research_system.log

# 查看工作流日志
tail -f logs/langgraph_workflow.log

# 查看错误日志
tail -f logs/error.log

# 查看性能日志
tail -f logs/performance.log
```

#### 监控指标

系统自动记录以下指标：

- **节点执行时间**：每个LangGraph节点的执行时间
- **API调用统计**：各LLM提供商的调用次数和成功率
- **Token使用**：各模型的Token消耗统计
- **内存使用**：系统内存和CPU使用情况
- **请求延迟**：端到端请求延迟分布

访问 `http://localhost:8080/metrics` 查看实时指标。

### 诊断工具

#### 工作流可视化

访问 `http://localhost:8080` 查看实时工作流执行过程：

- **节点状态**：查看每个节点的执行状态（等待、执行中、完成、失败）
- **执行路径**：查看查询的执行路径和路由决策
- **性能指标**：查看每个节点的执行时间和资源消耗
- **错误信息**：查看失败节点的错误详情

#### 调试模式

启用调试模式获取详细信息：

```python
# 启用详细调试
from src.core.monitoring_system import MonitoringSystem

monitor = MonitoringSystem()
monitor.enable_debug_mode()

# 或者通过环境变量
import os
os.environ['DEBUG_MODE'] = 'true'
os.environ['LOG_LEVEL'] = 'DEBUG'
```

#### 性能分析

```python
from src.services.performance_analyzer import PerformanceAnalyzer

# 创建性能分析器
analyzer = PerformanceAnalyzer()

# 生成性能报告
report = analyzer.generate_performance_report()

print(f"平均响应时间: {report.avg_response_time:.2f}秒")
print(f"成功率: {report.success_rate:.1%}")
print(f"最慢的节点: {report.slowest_node}")
print(f"Token使用统计: {report.token_usage}")
print(f"成本统计: {report.cost_summary}")

# 导出报告
analyzer.export_report('performance_report.json')
```

## 🔄 常见操作

### 系统管理

#### 启动和停止

```bash
# 启动系统
python scripts/start_unified_server.py --port 8080

# 停止系统（优雅关闭）
curl -X POST http://localhost:8080/shutdown

# 强制停止
pkill -f "start_unified_server.py"
```

#### 重启系统

```bash
# 重启API服务器
python scripts/restart_server.py

# 重启所有服务
python scripts/restart_system.sh
```

#### 清理缓存

```bash
# 清理模型缓存
python scripts/fix_model_cache.sh

# 清理工作流缓存
python src/core/cache_system.py --clear

# 清理所有临时文件
python scripts/cleanup_temporary_files.py
```

### 数据管理

#### 备份和恢复

```bash
# 备份数据库
python scripts/backup_database.py --output backup.db

# 恢复数据库
python scripts/restore_database.py --input backup.db

# 备份配置文件
python scripts/backup_config.py --output config_backup/
```

#### 日志管理

```bash
# 查看日志大小
du -sh logs/

# 清理旧日志
python scripts/cleanup_old_logs.py --days 7

# 压缩日志
python scripts/compress_logs.py --output logs_archive.tar.gz
```

### 版本管理

#### 检查版本

```bash
# 检查系统版本
python -c "from src.core.config_manager import ConfigManager; print(ConfigManager().get_version())"

# 检查组件版本
python scripts/check_versions.py
```

#### 升级系统

```bash
# 更新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt

# 运行迁移脚本
python scripts/migrate.py

# 重启系统
python scripts/restart_system.sh
```

## 🛠️ 故障处理

### 常见问题

#### 问题1：系统启动失败

**症状**：服务器无法启动，端口被占用或依赖缺失

**解决方案**：
```bash
# 检查端口占用
lsof -i :8080
lsof -i :8000

# 使用不同端口启动
python scripts/start_unified_server.py --port 8082

# 检查依赖
pip install -r requirements.txt
pip install -r requirements-optional.txt

# 查看详细错误
tail -f logs/research_system.log
```

#### 问题2：查询超时

**症状**：查询长时间没有响应

**解决方案**：
```bash
# 增加超时时间
export REQUEST_TIMEOUT=120

# 检查网络连接
curl https://api.deepseek.com/v1/chat/completions

# 使用简单查询测试
curl -X POST http://localhost:8080/research \
  -H "Content-Type: application/json" \
  -d '{"query": "你好", "priority": "fast"}'

# 查看工作流状态
curl http://localhost:8080/api/v1/workflow/status
```

#### 问题3：知识检索失败

**症状**：检索不到相关信息或返回空结果

**解决方案**：
```bash
# 初始化知识库
python scripts/init_knowledge_base.py

# 重建向量数据库
python scripts/build_frames_kb_full.py

# 检查检索服务
curl http://localhost:8080/api/v1/retrieval/health

# 使用替代检索策略
export ENABLE_FALLBACK_RETRIEVAL=true
```

#### 问题4：内存不足

**症状**：系统变慢或崩溃，内存使用率高

**解决方案**：
```bash
# 限制工作线程数
export MAX_WORKERS=2

# 启用内存优化
export ENABLE_MEMORY_OPTIMIZATION=true

# 清理缓存
python src/core/cache_system.py --clear --force

# 监控内存使用
python scripts/monitor_memory.py
```

### 诊断流程

#### 步骤1：收集信息

```bash
# 收集系统状态
python scripts/check_system_status.py

# 收集环境信息
python scripts/check_current_env.py

# 收集日志信息
python scripts/collect_logs.py --output diagnostic_info/
```

#### 步骤2：分析问题

```bash
# 分析错误日志
python scripts/analyze_error_logs.py

# 分析性能问题
python scripts/profile_bottlenecks.py

# 分析工作流执行
python scripts/diagnose_workflow.py --query "问题描述"
```

#### 步骤3：解决问题

```bash
# 应用修复
python scripts/fix_common_issues.py

# 重启受影响的服务
python scripts/restart_affected_services.py

# 验证修复
python scripts/verify_fix.py
```

#### 步骤4：预防措施

```bash
# 设置监控告警
python scripts/setup_monitoring_alerts.py

# 优化配置
python scripts/optimize_configuration.py

# 创建备份
python scripts/create_backup.py
```

## 📚 学习资源

### 进一步学习

1. **高级功能**：[用户指南](../user_guide.md) - 系统高级功能详解
2. **本地模型**：[本地模型指南](./local-model-guide.md) - 使用本地模型降低成本
3. **API参考**：[开发指南](../../development/README.md) - 完整API文档
4. **架构设计**：[架构设计](../../architecture/README.md) - 系统架构详解

### 获取帮助

- **文档问题**：查看[文档中心](../../README.md)
- **技术问题**：[提交GitHub Issue](https://github.com/your-repo/RANGEN/issues)
- **功能咨询**：[参与社区讨论](https://github.com/your-repo/RANGEN/discussions)
- **紧急支持**：联系技术支持团队

### 反馈和改进

我们欢迎您的反馈和建议：

1. **报告问题**：在GitHub Issues中创建问题
2. **建议改进**：在讨论区分享您的想法
3. **贡献代码**：提交Pull Request改进系统
4. **改进文档**：直接提交文档改进

## 🎯 下一步

1. **实践操作**：按照本指南尝试系统各项功能
2. **探索高级功能**：学习用户指南中的高级功能
3. **集成开发**：将系统集成到您的应用中
4. **优化配置**：根据您的需求优化系统配置

祝您使用愉快！🚀