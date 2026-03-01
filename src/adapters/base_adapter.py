#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移适配器基类

提供统一的适配器接口，用于实现Agent迁移的适配逻辑。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from dataclasses import asdict, is_dataclass
import json
import logging

logger = logging.getLogger(__name__)


class MigrationAdapter(ABC):
    """迁移适配器基类"""
    
    def __init__(self, source_agent_name: str, target_agent_name: str):
        """
        初始化适配器
        
        Args:
            source_agent_name: 源Agent名称
            target_agent_name: 目标Agent名称
        """
        self.source = source_agent_name
        self.target = target_agent_name
        self.migration_log: List[Dict[str, Any]] = []
        self.log_file = Path("logs") / f"migration_{source_agent_name}.log"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 延迟初始化目标Agent
        self._target_agent = None
    
    @property
    def target_agent(self):
        """获取目标Agent实例（延迟初始化）"""
        if self._target_agent is None:
            self._target_agent = self._initialize_target_agent()
        return self._target_agent
    
    @abstractmethod
    def _initialize_target_agent(self):
        """初始化目标Agent（子类实现）"""
        pass
    
    def adapt_context(self, old_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换上下文参数
        
        Args:
            old_context: 旧Agent的上下文参数
            
        Returns:
            转换后的上下文参数
        """
        adapted = old_context.copy()
        
        # 添加迁移标记
        adapted["_migrated_from"] = self.source
        adapted["_migration_timestamp"] = datetime.now().isoformat()
        
        return adapted
    
    def adapt_result(self, new_result: Any) -> Dict[str, Any]:
        """
        转换执行结果
        
        Args:
            new_result: 新Agent的执行结果（可能是AgentResult对象或字典）
            
        Returns:
            转换后的结果（保持与旧Agent结果格式兼容）
        """
        # 将AgentResult转换为字典
        if is_dataclass(new_result):
            adapted = asdict(new_result)
        elif isinstance(new_result, dict):
            adapted = new_result.copy()
        elif hasattr(new_result, '__dict__'):
            adapted = dict(new_result.__dict__)
        else:
            adapted = {"data": new_result}
        
        # 添加迁移标记
        adapted["_executed_by"] = self.target
        adapted["_migration_adapter"] = self.__class__.__name__
        
        return adapted
    
    def log_migration(self, details: Dict[str, Any]):
        """
        记录迁移日志
        
        Args:
            details: 日志详情
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "source": self.source,
            "target": self.target,
            **details
        }
        
        self.migration_log.append(log_entry)
        
        # 写入文件
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"写入迁移日志失败: {e}")
    
    async def execute_adapted(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行适配后的调用
        
        Args:
            context: 原始上下文
            
        Returns:
            适配后的执行结果
        """
        # 转换上下文
        adapted_context = self.adapt_context(context)
        
        # 记录调用
        self.log_migration({
            "action": "execute",
            "original_context_keys": list(context.keys()),
            "adapted_context_keys": list(adapted_context.keys())
        })
        
        try:
            # 执行目标Agent
            result = await self.target_agent.execute(adapted_context)
            
            # 转换结果
            adapted_result = self.adapt_result(result)
            
            # 记录成功
            self.log_migration({
                "action": "execute_success",
                "result_keys": list(adapted_result.keys())
            })
            
            return adapted_result
            
        except Exception as e:
            # 记录失败
            self.log_migration({
                "action": "execute_failure",
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise
    
    def get_migration_stats(self) -> Dict[str, Any]:
        """
        获取迁移统计信息
        
        Returns:
            统计信息字典
        """
        total_calls = len(self.migration_log)
        success_calls = sum(1 for log in self.migration_log 
                          if log.get("action") == "execute_success")
        failure_calls = sum(1 for log in self.migration_log 
                          if log.get("action") == "execute_failure")
        
        return {
            "source_agent": self.source,
            "target_agent": self.target,
            "total_calls": total_calls,
            "success_calls": success_calls,
            "failure_calls": failure_calls,
            "success_rate": success_calls / total_calls if total_calls > 0 else 0.0,
            "migration_log_file": str(self.log_file)
        }

