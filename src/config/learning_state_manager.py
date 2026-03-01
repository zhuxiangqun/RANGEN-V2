#!/usr/bin/env python3
"""
学习状态管理器
负责保存和恢复动态调整的学习参数
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class LearningStateManager:
    """学习状态管理器 - 负责学习参数的持久化"""
    
    def __init__(self, state_file: str = "learning_state.json"):
        self.state_file = Path(state_file)
        self.learning_state = {}
        self.logger = logging.getLogger(__name__)
        self._load_state()
    
    def _load_state(self):
        """加载学习状态"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    self.learning_state = json.load(f)
                self.logger.info(f"学习状态已加载: {self.state_file}")
            else:
                self.learning_state = self._get_default_state()
                self.logger.info("使用默认学习状态")
        except Exception as e:
            self.logger.error(f"加载学习状态失败: {e}")
            self.learning_state = self._get_default_state()
    
    def _get_default_state(self) -> Dict[str, Any]:
        """获取默认学习状态"""
        return {
            "learning_rate": {
                "current_value": 0.001,  # 从环境变量获取的初始值
                "min_value": 0.001,
                "max_value": 0.1,
                "adjustment_history": [],
                "last_adjustment": None,
                "performance_trend": "stable"
            },
            "batch_size": {
                "current_value": 32,
                "min_value": 8,
                "max_value": 128,
                "adjustment_history": [],
                "last_adjustment": None
            },
            "exploration_rate": {
                "current_value": 0.1,
                "min_value": 0.01,
                "max_value": 0.3,
                "adjustment_history": [],
                "last_adjustment": None
            },
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "version": "1.0.0"
            }
        }
    
    def get_learning_rate(self, default_value: float = 0.001) -> float:
        """获取当前学习率"""
        return self.learning_state.get("learning_rate", {}).get("current_value", default_value)
    
    def update_learning_rate(self, new_rate: float, reason: str = "dynamic_adjustment", 
                            performance_metrics: Optional[Dict[str, Any]] = None):
        """更新学习率并保存"""
        try:
            learning_rate_state = self.learning_state.get("learning_rate", {})
            old_rate = learning_rate_state.get("current_value", 0.001)
            
            # 记录调整历史
            adjustment_record = {
                "timestamp": datetime.now().isoformat(),
                "old_value": old_rate,
                "new_value": new_rate,
                "reason": reason,
                "performance_metrics": performance_metrics or {}
            }
            
            # 更新状态
            learning_rate_state["current_value"] = new_rate
            learning_rate_state["last_adjustment"] = adjustment_record
            learning_rate_state["adjustment_history"].append(adjustment_record)
            
            # 保持历史记录在合理范围内
            if len(learning_rate_state["adjustment_history"]) > 100:
                learning_rate_state["adjustment_history"] = learning_rate_state["adjustment_history"][-50:]
            
            # 更新元数据
            self.learning_state["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # 保存状态
            self._save_state()
            
            self.logger.info(f"学习率已更新: {old_rate} -> {new_rate} (原因: {reason})")
            
        except Exception as e:
            self.logger.error(f"更新学习率失败: {e}")
    
    def get_batch_size(self, default_value: int = 32) -> int:
        """获取当前批次大小"""
        return self.learning_state.get("batch_size", {}).get("current_value", default_value)
    
    def update_batch_size(self, new_size: int, reason: str = "dynamic_adjustment"):
        """更新批次大小并保存"""
        try:
            batch_size_state = self.learning_state.get("batch_size", {})
            old_size = batch_size_state.get("current_value", 32)
            
            adjustment_record = {
                "timestamp": datetime.now().isoformat(),
                "old_value": old_size,
                "new_value": new_size,
                "reason": reason
            }
            
            batch_size_state["current_value"] = new_size
            batch_size_state["last_adjustment"] = adjustment_record
            batch_size_state["adjustment_history"].append(adjustment_record)
            
            # 保持历史记录在合理范围内
            if len(batch_size_state["adjustment_history"]) > 100:
                batch_size_state["adjustment_history"] = batch_size_state["adjustment_history"][-50:]
            
            self.learning_state["metadata"]["last_updated"] = datetime.now().isoformat()
            self._save_state()
            
            self.logger.info(f"批次大小已更新: {old_size} -> {new_size} (原因: {reason})")
            
        except Exception as e:
            self.logger.error(f"更新批次大小失败: {e}")
    
    def get_adjustment_history(self, parameter: str = "learning_rate") -> list:
        """获取参数调整历史"""
        return self.learning_state.get(parameter, {}).get("adjustment_history", [])
    
    def get_last_adjustment(self, parameter: str = "learning_rate") -> Optional[Dict[str, Any]]:
        """获取最后一次调整记录"""
        return self.learning_state.get(parameter, {}).get("last_adjustment")
    
    def _save_state(self):
        """保存学习状态到文件"""
        try:
            # 确保目录存在
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存到文件
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.learning_state, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"学习状态已保存: {self.state_file}")
            
        except Exception as e:
            self.logger.error(f"保存学习状态失败: {e}")
    
    def reset_to_defaults(self):
        """重置为默认值"""
        self.learning_state = self._get_default_state()
        self._save_state()
        self.logger.info("学习状态已重置为默认值")
    
    def get_state_summary(self) -> Dict[str, Any]:
        """获取状态摘要"""
        return {
            "learning_rate": self.get_learning_rate(),
            "batch_size": self.get_batch_size(),
            "last_updated": self.learning_state.get("metadata", {}).get("last_updated"),
            "adjustment_count": {
                "learning_rate": len(self.get_adjustment_history("learning_rate")),
                "batch_size": len(self.get_adjustment_history("batch_size"))
            }
        }


# 全局实例
_learning_state_manager = None

def get_learning_state_manager() -> LearningStateManager:
    """获取学习状态管理器实例"""
    global _learning_state_manager
    if _learning_state_manager is None:
        _learning_state_manager = LearningStateManager()
    return _learning_state_manager

# 便捷函数
def get_current_learning_rate(default_value: float = 0.001) -> float:
    """获取当前学习率（优先使用持久化的值）"""
    return get_learning_state_manager().get_learning_rate(default_value)

def update_learning_rate(new_rate: float, reason: str = "dynamic_adjustment", 
                        performance_metrics: Optional[Dict[str, Any]] = None):
    """更新学习率"""
    get_learning_state_manager().update_learning_rate(new_rate, reason, performance_metrics)

def get_current_batch_size(default_value: int = 32) -> int:
    """获取当前批次大小（优先使用持久化的值）"""
    return get_learning_state_manager().get_batch_size(default_value)

def update_batch_size(new_size: int, reason: str = "dynamic_adjustment"):
    """更新批次大小"""
    get_learning_state_manager().update_batch_size(new_size, reason)
