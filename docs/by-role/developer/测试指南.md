# 单元测试指南

## 📖 概述

本指南介绍如何在RANGEN系统中编写和运行单元测试。RANGEN系统使用Python的`unittest`框架和`pytest`框架进行测试，支持同步和异步测试，提供了丰富的测试基础设施和工具。

## 🎯 测试目标

### 核心测试原则
1. **全面覆盖**：核心模块测试覆盖率≥80%，重要功能≥95%
2. **快速反馈**：测试运行快速，提供即时反馈
3. **可靠性**：测试稳定可靠，不产生假阳性或假阴性
4. **可维护性**：测试代码清晰、可读、易于维护
5. **隔离性**：测试之间相互独立，不产生副作用

### 测试级别
- **单元测试**：测试单个函数、类或模块的功能
- **集成测试**：测试多个模块或系统的协作
- **性能测试**：测试系统性能和资源使用情况
- **端到端测试**：测试完整的用户工作流程

## 🏗️ 测试基础设施

### 测试框架基类
RANGEN系统提供了三个核心测试基类：

#### 1. RANGENTestCase (基础测试类)
```python
from tests.test_framework import RANGENTestCase

class MyTestCase(RANGENTestCase):
    def setUp(self):
        super().setUp()
        # 测试前准备
        
    def tearDown(self):
        # 测试后清理
        super().tearDown()
    
    def test_example(self):
        # 测试逻辑
        pass
```

#### 2. AsyncTestCase (异步测试类)
```python
from tests.test_framework import AsyncTestCase

class MyAsyncTestCase(AsyncTestCase):
    async def test_async_function(self):
        # 异步测试逻辑
        result = await async_function()
        self.assertEqual(result, expected_value)
```

#### 3. MockTestCase (模拟测试类)
```python
from tests.test_framework import MockTestCase

class MyMockTestCase(MockTestCase):
    def test_with_mocks(self):
        # 创建模拟对象
        mock_service = self.create_mock("service")
        mock_service.process.return_value = "mocked_result"
        
        # 使用模拟对象测试
        result = my_function(mock_service)
        self.assertEqual(result, "mocked_result")
```

### 测试工具函数
```python
from tests.test_framework import create_mock_agent, create_mock_config, create_test_data

# 创建模拟智能体
mock_agent = create_mock_agent()

# 创建模拟配置
test_config = create_mock_config()

# 创建测试数据
test_data = create_test_data()
```

## 📝 编写单元测试

### 智能体测试示例
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能体单元测试示例
"""

import unittest
import asyncio
from unittest.mock import Mock, patch
from tests.test_framework import AsyncTestCase, MockTestCase

class TestKnowledgeRetrievalAgent(AsyncTestCase):
    """知识检索智能体测试"""
    
    def setUp(self):
        super().setUp()
        # 模拟智能体类
        self.agent_class = Mock()
        self.agent_class.return_value.name = "KnowledgeRetrievalAgent"
        self.agent_class.return_value.process = Mock(return_value={"result": "test"})
    
    async def test_agent_initialization(self):
        """测试智能体初始化"""
        agent = self.agent_class()
        self.assertEqual(agent.name, "KnowledgeRetrievalAgent")
    
    async def test_agent_processing(self):
        """测试智能体处理"""
        agent = self.agent_class()
        result = agent.process("test query")
        self.assertEqual(result, {"result": "test"})
    
    async def test_agent_error_handling(self):
        """测试智能体错误处理"""
        agent = self.agent_class()
        agent.process.side_effect = Exception("Processing error")
        
        with self.assertRaises(Exception) as context:
            agent.process("test query")
        
        self.assertEqual(str(context.exception), "Processing error")
```

### 服务测试示例
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务层单元测试示例
"""

import unittest
import json
from unittest.mock import Mock, patch
from tests.test_framework import RANGENTestCase

class TestConfigService(RANGENTestCase):
    """配置服务测试"""
    
    def setUp(self):
        super().setUp()
        # 创建测试配置文件
        self.config_data = {
            "timeout": 30,
            "max_retries": 3,
            "debug": True,
            "model": "deepseek-reasoner"  # 外部LLM只使用DeepSeek
        }
        self.config_path = self.create_test_config(self.config_data)
    
    def test_config_loading(self):
        """测试配置加载"""
        from src.core.config import ConfigService
        
        # 使用模拟的文件路径
        with patch('src.core.config.CONFIG_FILE_PATH', self.config_path):
            config_service = ConfigService()
            config = config_service.load_config()
            
            self.assertEqual(config["timeout"], 30)
            self.assertEqual(config["max_retries"], 3)
            self.assertTrue(config["debug"])
            self.assertEqual(config["model"], "deepseek-reasoner")
    
    def test_config_validation(self):
        """测试配置验证"""
        from src.core.config import ConfigService
        
        # 测试有效配置
        valid_config = self.config_data.copy()
        self.assertTrue(ConfigService.validate_config(valid_config))
        
        # 测试无效配置
        invalid_config = self.config_data.copy()
        invalid_config["timeout"] = "invalid"  # 应该为整数
        
        with self.assertRaises(ValueError):
            ConfigService.validate_config(invalid_config)
