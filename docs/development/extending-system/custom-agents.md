# 🔧 自定义智能体开发指南

本指南详细介绍如何在RANGEN系统中创建和集成自定义智能体，扩展系统能力。

## 🎯 概述

RANGEN系统采用模块化的智能体架构，支持开发者创建自定义智能体来扩展系统功能。所有智能体都基于统一的`BaseAgent`基类构建，遵循标准接口和协作协议。

### 开发流程概览

```
1. 需求分析 → 2. 智能体设计 → 3. 代码实现 → 
4. 测试验证 → 5. 注册集成 → 6. 部署使用
```

## 🏗️ 智能体架构基础

### BaseAgent基类

所有智能体都继承自`BaseAgent`基类（位于`src/agents/base_agent.py`），提供以下核心功能：

```python
class BaseAgent(ABC):
    """基础智能体抽象类"""
    
    def __init__(self, agent_id: str, capabilities: Optional[List[str]] = None, 
                 config: Optional[AgentConfig] = None, max_history_size: int = 1000):
        # 初始化智能体基础组件
        self.agent_id = agent_id
        self.capabilities = capabilities or []
        self.config_manager = AgentConfigManager(agent_id, config)
        self.performance_tracker = AgentPerformanceTracker(agent_id)
        self.history_manager = AgentHistoryManager(agent_id, max_history_size)
        
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """核心处理逻辑 - 子类必须实现"""
        pass
```

### 智能体能力模型

智能体通过`capabilities_dict`定义能力矩阵：

```python
capabilities_dict: Dict[AgentCapability, bool] = {
    AgentCapability.EXTENSIBILITY: True,           # 可扩展性
    AgentCapability.INTELLIGENCE: True,            # 智能性
    AgentCapability.AUTONOMOUS_DECISION: True,     # 自主决策
    AgentCapability.DYNAMIC_STRATEGY: True,        # 动态策略
    AgentCapability.STRATEGY_LEARNING: True,       # 策略学习
    AgentCapability.SELF_LEARNING: True,           # 自我学习
    AgentCapability.AUTOMATIC_REASONING: True,     # 自动推理
    AgentCapability.DYNAMIC_CONFIDENCE: True,      # 动态置信度
    AgentCapability.LLM_DRIVEN_RECOGNITION: True,  # LLM驱动识别
    AgentCapability.DYNAMIC_CHAIN_OF_THOUGHT: True, # 动态思维链
    AgentCapability.DYNAMIC_CLASSIFICATION: True   # 动态分类
}
```

## 🔧 创建自定义智能体

### 步骤1：创建智能体类

创建一个新的Python文件，继承`BaseAgent`基类：

