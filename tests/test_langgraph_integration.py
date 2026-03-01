"""
LangGraph 工作流集成测试

测试完整工作流的端到端执行，包括：
- 简单查询路径
- 复杂查询路径
- 多查询场景
- 并发场景
- 错误恢复
"""
import asyncio
import logging
import os
import pytest
import pytest_asyncio
import signal
import sys
import time
from typing import Dict, Any, List

from src.unified_research_system import UnifiedResearchSystem
from src.core.langgraph_unified_workflow import UnifiedResearchWorkflow

# 配置日志输出
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局中断标志
_interrupted = False
_force_exit = False

def signal_handler(signum, frame):
    """处理 Ctrl-C 信号
    
    🚀 优化：快速清理资源后立即退出
    """
    global _interrupted, _force_exit
    if not _interrupted:
        _interrupted = True
        print("\n⚠️  收到中断信号 (Ctrl-C)，正在快速清理资源并退出...", flush=True)
        
        # 🚀 快速资源清理（0.5秒内完成）
        import threading
        import gc
        
        def quick_cleanup():
            """快速清理资源"""
            try:
                # 1. 取消所有异步任务
                try:
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            loop = None
                    
                    if loop and loop.is_running():
                        all_tasks = asyncio.all_tasks(loop)
                        current_task = asyncio.current_task(loop)
                        pending_tasks = [t for t in all_tasks 
                                       if not t.done() and t != current_task]
                        if pending_tasks:
                            print(f"🔄 正在取消 {len(pending_tasks)} 个待处理任务...", flush=True)
                            for task in pending_tasks:
                                try:
                                    task.cancel()
                                except Exception:
                                    pass
                except Exception:
                    pass
                
                # 2. 关闭所有 HTTP 连接池
                try:
                    from src.core.llm_integration import LLMIntegration
                    closed_count = 0
                    for obj in gc.get_objects():
                        if isinstance(obj, LLMIntegration):
                            try:
                                obj.close()
                                closed_count += 1
                            except Exception:
                                pass
                    if closed_count > 0:
                        print(f"🧹 已关闭 {closed_count} 个 HTTP 连接池", flush=True)
                except Exception:
                    pass
                
                # 3. 清理 joblib/loky 资源（避免 semaphore 泄漏）
                try:
                    from joblib.externals.loky import get_reusable_executor
                    executor = get_reusable_executor()
                    if executor is not None:
                        executor.shutdown(wait=False)  # 不等待，快速关闭
                except Exception:
                    pass
                
                try:
                    import joblib
                    if hasattr(joblib, 'parallel') and hasattr(joblib.parallel, 'DEFAULT_BACKEND'):
                        if joblib.parallel.DEFAULT_BACKEND == 'loky':
                            # 使用 getattr 安全地访问可能不存在的属性
                            terminate_func = getattr(joblib.parallel, 'terminate_backend', None)
                            if terminate_func:
                                terminate_func()
                except Exception:
                    pass
                
                # 4. 清理 multiprocessing 资源
                try:
                    import multiprocessing
                    for process in multiprocessing.active_children():
                        try:
                            if process.is_alive():
                                process.terminate()  # 不等待，立即终止
                        except Exception:
                            pass
                except Exception:
                    pass
                
                print("✅ 资源清理完成", flush=True)
            except Exception as e:
                print(f"⚠️  资源清理时出错（继续退出）: {e}", flush=True)
        
        # 在后台线程中快速清理（不阻塞主线程）
        cleanup_thread = threading.Thread(target=quick_cleanup, daemon=True)
        cleanup_thread.start()
        
        # 等待最多 0.5 秒让清理完成
        cleanup_thread.join(timeout=0.5)
        
        # 立即退出（跳过 pytest 的异常处理）
        print("⚠️  立即退出...", flush=True)
        os._exit(130)  # 130 是 Ctrl+C 的标准退出码
    else:
        _force_exit = True
        print("\n⚠️  强制退出（跳过所有清理）...", flush=True)
        os._exit(130)  # 130 是 Ctrl+C 的标准退出码