```

### 异步组件测试示例
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步组件测试示例
"""

import unittest
import asyncio
from unittest.mock import AsyncMock, patch
from tests.test_framework import AsyncTestCase

class TestAsyncService(AsyncTestCase):
    """异步服务测试"""
    
    def setUp(self):
        super().setUp()
        # 创建异步模拟对象
        self.async_service = AsyncMock()
        self.async_service.process_async.return_value = {"result": "async_test"}
    
    async def test_async_processing(self):
        """测试异步处理"""
        result = await self.async_service.process_async("test query")
        self.assertEqual(result, {"result": "async_test"})
    
    async def test_async_timeout(self):
        """测试异步超时处理"""
        async def slow_operation():
            await asyncio.sleep(10)  # 模拟长时间操作
            return {"result": "slow"}
        
        self.async_service.process_async = slow_operation
        
        try:
            result = await asyncio.wait_for(
                self.async_service.process_async("test query"),
                timeout=1.0
            )
            self.fail("应该超时")
        except asyncio.TimeoutError:
            pass  # 预期的超时
    
    async def test_concurrent_processing(self):
        """测试并发处理"""
        # 模拟并发处理多个请求
        self.async_service.process_async.return_value = {"result": "concurrent"}
        
        tasks = [
            self.async_service.process_async(f"query_{i}")
            for i in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # 验证所有任务都完成
        self.assertEqual(len(results), 10)
        for result in results:
            self.assertEqual(result, {"result": "concurrent"})
```

## 🔧 测试工具和辅助函数

### 创建测试数据
```python
def create_test_knowledge_data():
    """创建知识测试数据"""
    return {
        "query": "什么是机器学习？",
        "context": "机器学习是人工智能的一个分支...",
        "expected_result": "机器学习定义和技术细节"
    }

def create_test_agent_config():
    """创建智能体测试配置"""
    return {
        "agent_type": "research",
        "capabilities": ["analysis", "synthesis", "evaluation"],
        "timeout": 60,
        "model": "deepseek-reasoner"  # 外部LLM只使用DeepSeek
    }
```

### 模拟外部依赖
```python
def mock_llm_response():
    """模拟LLM响应"""
    return {
        "choices": [{
            "message": {
                "content": "这是模拟的LLM响应",
                "role": "assistant"
            }
        }],
        "usage": {
            "total_tokens": 100,
            "prompt_tokens": 70,
            "completion_tokens": 30
        }
    }

def mock_api_response():
    """模拟API响应"""
    return {
        "status": "success",
        "data": {"result": "api_response"},
        "timestamp": "2024-01-01T00:00:00Z"
    }
```

## 🚀 运行测试

### 使用测试运行器
```python
# tests/run_tests_with_timeout.py - 带超时的完整测试套件
python tests/run_tests_with_timeout.py

# 自定义超时（10分钟）
python tests/run_tests_with_timeout.py 600
```

### 运行单个测试
```python
# 运行单个测试文件
python tests/run_single_test.py 1  # 测试编号1

# 使用pytest运行特定测试
pytest tests/test_agents.py::TestKnowledgeRetrievalAgent::test_agent_initialization -v

# 运行特定测试类
pytest tests/test_agents.py::TestKnowledgeRetrievalAgent -v
```

### 快速测试和验证
```python
# 快速测试（不调用实际LLM API）
python tests/quick_test.py

# 检查测试状态
python tests/check_test_status.py

# 运行带输出的测试
python tests/run_test_with_output.py -t TestClass::test_method
```

### 使用pytest运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_agents.py

# 运行特定测试标记
pytest -m unit  # 单元测试
pytest -m integration  # 集成测试
pytest -m performance  # 性能测试

# 显示详细输出
pytest -v

# 显示输出（不捕获输出）
pytest -s

# 并行运行测试
pytest -n auto
```

## 🧪 测试策略

### 1. 智能体测试策略
```python
class AgentTestStrategy:
    """智能体测试策略"""
    
    def test_agent_initialization(self):
        """测试智能体初始化"""
        # 验证智能体名称、配置、状态
        pass
    
    def test_agent_capabilities(self):
        """测试智能体能力"""
        # 验证智能体的核心功能
        pass
    
    def test_agent_error_handling(self):
        """测试智能体错误处理"""
        # 验证错误情况的处理
        pass
    
    def test_agent_performance(self):
        """测试智能体性能"""
        # 验证响应时间、资源使用
        pass
    
    def test_agent_integration(self):
        """测试智能体集成"""
        # 验证与其他智能体或服务的协作
        pass