```python
# src/agents/custom/my_custom_agent.py

#!/usr/bin/env python3
"""
自定义智能体示例 - 演示如何创建新的智能体
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from src.agents.base_agent import BaseAgent
from src.agents.agent_models import AgentConfig, AgentResult

logger = logging.getLogger(__name__)


@dataclass
class CustomAgentConfig(AgentConfig):
    """自定义智能体配置"""
    custom_param_1: str = "default_value"
    custom_param_2: int = 100
    enable_special_feature: bool = False


class MyCustomAgent(BaseAgent):
    """自定义智能体示例
    
    这是一个示例智能体，演示如何创建新的智能体类型。
    智能体负责处理特定类型的任务，如文本分析、数据转换等。
    """
    
    def __init__(self, agent_id: str, custom_config: Optional[CustomAgentConfig] = None, **kwargs):
        """初始化自定义智能体
        
        Args:
            agent_id: 智能体唯一标识符
            custom_config: 自定义配置参数
            **kwargs: 传递给基类的其他参数
        """
        # 合并配置
        if custom_config is None:
            custom_config = CustomAgentConfig()
        
        # 调用基类初始化
        super().__init__(agent_id=agent_id, config=custom_config, **kwargs)
        
        # 自定义初始化逻辑
        self.custom_param_1 = custom_config.custom_param_1
        self.custom_param_2 = custom_config.custom_param_2
        self.enable_special_feature = custom_config.enable_special_feature
        
        # 更新能力配置
        self.capabilities_dict.update({
            "CUSTOM_CAPABILITY": True,
            "SPECIAL_PROCESSING": self.enable_special_feature
        })
        
        # 添加自定义能力标签
        self.custom_capabilities = ["text_analysis", "data_transformation"]
        
        # 初始化自定义组件
        self._init_custom_components()
        
        logger.info(f"自定义智能体 {agent_id} 初始化完成")
    
    def _init_custom_components(self):
        """初始化自定义组件"""
        # 这里可以初始化专用的工具、模型或其他资源
        self.special_processor = None
        if self.enable_special_feature:
            # 初始化特殊处理器
            from src.services.special_processor import SpecialProcessor
            self.special_processor = SpecialProcessor()
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """核心处理逻辑
        
        Args:
            input_data: 输入数据，包含任务描述和其他参数
            
        Returns:
            处理结果，包含输出数据和元数据
        """
        # 开始性能跟踪
        self.performance_tracker.start_tracking(self.agent_id, "process")
        
        try:
            # 1. 解析输入
            task_description = input_data.get("task", "")
            parameters = input_data.get("parameters", {})
            
            # 2. 执行处理逻辑
            result = await self._execute_custom_logic(task_description, parameters)
            
            # 3. 记录成功
            self.performance_tracker.record_success(
                agent_id=self.agent_id,
                execution_time=self.performance_tracker.get_elapsed_time()
            )
            
            # 4. 返回标准化结果
            return {
                "success": True,
                "result": result,
                "agent_id": self.agent_id,
                "processing_time": self.performance_tracker.get_elapsed_time(),
                "metadata": {
                    "custom_param_1": self.custom_param_1,
                    "custom_param_2": self.custom_param_2
                }
            }
            
        except Exception as e:
            # 记录错误
            self.performance_tracker.record_error(
                agent_id=self.agent_id,
                error_message=str(e),
                execution_time=self.performance_tracker.get_elapsed_time()
            )
            
            logger.error(f"自定义智能体处理失败: {e}", exc_info=True)
            
            # 返回错误结果
            return {
                "success": False,
                "error": str(e),
                "agent_id": self.agent_id,
                "processing_time": self.performance_tracker.get_elapsed_time()
            }
    
    async def _execute_custom_logic(self, task: str, parameters: Dict[str, Any]) -> Any:
        """执行自定义逻辑
        
        这是智能体的核心业务逻辑，根据具体需求实现。
        
        Args:
            task: 任务描述
            parameters: 任务参数
            
        Returns:
            处理结果
        """
        logger.info(f"执行自定义逻辑: {task}")
        
        # 示例：根据任务类型执行不同处理
        if "analyze" in task.lower():
            return await self._analyze_text(task, parameters)
        elif "transform" in task.lower():
            return await self._transform_data(task, parameters)
        elif "generate" in task.lower():
            return await self._generate_content(task, parameters)
        else:
            # 默认处理
            return {
                "original_task": task,
                "processed_by": self.agent_id,
                "result": f"任务 '{task}' 已处理",
                "parameters": parameters
            }
    
    async def _analyze_text(self, task: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """文本分析处理"""
        text = parameters.get("text", "")
        
        # 简单的文本分析示例
        word_count = len(text.split())
        char_count = len(text)
        
        # 如果有特殊处理器，使用它
        if self.enable_special_feature and self.special_processor:
            analysis = await self.special_processor.analyze(text)
        else:
            # 基础分析
            analysis = {
                "sentiment": "neutral",  # 简化示例
                "keywords": ["example", "analysis"],
                "summary": f"文本分析完成，共{word_count}个单词"
            }
        
        return {
            "analysis_type": "text_analysis",
            "text_preview": text[:100] + "..." if len(text) > 100 else text,
            "statistics": {
                "word_count": word_count,
                "character_count": char_count
            },
            "analysis_result": analysis
        }
    
    async def _transform_data(self, task: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """数据转换处理"""
        data = parameters.get("data", {})
        transform_type = parameters.get("transform_type", "default")
        
        # 数据转换逻辑
        transformed_data = {}
        
        if transform_type == "uppercase_keys":
            # 示例：键转换为大写
            for key, value in data.items():
                if isinstance(key, str):
                    transformed_data[key.upper()] = value
                else:
                    transformed_data[key] = value
        elif transform_type == "filter_numeric":
            # 示例：过滤数值数据
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    transformed_data[key] = value
        else:
            # 默认转换：添加处理标记
            transformed_data = {
                "original_data": data,
                "transformed_at": self._get_current_timestamp(),
                "processed_by": self.agent_id
            }
        
        return {
            "transform_type": transform_type,
            "input_data_size": len(str(data)),
            "output_data_size": len(str(transformed_data)),
            "transformed_data": transformed_data
        }
    
    async def _generate_content(self, task: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """内容生成处理"""
        topic = parameters.get("topic", "general")
        length = parameters.get("length", 100)
        
        # 简单的内容生成示例
        content = f"这是关于{topic}的生成内容，长度约{length}字。"
        content += " " * max(0, length - len(content))
        
        return {
            "content_type": "generated_text",
            "topic": topic,
            "content_length": len(content),
            "content": content[:length]
        }
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    # ==================== 可选：高级功能 ====================
    
    def enable_self_learning(self, learning_rate: float = 0.01):
        """启用自我学习能力"""
        from src.agents.self_evolving_mixin import SelfEvolvingMixin
        
        # 混入自学习能力
        self.self_evolver = SelfEvolvingMixin(
            agent_id=self.agent_id,
            learning_rate=learning_rate
        )
        
        logger.info(f"智能体 {self.agent_id} 已启用自我学习")
    
    async def learn_from_experience(self, experience_data: Dict[str, Any]):
        """从经验中学习"""
        if hasattr(self, 'self_evolver'):
            await self.self_evolver.learn(experience_data)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return self.performance_tracker.get_report()
```

