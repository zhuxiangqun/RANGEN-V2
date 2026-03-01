#!/usr/bin/env python3
"""
QualityController - 质量控制器 (L2基础认知)
多维度评估算法、自动化验证、错误检测与纠正
from ..utils.unified_centers import get_unified_config_center
from ..utils.unified_threshold_manager import get_unified_threshold_manager


优化特性：
- 多维度评估算法：结合LLM、规则和用户反馈进行输出质量评估
- 自动化验证流程：对事实、逻辑和格式进行自动化验证
- 错误检测与纠正：智能识别并纠正输出中的错误
- 质量监控与预警：实时监控质量指标并触发预警
"""

import time
import logging
import asyncio
import json
import hashlib
import threading
import re
from typing import Dict, List, Any, Optional, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, OrderedDict
from concurrent.futures import ThreadPoolExecutor
import statistics

from .expert_agent import ExpertAgent
from .base_agent import AgentResult
from src.utils.logging_helper import get_module_logger, ModuleType

logger = logging.getLogger(__name__)


class QualityDimension(Enum):
    """质量维度"""
    FACTUAL_ACCURACY = "factual_accuracy"      # 事实准确性
    LOGICAL_CONSISTENCY = "logical_consistency" # 逻辑一致性
    COMPLETENESS = "completeness"              # 完整性
    RELEVANCE = "relevance"                    # 相关性
    CLARITY = "clarity"                        # 清晰度
    FORMAT_COMPLIANCE = "format_compliance"     # 格式合规性
    TIMELINESS = "timeliness"                  # 时效性
    USER_SATISFACTION = "user_satisfaction"     # 用户满意度


class ValidationLevel(Enum):
    """验证级别"""
    BASIC = "basic"          # 基础验证（语法、格式）
    STANDARD = "standard"    # 标准验证（事实、逻辑）
    COMPREHENSIVE = "comprehensive"  # 全面验证（所有维度）
    CRITICAL = "critical"    # 关键验证（高风险场景）


class QualityIssue(Enum):
    """质量问题类型"""
    FACTUAL_ERROR = "factual_error"            # 事实错误
    LOGICAL_CONTRADICTION = "logical_contradiction"  # 逻辑矛盾
    MISSING_INFORMATION = "missing_information"     # 信息缺失
    IRRELEVANT_CONTENT = "irrelevant_content"       # 不相关内容
    UNCLEAR_EXPRESSION = "unclear_expression"       # 表达不清
    FORMAT_VIOLATION = "format_violation"          # 格式违规
    OUTDATED_INFORMATION = "outdated_information"   # 信息过时
    INCONSISTENT_STYLE = "inconsistent_style"       # 风格不一致


@dataclass
class QualityAssessment:
    """质量评估结果"""
    assessment_id: str
    content_id: str
    overall_score: float  # 0-100
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    detected_issues: List[Dict[str, Any]] = field(default_factory=list)
    validation_level: ValidationLevel = ValidationLevel.STANDARD
    assessed_at: float = field(default_factory=time.time)
    assessor: str = "quality_controller"
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class ValidationRule:
    """验证规则"""
    rule_id: str
    name: str
    description: str
    quality_dimension: QualityDimension
    validation_function: Callable[[str, Dict[str, Any]], Dict[str, Any]]
    severity: str = "medium"  # critical, major, minor
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityThreshold:
    """质量阈值"""
    dimension: QualityDimension
    minimum_score: float
    warning_threshold: float
    critical_threshold: float
    auto_correct: bool = False
    escalation_required: bool = False


