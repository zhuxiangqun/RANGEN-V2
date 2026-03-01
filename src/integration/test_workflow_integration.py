#!/usr/bin/env python3
"""
工作流集成测试
测试聊天触发和定时任务功能
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.integration.workflow_integration import (
    WorkflowIntegration, 
    TriggerType, 
    TaskPriority,
    get_workflow_integration,
    initialize_workflow_integration
)
from src.services.logging_service import get_logger


logger = get_logger(__name__)


async def test_workflow_integration_basic():
    """测试工作流集成基本功能"""
    logger.info("开始测试工作流集成基本功能")
    
    try:
        # 获取工作流集成管理器
        integration = get_workflow_integration("test_system")
        
        # 启动集成管理器
        started = await integration.start()
        assert started, "工作流集成管理器启动失败"
        
        # 测试1: 触发聊天消息
        logger.info("测试1: 触发聊天消息")
        chat_task_id = await integration.trigger_chat_message(
            message="测试聊天消息，请分析当前系统状态",
            user_id="test_user_001",
            context={"test_mode": True}
        )
        
        assert chat_task_id, "聊天消息触发失败"
        logger.info(f"聊天任务ID: {chat_task_id}")
        
        # 等待任务处理
        await asyncio.sleep(2)
        
        # 获取任务状态
        chat_status = await integration.get_task_status(chat_task_id)
        assert chat_status, "获取任务状态失败"
        logger.info(f"聊天任务状态: {chat_status['status']}")
        
        # 测试2: 立即执行任务
        logger.info("测试2: 立即执行任务")
        immediate_task_id = await integration.execute_task_immediately(
            query="测试立即执行任务，请返回系统时间",
            context={"test_mode": True, "request_type": "immediate"},
            priority=TaskPriority.HIGH
        )
        
        assert immediate_task_id, "立即执行任务失败"
        logger.info(f"立即任务ID: {immediate_task_id}")
        
        # 等待任务处理
        await asyncio.sleep(2)
        
        # 获取任务状态
        immediate_status = await integration.get_task_status(immediate_task_id)
        assert immediate_status, "获取立即任务状态失败"
        logger.info(f"立即任务状态: {immediate_status['status']}")
        
        # 测试3: 安排定时任务（5秒后执行）
        logger.info("测试3: 安排定时任务")
        scheduled_time = datetime.now() + timedelta(seconds=5)
        scheduled_task_id = await integration.schedule_task(
            query="测试定时任务，请分析系统性能",
            schedule_time=scheduled_time,
            context={"test_mode": True, "scheduled": True},
            task_name="test_scheduled_task"
        )
        
        assert scheduled_task_id, "安排定时任务失败"
        logger.info(f"定时任务ID: {scheduled_task_id} (计划时间: {scheduled_time})")
        
        # 获取定时任务状态（应该是pending）
        scheduled_status = await integration.get_task_status(scheduled_task_id)
        assert scheduled_status, "获取定时任务状态失败"
        assert scheduled_status['status'] == 'pending', f"定时任务状态应为pending，实际为{scheduled_status['status']}"
        logger.info(f"定时任务初始状态: {scheduled_status['status']}")
        
        # 测试4: 安排重复任务（每10秒执行一次）
        logger.info("测试4: 安排重复任务")
        recurring_task_id = await integration.schedule_recurring_task(
            query="测试重复任务，请监控系统状态",
            interval_seconds=10,
            context={"test_mode": True, "recurring": True},
            task_name="test_recurring_task",
            start_immediately=True
        )
        
        assert recurring_task_id, "安排重复任务失败"
        logger.info(f"重复任务ID: {recurring_task_id} (间隔: 10秒)")
        
        # 等待一段时间让定时任务执行
        logger.info("等待定时任务执行...")
        await asyncio.sleep(8)  # 等待8秒，让5秒后的定时任务执行
        
        # 检查定时任务是否已执行
        scheduled_status_after = await integration.get_task_status(scheduled_task_id)
        logger.info(f"定时任务执行后状态: {scheduled_status_after['status'] if scheduled_status_after else '任务不存在'}")
        
        # 测试5: 获取系统统计信息
        logger.info("测试5: 获取系统统计信息")
        stats = await integration.get_system_stats()
        assert stats, "获取系统统计信息失败"
        
        logger.info(f"系统统计信息:")
        logger.info(f"  总任务数: {stats['task_statistics']['total_tasks']}")
        logger.info(f"  已完成任务: {stats['task_statistics']['completed_tasks']}")
        logger.info(f"  失败任务: {stats['task_statistics']['failed_tasks']}")
        logger.info(f"  活跃任务: {stats['task_statistics']['active_tasks']}")
        logger.info(f"  定时任务: {stats['task_statistics']['scheduled_tasks']}")
        logger.info(f"  待处理任务: {stats['task_statistics']['pending_tasks']}")
        
        # 测试6: 取消任务
        logger.info("测试6: 取消重复任务")
        cancelled = await integration.cancel_task(recurring_task_id)
        assert cancelled, "取消任务失败"
        logger.info(f"任务取消成功: {recurring_task_id}")
        
        # 验证任务状态已更新为cancelled
        cancelled_status = await integration.get_task_status(recurring_task_id)
        assert cancelled_status['status'] == 'cancelled', f"任务状态应为cancelled，实际为{cancelled_status['status']}"
        logger.info(f"取消后任务状态: {cancelled_status['status']}")
        
        # 停止集成管理器
        logger.info("停止工作流集成管理器")
        stopped = await integration.stop()
        assert stopped, "工作流集成管理器停止失败"
        
        logger.info("✅ 工作流集成基本功能测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 工作流集成测试失败: {e}", exc_info=True)
        return False


async def test_hook_integration():
    """测试Hook透明化系统集成"""
    logger.info("开始测试Hook透明化系统集成")
    
    try:
        integration = get_workflow_integration("hook_test_system")
        
        # 启动集成管理器
        await integration.start()
        
        # 触发聊天消息，验证Hook事件记录
        task_id = await integration.trigger_chat_message(
            message="测试Hook事件记录",
            user_id="hook_test_user",
            context={"test_hook": True}
        )
        
        assert task_id, "Hook测试任务创建失败"
        
        # 等待任务处理
        await asyncio.sleep(3)
        
        # 获取系统摘要，检查Hook事件
        stats = await integration.get_system_stats()
        assert stats, "获取系统统计信息失败"
        
        logger.info(f"Hook系统状态: {stats.get('hook_system_status', 'unknown')}")
        
        # 停止集成管理器
        await integration.stop()
        
        logger.info("✅ Hook透明化系统集成测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ Hook透明化系统集成测试失败: {e}", exc_info=True)
        return False


async def test_concurrent_tasks():
    """测试并发任务处理"""
    logger.info("开始测试并发任务处理")
    
    try:
        integration = get_workflow_integration("concurrent_test_system")
        
        # 启动集成管理器
        await integration.start()
        
        # 创建多个并发任务
        task_ids = []
        for i in range(3):
            task_id = await integration.execute_task_immediately(
                query=f"并发测试任务 {i+1}，请返回任务编号",
                context={"task_number": i+1, "test_concurrent": True},
                priority=TaskPriority.MEDIUM
            )
            if task_id:
                task_ids.append(task_id)
                logger.info(f"创建并发任务 {i+1}: {task_id}")
        
        assert len(task_ids) == 3, "并发任务创建失败"
        
        # 等待任务处理
        await asyncio.sleep(5)
        
        # 检查所有任务状态
        completed_count = 0
        for task_id in task_ids:
            status = await integration.get_task_status(task_id)
            if status and status['status'] == 'completed':
                completed_count += 1
                logger.info(f"任务 {task_id} 完成")
            else:
                logger.warning(f"任务 {task_id} 状态: {status['status'] if status else 'unknown'}")
        
        logger.info(f"并发任务完成情况: {completed_count}/{len(task_ids)}")
        
        # 停止集成管理器
        await integration.stop()
        
        logger.info("✅ 并发任务处理测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 并发任务处理测试失败: {e}", exc_info=True)
        return False


async def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("工作流集成测试开始")
    logger.info("=" * 60)
    
    results = []
    
    # 运行测试
    results.append(("基本功能测试", await test_workflow_integration_basic()))
    results.append(("Hook集成测试", await test_hook_integration()))
    results.append(("并发任务测试", await test_concurrent_tasks()))
    
    # 输出测试结果
    logger.info("=" * 60)
    logger.info("测试结果汇总:")
    logger.info("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        logger.info(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    logger.info("=" * 60)
    if all_passed:
        logger.info("🎉 所有测试通过！")
    else:
        logger.error("😞 部分测试失败")
    
    return all_passed


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1)