### 步骤2：创建配置类（可选）

如果智能体需要自定义配置参数，可以创建配置类：

```python
# src/agents/config/custom_agent_config.py

from dataclasses import dataclass
from typing import Optional, List
from src.agents.agent_models import AgentConfig


@dataclass
class MyCustomAgentConfig(AgentConfig):
    """MyCustomAgent配置类"""
    
    # 自定义参数
    processing_mode: str = "standard"
    max_processing_time: int = 30000  # 毫秒
    enable_cache: bool = True
    cache_ttl: int = 3600  # 秒
    
    # 模型参数
    model_name: str = "default_model"
    temperature: float = 0.7
    max_tokens: int = 1000
    
    # 业务参数
    allowed_domains: List[str] = None
    blacklist_patterns: List[str] = None
    
    def __post_init__(self):
        """后初始化处理"""
        if self.allowed_domains is None:
            self.allowed_domains = ["general"]
        if self.blacklist_patterns is None:
            self.blacklist_patterns = []
```

### 步骤3：注册智能体到工厂

在智能体工厂中注册新智能体：

```python
# src/agents/agent_factory.py 或创建单独的注册文件

from src.agents.agent_factory import AgentFactory
from src.agents.custom.my_custom_agent import MyCustomAgent, CustomAgentConfig


def register_custom_agents():
    """注册自定义智能体"""
    
    # 注册MyCustomAgent
    AgentFactory.register_agent_type(
        agent_type="my_custom_agent",
        agent_class=MyCustomAgent,
        default_config=CustomAgentConfig(
            agent_id="custom_agent_template",
            capabilities=["text_analysis", "data_transformation"],
            max_history_size=500
        ),
        description="自定义智能体，支持文本分析和数据转换"
    )
    
    # 可以在应用启动时调用此函数
    # 例如在 src/__init__.py 或应用启动脚本中
```

## ⚙️ 配置管理

### 通过配置文件配置

