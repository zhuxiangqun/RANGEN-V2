#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逐步替换策略

实现Agent的逐步替换，通过逐步增加替换比例来降低风险。
"""

from typing import Dict, Any, Optional
from collections import defaultdict
from datetime import datetime
import random
import logging
from dataclasses import asdict, is_dataclass

logger = logging.getLogger(__name__)


class GradualReplacementStrategy:
    """逐步替换策略"""
    
    def __init__(self, old_agent, new_agent, adapter):
        """
        初始化逐步替换策略
        
        Args:
            old_agent: 旧Agent实例
            new_agent: 新Agent实例（通过适配器）
            adapter: 迁移适配器
        """
        self.old_agent = old_agent
        self.new_agent = new_agent
        self.adapter = adapter
        self.replacement_rate = 0.0  # 初始替换比例
        self.metrics = defaultdict(list)
        self.log_file = f"logs/replacement_progress_{old_agent.__class__.__name__}.log"
        
    async def execute_with_gradual_replacement(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行逐步替换
        
        Args:
            context: 执行上下文
            
        Returns:
            执行结果
        """
        # 根据替换比例决定使用哪个Agent
        use_new_agent = random.random() < self.replacement_rate
        
        if use_new_agent:
            # 使用新Agent（通过适配器）
            try:
                result = await self.adapter.execute_adapted(context)
                self._record_success("new_agent")
                # 将AgentResult转换为字典，添加元数据
                if is_dataclass(result):
                    result_dict = asdict(result)
                elif isinstance(result, dict):
                    result_dict = result.copy()
                elif hasattr(result, '__dict__'):
                    result_dict = dict(result.__dict__)
                else:
                    result_dict = {"data": result}
                result_dict["_executed_by"] = "new_agent"
                result_dict["_replacement_rate"] = self.replacement_rate
                return result_dict
            except Exception as e:
                # 新Agent失败，回退到旧Agent
                logger.warning(f"新Agent执行失败，回退到旧Agent: {e}")
                self._record_failure("new_agent", str(e))
                # 继续使用旧Agent
                pass
        
        # 使用旧Agent
        try:
            result = await self.old_agent.execute(context)
            self._record_success("old_agent")
            # 将AgentResult转换为字典，添加元数据
            if is_dataclass(result):
                result_dict = asdict(result)
            elif isinstance(result, dict):
                result_dict = result.copy()
            elif hasattr(result, '__dict__'):
                result_dict = dict(result.__dict__)
            else:
                result_dict = {"data": result}
            result_dict["_executed_by"] = "old_agent"
            result_dict["_replacement_rate"] = self.replacement_rate
            return result_dict
        except Exception as e:
            self._record_failure("old_agent", str(e))
            raise
    
    def increase_replacement_rate(self, step: float = 0.1) -> float:
        """
        逐步增加替换比例
        
        Args:
            step: 增加的步长（默认0.1，即10%）
            
        Returns:
            新的替换比例
        """
        new_rate = min(1.0, self.replacement_rate + step)
        
        if new_rate > self.replacement_rate:
            old_rate = self.replacement_rate
            self.replacement_rate = new_rate
            
            logger.info(
                f"🔄 {self.old_agent.__class__.__name__} -> "
                f"{self.new_agent.__class__.__name__}: "
                f"替换比例从 {old_rate:.0%} 提升到 {new_rate:.0%}"
            )
            
            # 记录调整日志
            self._log_rate_change(old_rate, new_rate)
        
        return self.replacement_rate
    
    def _log_rate_change(self, old_rate: float, new_rate: float):
        """记录替换比例变化"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "old_agent": self.old_agent.__class__.__name__,
            "new_agent": self.new_agent.__class__.__name__,
            "old_rate": old_rate,
            "new_rate": new_rate,
            "success_rate": self._calculate_success_rate("new_agent")
        }
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                import json
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"写入替换日志失败: {e}")
    
    def should_increase_rate(self) -> bool:
        """
        判断是否应该增加替换比例
        
        Returns:
            是否应该增加
        """
        if self.replacement_rate >= 1.0:
            return False
        
        # 基于成功率判断
        success_rate = self._calculate_success_rate("new_agent")
        
        # 如果成功率≥95%且至少有100次调用，可以增加
        if len(self.metrics["new_agent_success"]) >= 100:
            return success_rate >= 0.95
        
        return False
    
    def should_complete_replacement(self) -> bool:
        """
        判断是否应该完成替换
        
        Returns:
            是否应该完成替换
        """
        # 替换比例必须达到100%
        if self.replacement_rate < 1.0:
            return False
        
        # 成功率必须≥95%
        success_rate = self._calculate_success_rate("new_agent")
        if success_rate < 0.95:
            return False
        
        # 必须有足够的样本
        total_calls = (
            len(self.metrics["new_agent_success"]) +
            len(self.metrics["new_agent_failure"])
        )
        if total_calls < 1000:
            return False
        
        return True
    
    def _record_success(self, agent_type: str):
        """记录成功调用"""
        self.metrics[f"{agent_type}_success"].append(datetime.now())
    
    def _record_failure(self, agent_type: str, error: str):
        """记录失败调用"""
        self.metrics[f"{agent_type}_failure"].append({
            "timestamp": datetime.now(),
            "error": error
        })
    
    def _calculate_success_rate(self, agent_type: str) -> float:
        """计算成功率"""
        successes = len(self.metrics[f"{agent_type}_success"])
        failures = len(self.metrics[f"{agent_type}_failure"])
        total = successes + failures
        
        if total == 0:
            return 0.0
        
        return successes / total
    
    def get_replacement_stats(self) -> Dict[str, Any]:
        """
        获取替换统计信息
        
        Returns:
            统计信息字典
        """
        new_success_rate = self._calculate_success_rate("new_agent")
        old_success_rate = self._calculate_success_rate("old_agent")
        
        return {
            "old_agent": self.old_agent.__class__.__name__,
            "new_agent": self.new_agent.__class__.__name__,
            "replacement_rate": self.replacement_rate,
            "new_agent_success_rate": new_success_rate,
            "old_agent_success_rate": old_success_rate,
            "new_agent_total_calls": (
                len(self.metrics["new_agent_success"]) +
                len(self.metrics["new_agent_failure"])
            ),
            "old_agent_total_calls": (
                len(self.metrics["old_agent_success"]) +
                len(self.metrics["old_agent_failure"])
            ),
            "should_increase_rate": self.should_increase_rate(),
            "should_complete": self.should_complete_replacement()
        }

