#!/usr/bin/env python3
"""
业务层 - 命令模式实现
Business Command Pattern Implementations

提供业务命令基类、命令处理器、具体命令实现
"""
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from src.core.services import get_core_logger


class BusinessCommand(ABC):
    """业务命令基类"""
    
    @abstractmethod
    def execute(self) -> Any:
        """执行命令"""
        try:
            # 执行具体的业务命令
            result = self._do_execute()
            
            # 记录执行历史
            if not hasattr(self, 'execution_history'):
                self.execution_history = []
            
            self.execution_history.append({
                'timestamp': time.time(),
                'command': self.__class__.__name__,
                'result': result,
                'success': True
            })
            
            return result
        except Exception as e:
            # 记录错误
            if not hasattr(self, 'execution_history'):
                self.execution_history = []
            
            self.execution_history.append({
                'timestamp': time.time(),
                'command': self.__class__.__name__,
                'error': str(e),
                'success': False
            })
            raise e
    
    def _do_execute(self) -> Any:
        """具体的执行逻辑，由子类实现"""
        return None
    
    @abstractmethod
    def undo(self) -> Any:
        """撤销命令"""
        try:
            # 执行撤销操作
            result = self._do_undo()
            
            # 记录撤销历史
            if not hasattr(self, 'undo_history'):
                self.undo_history = []
            
            self.undo_history.append({
                'timestamp': time.time(),
                'command': self.__class__.__name__,
                'result': result,
                'success': True
            })
            
            return result
        except Exception as e:
            # 记录撤销错误
            if not hasattr(self, 'undo_history'):
                self.undo_history = []
            
            self.undo_history.append({
                'timestamp': time.time(),
                'command': self.__class__.__name__,
                'error': str(e),
                'success': False
            })
            raise e
    
    def _do_undo(self) -> Any:
        """具体的撤销逻辑，由子类实现"""
        return None


class BusinessCommandProcessor:
    """业务命令处理器"""
    
    def __init__(self):
        self.command_history: List[BusinessCommand] = []
        self.undo_stack: List[BusinessCommand] = []
        self.logger = get_core_logger("business_command_processor")
    
    def execute_command(self, command: BusinessCommand) -> Any:
        """执行命令"""
        try:
            result = command.execute()
            self.command_history.append(command)
            self.undo_stack.append(command)
            self.logger.info(f"命令执行成功: {command.__class__.__name__}")
            return result
        except Exception as e:
            self.logger.error(f"命令执行失败: {e}")
            raise
    
    def undo_last_command(self) -> Any:
        """撤销上一个命令"""
        if not self.undo_stack:
            self.logger.warning("没有可撤销的命令")
            return None
        
        command = self.undo_stack.pop()
        try:
            result = command.undo()
            self.logger.info(f"命令撤销成功: {command.__class__.__name__}")
            return result
        except Exception as e:
            self.logger.error(f"命令撤销失败: {e}")
            raise
    
    def get_command_history(self) -> List[Dict[str, Any]]:
        """获取命令历史"""
        history = []
        for cmd in self.command_history:
            if hasattr(cmd, 'execution_history') and cmd.execution_history:
                history.append(cmd.execution_history[-1])
        return history
    
    def clear_history(self):
        """清空命令历史"""
        self.command_history.clear()
        self.undo_stack.clear()
        self.logger.info("命令历史已清空")