在配置文件中添加智能体配置：

```yaml
# config/agents/custom_agents.yaml

my_custom_agent:
  enabled: true
  instances:
    text_analyzer:
      agent_id: "text_analyzer_001"
      config:
        custom_param_1: "advanced_mode"
        custom_param_2: 200
        enable_special_feature: true
        capabilities:
          - "text_analysis"
          - "sentiment_detection"
        max_history_size: 1000
      deployment:
        replicas: 2
        resources:
          cpu: "0.5"
          memory: "512Mi"
    
    data_transformer:
      agent_id: "data_transformer_001"
      config:
        custom_param_1: "efficient_mode"
        custom_param_2: 150
        enable_special_feature: false
        capabilities:
          - "data_transformation"
          - "data_validation"
```

### 通过环境变量配置

```bash
# 环境变量配置示例
export CUSTOM_AGENT_ENABLED=true
export CUSTOM_AGENT_MODE=advanced
export CUSTOM_AGENT_MAX_PROCESSING_TIME=30000
export CUSTOM_AGENT_CACHE_ENABLED=true
```

### 动态配置加载

```python
from src.config.unified import UnifiedConfigCenter

# 从统一配置中心加载配置
config_center = UnifiedConfigCenter()
agent_config = config_center.get_agent_config("my_custom_agent")

# 创建智能体实例
agent = MyCustomAgent(
    agent_id=agent_config["agent_id"],
    custom_config=CustomAgentConfig(**agent_config["config"])
)
```

## 🧪 测试智能体

### 单元测试

```python
# tests/agents/test_my_custom_agent.py

import pytest
import asyncio
from unittest.mock import Mock, patch
from src.agents.custom.my_custom_agent import MyCustomAgent, CustomAgentConfig


class TestMyCustomAgent:
    """MyCustomAgent测试类"""
    
    @pytest.fixture
    def agent(self):
        """创建测试智能体实例"""
        config = CustomAgentConfig(
            agent_id="test_agent",
            custom_param_1="test_value",
            custom_param_2=100,
            enable_special_feature=False
        )
        return MyCustomAgent(agent_id="test_agent", custom_config=config)
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent):
        """测试智能体初始化"""
        assert agent.agent_id == "test_agent"
        assert agent.custom_param_1 == "test_value"
        assert agent.custom_param_2 == 100
        assert agent.enable_special_feature is False
        assert "CUSTOM_CAPABILITY" in agent.capabilities_dict
        assert agent.status == "initialized"
    
    @pytest.mark.asyncio
    async def test_process_text_analysis(self, agent):
        """测试文本分析功能"""
        input_data = {
            "task": "分析文本内容",
            "parameters": {
                "text": "这是一个测试文本，用于验证智能体功能。",
                "analysis_type": "basic"
            }
        }
        
        result = await agent.process(input_data)
        
        assert result["success"] is True
        assert "result" in result
        assert result["result"]["analysis_type"] == "text_analysis"
        assert "statistics" in result["result"]
        assert result["agent_id"] == "test_agent"
    
    @pytest.mark.asyncio
    async def test_process_data_transformation(self, agent):
        """测试数据转换功能"""
        input_data = {
            "task": "转换数据格式",
            "parameters": {
                "data": {"name": "test", "value": 123},
                "transform_type": "uppercase_keys"
            }
        }
        
        result = await agent.process(input_data)
        
        assert result["success"] is True
        assert "transformed_data" in result["result"]
        transformed_data = result["result"]["transformed_data"]
        assert "NAME" in transformed_data  # 键已转换为大写
    
    @pytest.mark.asyncio
    async def test_process_error_handling(self, agent):
        """测试错误处理"""
        # 模拟处理过程中的异常
        with patch.object(agent, '_execute_custom_logic', side_effect=Exception("测试异常")):
            input_data = {"task": "触发异常"}
            result = await agent.process(input_data)
            
            assert result["success"] is False
            assert "error" in result
            assert "测试异常" in result["error"]
    
    def test_performance_tracking(self, agent):
        """测试性能跟踪"""
        # 模拟执行
        agent.performance_tracker.record_success(
            agent_id="test_agent",
            execution_time=1500
        )
        
        report = agent.get_performance_report()
        assert "test_agent" in report
        assert "success_count" in report["test_agent"]
```

