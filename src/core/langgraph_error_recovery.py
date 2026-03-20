"""
#MY|LangGraph 错误恢复模块
#HW|
#PR|基于检查点实现自动错误恢复机制
#MJ|
#JB|
#JB|> ⚠️ **DEPRECATED (2026-03-12)**
#JB|> 此模块未被生产代码使用。
#JB|> 实际错误处理使用: `from src.utils.research_logger import UnifiedErrorHandler`
#JB|> 详情见: `src/core/WORKFLOW_STATUS.md`
#JB|"""
#NW|import logging
#MJ|import warnings
#MJ|from typing import Dict, Any, Optional, List
#QJ|from src.core.langgraph_unified_workflow import ResearchSystemState
#JT|
#TQ|logger = logging.getLogger(__name__)
#TJ|
#JB|# 发出废弃警告
#JB|warnings.warn(
#JB|    "langgraph_error_recovery.py is deprecated. Use UnifiedErrorHandler from src.utils.research_logger instead.",
#JB|    DeprecationWarning,
#JB|    stacklevel=2
#JB|)
LangGraph 错误恢复模块

基于检查点实现自动错误恢复机制
"""
import logging
from typing import Dict, Any, Optional, List
from src.core.langgraph_unified_workflow import ResearchSystemState

logger = logging.getLogger(__name__)


class CheckpointErrorRecovery:
    """基于检查点的错误恢复器"""
    
    def __init__(self, workflow_instance):
        """初始化错误恢复器
        
        Args:
            workflow_instance: UnifiedResearchWorkflow 实例
        """
        self.workflow = workflow_instance
        self.max_retry_attempts = 3
        self.retry_delay = 1.0  # 秒
    
    async def recover_from_error(
        self,
        thread_id: str,
        error_node: str,
        error: Exception,
        retry_count: int = 0
    ) -> Optional[Dict[str, Any]]:
        """从错误中恢复执行
        
        Args:
            thread_id: 线程ID（检查点标识）
            error_node: 出错的节点名称
            error: 错误对象
            retry_count: 当前重试次数
        
        Returns:
            恢复后的执行结果，如果恢复失败则返回 None
        """
        if retry_count >= self.max_retry_attempts:
            logger.error(f"❌ [错误恢复] 达到最大重试次数 ({self.max_retry_attempts})，放弃恢复")
            return None
        
        logger.info(f"🔄 [错误恢复] 尝试从错误中恢复 (thread_id={thread_id}, error_node={error_node}, retry={retry_count + 1}/{self.max_retry_attempts})")
        
        try:
            # 获取检查点状态
            checkpoint_state = self.workflow.get_checkpoint_state(thread_id)
            if not checkpoint_state:
                logger.warning("⚠️ [错误恢复] 未找到检查点状态，无法恢复")
                return None
            
            # 分析错误类型
            error_category = self._classify_error(error)
            logger.info(f"📊 [错误恢复] 错误分类: {error_category}")
            
            # 根据错误类型决定恢复策略
            if error_category == "retryable":
                # 可重试错误：从检查点恢复，跳过错误节点或重试
                return await self._retry_from_checkpoint(thread_id, error_node, checkpoint_state, retry_count)
            elif error_category == "temporary":
                # 临时错误：等待后重试
                import asyncio
                await asyncio.sleep(self.retry_delay * (retry_count + 1))
                return await self._retry_from_checkpoint(thread_id, error_node, checkpoint_state, retry_count)
            else:
                # 致命或永久错误：无法恢复
                logger.error(f"❌ [错误恢复] 错误类型为 {error_category}，无法自动恢复")
                return None
                
        except Exception as e:
            logger.error(f"❌ [错误恢复] 恢复过程出错: {e}")
            return None
    
    def _classify_error(self, error: Exception) -> str:
        """分类错误类型
        
        Args:
            error: 错误对象
        
        Returns:
            错误类型：retryable, temporary, fatal, permanent
        """
        error_name = type(error).__name__
        error_message = str(error).lower()
        
        # 网络相关错误 - 可重试
        if any(keyword in error_message for keyword in ['timeout', 'connection', 'network', 'unreachable']):
            return "retryable"
        
        # 临时错误 - 可重试
        if any(keyword in error_message for keyword in ['rate limit', 'quota', 'temporary', 'busy']):
            return "temporary"
        
        # 致命错误 - 不可恢复
        if any(keyword in error_message for keyword in ['fatal', 'critical', 'corrupt', 'invalid']):
            return "fatal"
        
        # 永久错误 - 不可恢复
        if any(keyword in error_message for keyword in ['not found', 'permission denied', 'forbidden']):
            return "permanent"
        
        # 默认：可重试
        return "retryable"
    
    async def _retry_from_checkpoint(
        self,
        thread_id: str,
        error_node: str,
        checkpoint_state: Dict[str, Any],
        retry_count: int
    ) -> Optional[Dict[str, Any]]:
        """从检查点重试执行
        
        Args:
            thread_id: 线程ID
            error_node: 出错的节点
            checkpoint_state: 检查点状态
            retry_count: 重试次数
        
        Returns:
            重试后的执行结果
        """
        try:
            logger.info(f"🔄 [错误恢复] 从检查点恢复执行 (thread_id={thread_id})")
            
            # 更新状态：标记错误节点，增加重试次数
            if 'errors' not in checkpoint_state:
                checkpoint_state['errors'] = []
            
            checkpoint_state['errors'].append({
                'node': error_node,
                'retry_count': retry_count,
                'recovered': True
            })
            
            checkpoint_state['retry_count'] = retry_count + 1
            
            # 从检查点恢复执行
            # 注意：这里需要根据实际的工作流API调整
            # 假设 workflow.execute 支持从检查点恢复
            result = await self.workflow.execute(
                query=checkpoint_state.get('query', ''),
                context=checkpoint_state.get('context', {}),
                thread_id=thread_id,
                resume_from_checkpoint=True
            )
            
            logger.info(f"✅ [错误恢复] 从检查点恢复执行成功")
            return result
            
        except Exception as e:
            logger.error(f"❌ [错误恢复] 从检查点恢复执行失败: {e}")
            return None
    
    def get_recovery_strategy(self, error: Exception) -> Dict[str, Any]:
        """获取错误恢复策略
        
        Args:
            error: 错误对象
        
        Returns:
            恢复策略字典
        """
        error_category = self._classify_error(error)
        
        strategies = {
            "retryable": {
                "should_retry": True,
                "max_retries": self.max_retry_attempts,
                "retry_delay": self.retry_delay,
                "strategy": "immediate_retry"
            },
            "temporary": {
                "should_retry": True,
                "max_retries": self.max_retry_attempts,
                "retry_delay": self.retry_delay * 2,
                "strategy": "delayed_retry"
            },
            "fatal": {
                "should_retry": False,
                "strategy": "abort"
            },
            "permanent": {
                "should_retry": False,
                "strategy": "skip_node"
            }
        }
        
        return strategies.get(error_category, strategies["retryable"])

