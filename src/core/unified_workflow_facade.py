"""
统一工作流入口 - Unified Workflow Facade

职责:
1. 提供单一入口点访问所有工作流
2. 管理不同工作流模式的切换
3. 整合 ExecutionCoordinator 作为主入口
4. 整合废弃的 langgraph_unified_workflow.py

使用方式:
    from src.core.unified_workflow_facade import get_workflow
    
    # 获取默认工作流 (ExecutionCoordinator)
    workflow = get_workflow()
    result = await workflow.execute(query)
    
    # 获取特定模式工作流
    workflow = get_workflow(mode="layered")
"""

from enum import Enum
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

from src.services.logging_service import get_logger

logger = get_logger(__name__)


class WorkflowMode(Enum):
    """工作流模式枚举"""
    STANDARD = "standard"      # 标准模式 (ExecutionCoordinator)
    LAYERED = "layered"        # 分层模式 (简化版)
    BUSINESS = "business"       # 业务模式 (简化版)


@dataclass
class WorkflowConfig:
    """工作流配置"""
    mode: WorkflowMode = WorkflowMode.STANDARD
    enable_checkpointer: bool = True
    enable_monitoring: bool = True
    max_retries: int = 3
    timeout: float = 60.0


class UnifiedWorkflowFacade:
    """
    统一工作流门面类
    
    提供统一的工作流访问接口，隐藏内部实现细节。
    支持不同工作流模式的热切换。
    """
    
    _instance: Optional['UnifiedWorkflowFacade'] = None
    _workflow: Optional[Any] = None
    _current_mode: WorkflowMode = WorkflowMode.STANDARD
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[WorkflowConfig] = None):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._config = config or WorkflowConfig()
        self._initialized = True
        self._workflow_registry: Dict[WorkflowMode, Callable] = {}
        
        # 注册工作流工厂
        self._register_workflows()
        
        logger.info(f"✅ UnifiedWorkflowFacade 初始化完成, 模式: {self._current_mode.value}")
    
    def _register_workflows(self):
        """注册可用工作流"""
        # 标准模式 - 使用 ExecutionCoordinator
        self._workflow_registry[WorkflowMode.STANDARD] = self._create_standard_workflow
        
        # 分层模式 - 使用 SimplifiedLayeredWorkflow
        self._workflow_registry[WorkflowMode.LAYERED] = self._create_layered_workflow
        
        # 业务模式 - 使用 SimplifiedBusinessWorkflow  
        self._workflow_registry[WorkflowMode.BUSINESS] = self._create_business_workflow
    
    def _create_standard_workflow(self):
        """创建标准工作流 (ExecutionCoordinator)"""
        from src.core.execution_coordinator import ExecutionCoordinator
        return ExecutionCoordinator()
    
    def _create_layered_workflow(self):
        """创建分层工作流"""
        # 延迟导入避免循环依赖
        from src.core.simplified_layered_workflow import SimplifiedLayeredWorkflow
        return SimplifiedLayeredWorkflow()
    
    def _create_business_workflow(self):
        """创建业务工作流"""
        from src.core.simplified_business_workflow import SimplifiedBusinessWorkflow
        return SimplifiedBusinessWorkflow()
    
    def get_workflow(self, mode: Optional[WorkflowMode] = None):
        """
        获取工作流实例
        
        Args:
            mode: 工作流模式，如果为 None 则使用当前模式
            
        Returns:
            工作流实例
        """
        target_mode = mode or self._current_mode
        
        # 如果模式切换，创建新的工作流
        if target_mode != self._current_mode:
            self._switch_mode(target_mode)
        
        return self._workflow
    
    def _switch_mode(self, mode: WorkflowMode):
        """切换工作流模式"""
        logger.info(f"🔄 切换工作流模式: {self._current_mode.value} -> {mode.value}")
        
        if mode not in self._workflow_registry:
            logger.warning(f"⚠️ 未知工作流模式: {mode.value}, 使用标准模式")
            mode = WorkflowMode.STANDARD
        
        factory = self._workflow_registry[mode]
        self._workflow = factory()
        self._current_mode = mode
        
        logger.info(f"✅ 工作流模式切换完成: {mode.value}")
    
    async def execute(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None,
        mode: Optional[WorkflowMode] = None
    ) -> Dict[str, Any]:
        """
        执行工作流
        
        Args:
            query: 用户查询
            context: 上下文
            mode: 指定工作流模式
            
        Returns:
            执行结果
        """
        workflow = self.get_workflow(mode)
        
        try:
            # 统一调用接口
            if hasattr(workflow, 'execute'):
                if hasattr(workflow.execute, '__await__'):
                    result = await workflow.execute(query, context)
                else:
                    result = workflow.execute(query, context)
            elif hasattr(workflow, 'run'):
                result = await workflow.run(query, context)
            else:
                # ExecutionCoordinator 使用 invoke
                result = await workflow.graph.ainvoke({
                    "query": query,
                    "context": context or {}
                })
            
            return result if result else {}
            
        except Exception as e:
            logger.error(f"❌ 工作流执行失败: {e}")
            return {
                "error": str(e),
                "query": query,
                "status": "failed"
            }
    
    @property
    def current_mode(self) -> WorkflowMode:
        """获取当前工作流模式"""
        return self._current_mode
    
    def list_available_modes(self) -> list:
        """列出可用工作流模式"""
        return [mode.value for mode in self._workflow_registry.keys()]


# 全局单例访问函数
_workflow_facade: Optional[UnifiedWorkflowFacade] = None


def get_workflow(config: Optional[WorkflowConfig] = None) -> UnifiedWorkflowFacade:
    """
    获取统一工作流门面单例
    
    Args:
        config: 工作流配置
        
    Returns:
        UnifiedWorkflowFacade 实例
    """
    global _workflow_facade
    
    if _workflow_facade is None:
        _workflow_facade = UnifiedWorkflowFacade(config)
    
    return _workflow_facade


def get_execution_coordinator():
    """
    获取默认的 ExecutionCoordinator (向后兼容)
    
    推荐使用 get_workflow() 代替
    """
    facade = get_workflow()
    return facade.get_workflow(WorkflowMode.STANDARD)


# 导出常用接口
__all__ = [
    'UnifiedWorkflowFacade',
    'WorkflowMode', 
    'WorkflowConfig',
    'get_workflow',
    'get_execution_coordinator'
]
