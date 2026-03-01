#!/usr/bin/env python3
"""
Dynamic State Machine
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple

logger = logging.getLogger(__name__)


class DynamicStateMachine:
    """动态状态机类"""
    
    def __init__(self) -> None:
        """初始化"""
        self.states = {}
        self.current_state = None
        self.transitions = {}
        self.initialized = True
        logger.info("动态状态机初始化完成")
    
    def add_state(self, state_name: str, state_data: Any = None) -> bool:
        """添加状态"""
        try:
            # 验证状态名称
            if not self._validate_state_name(state_name):
                return False
            
            # 检查状态是否已存在
            if state_name in self.states:
                logger.warning(f"状态已存在: {state_name}")
                return False
            
            # 添加状态
            self.states[state_name] = {
                'data': state_data,
                'created_at': time.time(),
                'transitions': [],
                'metadata': {}
            }
            
            # 记录状态添加历史
            self._record_state_addition(state_name, state_data)
            
            logger.debug(f"添加状态: {state_name}")
            return True
            
        except Exception as e:
            logger.error(f"添加状态失败: {e}")
            return False
    
    def _validate_state_name(self, state_name: str) -> bool:
        """验证状态名称"""
        return isinstance(state_name, str) and len(state_name.strip()) > 0
    
    def _record_state_addition(self, state_name: str, state_data: Any):
        """记录状态添加历史"""
        if not hasattr(self, 'state_history'):
            self.state_history = []
        
        self.state_history.append({
            'action': 'add_state',
            'state_name': state_name,
            'state_data': state_data,
            'timestamp': time.time()
        })
    
    def set_current_state(self, state_name: str) -> bool:
        """设置当前状态"""
        try:
            # 验证状态名称
            if not self._validate_state_name(state_name):
                return False
            
            # 检查状态是否存在
            if state_name not in self.states:
                logger.warning(f"状态不存在: {state_name}")
                return False
            
            # 检查状态转换是否有效
            if not self._validate_state_transition(self.current_state, state_name):
                logger.warning(f"无效的状态转换: {self.current_state} -> {state_name}")
                return False
            
            # 记录状态转换
            previous_state = self.current_state
            self.current_state = state_name
            
            # 记录状态转换历史
            self._record_state_transition(previous_state, state_name)
            
            logger.debug(f"当前状态设置为: {state_name}")
            return True
            
        except Exception as e:
            logger.error(f"设置状态失败: {e}")
            return False
    
    def _validate_state_transition(self, from_state: str, to_state: str) -> bool:
        """验证状态转换"""
        if from_state is None:
            return True  # 初始状态转换总是有效的
        
        if from_state not in self.states:
            return False
        
        # 检查是否有有效的转换
        state_info = self.states[from_state]
        if 'transitions' in state_info:
            return to_state in state_info['transitions']
        
        return True  # 如果没有限制，允许转换
    
    def _record_state_transition(self, from_state: str, to_state: str):
        """记录状态转换历史"""
        if not hasattr(self, 'transition_history'):
            self.transition_history = []
        
        self.transition_history.append({
            'from_state': from_state,
            'to_state': to_state,
            'timestamp': time.time()
        })
    
    def add_transition(self, from_state: str, to_state: str, condition: str = None) -> bool:
        """添加状态转换"""
        try:
            if from_state not in self.transitions:
                self.transitions[from_state] = []
            self.transitions[from_state].append({
                'to': to_state,
                'condition': condition
            })
            logger.debug(f"添加转换: {from_state} -> {to_state}")
            return True
        except Exception as e:
            logger.error(f"添加转换失败: {e}")
            return False
    
    def can_transition(self, to_state: str) -> bool:
        """检查是否可以转换到指定状态"""
        try:
            if not self.current_state:
                return False
            
            if self.current_state not in self.transitions:
                return False
            
            for transition in self.transitions[self.current_state]:
                if transition['to'] == to_state:
                    return True
            
            return False
        except Exception as e:
            logger.error(f"检查转换条件失败: {e}")
            return False
    
    def transition_to(self, to_state: str) -> bool:
        """转换到指定状态"""
        try:
            if self.can_transition(to_state):
                self.current_state = to_state
                logger.info(f"状态转换成功: {self.current_state}")
                return True
            else:
                logger.warning(f"无法转换到状态: {to_state}")
                return False
        except Exception as e:
            logger.error(f"状态转换失败: {e}")
            return False
    
    def get_current_state(self) -> Optional[str]:
        """获取当前状态"""
        return self.current_state
    
    def get_state_data(self, state_name: str) -> Any:
        """获取状态数据"""
        return self.states.get(state_name)
    
    def process_data(self, data: Any) -> Any:
        """处理数据"""
        try:
            if self.current_state:
                logger.debug(f"在状态 {self.current_state} 处理数据")
                return data
            else:
                logger.warning("没有设置当前状态")
                return None
        except Exception as e:
            logger.error(f"处理数据失败: {e}")
            return None
    
    def validate(self, data: Any) -> bool:
        """验证数据"""
        try:
            if data is None:
                return False
            
            # 基本验证逻辑
            if isinstance(data, (str, int, float, bool)):
                return True
            
            if isinstance(data, (list, dict)):
                return len(data) > 0
            
            return True
        except Exception as e:
            logger.error(f"数据验证失败: {e}")
            return False


# 便捷函数
def get_dynamic_state_machine() -> DynamicStateMachine:
    """获取动态状态机实例"""
    return DynamicStateMachine()