### 集成测试

```python
# tests/integration/test_custom_agent_integration.py

import pytest
import asyncio
from src.agents.agent_factory import AgentFactory
from src.agents.custom.my_custom_agent import MyCustomAgent


class TestCustomAgentIntegration:
    """自定义智能体集成测试"""
    
    @pytest.fixture(autouse=True)
    def setup_factory(self):
        """设置测试环境"""
        # 注册智能体到工厂
        from src.agents.custom.my_custom_agent import CustomAgentConfig
        AgentFactory.register_agent_type(
            agent_type="my_custom_agent",
            agent_class=MyCustomAgent,
            default_config=CustomAgentConfig()
        )
        yield
        # 清理
        AgentFactory._agent_types.pop("my_custom_agent", None)
    
    @pytest.mark.asyncio
    async def test_agent_factory_creation(self):
        """测试通过工厂创建智能体"""
        agent = AgentFactory.create_agent(
            agent_type="my_custom_agent",
            agent_id="factory_created_agent"
        )
        
        assert isinstance(agent, MyCustomAgent)
        assert agent.agent_id == "factory_created_agent"
    
    @pytest.mark.asyncio  
    async def test_agent_communication(self):
        """测试智能体间通信"""
        from src.agents.agent_communication import AgentCommunicationProtocol
        
        # 创建两个智能体
        agent1 = MyCustomAgent(agent_id="agent_1")
        agent2 = MyCustomAgent(agent_id="agent_2")
        
        # 创建通信协议
        comm_protocol = AgentCommunicationProtocol()
        
        # 模拟消息传递
        message = {
            "sender": "agent_1",
            "recipient": "agent_2",
            "message_type": "task_request",
            "content": {"task": "协助处理"}
        }
        
        # 在实际系统中，这里会有实际的消息传递逻辑
        # 这里简化为直接调用
        response = await comm_protocol.send_message(message)
        
        assert response is not None
```

### 性能测试

```python
# tests/performance/test_custom_agent_performance.py

import pytest
import asyncio
import time
from src.agents.custom.my_custom_agent import MyCustomAgent


class TestCustomAgentPerformance:
    """自定义智能体性能测试"""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_processing_latency(self):
        """测试处理延迟"""
        agent = MyCustomAgent(agent_id="perf_test_agent")
        
        # 测试多次执行的平均延迟
        test_cases = [
            {"task": "分析短文本", "parameters": {"text": "短文本"}},
            {"task": "分析中文本", "parameters": {"text": "中等长度文本" * 10}},
            {"task": "分析长文本", "parameters": {"text": "长文本" * 100}}
        ]
        
        latencies = []
        for test_case in test_cases:
            start_time = time.time()
            result = await agent.process(test_case)
            end_time = time.time()
            
            assert result["success"] is True
            latencies.append(end_time - start_time)
        
        avg_latency = sum(latencies) / len(latencies)
        print(f"平均延迟: {avg_latency:.3f}秒")
        
        # 断言延迟在可接受范围内
        assert avg_latency < 1.0  # 平均延迟应小于1秒
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_processing(self):
        """测试并发处理能力"""
        agent = MyCustomAgent(agent_id="concurrent_test_agent")
        
        # 并发执行多个任务
        tasks = []
        for i in range(10):
            task_data = {
                "task": f"并发任务{i}",
                "parameters": {"text": f"任务{i}内容"}
            }
            tasks.append(agent.process(task_data))
        
        # 并发执行
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = end_time - start_time
        print(f"10个并发任务总时间: {total_time:.3f}秒")
        
        # 验证所有任务都成功
        success_count = sum(1 for r in results if r["success"])
        assert success_count == 10
        
        # 并发性能断言
        assert total_time < 5.0  # 10个并发任务应在5秒内完成
```

