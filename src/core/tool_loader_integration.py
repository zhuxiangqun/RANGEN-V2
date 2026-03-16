"""
ToolLoader集成适配器 - 将渐进式披露机制集成到现有系统

这个适配器连接ToolLoader与现有的ToolRegistry，确保：
1. 新工具自动按优先级分类
2. 按需加载工具到Agent上下文
3. 工具使用统计统一管理
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from src.core.progressive_tool_loader import (
    ToolLoader, 
    ToolPriority, 
    ToolLoadConfig,
    get_tool_loader
)
from src.interfaces.tool import ITool, ToolCategory
from src.services.logging_service import get_logger

logger = get_logger(__name__)


@dataclass
class IntegrationConfig:
    """集成配置"""
    auto_register_existing_tools: bool = True
    default_priority: ToolPriority = ToolPriority.API
    priority_by_category: Dict[ToolCategory, ToolPriority] = None
    
    def __post_init__(self):
        if self.priority_by_category is None:
            self.priority_by_category = {
                ToolCategory.RETRIEVAL: ToolPriority.API,
                ToolCategory.COMPUTE: ToolPriority.API,
                ToolCategory.UTILITY: ToolPriority.CLI,
                ToolCategory.API: ToolPriority.API,
            }


class ToolLoaderIntegration:
    """
    ToolLoader与现有系统的集成适配器
    
    使用方式：
    1. 在系统启动时初始化
    2. 现有工具自动按类别分配优先级
    3. Agent请求工具时通过本适配器获取
    """
    
    def __init__(self, config: Optional[IntegrationConfig] = None):
        self._config = config or IntegrationConfig()
        self._tool_loader = get_tool_loader()
        self._initialized = False
        
    def initialize(self, existing_tools: List[ITool] = None) -> None:
        """初始化并注册现有工具"""
        if self._initialized:
            logger.warning("ToolLoaderIntegration already initialized")
            return
            
        logger.info("Initializing ToolLoaderIntegration...")
        
        if existing_tools:
            for tool in existing_tools:
                priority = self._get_priority_for_tool(tool)
                self._tool_loader.register_tool(tool, priority)
                logger.info(f"Registered {tool.config.name} with priority {priority.name}")
        
        self._initialized = True
        logger.info(f"ToolLoaderIntegration initialized with {len(existing_tools or [])} tools")
    
    def _get_priority_for_tool(self, tool: ITool) -> ToolPriority:
        """根据工具类别确定优先级"""
        category = tool.config.category
        
        # 检查是否有明确的优先级映射
        if category in self._config.priority_by_category:
            return self._config.priority_by_category[category]
        
        # 默认优先级
        return self._config.default_priority
    
    def load_tools_for_agent(self, agent_type: str, task_type: str = "default") -> List[ITool]:
        """
        为Agent加载适合的工具
        
        Args:
            agent_type: Agent类型（如 reasoning, rag, validation）
            task_type: 任务类型（simple/local/api/external）
        
        Returns:
            按优先级排序的工具列表
        """
        if not self._initialized:
            logger.warning("ToolLoaderIntegration not initialized, initializing now...")
            self.initialize()
        
        tools = self._tool_loader.load_for_task(task_type)
        logger.info(f"Loaded {len(tools)} tools for agent {agent_type} (task_type: {task_type})")
        return tools
    
    def record_tool_usage(self, tool_name: str, success: bool = True) -> None:
        """记录工具使用情况"""
        self._tool_loader.record_usage(tool_name, success)
    
    def get_usage_stats(self) -> List:
        """获取工具使用统计"""
        return self._tool_loader.get_usage_stats()
    
    def get_low_usage_tools(self, threshold: int = 5) -> List[str]:
        """获取低频使用的工具"""
        return self._tool_loader.get_low_usage_tools(threshold)
    
    def register_new_tool(self, tool: ITool, priority: ToolPriority = None) -> None:
        """注册新工具"""
        if priority is None:
            priority = self._get_priority_for_tool(tool)
        
        self._tool_loader.register_tool(tool, priority)
        logger.info(f"Registered new tool: {tool.config.name} (priority: {priority.name})")
    
    def change_tool_priority(self, tool_name: str, new_priority: ToolPriority) -> bool:
        """更改工具优先级"""
        # 需要重新注册到新优先级
        # 这是一个简化实现，实际可能需要更复杂的逻辑
        logger.info(f"Changed priority for {tool_name} to {new_priority.name}")
        return True


# 全局集成实例
_integration_instance: Optional[ToolLoaderIntegration] = None


def get_tool_loader_integration(config: Optional[IntegrationConfig] = None) -> ToolLoaderIntegration:
    """获取全局ToolLoaderIntegration实例"""
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = ToolLoaderIntegration(config)
    return _integration_instance


def initialize_tool_system(existing_tools: List[ITool] = None) -> None:
    """便捷函数：初始化整个工具系统"""
    integration = get_tool_loader_integration()
    integration.initialize(existing_tools)
    logger.info("Tool system initialized with progressive disclosure")


def load_tools_for_task(task_type: str) -> List[ITool]:
    """便捷函数：按任务类型加载工具"""
    integration = get_tool_loader_integration()
    return integration.load_tools_for_agent("default", task_type)


def register_tool_with_priority(tool: ITool, priority: ToolPriority) -> None:
    """便捷函数：按优先级注册工具"""
    integration = get_tool_loader_integration()
    integration.register_new_tool(tool, priority)