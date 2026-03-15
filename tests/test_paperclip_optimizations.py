#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试基于Paperclip设计模式优化的系统组件

这个测试验证了以下优化组件：
1. 声明式配置系统 (declarative_config.py)
2. 处理器链模式 (processor_chain.py) 
3. 统一存储抽象层 (storage_abstraction.py)
4. 增强事件系统 (event_system.py)
5. 增强参数验证系统 (validation_system.py)
"""

import asyncio
import sys
import os
import tempfile
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.declarative_config import (
    get_config_registry, register_llm_model, 
    register_routing_strategy, register_processor, on_event
)
from src.core.processor_chain import (
    ProcessorChain, BaseProcessor, ProcessingContext,
    ProcessorResult, InputValidatorProcessor,
    CostOptimizerProcessor, PerformanceEvaluatorProcessor,
    ABTestingProcessor, CircuitBreakerProcessor, FinalSelectorProcessor
)
from src.core.storage_abstraction import (
    StorageFactory, StorageConfig, get_default_storage,
    MemoryStorageBackend, FileStorageBackend
)
from src.core.event_system import (
    get_event_bus, EventBus, EventTypes,
    ConfigRegisteredEvent, ModelSelectedEvent,
    EventMetadata, event_subscriber, on_config_registered
)
from src.core.validation_system import (
    Validator, Required, String, Integer, Float,
    Range, Length, Regex, get_llm_model_validator,
    ValidationResult, ValidationError
)


def test_declarative_config():
    """测试声明式配置系统"""
    print("测试声明式配置系统...")
    
    # 获取注册表
    registry = get_config_registry()
    
    # 定义测试类
    class TestLLMModel:
        def __init__(self, name):
            self.name = name
    
    class TestRoutingStrategy:
        def __init__(self, name):
            self.name = name
    
    class TestProcessor:
        def __init__(self, name):
            self.name = name
    
    # 使用装饰器注册
    @register_llm_model(
        name="test-model",
        provider="test",
        cost_per_token=0.001,
        max_tokens=4000,
        temperature=0.7
    )
    class DecoratedTestLLMModel(TestLLMModel):
        pass
    
    @register_routing_strategy(
        name="test-strategy",
        description="测试路由策略",
        processors=["input_validator", "cost_optimizer"],
        cost_weight=0.5,
        performance_weight=0.3,
        quality_weight=0.2,
        priority=5
    )
    class DecoratedTestRoutingStrategy(TestRoutingStrategy):
        pass
    
    @register_processor(
        name="test-processor",
        description="测试处理器",
        async_execution=True,
        timeout=10.0,
        max_retries=3
    )
    class DecoratedTestProcessor(TestProcessor):
        async def process(self, context):
            """测试处理器方法"""
            return context
    
    # 验证注册
    assert "test-model" in registry.llm_models
    assert "test-strategy" in registry.routing_strategies
    assert "test-processor" in registry.processors
    
    # 验证配置
    model_config = registry.llm_models["test-model"]
    assert model_config["provider"] == "test"
    assert model_config["cost_per_token"] == 0.001
    
    strategy_config = registry.routing_strategies["test-strategy"]
    assert strategy_config["description"] == "测试路由策略"
    assert strategy_config["priority"] == 5
    
    processor_config = registry.processors["test-processor"]
    assert processor_config["async_execution"] is True
    assert processor_config["timeout"] == 10.0
    
    print("✓ 声明式配置系统测试通过")
    return True


def test_processor_chain():
    """测试处理器链模式"""
    print("测试处理器链模式...")
    
    # 创建处理器链
    chain = ProcessorChain(name="test-processor-chain")
    
    # 添加处理器（在创建处理器时设置优先级）
    chain.add_processor(InputValidatorProcessor(name="input_validator", priority=10))
    chain.add_processor(CostOptimizerProcessor(name="cost_optimizer", priority=20))
    chain.add_processor(PerformanceEvaluatorProcessor(name="performance_evaluator", priority=30))
    chain.add_processor(ABTestingProcessor(name="ab_testing", priority=40))
    chain.add_processor(CircuitBreakerProcessor(name="circuit_breaker", priority=50))
    chain.add_processor(FinalSelectorProcessor(name="final_selector", priority=60))
    
    # 创建测试上下文
    context = ProcessingContext(
        request={
            "request_id": "test-request-123",
            "user_id": "test-user",
            "query": "测试提示",  # InputValidatorProcessor 需要 query 字段
            "task_type": "general",  # InputValidatorProcessor 需要 task_type 字段
            "budget": 0.1,
            "quality_requirements": {"min_confidence": 0.8}
        },
        available_models=["deepseek-reasoner", "deepseek-chat", "llama-3"]
    )
    
    # 测试处理器链执行
    async def run_test():
        result_context = await chain.execute(context)
        
        # 验证结果
        assert result_context is not None
        assert result_context.selected_model is not None
        assert result_context.decision_reason is not None
        assert result_context.final_decision is True
        
        print(f"✓ 处理器链选择模型: {result_context.selected_model}")
        print(f"✓ 决策原因: {result_context.decision_reason}")
        
        return True
    
    # 运行异步测试
    success = asyncio.run(run_test())
    
    print("✓ 处理器链模式测试通过")
    return success


def test_storage_abstraction():
    """测试存储抽象层"""
    print("测试存储抽象层...")
    
    async def run_tests():
        # 创建临时目录用于文件存储测试
        with tempfile.TemporaryDirectory() as temp_dir:
            # 测试内存存储
            memory_storage = StorageFactory.create_memory_storage()
            
            # 测试文件存储
            file_storage = StorageFactory.create_file_storage(
                storage_dir=os.path.join(temp_dir, "test_storage"),
                file_extension=".json",
                pretty_print=True
            )
            
            test_data = {
                "name": "test-config",
                "value": 123,
                "timestamp": datetime.now().isoformat(),
                "nested": {"key": "value"}
            }
            
            async def test_storage(storage, storage_name):
                # 测试保存
                save_success = await storage.save("test-key", test_data, immediate=True)
                assert save_success, f"{storage_name}保存失败"
                
                # 测试加载
                loaded_data = await storage.load("test-key", use_cache=True)
                assert loaded_data is not None, f"{storage_name}加载失败"
                assert loaded_data["name"] == test_data["name"], f"{storage_name}数据不一致"
                
                # 测试存在检查
                exists = await storage.exists("test-key")
                assert exists, f"{storage_name}存在检查失败"
                
                # 测试统计信息
                stats = storage.get_stats()
                assert stats is not None, f"{storage_name}统计信息失败"
                
                # 测试删除
                delete_success = await storage.delete("test-key")
                assert delete_success, f"{storage_name}删除失败"
                
                # 验证删除
                exists_after_delete = await storage.exists("test-key")
                assert not exists_after_delete, f"{storage_name}删除后仍然存在"
                
                print(f"✓ {storage_name}测试通过")
                return True
            
            # 运行测试
            success_memory = await test_storage(memory_storage, "内存存储")
            success_file = await test_storage(file_storage, "文件存储")
            
            # 测试默认存储
            default_storage = get_default_storage()
            assert default_storage is not None, "默认存储获取失败"
            
            # 清理
            await memory_storage.close()
            await file_storage.close()
            
            return success_memory and success_file
    
    # 运行异步测试
    success = asyncio.run(run_tests())
    print("✓ 存储抽象层测试通过")
    return success


def test_event_system():
    """测试事件系统"""
    print("测试事件系统...")
    
    # 获取事件总线
    event_bus = get_event_bus()
    
    # 记录接收到的事件
    received_events = []
    
    # 定义事件处理器
    @event_subscriber(EventTypes.CONFIG_REGISTERED)
    async def handle_config_registered(event):
        received_events.append(("config_registered", event))
        print(f"收到配置注册事件: {event.config_name}")
    
    @event_subscriber(EventTypes.MODEL_SELECTED)
    async def handle_model_selected(event):
        received_events.append(("model_selected", event))
        print(f"收到模型选择事件: {event.model_name}")
    
    # 创建并发布测试事件
    async def publish_test_events():
        # 发布配置注册事件
        config_event = ConfigRegisteredEvent(
            metadata=EventMetadata(
                event_id="test-config-123",
                event_type=EventTypes.CONFIG_REGISTERED,
                timestamp=datetime.now(),
                source="test_system"
            ),
            config_type="llm_model",
            config_name="test-event-model",
            config_data={"provider": "test", "cost": 0.001},
            source_class="TestLLMModel"
        )
        
        await event_bus.publish(
            EventTypes.CONFIG_REGISTERED,
            config_event,
            source="test_event_system",
            wait_for_processing=True
        )
        
        # 发布模型选择事件
        model_event = ModelSelectedEvent(
            metadata=EventMetadata(
                event_id="test-model-456",
                event_type=EventTypes.MODEL_SELECTED,
                timestamp=datetime.now(),
                source="test_system"
            ),
            request_id="test-request-123",
            model_name="deepseek-reasoner",
            model_provider="deepseek",
            selection_reason="cost_optimization",
            cost_estimate=0.05,
            latency_estimate=250.0,
            alternatives=["claude-3", "llama-3"]
        )
        
        await event_bus.publish(
            EventTypes.MODEL_SELECTED,
            model_event,
            source="test_event_system",
            wait_for_processing=True
        )
        
        return True
    
    # 运行测试
    success = asyncio.run(publish_test_events())
    
    # 验证事件接收
    assert len(received_events) >= 2, f"预期收到2个事件，实际收到{len(received_events)}个"
    
    # 验证事件内容
    for event_type, event in received_events:
        if event_type == "config_registered":
            assert event.config_name == "test-event-model"
        elif event_type == "model_selected":
            assert event.model_name == "deepseek-reasoner"
    
    # 获取统计信息
    stats = event_bus.get_bus_stats()
    assert stats["events_published"] >= 2, f"事件发布数量不足: {stats['events_published']}"
    
    print(f"✓ 事件系统测试通过，收到 {len(received_events)} 个事件")
    return success


def test_validation_system():
    """测试验证系统"""
    print("测试验证系统...")
    
    # 测试基本验证器
    validator = Validator()
    
    validator.add_rule("name", [
        Required(),
        String(),
        Length(min=1, max=50),
        Regex(r"^[a-zA-Z0-9_-]+$", message="名称只能包含字母、数字、下划线和短横线")
    ])
    
    validator.add_rule("age", [
        Required(),
        Integer(),
        Range(min=0, max=150, message="年龄必须在0到150之间")
    ])
    
    validator.add_rule("email", [
        Required(),
        String(),
        Regex(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", message="必须是有效的邮箱地址")
    ])
    
    validator.add_rule("score", [
        Float(),
        Range(min=0.0, max=100.0, message="分数必须在0到100之间")
    ])
    
    # 测试有效数据
    valid_data = {
        "name": "test_user_123",
        "age": 25,
        "email": "test@example.com",
        "score": 85.5
    }
    
    # 测试无效数据
    invalid_data = {
        "name": "invalid name!",  # 包含空格和感叹号
        "age": -5,  # 负数
        "email": "not-an-email",
        "score": 150.0  # 超过最大值
    }
    
    async def run_validation_tests():
        # 测试有效数据
        valid_result = await validator.validate(valid_data)
        assert valid_result.valid, f"有效数据验证失败: {valid_result.errors}"
        assert len(valid_result.errors) == 0, f"有效数据不应有错误: {valid_result.errors}"
        
        # 测试无效数据
        invalid_result = await validator.validate(invalid_data)
        assert not invalid_result.valid, "无效数据应该验证失败"
        assert len(invalid_result.errors) >= 4, f"预期至少4个错误，实际{len(invalid_result.errors)}个"
        
        # 验证具体错误
        error_fields = {error.field for error in invalid_result.errors}
        expected_fields = {"name", "age", "email", "score"}
        assert error_fields == expected_fields, f"错误字段不匹配: {error_fields}"
        
        print("✓ 基本验证器测试通过")
        
        # 测试预定义验证器
        llm_validator = get_llm_model_validator()
        
        valid_llm_config = {
            "name": "deepseek-reasoner",
            "provider": "deepseek",
            "cost_per_token": 0.03,
            "max_tokens": 4000,
            "temperature": 0.7,
            "timeout": 60,
            "max_retries": 3,
            "enabled": True
        }
        
        invalid_llm_config = {
            "name": "",  # 空名称
            "provider": "",  # 空提供商
            "cost_per_token": -0.1,  # 负数成本
            "max_tokens": 0,  # 0 token
            "temperature": 3.0,  # 温度过高
            "timeout": 0,  # 0超时
            "max_retries": -1,  # 负数重试
            "enabled": "yes"  # 不是布尔值
        }
        
        # 测试有效LLM配置
        llm_valid_result = await llm_validator.validate(valid_llm_config)
        assert llm_valid_result.valid, f"有效LLM配置验证失败: {llm_valid_result.errors}"
        
        # 测试无效LLM配置
        llm_invalid_result = await llm_validator.validate(invalid_llm_config)
        assert not llm_invalid_result.valid, "无效LLM配置应该验证失败"
        
        print(f"✓ LLM验证器测试通过，发现 {len(llm_invalid_result.errors)} 个错误")
        
        return True
    
    # 运行测试
    success = asyncio.run(run_validation_tests())
    
    print("✓ 验证系统测试通过")
    return success


def test_integration():
    """测试组件集成"""
    print("测试组件集成...")
    
    async def run_integration_test():
        # 获取所有组件
        registry = get_config_registry()
        event_bus = get_event_bus()
        default_storage = get_default_storage()
        
        # 清除之前的事件处理器（确保干净状态）
        event_bus.clear_handlers()
        
        # 创建事件接收标志
        config_registered_event_received = False
        
        # 订阅通配符事件以调试
        @event_subscriber("*")
        async def debug_event_handler(event):
            print(f"调试 - 收到事件类型: {event.metadata.event_type}, 源: {event.metadata.source}")
        
        @event_subscriber(EventTypes.CONFIG_REGISTERED)
        async def integration_event_handler(event):
            nonlocal config_registered_event_received
            config_registered_event_received = True
            print(f"集成测试收到事件: {event.config_name}")
            
            # 验证后保存到存储
            if default_storage:
                await default_storage.save(
                    f"config:{event.config_name}",
                    event.config_data,
                    immediate=True
                )
        
        # 集成事件系统（这会增强registry.emit_event以发布到事件总线）
        from src.core.event_system import EventSystemIntegration
        EventSystemIntegration.integrate_with_config_registry(registry)
        
        # 定义测试类
        class IntegratedLLMModel:
            def __init__(self, name):
                self.name = name
        
        # 使用装饰器注册（触发事件）
        @register_llm_model(
            name="integration-model",
            provider="integration-test",
            cost_per_token=0.002,
            max_tokens=8000,
            temperature=0.8
        )
        class IntegratedTestModel(IntegratedLLMModel):
            pass
        
        # 等待事件处理（增加等待时间确保异步事件处理完成）
        for _ in range(5):  # 最多重试5次
            if config_registered_event_received:
                break
            await asyncio.sleep(0.1)
        
        # 验证事件接收
        assert config_registered_event_received, "配置注册事件未收到"
        
        # 验证配置注册
        assert "integration-model" in registry.llm_models
        
        # 验证存储（如果启用）
        if registry.get_storage():
            stored_data = await registry.get_storage().load(
                f"{registry._storage_namespace}:llm_model:integration-model",
                use_cache=True
            )
            assert stored_data is not None, "配置未保存到存储"
        
        print("✓ 组件集成测试通过")
        return True
    
    # 运行集成测试
    success = asyncio.run(run_integration_test())
    
    print("✓ 集成测试通过")
    return success


def main():
    """运行所有测试"""
    print("=" * 60)
    print("开始测试基于Paperclip设计模式优化的系统组件")
    print("=" * 60)
    
    results = []
    
    try:
        # 测试声明式配置系统
        results.append(("声明式配置系统", test_declarative_config()))
    except Exception as e:
        print(f"✗ 声明式配置系统测试失败: {e}")
        results.append(("声明式配置系统", False))
    
    try:
        # 测试处理器链模式
        results.append(("处理器链模式", test_processor_chain()))
    except Exception as e:
        print(f"✗ 处理器链模式测试失败: {e}")
        results.append(("处理器链模式", False))
    
    try:
        # 测试存储抽象层
        results.append(("存储抽象层", test_storage_abstraction()))
    except Exception as e:
        print(f"✗ 存储抽象层测试失败: {e}")
        results.append(("存储抽象层", False))
    
    try:
        # 测试事件系统
        results.append(("事件系统", test_event_system()))
    except Exception as e:
        print(f"✗ 事件系统测试失败: {e}")
        results.append(("事件系统", False))
    
    try:
        # 测试验证系统
        results.append(("验证系统", test_validation_system()))
    except Exception as e:
        print(f"✗ 验证系统测试失败: {e}")
        results.append(("验证系统", False))
    
    try:
        # 测试组件集成
        results.append(("组件集成", test_integration()))
    except Exception as e:
        print(f"✗ 组件集成测试失败: {e}")
        results.append(("组件集成", False))
    
    # 打印结果摘要
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for component, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{component:20} {status}")
        
        if success:
            passed += 1
        else:
            failed += 1
    
    print("-" * 60)
    print(f"总计: {len(results)} 个测试, 通过: {passed}, 失败: {failed}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！基于Paperclip的优化组件工作正常。")
        return True
    else:
        print(f"\n⚠️  {failed} 个测试失败，请检查问题。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)