## 🔌 集成到系统

### 方式1：直接实例化使用

```python
# 在服务或应用代码中直接使用

from src.agents.custom.my_custom_agent import MyCustomAgent, CustomAgentConfig

# 创建配置
config = CustomAgentConfig(
    agent_id="production_analyzer",
    custom_param_1="production_mode",
    custom_param_2=300,
    enable_special_feature=True,
    capabilities=["text_analysis", "sentiment_detection", "content_summarization"]
)

# 创建智能体实例
agent = MyCustomAgent(agent_id="production_analyzer", custom_config=config)

# 使用智能体
async def handle_request(request_data):
    """处理请求"""
    result = await agent.process(request_data)
    return result
```

### 方式2：通过路由系统集成

```python
# 在路由系统中注册智能体

from src.core.routing.agent_router import AgentRouter
from src.agents.custom.my_custom_agent import MyCustomAgent

class CustomAgentRouter:
    """自定义智能体路由器"""
    
    def __init__(self):
        self.router = AgentRouter()
        self._register_custom_agents()
    
    def _register_custom_agents(self):
        """注册自定义智能体"""
        # 注册文本分析路由
        self.router.register_route(
            route_pattern="analyze/text/*",
            agent_type="my_custom_agent",
            agent_config={
                "capabilities": ["text_analysis"],
                "processing_mode": "fast"
            },
            priority=1
        )
        
        # 注册数据转换路由
        self.router.register_route(
            route_pattern="transform/data/*",
            agent_type="my_custom_agent",
            agent_config={
                "capabilities": ["data_transformation"],
                "processing_mode": "accurate"
            },
            priority=2
        )
    
    async def route_request(self, request):
        """路由请求到合适的智能体"""
        return await self.router.route(request)
```

### 方式3：通过工作流集成

```python
# 在LangGraph工作流中集成

from langgraph.graph import StateGraph, END
from src.agents.custom.my_custom_agent import MyCustomAgent

def create_custom_workflow():
    """创建包含自定义智能体的工作流"""
    
    # 创建工作流
    workflow = StateGraph(name="CustomAgentWorkflow")
    
    # 添加节点
    workflow.add_node("input_validation", validate_input)
    workflow.add_node("custom_processing", custom_processing_node)
    workflow.add_node("result_formatting", format_result)
    
    # 添加边
    workflow.add_edge("input_validation", "custom_processing")
    workflow.add_edge("custom_processing", "result_formatting")
    workflow.add_edge("result_formatting", END)
    
    return workflow.compile()


async def custom_processing_node(state):
    """自定义处理节点"""
    # 创建或获取智能体实例
    agent = MyCustomAgent(agent_id="workflow_agent")
    
    # 执行处理
    result = await agent.process({
        "task": state.get("task", ""),
        "parameters": state.get("parameters", {})
    })
    
    # 更新状态
    return {**state, "processing_result": result}
```

## 🚀 最佳实践

### 设计原则

1. **单一职责**：每个智能体专注于一个特定领域或功能
2. **接口标准化**：遵循`BaseAgent`接口规范
3. **配置驱动**：通过配置文件管理智能体行为
4. **错误处理**：完善的错误处理和日志记录
5. **性能监控**：集成性能跟踪和监控

### 性能优化建议

1. **资源管理**：
   - 合理设置`max_history_size`避免内存泄漏
   - 使用连接池管理外部资源连接
   - 实现懒加载机制减少启动时间

2. **并发处理**：
   - 支持异步处理提高吞吐量
   - 实现请求队列和限流机制
   - 使用线程池处理CPU密集型任务

3. **缓存策略**：
   - 实现结果缓存减少重复计算
   - 使用LRU缓存管理频繁访问的数据
   - 支持缓存失效和更新机制

### 安全考虑

