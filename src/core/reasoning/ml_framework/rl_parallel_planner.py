"""
RL并行规划器 - 使用强化学习优化并行分解策略的选择

初始版本：基于规则的策略选择 + 简单Q表
未来版本：PPO或DQN智能体
"""
import logging
import random
from typing import Dict, Any, List, Optional
from collections import defaultdict
from .base_ml_component import BaseRLComponent

logger = logging.getLogger(__name__)


class RLParallelPlanner(BaseRLComponent):
    """RL并行规划器
    
    使用强化学习优化并行分解策略的选择：
    - 完全并行
    - 部分并行
    - 串行但独立
    - 合并步骤
    """
    
    # 分解策略类型
    DECOMPOSITION_STRATEGIES = {
        0: "fully_parallel",      # 完全并行
        1: "partially_parallel",  # 部分并行
        2: "serial_independent",  # 串行但独立
        3: "merge_steps",         # 合并步骤
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化RL并行规划器
        
        Args:
            config: 配置字典
        """
        super().__init__(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # RL参数
        self.exploration_rate = self.config.get("exploration_rate", 0.1)
        self.learning_rate = self.config.get("learning_rate", 0.01)
        self.discount_factor = self.config.get("discount_factor", 0.95)
        
        # 策略性能记录（简单Q表）
        self.strategy_performance = {
            strategy: {"success_count": 0, "total_count": 0, "avg_reward": 0.0}
            for strategy in self.DECOMPOSITION_STRATEGIES.values()
        }
        
        # 经验回放缓冲区
        self.replay_buffer = []
        self.max_buffer_size = self.config.get("max_buffer_size", 1000)
        
        # 训练相关
        self.training_enabled = self.config.get("training_enabled", True)
        self.min_buffer_size = self.config.get("min_buffer_size", 100)  # 开始训练的最小经验数
        self.batch_size = self.config.get("batch_size", 32)
        self.update_frequency = self.config.get("update_frequency", 10)  # 每N个经验更新一次
        self.update_count = 0
        
    def select_action(self, state: Dict[str, Any]) -> int:
        """选择分解策略
        
        Args:
            state: 状态字典，包含：
                - query_features: 查询特征
                - system_state: 系统状态
                - query_complexity: 查询复杂度
                - estimated_steps: 估算步骤数
                
        Returns:
            策略索引（0-3）
        """
        try:
            # 提取状态特征
            query_complexity = state.get("query_complexity", "medium")
            estimated_steps = state.get("estimated_steps", 3)
            
            # 探索 vs 利用
            if random.random() < self.exploration_rate:
                # 探索：随机选择策略
                strategy_idx = random.randint(0, len(self.DECOMPOSITION_STRATEGIES) - 1)
                self.logger.debug(f"🔍 [探索] 随机选择分解策略: {self.DECOMPOSITION_STRATEGIES[strategy_idx]}")
            else:
                # 利用：选择性能最好的策略
                strategy_idx = self._select_best_strategy(state)
                self.logger.debug(f"🎯 [利用] 选择最优分解策略: {self.DECOMPOSITION_STRATEGIES[strategy_idx]}")
            
            return strategy_idx
            
        except Exception as e:
            self.logger.error(f"选择分解策略失败: {e}")
            return 0  # 默认：完全并行
    
    def _select_best_strategy(self, state: Dict[str, Any]) -> int:
        """选择性能最好的策略"""
        query_complexity = state.get("query_complexity", "medium")
        estimated_steps = state.get("estimated_steps", 3)
        
        # 根据查询复杂度和步骤数选择策略
        if estimated_steps <= 2:
            # 步骤少，使用串行但独立
            return 2
        elif estimated_steps <= 5:
            # 中等步骤，使用部分并行
            return 1
        elif query_complexity == "complex":
            # 复杂查询，使用完全并行
            return 0
        else:
            # 默认：部分并行
            return 1
    
    def update(self, state: Dict[str, Any], action: int, reward: float, next_state: Dict[str, Any], done: bool):
        """更新策略
        
        Args:
            state: 当前状态
            action: 执行的动作（策略索引）
            reward: 获得的奖励
            next_state: 下一个状态
            done: 是否结束
        """
        try:
            strategy_name = self.DECOMPOSITION_STRATEGIES[action]
            
            # 更新策略性能记录
            self.strategy_performance[strategy_name]["total_count"] += 1
            if reward > 0:
                self.strategy_performance[strategy_name]["success_count"] += 1
            
            # 更新平均奖励（简单移动平均）
            current_avg = self.strategy_performance[strategy_name]["avg_reward"]
            count = self.strategy_performance[strategy_name]["total_count"]
            new_avg = (current_avg * (count - 1) + reward) / count
            self.strategy_performance[strategy_name]["avg_reward"] = new_avg
            
            # 添加到经验回放缓冲区
            experience = {
                "state": state,
                "action": action,
                "reward": reward,
                "next_state": next_state,
                "done": done,
            }
            self.replay_buffer.append(experience)
            
            # 限制缓冲区大小
            if len(self.replay_buffer) > self.max_buffer_size:
                self.replay_buffer.pop(0)
            
            # 训练RL模型（如果启用且缓冲区足够大）
            self.update_count += 1
            if (self.training_enabled and 
                len(self.replay_buffer) >= self.min_buffer_size and
                self.update_count % self.update_frequency == 0):
                self._train_from_replay_buffer()
            
            self.logger.debug(f"✅ 策略更新: {strategy_name}, 奖励: {reward:.2f}, 平均奖励: {new_avg:.2f}")
            
        except Exception as e:
            self.logger.error(f"更新策略失败: {e}")
    
    def get_strategy_name(self, action: int) -> str:
        """获取策略名称"""
        return self.DECOMPOSITION_STRATEGIES.get(action, "fully_parallel")
    
    def get_strategy_performance(self) -> Dict[str, Any]:
        """获取策略性能统计"""
        return {
            strategy: {
                "success_rate": (
                    perf["success_count"] / perf["total_count"]
                    if perf["total_count"] > 0 else 0.0
                ),
                "avg_reward": perf["avg_reward"],
                "total_count": perf["total_count"],
            }
            for strategy, perf in self.strategy_performance.items()
        }
    
    def calculate_reward(self, execution_result: Dict[str, Any]) -> float:
        """计算奖励（重写基类方法）
        
        Args:
            execution_result: 执行结果字典
            
        Returns:
            奖励值
        """
        base_reward = 0.0
        
        # 正确性奖励（主要，权重40%）
        if execution_result.get("is_correct", False):
            base_reward += 10.0
        
        # 效率奖励（权重30%）
        execution_time = execution_result.get("execution_time", 0)
        if execution_time > 0:
            # 时间越短，奖励越高
            time_reward = max(0, 10.0 - execution_time * 0.1)
            base_reward += time_reward * 0.3
        
        # 资源使用奖励（权重20%）
        api_calls = execution_result.get("api_calls", 0)
        if api_calls > 0:
            # API调用越少，奖励越高
            resource_reward = max(0, 5.0 - api_calls * 0.5)
            base_reward += resource_reward * 0.2
        
        # 答案质量奖励（权重10%）
        confidence = execution_result.get("avg_confidence", 0)
        base_reward += confidence * 2.0 * 0.1
        
        return base_reward
    
    def _train_from_replay_buffer(self):
        """从经验回放缓冲区训练（PPO/DQN）"""
        try:
            if len(self.replay_buffer) < self.min_buffer_size:
                return
            
            # 🚀 尝试使用PyTorch PPO/DQN，如果不可用则使用Q-learning
            use_ppo = self.config.get("use_ppo", True)
            
            try:
                if use_ppo:
                    import torch
                    import torch.nn as nn
                    import torch.optim as optim
                    import torch.nn.functional as F
                    
                    # 定义策略网络（Actor）和价值网络（Critic）
                    if not hasattr(self, 'actor_network') or self.actor_network is None:
                        class ActorNetwork(nn.Module):
                            def __init__(self, state_dim, action_dim, hidden_dim=64):
                                super().__init__()
                                self.fc1 = nn.Linear(state_dim, hidden_dim)
                                self.fc2 = nn.Linear(hidden_dim, hidden_dim)
                                self.fc3 = nn.Linear(hidden_dim, action_dim)
                                
                            def forward(self, state):
                                x = F.relu(self.fc1(state))
                                x = F.relu(self.fc2(x))
                                return F.softmax(self.fc3(x), dim=-1)
                        
                        class CriticNetwork(nn.Module):
                            def __init__(self, state_dim, hidden_dim=64):
                                super().__init__()
                                self.fc1 = nn.Linear(state_dim, hidden_dim)
                                self.fc2 = nn.Linear(hidden_dim, hidden_dim)
                                self.fc3 = nn.Linear(hidden_dim, 1)
                                
                            def forward(self, state):
                                x = F.relu(self.fc1(state))
                                x = F.relu(self.fc2(x))
                                return self.fc3(x)
                        
                        # 初始化网络
                        state_dim = 10  # 状态特征维度
                        action_dim = len(self.DECOMPOSITION_STRATEGIES)
                        self.actor_network = ActorNetwork(state_dim, action_dim)
                        self.critic_network = CriticNetwork(state_dim)
                        self.actor_optimizer = optim.Adam(self.actor_network.parameters(), lr=0.001)
                        self.critic_optimizer = optim.Adam(self.critic_network.parameters(), lr=0.001)
                    
                    # 随机采样一批经验
                    import random
                    batch = random.sample(self.replay_buffer, min(self.batch_size, len(self.replay_buffer)))
                    
                    # 准备数据
                    states = []
                    actions = []
                    rewards = []
                    next_states = []
                    dones = []
                    
                    for exp in batch:
                        state_features = self._extract_state_features(exp["state"])
                        next_state_features = self._extract_state_features(exp["next_state"])
                        states.append(list(state_features.values())[:state_dim])
                        actions.append(exp["action"])
                        rewards.append(exp["reward"])
                        next_states.append(list(next_state_features.values())[:state_dim])
                        dones.append(exp["done"])
                    
                    states_tensor = torch.FloatTensor(states)
                    actions_tensor = torch.LongTensor(actions)
                    rewards_tensor = torch.FloatTensor(rewards)
                    next_states_tensor = torch.FloatTensor(next_states)
                    dones_tensor = torch.FloatTensor(dones)
                    
                    # PPO训练
                    # 计算优势
                    values = self.critic_network(states_tensor).squeeze()
                    next_values = self.critic_network(next_states_tensor).squeeze()
                    advantages = rewards_tensor + self.discount_factor * next_values * (1 - dones_tensor) - values
                    
                    # 更新Critic
                    critic_loss = F.mse_loss(values, rewards_tensor + self.discount_factor * next_values * (1 - dones_tensor))
                    self.critic_optimizer.zero_grad()
                    critic_loss.backward()
                    self.critic_optimizer.step()
                    
                    # 更新Actor
                    probs = self.actor_network(states_tensor)
                    action_probs = probs.gather(1, actions_tensor.unsqueeze(1)).squeeze()
                    actor_loss = -(action_probs * advantages.detach()).mean()
                    self.actor_optimizer.zero_grad()
                    actor_loss.backward()
                    self.actor_optimizer.step()
                    
                    self.model_type = "ppo"
                    self.logger.debug(f"🔄 PPO训练完成: 批次大小={len(batch)}, Actor Loss: {actor_loss.item():.4f}, Critic Loss: {critic_loss.item():.4f}")
                    return
                    
            except ImportError:
                # PyTorch不可用，使用Q-learning
                self.logger.debug("⚠️ PyTorch不可用，使用Q-learning")
                use_ppo = False
            
            if not use_ppo:
                # 简单的Q-learning更新（fallback）
                import random
                batch = random.sample(self.replay_buffer, min(self.batch_size, len(self.replay_buffer)))
                
                for experience in batch:
                    state = experience["state"]
                    action = experience["action"]
                    reward = experience["reward"]
                    next_state = experience["next_state"]
                    done = experience["done"]
                    
                    # 更新Q值
                    state_features = self._extract_state_features(state)
                    next_state_features = self._extract_state_features(next_state)
                    state_idx = self._get_state_index(state_features)
                    next_state_idx = self._get_state_index(next_state_features)
                    
                    old_value = self.q_table.get((state_idx, action), 0.0)
                    next_max = max([self.q_table.get((next_state_idx, a), 0.0) for a in self.DECOMPOSITION_STRATEGIES.keys()])
                    new_value = old_value + self.learning_rate * (reward + self.discount_factor * next_max * (1 - int(done)) - old_value)
                    self.q_table[(state_idx, action)] = new_value
                
                self.model_type = "q_learning"
                self.logger.debug(f"🔄 Q-learning训练完成: 批次大小={len(batch)}, 缓冲区大小={len(self.replay_buffer)}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ RL训练失败: {e}")
    
    def train(self, training_data: Optional[List[Any]] = None) -> Dict[str, Any]:
        """训练RL模型（从经验回放缓冲区）
        
        Args:
            training_data: 可选的外部训练数据（当前使用内部缓冲区）
            
        Returns:
            训练结果字典
        """
        try:
            import time
            start_time = time.time()
            
            if len(self.replay_buffer) < self.min_buffer_size:
                return {
                    "success": False,
                    "error": f"经验缓冲区不足，需要至少{self.min_buffer_size}条经验，当前{len(self.replay_buffer)}条"
                }
            
            # 执行多轮训练
            num_epochs = self.config.get("num_epochs", 10)
            for epoch in range(num_epochs):
                self._train_from_replay_buffer()
            
            training_time = time.time() - start_time
            
            # 计算平均奖励
            if self.replay_buffer:
                avg_reward = sum(exp["reward"] for exp in self.replay_buffer) / len(self.replay_buffer)
            else:
                avg_reward = 0.0
            
            self.logger.info(f"✅ RL训练完成: {num_epochs}轮, 平均奖励: {avg_reward:.2f}, 训练时间: {training_time:.2f}s")
            
            return {
                "success": True,
                "num_epochs": num_epochs,
                "buffer_size": len(self.replay_buffer),
                "avg_reward": float(avg_reward),
                "training_time": training_time,
                "model_type": getattr(self, 'model_type', 'q_learning_v1')
            }
            
        except Exception as e:
            self.logger.error(f"❌ RL训练失败: {e}")
            return {"success": False, "error": str(e)}

