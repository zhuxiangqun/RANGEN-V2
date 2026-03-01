#!/usr/bin/env python3
"""
强化学习优化器 - 阶段3：强化学习
使用Q-learning优化策略选择
"""

import json
import time
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, asdict
from ..utils.logger import get_logger

logger = get_logger()


@dataclass
class State:
    """状态表示"""
    query_type: str
    query_length: int
    avg_similarity: float
    result_count: int


@dataclass
class Action:
    """动作表示（策略选择）"""
    strategy: str  # 'vector_only', 'vector_rerank', 'vector_graph', 'vector_llamaindex', 'hybrid'
    top_k: int
    similarity_threshold: float
    use_rerank: bool
    use_graph: bool
    use_llamaindex: bool


@dataclass
class Experience:
    """经验（状态-动作-奖励-下一状态）"""
    state: State
    action: Action
    reward: float
    next_state: Optional[State]
    timestamp: float


class ReinforcementLearningOptimizer:
    """强化学习优化器（Q-learning）"""
    
    def __init__(
        self,
        data_path: str = "data/knowledge_management/rl_optimization.json",
        learning_rate: float = 0.1,
        discount_factor: float = 0.9,
        epsilon: float = 0.1
    ):
        self.logger = logger
        self.data_path = Path(data_path)
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Q-learning参数
        self.learning_rate = learning_rate  # α
        self.discount_factor = discount_factor  # γ
        self.epsilon = epsilon  # ε-greedy探索率
        
        # Q表：state -> action -> Q值
        self.q_table: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        
        # 经验回放缓冲区
        self.experience_buffer: List[Experience] = []
        self.max_buffer_size = 1000
        
        # 统计信息
        self.stats = {
            'total_episodes': 0,
            'total_rewards': 0.0,
            'avg_reward': 0.0,
            'exploration_count': 0,
            'exploitation_count': 0
        }
        
        # 加载历史数据
        self._load_history()
    
    def _load_history(self) -> None:
        """加载历史Q表和经验"""
        try:
            if self.data_path.exists():
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if 'q_table' in data:
                        self.q_table = defaultdict(
                            lambda: defaultdict(float),
                            {k: defaultdict(float, v) for k, v in data['q_table'].items()}
                        )
                    
                    if 'stats' in data:
                        self.stats.update(data['stats'])
                    
                    self.logger.info(f"✅ 加载RL历史数据: Q表大小={len(self.q_table)}")
        except Exception as e:
            self.logger.warning(f"加载RL历史数据失败: {e}")
    
    def _save_history(self) -> None:
        """保存历史Q表和经验"""
        try:
            # 将defaultdict转换为普通dict以便序列化
            q_table_dict = {
                state: dict(actions)
                for state, actions in self.q_table.items()
            }
            
            data = {
                'q_table': q_table_dict,
                'stats': self.stats
            }
            
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存RL历史数据失败: {e}")
    
    def _state_to_key(self, state: State) -> str:
        """将状态转换为Q表的键"""
        # 简化状态表示（离散化）
        query_type = state.query_type
        query_length_bin = 'short' if state.query_length < 50 else 'medium' if state.query_length < 150 else 'long'
        similarity_bin = 'low' if state.avg_similarity < 0.6 else 'medium' if state.avg_similarity < 0.8 else 'high'
        result_count_bin = 'few' if state.result_count < 3 else 'medium' if state.result_count < 10 else 'many'
        
        return f"{query_type}_{query_length_bin}_{similarity_bin}_{result_count_bin}"
    
    def _action_to_key(self, action: Action) -> str:
        """将动作转换为Q表的键"""
        return f"{action.strategy}_k{action.top_k}_t{action.similarity_threshold:.2f}_r{action.use_rerank}_g{action.use_graph}_l{action.use_llamaindex}"
    
    def select_action(self, state: State, available_actions: List[Action]) -> Action:
        """
        选择动作（ε-greedy策略）
        
        Args:
            state: 当前状态
            available_actions: 可用动作列表
            
        Returns:
            选择的动作
        """
        if not available_actions:
            # 默认动作
            return Action(
                strategy='vector_rerank',
                top_k=5,
                similarity_threshold=0.7,
                use_rerank=True,
                use_graph=False,
                use_llamaindex=False
            )
        
        state_key = self._state_to_key(state)
        
        # ε-greedy策略
        if np.random.random() < self.epsilon:
            # 探索：随机选择动作
            action = np.random.choice(available_actions)
            self.stats['exploration_count'] += 1
            self.logger.debug(f"探索：随机选择动作 {action.strategy}")
        else:
            # 利用：选择Q值最高的动作
            best_action = None
            best_q_value = float('-inf')
            
            for action in available_actions:
                action_key = self._action_to_key(action)
                q_value = self.q_table[state_key][action_key]
                
                if q_value > best_q_value:
                    best_q_value = q_value
                    best_action = action
            
            if best_action is None:
                # 如果Q表中没有记录，随机选择
                action = np.random.choice(available_actions)
            else:
                action = best_action
            
            self.stats['exploitation_count'] += 1
            self.logger.debug(f"利用：选择Q值最高的动作 {action.strategy} (Q={best_q_value:.4f})")
        
        return action
    
    def update_q_value(
        self,
        state: State,
        action: Action,
        reward: float,
        next_state: Optional[State]
    ) -> None:
        """
        更新Q值（Q-learning更新规则）
        
        Q(s, a) = Q(s, a) + α * [r + γ * max(Q(s', a')) - Q(s, a)]
        """
        try:
            state_key = self._state_to_key(state)
            action_key = self._action_to_key(action)
            
            # 当前Q值
            current_q = self.q_table[state_key][action_key]
            
            # 计算下一状态的最大Q值
            if next_state is not None:
                next_state_key = self._state_to_key(next_state)
                max_next_q = max(
                    self.q_table[next_state_key].values(),
                    default=0.0
                )
            else:
                max_next_q = 0.0  # 终止状态
            
            # Q-learning更新
            new_q = current_q + self.learning_rate * (
                reward + self.discount_factor * max_next_q - current_q
            )
            
            self.q_table[state_key][action_key] = new_q
            
            # 记录经验
            experience = Experience(
                state=state,
                action=action,
                reward=reward,
                next_state=next_state,
                timestamp=time.time()
            )
            self.experience_buffer.append(experience)
            
            # 限制缓冲区大小
            if len(self.experience_buffer) > self.max_buffer_size:
                self.experience_buffer = self.experience_buffer[-self.max_buffer_size:]
            
            # 更新统计信息
            self.stats['total_episodes'] += 1
            self.stats['total_rewards'] += reward
            self.stats['avg_reward'] = self.stats['total_rewards'] / self.stats['total_episodes']
            
            # 每10次更新保存一次
            if self.stats['total_episodes'] % 10 == 0:
                self._save_history()
        except Exception as e:
            self.logger.error(f"更新Q值失败: {e}")
    
    def calculate_reward(
        self,
        result_count: int,
        max_similarity: float,
        avg_similarity: float,
        processing_time: float,
        success: bool
    ) -> float:
        """
        计算奖励
        
        Args:
            result_count: 结果数量
            max_similarity: 最大相似度
            avg_similarity: 平均相似度
            processing_time: 处理时间
            success: 是否成功
            
        Returns:
            奖励值
        """
        # 基础奖励（成功+1，失败-1）
        base_reward = 1.0 if success else -1.0
        
        # 质量奖励（基于相似度）
        quality_reward = (max_similarity + avg_similarity) / 2.0
        
        # 效率奖励（基于处理时间，时间越短奖励越高）
        efficiency_reward = 1.0 / (1.0 + processing_time)
        
        # 结果数量奖励（适中的结果数量更好）
        if 3 <= result_count <= 10:
            count_reward = 1.0
        elif result_count > 0:
            count_reward = 0.5
        else:
            count_reward = -0.5
        
        # 总奖励（加权组合）
        total_reward = (
            base_reward * 0.4 +
            quality_reward * 0.3 +
            efficiency_reward * 0.2 +
            count_reward * 0.1
        )
        
        return total_reward
    
    def get_best_action(self, state: State, available_actions: List[Action]) -> Optional[Action]:
        """获取最优动作（不进行探索）"""
        if not available_actions:
            return None
        
        state_key = self._state_to_key(state)
        best_action = None
        best_q_value = float('-inf')
        
        for action in available_actions:
            action_key = self._action_to_key(action)
            q_value = self.q_table[state_key][action_key]
            
            if q_value > best_q_value:
                best_q_value = q_value
                best_action = action
        
        return best_action
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_episodes': self.stats['total_episodes'],
            'total_rewards': self.stats['total_rewards'],
            'avg_reward': self.stats['avg_reward'],
            'exploration_count': self.stats['exploration_count'],
            'exploitation_count': self.stats['exploitation_count'],
            'exploration_rate': (
                self.stats['exploration_count'] / (self.stats['exploration_count'] + self.stats['exploitation_count'])
                if (self.stats['exploration_count'] + self.stats['exploitation_count']) > 0 else 0.0
            ),
            'q_table_size': len(self.q_table),
            'experience_buffer_size': len(self.experience_buffer)
        }

