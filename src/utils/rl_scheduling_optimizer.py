#!/usr/bin/env python3
"""
RL驱动的调度优化器
使用强化学习优化调度决策
"""

import json
import time
import numpy as np
from typing import Dict, Any, Optional, List
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class SchedulingState:
    """调度状态"""
    query_type: str
    query_complexity: str
    query_length: int
    has_knowledge: bool
    knowledge_quality: float


@dataclass
class SchedulingAction:
    """调度动作"""
    knowledge_timeout: float
    reasoning_timeout: float
    parallel_execution: bool
    skip_answer_generation: bool


@dataclass
class SchedulingExperience:
    """调度经验（状态-动作-奖励-下一状态）"""
    state: SchedulingState
    action: SchedulingAction
    reward: float
    next_state: Optional[SchedulingState]
    timestamp: float


class RLSchedulingOptimizer:
    """RL驱动的调度优化器（Q-learning）"""
    
    def __init__(
        self,
        data_path: str = "data/learning/rl_scheduling.json",
        learning_rate: float = 0.1,
        discount_factor: float = 0.9,
        epsilon: float = 0.1
    ):
        """
        初始化RL调度优化器
        
        Args:
            data_path: 学习数据存储路径
            learning_rate: 学习率（α）
            discount_factor: 折扣因子（γ）
            epsilon: ε-greedy探索率
        """
        self.logger = logger
        self.data_path = Path(data_path)
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Q-learning参数
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        
        # Q表：state -> action -> Q值
        self.q_table: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        
        # 经验回放缓冲区
        self.experience_buffer: List[SchedulingExperience] = []
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
    
    def _load_history(self):
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
                    
                    self.logger.info(f"✅ 加载RL调度优化历史数据: Q表大小={len(self.q_table)}")
        except Exception as e:
            self.logger.warning(f"加载RL调度优化历史数据失败: {e}")
    
    def _save_history(self):
        """保存历史Q表和经验"""
        try:
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
            self.logger.error(f"保存RL调度优化历史数据失败: {e}")
    
    def _state_to_key(self, state: SchedulingState) -> str:
        """将状态转换为Q表的键"""
        query_type = state.query_type
        complexity_bin = 'low' if state.query_complexity in ['simple'] else 'medium' if state.query_complexity == 'medium' else 'high'
        knowledge_bin = 'yes' if state.has_knowledge else 'no'
        quality_bin = 'high' if state.knowledge_quality > 0.7 else 'medium' if state.knowledge_quality > 0.4 else 'low'
        
        return f"{query_type}_{complexity_bin}_{knowledge_bin}_{quality_bin}"
    
    def _action_to_key(self, action: SchedulingAction) -> str:
        """将动作转换为Q表的键"""
        timeout_k = int(action.knowledge_timeout)
        timeout_r = int(action.reasoning_timeout)
        parallel = 'p' if action.parallel_execution else 's'
        skip = 'skip' if action.skip_answer_generation else 'gen'
        return f"k{timeout_k}_r{timeout_r}_{parallel}_{skip}"
    
    def select_action(
        self,
        state: SchedulingState,
        available_actions: Optional[List[SchedulingAction]] = None
    ) -> SchedulingAction:
        """
        选择动作（ε-greedy策略）
        
        Args:
            state: 当前状态
            available_actions: 可用动作列表（如果为None，生成默认动作）
            
        Returns:
            选择的动作
        """
        if available_actions is None:
            available_actions = self._generate_available_actions(state)
        
        if not available_actions:
            return self._get_default_action(state)
        
        state_key = self._state_to_key(state)
        
        # ε-greedy策略
        if np.random.random() < self.epsilon:
            # 探索：随机选择动作
            action = np.random.choice(available_actions)
            self.stats['exploration_count'] += 1
            self.logger.debug(f"探索：随机选择动作")
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
            self.logger.debug(f"利用：选择Q值最高的动作 (Q={best_q_value:.4f})")
        
        return action
    
    def _generate_available_actions(self, state: SchedulingState) -> List[SchedulingAction]:
        """生成可用动作列表"""
        actions = []
        
        # 根据状态生成不同的动作
        if state.query_complexity == 'simple':
            # 简单查询：较短的超时时间
            knowledge_timeouts = [10.0, 12.0]
            reasoning_timeouts = [150.0, 200.0]
        elif state.query_complexity in ['complex', 'very_complex']:
            # 复杂查询：较长的超时时间
            knowledge_timeouts = [12.0, 15.0, 18.0]
            reasoning_timeouts = [200.0, 250.0, 300.0]
        else:
            # 中等复杂度
            knowledge_timeouts = [12.0, 15.0]
            reasoning_timeouts = [200.0, 250.0]
        
        # 生成动作组合
        for k_timeout in knowledge_timeouts:
            for r_timeout in reasoning_timeouts:
                for parallel in [False, True]:  # 是否并行执行
                    for skip_answer in [False, True]:  # 是否跳过答案生成
                        actions.append(SchedulingAction(
                            knowledge_timeout=k_timeout,
                            reasoning_timeout=r_timeout,
                            parallel_execution=parallel,
                            skip_answer_generation=skip_answer
                        ))
        
        return actions
    
    def _get_default_action(self, state: SchedulingState) -> SchedulingAction:
        """获取默认动作"""
        return SchedulingAction(
            knowledge_timeout=12.0,
            reasoning_timeout=200.0,
            parallel_execution=False,
            skip_answer_generation=False
        )
    
    def update_q_value(
        self,
        state: SchedulingState,
        action: SchedulingAction,
        reward: float,
        next_state: Optional[SchedulingState]
    ):
        """
        更新Q值（Q-learning更新规则）
        
        Q(s, a) = Q(s, a) + α * [r + γ * max(Q(s', a')) - Q(s, a)]
        """
        try:
            state_key = self._state_to_key(state)
            action_key = self._action_to_key(action)
            
            # 获取当前Q值
            current_q = self.q_table[state_key][action_key]
            
            # 计算下一状态的最大Q值
            if next_state:
                next_state_key = self._state_to_key(next_state)
                next_actions = self._generate_available_actions(next_state)
                max_next_q = max(
                    [self.q_table[next_state_key][self._action_to_key(a)] for a in next_actions],
                    default=0.0
                )
            else:
                max_next_q = 0.0
            
            # Q-learning更新
            new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
            self.q_table[state_key][action_key] = new_q
            
            # 更新统计信息
            self.stats['total_episodes'] += 1
            self.stats['total_rewards'] += reward
            self.stats['avg_reward'] = self.stats['total_rewards'] / self.stats['total_episodes']
            
            # 定期保存
            if self.stats['total_episodes'] % 10 == 0:
                self._save_history()
            
        except Exception as e:
            self.logger.warning(f"更新Q值失败: {e}")
    
    def calculate_reward(
        self,
        total_time: float,
        success: bool,
        accuracy: float,
        knowledge_time: float,
        reasoning_time: float,
        answer_time: float = 0.0,
        citation_time: float = 0.0,
        evidence_count: int = 0,
        confidence: float = 0.0
    ) -> float:
        """
        🚀 ML/RL优化：改进的奖励函数（多目标优化）
        
        Args:
            total_time: 总处理时间
            success: 是否成功
            accuracy: 答案准确率
            knowledge_time: 知识检索时间
            reasoning_time: 推理时间
            answer_time: 答案生成时间（新增）
            citation_time: 引用生成时间（新增）
            evidence_count: 证据数量（新增）
            confidence: 答案置信度（新增）
            
        Returns:
            奖励值（范围：-2.0 到 2.0）
        """
        # 🚀 ML/RL优化：多目标奖励函数
        # 1. 基础奖励：成功+1.5，失败-1.5（提高成功奖励）
        base_reward = 1.5 if success else -1.5
        
        # 2. 准确率奖励：准确率越高，奖励越高（权重0.4）
        accuracy_reward = accuracy * 0.4
        
        # 3. 置信度奖励：置信度越高，奖励越高（权重0.2）
        confidence_reward = confidence * 0.2
        
        # 4. 时间效率奖励：时间越短，奖励越高（权重0.2）
        # 归一化：理想时间100秒，超过600秒得分降低
        ideal_time = 100.0
        max_time = 600.0
        if total_time <= ideal_time:
            time_efficiency = 1.0
        elif total_time >= max_time:
            time_efficiency = 0.0
        else:
            time_efficiency = 1.0 - (total_time - ideal_time) / (max_time - ideal_time)
        time_reward = time_efficiency * 0.2
        
        # 5. 时间平衡奖励：知识检索和推理时间平衡（权重0.1）
        # 避免某个阶段耗时过长
        if total_time > 0:
            knowledge_ratio = knowledge_time / total_time
            reasoning_ratio = reasoning_time / total_time
            # 理想比例：知识检索30%，推理60%，其他10%
            ideal_knowledge_ratio = 0.3
            ideal_reasoning_ratio = 0.6
            balance_score = 1.0 - abs(knowledge_ratio - ideal_knowledge_ratio) - abs(reasoning_ratio - ideal_reasoning_ratio)
            balance_reward = max(0.0, balance_score) * 0.1
        else:
            balance_reward = 0.0
        
        # 6. 证据质量奖励：证据数量适中（权重0.1）
        # 理想证据数量：5-10个
        if 5 <= evidence_count <= 10:
            evidence_reward = 0.1
        elif 3 <= evidence_count < 5 or 10 < evidence_count <= 15:
            evidence_reward = 0.05
        else:
            evidence_reward = 0.0
        
        # 总奖励（范围：-1.5 到 2.5）
        total_reward = base_reward + accuracy_reward + confidence_reward + time_reward + balance_reward + evidence_reward
        
        # 归一化到 -2.0 到 2.0 范围
        normalized_reward = max(-2.0, min(2.0, total_reward))
        
        return normalized_reward
        reward = base_reward + accuracy_reward + time_reward
        
        return reward
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            'q_table_size': len(self.q_table),
            'exploration_rate': self.stats['exploration_count'] / max(self.stats['total_episodes'], 1),
            'exploitation_rate': self.stats['exploitation_count'] / max(self.stats['total_episodes'], 1)
        }


# 单例模式
_rl_scheduling_optimizer_instance = None

def get_rl_scheduling_optimizer() -> RLSchedulingOptimizer:
    """获取RL调度优化器单例"""
    global _rl_scheduling_optimizer_instance
    if _rl_scheduling_optimizer_instance is None:
        _rl_scheduling_optimizer_instance = RLSchedulingOptimizer()
    return _rl_scheduling_optimizer_instance

