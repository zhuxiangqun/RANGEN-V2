"""
渐进式披露工具加载器 - Progressive Disclosure Tool Loader

基于2026-03 Perplexity放弃MCP事件的深度分析：
- MCP有线性上下文成本问题
- CLI是更自然的执行层
- Skill封装是低成本方案
- 工具应该按需加载，而非全量注入

优先级：Skill > CLI > API > MCP
"""

import os
from typing import Dict, List, Optional, Set
from enum import Enum
from dataclasses import dataclass, field

from src.interfaces.tool import ITool, ToolCategory
from src.services.logging_service import get_logger

logger = get_logger(__name__)


class ToolPriority(Enum):
    """工具调用优先级（从高到低）"""
    SKILL = 1      # Skill: 知识/流程封装，零上下文成本
    CLI = 2        # CLI: 本地执行，LLM天然理解
    API = 3        # API: 程序化集成
    MCP = 4        # MCP: 复杂外部系统集成，有上下文成本


@dataclass
class ToolLoadConfig:
    """工具加载配置"""
    enable_skill: bool = True
    enable_cli: bool = True
    enable_api: bool = True
    enable_mcp: bool = False  # 默认关闭，需显式启用
    max_tools_per_priority: int = 20  # 每种优先级最大工具数


@dataclass
class ToolUsageStats:
    """工具使用统计"""
    tool_name: str
    priority: ToolPriority
    call_count: int = 0
    last_called: Optional[str] = None
    success_rate: float = 1.0


class ToolLoader:
    """
    渐进式披露工具加载器
    
    核心思想：根据任务类型按需加载工具，避免全量注入导致的上下文爆炸
    """
    
    def __init__(self, config: Optional[ToolLoadConfig] = None):
        self._config = config or ToolLoadConfig()
        self._priority_registry: Dict[ToolPriority, List[ITool]] = {
            ToolPriority.SKILL: [],
            ToolPriority.CLI: [],
            ToolPriority.API: [],
            ToolPriority.MCP: [],
        }
        self._usage_stats: Dict[str, ToolUsageStats] = {}
        self._initialized = False
        
    def register_tool(self, tool: ITool, priority: ToolPriority = ToolPriority.API) -> None:
        """注册工具到指定优先级"""
        if priority not in self._priority_registry:
            priority = ToolPriority.API
            
        self._priority_registry[priority].append(tool)
        
        # 初始化使用统计
        self._usage_stats[tool.config.name] = ToolUsageStats(
            tool_name=tool.config.name,
            priority=priority
        )
        logger.info(f"Registered tool: {tool.config.name} (priority: {priority.name})")
    
    def _should_load_priority(self, priority: ToolPriority) -> bool:
        """检查是否应该加载该优先级的工具"""
        config = self._config
        priority_checks = {
            ToolPriority.SKILL: config.enable_skill,
            ToolPriority.CLI: config.enable_cli,
            ToolPriority.API: config.enable_api,
            ToolPriority.MCP: config.enable_mcp,
        }
        return priority_checks.get(priority, False)
    
    def load_for_task(self, task_type: str) -> List[ITool]:
        """
        根据任务类型按需加载工具
        
        Args:
            task_type: 任务类型
                - "simple": 简单任务，仅加载Skill
                - "local": 本地操作，加载Skill+CLI
                - "api": API调用，加载Skill+CLI+API
                - "external": 外部系统，加载全部（包括MCP）
                - "default": 默认，加载Skill+CLI+API
        
        Returns:
            按优先级排序的工具列表
        """
        logger.info(f"Loading tools for task type: {task_type}")
        
        result: List[ITool] = []
        
        # 定义任务类型对应的优先级加载顺序
        task_priority_map = {
            "simple": [ToolPriority.SKILL],
            "local": [ToolPriority.SKILL, ToolPriority.CLI],
            "api": [ToolPriority.SKILL, ToolPriority.CLI, ToolPriority.API],
            "external": [ToolPriority.SKILL, ToolPriority.CLI, ToolPriority.API, ToolPriority.MCP],
            "default": [ToolPriority.SKILL, ToolPriority.CLI, ToolPriority.API],
        }
        
        priorities = task_priority_map.get(task_type, task_priority_map["default"])
        
        for priority in priorities:
            if not self._should_load_priority(priority):
                continue
                
            tools = self._priority_registry[priority]
            # 按热度排序，优先加载高频工具
            sorted_tools = self._sort_by_usage(tools)
            
            # 限制每种优先级的工具数量
            max_count = self._config.max_tools_per_priority
            result.extend(sorted_tools[:max_count])
            logger.debug(f"Loaded {len(sorted_tools[:max_count])} tools for priority {priority.name}")
        
        logger.info(f"Total tools loaded: {len(result)}")
        return result
    
    def _sort_by_usage(self, tools: List[ITool]) -> List[ITool]:
        """按使用频率排序"""
        return sorted(
            tools,
            key=lambda t: self._usage_stats.get(t.config.name, ToolUsageStats(
                tool_name=t.config.name,
                priority=ToolPriority.API
            )).call_count,
            reverse=True
        )
    
    def record_usage(self, tool_name: str, success: bool = True) -> None:
        """记录工具使用情况"""
        if tool_name in self._usage_stats:
            stats = self._usage_stats[tool_name]
            stats.call_count += 1
            if not success:
                # 更新成功率
                stats.success_rate = (
                    (stats.success_rate * (stats.call_count - 1) + 0) / stats.call_count
                )
            logger.debug(f"Recorded usage for {tool_name}: count={stats.call_count}, success_rate={stats.success_rate:.2f}")
    
    def get_usage_stats(self) -> List[ToolUsageStats]:
        """获取所有工具的使用统计"""
        return list(self._usage_stats.values())
    
    def get_low_usage_tools(self, threshold: int = 5) -> List[str]:
        """获取低频使用的工具（可用于清理）"""
        return [
            name for name, stats in self._usage_stats.items()
            if stats.call_count < threshold
        ]
    
    def get_tools_by_priority(self, priority: ToolPriority) -> List[ITool]:
        """获取指定优先级的所有工具"""
        return self._priority_registry.get(priority, [])


# 全局实例
_tool_loader_instance: Optional[ToolLoader] = None
_default_config = ToolLoadConfig()


def get_tool_loader(config: Optional[ToolLoadConfig] = None) -> ToolLoader:
    """获取全局ToolLoader实例"""
    global _tool_loader_instance
    if _tool_loader_instance is None:
        _tool_loader_instance = ToolLoader(config or _default_config)
    return _tool_loader_instance


def create_skill_tool(tool: ITool) -> None:
    """快捷方法：将工具注册为Skill优先级"""
    loader = get_tool_loader()
    loader.register_tool(tool, ToolPriority.SKILL)


def create_cli_tool(tool: ITool) -> None:
    """快捷方法：将工具注册为CLI优先级"""
    loader = get_tool_loader()
    loader.register_tool(tool, ToolPriority.CLI)


def create_mcp_tool(tool: ITool) -> None:
    """快捷方法：将工具注册为MCP优先级（需显式启用）"""
    loader = get_tool_loader()
    loader.register_tool(tool, ToolPriority.MCP)