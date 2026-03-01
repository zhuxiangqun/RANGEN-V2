#!/usr/bin/env python3
"""
工具基类
定义所有工具的统一接口
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from src.utils.logging_helper import get_module_logger, ModuleType
from src.visualization.orchestration_tracker import get_orchestration_tracker

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class BaseTool(ABC):
    """工具基类 - 所有工具必须继承此类"""
    
    def __init__(self, tool_name: str, description: str = ""):
        """
        初始化工具
        
        Args:
            tool_name: 工具名称
            description: 工具描述
        """
        self.tool_name = tool_name
        self.description = description
        # 使用模块日志器
        self.logger = logging.getLogger(f"{__name__}.{tool_name}")
        self.module_logger = get_module_logger(ModuleType.TOOL, tool_name)
        self._call_count = 0
        self._success_count = 0
        self._error_count = 0
    
    async def _call_with_tracking(self, call_func, **kwargs) -> ToolResult:
        """
        带追踪的工具调用包装器（辅助方法）
        
        子类可以在自己的 call 方法中使用此方法来添加追踪功能：
        
        async def call(self, **kwargs) -> ToolResult:
            async def _actual_call(**kwargs):
                # 实际的工具逻辑
                return ToolResult(...)
            return await self._call_with_tracking(_actual_call, **kwargs)
        
        Args:
            call_func: 实际的工具调用函数（async）
            **kwargs: 工具参数
            
        Returns:
            ToolResult: 工具执行结果
        """
        # 🚀 编排追踪：追踪工具调用
        tracker = getattr(self, '_orchestration_tracker', None) or get_orchestration_tracker()
        tool_event_id = None
        
        if tracker:
            try:
                tool_event_id = tracker.track_tool_start(
                    tool_name=self.tool_name,
                    params=kwargs
                )
            except Exception as e:
                logger.debug(f"追踪工具开始失败（可忽略）: {e}")
        
        try:
            # 调用实际的工具实现
            result = await call_func(**kwargs)
            
            # 记录调用统计
            if isinstance(result, ToolResult):
                self._record_call(result.success)
                
                # 🚀 编排追踪：追踪工具调用结束
                if tracker and tool_event_id:
                    try:
                        result_dict = result.data if result.success else None
                        tracker.track_tool_end(
                            tool_name=self.tool_name,
                            result=result_dict if isinstance(result_dict, dict) else {"data": result_dict} if result_dict else None,
                            error=result.error if not result.success else None
                        )
                    except Exception as e:
                        logger.debug(f"追踪工具结束失败（可忽略）: {e}")
            
            return result
            
        except Exception as e:
            # 记录错误
            self._record_call(False)
            
            # 🚀 编排追踪：追踪工具调用错误
            if tracker and tool_event_id:
                try:
                    tracker.track_tool_end(
                        tool_name=self.tool_name,
                        result=None,
                        error=str(e)
                    )
                except Exception:
                    pass
            
            # 返回错误结果
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                execution_time=0.0
            )
    
    @abstractmethod
    async def call(self, **kwargs) -> ToolResult:
        """
        调用工具 - 子类必须实现此方法
        
        建议：子类可以在实现中使用 _call_with_tracking 来添加追踪功能
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            ToolResult: 工具执行结果
        """
        pass
    
    def get_tool_info(self) -> Dict[str, Any]:
        """
        获取工具信息
        
        Returns:
            Dict: 工具信息，包括名称、描述、参数等
        """
        return {
            "name": self.tool_name,
            "description": self.description,
            "parameters": self.get_parameters_schema(),
            "statistics": {
                "call_count": self._call_count,
                "success_count": self._success_count,
                "error_count": self._error_count,
                "success_rate": self._success_count / self._call_count if self._call_count > 0 else 0.0
            }
        }
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """
        获取工具参数模式 - 子类可以重写此方法
        
        Returns:
            Dict: 参数模式，描述工具需要的参数
        """
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    def _record_call(self, success: bool):
        """记录工具调用"""
        self._call_count += 1
        if success:
            self._success_count += 1
        else:
            self._error_count += 1
    
    def __str__(self) -> str:
        return f"{self.tool_name}: {self.description}"

