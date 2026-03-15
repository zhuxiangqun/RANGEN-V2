"""
灰度发布系统

实现智能的流量分配和渐进式部署
支持A/B测试、性能监控、自动回滚等功能
"""

import asyncio
import logging
import time
import random
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


logger = logging.getLogger(__name__)


class DeploymentStrategy(Enum):
    """部署策略枚举"""
    PERCENTAGE = "percentage"  # 百分比流量分配
    USER_ID = "user_id"        # 基于用户ID的分配
    RANDOM = "random"          # 随机分配
    GRADUAL = "gradual"        # 渐进式增加流量


@dataclass
class DeploymentVersion:
    """部署版本信息"""
    version: str
    name: str
    weight: float = 0.0  # 流量权重 (0.0-1.0)
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrafficAllocation:
    """流量分配结果"""
    version: str
    strategy: DeploymentStrategy
    allocation_time: float
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeploymentMetrics:
    """部署指标"""
    version: str
    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    average_response_time: float = 0.0
    error_rate: float = 0.0
    traffic_percentage: float = 0.0
    last_updated: float = 0.0


class TrafficRouter:
    """流量路由器"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._versions: Dict[str, DeploymentVersion] = {}
        self._metrics: Dict[str, DeploymentMetrics] = {}

    def add_version(self, version: DeploymentVersion):
        """添加部署版本"""
        self._versions[version.version] = version
        self._metrics[version.version] = DeploymentMetrics(version=version.version)
        self.logger.info(f"✅ 添加部署版本: {version.name} ({version.version})")

    def remove_version(self, version: str):
        """移除部署版本"""
        if version in self._versions:
            del self._versions[version]
            del self._metrics[version]
            self.logger.info(f"✅ 移除部署版本: {version}")

    def update_version_weight(self, version: str, weight: float):
        """更新版本权重"""
        if version in self._versions:
            old_weight = self._versions[version].weight
            self._versions[version].weight = max(0.0, min(1.0, weight))
            self.logger.info(f"✅ 更新版本权重: {version} {old_weight:.1%} → {weight:.1%}")

    def route_traffic(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        strategy: DeploymentStrategy = DeploymentStrategy.PERCENTAGE
    ) -> TrafficAllocation:
        """路由流量"""

        if not self._versions:
            return TrafficAllocation(
                version="default",
                strategy=strategy,
                allocation_time=time.time()
            )

        # 选择版本
        if strategy == DeploymentStrategy.PERCENTAGE:
            selected_version = self._route_by_percentage()
        elif strategy == DeploymentStrategy.USER_ID and user_id:
            selected_version = self._route_by_user_id(user_id)
        elif strategy == DeploymentStrategy.RANDOM:
            selected_version = self._route_by_random()
        else:
            selected_version = self._route_by_percentage()  # 默认使用百分比

        return TrafficAllocation(
            version=selected_version,
            strategy=strategy,
            allocation_time=time.time(),
            user_id=user_id,
            session_id=session_id
        )

    def _route_by_percentage(self) -> str:
        """基于百分比路由"""
        total_weight = sum(v.weight for v in self._versions.values() if v.enabled)

        if total_weight <= 0:
            # 如果没有权重，返回第一个启用的版本
            enabled_versions = [v for v in self._versions.values() if v.enabled]
            return enabled_versions[0].version if enabled_versions else "default"

        # 归一化权重
        rand = random.random() * total_weight
        cumulative_weight = 0.0

        for version_info in self._versions.values():
            if not version_info.enabled:
                continue

            cumulative_weight += version_info.weight
            if rand <= cumulative_weight:
                return version_info.version

        # 默认返回第一个版本
        return list(self._versions.keys())[0]

    def _route_by_user_id(self, user_id: str) -> str:
        """基于用户ID路由（一致性哈希）"""
        # 简单的用户ID哈希分配
        user_hash = hash(user_id) % 100
        cumulative_weight = 0.0

        for version_info in self._versions.values():
            if not version_info.enabled:
                continue

            cumulative_weight += version_info.weight * 100
            if user_hash < cumulative_weight:
                return version_info.version

        return list(self._versions.keys())[0]

    def _route_by_random(self) -> str:
        """随机路由"""
        enabled_versions = [v.version for v in self._versions.values() if v.enabled]
        return random.choice(enabled_versions) if enabled_versions else "default"

    def record_request(self, version: str, response_time: float, success: bool):
        """记录请求"""
        if version not in self._metrics:
            return

        metrics = self._metrics[version]
        metrics.request_count += 1
        metrics.last_updated = time.time()

        if success:
            metrics.success_count += 1
        else:
            metrics.error_count += 1

        # 更新平均响应时间
        if metrics.request_count == 1:
            metrics.average_response_time = response_time
        else:
            # 指数移动平均
            alpha = 0.1
            metrics.average_response_time = (
                alpha * response_time +
                (1 - alpha) * metrics.average_response_time
            )

        # 更新错误率
        total_responses = metrics.success_count + metrics.error_count
        if total_responses > 0:
            metrics.error_rate = metrics.error_count / total_responses

    def get_metrics(self) -> Dict[str, DeploymentMetrics]:
        """获取所有指标"""
        return self._metrics.copy()

    def get_version_info(self) -> Dict[str, DeploymentVersion]:
        """获取版本信息"""
        return self._versions.copy()


class CanaryDeploymentManager:
    """
    灰度发布管理器

    管理多版本部署、流量控制、监控和自动回滚
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._router = TrafficRouter()
        self._current_strategy = DeploymentStrategy.PERCENTAGE
        self._monitors: List[Callable] = []
        self._auto_rollback_enabled = True
        self._rollback_thresholds = {
            "error_rate": 0.1,      # 错误率阈值
            "response_time": 5.0,   # 响应时间阈值（秒）
            "min_requests": 10      # 最少请求数才触发回滚
        }

    def add_version(self, version: str, name: str, initial_weight: float = 0.0):
        """添加部署版本"""
        deployment_version = DeploymentVersion(
            version=version,
            name=name,
            weight=initial_weight,
            enabled=True
        )
        self._router.add_version(deployment_version)

    def update_traffic_distribution(self, version_weights: Dict[str, float]):
        """更新流量分配"""
        total_weight = sum(version_weights.values())

        if abs(total_weight - 1.0) > 0.01:
            self.logger.warning(f"⚠️ 流量权重总和不为1.0: {total_weight}")

        for version, weight in version_weights.items():
            self._router.update_version_weight(version, weight)

        self.logger.info(f"✅ 更新流量分配: {version_weights}")

    def set_deployment_strategy(self, strategy: DeploymentStrategy):
        """设置部署策略"""
        self._current_strategy = strategy
        self.logger.info(f"✅ 设置部署策略: {strategy.value}")

    def route_request(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> TrafficAllocation:
        """路由请求"""
        return self._router.route_traffic(
            user_id=user_id,
            session_id=session_id,
            strategy=self._current_strategy
        )

    def record_request_result(
        self,
        allocation: TrafficAllocation,
        response_time: float,
        success: bool
    ):
        """记录请求结果"""
        self._router.record_request(allocation.version, response_time, success)

        # 检查是否需要自动回滚
        if self._auto_rollback_enabled:
            self._check_auto_rollback(allocation.version)

        # 触发监控回调
        self._trigger_monitors(allocation, response_time, success)

    def add_monitor(self, monitor_callback: Callable):
        """添加监控回调"""
        self._monitors.append(monitor_callback)

    def remove_monitor(self, monitor_callback: Callable):
        """移除监控回调"""
        if monitor_callback in self._monitors:
            self._monitors.remove(monitor_callback)

    def _check_auto_rollback(self, version: str):
        """检查是否需要自动回滚"""
        metrics = self._router.get_metrics().get(version)
        if not metrics:
            return

        # 检查是否满足最小请求数
        if metrics.request_count < self._rollback_thresholds["min_requests"]:
            return

        # 检查错误率
        if metrics.error_rate > self._rollback_thresholds["error_rate"]:
            self.logger.warning(f"⚠️ 版本 {version} 错误率过高 ({metrics.error_rate:.1%})，触发自动回滚")
            self._trigger_rollback(version, f"错误率过高: {metrics.error_rate:.1%}")

        # 检查响应时间
        if metrics.average_response_time > self._rollback_thresholds["response_time"]:
            self.logger.warning(f"⚠️ 版本 {version} 响应时间过长 ({metrics.average_response_time:.2f}s)，触发自动回滚")
            self._trigger_rollback(version, f"响应时间过长: {metrics.average_response_time:.2f}s")

    def _trigger_rollback(self, version: str, reason: str):
        """触发回滚"""
        self.logger.error(f"🔄 触发自动回滚: 版本 {version}, 原因: {reason}")

        # 将有问题的版本权重设为0
        self._router.update_version_weight(version, 0.0)

        # 将流量分配给其他版本
        other_versions = [v for v in self._router._versions.keys() if v != version]
        if other_versions:
            weight_per_version = 1.0 / len(other_versions)
            for v in other_versions:
                self._router.update_version_weight(v, weight_per_version)

            self.logger.info(f"✅ 流量已重新分配给其他版本: {other_versions}")

    def _trigger_monitors(
        self,
        allocation: TrafficAllocation,
        response_time: float,
        success: bool
    ):
        """触发监控回调"""
        for monitor in self._monitors:
            try:
                asyncio.create_task(
                    monitor(allocation, response_time, success)
                )
            except Exception as e:
                self.logger.debug(f"监控回调异常: {e}")

    def get_deployment_status(self) -> Dict[str, Any]:
        """获取部署状态"""
        metrics = self._router.get_metrics()
        versions = self._router.get_version_info()

        return {
            "strategy": self._current_strategy.value,
            "versions": {
                version: {
                    "name": info.name,
                    "weight": info.weight,
                    "enabled": info.enabled,
                    "metrics": {
                        "requests": metrics.get(version, DeploymentMetrics(version)).request_count,
                        "success_rate": 1.0 - metrics.get(version, DeploymentMetrics(version)).error_rate,
                        "avg_response_time": metrics.get(version, DeploymentMetrics(version)).average_response_time
                    } if version in metrics else {}
                }
                for version, info in versions.items()
            },
            "total_requests": sum(m.request_count for m in metrics.values()),
            "auto_rollback": self._auto_rollback_enabled,
            "rollback_thresholds": self._rollback_thresholds
        }

    async def gradual_rollout(
        self,
        new_version: str,
        target_weight: float = 1.0,
        step_size: float = 0.1,
        step_interval: float = 60.0
    ):
        """
        渐进式发布

        Args:
            new_version: 新版本
            target_weight: 目标权重
            step_size: 每次增加的权重
            step_interval: 步骤间隔（秒）
        """
        self.logger.info(f"🚀 开始渐进式发布: {new_version}")

        current_weight = 0.0

        while current_weight < target_weight:
            current_weight = min(current_weight + step_size, target_weight)

            # 更新权重
            version_weights = {new_version: current_weight}

            # 为其他版本分配剩余权重
            remaining_weight = 1.0 - current_weight
            other_versions = [v for v in self._router._versions.keys() if v != new_version]

            if other_versions:
                weight_per_version = remaining_weight / len(other_versions)
                for v in other_versions:
                    version_weights[v] = weight_per_version

            self.update_traffic_distribution(version_weights)

            self.logger.info(f"📈 流量分配更新: {new_version} = {current_weight:.1%}")

            # 等待一段时间观察效果
            await asyncio.sleep(step_interval)

            # 检查是否有问题需要停止发布
            metrics = self._router.get_metrics().get(new_version)
            if metrics and metrics.request_count >= self._rollback_thresholds["min_requests"]:
                error_rate = metrics.error_rate
                avg_response_time = metrics.average_response_time

                if (error_rate > self._rollback_thresholds["error_rate"] or
                    avg_response_time > self._rollback_thresholds["response_time"]):
                    self.logger.error(f"❌ 渐进式发布检测到问题，中止发布")
                    self._trigger_rollback(new_version, "渐进式发布检测到性能问题")
                    return

        self.logger.info(f"✅ 渐进式发布完成: {new_version} = {target_weight:.1%}")


# 全局灰度发布管理器实例
_canary_manager_instance = None

def get_canary_deployment_manager() -> CanaryDeploymentManager:
    """获取灰度发布管理器实例"""
    global _canary_manager_instance
    if _canary_manager_instance is None:
        _canary_manager_instance = CanaryDeploymentManager()
    return _canary_manager_instance