```

### 2. 服务测试策略
```python
class ServiceTestStrategy:
    """服务测试策略"""
    
    def test_service_initialization(self):
        """测试服务初始化"""
        pass
    
    def test_service_functionality(self):
        """测试服务功能"""
        pass
    
    def test_service_configuration(self):
        """测试服务配置"""
        pass
    
    def test_service_error_recovery(self):
        """测试服务错误恢复"""
        pass
    
    def test_service_scalability(self):
        """测试服务可扩展性"""
        pass
```

### 3. 集成测试策略
```python
class IntegrationTestStrategy:
    """集成测试策略"""
    
    def test_component_integration(self):
        """测试组件集成"""
        pass
    
    def test_workflow_integration(self):
        """测试工作流集成"""
        pass
    
    def test_api_integration(self):
        """测试API集成"""
        pass
    
    def test_data_flow_integration(self):
        """测试数据流集成"""
        pass
```

## 📊 测试覆盖率

### 生成覆盖率报告
```bash
# 安装覆盖率工具
pip install coverage

# 运行测试并生成覆盖率报告
coverage run -m pytest
coverage report -m
coverage html  # 生成HTML报告
```

### 覆盖率目标
- **核心模块**：≥80%覆盖率
- **重要功能**：≥95%覆盖率
- **公共API**：100%覆盖率
- **错误处理**：≥90%覆盖率

### 覆盖率配置
```ini
# .coveragerc
[run]
source = src/
omit = 
    src/tests/*
    src/*/tests/*
    src/*/*/tests/*

[report]
exclude_lines = 
    pragma: no cover
    def __repr__
    if self.debug:
    if settings.DEBUG
    raise AssertionError
    raise NotImplementedError
    if 0:
    if __name__ == .__main__.:
```

## 🔍 调试测试

### 常见测试问题
1. **测试失败**：检查测试数据、模拟对象、断言条件
2. **测试超时**：增加超时时间或优化测试逻辑
3. **测试卡住**：检查异步任务是否正确清理
4. **测试不稳定**：检查时间敏感逻辑或随机性

### 调试工具
```python
# 使用pdb调试
import pdb
pdb.set_trace()

# 使用logging调试
import logging
logging.basicConfig(level=logging.DEBUG)

# 使用print调试
print(f"Debug info: {variable}")
```

### 测试诊断
```bash
# 运行诊断工具
python tests/test_diagnostic_tool.py

# 检查测试进程
python tests/check_test_status.py

# 查看测试日志
tail -f research_system.log
```

## 🏆 最佳实践

### 1. 测试命名规范
- 测试类名：`Test{ClassName}` 或 `Test{FeatureName}`
- 测试方法名：`test_{functionality}_{scenario}`
- 使用描述性的测试名称

### 2. 测试结构
- 每个测试方法只测试一个功能点
- 使用setup和teardown管理测试状态
- 保持测试独立性和可重复性

### 3. 测试数据
- 使用有意义的测试数据
- 避免硬编码魔法数字
- 使用工厂函数创建测试数据

### 4. 断言使用
- 使用明确的断言消息
- 优先使用特定断言（如assertEqual, assertRaises）
- 避免过于复杂的断言逻辑

### 5. 模拟使用
- 只在必要时使用模拟
- 模拟外部依赖，而不是内部逻辑
- 保持模拟的简单性和可控性

### 6. 异步测试
- 正确处理异步上下文
- 使用适当的超时设置
- 清理异步资源

## 📋 测试清单

### 新功能测试清单
- [ ] 编写单元测试
- [ ] 编写集成测试
- [ ] 验证测试覆盖率
- [ ] 运行所有相关测试
- [ ] 修复测试失败
- [ ] 更新测试文档

### 代码修改测试清单
- [ ] 运行现有相关测试
- [ ] 添加新测试覆盖修改
- [ ] 验证向后兼容性
- [ ] 运行完整测试套件
- [ ] 检查性能影响

## 🔗 相关资源

### 测试框架文档
- [Python unittest文档](https://docs.python.org/3/library/unittest.html)
- [pytest文档](https://docs.pytest.org/)
- [coverage.py文档](https://coverage.readthedocs.io/)

### 测试工具
- [RANGEN测试框架](../tests/test_framework.py)
- [测试工具使用指南](../../tests/README_TEST_TOOLS.md)
- [测试执行指南](../extending-system/test_execution_guide.md)

### 示例测试
- [智能体测试示例](../tests/test_agents.py)
- [集成测试示例](../tests/test_langgraph_integration.py)
- [性能测试示例](../tests/test_langgraph_performance_benchmark.py)

## 📝 注意事项

### 测试环境要求
- Python 3.9+
- pytest和pytest-asyncio
- 网络连接（部分测试需要API调用）
- 足够的内存和计算资源

### 测试优化
- 使用缓存减少重复计算
- 并行运行独立测试
- 使用模拟避免外部调用
- 定期清理测试数据

### 测试维护
- 定期更新测试以适应代码变更
- 修复不稳定的测试
- 优化测试执行时间
- 保持测试文档更新

---

*最后更新：2026-03-07*  
*文档版本：1.0.0*  
*维护团队：RANGEN测试工作组*