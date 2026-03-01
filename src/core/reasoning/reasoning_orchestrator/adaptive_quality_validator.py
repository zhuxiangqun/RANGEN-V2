"""
自适应质量验证器
根据查询类型和历史数据动态调整验证策略
"""

import logging
import time
import json
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    score: float
    scores: Dict[str, float]
    issues: List[str]
    query_type: str
    timestamp: float
    validation_time: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            'is_valid': self.is_valid,
            'score': self.score,
            'scores': self.scores,
            'issues': self.issues,
            'query_type': self.query_type,
            'timestamp': self.timestamp,
            'validation_time': self.validation_time
        }

class AdaptiveQualityValidator:
    """
    自适应质量验证器

    功能：
    - 动态权重调整：根据查询类型调整验证权重
    - 上下文感知：考虑查询的具体上下文
    - 学习优化：从历史验证结果中学习
    - 多维度验证：结构完整性、逻辑一致性、领域准确性等
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path("data/validation_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 默认权重配置
        self.default_weights = {
            'logic_consistency': 0.25,
            'premise_completeness': 0.25,
            'domain_accuracy': 0.20,
            'step_granularity': 0.15,
            'structural_completeness': 0.15
        }

        # 查询类型特定的权重
        self.query_type_weights = {
            'logic_trap': {
                'logic_consistency': 0.35,      # 逻辑一致性最重要
                'premise_completeness': 0.30,   # 前提完整性很重要
                'domain_accuracy': 0.20,
                'step_granularity': 0.10,
                'structural_completeness': 0.05
            },
            'factual_chain': {
                'logic_consistency': 0.20,
                'premise_completeness': 0.20,
                'domain_accuracy': 0.25,        # 领域准确性重要
                'step_granularity': 0.20,       # 步骤粒度重要
                'structural_completeness': 0.15
            },
            'cross_domain': {
                'logic_consistency': 0.25,
                'premise_completeness': 0.20,
                'domain_accuracy': 0.30,        # 跨领域准确性关键
                'step_granularity': 0.15,
                'structural_completeness': 0.10
            },
            'historical_fact': {
                'logic_consistency': 0.15,
                'premise_completeness': 0.15,
                'domain_accuracy': 0.40,        # 历史准确性最重要
                'step_granularity': 0.15,
                'structural_completeness': 0.15
            },
            'general': self.default_weights
        }

        # 验证历史
        self.validation_history: List[ValidationResult] = []
        self.max_history_size = 1000

        # 学习统计
        self.learning_stats = defaultdict(lambda: {
            'total_validations': 0,
            'correct_predictions': 0,
            'avg_score': 0.0,
            'score_variance': 0.0,
            'common_issues': defaultdict(int)
        })

        # 动态阈值
        self.dynamic_thresholds = {}
        self.threshold_learning_enabled = True

        # 加载历史数据
        self._load_validation_history()

        logger.info("✅ AdaptiveQualityValidator 初始化完成")

    def validate_reasoning(self, steps_text: str, query: str,
                          planning_result: Dict[str, Any]) -> ValidationResult:
        """
        验证推理步骤质量

        Args:
            steps_text: 推理步骤文本
            query: 原始查询
            planning_result: 推理规划结果

        Returns:
            ValidationResult: 验证结果
        """
        start_time = time.time()
        query_type = planning_result.get('query_type', 'general')

        try:
            # 1. 解析推理步骤
            parsed_steps = self._parse_steps(steps_text)
            if not parsed_steps:
                return ValidationResult(
                    is_valid=False,
                    score=0.0,
                    scores={},
                    issues=['无法解析推理步骤'],
                    query_type=query_type,
                    timestamp=time.time(),
                    validation_time=time.time() - start_time
                )

            # 2. 获取验证权重
            weights = self._get_weights_for_query_type(query_type)

            # 3. 执行多维度验证
            validation_scores = self._perform_multidimensional_validation(
                parsed_steps, query, planning_result
            )

            # 4. 计算综合得分
            overall_score = sum(score * weights[dimension]
                              for dimension, score in validation_scores.items()
                              if dimension in weights)

            # 5. 确定验证结果
            threshold = self._get_dynamic_threshold(query_type)
            is_valid = overall_score >= threshold

            # 6. 识别问题
            issues = self._identify_issues(validation_scores, weights, query_type)

            # 7. 创建结果
            result = ValidationResult(
                is_valid=is_valid,
                score=overall_score,
                scores=validation_scores,
                issues=issues,
                query_type=query_type,
                timestamp=time.time(),
                validation_time=time.time() - start_time
            )

            # 8. 记录历史用于学习
            self._record_validation_result(result)

            return result

        except Exception as e:
            logger.error(f"验证推理步骤失败: {e}")
            return ValidationResult(
                is_valid=False,
                score=0.0,
                scores={},
                issues=[f'验证过程异常: {str(e)}'],
                query_type=query_type,
                timestamp=time.time(),
                validation_time=time.time() - start_time
            )

    def _get_weights_for_query_type(self, query_type: str) -> Dict[str, float]:
        """获取查询类型的验证权重"""
        return self.query_type_weights.get(query_type, self.default_weights)

    def _perform_multidimensional_validation(self, parsed_steps: List[Dict[str, Any]],
                                          query: str, planning_result: Dict[str, Any]) -> Dict[str, float]:
        """执行多维度验证"""
        scores = {}

        # 1. 逻辑一致性验证
        scores['logic_consistency'] = self._validate_logic_consistency(parsed_steps, query, planning_result)

        # 2. 前提完整性验证
        scores['premise_completeness'] = self._validate_premise_completeness(parsed_steps, query, planning_result)

        # 3. 领域准确性验证
        scores['domain_accuracy'] = self._validate_domain_accuracy(parsed_steps, query, planning_result)

        # 4. 步骤粒度验证
        scores['step_granularity'] = self._validate_step_granularity(parsed_steps, query, planning_result)

        # 5. 结构完整性验证
        scores['structural_completeness'] = self._validate_structural_completeness(parsed_steps, query, planning_result)

        return scores

    def _validate_logic_consistency(self, steps: List[Dict[str, Any]], query: str,
                                  planning_result: Dict[str, Any]) -> float:
        """验证逻辑一致性"""
        score = 1.0
        issues = []

        # 检查步骤间的逻辑连贯性
        for i, step in enumerate(steps):
            step_content = step.get('description', '') + ' ' + step.get('sub_query', '')

            # 检查是否包含矛盾的逻辑
            if self._contains_logical_contradiction(step_content):
                score -= 0.3
                issues.append(f'步骤{i+1}包含逻辑矛盾')

            # 检查是否与查询类型匹配的逻辑模式
            query_type = planning_result.get('query_type', 'general')
            if not self._matches_query_type_logic(step, query_type):
                score -= 0.2
                issues.append(f'步骤{i+1}逻辑类型与查询不匹配')

        # 检查整体逻辑流
        if not self._has_logical_flow(steps):
            score -= 0.2
            issues.append('推理步骤缺乏逻辑流')

        return max(0.0, score)

    def _validate_premise_completeness(self, steps: List[Dict[str, Any]], query: str,
                                     planning_result: Dict[str, Any]) -> float:
        """验证前提完整性"""
        score = 1.0

        # 检查是否涵盖了查询中的所有关键元素
        query_elements = self._extract_query_elements(query)
        covered_elements = set()

        for step in steps:
            step_content = step.get('description', '') + ' ' + step.get('sub_query', '')
            step_elements = self._extract_query_elements(step_content)
            covered_elements.update(step_elements)

        # 计算覆盖率
        if query_elements:
            coverage = len(covered_elements & query_elements) / len(query_elements)
            score = min(1.0, coverage + 0.3)  # 给基础分

        # 对于逻辑陷阱，检查是否识别了关键前提
        query_type = planning_result.get('query_type', 'general')
        if query_type == 'logic_trap':
            if not self._identifies_key_premises(steps, query):
                score -= 0.4

        return max(0.0, score)

    def _validate_domain_accuracy(self, steps: List[Dict[str, Any]], query: str,
                                planning_result: Dict[str, Any]) -> float:
        """验证领域准确性"""
        score = 1.0

        query_type = planning_result.get('query_type', 'general')
        domain_knowledge = self._get_domain_knowledge(query_type)

        for i, step in enumerate(steps):
            step_content = step.get('description', '') + ' ' + step.get('sub_query', '')

            # 检查是否包含领域错误
            domain_errors = self._check_domain_errors(step_content, domain_knowledge)
            if domain_errors:
                score -= len(domain_errors) * 0.2

        return max(0.0, score)

    def _validate_step_granularity(self, steps: List[Dict[str, Any]], query: str,
                                 planning_result: Dict[str, Any]) -> float:
        """验证步骤粒度"""
        score = 1.0

        # 检查步骤是否过于粗糙或过于细碎
        for i, step in enumerate(steps):
            step_content = step.get('description', '') + ' ' + step.get('sub_query', '')

            # 检查步骤长度
            if len(step_content) < 20:
                score -= 0.1  # 步骤过于简短
            elif len(step_content) > 200:
                score -= 0.1  # 步骤过于冗长

        # 检查步骤数量是否合理
        expected_steps = planning_result.get('reasoning_requirements', {}).get('step_count', [2, 4])
        if isinstance(expected_steps, list) and len(expected_steps) == 2:
            min_steps, max_steps = expected_steps
            if len(steps) < min_steps or len(steps) > max_steps:
                score -= 0.2

        return max(0.0, score)

    def _validate_structural_completeness(self, steps: List[Dict[str, Any]], query: str,
                                        planning_result: Dict[str, Any]) -> float:
        """验证结构完整性"""
        score = 1.0

        # 检查必需的步骤类型
        required_types = {'information_retrieval', 'answer_synthesis'}
        present_types = {step.get('type') for step in steps if step.get('type')}

        missing_types = required_types - present_types
        if missing_types:
            score -= len(missing_types) * 0.2

        # 检查步骤顺序的合理性
        if not self._has_reasonable_step_order(steps):
            score -= 0.3

        # 检查每个步骤的必需字段
        for step in steps:
            required_fields = ['type', 'description', 'sub_query']
            missing_fields = [field for field in required_fields if not step.get(field)]
            if missing_fields:
                score -= len(missing_fields) * 0.1

        return max(0.0, score)

    def _contains_logical_contradiction(self, text: str) -> bool:
        """检查是否包含逻辑矛盾"""
        contradictions = [
            'is and is not',
            'both true and false',
            'cannot be both',
            'impossible but possible'
        ]

        text_lower = text.lower()
        return any(contradiction in text_lower for contradiction in contradictions)

    def _matches_query_type_logic(self, step: Dict[str, Any], query_type: str) -> bool:
        """检查步骤是否匹配查询类型的逻辑模式"""
        step_type = step.get('type', '')
        step_content = step.get('description', '') + ' ' + step.get('sub_query', '')

        if query_type == 'logic_trap':
            return step_type in ['logical_reasoning', 'information_retrieval']
        elif query_type == 'factual_chain':
            return step_type in ['information_retrieval', 'answer_synthesis']
        elif query_type == 'cross_domain':
            return 'convert' in step_content.lower() or 'transform' in step_content.lower() or step_type == 'data_processing'

        return True  # 其他类型默认匹配

    def _has_logical_flow(self, steps: List[Dict[str, Any]]) -> bool:
        """检查是否有逻辑流"""
        if len(steps) < 2:
            return True

        # 检查步骤间是否有引用关系
        has_references = False
        for i in range(1, len(steps)):
            current_content = steps[i].get('description', '') + ' ' + steps[i].get('sub_query', '')
            for j in range(i):
                prev_step_ref = f'step {j+1}'
                if prev_step_ref.lower() in current_content.lower():
                    has_references = True
                    break

        return has_references or len(steps) <= 3  # 短序列默认有逻辑流

    def _extract_query_elements(self, text: str) -> set:
        """提取查询中的关键元素"""
        # 简单的实体提取（生产环境中可以使用NER）
        words = text.lower().split()
        entities = set()

        # 查找可能的实体（大写开头的词、人名模式等）
        for word in words:
            word = word.strip('.,!?;:')
            if len(word) > 1 and (word[0].isupper() or word in ['d.c.', 'u.s.', 'usa']):
                entities.add(word.lower())

        return entities

    def _identifies_key_premises(self, steps: List[Dict[str, Any]], query: str) -> bool:
        """检查是否识别了关键前提"""
        # 对于D.C.相关的查询，检查是否识别了"D.C.不是州"这个前提
        if 'capitol' in query.lower() and 'state' in query.lower():
            for step in steps:
                step_content = step.get('description', '') + ' ' + step.get('sub_query', '')
                if 'not a state' in step_content.lower() or 'federal district' in step_content.lower():
                    return True
        return False

    def _get_domain_knowledge(self, query_type: str) -> Dict[str, Any]:
        """获取领域知识"""
        domain_knowledge = {
            'logic_trap': {
                'correct_facts': ['d.c. is not a state', 'federal district'],
                'incorrect_facts': ['d.c. is a state']
            },
            'factual_chain': {
                'requires_evidence': True,
                'needs_relationships': True
            },
            'cross_domain': {
                'requires_conversion': True,
                'needs_domain_mapping': True
            }
        }
        return domain_knowledge.get(query_type, {})

    def _check_domain_errors(self, content: str, domain_knowledge: Dict[str, Any]) -> List[str]:
        """检查领域错误"""
        errors = []

        content_lower = content.lower()

        # 检查错误的陈述
        for incorrect_fact in domain_knowledge.get('incorrect_facts', []):
            if incorrect_fact in content_lower:
                errors.append(f'包含错误事实: {incorrect_fact}')

        return errors

    def _has_reasonable_step_order(self, steps: List[Dict[str, Any]]) -> bool:
        """检查步骤顺序是否合理"""
        if len(steps) < 2:
            return True

        # 基本检查：信息收集步骤应该在分析步骤之前
        info_steps = []
        analysis_steps = []

        for i, step in enumerate(steps):
            step_type = step.get('type', '')
            if step_type == 'information_retrieval':
                info_steps.append(i)
            elif step_type in ['logical_reasoning', 'answer_synthesis']:
                analysis_steps.append(i)

        # 检查是否有不合理的顺序（分析在信息收集之前）
        for analysis_idx in analysis_steps:
            if any(info_idx > analysis_idx for info_idx in info_steps):
                return False

        return True

    def _parse_steps(self, steps_text: str) -> List[Dict[str, Any]]:
        """解析推理步骤文本"""
        try:
            # 尝试解析JSON
            if steps_text.strip().startswith('['):
                parsed = json.loads(steps_text)
                if isinstance(parsed, list):
                    return parsed
        except:
            pass

        # 如果JSON解析失败，返回空列表
        return []

    def _get_dynamic_threshold(self, query_type: str) -> float:
        """获取动态阈值"""
        if not self.threshold_learning_enabled or query_type not in self.dynamic_thresholds:
            # 默认阈值
            return 0.7

        return self.dynamic_thresholds[query_type]

    def _identify_issues(self, scores: Dict[str, float], weights: Dict[str, float],
                        query_type: str) -> List[str]:
        """识别问题"""
        issues = []

        for dimension, score in scores.items():
            if score < 0.6:  # 分数低于0.6认为有问题
                weight = weights.get(dimension, 0)
                issues.append(f'{dimension}分数过低: {score:.2f} (权重: {weight:.2f})')

        return issues

    def _record_validation_result(self, result: ValidationResult):
        """记录验证结果用于学习"""
        self.validation_history.append(result)

        # 限制历史记录大小
        if len(self.validation_history) > self.max_history_size:
            self.validation_history = self.validation_history[-self.max_history_size:]

        # 更新学习统计
        stats = self.learning_stats[result.query_type]
        stats['total_validations'] += 1

        if result.is_valid:
            stats['correct_predictions'] += 1

        # 更新平均分数
        recent_scores = [r.score for r in self.validation_history[-50:] if r.query_type == result.query_type]
        if recent_scores:
            stats['avg_score'] = statistics.mean(recent_scores)
            if len(recent_scores) > 1:
                stats['score_variance'] = statistics.variance(recent_scores)

        # 记录常见问题
        for issue in result.issues:
            stats['common_issues'][issue] += 1

        # 更新动态阈值
        if self.threshold_learning_enabled:
            self._update_dynamic_thresholds(result.query_type)

    def _update_dynamic_thresholds(self, query_type: str):
        """更新动态阈值"""
        recent_results = [r for r in self.validation_history[-100:] if r.query_type == query_type]

        if len(recent_results) >= 20:
            # 使用平均分减去一个标准差作为阈值
            scores = [r.score for r in recent_results]
            avg_score = statistics.mean(scores)

            if len(scores) > 1:
                std_dev = statistics.stdev(scores)
                threshold = max(0.5, avg_score - std_dev)
            else:
                threshold = max(0.5, avg_score - 0.1)

            self.dynamic_thresholds[query_type] = threshold

    def get_learning_stats(self) -> Dict[str, Any]:
        """获取学习统计"""
        return dict(self.learning_stats)

    def get_validation_history(self, query_type: Optional[str] = None, limit: int = 100) -> List[ValidationResult]:
        """获取验证历史"""
        history = self.validation_history

        if query_type:
            history = [r for r in history if r.query_type == query_type]

        return history[-limit:]

    def _load_validation_history(self):
        """加载验证历史"""
        history_file = self.cache_dir / "validation_history.json"

        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for item in data.get('history', []):
                    result = ValidationResult(**item)
                    self.validation_history.append(result)

                logger.info(f"✅ 加载了 {len(self.validation_history)} 条验证历史")

            except Exception as e:
                logger.error(f"加载验证历史失败: {e}")

    def save_validation_history(self):
        """保存验证历史"""
        history_file = self.cache_dir / "validation_history.json"

        try:
            data = {
                'history': [r.to_dict() for r in self.validation_history[-500:]],  # 只保存最近500条
                'learning_stats': dict(self.learning_stats),
                'dynamic_thresholds': self.dynamic_thresholds,
                'saved_at': time.time()
            }

            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"✅ 保存了 {len(self.validation_history)} 条验证历史")

        except Exception as e:
            logger.error(f"保存验证历史失败: {e}")

    def reset_learning(self):
        """重置学习数据"""
        self.validation_history.clear()
        self.learning_stats.clear()
        self.dynamic_thresholds.clear()

        # 删除历史文件
        history_file = self.cache_dir / "validation_history.json"
        if history_file.exists():
            history_file.unlink()

        logger.info("✅ 已重置学习数据")
