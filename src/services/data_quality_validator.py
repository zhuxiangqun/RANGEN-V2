"""
数据质量评估和验证机制
确保修复措施的有效性，提供数据质量监控和预警功能
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import statistics
from collections import defaultdict, Counter
import re

from .realtime_data_integration import BuildingData, DataSourceType
from .regional_data_integration import RegionalDataIntegrator, Region
from .numeric_precision_processor import PreciseNumber, NumericUnit, get_numeric_processor

logger = logging.getLogger(__name__)

class QualityIssueType(Enum):
    """质量问题类型"""
    MISSING_HEIGHT = "missing_height"
    MISSING_LOCATION = "missing_location"
    PRECISION_LOSS = "precision_loss"
    OUTDATED_DATA = "outdated_data"
    INCONSISTENT_UNITS = "inconsistent_units"
    DUPLICATE_DATA = "duplicate_data"
    LOW_CONFIDENCE = "low_confidence"
    REGIONAL_IMBALANCE = "regional_imbalance"
    DATA_SOURCE_UNRELIABLE = "data_source_unreliable"

class QualityLevel(Enum):
    """质量等级"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"

@dataclass
class QualityIssue:
    """质量问题"""
    issue_type: QualityIssueType
    severity: QualityLevel
    description: str
    affected_items: List[str] = field(default_factory=list)
    suggestion: Optional[str] = None
    detected_at: datetime = field(default_factory=datetime.now)
    auto_fixable: bool = False

@dataclass
class QualityMetrics:
    """质量指标"""
    overall_score: float
    completeness_score: float
    accuracy_score: float
    consistency_score: float
    timeliness_score: float
    regional_balance_score: float
    total_issues: int
    critical_issues: int
    auto_fixable_issues: int
    
    def get_quality_level(self) -> QualityLevel:
        """获取总体质量等级"""
        if self.overall_score >= 0.9:
            return QualityLevel.EXCELLENT
        elif self.overall_score >= 0.75:
            return QualityLevel.GOOD
        elif self.overall_score >= 0.6:
            return QualityLevel.FAIR
        elif self.overall_score >= 0.4:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL

class DataQualityValidator:
    """数据质量验证器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.numeric_processor = get_numeric_processor()
        self.quality_thresholds = {
            'min_completeness': self.config.get('min_completeness', 0.8),
            'min_accuracy': self.config.get('min_accuracy', 0.85),
            'min_consistency': self.config.get('min_consistency', 0.9),
            'min_timeliness': self.config.get('min_timeliness', 0.7),
            'min_regional_balance': self.config.get('min_regional_balance', 0.6)
        }
        self.data_freshness_hours = self.config.get('data_freshness_hours', 24)
        
    def validate_building_data(self, buildings: List[BuildingData]) -> List[QualityIssue]:
        """验证建筑数据质量"""
        issues = []
        
        # 检查完整性
        issues.extend(self._check_completeness(buildings))
        
        # 检查精确度
        issues.extend(self._check_precision(buildings))
        
        # 检查一致性
        issues.extend(self._check_consistency(buildings))
        
        # 检查时效性
        issues.extend(self._check_timeliness(buildings))
        
        # 检查重复数据
        issues.extend(self._check_duplicates(buildings))
        
        # 检查置信度
        issues.extend(self._check_confidence(buildings))
        
        return issues
    
    def _check_completeness(self, buildings: List[BuildingData]) -> List[QualityIssue]:
        """检查数据完整性"""
        issues = []
        
        # 检查缺失高度数据
        buildings_without_height = [
            b for b in buildings 
            if b.height_feet is None and b.height_meters is None
        ]
        
        if buildings_without_height:
            missing_ratio = len(buildings_without_height) / len(buildings)
            severity = self._calculate_severity(missing_ratio, inverse=True)
            
            issue = QualityIssue(
                issue_type=QualityIssueType.MISSING_HEIGHT,
                severity=severity,
                description=f"{len(buildings_without_height)} 栋建筑缺失高度数据 ({missing_ratio:.1%})",
                affected_items=[b.building_id for b in buildings_without_height],
                suggestion="补充高度测量数据或从其他数据源获取"
            )
            issues.append(issue)
        
        # 检查缺失位置信息
        buildings_without_location = [
            b for b in buildings 
            if not b.city or not b.country
        ]
        
        if buildings_without_location:
            missing_ratio = len(buildings_without_location) / len(buildings)
            severity = self._calculate_severity(missing_ratio, inverse=True)
            
            issue = QualityIssue(
                issue_type=QualityIssueType.MISSING_LOCATION,
                severity=severity,
                description=f"{len(buildings_without_location)} 栋建筑缺失位置信息 ({missing_ratio:.1%})",
                affected_items=[b.building_id for b in buildings_without_location],
                suggestion="补充城市和国家信息"
            )
            issues.append(issue)
        
        return issues
    
    def _check_precision(self, buildings: List[BuildingData]) -> List[QualityIssue]:
        """检查数据精确度"""
        issues = []
        
        precision_issues = []
        
        for building in buildings:
            # 检查高度值的精确度
            if building.height_feet is not None:
                # 检查是否为可疑的整数（可能存在精度损失）
                if building.height_feet == int(building.height_feet):
                    # 进一步检查原始数据
                    if building.height_meters is not None:
                        # 反向转换验证
                        calculated_feet = building.height_meters * 3.28084
                        if abs(calculated_feet - building.height_feet) > 0.5:
                            precision_issues.append(building.building_id)
                
                # 检查异常值
                if building.height_feet < 0 or building.height_feet > 10000:
                    precision_issues.append(building.building_id)
        
        if precision_issues:
            issue = QualityIssue(
                issue_type=QualityIssueType.PRECISION_LOSS,
                severity=QualityLevel.POOR,
                description=f"检测到 {len(precision_issues)} 栋建筑的精确度问题",
                affected_items=precision_issues,
                suggestion="验证测量数据，检查单位转换是否正确"
            )
            issues.append(issue)
        
        return issues
    
    def _check_consistency(self, buildings: List[BuildingData]) -> List[QualityIssue]:
        """检查数据一致性"""
        issues = []
        
        # 检查单位一致性
        inconsistent_buildings = []
        
        for building in buildings:
            if building.height_feet is not None and building.height_meters is not None:
                # 验证米英尺转换的一致性
                expected_feet = building.height_meters * 3.28084
                expected_meters = building.height_feet / 3.28084
                
                feet_diff = abs(building.height_feet - expected_feet)
                meters_diff = abs(building.height_meters - expected_meters)
                
                if feet_diff > 0.1 or meters_diff > 0.03:  # 允许小的舍入误差
                    inconsistent_buildings.append(building.building_id)
        
        if inconsistent_buildings:
            issue = QualityIssue(
                issue_type=QualityIssueType.INCONSISTENT_UNITS,
                severity=QualityLevel.POOR,
                description=f"{len(inconsistent_buildings)} 栋建筑的单位转换不一致",
                affected_items=inconsistent_buildings,
                suggestion="统一单位转换标准，重新计算不一致的数据"
            )
            issues.append(issue)
        
        return issues
    
    def _check_timeliness(self, buildings: List[BuildingData]) -> List[QualityIssue]:
        """检查数据时效性"""
        issues = []
        
        if not buildings:
            return issues
        
        now = datetime.now()
        outdated_threshold = timedelta(hours=self.data_freshness_hours)
        
        outdated_buildings = [
            b for b in buildings 
            if b.last_updated and (now - b.last_updated) > outdated_threshold
        ]
        
        if outdated_buildings:
            outdated_ratio = len(outdated_buildings) / len(buildings)
            severity = self._calculate_severity(outdated_ratio, inverse=True)
            
            issue = QualityIssue(
                issue_type=QualityIssueType.OUTDATED_DATA,
                severity=severity,
                description=f"{len(outdated_buildings)} 栋建筑的数据已过期 ({outdated_ratio:.1%})",
                affected_items=[b.building_id for b in outdated_buildings],
                suggestion="更新数据源，启用实时数据同步"
            )
            issues.append(issue)
        
        return issues
    
    def _check_duplicates(self, buildings: List[BuildingData]) -> List[QualityIssue]:
        """检查重复数据"""
        issues = []
        
        # 生成唯一标识（名称+城市+国家）
        building_signatures = defaultdict(list)
        
        for building in buildings:
            signature = f"{building.name}_{building.city}_{building.country}".lower()
            building_signatures[signature].append(building)
        
        duplicates = []
        for signature, building_list in building_signatures.items():
            if len(building_list) > 1:
                duplicates.extend([b.building_id for b in building_list])
        
        if duplicates:
            issue = QualityIssue(
                issue_type=QualityIssueType.DUPLICATE_DATA,
                severity=QualityLevel.FAIR,
                description=f"发现 {len(duplicates)} 条重复建筑数据",
                affected_items=duplicates,
                suggestion="合并重复条目，保留最完整的数据",
                auto_fixable=True
            )
            issues.append(issue)
        
        return issues
    
    def _check_confidence(self, buildings: List[BuildingData]) -> List[QualityIssue]:
        """检查数据置信度"""
        issues = []
        
        low_confidence_buildings = [
            b for b in buildings 
            if b.confidence_score is not None and b.confidence_score < 0.7
        ]
        
        if low_confidence_buildings:
            low_conf_ratio = len(low_confidence_buildings) / len(buildings)
            severity = self._calculate_severity(low_conf_ratio, inverse=True)
            
            issue = QualityIssue(
                issue_type=QualityIssueType.LOW_CONFIDENCE,
                severity=severity,
                description=f"{len(low_confidence_buildings)} 栋建筑的置信度较低 ({low_conf_ratio:.1%})",
                affected_items=[b.building_id for b in low_confidence_buildings],
                suggestion="从更可靠的数据源获取数据，或进行人工验证"
            )
            issues.append(issue)
        
        return issues
    
    def _calculate_severity(self, ratio: float, inverse: bool = False) -> QualityLevel:
        """根据比例计算严重程度"""
        if inverse:
            ratio = 1 - ratio
        
        if ratio >= 0.9:
            return QualityLevel.EXCELLENT
        elif ratio >= 0.75:
            return QualityLevel.GOOD
        elif ratio >= 0.6:
            return QualityLevel.FAIR
        elif ratio >= 0.4:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL
    
    def validate_regional_balance(self, regional_integrator: RegionalDataIntegrator) -> List[QualityIssue]:
        """验证区域平衡性"""
        issues = []
        
        coverage_summary = regional_integrator.get_regional_coverage_summary()
        
        # 计算区域覆盖率差异
        coverage_rates = [
            stats['coverage_rate'] for stats in coverage_summary.values()
        ]
        
        if coverage_rates:
            max_coverage = max(coverage_rates)
            min_coverage = min(coverage_rates)
            coverage_gap = max_coverage - min_coverage
            
            # 如果覆盖率差异过大
            if coverage_gap > 0.5:
                underrepresented_regions = [
                    region for region, stats in coverage_summary.items()
                    if stats['coverage_rate'] < 0.3
                ]
                
                issue = QualityIssue(
                    issue_type=QualityIssueType.REGIONAL_IMBALANCE,
                    severity=QualityLevel.FAIR,
                    description=f"区域数据不平衡，覆盖率差异达 {coverage_gap:.1%}",
                    affected_items=underrepresented_regions,
                    suggestion=f"加强以下地区的数据收集：{', '.join(underrepresented_regions)}"
                )
                issues.append(issue)
        
        return issues
    
    def calculate_quality_metrics(
        self, 
        buildings: List[BuildingData], 
        issues: List[QualityIssue]
    ) -> QualityMetrics:
        """计算质量指标"""
        if not buildings:
            return QualityMetrics(
                overall_score=0.0, completeness_score=0.0, accuracy_score=0.0,
                consistency_score=0.0, timeliness_score=0.0, regional_balance_score=0.0,
                total_issues=0, critical_issues=0, auto_fixable_issues=0
            )
        
        # 完整性分数
        buildings_with_height = len([
            b for b in buildings 
            if b.height_feet is not None or b.height_meters is not None
        ])
        buildings_with_location = len([
            b for b in buildings 
            if b.city and b.country
        ])
        
        completeness_score = (
            (buildings_with_height / len(buildings) + 
            buildings_with_location / len(buildings))
        ) / 2
        
        # 精确度分数（基于精确度问题）
        precision_issues = len([
            i for i in issues 
            if i.issue_type == QualityIssueType.PRECISION_LOSS
        ])
        accuracy_score = max(1.0 - (precision_issues / len(buildings)), 0.0)
        
        # 一致性分数
        consistency_issues = len([
            i for i in issues 
            if i.issue_type == QualityIssueType.INCONSISTENT_UNITS
        ])
        consistency_score = max(1.0 - (consistency_issues / len(buildings)), 0.0)
        
        # 时效性分数
        now = datetime.now()
        outdated_threshold = timedelta(hours=self.data_freshness_hours)
        fresh_buildings = len([
            b for b in buildings 
            if not b.last_updated or (now - b.last_updated) <= outdated_threshold
        ])
        timeliness_score = fresh_buildings / len(buildings)
        
        # 区域平衡分数（需要RegionalDataIntegrator的上下文）
        regional_balance_score = 0.7  # 默认值，需要更复杂的计算
        
        # 总体分数
        overall_score = (
            completeness_score * 0.3 +
            accuracy_score * 0.25 +
            consistency_score * 0.2 +
            timeliness_score * 0.15 +
            regional_balance_score * 0.1
        )
        
        # 问题统计
        critical_issues = len([i for i in issues if i.severity == QualityLevel.CRITICAL])
        auto_fixable_issues = len([i for i in issues if i.auto_fixable])
        
        return QualityMetrics(
            overall_score=overall_score,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            consistency_score=consistency_score,
            timeliness_score=timeliness_score,
            regional_balance_score=regional_balance_score,
            total_issues=len(issues),
            critical_issues=critical_issues,
            auto_fixable_issues=auto_fixable_issues
        )

class DataQualityMonitor:
    """数据质量监控器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.validator = DataQualityValidator(config)
        self.monitoring_interval = self.config.get('monitoring_interval_minutes', 60)
        self.alert_thresholds = {
            'min_overall_score': self.config.get('min_overall_score', 0.7),
            'max_critical_issues': self.config.get('max_critical_issues', 5),
            'max_outdated_ratio': self.config.get('max_outdated_ratio', 0.2)
        }
        self.quality_history = []
        
    async def monitor_data_quality(
        self, 
        buildings: List[BuildingData],
        regional_integrator: Optional[RegionalDataIntegrator] = None
    ) -> Dict[str, Any]:
        """监控数据质量"""
        logger.info("开始数据质量监控")
        
        # 执行验证
        issues = self.validator.validate_building_data(buildings)
        
        if regional_integrator:
            regional_issues = self.validator.validate_regional_balance(regional_integrator)
            issues.extend(regional_issues)
        
        # 计算指标
        metrics = self.validator.calculate_quality_metrics(buildings, issues)
        
        # 生成报告
        report = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {
                'overall_score': metrics.overall_score,
                'quality_level': metrics.get_quality_level().value,
                'completeness_score': metrics.completeness_score,
                'accuracy_score': metrics.accuracy_score,
                'consistency_score': metrics.consistency_score,
                'timeliness_score': metrics.timeliness_score,
                'regional_balance_score': metrics.regional_balance_score
            },
            'issues_summary': {
                'total_issues': metrics.total_issues,
                'critical_issues': metrics.critical_issues,
                'auto_fixable_issues': metrics.auto_fixable_issues,
                'issues_by_type': self._group_issues_by_type(issues),
                'issues_by_severity': self._group_issues_by_severity(issues)
            },
            'detailed_issues': [self._serialize_issue(issue) for issue in issues],
            'recommendations': self._generate_recommendations(metrics, issues)
        }
        
        # 检查是否需要告警
        alerts = self._check_alert_conditions(metrics, issues)
        if alerts:
            report['alerts'] = alerts
            await self._send_alerts(alerts)
        
        # 保存历史记录
        self.quality_history.append({
            'timestamp': datetime.now(),
            'metrics': metrics,
            'issues_count': len(issues)
        })
        
        # 保持历史记录不超过100条
        if len(self.quality_history) > 100:
            self.quality_history = self.quality_history[-100:]
        
        logger.info(f"数据质量监控完成，总体评分: {metrics.overall_score:.2f}")
        return report
    
    def _group_issues_by_type(self, issues: List[QualityIssue]) -> Dict[str, int]:
        """按类型分组问题"""
        groups = Counter([issue.issue_type.value for issue in issues])
        return dict(groups)
    
    def _group_issues_by_severity(self, issues: List[QualityIssue]) -> Dict[str, int]:
        """按严重程度分组问题"""
        groups = Counter([issue.severity.value for issue in issues])
        return dict(groups)
    
    def _serialize_issue(self, issue: QualityIssue) -> Dict[str, Any]:
        """序列化问题对象"""
        return {
            'type': issue.issue_type.value,
            'severity': issue.severity.value,
            'description': issue.description,
            'affected_count': len(issue.affected_items),
            'affected_items': issue.affected_items[:10],  # 限制显示数量
            'suggestion': issue.suggestion,
            'auto_fixable': issue.auto_fixable,
            'detected_at': issue.detected_at.isoformat()
        }
    
    def _generate_recommendations(
        self, 
        metrics: QualityMetrics, 
        issues: List[QualityIssue]
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于指标的建议
        if metrics.completeness_score < 0.8:
            recommendations.append("提高数据完整性：补充缺失的高度和位置信息")
        
        if metrics.accuracy_score < 0.8:
            recommendations.append("改善数据精确度：验证测量值，检查单位转换")
        
        if metrics.consistency_score < 0.9:
            recommendations.append("增强数据一致性：统一标准和格式")
        
        if metrics.timeliness_score < 0.7:
            recommendations.append("更新数据时效性：启用实时数据同步机制")
        
        # 基于问题类型的建议
        issue_types = set(issue.issue_type for issue in issues)
        
        if QualityIssueType.DUPLICATE_DATA in issue_types:
            recommendations.append("清理重复数据：实施去重算法")
        
        if QualityIssueType.LOW_CONFIDENCE in issue_types:
            recommendations.append("提高数据源质量：使用更可靠的权威数据源")
        
        if QualityIssueType.REGIONAL_IMBALANCE in issue_types:
            recommendations.append("平衡区域覆盖：加强数据不足地区的收集")
        
        # 基于可自动修复问题的建议
        auto_fixable_count = len([i for i in issues if i.auto_fixable])
        if auto_fixable_count > 0:
            recommendations.append(f"可自动修复 {auto_fixable_count} 个问题，建议启用自动修复")
        
        return recommendations
    
    def _check_alert_conditions(
        self, 
        metrics: QualityMetrics, 
        issues: List[QualityIssue]
    ) -> List[str]:
        """检查告警条件"""
        alerts = []
        
        if metrics.overall_score < self.alert_thresholds['min_overall_score']:
            alerts.append(f"数据质量评分过低: {metrics.overall_score:.2f}")
        
        if metrics.critical_issues > self.alert_thresholds['max_critical_issues']:
            alerts.append(f"严重问题数量过多: {metrics.critical_issues}")
        
        outdated_issues = [i for i in issues if i.issue_type == QualityIssueType.OUTDATED_DATA]
        if len(outdated_issues) > len(issues) * self.alert_thresholds['max_outdated_ratio']:
            alerts.append("数据过期问题严重")
        
        return alerts
    
    async def _send_alerts(self, alerts: List[str]):
        """发送告警"""
        logger.warning(f"数据质量告警: {'; '.join(alerts)}")
        # 这里可以集成实际的告警系统（邮件、短信、webhook等）
    
    def get_quality_trend(self, days: int = 7) -> Dict[str, Any]:
        """获取质量趋势"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_history = [
            record for record in self.quality_history
            if record['timestamp'] >= cutoff_date
        ]
        
        if len(recent_history) < 2:
            return {'trend': 'insufficient_data'}
        
        # 计算趋势
        first_score = recent_history[0]['metrics'].overall_score
        latest_score = recent_history[-1]['metrics'].overall_score
        
        if latest_score > first_score + 0.05:
            trend = 'improving'
        elif latest_score < first_score - 0.05:
            trend = 'declining'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'period_days': days,
            'data_points': len(recent_history),
            'start_score': first_score,
            'end_score': latest_score,
            'score_change': latest_score - first_score
        }

# 工厂函数
def create_data_quality_monitor(config: Optional[Dict[str, Any]] = None) -> DataQualityMonitor:
    """创建数据质量监控器实例"""
    return DataQualityMonitor(config)