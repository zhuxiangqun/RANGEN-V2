#!/usr/bin/env python3
"""
测试编排过程可视化功能

此脚本用于测试：
1. Agent 执行追踪
2. 工具调用追踪
3. 提示词工程追踪
4. 上下文工程追踪
5. 浏览器可视化显示
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ.setdefault('ENABLE_BROWSER_VISUALIZATION', 'true')
os.environ.setdefault('ENABLE_UNIFIED_WORKFLOW', 'true')
os.environ.setdefault('VISUALIZATION_PORT', '8080')

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

import logging
from src.unified_research_system import UnifiedResearchSystem, ResearchRequest
from src.visualization.orchestration_tracker import get_orchestration_tracker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_basic_orchestration():
    """测试基础编排追踪"""
    logger.info("=" * 80)
    logger.info("测试1: 基础编排追踪")
    logger.info("=" * 80)
    
    # 初始化系统
    system = UnifiedResearchSystem()
    await system.initialize()
    
    # 执行一个简单查询
    request = ResearchRequest(
        query="Who was the 15th first lady of the United States?",
        context={"test": "orchestration_visualization"}
    )
    
    logger.info(f"执行查询: {request.query}")
    result = await system.execute_research(request)
    
    logger.info(f"查询完成: success={result.success}")
    logger.info(f"答案长度: {len(result.answer) if result.answer else 0}")
    
    # 检查追踪器
    tracker = get_orchestration_tracker()
    if tracker:
        events = tracker.get_all_events()
        logger.info(f"追踪到 {len(events)} 个事件")
        
        # 按类型统计
        event_types = {}
        for event in events:
            event_type = event.event_type.value
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        logger.info("事件类型统计:")
        for event_type, count in sorted(event_types.items()):
            logger.info(f"  {event_type}: {count}")
    else:
        logger.warning("⚠️ 追踪器未初始化")
    
    return result


async def test_agent_tracking():
    """测试 Agent 追踪"""
    logger.info("=" * 80)
    logger.info("测试2: Agent 执行追踪")
    logger.info("=" * 80)
    
    system = UnifiedResearchSystem()
    await system.initialize()
    
    # 获取追踪器
    tracker = get_orchestration_tracker()
    if not tracker:
        logger.warning("⚠️ 追踪器未初始化，跳过测试")
        return
    
    # 开始新的执行
    execution_id = "test_agent_tracking"
    tracker.start_execution(execution_id)
    
    # 执行查询（应该触发 Agent 追踪）
    request = ResearchRequest(
        query="What is the capital of France?",
        context={"test": "agent_tracking"}
    )
    
    logger.info(f"执行查询: {request.query}")
    result = await system.execute_research(request)
    
    # 获取 Agent 相关事件
    agent_events = [
        e for e in tracker.get_all_events()
        if e.component_type == "agent"
    ]
    
    logger.info(f"追踪到 {len(agent_events)} 个 Agent 事件")
    for event in agent_events[:10]:  # 只显示前10个
        logger.info(f"  - {event.event_type.value}: {event.component_name} at {event.timestamp}")
    
    tracker.end_execution(execution_id)
    
    return result


async def test_tool_tracking():
    """测试工具调用追踪"""
    logger.info("=" * 80)
    logger.info("测试3: 工具调用追踪")
    logger.info("=" * 80)
    
    system = UnifiedResearchSystem()
    await system.initialize()
    
    tracker = get_orchestration_tracker()
    if not tracker:
        logger.warning("⚠️ 追踪器未初始化，跳过测试")
        return
    
    execution_id = "test_tool_tracking"
    tracker.start_execution(execution_id)
    
    request = ResearchRequest(
        query="Who invented the telephone?",
        context={"test": "tool_tracking"}
    )
    
    logger.info(f"执行查询: {request.query}")
    result = await system.execute_research(request)
    
    # 获取工具相关事件
    tool_events = [
        e for e in tracker.get_all_events()
        if e.component_type == "tool"
    ]
    
    logger.info(f"追踪到 {len(tool_events)} 个工具事件")
    for event in tool_events:
        logger.info(f"  - {event.event_type.value}: {event.component_name} at {event.timestamp}")
    
    tracker.end_execution(execution_id)
    
    return result


async def test_prompt_tracking():
    """测试提示词工程追踪"""
    logger.info("=" * 80)
    logger.info("测试4: 提示词工程追踪")
    logger.info("=" * 80)
    
    from src.utils.prompt_orchestrator import PromptOrchestrator
    from src.visualization.orchestration_tracker import get_orchestration_tracker
    
    tracker = get_orchestration_tracker()
    if not tracker:
        logger.warning("⚠️ 追踪器未初始化，跳过测试")
        return
    
    execution_id = "test_prompt_tracking"
    tracker.start_execution(execution_id)
    
    # 创建编排器并传递追踪器
    orchestrator = PromptOrchestrator()
    orchestrator._orchestration_tracker = tracker
    
    # 测试提示词编排
    query = "What is machine learning?"
    context = {
        "query_type": "general",
        "evidence": ["Machine learning is a subset of AI."]
    }
    
    logger.info(f"编排提示词: query={query[:50]}...")
    prompt = await orchestrator.orchestrate(
        query=query,
        context=context,
        orchestration_strategy="default"
    )
    
    logger.info(f"生成的提示词长度: {len(prompt) if prompt else 0}")
    
    # 获取提示词相关事件
    prompt_events = [
        e for e in tracker.get_all_events()
        if e.component_type == "prompt_engineering"
    ]
    
    logger.info(f"追踪到 {len(prompt_events)} 个提示词工程事件")
    for event in prompt_events:
        logger.info(f"  - {event.event_type.value}: {event.component_name} at {event.timestamp}")
    
    tracker.end_execution(execution_id)
    
    return prompt


async def test_context_tracking():
    """测试上下文工程追踪"""
    logger.info("=" * 80)
    logger.info("测试5: 上下文工程追踪")
    logger.info("=" * 80)
    
    from src.core.reasoning.context_manager import ContextManager
    from src.visualization.orchestration_tracker import get_orchestration_tracker
    
    tracker = get_orchestration_tracker()
    if not tracker:
        logger.warning("⚠️ 追踪器未初始化，跳过测试")
        return
    
    execution_id = "test_context_tracking"
    tracker.start_execution(execution_id)
    
    # 创建上下文管理器并传递追踪器
    context_manager = ContextManager()
    context_manager._orchestration_tracker = tracker
    
    # 测试上下文增强
    session_id = "test_session_123"
    logger.info(f"获取增强上下文: session_id={session_id}")
    enhanced_context = context_manager.get_enhanced_context(
        session_id=session_id,
        query="test query"
    )
    
    logger.info(f"增强上下文键: {list(enhanced_context.keys()) if isinstance(enhanced_context, dict) else 'N/A'}")
    
    # 测试添加上下文片段
    logger.info("添加上下文片段")
    fragment_id = context_manager.add_context_fragment(
        session_id=session_id,
        fragment={"type": "user_query", "content": "test query"}
    )
    
    logger.info(f"片段ID: {fragment_id}")
    
    # 获取上下文相关事件
    context_events = [
        e for e in tracker.get_all_events()
        if e.component_type == "context_engineering"
    ]
    
    logger.info(f"追踪到 {len(context_events)} 个上下文工程事件")
    for event in context_events:
        logger.info(f"  - {event.event_type.value}: {event.component_name} at {event.timestamp}")
    
    tracker.end_execution(execution_id)
    
    return enhanced_context


async def test_full_workflow():
    """测试完整工作流的编排追踪"""
    logger.info("=" * 80)
    logger.info("测试6: 完整工作流编排追踪")
    logger.info("=" * 80)
    
    system = UnifiedResearchSystem()
    await system.initialize()
    
    tracker = get_orchestration_tracker()
    if not tracker:
        logger.warning("⚠️ 追踪器未初始化，跳过测试")
        return
    
    execution_id = "test_full_workflow"
    tracker.start_execution(execution_id)
    
    # 执行一个复杂查询（应该触发多个组件）
    request = ResearchRequest(
        query="Who was the 15th first lady of the United States?",
        context={"test": "full_workflow"}
    )
    
    logger.info(f"执行查询: {request.query}")
    result = await system.execute_research(request)
    
    # 获取所有事件并按类型分组
    all_events = tracker.get_all_events()
    logger.info(f"总共追踪到 {len(all_events)} 个事件")
    
    # 按组件类型统计
    by_component = {}
    for event in all_events:
        comp_type = event.component_type
        if comp_type not in by_component:
            by_component[comp_type] = []
        by_component[comp_type].append(event)
    
    logger.info("按组件类型统计:")
    for comp_type, events in sorted(by_component.items()):
        logger.info(f"  {comp_type}: {len(events)} 个事件")
        # 显示事件类型
        event_types = {}
        for event in events:
            et = event.event_type.value
            event_types[et] = event_types.get(et, 0) + 1
        for et, count in sorted(event_types.items()):
            logger.info(f"    - {et}: {count}")
    
    # 检查事件层级关系
    parent_events = [e for e in all_events if e.parent_event_id is None]
    child_events = [e for e in all_events if e.parent_event_id is not None]
    
    logger.info(f"父事件: {len(parent_events)} 个")
    logger.info(f"子事件: {len(child_events)} 个")
    
    tracker.end_execution(execution_id)
    
    return result


async def main():
    """主测试函数"""
    logger.info("🚀 开始测试编排过程可视化功能")
    logger.info("=" * 80)
    
    try:
        # 测试1: 基础编排追踪
        await test_basic_orchestration()
        
        # 等待一下，避免事件混淆
        await asyncio.sleep(1)
        
        # 测试2: Agent 追踪
        await test_agent_tracking()
        
        await asyncio.sleep(1)
        
        # 测试3: 工具追踪
        await test_tool_tracking()
        
        await asyncio.sleep(1)
        
        # 测试4: 提示词追踪
        await test_prompt_tracking()
        
        await asyncio.sleep(1)
        
        # 测试5: 上下文追踪
        await test_context_tracking()
        
        await asyncio.sleep(1)
        
        # 测试6: 完整工作流
        await test_full_workflow()
        
        logger.info("=" * 80)
        logger.info("✅ 所有测试完成！")
        logger.info("=" * 80)
        logger.info("💡 提示: 打开浏览器访问 http://localhost:8080 查看可视化界面")
        logger.info("💡 提示: 在可视化界面中可以看到所有编排过程的实时追踪")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())

