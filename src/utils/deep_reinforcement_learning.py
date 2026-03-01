#!/usr/bin/env python3
"""
深度强化学习模块 - 实现Q-Learning和策略梯度算法
"""

import logging
import numpy as np
import json
import time
import random
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque

# 类型定义
State = Dict[str, Any]
Action = Dict[str, Any]
RewardType = float

logger = logging.getLogger(__name__)

@dataclass
class WorkflowState:
    """状态数据类"""
    state_id: str
    features: List[float]
    metadata: Dict[str, Any]

@dataclass
class Component:
    """动作数据类"""
    action_id: str
    action_type: str
    parameters: Dict[str, Any]
    metadata: Dict[str, Any]

@dataclass
class Reward:
    """奖励数据类"""
    reward_value: float
    reward_type: str
    timestamp: float
    metadata: Dict[str, Any]

@dataclass
class Episode:
    """回合数据类"""
    episode_id: str
    states: List[State]
    actions: List[Action]
    rewards: List[RewardType]
    total_reward: float
    metadata: Dict[str, Any]

class DeepReinforcementLearning:
    """深度强化学习模块"""
    
    def __init__(self, state_size: int, action_size: int, learning_rate: float = 0.01,
                 discount_factor: float = 0.95, epsilon: float = 1.0, 
                 epsilon_decay: float = 0.995, epsilon_min: float = 0.01):
        """初始化强化学习模块"""
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        
        # Q表
        self.q_table = defaultdict(lambda: np.zeros(action_size))
        self.replay_buffer = deque(maxlen=1000)
        self.episode_rewards = []
        
        # 训练历史
        self.training_history = []
        
        # 策略网络参数
        self.policy_weights = np.random.randn(state_size, action_size) * 0.1
        
        self.initialized = True
        logger.info("深度强化学习模块初始化完成")
    
    def select_action(self, state: State, use_exploration: bool = True) -> Action:
        """选择动作"""
        try:
            # 验证输入
            if not self._validate_state(state):
                return self._create_default_action()
            
            state_key = self._state_to_key(state)
            
            # 确保状态在Q表中
            if state_key not in self.q_table:
                self.q_table[state_key] = np.zeros(self.action_size)
            
            if use_exploration and random.random() < self.epsilon:
                # 探索：随机选择动作
                action_id = random.randint(0, self.action_size - 1)
            else:
                # 利用：选择Q值最高的动作
                q_values = self.q_table[state_key]
                action_id = np.argmax(q_values)
            
            action = {
                "action_id": f"action_{int(action_id)}",
                "action_type": self._get_action_type(int(action_id)),
                "parameters": self._get_action_parameters(int(action_id)),
                "metadata": {
                    "state_key": state_key, 
                    "q_value": float(self.q_table[state_key][int(action_id)]),
                    "exploration": use_exploration and random.random() < self.epsilon
                }
            }
            
            # 记录动作选择
            self._record_action_selection(state, action)
            
            return action
            
        except Exception as e:
            logger.error(f"动作选择失败: {e}")
            return self._create_default_action()
    
    def _validate_state(self, state: State) -> bool:
        """验证状态"""
        if not isinstance(state, dict):
            return False
        
        # 检查必要的状态字段
        required_fields = ['observation', 'reward', 'done']
        for field in required_fields:
            if field not in state:
                return False
        
        return True
    
    def _create_default_action(self) -> Action:
        """创建默认动作"""
        return {
            "action_id": "action_0",
            "action_type": "default",
            "parameters": {},
            "metadata": {"error": True, "default": True}
        }
    
    def _record_action_selection(self, state: State, action: Action):
        """记录动作选择"""
        try:
            self.action_history.append({
                'timestamp': time.time(),
                'state': state,
                'action': action,
                'epsilon': self.epsilon
            })
            
            # 保持历史记录在合理范围内
            if len(self.action_history) > 10000:
                self.action_history = self.action_history[-10000:]
                
        except Exception as e:
            logger.warning(f"记录动作选择失败: {e}")
    
    def update_q_table(self, state: State, action: Action, reward: RewardType, next_state: State):
        """更新Q表"""
        state_key = self._state_to_key(state)
        next_state_key = self._state_to_key(next_state)
        action_id = int(action.get("action_id", "action_0").split("_")[1])
        
        # Q-Learning更新规则
        current_q = self.q_table[state_key][action_id]
        max_next_q = np.max(self.q_table[next_state_key])
        
        # 计算目标Q值
        target_q = float(reward) + self.discount_factor * max_next_q
        
        # 更新Q值
        self.q_table[state_key][action_id] = current_q + self.learning_rate * (target_q - current_q)
        
        # 衰减epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def train_episode(self, episode: Episode) -> Dict[str, Any]:
        """训练一个回合"""
        episode_reward = 0
        training_steps = []
        
        for i in range(len(episode.states) - 1):
            state = episode.states[i]
            action = episode.actions[i]
            reward = episode.rewards[i]
            next_state = episode.states[i + 1]
            
            # 更新Q表
            self.update_q_table(state, action, reward, next_state)
            
            # 记录训练步骤
            training_steps.append({
                "step": i,
                "state_key": self._state_to_key(state),
                "action_id": action.get("action_id", "unknown"),
                "reward": float(reward),
                "q_value": self.q_table[self._state_to_key(state)][int(action.get("action_id", "action_0").split("_")[1])]
            })
            
            episode_reward += float(reward)
        
        # 记录回合信息
        episode_info = {
            "episode_id": episode.episode_id,
            "total_reward": episode_reward,
            "steps": len(training_steps),
            "epsilon": self.epsilon,
            "training_steps": training_steps
        }
        
        self.training_history.append(episode_info)
        self.episode_rewards.append(episode_reward)
        
        return episode_info
    
    def get_policy(self, state: State) -> Dict[str, Any]:
        """获取策略"""
        state_key = self._state_to_key(state)
        q_values = self.q_table[state_key]
        
        # 计算动作概率（使用softmax）
        exp_q = np.exp(q_values - np.max(q_values))
        action_probs = exp_q / np.sum(exp_q)
        
        policy = {}
        for i, prob in enumerate(action_probs):
            policy[f"action_{i}"] = {
                "probability": float(prob),
                "q_value": float(q_values[i]),
                "action_type": self._get_action_type(i)
            }
        
        return {
            "state_key": state_key,
            "policy": policy,
            "best_action": f"action_{np.argmax(q_values)}",
            "confidence": float(np.max(action_probs))
        }
    
    def evaluate_performance(self) -> Dict[str, Any]:
        """评估性能"""
        if not self.episode_rewards:
            return {"error": "No training data available"}
        
        recent_rewards = self.episode_rewards[-100:] if len(self.episode_rewards) >= 100 else self.episode_rewards
        
        return {
            "total_episodes": len(self.episode_rewards),
            "average_reward": np.mean(self.episode_rewards),
            "recent_average_reward": np.mean(recent_rewards),
            "max_reward": np.max(self.episode_rewards),
            "min_reward": np.min(self.episode_rewards),
            "current_epsilon": self.epsilon,
            "q_table_size": len(self.q_table),
            "learning_rate": self.learning_rate,
            "discount_factor": self.discount_factor
        }
    
    def _state_to_key(self, state: State) -> str:
        """将状态转换为键"""
        # 将状态特征转换为字符串键
        features = state.get("features", [0.0])
        features_str = "_".join([f"{f:.2f}" for f in features])
        return f"state_{features_str}"
    
    def _get_action_type(self, action_id: int) -> str:
        """获取动作类型"""
        action_types = ["explore", "exploit", "analyze", "optimize", "adapt"]
        return action_types[action_id % len(action_types)]
    
    def _get_action_parameters(self, action_id: int) -> Dict[str, Any]:
        """获取动作参数"""
        return {
            "duration": random.uniform(0.5, 2.0),
            "priority": random.randint(1, 5)
        }
    
    def process_data(self, data: Any) -> Any:
        """处理数据（兼容接口）"""
        if isinstance(data, dict) and "state" in data:
            # 处理状态数据
            state = {
                "state_id": data.get("type", "unknown"),
                "features": data.get("type", []),
                "metadata": data.get("type", {})
            }
            
            action = self.select_action(state)
            policy = self.get_policy(state)
            
            return {
                "state": state,
                "selected_action": action,
                "policy": policy,
                "epsilon": self.epsilon
            }
        else:
            return {"error", "Invalid data format for RL processing"}
    
    def validate(self, data: Any) -> bool:
        """验证数据（兼容接口）"""
        return data is not None and isinstance(data, dict)

# 全局实例
deep_reinforcement_learning = DeepReinforcementLearning(state_size=10, action_size=5)

def get_deep_reinforcement_learning() -> DeepReinforcementLearning:
    """获取深度强化学习模块实例"""
    return deep_reinforcement_learning
