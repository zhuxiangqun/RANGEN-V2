"""
智能算法集成器

集成先进的AI算法，提升系统的智能化水平
包括强化学习、迁移学习、自适应算法等
"""

import asyncio
import logging
import time
import random
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import defaultdict


logger = logging.getLogger(__name__)


class AlgorithmType(Enum):
    """算法类型"""
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    TRANSFER_LEARNING = "transfer_learning"
    ONLINE_LEARNING = "online_learning"
    BANDIT_ALGORITHM = "bandit_algorithm"
    EVOLUTIONARY_ALGORITHM = "evolutionary_algorithm"


@dataclass
class AlgorithmConfig:
    """算法配置"""
    name: str
    type: AlgorithmType
    parameters: Dict[str, Any] = field(default_factory=dict)
    learning_rate: float = 0.01
    exploration_rate: float = 0.1
    discount_factor: float = 0.9
    max_iterations: int = 1000
    convergence_threshold: float = 0.001


@dataclass
class LearningContext:
    """学习上下文"""
    state: Dict[str, Any]
    action: Any
    reward: float
    next_state: Dict[str, Any]
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlgorithmPerformance:
    """算法性能指标"""
    algorithm_name: str
    total_samples: int = 0
    average_reward: float = 0.0
    convergence_iterations: int = 0
    final_performance: float = 0.0
    improvement_rate: float = 0.0
    last_updated: float = field(default_factory=time.time)