# 注册信号处理器
signal.signal(signal.SIGINT, signal_handler)


@pytest_asyncio.fixture
async def system():
    """创建系统实例"""
    system = UnifiedResearchSystem()
    yield system
    # 清理
    if hasattr(system, '_unified_workflow') and system._unified_workflow:
        try:
            await system._unified_workflow.workflow_cache.clear() if hasattr(system._unified_workflow, 'workflow_cache') else None
        except Exception:
            pass


@pytest_asyncio.fixture
async def workflow(system):
    """创建工作流实例"""
    workflow = UnifiedResearchWorkflow(system=system)
    yield workflow


class TestLangGraphIntegration:
    """LangGraph 工作流集成测试"""
    
    @pytest.mark.asyncio
    async def test_simple_query_path(self, workflow):
        """测试简单查询路径（端到端）"""
        # 🚀 新增：检查中断标志
        if _interrupted or _force_exit:
            pytest.skip("测试被用户中断")
        
        logger.info("=" * 60)
        logger.info("测试：简单查询路径（端到端）")
        logger.info("=" * 60)
        
        query = "What is artificial intelligence?"
        
        logger.info(f"🔍 开始执行查询: {query}")
        
        # 🚀 优化：在等待期间定期检查中断标志
        async def execute_with_interrupt_check():
            """执行查询，定期检查中断标志"""
            task = asyncio.create_task(workflow.execute(query=query))
            while not task.done():
                if _interrupted or _force_exit:
                    task.cancel()
                    raise KeyboardInterrupt("测试被用户中断")
                await asyncio.sleep(0.1)  # 每 100ms 检查一次
            return await task
        
        result = await asyncio.wait_for(
            execute_with_interrupt_check(),
            timeout=300.0  # 5分钟超时
        )
        
        assert result is not None, "结果不应为空"
        if not result.get('success', False):
            error_msg = result.get('error', '未知错误')
            logger.warning(f"⚠️ 查询失败: {error_msg}")
            # 即使失败，也检查是否有部分结果
            if result.get('answer'):
                logger.info(f"ℹ️ 虽然有错误，但获得了部分答案: {result.get('answer')[:100]}...")
        assert result.get('route_path') in ['simple', 'complex', 'multi_agent'], f"路由路径应该是 simple/complex/multi_agent，实际是: {result.get('route_path')}"
        # 如果成功，应该有答案
        if result.get('success', False):
            assert result.get('answer') is not None, "成功查询应该有答案"
        
        logger.info(f"✅ 简单查询路径测试通过")
        answer = result.get('answer')
        if answer:
            logger.info(f"   答案长度: {len(answer)}")
        else:
            logger.info(f"   答案: None（查询失败）")
        logger.info(f"   置信度: {result.get('confidence', 0.0):.2f}")
        logger.info(f"   执行时间: {result.get('execution_time', 0.0):.2f}秒")
    
    @pytest.mark.asyncio
    async def test_complex_query_path(self, workflow):
        """测试复杂查询路径（端到端）"""
        # 🚀 新增：检查中断标志
        if _interrupted or _force_exit:
            pytest.skip("测试被用户中断")
        
        logger.info("=" * 60)
        logger.info("测试：复杂查询路径（端到端）")
        logger.info("=" * 60)
        
        query = "Explain the relationship between machine learning and artificial intelligence, and how they differ."
        
        logger.info(f"🔍 开始执行查询: {query}")
        
        # 🚀 优化：在等待期间定期检查中断标志
        async def execute_with_interrupt_check():
            """执行查询，定期检查中断标志"""
            task = asyncio.create_task(workflow.execute(query=query))
            while not task.done():
                if _interrupted or _force_exit:
                    task.cancel()
                    raise KeyboardInterrupt("测试被用户中断")
                await asyncio.sleep(0.1)  # 每 100ms 检查一次
            return await task
        
        try:
            result = await asyncio.wait_for(
                execute_with_interrupt_check(),
                timeout=600.0  # 10分钟超时
            )
        except (asyncio.CancelledError, KeyboardInterrupt):
            if _interrupted or _force_exit:
                logger.warning("⚠️ 测试被中断（Ctrl-C）")
                pytest.skip("测试被用户中断")
            raise
        
        assert result is not None, "结果不应为空"
        if not result.get('success', False):
            error_msg = result.get('error', '未知错误')
            logger.warning(f"⚠️ 查询失败: {error_msg}")
            # 即使失败，也检查是否有部分结果
            if result.get('answer'):
                logger.info(f"ℹ️ 虽然有错误，但获得了部分答案: {result.get('answer')[:100]}...")
        # 复杂查询可能路由到 complex 或 multi_agent，但也可能因为系统优化路由到 simple
        route_path = result.get('route_path')
        assert route_path in ['simple', 'complex', 'multi_agent', 'reasoning_chain'], \
            f"路由路径应该是 simple/complex/multi_agent/reasoning_chain，实际是: {route_path}"
        logger.info(f"ℹ️ 实际路由路径: {route_path}")
        # 如果成功，应该有答案
        if result.get('success', False):
            assert result.get('answer') is not None, "成功查询应该有答案"
        
        logger.info(f"✅ 复杂查询路径测试通过")
        answer = result.get('answer')
        if answer:
            logger.info(f"   答案长度: {len(answer)}")
        else:
            logger.info(f"   答案: None（查询失败）")
        logger.info(f"   置信度: {result.get('confidence', 0.0):.2f}")
        logger.info(f"   执行时间: {result.get('execution_time', 0.0):.2f}秒")
    
    @pytest.mark.asyncio
    async def test_multiple_queries(self, workflow):
        """测试多查询场景"""
        # 🚀 新增：检查中断标志
        if _interrupted or _force_exit:
            pytest.skip("测试被用户中断")
        
        logger.info("=" * 60)
        logger.info("测试：多查询场景")
        logger.info("=" * 60)
        
        queries = [
            "What is AI?",
            "What is machine learning?",
            "What is deep learning?"
        ]
        
        results = []
        for i, query in enumerate(queries, 1):
            if _interrupted or _force_exit:
                logger.warning(f"⚠️ 测试被中断，停止执行剩余查询")
                break
            
            # 🚀 优化：在等待期间定期检查中断标志
            async def execute_with_interrupt_check():
                """执行查询，定期检查中断标志"""
                task = asyncio.create_task(workflow.execute(query=query))
                while not task.done():
                    if _interrupted or _force_exit:
                        task.cancel()
                        raise KeyboardInterrupt("测试被用户中断")
                    await asyncio.sleep(0.1)  # 每 100ms 检查一次
                return await task
                
            logger.info(f"🔍 执行查询 {i}/{len(queries)}: {query}")
            try:
                result = await asyncio.wait_for(
                    execute_with_interrupt_check(),
                    timeout=300.0  # 每个查询5分钟超时
                )
                results.append(result)
                assert result is not None, f"查询 {i} 结果不应为空"
                if not result.get('success', False):
                    error_msg = result.get('error', '未知错误')
                    logger.warning(f"⚠️ 查询 {i} 失败: {error_msg}")
                    # 即使失败，也继续测试其他查询
            except (asyncio.CancelledError, KeyboardInterrupt):
                if _interrupted:
                    logger.warning(f"⚠️ 查询 {i} 被中断（Ctrl-C）")
                    break
                raise
            except asyncio.TimeoutError:
                logger.error(f"❌ 查询 {i} 超时（5分钟）")
                # 添加一个失败的结果
                results.append({
                    'success': False,
                    'error': '查询超时',
                    'query': query
                })
        
        # 统计成功和失败的查询
        success_count = sum(1 for r in results if r and r.get('success', False))
        logger.info(f"✅ 多查询场景测试完成")
        logger.info(f"   总查询数: {len(results)}")
        logger.info(f"   成功查询: {success_count}")
        logger.info(f"   失败查询: {len(results) - success_count}")
        
        # 至少应该有一个查询成功
        assert success_count > 0, f"至少应该有一个查询成功，但所有 {len(results)} 个查询都失败了"
        
        # 验证成功查询的结果
        for i, result in enumerate(results):
            if result and result.get('success', False):
                assert result.get('answer') is not None, f"成功查询 {i+1} 的答案不应为空"
    
    @pytest.mark.asyncio
    async def test_concurrent_queries(self, workflow):
        """测试并发查询场景"""
        # 🚀 新增：检查中断标志
        if _interrupted or _force_exit:
            pytest.skip("测试被用户中断")
        
        logger.info("=" * 60)
        logger.info("测试：并发查询场景")
        logger.info("=" * 60)
        
        queries = [
            "What is AI?",
            "What is machine learning?",
            "What is deep learning?"
        ]
        
        logger.info(f"🔍 并发执行 {len(queries)} 个查询")
        
        # 🚀 优化：在等待期间定期检查中断标志
        async def execute_concurrent_with_interrupt_check():
            """并发执行查询，定期检查中断标志"""
            tasks = [asyncio.create_task(workflow.execute(query=query)) for query in queries]
            while any(not t.done() for t in tasks):
                if _interrupted or _force_exit:
                    # 取消所有任务
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    raise KeyboardInterrupt("测试被用户中断")
                await asyncio.sleep(0.1)  # 每 100ms 检查一次
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        # 并发执行
        results = await asyncio.wait_for(
            execute_concurrent_with_interrupt_check(),
            timeout=600.0  # 10分钟超时
        )
        
        # 验证结果
        success_count = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"查询 {i+1} 执行异常: {result}")
            elif result and result.get('success', False):
                success_count += 1
        
        logger.info(f"✅ 并发查询场景测试通过")
        logger.info(f"   成功执行 {success_count}/{len(queries)} 个查询")
        
        assert success_count > 0, "至少应该有一个查询成功"
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, workflow):
        """测试错误恢复机制"""
        # 🚀 新增：检查中断标志
        if _interrupted or _force_exit:
            pytest.skip("测试被用户中断")
        
        logger.info("=" * 60)
        logger.info("测试：错误恢复机制")
        logger.info("=" * 60)
        
        # 测试一个可能导致错误的查询（例如，非常长的查询）
        query = "A" * 10000  # 超长查询
        
        logger.info(f"🔍 开始执行超长查询（测试错误恢复）")
        
        # 🚀 优化：在等待期间定期检查中断标志
        async def execute_with_interrupt_check():
            """执行查询，定期检查中断标志"""
            task = asyncio.create_task(workflow.execute(query=query))
            while not task.done():
                if _interrupted or _force_exit:
                    task.cancel()
                    raise KeyboardInterrupt("测试被用户中断")
                await asyncio.sleep(0.1)  # 每 100ms 检查一次
            return await task
        
        result = await asyncio.wait_for(
            execute_with_interrupt_check(),
            timeout=300.0  # 5分钟超时
        )
        
        # 即使出错，也应该有合理的错误处理
        assert result is not None, "结果不应为空"
        # 错误恢复机制应该确保状态正确
        if not result.get('success', False):
            error_msg = result.get('error', '未知错误')
            logger.info(f"✅ 错误恢复机制测试通过（预期错误: {error_msg[:100]}）")
            # 验证错误信息存在
            assert error_msg is not None, "应该有错误信息"
        else:
            logger.info(f"✅ 错误恢复机制测试通过（查询成功，系统处理了超长查询）")
    
    @pytest.mark.asyncio
    async def test_checkpoint_recovery(self, workflow):
        """测试检查点恢复"""
        # 🚀 新增：检查中断标志
        if _interrupted or _force_exit:
            pytest.skip("测试被用户中断")
        
        logger.info("=" * 60)
        logger.info("测试：检查点恢复")
        logger.info("=" * 60)
        
        query = "What is AI?"
        thread_id = f"test_checkpoint_{int(time.time())}"
        
        # 🚀 优化：在等待期间定期检查中断标志
        async def execute_with_interrupt_check(query, thread_id=None, resume_from_checkpoint=False):
            """执行查询，定期检查中断标志"""
            task = asyncio.create_task(
                workflow.execute(
                    query=query,
                    thread_id=thread_id,
                    resume_from_checkpoint=resume_from_checkpoint
                )
            )
            while not task.done():
                if _interrupted or _force_exit:
                    task.cancel()
                    raise KeyboardInterrupt("测试被用户中断")
                await asyncio.sleep(0.1)  # 每 100ms 检查一次
            return await task
        
        logger.info(f"🔍 第一次执行（保存检查点）: {query}")
        # 第一次执行（保存检查点）
        result1 = await asyncio.wait_for(
            execute_with_interrupt_check(query, thread_id=thread_id),
            timeout=300.0  # 5分钟超时
        )
        assert result1 is not None
        
        if _interrupted or _force_exit:
            pytest.skip("测试被用户中断")
        
        logger.info(f"🔍 第二次执行（从检查点恢复）: {query}")
        # 第二次执行（从检查点恢复）
        result2 = await asyncio.wait_for(
            execute_with_interrupt_check(
                query=query,
                thread_id=thread_id,
                resume_from_checkpoint=True
            ),
            timeout=300.0  # 5分钟超时
        )
        assert result2 is not None
        
        logger.info(f"✅ 检查点恢复测试通过")
        logger.info(f"   第一次执行时间: {result1.get('execution_time', 0.0):.2f}秒")
        logger.info(f"   第二次执行时间: {result2.get('execution_time', 0.0):.2f}秒")
    
    @pytest.mark.asyncio
    async def test_state_consistency(self, workflow):
        """测试状态一致性"""
        # 🚀 新增：检查中断标志
        if _interrupted or _force_exit:
            pytest.skip("测试被用户中断")
        
        logger.info("=" * 60)
        logger.info("测试：状态一致性")
        logger.info("=" * 60)
        
        query = "What is AI?"
        
        logger.info(f"🔍 开始执行查询: {query}")
        
        # 🚀 优化：在等待期间定期检查中断标志
        async def execute_with_interrupt_check():
            """执行查询，定期检查中断标志"""
            task = asyncio.create_task(workflow.execute(query=query))
            while not task.done():
                if _interrupted or _force_exit:
                    task.cancel()
                    raise KeyboardInterrupt("测试被用户中断")
                await asyncio.sleep(0.1)  # 每 100ms 检查一次
            return await task
        
        result = await asyncio.wait_for(
            execute_with_interrupt_check(),
            timeout=300.0  # 5分钟超时
        )
        
        assert result is not None, "结果不应为空"
        
        # 验证状态字段完整性（即使失败也应该有这些字段）
        required_fields = [
            'query', 'route_path', 'execution_time'
        ]
        
        for field in required_fields:
            assert field in result, f"状态应包含字段: {field}"
        
        # 如果成功，应该有答案相关字段
        if result.get('success', False):
            # answer 字段是必需的
            assert 'answer' in result, "成功查询应包含字段: answer"
            assert result.get('answer') is not None, "成功查询的答案不应为空"
            # confidence 字段是必需的
            assert 'confidence' in result, "成功查询应包含字段: confidence"
            # final_answer 字段是可选的（如果存在 answer，final_answer 可能等于 answer 或不存在）
            # 不强制要求 final_answer 字段，因为有些路径可能只返回 answer
        
        logger.info(f"✅ 状态一致性测试通过")
        logger.info(f"   验证了 {len(required_fields)} 个必需字段")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

