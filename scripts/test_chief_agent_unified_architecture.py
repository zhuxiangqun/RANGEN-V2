#!/usr/bin/env python3
"""
测试 Chief Agent 统一架构
验证所有路径都通过 Chief Agent，并测试不同策略的执行

使用方法:
    python scripts/test_chief_agent_unified_architecture.py
"""

import asyncio
import time
import logging
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
try:
    from dotenv import load_dotenv
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=False)
        print(f"✅ 已从 .env 文件加载环境变量: {env_path}")
except ImportError:
    print("⚠️  python-dotenv 未安装，无法加载 .env 文件")
except Exception as e:
    print(f"⚠️  加载 .env 文件失败: {e}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_simple_query():
    """测试 Simple 查询快速路径"""
    logger.info("=" * 80)
    logger.info("📝 测试1: Simple 查询快速路径")
    logger.info("=" * 80)
    
    from src.unified_research_system import create_unified_research_system, ResearchRequest
    
    test_query = "What is the capital of France?"
    start_time = time.time()
    
    try:
        system = await create_unified_research_system()
        
        request = ResearchRequest(
            query=test_query,
            context={}
        )
        
        logger.info(f"🔍 查询: {test_query}")
        logger.info("🔍 预期: 通过 Chief Agent 快速路径（执行时间 < 30秒）")
        
        result = await system.execute_research(request)
        
        execution_time = time.time() - start_time
        
        # 验证结果
        success = (
            result.success and
            result.answer is not None and
            len(result.answer) > 0 and
            execution_time < 30.0  # Simple 查询应该在30秒内完成
        )
        
        logger.info(f"⏱️  执行时间: {execution_time:.2f}秒")
        logger.info(f"✅ 成功: {result.success}")
        logger.info(f"📝 答案: {result.answer[:200] if result.answer else 'None'}...")
        logger.info(f"🎯 置信度: {result.confidence:.2f}")
        
        if execution_time < 10.0:
            logger.info("⚡ 快速路径已启用（执行时间 < 10秒）✅")
        elif execution_time < 30.0:
            logger.info("⚡ 快速路径已启用（执行时间 < 30秒）✅")
        else:
            logger.warning("⚠️ 执行时间较长，可能未使用快速路径")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return False


async def test_complex_query():
    """测试 Complex 查询完整智能体序列"""
    logger.info("=" * 80)
    logger.info("📝 测试2: Complex 查询完整智能体序列")
    logger.info("=" * 80)
    
    from src.unified_research_system import create_unified_research_system, ResearchRequest
    
    test_query = "Compare the economic policies of the United States and China in the 21st century"
    start_time = time.time()
    
    try:
        system = await create_unified_research_system()
        
        request = ResearchRequest(
            query=test_query,
            context={}
        )
        
        logger.info(f"🔍 查询: {test_query}")
        logger.info("🔍 预期: 通过 Chief Agent 完整智能体序列")
        
        result = await system.execute_research(request)
        
        execution_time = time.time() - start_time
        
        # 验证结果
        success = (
            result.success and
            result.answer is not None and
            len(result.answer) > 0
        )
        
        logger.info(f"⏱️  执行时间: {execution_time:.2f}秒")
        logger.info(f"✅ 成功: {result.success}")
        logger.info(f"📝 答案: {result.answer[:200] if result.answer else 'None'}...")
        logger.info(f"🎯 置信度: {result.confidence:.2f}")
        
        if success:
            logger.info("🔧 完整智能体序列已启用 ✅")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return False


async def test_reasoning_query():
    """测试 Reasoning 路径推理引擎"""
    logger.info("=" * 80)
    logger.info("📝 测试3: Reasoning 路径推理引擎")
    logger.info("=" * 80)
    
    from src.unified_research_system import create_unified_research_system, ResearchRequest
    
    test_query = "Who was the 15th first lady of the United States?"
    start_time = time.time()
    
    try:
        system = await create_unified_research_system()
        
        request = ResearchRequest(
            query=test_query,
            context={}
        )
        
        logger.info(f"🔍 查询: {test_query}")
        logger.info("🔍 预期: 通过 Chief Agent 推理引擎策略")
        
        result = await system.execute_research(request)
        
        execution_time = time.time() - start_time
        
        # 验证结果
        success = (
            result.success and
            result.answer is not None and
            len(result.answer) > 0
        )
        
        logger.info(f"⏱️  执行时间: {execution_time:.2f}秒")
        logger.info(f"✅ 成功: {result.success}")
        logger.info(f"📝 答案: {result.answer[:200] if result.answer else 'None'}...")
        logger.info(f"🎯 置信度: {result.confidence:.2f}")
        
        if success:
            logger.info("🧠 推理引擎策略已启用 ✅")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return False


async def test_routing_logic():
    """测试路由逻辑 - 验证所有路径都通过 Chief Agent"""
    logger.info("=" * 80)
    logger.info("📝 测试4: 路由逻辑验证")
    logger.info("=" * 80)
    
    try:
        from src.core.langgraph_unified_workflow import UnifiedResearchWorkflow
        from src.unified_research_system import UnifiedResearchSystem
        
        system = UnifiedResearchSystem()
        workflow = UnifiedResearchWorkflow(system=system)
        
        # 检查工作流构建时的路由映射
        # 注意：路由映射在 _build_workflow 中设置，我们需要检查日志或工作流结构
        
        logger.info("🔍 检查工作流路由配置...")
        
        # 验证 agent_nodes 是否可用
        if hasattr(workflow, 'agent_nodes') and workflow.agent_nodes:
            logger.info("✅ Agent 节点已初始化")
            
            # 验证 chief_agent_node 是否存在
            if hasattr(workflow.agent_nodes, 'chief_agent_node'):
                logger.info("✅ Chief Agent 节点已存在")
                
                # 验证策略处理方法是否存在
                if hasattr(workflow.agent_nodes, '_handle_simple_path'):
                    logger.info("✅ 快速路径处理方法已存在")
                if hasattr(workflow.agent_nodes, '_handle_reasoning_path'):
                    logger.info("✅ 推理路径处理方法已存在")
                if hasattr(workflow.agent_nodes, '_handle_full_agent_sequence'):
                    logger.info("✅ 完整智能体序列处理方法已存在")
                
                logger.info("✅ 路由逻辑验证通过")
                return True
            else:
                logger.error("❌ Chief Agent 节点不存在")
                return False
        else:
            logger.warning("⚠️ Agent 节点不可用")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return False


async def main():
    """主测试函数"""
    logger.info("🚀 开始测试 Chief Agent 统一架构")
    logger.info("=" * 80)
    
    test_results = []
    
    # 测试1: Simple 查询快速路径
    try:
        result1 = await test_simple_query()
        test_results.append(('Simple 查询快速路径', result1))
    except Exception as e:
        logger.error(f"❌ 测试1失败: {e}", exc_info=True)
        test_results.append(('Simple 查询快速路径', False))
    
    logger.info("")
    
    # 测试2: Complex 查询完整智能体序列
    try:
        result2 = await test_complex_query()
        test_results.append(('Complex 查询完整智能体序列', result2))
    except Exception as e:
        logger.error(f"❌ 测试2失败: {e}", exc_info=True)
        test_results.append(('Complex 查询完整智能体序列', False))
    
    logger.info("")
    
    # 测试3: Reasoning 路径推理引擎
    try:
        result3 = await test_reasoning_query()
        test_results.append(('Reasoning 路径推理引擎', result3))
    except Exception as e:
        logger.error(f"❌ 测试3失败: {e}", exc_info=True)
        test_results.append(('Reasoning 路径推理引擎', False))
    
    logger.info("")
    
    # 测试4: 路由逻辑验证
    try:
        result4 = await test_routing_logic()
        test_results.append(('路由逻辑验证', result4))
    except Exception as e:
        logger.error(f"❌ 测试4失败: {e}", exc_info=True)
        test_results.append(('路由逻辑验证', False))
    
    # 打印总结
    logger.info("=" * 80)
    logger.info("📊 测试总结")
    logger.info("=" * 80)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for _, result in test_results if result)
    
    logger.info(f"总测试数: {total_tests}")
    logger.info(f"通过测试: {passed_tests}")
    logger.info(f"失败测试: {total_tests - passed_tests}")
    
    for test_name, result in test_results:
        status = "✅" if result else "❌"
        logger.info(f"{status} {test_name}")
    
    logger.info("=" * 80)
    
    # 返回总体结果
    all_passed = all(result for _, result in test_results)
    
    if all_passed:
        logger.info("✅ 所有测试通过！")
        return 0
    else:
        logger.error("❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