class ReinforcementLearner:
    """
    强化学习算法实现

    支持Q-learning、SARSA等经典算法
    """

    def __init__(self, config: AlgorithmConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Q表：状态 -> 动作 -> Q值
        self.q_table: Dict[str, Dict[Any, float]] = defaultdict(dict)

        # 学习参数
        self.alpha = config.learning_rate  # 学习率
        self.gamma = config.discount_factor  # 折扣因子
        self.epsilon = config.exploration_rate  # 探索率

        # 统计信息
        self.episodes_completed = 0
        self.total_reward = 0.0

    def get_state_key(self, state: Dict[str, Any]) -> str:
        """将状态转换为可哈希的键"""
        # 简化的状态键生成（生产环境中应使用更复杂的方法）
        key_parts = []
        for k, v in sorted(state.items()):
            if isinstance(v, (int, float)):
                # 将数值型状态离散化
                key_parts.append(f"{k}:{int(v / 10) * 10}")
            elif isinstance(v, str):
                key_parts.append(f"{k}:{v}")
            else:
                key_parts.append(f"{k}:{str(v)}")

        return "|".join(key_parts)

    def choose_action(self, state: Dict[str, Any], available_actions: List[Any]) -> Any:
        """选择动作（ε-greedy策略）"""
        state_key = self.get_state_key(state)

        # 探索 vs 利用
        if random.random() < self.epsilon:
            # 探索：随机选择
            return random.choice(available_actions)
        else:
            # 利用：选择Q值最大的动作
            if state_key in self.q_table:
                q_values = self.q_table[state_key]
                # 只考虑可用的动作
                available_q_values = {
                    action: q_values.get(action, 0.0)
                    for action in available_actions
                }
                return max(available_q_values, key=available_q_values.get)
            else:
                # 如果没有Q值记录，随机选择
                return random.choice(available_actions)

    def update_q_value(self, context: LearningContext):
        """更新Q值"""
        state_key = self.get_state_key(context.state)
        next_state_key = self.get_state_key(context.next_state)

        # 获取当前Q值
        current_q = self.q_table[state_key].get(context.action, 0.0)

        # 计算最大未来Q值
        if next_state_key in self.q_table:
            max_future_q = max(self.q_table[next_state_key].values(), default=0.0)
        else:
            max_future_q = 0.0

        # Q-learning更新公式
        new_q = current_q + self.alpha * (
            context.reward + self.gamma * max_future_q - current_q
        )

        # 更新Q表
        self.q_table[state_key][context.action] = new_q

        # 更新统计信息
        self.total_reward += context.reward
        self.episodes_completed += 1

    def get_policy(self, state: Dict[str, Any]) -> Dict[Any, float]:
        """获取当前策略（状态下的动作概率）"""
        state_key = self.get_state_key(state)

        if state_key not in self.q_table:
            return {}

        q_values = self.q_table[state_key]
        if not q_values:
            return {}

        # 使用softmax将Q值转换为概率
        max_q = max(q_values.values())
        exp_values = {action: np.exp(q - max_q) for action, q in q_values.items()}
        total_exp = sum(exp_values.values())

        return {
            action: exp_val / total_exp
            for action, exp_val in exp_values.items()
        }

    def get_performance_metrics(self) -> AlgorithmPerformance:
        """获取性能指标"""
        avg_reward = self.total_reward / self.episodes_completed if self.episodes_completed > 0 else 0.0

        return AlgorithmPerformance(
            algorithm_name=self.config.name,
            total_samples=self.episodes_completed,
            average_reward=avg_reward,
            convergence_iterations=self.episodes_completed,
            final_performance=avg_reward,
            improvement_rate=0.0  # 需要历史数据计算
        )


class BanditAlgorithm:
    """
    多臂老虎机算法

    用于在线学习和资源分配优化
    """

    def __init__(self, config: AlgorithmConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 初始化臂（选项）
        self.arms: Dict[Any, Dict[str, Union[int, float]]] = {}
        self.total_trials = 0

    def add_arm(self, arm_id: Any):
        """添加臂"""
        if arm_id not in self.arms:
            self.arms[arm_id] = {
                "trials": 0,
                "rewards": 0.0,
                "average_reward": 0.0
            }

    def select_arm(self) -> Any:
        """选择臂（UCB1算法）"""
        if not self.arms:
            return None

        # UCB1 公式：平均奖励 + sqrt(2 * ln(总试验数) / 该臂试验数)
        best_arm = None
        best_ucb = float('-inf')

        for arm_id, stats in self.arms.items():
            if stats["trials"] == 0:
                # 未探索的臂优先选择
                return arm_id

            ucb_value = stats["average_reward"] + np.sqrt(
                2 * np.log(self.total_trials) / stats["trials"]
            )

            if ucb_value > best_ucb:
                best_ucb = ucb_value
                best_arm = arm_id

        return best_arm

    def update_arm(self, arm_id: Any, reward: float):
        """更新臂的奖励"""
        if arm_id not in self.arms:
            self.add_arm(arm_id)

        stats = self.arms[arm_id]
        stats["trials"] += 1
        stats["rewards"] += reward
        stats["average_reward"] = stats["rewards"] / stats["trials"]

        self.total_trials += 1

    def get_best_arm(self) -> Any:
        """获取当前最佳臂"""
        if not self.arms:
            return None

        return max(
            self.arms.keys(),
            key=lambda arm: self.arms[arm]["average_reward"]
        )

    def get_arm_statistics(self) -> Dict[Any, Dict[str, Union[int, float]]]:
        """获取臂统计信息"""
        return self.arms.copy()


class OnlineLearner:
    """
    在线学习算法

    支持增量学习和概念漂移检测
    """

    def __init__(self, config: AlgorithmConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 学习模型（简化实现）
        self.weights: Dict[str, float] = {}
        self.learning_rate = config.learning_rate
        self.samples_seen = 0

        # 概念漂移检测
        self.drift_detector = self._init_drift_detector()

    def _init_drift_detector(self) -> Dict[str, Any]:
        """初始化概念漂移检测器"""
        return {
            "window_size": 100,
            "recent_errors": [],
            "drift_threshold": 0.1,
            "drift_detected": False
        }

    def learn_incrementally(self, features: Dict[str, float], target: float):
        """增量学习"""
        self.samples_seen += 1

        # 简单的在线学习算法（类似感知机）
        prediction = self._predict(features)
        error = target - prediction

        # 更新权重
        for feature, value in features.items():
            if feature not in self.weights:
                self.weights[feature] = 0.0

            self.weights[feature] += self.learning_rate * error * value

        # 检测概念漂移
        self._detect_concept_drift(error)

    def _predict(self, features: Dict[str, float]) -> float:
        """预测"""
        prediction = 0.0
        for feature, value in features.items():
            prediction += self.weights.get(feature, 0.0) * value
        return prediction

    def predict(self, features: Dict[str, float]) -> float:
        """对外预测接口"""
        return self._predict(features)

    def _detect_concept_drift(self, error: float):
        """检测概念漂移"""
        detector = self.drift_detector
        detector["recent_errors"].append(abs(error))

        # 保持窗口大小
        if len(detector["recent_errors"]) > detector["window_size"]:
            detector["recent_errors"].pop(0)

        # 计算平均错误率
        if len(detector["recent_errors"]) >= detector["window_size"] // 2:
            avg_error = sum(detector["recent_errors"]) / len(detector["recent_errors"])

            if avg_error > detector["drift_threshold"] and not detector["drift_detected"]:
                detector["drift_detected"] = True
                self.logger.warning(f"⚠️ 检测到概念漂移，平均错误率: {avg_error:.3f}")

                # 重置学习器
                self._reset_learner()

    def _reset_learner(self):
        """重置学习器"""
        self.weights.clear()
        self.drift_detector["drift_detected"] = False
        self.drift_detector["recent_errors"].clear()
        self.logger.info("🔄 学习器已重置以适应新的概念")

    def get_learning_stats(self) -> Dict[str, Any]:
        """获取学习统计信息"""
        return {
            "samples_seen": self.samples_seen,
            "features_learned": len(self.weights),
            "drift_detected": self.drift_detector["drift_detected"],
            "average_recent_error": (
                sum(self.drift_detector["recent_errors"]) /
                len(self.drift_detector["recent_errors"])
                if self.drift_detector["recent_errors"] else 0.0
            )
        }


class IntelligentAlgorithmIntegrator:
    """
    智能算法集成器

    统一管理各种AI算法，提供智能决策和优化能力
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 算法注册表
        self.algorithms: Dict[str, Any] = {}
        self.algorithm_configs: Dict[str, AlgorithmConfig] = {}

        # 性能监控
        self.performance_history: Dict[str, List[AlgorithmPerformance]] = defaultdict(list)

        # 自动算法选择
        self.auto_selection_enabled = True

    def register_algorithm(
        self,
        name: str,
        algorithm_type: AlgorithmType,
        algorithm_instance: Any,
        config: AlgorithmConfig
    ):
        """注册算法"""
        self.algorithms[name] = algorithm_instance
        self.algorithm_configs[name] = config

        self.logger.info(f"✅ 注册算法: {name} ({algorithm_type.value})")

    def create_reinforcement_learner(
        self,
        name: str,
        learning_rate: float = 0.1,
        exploration_rate: float = 0.1,
        discount_factor: float = 0.9
    ) -> ReinforcementLearner:
        """创建强化学习算法"""
        config = AlgorithmConfig(
            name=name,
            type=AlgorithmType.REINFORCEMENT_LEARNING,
            learning_rate=learning_rate,
            exploration_rate=exploration_rate,
            discount_factor=discount_factor
        )

        learner = ReinforcementLearner(config)
        self.register_algorithm(name, AlgorithmType.REINFORCEMENT_LEARNING, learner, config)

        return learner

    def create_bandit_algorithm(
        self,
        name: str,
        arms: List[Any] = None
    ) -> BanditAlgorithm:
        """创建多臂老虎机算法"""
        config = AlgorithmConfig(
            name=name,
            type=AlgorithmType.BANDIT_ALGORITHM
        )

        bandit = BanditAlgorithm(config)

        # 初始化臂
        if arms:
            for arm in arms:
                bandit.add_arm(arm)

        self.register_algorithm(name, AlgorithmType.BANDIT_ALGORITHM, bandit, config)

        return bandit

    def create_online_learner(
        self,
        name: str,
        learning_rate: float = 0.01
    ) -> OnlineLearner:
        """创建在线学习算法"""
        config = AlgorithmConfig(
            name=name,
            type=AlgorithmType.ONLINE_LEARNING,
            learning_rate=learning_rate
        )

        learner = OnlineLearner(config)
        self.register_algorithm(name, AlgorithmType.ONLINE_LEARNING, learner, config)

        return learner

    def get_algorithm(self, name: str) -> Optional[Any]:
        """获取算法实例"""
        return self.algorithms.get(name)

    def execute_algorithm(
        self,
        algorithm_name: str,
        operation: str,
        **kwargs
    ) -> Any:
        """执行算法操作"""
        algorithm = self.get_algorithm(algorithm_name)
        if not algorithm:
            raise ValueError(f"算法 '{algorithm_name}' 不存在")

        try:
            if operation == "choose_action":
                return algorithm.choose_action(**kwargs)
            elif operation == "update_q_value":
                return algorithm.update_q_value(**kwargs)
            elif operation == "select_arm":
                return algorithm.select_arm()
            elif operation == "update_arm":
                return algorithm.update_arm(**kwargs)
            elif operation == "learn_incremental":
                return algorithm.learn_incrementally(**kwargs)
            elif operation == "predict":
                return algorithm.predict(**kwargs)
            else:
                raise ValueError(f"不支持的操作: {operation}")

        except Exception as e:
            self.logger.error(f"❌ 算法执行失败 {algorithm_name}.{operation}: {e}")
            raise

    def update_algorithm_performance(self, algorithm_name: str, context: LearningContext = None):
        """更新算法性能"""
        algorithm = self.get_algorithm(algorithm_name)
        if not algorithm:
            return

        try:
            performance = algorithm.get_performance_metrics()
            self.performance_history[algorithm_name].append(performance)

            # 保持历史记录数量
            if len(self.performance_history[algorithm_name]) > 100:
                self.performance_history[algorithm_name] = self.performance_history[algorithm_name][-100:]

        except Exception as e:
            self.logger.debug(f"性能更新失败 {algorithm_name}: {e}")

    def get_algorithm_recommendations(self, context: Dict[str, Any]) -> List[str]:
        """获取算法使用建议"""
        recommendations = []

        # 基于上下文推荐算法
        if context.get("need_exploration", False):
            recommendations.append("推荐使用强化学习算法进行探索")

        if context.get("have_multiple_options", False):
            recommendations.append("推荐使用多臂老虎机算法进行选项选择")

        if context.get("streaming_data", False):
            recommendations.append("推荐使用在线学习算法处理流数据")

        if context.get("need_personalization", False):
            recommendations.append("考虑使用迁移学习进行个性化")

        return recommendations if recommendations else ["根据具体需求选择合适的算法"]

    def get_system_intelligence_metrics(self) -> Dict[str, Any]:
        """获取系统智能化指标"""
        total_algorithms = len(self.algorithms)
        active_algorithms = sum(1 for alg in self.algorithms.values()
                              if hasattr(alg, 'episodes_completed') and alg.episodes_completed > 0)

        # 计算学习效率
        learning_efficiency = 0.0
        if self.performance_history:
            recent_performances = []
            for history in self.performance_history.values():
                if history:
                    recent_performances.append(history[-1].average_reward)

            if recent_performances:
                learning_efficiency = sum(recent_performances) / len(recent_performances)

        return {
            "total_algorithms": total_algorithms,
            "active_algorithms": active_algorithms,
            "learning_efficiency": learning_efficiency,
            "algorithm_types": list(set(config.type.value for config in self.algorithm_configs.values())),
            "performance_trend": "improving" if learning_efficiency > 0.5 else "stable"
        }

    def optimize_algorithm_parameters(self, algorithm_name: str) -> Dict[str, Any]:
        """优化算法参数"""
        config = self.algorithm_configs.get(algorithm_name)
        if not config:
            return {}

        # 基于性能历史进行参数优化建议
        history = self.performance_history.get(algorithm_name, [])

        if len(history) < 5:
            return {"status": "insufficient_data"}

        # 简单的参数优化逻辑
        recent_avg_reward = sum(h.average_reward for h in history[-5:]) / 5
        trend = "improving" if recent_avg_reward > history[0].average_reward else "declining"

        optimizations = {}

        if trend == "improving":
            optimizations["learning_rate"] = "保持当前学习率"
        else:
            if config.learning_rate > 0.001:
                optimizations["learning_rate"] = "建议降低学习率"
            else:
                optimizations["learning_rate"] = "学习率已很低，考虑其他优化"

        return {
            "status": "analyzed",
            "trend": trend,
            "optimizations": optimizations,
            "confidence": "medium"
        }


# 全局智能算法集成器实例
_intelligent_integrator_instance = None

def get_intelligent_algorithm_integrator() -> IntelligentAlgorithmIntegrator:
    """获取智能算法集成器实例"""
    global _intelligent_integrator_instance
    if _intelligent_integrator_instance is None:
        _intelligent_integrator_instance = IntelligentAlgorithmIntegrator()
    return _intelligent_integrator_instance

async def initialize_intelligent_algorithms():
    """初始化智能算法"""
    integrator = get_intelligent_algorithm_integrator()

    # 创建基础算法
    rl_learner = integrator.create_reinforcement_learner(
        "performance_optimizer",
        learning_rate=0.1,
        exploration_rate=0.2
    )

    bandit = integrator.create_bandit_algorithm(
        "resource_allocator",
        arms=["high", "medium", "low"]
    )

    online_learner = integrator.create_online_learner(
        "adaptive_predictor",
        learning_rate=0.01
    )

    logger.info("✅ 智能算法初始化完成")

    return integrator
