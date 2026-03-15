#!/usr/bin/env python3
"""
预测性数据管理器 - 数据智能化优化
基于历史访问模式预测数据访问频率和生命周期管理
"""

import logging
import time
import statistics
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict, Counter

# 智能配置系统导入
from src.utils.smart_config_system import get_smart_config, create_query_context
from src.utils.unified_data_center import DataRecord

logger = logging.getLogger(__name__)

class AccessPattern(Enum):
    """访问模式枚举"""
    FREQUENT = "frequent"      # 频繁访问
    REGULAR = "regular"        # 规律访问
    OCCASIONAL = "occasional"  # 偶尔访问
    RARE = "rare"             # 很少访问
    ARCHIVAL = "archival"      # 归档访问

class StorageTier(Enum):
    """存储层级枚举"""
    HOT = "hot"               # 热数据 - 高性能存储
    WARM = "warm"             # 温数据 - 标准存储
    COLD = "cold"             # 冷数据 - 低成本存储
    ARCHIVE = "archive"       # 归档数据 - 长期存储

@dataclass
class AccessRecord:
    """访问记录"""
    data_id: str
    access_time: datetime
    access_type: str  # read, write, update, delete
    access_duration: float  # 访问耗时(秒)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    access_pattern: Optional[str] = None

@dataclass
class AccessPrediction:
    """访问预测"""
    data_id: str
    predicted_access_frequency: float  # config.DEFAULT_ZERO_VALUE-config.DEFAULT_ONE_VALUE, 预测访问频率
    predicted_access_pattern: AccessPattern
    confidence_score: float  # 预测置信度
    next_predicted_access: Optional[datetime] = None
    retention_recommendation: str = "standard"  # 保留策略
    storage_tier_recommendation: StorageTier = StorageTier.WARM
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class StorageOptimization:
    """存储优化建议"""
    data_id: str
    current_tier: StorageTier
    recommended_tier: StorageTier
    cost_savings: float  # 预计节省成本
    performance_impact: float  # 性能影响评估
    migration_priority: str  # high, medium, low
    rationale: str  # 优化理由