1. **输入验证**：
   ```python
   def validate_input(input_data):
       """验证输入数据"""
       # 检查必需字段
       required_fields = ["task", "parameters"]
       for field in required_fields:
           if field not in input_data:
               raise ValueError(f"缺少必需字段: {field}")
       
       # 检查参数类型
       if not isinstance(input_data["parameters"], dict):
           raise TypeError("parameters必须是字典类型")
       
       # 检查任务长度限制
       task = input_data.get("task", "")
       if len(task) > 10000:
           raise ValueError("任务描述过长")
   ```

2. **访问控制**：
   - 实现基于角色的访问控制
   - 验证调用者权限
   - 记录所有操作日志

3. **数据保护**：
   - 敏感数据脱敏处理
   - 加密存储敏感信息
   - 遵守数据保护法规

### 监控和日志

1. **结构化日志**：
   ```python
   import structlog
   
   logger = structlog.get_logger(__name__)
   
   async def process(self, input_data):
       # 记录结构化日志
       logger.info("开始处理任务",
                   agent_id=self.agent_id,
                   task_type=input_data.get("task_type", "unknown"),
                   input_size=len(str(input_data)))
       
       # ... 处理逻辑
       
       logger.info("任务处理完成",
                   agent_id=self.agent_id,
                   processing_time=processing_time,
                   success=result["success"])
   ```

2. **性能指标**：
   - 记录处理延迟、成功率、错误率
   - 集成Prometheus指标导出
   - 设置性能告警阈值

3. **健康检查**：
   ```python
   async def health_check(self):
       """健康检查"""
       return {
           "status": "healthy",
           "agent_id": self.agent_id,
           "timestamp": self._get_current_timestamp(),
           "metrics": {
               "uptime": self.performance_tracker.get_uptime(),
               "success_rate": self.performance_tracker.get_success_rate(),
               "avg_processing_time": self.performance_tracker.get_avg_processing_time()
           }
       }
   ```

## 🔧 故障排除

### 常见问题

1. **智能体初始化失败**
   - 检查依赖包是否安装
   - 验证配置文件格式
   - 检查日志获取详细错误信息

2. **处理性能低下**
   - 检查资源使用情况（CPU、内存）
   - 优化算法复杂度
   - 增加缓存策略

3. **通信问题**
   - 验证网络连接
   - 检查消息格式
   - 确认服务发现配置

### 调试技巧

```python
# 启用调试模式
agent = MyCustomAgent(
    agent_id="debug_agent",
    custom_config=CustomAgentConfig(
        debug_mode=True,
        log_level="DEBUG"
    )
)

# 添加调试钩子
import pdb

class DebuggableAgent(MyCustomAgent):
    """可调试的智能体"""
    
    async def process(self, input_data):
        # 设置断点
        if self.config.debug_mode:
            pdb.set_trace()
        
        return await super().process(input_data)
```

## 📚 示例项目

### 完整示例：情感分析智能体

查看示例项目：[examples/sentiment_analysis_agent](examples/sentiment_analysis_agent/)

包含：
- 完整的智能体实现
- 单元测试和集成测试
- 配置文件示例
- 部署脚本
- 使用文档

### 模板项目

快速开始模板：[templates/custom-agent-template](templates/custom-agent-template/)

```bash
# 使用模板创建新智能体
python scripts/create_agent_template.py \
  --name "MyNewAgent" \
  --type "analysis" \
  --output-dir "src/agents/custom/"
```

## 🔗 相关资源

- [BaseAgent源代码](../../src/agents/base_agent.py)
- [智能体配置模型](../../src/agents/agent_models.py)
- [智能体工厂](../../src/agents/agent_factory.py)
- [系统智能体清单](system_agents_inventory.md)
- [单元测试指南](../testing/unit-testing.md)
- [API参考](../api-reference/)

## 📝 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2026-03-07 | 初始版本，创建自定义智能体开发指南 |
| 1.0.1 | 2026-03-07 | 添加完整代码示例和测试指南 |
| 1.0.2 | 2026-03-07 | 完善集成指南和最佳实践 |

---

*最后更新：2026-03-07*  
*文档版本：1.0.2*  
*维护团队：RANGEN开发工作组*
