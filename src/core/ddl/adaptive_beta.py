import json
import os
import logging
from typing import Dict, Any, Optional
from .beta_parameter_calculator import BetaParameterCalculator

logger = logging.getLogger(__name__)

class AdaptiveBetaThreshold:
    """
    自适应β阈值管理器 (Adaptive Beta Threshold Manager)
    
    动态调整不同策略之间的切换阈值，基于历史成功率。
    P1阶段目标：消除硬编码的 0.5 和 1.4 阈值。
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self.config_path = "data/learning/beta_thresholds.json"
        
        # Initialize the BetaParameterCalculator for ML-based calculations
        self.beta_calculator = BetaParameterCalculator()
        
        # 默认阈值 (Hardcoded defaults as fallback)
        self.thresholds = {
            "direct_to_hyde": 0.5,  # Beta < 0.5 -> Direct
            "hyde_to_cot": 1.4      # Beta > 1.4 -> CoT
        }
        
        # 统计数据 (用于调整)
        self.stats = {
            "direct": {"success": 0, "total": 0},
            "hyde": {"success": 0, "total": 0},
            "cot": {"success": 0, "total": 0}
        }
        
        self._load_config()
        
    def get_threshold(self, name: str) -> float:
        """获取当前阈值"""
        return self.thresholds.get(name, 0.5)
        
    def record_outcome(self, strategy: str, success: bool, execution_time: Optional[float] = None, 
                      relevance_score: Optional[float] = None, beta_value: Optional[float] = None,
                      query: Optional[str] = None):
        """
        记录策略执行结果并集成ML性能跟踪
        Enhanced for P1 phase with BetaParameterCalculator integration
        """
        # 映射策略名称到标准键
        key = "unknown"
        if "direct" in strategy: key = "direct"
        elif "hyde" in strategy: key = "hyde"
        elif "cot" in strategy: key = "cot"
        
        if key in self.stats:
            self.stats[key]["total"] += 1
            if success:
                self.stats[key]["success"] += 1
        
        # Enhanced ML-based performance tracking (P1 Phase)
        if query and beta_value is not None and execution_time is not None:
            self.beta_calculator.record_strategy_execution(
                strategy_name=strategy,
                query=query,
                beta_value=beta_value,
                execution_time=execution_time,
                success=success,
                relevance_score=relevance_score or 0.0,
                coverage_score=0.0  # Default for now
            )
                
        # 每10次记录触发一次调整检查
        if sum(s["total"] for s in self.stats.values()) % 10 == 0:
            self._adjust_thresholds()

    def _adjust_thresholds(self):
        """
        根据成功率调整阈值 - Enhanced for P1 Phase with ML insights
        逻辑：
        1. 如果 Direct 成功率很高 (>90%)，可以提高 direct_to_hyde 阈值 (e.g. 0.5 -> 0.6)，让更多查询走 Direct (省钱/快)。
        2. 如果 HyDE 成功率很低 (<60%)，可以降低 hyde_to_cot 阈值 (e.g. 1.4 -> 1.3)，让更多查询走 CoT (更强)。
        3. P1 Enhancement: Use ML-based performance insights from BetaParameterCalculator for more intelligent adjustments
        """
        # 计算成功率
        rates = {}
        for k, v in self.stats.items():
            rates[k] = v["success"] / v["total"] if v["total"] > 0 else 0.0
            
        logger.info(f"AdaptiveBeta Stats: {rates}")
        
        # P1 Phase: Get ML-based performance insights
        ml_metrics = self.beta_calculator.get_performance_metrics()
        logger.debug(f"ML Performance Metrics: {ml_metrics}")
        
        changed = False
        
        # Enhanced adjustment logic with ML insights
        for strategy in ["direct", "hyde", "cot"]:
            base_success_rate = rates.get(strategy, 0)
            ml_perf = ml_metrics.get(strategy, {})
            ml_success_rate = ml_perf.get("success_rate", base_success_rate)
            
            # Weighted success rate: 70% historical, 30% ML insights
            weighted_success_rate = 0.7 * base_success_rate + 0.3 * ml_success_rate
            
            # 调整 Direct -> HyDE 阈值
            if strategy == "direct":
                if weighted_success_rate > 0.9:
                    # Direct 表现很好，扩大它的范围
                    self.thresholds["direct_to_hyde"] = min(0.8, self.thresholds["direct_to_hyde"] + 0.05)
                    changed = True
                elif weighted_success_rate < 0.6:
                    # Direct 表现差，缩小它的范围
                    self.thresholds["direct_to_hyde"] = max(0.2, self.thresholds["direct_to_hyde"] - 0.05)
                    changed = True
            
            # 调整 HyDE -> CoT 阈值
            elif strategy == "hyde":
                if weighted_success_rate < 0.6:
                    # HyDE 表现差，让更多流量去 CoT (降低门槛)
                    self.thresholds["hyde_to_cot"] = max(1.0, self.thresholds["hyde_to_cot"] - 0.05)
                    changed = True
                elif weighted_success_rate > 0.9:
                    # HyDE 表现很好，不需要那么多 CoT (提高门槛)
                    self.thresholds["hyde_to_cot"] = min(1.8, self.thresholds["hyde_to_cot"] + 0.05)
                    changed = True
            
        if changed:
            logger.info(f"AdaptiveBeta Adjusted: {self.thresholds}")
            self._save_config()

    def _load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    self.thresholds.update(data.get("thresholds", {}))
                    self.stats.update(data.get("stats", {}))
            except Exception as e:
                logger.warning(f"Failed to load adaptive beta config: {e}")

    def _save_config(self):
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump({
                    "thresholds": self.thresholds,
                    "stats": self.stats
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save adaptive beta config: {e}")