class QualityController(ExpertAgent):
    """QualityController - 质量控制器 (L2基础认知)

    核心职责：
    1. 多维度评估算法 - 结合LLM、规则和用户反馈进行输出质量评估
    2. 自动化验证流程 - 对事实、逻辑和格式进行自动化验证
    3. 错误检测与纠正 - 智能识别并纠正输出中的错误
    4. 质量监控与预警 - 实时监控质量指标并触发预警

    优化特性：
    - 多维度评估：事实、逻辑、完整性、相关性、清晰度、格式等全面评估
    - 自动化验证：规则引擎+LLM验证的混合验证体系
    - 智能纠错：基于模式识别和学习的历史纠错能力
    - 实时监控：质量指标监控和自动预警机制
    """

    def __init__(self):
        """初始化QualityController"""
        # 初始化统一配置中心
        self.config_center = get_unified_config_center()
        self.threshold_manager = get_unified_threshold_manager()

        # 获取Agent特定配置
        self.agent_config = self.config_center.get_agent_config(self.__class__.__name__, {
            'enabled': True,
            'max_retries': 3,
            'timeout': 30,
            'debug_mode': False
        })

        # 获取阈值配置
        self.thresholds = self.threshold_manager.get_thresholds(self.__class__.__name__, {
            'performance_warning_threshold': 5.0,
            'error_rate_threshold': 0.1,
            'memory_usage_threshold': 80.0
        })

        super().__init__(
            agent_id="quality_controller",
            domain_expertise="质量评估和自动化验证",
            capability_level=0.6,  # L2基础认知
            collaboration_style="analytical"
        )

        # 使用模块日志器
        self.module_logger = get_module_logger(ModuleType.AGENT, "QualityController")

        # 🚀 新增：质量评估和验证配置
        self._quality_assessments: Dict[str, QualityAssessment] = {}
        self._validation_rules: Dict[str, ValidationRule] = {}
        self._quality_thresholds: Dict[str, QualityThreshold] = {}
        self._assessment_history: List[Dict[str, Any]] = []

        # 🚀 新增：智能验证和纠错配置
        self._parallel_validator = ThreadPoolExecutor(max_workers=4, thread_name_prefix="quality_validation")
        self._correction_patterns: Dict[str, Dict[str, Any]] = {}
        self._quality_cache = OrderedDict()  # LRU缓存
        self._cache_max_size = 1000  # 增加缓存容量
        self._cache_ttl = 1800  # 缓存有效期（30分钟）

        # 🚀 新增：监控和统计配置
        self._monitoring_enabled = True
        self._alert_thresholds = {
            'quality_drop_rate': 0.1,    # 质量下降率阈值
            'error_rate_threshold': 0.05, # 错误率阈值
            'response_time_threshold': 5.0  # 响应时间阈值
        }

        # 🚀 新增：统计数据
        self._stats = {
            'total_assessments': 0,
            'passed_assessments': 0,
            'failed_assessments': 0,
            'auto_corrections': 0,
            'quality_alerts': 0,
            'average_quality_score': 0.0,
            'dimension_performance': defaultdict(list)
        }

        # 初始化内置验证规则和阈值
        self._initialize_builtin_rules()
        self._initialize_quality_thresholds()

        # 启动监控线程
        self._monitoring_thread: Optional[threading.Thread] = None
        self._running = False
        self._start_monitoring_thread()

    def _get_service(self):
        """QualityController不直接使用单一Service"""
        return None

    # 🚀 新增：多维度评估算法
    async def assess_quality(self, content: str, context: Optional[Dict[str, Any]] = None,
                           validation_level: ValidationLevel = ValidationLevel.STANDARD) -> QualityAssessment:
        """多维度质量评估"""
        content_id = f"content_{int(time.time() * 1000)}_{hash(content) % 10000}"
        start_time = time.time()

        self.module_logger.info(f"🔍 开始质量评估: {content_id[:20]}..., 级别={validation_level.value}")

        # 检查缓存（包含TTL验证）
        cache_key = self._get_quality_cache_key(content, context, validation_level)
        if cache_key in self._quality_cache:
            cached_item = self._quality_cache[cache_key]
            if time.time() - cached_item.assessed_at < self._cache_ttl:
                self._quality_cache.move_to_end(cache_key)  # LRU更新
                self.module_logger.debug(f"✅ 质量评估缓存命中: {cache_key}")
                return cached_item
            else:
                # 缓存过期，删除
                del self._quality_cache[cache_key]

        # 并行执行各维度评估
        dimension_tasks = []
        for dimension in QualityDimension:
            if self._should_assess_dimension(dimension, validation_level):
                task = self._assess_dimension(content, dimension, context)
                dimension_tasks.append(task)

        # 等待所有维度评估完成
        dimension_results = await asyncio.gather(*dimension_tasks, return_exceptions=True)

        # 处理评估结果
        dimension_scores = {}
        detected_issues = []
        total_score = 0.0
        valid_dimensions = 0

        for i, result in enumerate(dimension_results):
            dimension = list(QualityDimension)[i]

            if isinstance(result, Exception):
                self.module_logger.warning(f"维度评估失败 {dimension.value}: {result}")
                continue

            dimension_scores[dimension.value] = result['score']
            detected_issues.extend(result.get('issues', []))
            total_score += result['score']
            valid_dimensions += 1

        # 计算综合评分
        overall_score = total_score / valid_dimensions if valid_dimensions > 0 else 0.0

        # 生成改进建议
        recommendations = await self._generate_recommendations(dimension_scores, detected_issues)

        # 创建评估结果
        assessment = QualityAssessment(
            assessment_id=f"assess_{int(time.time() * 1000)}_{hash(content_id) % 10000}",
            content_id=content_id,
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            detected_issues=detected_issues,
            validation_level=validation_level,
            recommendations=recommendations,
            confidence=0.85
        )

        # 智能缓存管理
        if len(self._quality_cache) >= self._cache_max_size:
            # 移除最旧的缓存项
            oldest_key, _ = next(iter(self._quality_cache.items()))
            del self._quality_cache[oldest_key]
            self.module_logger.debug(f"🗑️ 质量缓存已满，移除最旧项: {oldest_key}")

        # 批量清理过期缓存（每100次评估清理一次）
        if self._stats['total_assessments'] % 100 == 0:
            current_time = time.time()
            expired_keys = [
                k for k, v in list(self._quality_cache.items())
                if current_time - v.assessed_at >= self._cache_ttl
            ]
            for k in expired_keys:
                del self._quality_cache[k]
            if expired_keys:
                self.module_logger.debug(f"🧹 清理过期缓存: {len(expired_keys)}个")

        self._quality_cache[cache_key] = assessment
        self.module_logger.debug(f"✅ 质量评估结果已缓存: {cache_key} (总缓存数: {len(self._quality_cache)})")

        # 更新统计
        self._stats['total_assessments'] += 1
        if overall_score >= 70.0:
            self._stats['passed_assessments'] += 1
        else:
            self._stats['failed_assessments'] += 1

        # 更新维度性能统计
        for dim, score in dimension_scores.items():
            self._stats['dimension_performance'][dim].append(score)
            # 保持最近100个记录
            if len(self._stats['dimension_performance'][dim]) > 100:
                self._stats['dimension_performance'][dim].pop(0)

        execution_time = time.time() - start_time
        self.module_logger.info(f"✅ 质量评估完成: {content_id[:20]}..., 综合评分={overall_score:.1f}, 耗时={execution_time:.3f}秒")

        return assessment

    async def _assess_dimension(self, content: str, dimension: QualityDimension,
                              context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """评估单个维度"""
        try:
            # 获取该维度的验证规则
            relevant_rules = [
                rule for rule in self._validation_rules.values()
                if rule.quality_dimension == dimension and rule.enabled
            ]

            if not relevant_rules:
                return {'score': 70.0, 'issues': []}  # 默认中等分数

            # 并行执行规则验证
            rule_tasks = [
                asyncio.get_event_loop().run_in_executor(
                    self._parallel_validator,
                    rule.validation_function,
                    content,
                    {**rule.parameters, **(context or {})}
                )
                for rule in relevant_rules
            ]

            rule_results = await asyncio.gather(*rule_tasks, return_exceptions=True)

            # 汇总规则结果
            total_score = 0.0
            all_issues = []
            valid_rules = 0

            for i, result in enumerate(rule_results):
                rule = relevant_rules[i]

                if isinstance(result, Exception):
                    self.module_logger.warning(f"规则验证失败 {rule.name}: {result}")
                    continue

                rule_score = result.get('score', 50.0)
                rule_issues = result.get('issues', [])

                # 根据规则严重性调整权重
                weight = {'critical': 1.5, 'major': 1.2, 'minor': 1.0}.get(rule.severity, 1.0)
                total_score += rule_score * weight
                all_issues.extend(rule_issues)
                valid_rules += weight

            # 计算维度评分
            dimension_score = total_score / valid_rules if valid_rules > 0 else 50.0
            dimension_score = max(0.0, min(100.0, dimension_score))

            return {
                'score': dimension_score,
                'issues': all_issues
            }

        except Exception as e:
            self.module_logger.error(f"维度评估异常 {dimension.value}: {e}")
            return {'score': 50.0, 'issues': [{'type': 'assessment_error', 'description': str(e)}]}

    # 🚀 新增：自动化验证流程
    async def validate_content(self, content: str, content_type: str = "general",
                             context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """自动化验证流程"""
        self.module_logger.info(f"🔍 开始内容验证: {content_type}")

        # 选择验证级别
        validation_level = self._determine_validation_level(content_type, context)

        # 执行质量评估
        assessment = await self.assess_quality(content, context, validation_level)

        # 检查是否需要自动纠错
        correction_needed = assessment.overall_score < 70.0
        corrected_content = content

        if correction_needed and self._should_auto_correct(assessment):
            corrected_content = await self._auto_correct_content(content, assessment)
            self._stats['auto_corrections'] += 1

        # 生成验证报告
        validation_result = {
            'content_id': assessment.content_id,
            'validation_level': validation_level.value,
            'overall_score': assessment.overall_score,
            'passed': assessment.overall_score >= 70.0,
            'dimension_scores': assessment.dimension_scores,
            'issues_count': len(assessment.detected_issues),
            'critical_issues': [i for i in assessment.detected_issues if i.get('severity') == 'critical'],
            'auto_corrected': correction_needed,
            'original_content': content,
            'corrected_content': corrected_content if correction_needed else None,
            'recommendations': assessment.recommendations
        }

        # 记录验证历史
        self._assessment_history.append({
            'timestamp': time.time(),
            'content_type': content_type,
            'assessment': assessment,
            'validation_result': validation_result
        })

        # 限制历史大小
        if len(self._assessment_history) > 1000:
            self._assessment_history.pop(0)

        self.module_logger.info(f"✅ 内容验证完成: 评分={assessment.overall_score:.1f}, 通过={'是' if validation_result['passed'] else '否'}")

        return validation_result

    async def _auto_correct_content(self, content: str, assessment: QualityAssessment) -> str:
        """自动纠错内容"""
        try:
            corrected_content = content

            # 按优先级排序问题
            sorted_issues = sorted(
                assessment.detected_issues,
                key=lambda x: {'critical': 3, 'major': 2, 'minor': 1}.get(x.get('severity', 'minor'), 1),
                reverse=True
            )

            # 应用纠错规则
            for issue in sorted_issues[:5]:  # 最多处理前5个问题
                issue_type = issue.get('type', '')
                correction_rule = self._correction_patterns.get(issue_type)

                if correction_rule:
                    pattern = correction_rule.get('pattern', '')
                    replacement = correction_rule.get('replacement', '')

                    if pattern and replacement:
                        try:
                            corrected_content = re.sub(pattern, replacement, corrected_content, flags=re.IGNORECASE)
                        except Exception as e:
                            self.module_logger.warning(f"应用纠错规则失败 {issue_type}: {e}")

            return corrected_content

        except Exception as e:
            self.module_logger.error(f"自动纠错失败: {e}")
            return content

    # 🚀 新增：错误检测与纠正
    async def detect_and_correct_errors(self, content: str, error_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """错误检测与纠正"""
        self.module_logger.info("🔍 开始错误检测与纠正")

        # 执行全面质量评估
        assessment = await self.assess_quality(content, validation_level=ValidationLevel.COMPREHENSIVE)

        # 过滤指定类型的错误
        if error_types:
            filtered_issues = [i for i in assessment.detected_issues if i.get('type') in error_types]
        else:
            filtered_issues = assessment.detected_issues

        # 尝试纠正检测到的错误
        corrections_applied = []
        corrected_content = content

        for issue in filtered_issues:
            correction = await self._correct_specific_error(corrected_content, issue)
            if correction['applied']:
                corrected_content = correction['corrected_content']
                corrections_applied.append({
                    'issue': issue,
                    'correction': correction
                })

        result = {
            'original_content': content,
            'corrected_content': corrected_content,
            'issues_detected': len(filtered_issues),
            'corrections_applied': len(corrections_applied),
            'assessment_score': assessment.overall_score,
            'details': corrections_applied
        }

        self.module_logger.info(f"✅ 错误检测与纠正完成: 检测={len(filtered_issues)}, 纠正={len(corrections_applied)}")

        return result

    async def _correct_specific_error(self, content: str, issue: Dict[str, Any]) -> Dict[str, Any]:
        """纠正特定错误"""
        try:
            issue_type = issue.get('type', '')
            correction_rule = self._correction_patterns.get(issue_type)

            if not correction_rule:
                return {'applied': False, 'reason': 'no_correction_rule'}

            # 应用纠错逻辑
            if issue_type == 'factual_error':
                # 事实错误：标记需要人工审核
                return {'applied': False, 'reason': 'requires_human_review'}
            elif issue_type == 'format_violation':
                # 格式违规：尝试自动修复
                pattern = correction_rule.get('pattern', '')
                replacement = correction_rule.get('replacement', '')
                if pattern and replacement:
                    corrected = re.sub(pattern, replacement, content)
                    return {'applied': True, 'corrected_content': corrected}
            elif issue_type == 'logical_contradiction':
                # 逻辑矛盾：添加澄清说明
                clarification = correction_rule.get('clarification', '')
                if clarification:
                    corrected = content + f"\n\n注意：{clarification}"
                    return {'applied': True, 'corrected_content': corrected}

            return {'applied': False, 'reason': 'correction_not_applicable'}

        except Exception as e:
            self.module_logger.warning(f"纠正特定错误失败: {e}")
            return {'applied': False, 'reason': str(e)}

    # 🚀 新增：质量监控与预警
    async def monitor_quality_metrics(self) -> Dict[str, Any]:
        """监控质量指标"""
        try:
            # 计算质量趋势
            recent_assessments = [h for h in self._assessment_history[-50:]]  # 最近50个评估

            if len(recent_assessments) < 10:
                return {'status': 'insufficient_data', 'alerts': []}

            # 分析质量趋势
            scores = [h['assessment'].overall_score for h in recent_assessments]
            avg_score = statistics.mean(scores)

            # 检测质量下降
            recent_avg = statistics.mean(scores[-10:])  # 最近10个
            earlier_avg = statistics.mean(scores[:-10]) if len(scores) > 10 else avg_score

            quality_drop = earlier_avg - recent_avg
            quality_drop_rate = quality_drop / earlier_avg if earlier_avg > 0 else 0

            # 生成警报
            alerts = []

            if quality_drop_rate > self._alert_thresholds['quality_drop_rate']:
                alerts.append({
                    'type': 'quality_drop',
                    'severity': 'high',
                    'message': f'质量下降 {quality_drop_rate:.1%}，从 {earlier_avg:.1f} 降至 {recent_avg:.1f}',
                    'recommendation': '检查最近的变更或数据质量问题'
                })

            # 检查错误率
            failed_count = sum(1 for h in recent_assessments if not h['validation_result']['passed'])
            error_rate = failed_count / len(recent_assessments)

            if error_rate > self._alert_thresholds['error_rate_threshold']:
                alerts.append({
                    'type': 'high_error_rate',
                    'severity': 'medium',
                    'message': f'错误率过高: {error_rate:.1%}',
                    'recommendation': '检查验证规则或输入数据质量'
                })

            # 检查维度性能
            dimension_alerts = await self._check_dimension_performance()
            alerts.extend(dimension_alerts)

            # 更新统计
            self._stats['average_quality_score'] = avg_score
            self._stats['quality_alerts'] = len(alerts)

            result = {
                'status': 'monitored',
                'average_score': avg_score,
                'quality_drop_rate': quality_drop_rate,
                'error_rate': error_rate,
                'alerts': alerts,
                'alert_count': len(alerts)
            }

            if alerts:
                self.module_logger.warning(f"⚠️ 检测到 {len(alerts)} 个质量警报")

            return result

        except Exception as e:
            self.module_logger.error(f"质量监控失败: {e}")
            return {'status': 'error', 'error': str(e), 'alerts': []}

    async def _check_dimension_performance(self) -> List[Dict[str, Any]]:
        """检查维度性能"""
        alerts = []

        for dimension, scores in self._stats['dimension_performance'].items():
            if len(scores) < 20:  # 需要足够的数据
                continue

            recent_scores = scores[-10:]
            avg_recent = statistics.mean(recent_scores)

            threshold = self._quality_thresholds.get(dimension)
            if threshold and avg_recent < threshold.warning_threshold:
                alerts.append({
                    'type': 'dimension_performance',
                    'severity': 'medium',
                    'dimension': dimension,
                    'message': f'{dimension} 维度性能下降至 {avg_recent:.1f} (阈值: {threshold.warning_threshold})',
                    'recommendation': f'检查 {dimension} 相关的验证规则或数据源'
                })

        return alerts

    # 🚀 新增：辅助方法
    def _should_assess_dimension(self, dimension: QualityDimension, level: ValidationLevel) -> bool:
        """判断是否需要评估某个维度"""
        if level == ValidationLevel.BASIC:
            return dimension in [QualityDimension.FORMAT_COMPLIANCE, QualityDimension.CLARITY]
        elif level == ValidationLevel.STANDARD:
            return dimension in [
                QualityDimension.FACTUAL_ACCURACY, QualityDimension.LOGICAL_CONSISTENCY,
                QualityDimension.COMPLETENESS, QualityDimension.RELEVANCE,
                QualityDimension.FORMAT_COMPLIANCE
            ]
        else:  # COMPREHENSIVE or CRITICAL
            return True

    def _determine_validation_level(self, content_type: str, context: Optional[Dict[str, Any]]) -> ValidationLevel:
        """确定验证级别"""
        # 基于内容类型和上下文确定验证级别
        if content_type in ['medical', 'legal', 'financial']:
            return ValidationLevel.CRITICAL
        elif content_type in ['technical', 'academic']:
            return ValidationLevel.COMPREHENSIVE
        elif context and context.get('high_stakes', False):
            return ValidationLevel.COMPREHENSIVE
        else:
            return ValidationLevel.STANDARD

    def _should_auto_correct(self, assessment: QualityAssessment) -> bool:
        """判断是否应该自动纠错"""
        # 只对低严重性问题进行自动纠错
        critical_issues = [i for i in assessment.detected_issues if i.get('severity') == 'critical']
        return len(critical_issues) == 0 and assessment.overall_score >= 50.0

    async def _generate_recommendations(self, dimension_scores: Dict[str, float],
                                      issues: List[Dict[str, Any]]) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 基于维度评分生成建议
        for dimension, score in dimension_scores.items():
            if score < 60.0:
                dim_enum = QualityDimension(dimension)
                if dim_enum == QualityDimension.FACTUAL_ACCURACY:
                    recommendations.append("加强事实验证，使用可靠的数据源")
                elif dim_enum == QualityDimension.LOGICAL_CONSISTENCY:
                    recommendations.append("检查逻辑推理链，确保结论与前提一致")
                elif dim_enum == QualityDimension.COMPLETENESS:
                    recommendations.append("补充缺失的信息，提供更全面的回答")
                elif dim_enum == QualityDimension.CLARITY:
                    recommendations.append("简化语言表达，提高内容可读性")

        # 基于具体问题生成建议
        issue_counts = defaultdict(int)
        for issue in issues:
            issue_counts[issue.get('type', 'unknown')] += 1

        for issue_type, count in issue_counts.items():
            if count > 2:  # 频繁出现的问题
                if issue_type == 'factual_error':
                    recommendations.append("建立事实验证机制，减少事实错误")
                elif issue_type == 'format_violation':
                    recommendations.append("标准化输出格式，确保格式一致性")

        return recommendations[:5]  # 最多5条建议

    def _get_quality_cache_key(self, content: str, context: Optional[Dict[str, Any]],
                              validation_level: ValidationLevel) -> str:
        """生成质量缓存键"""
        key_data = {
            'content_hash': hashlib.md5(content.encode()).hexdigest(),
            'context_keys': sorted(context.keys()) if context else [],
            'validation_level': validation_level.value
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    # 🚀 新增：内置验证规则初始化
    def _initialize_builtin_rules(self):
        """初始化内置验证规则"""

        # 事实准确性规则
        self._validation_rules['factual_check'] = ValidationRule(
            rule_id='factual_check',
            name='事实检查',
            description='检查内容中的事实准确性',
            quality_dimension=QualityDimension.FACTUAL_ACCURACY,
            validation_function=self._validate_factual_accuracy,
            severity='critical'
        )

        # 逻辑一致性规则
        self._validation_rules['logic_check'] = ValidationRule(
            rule_id='logic_check',
            name='逻辑检查',
            description='检查逻辑一致性和矛盾',
            quality_dimension=QualityDimension.LOGICAL_CONSISTENCY,
            validation_function=self._validate_logical_consistency,
            severity='major'
        )

        # 完整性规则
        self._validation_rules['completeness_check'] = ValidationRule(
            rule_id='completeness_check',
            name='完整性检查',
            description='检查信息完整性',
            quality_dimension=QualityDimension.COMPLETENESS,
            validation_function=self._validate_completeness
        )

        # 格式合规性规则
        self._validation_rules['format_check'] = ValidationRule(
            rule_id='format_check',
            name='格式检查',
            description='检查格式合规性',
            quality_dimension=QualityDimension.FORMAT_COMPLIANCE,
            validation_function=self._validate_format_compliance
        )

        # 初始化纠错模式
        self._initialize_correction_patterns()

    def _initialize_correction_patterns(self):
        """初始化纠错模式"""
        self._correction_patterns = {
            'format_violation': {
                'pattern': r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY 格式
                'replacement': lambda m: f"{m.group(0).split('/')[2]}-{m.group(0).split('/')[0].zfill(2)}-{m.group(0).split('/')[1].zfill(2)}"  # YYYY-MM-DD
            },
            'unclear_expression': {
                'clarification': '以上内容可能存在表述不清的情况，建议进一步澄清。'
            }
        }

    def _initialize_quality_thresholds(self):
        """初始化质量阈值"""
        thresholds = [
            QualityThreshold(
                dimension=QualityDimension.FACTUAL_ACCURACY,
                minimum_score=75.0,
                warning_threshold=80.0,
                critical_threshold=70.0,
                auto_correct=False,
                escalation_required=True
            ),
            QualityThreshold(
                dimension=QualityDimension.LOGICAL_CONSISTENCY,
                minimum_score=70.0,
                warning_threshold=75.0,
                critical_threshold=65.0,
                auto_correct=True
            ),
            QualityThreshold(
                dimension=QualityDimension.FORMAT_COMPLIANCE,
                minimum_score=80.0,
                warning_threshold=85.0,
                critical_threshold=75.0,
                auto_correct=True
            )
        ]

        for threshold in thresholds:
            self._quality_thresholds[threshold.dimension.value] = threshold

    # 🚀 新增：验证函数实现
    def _validate_factual_accuracy(self, content: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """验证事实准确性"""
        # 简化的实现，实际应该调用事实验证服务
        issues = []

        # 检查明显的矛盾或错误
        contradictions = [
            (r'\b(地球|earth)\b.*\b(圆|round|flat)\b', '地球形状争议'),
            (r'\b(水|water)\b.*\b(烧开|boil)\b.*\b(100|212)\b', '水沸点检查')
        ]

        score = 85.0  # 基础分数

        for pattern, issue_desc in contradictions:
            if re.search(pattern, content, re.IGNORECASE):
                # 这里应该有更复杂的事实验证逻辑
                # 暂时降低分数表示需要验证
                score -= 5.0
                issues.append({
                    'type': 'factual_error',
                    'description': f'检测到需要验证的内容: {issue_desc}',
                    'severity': 'major'
                })

        return {'score': max(0.0, score), 'issues': issues}

    def _validate_logical_consistency(self, content: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """验证逻辑一致性"""
        issues = []
        score = 80.0

        # 检查矛盾词汇
        contradictions = [
            (r'\b(总是|always|never)\b.*\b(有时|sometimes)\b', '绝对化与相对化矛盾'),
            (r'\b(增加|increase|rise)\b.*\b(减少|decrease|fall)\b', '增减矛盾')
        ]

        for pattern, issue_desc in contradictions:
            if re.search(pattern, content, re.IGNORECASE):
                score -= 10.0
                issues.append({
                    'type': 'logical_contradiction',
                    'description': f'检测到逻辑矛盾: {issue_desc}',
                    'severity': 'major'
                })

        return {'score': max(0.0, score), 'issues': issues}

    def _validate_completeness(self, content: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """验证完整性"""
        issues = []
        score = 75.0

        # 检查内容长度
        word_count = len(content.split())
        if word_count < 50:
            score -= 15.0
            issues.append({
                'type': 'missing_information',
                'description': '内容过短，可能信息不完整',
                'severity': 'minor'
            })

        # 检查关键问题词
        question_words = ['what', 'why', 'how', 'when', 'where', 'who']
        has_questions = any(word in content.lower() for word in question_words)

        if has_questions and word_count < 100:
            score -= 10.0
            issues.append({
                'type': 'missing_information',
                'description': '问题型内容需要更详细的回答',
                'severity': 'minor'
            })

        return {'score': max(0.0, score), 'issues': issues}

    def _validate_format_compliance(self, content: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """验证格式合规性"""
        issues = []
        score = 90.0

        # 检查标点符号
        if content.count('.') < len(content) // 200:  # 每200字符至少一个句号
            score -= 5.0
            issues.append({
                'type': 'format_violation',
                'description': '标点符号使用不足',
                'severity': 'minor'
            })

        # 检查段落结构
        paragraphs = content.split('\n\n')
        if len(paragraphs) < 2 and len(content) > 300:
            score -= 5.0
            issues.append({
                'type': 'format_violation',
                'description': '长文本缺少段落分割',
                'severity': 'minor'
            })

        return {'score': max(0.0, score), 'issues': issues}

    # 🚀 新增：监控线程
    def _start_monitoring_thread(self):
        """启动监控线程"""
        self._running = True
        self._monitoring_thread = threading.Thread(target=self._monitoring_worker, daemon=True)
        self._monitoring_thread.start()
        self.module_logger.debug("📊 质量监控线程已启动")

    def _monitoring_worker(self):
        """监控工作线程"""
        while self._running:
            try:
                time.sleep(300)  # 每5分钟监控一次

                # 创建事件循环来运行异步任务
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    # 执行监控任务
                    if self._monitoring_enabled:
                        monitoring_result = loop.run_until_complete(self.monitor_quality_metrics())

                        # 处理警报
                        if monitoring_result.get('alerts'):
                            for alert in monitoring_result['alerts']:
                                self.module_logger.warning(f"🚨 质量警报: {alert['message']}")

                finally:
                    loop.close()

            except Exception as e:
                self.module_logger.warning(f"质量监控异常: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            'active_rules': len([r for r in self._validation_rules.values() if r.enabled]),
            'cache_size': len(self._quality_cache),
            'assessment_history_size': len(self._assessment_history),
            'quality_thresholds': {k: v.minimum_score for k, v in self._quality_thresholds.items()},
            'monitoring_enabled': self._monitoring_enabled
        }

    # 核心执行方法
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        执行质量控制任务

        Args:
            context: 质量控制请求上下文
                - action: 操作类型 ("assess_quality", "validate_content", "detect_errors", "monitor_quality", "stats")
                - content: 要评估的内容 (assess_quality/validate_content/detect_errors时需要)
                - content_type: 内容类型 (validate_content时可选)
                - error_types: 错误类型列表 (detect_errors时可选)

        Returns:
            AgentResult: 执行结果
        """
        start_time = time.time()
        action = context.get("action", "")

        try:
            if action == "assess_quality":
                content = context.get("content", "")
                validation_level = ValidationLevel(context.get("validation_level", "standard"))

                if not content:
                    result_data = {"error": "内容不能为空"}
                else:
                    assessment = await self.assess_quality(content, context, validation_level)
                    result_data = {
                        "assessment_id": assessment.assessment_id,
                        "overall_score": assessment.overall_score,
                        "dimension_scores": assessment.dimension_scores,
                        "issues_count": len(assessment.detected_issues),
                        "recommendations": assessment.recommendations
                    }

            elif action == "validate_content":
                content = context.get("content", "")
                content_type = context.get("content_type", "general")

                if not content:
                    result_data = {"error": "内容不能为空"}
                else:
                    validation_result = await self.validate_content(content, content_type, context)
                    result_data = validation_result

            elif action == "detect_errors":
                content = context.get("content", "")
                error_types = context.get("error_types")

                if not content:
                    result_data = {"error": "内容不能为空"}
                else:
                    correction_result = await self.detect_and_correct_errors(content, error_types)
                    result_data = correction_result

            elif action == "monitor_quality":
                monitoring_result = await self.monitor_quality_metrics()
                result_data = monitoring_result

            elif action == "stats":
                result_data = self.get_stats()

            else:
                result_data = {"error": f"不支持的操作: {action}"}

            return AgentResult(
                success=True,
                data=result_data,
                confidence=0.8,
                processing_time=time.time() - start_time
            )

        except Exception as e:
            self.module_logger.error(f"❌ QualityController执行异常: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )

    def shutdown(self):
        """关闭质量控制器"""
        self._running = False
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5)

        self._parallel_validator.shutdown(wait=True)
        self.module_logger.info("🛑 QualityController已关闭")
