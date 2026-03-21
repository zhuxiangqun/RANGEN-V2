"""
基础ML组件 - 所有ML组件的基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class BaseMLComponent(ABC):
    """ML组件基类
    
    所有ML组件都应该继承这个基类，确保统一的接口和生命周期管理。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化ML组件
        
        Args:
            config: 配置字典，包含模型路径、超参数等
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        self.model = None
        self.is_trained = False
        
    @abstractmethod
    def predict(self, input_data: Any) -> Dict[str, Any]:
        """执行预测
        
        Args:
            input_data: 输入数据（格式由子类定义）
            
        Returns:
            预测结果字典，至少包含：
            - prediction: 主要预测结果
            - confidence: 置信度（0-1）
            - metadata: 其他元数据
        """
        pass
    
    @abstractmethod
    def train(self, training_data: List[Any], labels: Optional[List[Any]] = None) -> Dict[str, Any]:
        """训练模型
        
        Args:
            training_data: 训练数据
            labels: 标签（如果是监督学习）
            
        Returns:
            训练结果字典，包含：
            - loss: 损失值
            - metrics: 评估指标
            - training_time: 训练时间
        """
        pass
    
    def load_model(self, model_path: str) -> bool:
        """加载预训练模型
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            是否加载成功
        """
        try:
            # 子类实现具体的加载逻辑
            self._load_model_impl(model_path)
            self.is_trained = True
            self.logger.info(f"✅ 成功加载模型: {model_path}")
            return True
        except Exception as e:
            self.logger.error(f"❌ 加载模型失败: {e}")
            return False
    
    def save_model(self, model_path: str) -> bool:
        """保存模型
        
        Args:
            model_path: 模型保存路径
            
        Returns:
            是否保存成功
        """
        try:
            # 子类实现具体的保存逻辑
            self._save_model_impl(model_path)
            self.logger.info(f"✅ 成功保存模型: {model_path}")
            return True
        except Exception as e:
            self.logger.error(f"❌ 保存模型失败: {e}")
            return False
    
    @abstractmethod
    def _load_model_impl(self, model_path: str):
        """子类实现：加载模型的具体逻辑"""
        pass
    
    @abstractmethod
    def _save_model_impl(self, model_path: str):
        """子类实现：保存模型的具体逻辑"""
        pass
    
    def evaluate(self, test_data: List[Any], test_labels: List[Any]) -> Dict[str, float]:
        """评估模型性能
        
        Args:
            test_data: 测试数据
            test_labels: 测试标签
            
        Returns:
            评估指标字典
        """
        if not self.is_trained:
            self.logger.warning("⚠️ 模型未训练，无法评估")
            return {}
        
        # 子类实现具体的评估逻辑
        return self._evaluate_impl(test_data, test_labels)
    
    @abstractmethod
    def _evaluate_impl(self, test_data: List[Any], test_labels: List[Any]) -> Dict[str, float]:
        """子类实现：评估的具体逻辑"""
        pass


class BaseRLComponent(ABC):
    """RL组件基类
    
    所有RL组件都应该继承这个基类。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化RL组件
        
        Args:
            config: 配置字典，包含算法类型、超参数等
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        self.agent = None
        self.replay_buffer = []
        
    @abstractmethod
    def select_action(self, state: Any) -> int:
        """选择动作
        
        Args:
            state: 当前状态
            
        Returns:
            动作索引
        """
        pass
    
    @abstractmethod
    def update(self, state: Any, action: int, reward: float, next_state: Any, done: bool):
        """更新策略
        
        Args:
            state: 当前状态
            action: 执行的动作
            reward: 获得的奖励
            next_state: 下一个状态
            done: 是否结束
        """
        pass
    
    def calculate_reward(self, execution_result: Dict[str, Any]) -> float:
        """计算奖励
        
        Args:
            execution_result: 执行结果字典
            
        Returns:
            奖励值
        """
        # 基础奖励计算，子类可以重写
        base_reward = 0.0
        
        # 正确性奖励（主要）
        if execution_result.get("is_correct", False):
            base_reward += 10.0
        
        # 效率惩罚
        time_penalty = execution_result.get("execution_time", 0) * 0.1
        base_reward -= time_penalty
        
        # 资源使用惩罚
        api_call_penalty = execution_result.get("api_calls", 0) * 0.05
        base_reward -= api_call_penalty
        
        # 答案质量奖励
        confidence_bonus = execution_result.get("avg_confidence", 0) * 2.0
        base_reward += confidence_bonus
        
        return base_reward

