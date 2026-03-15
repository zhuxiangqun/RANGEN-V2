#!/usr/bin/env python3
"""
Step-3.5-Flash 使用示例
展示如何在 RANGEN 系统中使用 Step-3.5-Flash 模型
"""

import os
import sys
import asyncio
from typing import Dict, Any, List

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def example_direct_adapter_usage():
    """示例 1: 直接使用 StepFlashAdapter"""
    print("=" * 60)
    print("示例 1: 直接使用 StepFlashAdapter")
    print("=" * 60)
    
    from src.services.stepflash_adapter import StepFlashAdapter
    
    # 方法 1: 使用 OpenRouter (默认)
    print("\n1. 使用 OpenRouter 部署:")
    adapter = StepFlashAdapter(
        deployment_type="openrouter",
        api_key=os.getenv("STEPSFLASH_API_KEY", "your-api-key-here"),
        timeout=30,
        max_tokens=4096,
        temperature=0.7,
        max_retries=3
    )
    
    print(f"   部署类型: {adapter.deployment_type.value}")
    print(f"   模型名称: {adapter.model}")
    print(f"   API URL: {adapter.api_url}")
    
    # 方法 2: 使用 vLLM 本地部署
    print("\n2. 使用 vLLM 本地部署:")
    adapter = StepFlashAdapter(
        deployment_type="vllm_local",
        base_url="http://localhost:8000",
        timeout=60,
        max_retries=5,
        retry_delay=2.0
    )
    
    print(f"   部署类型: {adapter.deployment_type.value}")
    print(f"   模型名称: {adapter.model}")
    print(f"   API URL: {adapter.api_url}")
    
    # 方法 3: 使用 NVIDIA NIM
    print("\n3. 使用 NVIDIA NIM 部署:")
    adapter = StepFlashAdapter(
        deployment_type="nvidia_nim",
        api_key=os.getenv("STEPSFLASH_API_KEY", "your-nim-api-key"),
        base_url="https://api.nvidia.com/nim/v1"
    )
    
    print(f"   部署类型: {adapter.deployment_type.value}")
    print(f"   模型名称: {adapter.model}")
    print(f"   API URL: {adapter.api_url}")
    
    print("\n✅ 适配器初始化成功!")


def example_llm_integration_usage():
    """示例 2: 通过 LLMIntegration 使用 Step-3.5-Flash"""
    print("\n" + "=" * 60)
    print("示例 2: 通过 LLMIntegration 使用 Step-3.5-Flash")
    print("=" * 60)
    
    from src.core.llm_integration import LLMIntegration
    
    # 配置 Step-3.5-Flash
    config = {
        "llm_provider": "stepflash",
        "api_key": os.getenv("STEPSFLASH_API_KEY", "test-api-key"),
        "model": "step-3.5-flash",
        "base_url": "https://openrouter.ai/api/v1"  # 可选
    }
    
    llm = LLMIntegration(config)
    
    print(f"LLM 提供者: {llm.llm_provider}")
    print(f"模型: {llm.model}")
    print(f"API 密钥: {'已设置' if llm.api_key else '未设置'}")
    
    # 测试调用 (模拟模式，无真实 API 调用)
    if llm.api_key == "test-api-key" or not llm.api_key:
        print("\n⚠️  使用模拟模式 (无真实 API 密钥)")
        print("   要使用真实 API，请设置 STEPSFLASH_API_KEY 环境变量")
    
    print("\n✅ LLMIntegration 初始化成功!")


def example_adapter_factory_usage():
    """示例 3: 通过 LLMAdapterFactory 使用 Step-3.5-Flash"""
    print("\n" + "=" * 60)
    print("示例 3: 通过 LLMAdapterFactory 使用 Step-3.5-Flash")
    print("=" * 60)
    
    from src.utils.llm_client import LLMAdapterFactory
    
    # 获取可用适配器列表
    available_adapters = LLMAdapterFactory.get_available_adapters()
    print(f"可用适配器: {available_adapters}")
    
    if "stepflash" in available_adapters:
        # 创建 Step-3.5-Flash 适配器
        adapter = LLMAdapterFactory.create_adapter(
            "stepflash",
            api_key=os.getenv("STEPSFLASH_API_KEY", "test-key"),
            deployment_type="openrouter"
        )
        
        print(f"适配器类型: {type(adapter).__name__}")
        print(f"适配器部署类型: {adapter.deployment_type.value}")
        print(f"适配器模型: {adapter.model}")
        
        print("\n✅ LLMAdapterFactory 成功创建 StepFlashAdapter")
    else:
        print("❌ Step-3.5-Flash 适配器未在工厂中注册")


def example_agent_usage():
    """示例 4: 在 Agent 中使用 Step-3.5-Flash"""
    print("\n" + "=" * 60)
    print("示例 4: 在 Agent 中使用 Step-3.5-Flash")
    print("=" * 60)
    
    # 设置环境变量以使用 Step-3.5-Flash
    os.environ["LLM_PROVIDER"] = "stepflash"
    os.environ["STEPSFLASH_API_KEY"] = "mock-key-for-demo"
    
    try:
        from src.agents.reasoning_agent import ReasoningAgent
        from src.agents.tools.tool_registry import ToolRegistry
        from unittest.mock import Mock
        
        # 创建模拟工具注册表
        mock_tool_registry = Mock(spec=ToolRegistry)
        mock_tool_registry.get_all_tools.return_value = []
        
        # 创建 ReasoningAgent (会使用 LLMIntegration)
        agent = ReasoningAgent(mock_tool_registry)
        
        print(f"Agent 名称: {agent.agent_id}")
        print(f"Agent 已初始化: {agent is not None}")
        
        # 检查 LLMIntegration 配置
        if hasattr(agent, 'llm_integration'):
            print(f"LLM 提供者: {agent.llm_integration.llm_provider}")
            print(f"LLM 模型: {agent.llm_integration.model}")
        
        print("\n✅ Agent 成功初始化 Step-3.5-Flash 配置")
        
    except Exception as e:
        print(f"⚠️  Agent 初始化警告: {e}")
        print("   这可能是由于缺少真实的 API 密钥或依赖项")