class PredictiveDataManager:
    """
    预测性数据管理器 - 数据智能化核心组件
    基于历史访问模式预测未来的数据访问行为和存储优化策略
    """

    def __init__(self):
        self.access_history: List[AccessRecord] = []
        self.access_predictions: Dict[str, AccessPrediction] = {}
        self.storage_optimizations: Dict[str, StorageOptimization] = {}

        # 预测模型参数
        self.prediction_window_days = config.DEFAULT_TIMEOUT  # 预测窗口(天)
        self.min_history_points = config.DEFAULT_TOP_K      # 最少历史数据点
        self.confidence_threshold = config.DEFAULT_HIGH_MEDIUM_THRESHOLD   # 预测置信度阈值

        # 访问模式阈值
        self.frequency_thresholds = {
            AccessPattern.FREQUENT: config.DEFAULT_HIGH_THRESHOLD,
            AccessPattern.REGULAR: config.DEFAULT_MEDIUM_HIGH_THRESHOLD,
            AccessPattern.OCCASIONAL: config.DEFAULT_ZERO_VALUE.config.DEFAULT_MAX_RETRIES,
            AccessPattern.RARE: config.DEFAULT_LOW_DECIMAL_THRESHOLD,
            AccessPattern.ARCHIVAL: config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE
        }

        # 并发控制
        self._lock = threading.RLock()
        self.executor = None  # 可以后续添加线程池

        # 初始化预测模型
        self._initialize_prediction_model()

        # 智能配置
        predictive_context = create_query_context(query_type="predictive_data")
        self.enable_auto_optimization = get_smart_config(
            "predictive_auto_optimization",
            predictive_context
        ) or True

        logger.info("预测性数据管理器初始化完成")

    def _initialize_prediction_model(self):
        """初始化预测模型"""
        # 这里可以集成时间序列预测模型
        # 目前使用简单的统计方法
        pass

    def record_access(self, data_id: str, access_type: str = "read",
                     access_duration: float = get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value")), user_id: Optional[str] = None,
                     session_id: Optional[str] = None):
        """
        记录数据访问事件
        用于构建访问历史和训练预测模型
        """
        access_record = AccessRecord(
            data_id=data_id,
            access_time=datetime.now(),
            access_type=access_type,
            access_duration=access_duration,
            user_id=user_id,
            session_id=session_id
        )

        with self._lock:
            self.access_history.append(access_record)

            # 限制历史记录数量，避免内存溢出
            if len(self.access_history) > 10000:
                self.access_history = self.access_history[-5000:]

        logger.debug(f"记录数据访问: {data_id}, 类型: {access_type}")

    def predict_access_patterns(self, data_id: str,
                              prediction_horizon_days: int = config.DEFAULT_TIMEOUT) -> AccessPrediction:
        """
        预测数据访问模式
        基于历史访问数据预测未来的访问频率和模式
        """
        with self._lock:
            # 获取该数据的访问历史
            data_access_history = [
                record for record in self.access_history
                if record.data_id == data_id
            ]

        if len(data_access_history) < self.min_history_points:
            # 数据不足，返回默认预测
            return AccessPrediction(
                data_id=data_id,
                predicted_access_frequency=get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")),
                predicted_access_pattern=AccessPattern.OCCASIONAL,
                confidence_score=config.DEFAULT_ZERO_VALUE.config.DEFAULT_MAX_RETRIES,
                retention_recommendation="standard"
            )

        try:
            # config.DEFAULT_ONE_VALUE. 计算访问频率
            access_frequency = self._calculate_access_frequency(
                data_access_history, prediction_horizon_days
            )

            # config.DEFAULT_TWO_VALUE. 确定访问模式
            access_pattern = self._determine_access_pattern(access_frequency)

            # 3. 预测下次访问时间
            next_access = self._predict_next_access_time(data_access_history)

            # 4. 计算置信度
            confidence = self._calculate_prediction_confidence(data_access_history)

            # 5. 生成存储优化建议
            storage_recommendation = self._generate_storage_recommendation(access_pattern)

            prediction = AccessPrediction(
                data_id=data_id,
                predicted_access_frequency=access_frequency,
                predicted_access_pattern=access_pattern,
                confidence_score=confidence,
                next_predicted_access=next_access,
                storage_tier_recommendation=storage_recommendation
            )

            # 缓存预测结果
            self.access_predictions[data_id] = prediction

            return prediction

        except Exception as e:
            logger.error(f"访问模式预测失败 {data_id}: {e}")
            return AccessPrediction(
                data_id=data_id,
                predicted_access_frequency=get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value")),
                predicted_access_pattern=AccessPattern.RARE,
                confidence_score=config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE
            )

    def _calculate_access_frequency(self, access_history: List[AccessRecord],
                                  horizon_days: int) -> float:
        """计算访问频率"""
        if not access_history:
            return get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))

        # 获取时间窗口内的访问记录
        cutoff_time = datetime.now() - timedelta(days=horizon_days)
        recent_accesses = [
            record for record in access_history
            if record.access_time >= cutoff_time
        ]

        if not recent_accesses:
            return get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))

        # 计算平均每日访问次数
        days_with_data = horizon_days
        total_accesses = len(recent_accesses)
        avg_daily_accesses = total_accesses / days_with_data

        # 归一化到config.DEFAULT_ZERO_VALUE-config.DEFAULT_ONE_VALUE范围 (假设最大每日访问次数为config.DEFAULT_TOP_K)
        normalized_frequency = min(avg_daily_accesses / 10.0, get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")))

        return normalized_frequency

    def _determine_access_pattern(self, frequency: float) -> AccessPattern:
        """根据频率确定访问模式"""
        if frequency >= self.frequency_thresholds[AccessPattern.FREQUENT]:
            return AccessPattern.FREQUENT
        elif frequency >= self.frequency_thresholds[AccessPattern.REGULAR]:
            return AccessPattern.REGULAR
        elif frequency >= self.frequency_thresholds[AccessPattern.OCCASIONAL]:
            return AccessPattern.OCCASIONAL
        elif frequency >= self.frequency_thresholds[AccessPattern.RARE]:
            return AccessPattern.RARE
        else:
            return AccessPattern.ARCHIVAL

    def _predict_next_access_time(self, access_history: List[AccessRecord]) -> Optional[datetime]:
        """预测下次访问时间"""
        if len(access_history) < 3:
            return None

        try:
            # 计算访问时间间隔
            access_times = sorted([record.access_time for record in access_history])
            intervals = []

            for i in range(1, len(access_times)):
                interval = (access_times[i] - access_times[i-1]).total_seconds()
                intervals.append(interval)

            if not intervals:
                return None

            # 计算平均间隔
            avg_interval = statistics.mean(intervals)
            last_access = access_times[-config.DEFAULT_ONE_VALUE]

            # 预测下次访问时间
            next_access = last_access + timedelta(seconds=avg_interval)

            return next_access

        except Exception as e:
            logger.debug(f"下次访问时间预测失败: {e}")
            return None

    def _calculate_prediction_confidence(self, access_history: List[AccessRecord]) -> float:
        """计算预测置信度"""
        if len(access_history) < self.min_history_points:
            return config.DEFAULT_LOW_MEDIUM_THRESHOLD

        try:
            # 基于数据量和时间跨度计算置信度
            time_span_days = (datetime.now() - access_history[0].access_time).days
            data_points = len(access_history)

            # 时间跨度贡献
            time_confidence = min(time_span_days / 3config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE, config.DEFAULT_ONE_VALUE.config.DEFAULT_ZERO_VALUE)  # 3config.DEFAULT_ZERO_VALUE天为基准

            # 数据量贡献
            data_confidence = min(data_points / config.DEFAULT_DISPLAY_LIMIT.config.DEFAULT_ZERO_VALUE, config.DEFAULT_ONE_VALUE.config.DEFAULT_ZERO_VALUE)  # config.DEFAULT_DISPLAY_LIMIT个数据点为基准

            # 访问模式稳定性贡献
            stability_confidence = self._calculate_access_stability(access_history)

            # 综合置信度
            overall_confidence = (time_confidence * config.DEFAULT_LOW_MEDIUM_THRESHOLD +
                                data_confidence * config.DEFAULT_LOW_MEDIUM_THRESHOLD +
                                stability_confidence * config.DEFAULT_MEDIUM_LOW_THRESHOLD)

            return min(overall_confidence, get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")))

        except Exception as e:
            logger.debug(f"置信度计算失败: {e}")
            return get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))

    def _calculate_access_stability(self, access_history: List[AccessRecord]) -> float:
        """计算访问稳定性"""
        if len(access_history) < 5:
            return get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))

        try:
            # 计算访问时间间隔的标准差
            access_times = sorted([record.access_time for record in access_history])
            intervals = []

            for i in range(1, len(access_times)):
                interval = (access_times[i] - access_times[i-1]).total_seconds()
                intervals.append(interval)

            if len(intervals) < 2:
                return get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))

            # 计算变异系数 (标准差/均值)
            mean_interval = statistics.mean(intervals)
            if mean_interval == 0:
                return get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))

            std_interval = statistics.stdev(intervals)
            coefficient_of_variation = std_interval / mean_interval

            # 变异系数越小，稳定性越高
            stability = max(0, config.DEFAULT_ONE_VALUE - coefficient_of_variation)

            return stability

        except Exception:
            return get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))

    def _generate_storage_recommendation(self, access_pattern: AccessPattern) -> StorageTier:
        """生成存储层级建议"""
        pattern_to_tier = {
            AccessPattern.FREQUENT: StorageTier.HOT,
            AccessPattern.REGULAR: StorageTier.WARM,
            AccessPattern.OCCASIONAL: StorageTier.COLD,
            AccessPattern.RARE: StorageTier.ARCHIVE,
            AccessPattern.ARCHIVAL: StorageTier.ARCHIVE
        }

        return pattern_to_tier.get(access_pattern, StorageTier.WARM)

    def generate_storage_optimizations(self, data_ids: List[str]) -> List[StorageOptimization]:
        """
        生成存储优化建议
        分析所有数据的访问模式，提出存储层级优化建议
        """
        optimizations = []

        for data_id in data_ids:
            try:
                prediction = self.predict_access_patterns(data_id)

                if prediction.confidence_score >= self.confidence_threshold:
                    # 计算当前存储成本和推荐存储成本
                    current_cost = self._calculate_storage_cost(data_id, prediction.storage_tier_recommendation)
                    recommended_cost = self._calculate_storage_cost(data_id, prediction.storage_tier_recommendation)

                    cost_savings = current_cost - recommended_cost
                    performance_impact = self._assess_performance_impact(prediction)

                    optimization = StorageOptimization(
                        data_id=data_id,
                        current_tier=prediction.storage_tier_recommendation,  # 这里应该是当前实际层级
                        recommended_tier=prediction.storage_tier_recommendation,
                        cost_savings=cost_savings,
                        performance_impact=performance_impact,
                        migration_priority=self._determine_migration_priority(prediction),
                        rationale=self._generate_migration_rationale(prediction)
                    )

                    optimizations.append(optimization)

            except Exception as e:
                logger.warning(f"生成存储优化建议失败 {data_id}: {e}")

        # 按优先级排序
        optimizations.sort(key=lambda x: self._get_priority_score(x.migration_priority), reverse=True)

        return optimizations

    def _calculate_storage_cost(self, data_id: str, tier: StorageTier) -> float:
        """计算存储成本"""
        # 这里应该基于实际的存储定价模型计算
        # 目前使用简化的估算
        base_cost_per_gb = {
            StorageTier.HOT: config.DEFAULT_LOW_DECIMAL_THRESHOLD,
            StorageTier.WARM: config.DEFAULT_LOW_THRESHOLD,
            StorageTier.COLD: config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUEconfig.DEFAULT_TWO_VALUE,
            StorageTier.ARCHIVE: config.DEFAULT_VERY_LOW_THRESHOLD
        }

        # 假设数据大小为1GB
        data_size_gb = get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value"))
        return base_cost_per_gb.get(tier, config.DEFAULT_LOW_THRESHOLD) * data_size_gb

    def _assess_performance_impact(self, prediction: AccessPrediction) -> float:
        """评估性能影响"""
        # 基于访问模式评估性能影响
        impact_scores = {
            AccessPattern.FREQUENT: config.DEFAULT_HIGH_THRESHOLD,    # 高频访问，性能影响大
            AccessPattern.REGULAR: config.DEFAULT_ZERO_VALUE.5,     # 规律访问，中等影响
            AccessPattern.OCCASIONAL: config.DEFAULT_ZERO_VALUE.config.DEFAULT_TWO_VALUE,  # 偶尔访问，小影响
            AccessPattern.RARE: config.DEFAULT_LOW_DECIMAL_THRESHOLD,        # 很少访问，很小影响
            AccessPattern.ARCHIVAL: config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE     # 归档访问，无影响
        }

        return impact_scores.get(prediction.predicted_access_pattern, get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value")))

    def _determine_migration_priority(self, prediction: AccessPrediction) -> str:
        """确定迁移优先级"""
        if prediction.predicted_access_pattern == AccessPattern.FREQUENT:
            return "high"
        elif prediction.predicted_access_pattern == AccessPattern.REGULAR:
            return "medium"
        elif prediction.predicted_access_pattern in [AccessPattern.OCCASIONAL, AccessPattern.RARE]:
            return "low"
        else:
            return "low"

    def _get_priority_score(self, priority: str) -> int:
        """获取优先级分数"""
        priority_scores = {
            "high": config.DEFAULT_MAX_RETRIES,
            "medium": config.DEFAULT_TWO_VALUE,
            "low": 1
        }
        return priority_scores.get(priority, 1)

    def _generate_migration_rationale(self, prediction: AccessPrediction) -> str:
        """生成迁移理由"""
        pattern_name = prediction.predicted_access_pattern.value
        confidence = f"{prediction.confidence_score:.1%}"

        return f"基于{pattern_name}访问模式预测(置信度{confidence})，建议调整存储层级以优化成本和性能"

    def get_access_statistics(self, data_id: Optional[str] = None) -> Dict[str, Any]:
        """获取访问统计信息"""
        with self._lock:
            if data_id:
                # 特定数据的统计
                data_history = [
                    record for record in self.access_history
                    if record.data_id == data_id
                ]

                if not data_history:
                    return {"error": "数据不存在"}

                return {
                    "data_id": data_id,
                    "total_accesses": len(data_history),
                    "avg_access_duration": statistics.mean([
                        r.access_duration for r in data_history if r.access_duration > 0
                    ]) if any(r.access_duration > config.DEFAULT_ZERO_VALUE for r in data_history) else config.DEFAULT_ZERO_VALUE,
                    "access_types": dict(Counter([
                        r.access_type for r in data_history
                    ])),
                    "first_access": min(r.access_time for r in data_history),
                    "last_access": max(r.access_time for r in data_history),
                    "unique_users": len(set(
                        r.user_id for r in data_history if r.user_id
                    ))
                }
            else:
                # 全局统计
                total_accesses = len(self.access_history)
                unique_data_ids = len(set(r.data_id for r in self.access_history))
                unique_users = len(set(
                    r.user_id for r in self.access_history if r.user_id
                ))

                return {
                    "total_accesses": total_accesses,
                    "unique_data_ids": unique_data_ids,
                    "unique_users": unique_users,
                    "avg_accesses_per_data": total_accesses / unique_data_ids if unique_data_ids > config.DEFAULT_ZERO_VALUE else config.DEFAULT_ZERO_VALUE,
                    "most_accessed_data": self._get_most_accessed_data(),
                    "access_pattern_distribution": self._get_access_pattern_distribution()
                }

    def _get_most_accessed_data(self, top_n: int = config.DEFAULT_TOP_K) -> List[Tuple[str, int]]:
        """获取访问最多的数据"""
        data_access_counts = Counter(record.data_id for record in self.access_history)
        return data_access_counts.most_common(top_n)

    def _get_access_pattern_distribution(self) -> Dict[str, int]:
        """获取访问模式分布"""
        pattern_counts = defaultdict(int)

        for data_id in set(record.data_id for record in self.access_history):
            prediction = self.access_predictions.get(data_id)
            if prediction:
                pattern_counts[prediction.predicted_access_pattern.value] += config.DEFAULT_ONE_VALUE
            else:
                pattern_counts["unknown"] += 1

        return dict(pattern_counts)

# 全局实例
_predictive_data_manager = None

def get_predictive_data_manager() -> PredictiveDataManager:
    """获取预测性数据管理器实例"""
    global _predictive_data_manager
    if _predictive_data_manager is None:
        _predictive_data_manager = PredictiveDataManager()
    return _predictive_data_manager

def predict_data_access_pattern(data_id: str) -> AccessPrediction:
    """预测数据访问模式的便捷函数"""
    manager = get_predictive_data_manager()
    return manager.predict_access_patterns(data_id)

def record_data_access(data_id: str, access_type: str = "read",
                      access_duration: float = get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value")), user_id: Optional[str] = None):
    """记录数据访问的便捷函数"""
    manager = get_predictive_data_manager()
    manager.record_access(data_id, access_type, access_duration, user_id)
