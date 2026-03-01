"""
状态管理优化模块 - 阶段5.3
减少不必要的状态更新，优化状态更新逻辑
"""
import logging
import time
from typing import Dict, Any, Optional, Set, List
from copy import deepcopy

logger = logging.getLogger(__name__)


class StateOptimizer:
    """状态优化器 - 阶段5.3"""
    
    def __init__(self):
        """初始化状态优化器"""
        self.logger = logging.getLogger(__name__)
        self.state_update_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        
        # 定义只读字段（不应该被更新）
        self.readonly_fields: Set[str] = {
            'query',  # 查询不应该被修改
            'user_id',  # 用户ID不应该被修改
            'session_id',  # 会话ID不应该被修改
        }
        
        # 定义需要深度比较的字段（避免不必要的更新）
        self.deep_compare_fields: Set[str] = {
            'context',
            'metadata',
            'knowledge',
            'evidence',
            'citations',
            'reasoning_steps',
            'agent_thoughts',
            'agent_actions',
            'agent_observations'
        }
    
    def should_update_field(self, field_name: str, old_value: Any, new_value: Any) -> bool:
        """判断是否应该更新字段
        
        Args:
            field_name: 字段名称
            old_value: 旧值
            new_value: 新值
        
        Returns:
            是否应该更新
        """
        # 只读字段不应该被更新
        if field_name in self.readonly_fields:
            if old_value != new_value:
                self.logger.warning(f"⚠️ [State Optimizer] 尝试更新只读字段: {field_name}")
            return False
        
        # 如果值相同，不需要更新
        if old_value == new_value:
            return False
        
        # 对于需要深度比较的字段，进行深度比较
        if field_name in self.deep_compare_fields:
            if self._deep_equal(old_value, new_value):
                return False
        
        return True
    
    def _deep_equal(self, obj1: Any, obj2: Any) -> bool:
        """深度比较两个对象是否相等"""
        try:
            if type(obj1) != type(obj2):
                return False
            
            if isinstance(obj1, dict):
                if set(obj1.keys()) != set(obj2.keys()):
                    return False
                return all(self._deep_equal(obj1[k], obj2[k]) for k in obj1.keys())
            
            elif isinstance(obj1, list):
                if len(obj1) != len(obj2):
                    return False
                return all(self._deep_equal(obj1[i], obj2[i]) for i in range(len(obj1)))
            
            else:
                return obj1 == obj2
        except Exception:
            # 如果比较失败，假设不相等（安全起见）
            return False
    
    def optimize_state_update(
        self,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any],
        node_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """优化状态更新 - 只更新实际变化的字段
        
        Args:
            old_state: 旧状态
            new_state: 新状态
            node_name: 节点名称（可选）
        
        Returns:
            优化后的状态
        """
        optimized_state = old_state.copy()
        updated_fields = []
        skipped_fields = []
        
        for field_name, new_value in new_state.items():
            old_value = old_state.get(field_name)
            
            if self.should_update_field(field_name, old_value, new_value):
                optimized_state[field_name] = new_value
                updated_fields.append(field_name)
            else:
                skipped_fields.append(field_name)
        
        # 记录更新历史
        if updated_fields or skipped_fields:
            self._record_update(node_name, updated_fields, skipped_fields)
        
        return optimized_state
    
    def _record_update(self, node_name: Optional[str], updated_fields: List[str], skipped_fields: List[str]) -> None:
        """记录状态更新历史"""
        update_record = {
            'node_name': node_name,
            'updated_fields': updated_fields,
            'skipped_fields': skipped_fields,
            'timestamp': time.time()
        }
        
        self.state_update_history.append(update_record)
        
        # 限制历史大小
        if len(self.state_update_history) > self.max_history_size:
            self.state_update_history = self.state_update_history[-self.max_history_size:]
    
    def get_update_statistics(self) -> Dict[str, Any]:
        """获取状态更新统计信息"""
        if not self.state_update_history:
            return {
                'total_updates': 0,
                'total_updated_fields': 0,
                'total_skipped_fields': 0,
                'field_update_counts': {},
                'field_skip_counts': {}
            }
        
        total_updated = 0
        total_skipped = 0
        field_update_counts = {}
        field_skip_counts = {}
        
        for record in self.state_update_history:
            total_updated += len(record['updated_fields'])
            total_skipped += len(record['skipped_fields'])
            
            for field in record['updated_fields']:
                field_update_counts[field] = field_update_counts.get(field, 0) + 1
            
            for field in record['skipped_fields']:
                field_skip_counts[field] = field_skip_counts.get(field, 0) + 1
        
        return {
            'total_updates': len(self.state_update_history),
            'total_updated_fields': total_updated,
            'total_skipped_fields': total_skipped,
            'field_update_counts': field_update_counts,
            'field_skip_counts': field_skip_counts,
            'optimization_rate': total_skipped / (total_updated + total_skipped) if (total_updated + total_skipped) > 0 else 0.0
        }
    
    def merge_state_updates(
        self,
        base_state: Dict[str, Any],
        updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """合并多个状态更新 - 批量优化
        
        Args:
            base_state: 基础状态
            updates: 更新列表
        
        Returns:
            合并后的状态
        """
        merged_state = base_state.copy()
        
        for update in updates:
            merged_state = self.optimize_state_update(merged_state, update)
        
        return merged_state
    
    def create_state_snapshot(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """创建状态快照（用于检查点）
        
        Args:
            state: 状态字典
        
        Returns:
            状态快照（深拷贝）
        """
        return deepcopy(state)
    
    def restore_state_snapshot(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """恢复状态快照
        
        Args:
            snapshot: 状态快照
        
        Returns:
            恢复后的状态
        """
        return deepcopy(snapshot)


# 全局状态优化器实例
_state_optimizer = None


def get_state_optimizer() -> StateOptimizer:
    """获取全局状态优化器实例"""
    global _state_optimizer
    if _state_optimizer is None:
        _state_optimizer = StateOptimizer()
    return _state_optimizer


def optimize_node_state_update(
    old_state: Dict[str, Any],
    new_state: Dict[str, Any],
    node_name: Optional[str] = None
) -> Dict[str, Any]:
    """优化节点状态更新（便捷函数）
    
    Args:
        old_state: 旧状态
        new_state: 新状态
        node_name: 节点名称（可选）
    
    Returns:
        优化后的状态
    """
    optimizer = get_state_optimizer()
    return optimizer.optimize_state_update(old_state, new_state, node_name)

