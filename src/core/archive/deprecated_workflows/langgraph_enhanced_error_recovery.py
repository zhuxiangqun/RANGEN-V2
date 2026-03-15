"""
#MY|LangGraph 增强错误恢复模块
#HW|
#PZ|支持 LangGraph Command API 和工作流级备用路由
#MJ|
#JB|> ⚠️ **DEPRECATED (2026-03-12)**
#JB|> 此模块未被生产代码使用。
#JB|> 实际错误处理使用: `from src.utils.research_logger import UnifiedErrorHandler`
#JB|> 详情见: `src/core/WORKFLOW_STATUS.md`
#JB|"""
#NW|import logging
#NK|import warnings
#NK|import asyncio
#QB|from typing import Dict, Any, Optional, Union
#QJ|from src.core.langgraph_unified_workflow import ResearchSystemState
#SK|
#JB|# 废弃警告
#JB|warnings.warn(
#JB|    "langgraph_enhanced_error_recovery.py is deprecated. Use UnifiedErrorHandler from src.utils.research_logger instead.",
#JB|    DeprecationWarning,
#JB|    stacklevel=2
#JB|)
LangGraph 增强错误恢复模块

支持 LangGraph Command API 和工作流级备用路由
"""
import logging
import asyncio
from typing import Dict, Any, Optional, Union
from src.core.langgraph_unified_workflow import ResearchSystemState

logger = logging.getLogger(__name__)

# 尝试导入 LangGraph Command API
try:
    from langgraph.types import Command
    COMMAND_API_AVAILABLE = True
except ImportError:
    COMMAND_API_AVAILABLE = False
    Command = None
    # 🚀 优化：使用 DEBUG 级别，因为这是可选的依赖，系统有备用错误恢复策略
    logger.debug("ℹ️ LangGraph Command API 不可用（这是可选的，系统将使用备用错误恢复策略）")


class EnhancedErrorRecovery:
    """增强错误恢复器 - 支持 LangGraph Command API 和工作流级备用路由"""
    
    def __init__(self):
        """初始化增强错误恢复器"""
        self.logger = logging.getLogger(__name__)
    
    def should_use_command_retry(self, error: Exception) -> bool:
        """判断是否应该使用 Command API 进行延迟重试
        
        Args:
            error: 错误对象
        
        Returns:
            是否应该使用 Command API
        """
        if not COMMAND_API_AVAILABLE:
            return False
        
        error_message = str(error).lower()
        error_name = type(error).__name__
        
        # 速率限制错误 - 使用延迟重试
        if any(keyword in error_message for keyword in ['rate limit', 'quota', '429']):
            return True
        
        # 临时服务不可用 - 使用延迟重试
        if any(keyword in error_message for keyword in ['temporary', 'unavailable', '503', '502']):
            return True
        
        # 特定错误类型
        if error_name in ['RateLimitError', 'TemporaryUnavailableError']:
            return True
        
        return False
    
    def create_reschedule_command(self, error: Exception, delay_seconds: int = 60) -> Optional[Any]:
        """创建延迟重试的 Command 对象
        
        LangGraph Command API 主要用于控制节点流转和状态更新。
        对于延迟重试，我们使用以下策略：
        1. 如果 Command API 可用，尝试使用 Command 更新状态并标记需要延迟
        2. 如果 Command API 不可用或参数不支持，返回 None，使用备用策略（asyncio.sleep）
        
        Args:
            error: 错误对象
            delay_seconds: 延迟秒数
        
        Returns:
            Command 对象（如果可用且支持），否则返回 None
        """
        if not COMMAND_API_AVAILABLE:
            self.logger.debug("ℹ️ Command API 不可用，将使用 asyncio.sleep 实现延迟重试")
            return None
        
        if not self.should_use_command_retry(error):
            return None
        
        try:
            self.logger.info(f"🔄 [增强错误恢复] 创建延迟重试命令: {delay_seconds}秒后重试")
            
            # 🚀 策略1：尝试使用 Command 更新状态，标记需要延迟重试
            # 在工作流中，可以检查状态中的 'reschedule_after' 字段来实现延迟
            try:
                # 使用 Command 更新状态，标记延迟重试信息
                # 注意：LangGraph Command 主要用于 goto 和 update，不直接支持延迟
                # 我们通过更新状态来实现延迟重试的逻辑
                import time
                return Command(
                    update={
                        'reschedule_after': delay_seconds,
                        'reschedule_error': str(error),
                        'reschedule_timestamp': time.time(),
                        'need_reschedule': True
                    }
                )
            except TypeError as e:
                # 如果 Command 不接受 update 参数，尝试其他格式
                self.logger.debug(f"Command(update=...) 格式不支持: {e}，尝试其他格式")
                try:
                    # 尝试使用 goto 参数跳转到延迟节点（如果工作流中有延迟节点）
                    # 注意：这需要工作流中有一个专门的延迟节点
                    return Command(goto="delay_retry_node")
                except TypeError:
                    # 如果都不支持，返回 None，使用备用策略
                    self.logger.debug(
                        f"Command API 不支持延迟重试参数，将使用 asyncio.sleep 实现延迟重试"
                    )
                    return None
        except Exception as e:
            # 捕获任何其他异常，优雅降级
            self.logger.debug(
                f"创建延迟重试命令时出错: {e}。将使用 asyncio.sleep 实现延迟重试。"
            )
            return None
    
    def should_route_to_fallback(self, state: ResearchSystemState) -> bool:
        """判断是否应该路由到备用节点
        
        Args:
            state: 工作流状态
        
        Returns:
            是否应该路由到备用节点
        """
        # 检查是否有错误标记
        if state.get('need_fallback', False):
            return True
        
        # 检查错误计数
        errors = state.get('errors', [])
        if len(errors) > 0:
            # 如果最近的错误是不可恢复的，路由到备用节点
            last_error = errors[-1]
            if last_error.get('category') in ['fatal', 'permanent']:
                return True
        
        # 检查重试次数
        retry_count = state.get('retry_count', 0)
        if retry_count >= 3:  # 达到最大重试次数
            return True
        
        return False
    
    def get_fallback_route(self, node_name: str) -> str:
        """获取备用路由节点名称
        
        Args:
            node_name: 当前节点名称
        
        Returns:
            备用节点名称
        """
        # 定义节点到备用节点的映射
        fallback_map = {
            'knowledge_retrieval_agent': 'fallback_knowledge_retrieval',
            'reasoning_agent': 'fallback_reasoning',
            'answer_generation_agent': 'fallback_answer_generation',
            'citation_agent': 'fallback_citation',
            'generate_steps': 'fallback_reasoning',
            'execute_step': 'fallback_reasoning',
        }
        
        return fallback_map.get(node_name, 'synthesize')  # 默认路由到 synthesize


def create_resilient_node_with_command(
    node_func,
    node_name: str,
    fallback_node: Optional[Any] = None
):
    """创建支持 Command API 的弹性节点
    
    Args:
        node_func: 节点函数
        node_name: 节点名称
        fallback_node: 备用节点函数（可选）
    
    Returns:
        增强的节点函数
    """
    recovery = EnhancedErrorRecovery()
    
    async def resilient_wrapper(state: ResearchSystemState) -> Union[ResearchSystemState, Any]:
        """弹性节点包装器"""
        try:
            result = await node_func(state)
            return result
        except Exception as e:
            # 尝试使用 Command API 延迟重试
            command = recovery.create_reschedule_command(e, delay_seconds=60)
            if command:
                logger.info(f"🔄 [{node_name}] 使用 Command API 延迟重试: 60秒后重试")
                return command
            
            # 🚀 备用策略：如果 Command API 不可用，使用 asyncio.sleep 实现延迟重试
            if recovery.should_use_command_retry(e):
                delay_seconds = 60
                logger.info(f"🔄 [{node_name}] 使用 asyncio.sleep 实现延迟重试: {delay_seconds}秒后重试")
                await asyncio.sleep(delay_seconds)
                # 延迟后，尝试重新执行节点
                try:
                    logger.info(f"🔄 [{node_name}] 延迟后重新执行节点")
                    result = await node_func(state)
                    return result
                except Exception as retry_error:
                    logger.warning(f"⚠️ [{node_name}] 延迟重试后仍然失败: {retry_error}")
                    # 继续执行备用路由逻辑
            
            # 如果 Command API 不可用或不应该使用，标记需要备用路由
            state['need_fallback'] = True
            state['error'] = str(e)
            
            # 如果有备用节点，尝试使用
            if fallback_node:
                logger.info(f"🔄 [{node_name}] 尝试备用节点")
                try:
                    return await fallback_node(state)
                except Exception as fallback_error:
                    logger.error(f"❌ [{node_name}] 备用节点也失败: {fallback_error}")
            
            return state
    
    return resilient_wrapper