def example_configuration_options():
    """示例 5: 配置选项展示"""
    print("\n" + "=" * 60)
    print("示例 5: Step-3.5-Flash 配置选项")
    print("=" * 60)
    
    from src.services.stepflash_adapter import StepFlashAdapter
    
    print("可配置的性能参数:")
    print("-" * 40)
    
    # 默认配置
    adapter_default = StepFlashAdapter()
    print("1. 默认配置:")
    print(f"   timeout: {adapter_default.timeout}秒")
    print(f"   max_tokens: {adapter_default.max_tokens}")
    print(f"   temperature: {adapter_default.temperature}")
    print(f"   max_retries: {adapter_default.max_retries}")
    print(f"   retry_delay: {adapter_default.retry_delay}秒")
    
    # 自定义配置
    adapter_custom = StepFlashAdapter(
        timeout=60,
        max_tokens=16384,
        temperature=0.3,
        max_retries=5,
        retry_delay=2.0
    )
    
    print("\n2. 自定义配置 (长文本处理):")
    print(f"   timeout: {adapter_custom.timeout}秒")
    print(f"   max_tokens: {adapter_custom.max_tokens}")
    print(f"   temperature: {adapter_custom.temperature}")
    print(f"   max_retries: {adapter_custom.max_retries}")
    print(f"   retry_delay: {adapter_custom.retry_delay}秒")
    
    # 生产环境配置
    adapter_prod = StepFlashAdapter(
        timeout=45,
        max_tokens=8192,
        temperature=0.8,
        max_retries=3,
        retry_delay=1.5
    )
    
    print("\n3. 生产环境配置:")
    print(f"   timeout: {adapter_prod.timeout}秒")
    print(f"   max_tokens: {adapter_prod.max_tokens}")
    print(f"   temperature: {adapter_prod.temperature}")
    print(f"   max_retries: {adapter_prod.max_retries}")
    print(f"   retry_delay: {adapter_prod.retry_delay}秒")
    
    print("\n✅ 配置选项展示完成")


def example_environment_variables():
    """示例 6: 环境变量配置"""
    print("\n" + "=" * 60)
    print("示例 6: 环境变量配置")
    print("=" * 60)
    
    print("支持的环境变量:")
    print("-" * 40)
    
    env_vars = {
        "LLM_PROVIDER": "设置 LLM 提供者 (stepflash, deepseek, openai, mock)",
        "STEPSFLASH_API_KEY": "Step-3.5-Flash API 密钥",
        "STEPFLASH_DEPLOYMENT_TYPE": "部署类型 (openrouter, nim, vllm_local)",
        "STEPFLASH_BASE_URL": "自定义基础 URL",
        "STEPFLASH_MODEL": "自定义模型名称",
        "STEPFLASH_TIMEOUT": "超时时间(秒)",
        "STEPFLASH_MAX_TOKENS": "最大生成 token 数",
        "STEPFLASH_TEMPERATURE": "温度参数",
        "STEPFLASH_MAX_RETRIES": "最大重试次数",
        "STEPFLASH_RETRY_DELAY": "重试延迟时间(秒)",
    }
    
    for var, desc in env_vars.items():
        value = os.getenv(var, "未设置")
        print(f"{var}:")
        print(f"  描述: {desc}")
        print(f"  当前值: {value}")
        print()
    
    print("配置示例:")
    print("-" * 40)
    print('''# 使用 OpenRouter
export LLM_PROVIDER="stepflash"
export STEPSFLASH_API_KEY="sk-or-xxx-xxx"
export STEPFLASH_DEPLOYMENT_TYPE="openrouter"

# 使用 vLLM 本地部署
export LLM_PROVIDER="stepflash"
export STEPFLASH_DEPLOYMENT_TYPE="vllm_local"
export STEPFLASH_BASE_URL="http://localhost:8000/v1"
export STEPFLASH_TIMEOUT="60"
export STEPFLASH_MAX_RETRIES="5"''')
    
    print("\n✅ 环境变量配置说明完成")


def main():
    """主函数"""
    print("Step-3.5-Flash 使用示例")
    print("=" * 60)
    print("本示例展示如何在 RANGEN 系统中使用 Step-3.5-Flash 模型")
    print("注意: 部分示例需要真实的 API 密钥才能完全运行")
    print()
    
    try:
        # 运行所有示例
        example_direct_adapter_usage()
        example_llm_integration_usage()
        example_adapter_factory_usage()
        example_agent_usage()
        example_configuration_options()
        example_environment_variables()
        
        print("\n" + "=" * 60)
        print("✅ 所有示例执行完成!")
        print("=" * 60)
        print("\n下一步建议:")
        print("1. 设置真实 STEPSFLASH_API_KEY 环境变量")
        print("2. 运行集成测试: python tests/test_stepflash_integration.py")
        print("3. 启动可视化界面测试 Agent Creation 功能")
        print("4. 参考 API_CONFIG_README.md 获取详细配置说明")
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保已安装所有依赖项并设置正确的 Python 路径")
        return 1
    except Exception as e:
        print(f"❌ 执行错误: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())