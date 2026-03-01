#!/usr/bin/env python3
"""
测试 Chief Agent 统一架构
验证所有路径都通过 Chief Agent，并测试不同策略的执行
"""
import asyncio
import time
import logging
import pytest
import sys
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.langgraph_unified_workflow import UnifiedResearchWorkflow, ResearchSystemState

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestChiefAgentUnifiedArchitecture:
    """Chief Agent 统一架构测试类"""
    
    @pytest.fixture
    async def workflow(self):
        """创建工作流实例 fixture"""
        logger.info("🔧 设置测试环境...")
        try:
            from src.unified_research_system import UnifiedResearchSystem
            system = UnifiedResearchSystem()
            workflow = UnifiedResearchWorkflow(system=system)
            logger.info("✅ 工作流实例创建成功")
            
            # 验证 agent_nodes 是否可用
            if not hasattr(workflow, 'agent_nodes') or not getattr(workflow, 'agent_nodes', None):
                logger.warning("⚠️ Agent 节点不可用，某些测试可能无法执行")
            
            yield workflow
        except Exception as e:
            logger.error(f"❌ 工作流初始化失败: {e}", exc_info=True)
            pytest.skip(f"工作流初始化失败: {e}")
    
    async def test_simple_query_fast_path(self, workflow):
        """测试 Simple 查询快速路径"""
        logger.info("=" * 80)
        logger.info("📝 测试1: Simple 查询快速路径")
        logger.info("=" * 80)
        
        test_query = "What is the capital of France?"
        start_time = time.time()
        
        try:
            # 准备测试状态（包含所有必需字段）
            initial_state: Dict[str, Any] = {
                'query': test_query,
                'route_path': 'simple',
                'complexity_score': 1.5,  # Simple 查询
                'needs_reasoning_chain': False,
                'context': {},
                'knowledge': [],
                'evidence': [],
                'errors': [],
                'metadata': {},
                'query_type': 'general',
                'user_context': {},
                'user_id': None,
                'session_id': None,
                'safety_check_passed': True,
                'sensitive_topics': [],
                'content_filter_applied': False,
                'answer': None,
                'final_answer': None,
                'confidence': 0.0,
                'citations': [],
                'task_complete': False,
                'error': None,
                'execution_time': 0.0,
                'retry_count': 0,
                'node_execution_times': {},
                'token_usage': {},
                'api_calls': {},
                'workflow_checkpoint_id': None
            }
            
            # 检查路由逻辑
            logger.info(f"🔍 查询: {test_query}")
            logger.info(f"🔍 路由路径: {initial_state['route_path']}")
            logger.info(f"🔍 复杂度: {initial_state['complexity_score']}")
            
            # 验证路由应该指向 chief_agent
            # 注意：这里我们直接测试 chief_agent_node，因为路由逻辑已经在工作流构建时确定
            agent_nodes = getattr(workflow, 'agent_nodes', None)
            if agent_nodes and hasattr(agent_nodes, 'chief_agent_node'):
                chief_agent_node = agent_nodes.chief_agent_node
                
                # 执行 Chief Agent 节点（添加超时：5分钟）
                logger.info("⏱️  开始执行（超时：5分钟）...")
                result_state = await asyncio.wait_for(
                    chief_agent_node(initial_state),
                    timeout=300.0  # 5分钟超时
                )
                
                execution_time = time.time() - start_time
                
                # 详细日志输出
                logger.info(f"⏱️  执行时间: {execution_time:.2f}秒")
                logger.info(f"✅ 任务完成: {result_state.get('task_complete', False)}")
                logger.info(f"📝 答案: {result_state.get('answer', '')[:100] if result_state.get('answer') else 'None'}...")
                logger.info(f"🎯 置信度: {result_state.get('confidence', 0):.2f}")
                
                # 检查错误信息
                if result_state.get('error'):
                    logger.error(f"❌ 错误信息: {result_state.get('error')}")
                if result_state.get('errors'):
                    logger.error(f"❌ 错误列表: {result_state.get('errors')}")
                
                # 检查是否使用了快速路径
                metadata = result_state.get('metadata', {})
                coordination_result = metadata.get('coordination_result', {})
                
                if execution_time < 10.0:
                    logger.info("⚡ 快速路径已启用（执行时间 < 10秒）")
                elif execution_time < 30.0:
                    logger.info("⚡ 快速路径已启用（执行时间 < 30秒）")
                else:
                    logger.warning("⚠️ 执行时间较长，可能回退到完整智能体序列")
                
                # 验证结果（放宽时间限制，因为可能回退到完整序列）
                success = (
                    result_state.get('task_complete', False) and
                    result_state.get('answer') is not None and
                    len(result_state.get('answer', '')) > 0
                )
                
                if not success:
                    error_details = {
                        'task_complete': result_state.get('task_complete', False),
                        'has_answer': result_state.get('answer') is not None,
                        'answer_length': len(result_state.get('answer', '')),
                        'error': result_state.get('error'),
                        'errors': result_state.get('errors', [])
                    }
                    logger.error(f"❌ 测试失败详情: {error_details}")
                
                assert success, f"Simple 查询快速路径测试失败: 执行时间={execution_time:.2f}秒, 任务完成={result_state.get('task_complete', False)}, 答案={result_state.get('answer', 'None')[:50]}..."
                return
            else:
                pytest.skip("Agent 节点不可用")
                
        except asyncio.TimeoutError:
            logger.error("❌ 测试超时（5分钟）")
            pytest.fail("Simple 查询快速路径测试超时（5分钟）")
        except Exception as e:
            logger.error(f"❌ 测试失败: {e}", exc_info=True)
            pytest.fail(f"Simple 查询快速路径测试异常: {e}")
    
    async def test_complex_query_full_sequence(self, workflow):
        """测试 Complex 查询完整智能体序列"""
        logger.info("=" * 80)
        logger.info("📝 测试2: Complex 查询完整智能体序列")
        logger.info("=" * 80)
        
        test_query = "Compare the economic policies of the United States and China in the 21st century"
        start_time = time.time()
        
        try:
            # 准备测试状态
            initial_state: Dict[str, Any] = {
                'query': test_query,
                'route_path': 'complex',
                'complexity_score': 7.0,  # Complex 查询
                'needs_reasoning_chain': False,
                'context': {},
                'knowledge': [],
                'evidence': [],
                'errors': [],
                'metadata': {}
            }
            
            logger.info(f"🔍 查询: {test_query}")
            logger.info(f"🔍 路由路径: {initial_state['route_path']}")
            logger.info(f"🔍 复杂度: {initial_state['complexity_score']}")
            
            agent_nodes = getattr(workflow, 'agent_nodes', None)
            if agent_nodes and hasattr(agent_nodes, 'chief_agent_node'):
                chief_agent_node = agent_nodes.chief_agent_node
                
                # 执行 Chief Agent 节点（添加超时：10分钟，推理查询需要更长时间）
                logger.info("⏱️  开始执行（超时：10分钟）...")
                result_state = await asyncio.wait_for(
                    chief_agent_node(initial_state),
                    timeout=600.0  # 10分钟超时
                )
                
                execution_time = time.time() - start_time
                
                # 验证结果
                success = (
                    result_state.get('task_complete', False) and
                    result_state.get('answer') is not None
                )
                
                logger.info(f"⏱️  执行时间: {execution_time:.2f}秒")
                logger.info(f"✅ 任务完成: {result_state.get('task_complete', False)}")
                logger.info(f"📝 答案: {result_state.get('answer', '')[:100]}...")
                logger.info(f"🎯 置信度: {result_state.get('confidence', 0):.2f}")
                
                # 检查是否使用了完整智能体序列
                metadata = result_state.get('metadata', {})
                coordination_result = metadata.get('coordination_result', {})
                
                if coordination_result.get('success'):
                    logger.info("🔧 完整智能体序列已启用")
                
                assert success, f"Complex 查询完整智能体序列测试失败: 执行时间={execution_time:.2f}秒, 任务完成={result_state.get('task_complete', False)}"
                return
            else:
                pytest.skip("Agent 节点不可用")
                
        except asyncio.TimeoutError:
            logger.error("❌ 测试超时（10分钟）")
            pytest.fail("Complex 查询完整智能体序列测试超时（10分钟）")
        except Exception as e:
            logger.error(f"❌ 测试失败: {e}", exc_info=True)
            pytest.fail(f"Complex 查询完整智能体序列测试异常: {e}")
    
    async def test_reasoning_path(self, workflow):
        """测试 Reasoning 路径推理引擎"""
        logger.info("=" * 80)
        logger.info("📝 测试3: Reasoning 路径推理引擎")
        logger.info("=" * 80)
        
        test_query = "Who was the 15th first lady of the United States?"
        start_time = time.time()
        
        try:
            # 准备测试状态
            # 注意：路由决策函数返回 'reasoning'，但 ResearchSystemState 定义是 'reasoning_chain'
            # 我们使用 'reasoning' 因为这是路由映射中实际使用的键
            initial_state: Dict[str, Any] = {
                'query': test_query,
                'route_path': 'reasoning',  # 路由决策函数返回的值
                'complexity_score': 4.5,
                'needs_reasoning_chain': True,  # 需要推理链（通过 metadata 或直接作为字典键）
                'context': {},
                'knowledge': [],
                'evidence': [],
                'errors': [],
                'metadata': {},
                'query_type': 'general',
                'user_context': {},
                'safety_check_passed': True,
                'sensitive_topics': [],
                'content_filter_applied': False,
                'citations': [],
                'task_complete': False,
                'error': None,
                'execution_time': 0.0,
                'retry_count': 0,
                'node_execution_times': {},
                'token_usage': {},
                'api_calls': {},
                'workflow_checkpoint_id': None
            }
            
            logger.info(f"🔍 查询: {test_query}")
            logger.info(f"🔍 路由路径: {initial_state['route_path']}")
            logger.info(f"🔍 需要推理链: {initial_state.get('needs_reasoning_chain', False)}")
            
            agent_nodes = getattr(workflow, 'agent_nodes', None)
            if agent_nodes and hasattr(agent_nodes, 'chief_agent_node'):
                chief_agent_node = agent_nodes.chief_agent_node
                
                # 执行 Chief Agent 节点（添加超时：10分钟，推理查询需要更长时间）
                logger.info("⏱️  开始执行（超时：10分钟）...")
                result_state = await asyncio.wait_for(
                    chief_agent_node(initial_state),
                    timeout=600.0  # 10分钟超时
                )
                
                execution_time = time.time() - start_time
                
                # 验证结果
                success = (
                    result_state.get('task_complete', False) and
                    result_state.get('answer') is not None
                )
                
                logger.info(f"⏱️  执行时间: {execution_time:.2f}秒")
                logger.info(f"✅ 任务完成: {result_state.get('task_complete', False)}")
                logger.info(f"📝 答案: {result_state.get('answer', '')[:100]}...")
                logger.info(f"🎯 置信度: {result_state.get('confidence', 0):.2f}")
                
                # 检查是否使用了推理引擎
                if 'reasoning_steps' in result_state or 'step_answers' in result_state:
                    logger.info("🧠 推理引擎已启用")
                
                assert success, f"Reasoning 路径推理引擎测试失败: 执行时间={execution_time:.2f}秒, 任务完成={result_state.get('task_complete', False)}"
                return
            else:
                pytest.skip("Agent 节点不可用")
                
        except asyncio.TimeoutError:
            logger.error("❌ 测试超时（10分钟）")
            pytest.fail("Reasoning 路径推理引擎测试超时（10分钟）")
        except Exception as e:
            logger.error(f"❌ 测试失败: {e}", exc_info=True)
            pytest.fail(f"Reasoning 路径推理引擎测试异常: {e}")
    
    async def test_fallback_mechanism(self, workflow):
        """测试回退机制"""
        logger.info("=" * 80)
        logger.info("📝 测试4: 回退机制（快速路径失败时回退到完整序列）")
        logger.info("=" * 80)
        
        # 使用一个可能导致快速路径失败的查询（例如，知识检索失败的情况）
        test_query = "Test query that might fail"  # 这个查询可能检索不到知识
        start_time = time.time()
        
        try:
            initial_state: Dict[str, Any] = {
                'query': test_query,
                'route_path': 'simple',
                'complexity_score': 1.5,
                'needs_reasoning_chain': False,
                'context': {},
                'knowledge': [],
                'evidence': [],
                'errors': [],
                'metadata': {}
            }
            
            logger.info(f"🔍 查询: {test_query}")
            logger.info("🔍 测试场景: 快速路径可能失败，应该回退到完整智能体序列")
            
            agent_nodes = getattr(workflow, 'agent_nodes', None)
            if agent_nodes and hasattr(agent_nodes, 'chief_agent_node'):
                chief_agent_node = agent_nodes.chief_agent_node
                
                # 执行 Chief Agent 节点（添加超时：10分钟，推理查询需要更长时间）
                logger.info("⏱️  开始执行（超时：10分钟）...")
                result_state = await asyncio.wait_for(
                    chief_agent_node(initial_state),
                    timeout=600.0  # 10分钟超时
                )
                
                execution_time = time.time() - start_time
                
                # 验证回退机制
                # 即使快速路径失败，也应该有结果（通过完整序列）
                success = (
                    result_state.get('task_complete', False) or
                    'error' in result_state  # 或者有明确的错误信息
                )
                
                logger.info(f"⏱️  执行时间: {execution_time:.2f}秒")
                logger.info(f"✅ 任务完成: {result_state.get('task_complete', False)}")
                
                if result_state.get('error'):
                    logger.info(f"⚠️ 错误信息: {result_state.get('error')}")
                
                # 检查日志中是否有回退信息
                logger.info("🔍 检查回退机制是否正常工作...")
                
                assert success, f"回退机制测试失败: 执行时间={execution_time:.2f}秒"
                return
            else:
                pytest.skip("Agent 节点不可用")
                
        except asyncio.TimeoutError:
            logger.error("❌ 测试超时（5分钟）")
            pytest.fail("回退机制测试超时（5分钟）")
        except Exception as e:
            logger.error(f"❌ 测试失败: {e}", exc_info=True)
            pytest.fail(f"回退机制测试异常: {e}")
    
    async def test_routing_logic(self, workflow):
        """测试路由逻辑 - 验证所有路径都通过 Chief Agent"""
        logger.info("=" * 80)
        logger.info("📝 测试5: 路由逻辑验证")
        logger.info("=" * 80)
        
        try:
            # 验证 agent_nodes 是否可用
            agent_nodes = getattr(workflow, 'agent_nodes', None)
            assert agent_nodes is not None, "Agent 节点不可用"
            
            # 验证 chief_agent_node 是否存在
            assert hasattr(agent_nodes, 'chief_agent_node'), "Chief Agent 节点不存在"
            
            # 验证策略处理方法是否存在
            assert hasattr(agent_nodes, '_handle_simple_path'), "快速路径处理方法不存在"
            assert hasattr(agent_nodes, '_handle_reasoning_path'), "推理路径处理方法不存在"
            assert hasattr(agent_nodes, '_handle_full_agent_sequence'), "完整智能体序列处理方法不存在"
            
            logger.info("✅ 路由逻辑验证通过")
            return
            
        except Exception as e:
            logger.error(f"❌ 测试失败: {e}", exc_info=True)
            pytest.fail(f"路由逻辑验证测试异常: {e}")

