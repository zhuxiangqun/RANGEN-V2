"""
自适应重试策略智能体 - 基于强化学习优化重试策略选择

初始版本：基于规则的策略选择
未来版本：基于PPO的强化学习智能体
"""
import logging
import random
from typing import Dict, Any, List, Optional, Tuple
from .base_ml_component import BaseRLComponent

logger = logging.getLogger(__name__)


class AdaptiveRetryAgent(BaseRLComponent):
    """自适应重试策略智能体
    
    使用强化学习优化重试策略的选择，包括：
    - 重试相同查询
    - 同义词替换
    - 查询重写
    - 添加上下文
    - 切换数据源
    """
    
    # 重试策略类型
    RETRY_STRATEGIES = {
        0: "retry_same_query",      # 重试相同查询
        1: "synonym_replacement",    # 同义词替换
        2: "query_rewrite",          # 查询重写
        3: "add_context",            # 添加上下文
        4: "switch_data_source",     # 切换数据源
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化自适应重试智能体
        
        Args:
            config: 配置字典
        """
        super().__init__(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 策略选择参数
        self.exploration_rate = self.config.get("exploration_rate", 0.1)
        self.learning_rate = self.config.get("learning_rate", 0.01)
        
        # 策略性能记录（简单Q表）
        self.strategy_performance = {
            strategy: {"success_count": 0, "total_count": 0, "avg_reward": 0.0}
            for strategy in self.RETRY_STRATEGIES.values()
        }
        
        # 经验回放缓冲区
        self.replay_buffer = []
        self.max_buffer_size = self.config.get("max_buffer_size", 1000)
        
        # 训练相关
        self.training_enabled = self.config.get("training_enabled", True)
        self.min_buffer_size = self.config.get("min_buffer_size", 100)
        self.batch_size = self.config.get("batch_size", 32)
        self.update_frequency = self.config.get("update_frequency", 10)
        self.update_count = 0
        
    def select_action(self, state: Dict[str, Any]) -> int:
        """选择重试策略
        
        Args:
            state: 状态字典，包含：
                - retry_count: 重试次数
                - initial_confidence: 初始置信度
                - result_features: 结果特征
                - context_features: 上下文特征
                - history_features: 历史特征
                
        Returns:
            策略索引（0-4）
        """
        try:
            # 提取状态特征
            retry_count = state.get("retry_count", 0)
            initial_confidence = state.get("initial_confidence", 0.0)
            result_features = state.get("result_features", {})
            
            # 探索 vs 利用
            if random.random() < self.exploration_rate:
                # 探索：随机选择策略
                strategy_idx = random.randint(0, len(self.RETRY_STRATEGIES) - 1)
                self.logger.debug(f"🔍 [探索] 随机选择策略: {self.RETRY_STRATEGIES[strategy_idx]}")
            else:
                # 利用：选择性能最好的策略
                strategy_idx = self._select_best_strategy(state)
                self.logger.debug(f"🎯 [利用] 选择最优策略: {self.RETRY_STRATEGIES[strategy_idx]}")
            
            return strategy_idx
            
        except Exception as e:
            self.logger.error(f"选择重试策略失败: {e}")
            return 0  # 默认：重试相同查询
    
    def _select_best_strategy(self, state: Dict[str, Any]) -> int:
        """选择性能最好的策略"""
        retry_count = state.get("retry_count", 0)
        initial_confidence = state.get("initial_confidence", 0.0)
        
        # 根据重试次数和置信度选择策略
        if retry_count == 0:
            # 第一次重试：尝试查询重写
            return 2
        elif retry_count == 1:
            # 第二次重试：尝试同义词替换
            return 1
        elif retry_count == 2:
            # 第三次重试：添加上下文
            return 3
        else:
            # 多次重试后：切换数据源
            return 4
    
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
            strategy_name = self.RETRY_STRATEGIES[action]
            
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
        return self.RETRY_STRATEGIES.get(action, "retry_same_query")
    
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
    
    def _train_from_replay_buffer(self):
        """从经验回放缓冲区训练（PPO）"""
        try:
            if len(self.replay_buffer) < self.min_buffer_size:
                return
            
            # 🚀 尝试使用PyTorch PPO，如果不可用则使用Q-learning
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
                        action_dim = len(self.RETRY_STRATEGIES)
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
                    next_max = max([self.q_table.get((next_state_idx, a), 0.0) for a in self.RETRY_STRATEGIES.keys()])
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

