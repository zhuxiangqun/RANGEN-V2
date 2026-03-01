"""
Gateway Integration Test

测试 Gateway 的完整功能
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.gateway import Gateway, GatewayConfig
from src.gateway.channels import WebChatAdapter
from src.gateway.memory import SessionMemory
from src.gateway.agents import AgentRuntime, AgentConfig
from src.gateway.agents.prompt_builder import create_personal_assistant_prompt


async def test_gateway_basic():
    """测试 Gateway 基本功能"""
    print("=" * 60)
    print("Test 1: Gateway 基本初始化")
    print("=" * 60)
    
    config = GatewayConfig(
        heartbeat_interval=10,
        rate_limit_enabled=True,
        rate_limit_max_per_minute=5
    )
    
    gateway = Gateway(config)
    
    print(f"✓ Gateway created")
    print(f"  - Status: {gateway.status}")
    print(f"  - Config: heartbeat={config.heartbeat_interval}s, rate_limit={config.rate_limit_max_per_minute}/min")
    
    # 启动
    await gateway.start()
    print(f"✓ Gateway started")
    print(f"  - Status: {gateway.status}")
    
    # 检查状态
    status = gateway.get_status()
    print(f"✓ Status check:")
    print(f"  - {status}")
    
    # 停止
    await gateway.stop()
    print(f"✓ Gateway stopped")
    print(f"  - Status: {gateway.status}")
    
    print()


async def test_memory():
    """测试记忆功能"""
    print("=" * 60)
    print("Test 2: Session Memory")
    print("=" * 60)
    
    memory = SessionMemory(context_window=5)
    
    # 添加记忆
    await memory.add_interaction(
        session_id="test_session",
        user_input="Hello",
        agent_response="Hi there!"
    )
    
    await memory.add_interaction(
        session_id="test_session",
        user_input="How are you?",
        agent_response="I'm doing well, thanks!"
    )
    
    # 获取记忆
    mem = await memory.get_memory("test_session")
    print(f"✓ Added 2 interactions, retrieved {len(mem)} messages")
    
    for m in mem:
        print(f"  - {m['role']}: {m['content'][:30]}...")
    
    # 获取摘要
    summary = await memory.get_summary("test_session")
    print(f"✓ Summary: {summary}")
    
    print()


async def test_prompt_builder():
    """测试提示构建器"""
    print("=" * 60)
    print("Test 3: Prompt Builder (三层提示结构)")
    print("=" * 60)
    
    builder = create_personal_assistant_prompt()
    
    # 构建完整提示
    prompt = builder.build_full_prompt(
        user_input="What's the weather today?",
        memory=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"}
        ]
    )
    
    print(f"✓ Generated prompt ({len(prompt)} chars)")
    print(f"  - Contains SOUL: {'SOUL' in prompt}")
    print(f"  - Contains AGENTS: {'AGENTS' in prompt}")
    print(f"  - Contains TOOLS: {'TOOLS' in prompt}")
    print(f"  - Contains Context: {'Context' in prompt}")
    
    # 构建推理提示
    reasoning_prompt = builder.build_reasoning_prompt(
        user_input="Calculate 2+2",
        memory=[],
        tools=["calculator"],
        history=[],
        enable_thinking=True
    )
    
    print(f"✓ Generated reasoning prompt ({len(reasoning_prompt)} chars)")
    
    print()


async def test_agent_runtime():
    """测试 Agent Runtime"""
    print("=" * 60)
    print("Test 4: Agent Runtime")
    print("=" * 60)
    
    config = AgentConfig(
        max_iterations=3,
        enable_thinking=True
    )
    
    runtime = AgentRuntime(config=config)
    
    # 启动
    await runtime.start()
    print(f"✓ AgentRuntime started")
    
    # 检查状态
    print(f"  - Status: {runtime.status}")
    print(f"  - Tools available: {len(runtime.tool_registry)}")
    
    # 停止
    await runtime.stop()
    print(f"✓ AgentRuntime stopped")
    
    print()


async def test_channel():
    """测试渠道适配器"""
    print("=" * 60)
    print("Test 5: WebChat Channel")
    print("=" * 60)
    
    adapter = WebChatAdapter({"port": 18765})
    
    # 连接
    await adapter.connect()
    print(f"✓ WebChat adapter connected")
    print(f"  - Port: 18765")
    
    # 获取连接信息
    info = adapter.get_connection_info()
    print(f"  - Connections: {info['total_connections']}")
    
    # 断开
    await adapter.disconnect()
    print(f"✓ WebChat adapter disconnected")
    
    print()


async def test_kill_switch():
    """测试 Kill Switch"""
    print("=" * 60)
    print("Test 6: Kill Switch")
    print("=" * 60)
    
    gateway = Gateway()
    await gateway.start()
    
    # 激活 Kill Switch
    await gateway.activate_kill_switch("Test activation")
    print(f"✓ Kill Switch activated")
    print(f"  - kill_switch_active: {gateway.kill_switch_active}")
    
    # 停用 Kill Switch
    await gateway.deactivate_kill_switch()
    print(f"✓ Kill Switch deactivated")
    print(f"  - kill_switch_active: {gateway.kill_switch_active}")
    
    await gateway.stop()
    
    print()


async def test_rate_limiter():
    """测试速率限制"""
    print("=" * 60)
    print("Test 7: Rate Limiter")
    print("=" * 60)
    
    from src.gateway.channels import User
    
    config = GatewayConfig(
        rate_limit_enabled=True,
        rate_limit_max_per_minute=3
    )
    
    gateway = Gateway(config)
    await gateway.start()
    
    user = User(id="test_user")
    
    # 测试速率限制
    for i in range(5):
        allowed = await gateway._check_rate_limit(user)
        print(f"  Request {i+1}: {'✓ Allowed' if allowed else '✗ Blocked'}")
    
    await gateway.stop()
    
    print()


async def test_full_integration():
    """完整集成测试"""
    print("=" * 60)
    print("Test 8: Full Integration")
    print("=" * 60)
    
    # 创建 Gateway
    config = GatewayConfig(
        heartbeat_interval=5,
        rate_limit_enabled=True,
        rate_limit_max_per_minute=10,
        memory_enabled=True
    )
    
    gateway = Gateway(config)
    
    # 注册 WebChat 渠道
    webchat = WebChatAdapter({"port": 18766})
    await gateway.register_channel("webchat", webchat)
    await webchat.connect()
    print(f"✓ Registered WebChat channel")
    
    # 启动
    await gateway.start()
    print(f"✓ Gateway started")
    
    # 获取状态
    status = gateway.get_status()
    print(f"✓ Status:")
    print(f"  - Channels: {status['channels']}")
    print(f"  - Sessions: {status['active_sessions']}")
    print(f"  - Status: {status['status']}")
    
    # 停止
    await webchat.disconnect()
    await gateway.stop()
    print(f"✓ Gateway stopped")
    
    print()


async def main():
    """主测试函数"""
    print()
    print("🚀 RANGEN Gateway Integration Tests")
    print("=" * 60)
    print()
    
    try:
        # 基本测试
        await test_gateway_basic()
        await test_memory()
        await test_prompt_builder()
        await test_agent_runtime()
        await test_channel()
        await test_kill_switch()
        await test_rate_limiter()
        
        # 集成测试
        await test_full_integration()
        
        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Test failed: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
