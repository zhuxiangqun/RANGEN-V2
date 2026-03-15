#!/usr/bin/env python3
"""
技能触发优化器
借鉴Anthropic skill-creator的触发优化功能，自动分析并优化技能触发效果

核心功能：
1. 触发效果分析 - 检测过度触发/触发不足
2. 智能建议生成 - 基于分析结果给出优化建议
3. 触发词自动优化 - 根据样本自动调整触发词
"""

import asyncio
import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor
import uuid

logger = logging.getLogger(__name__)


# ============== 数据结构 ==============

@dataclass
class TriggerTestCase:
    """触发测试用例"""
    prompt: str
    should_trigger: bool  # 期望是否触发
    category: str = "manual"  # manual/automatic/edge_case
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TriggerTestResult:
    """单个测试用例的结果"""
    prompt: str
    expected: bool
    actual: bool
    passed: bool
    confidence: float = 1.0
    matched_triggers: List[str] = field(default_factory=list)


@dataclass
class TriggerAnalysis:
    """触发效果分析结果"""
    skill_name: str
    
    # 测试统计
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    
    # 过度触发 (False Positives) - 不该触发但触发了
    false_positives: List[str] = field(default_factory=list)
    fp_count: int = 0
    fp_rate: float = 0.0
    
    # 触发不足 (False Negatives) - 该触发但没触发
    false_negatives: List[str] = field(default_factory=list)
    fn_count: int = 0
    fn_rate: float = 0.0
    
    # 正确触发
    true_positives: List[str] = field(default_factory=list)
    tp_count: int = 0
    tp_rate: float = 0.0
    
    # 未触发且不该触发 (正确拒绝)
    true_negatives: List[str] = field(default_factory=list)
    tn_count: int = 0
    tn_rate: float = 0.0
    
    # 总体指标
    accuracy: float = 0.0
    precision: float = 0.0  # 触发准确率
    recall: float = 0.0    # 触发召回率
    f1_score: float = 0.0
    
    # 详细测试结果
    test_results: List[TriggerTestResult] = field(default_factory=list)
    
    # 改进建议
    suggestions: List[str] = field(default_factory=list)
    
    # 分析时间
    analyzed_at: datetime = field(default_factory=datetime.now)
    
    # 样本信息
    positive_sample_count: int = 0
    negative_sample_count: int = 0


@dataclass
class OptimizedTriggerConfig:
    """优化后的触发配置"""
    skill_name: str
    
    # 当前配置
    current_triggers: List[str] = field(default_factory=list)
    current_description: str = ""
    
    # 推荐的配置
    recommended_triggers: List[str] = field(default_factory=list)
    recommended_description_additions: List[str] = field(default_factory=list)
    
    # 排除条件 (用于减少过度触发)
    exclusion_patterns: List[str] = field(default_factory=list)
    
    # 置信度
    confidence: float = 0.0
    
    # 预期改进
    expected_improvement: Dict[str, float] = field(default_factory=dict)
    
    # 原因
    reason: str = ""
    
    optimized_at: datetime = field(default_factory=datetime.now)


@dataclass
class TriggerMetrics:
    """触发指标历史"""
    skill_name: str
    timestamp: datetime
    precision: float
    recall: float
    f1_score: float
    total_tests: int
    fp_count: int
    fn_count: int


# ============== 技能触发优化器 ==============

class SkillTriggerOptimizer:
    """技能触发优化器"""
    
    def __init__(self, llm_service=None):
        """
        初始化触发优化器
        
        Args:
            llm_service: 可选的LLM服务（用于智能分析）
        """
        self.llm_service = llm_service
        self.logger = logging.getLogger(f"{__name__}.SkillTriggerOptimizer")
        
        # 触发词权重配置
        self.trigger_weights = {
            'exact_match': 3.0,      # 精确匹配
            'partial_match': 1.0,    # 部分匹配
            'keyword_match': 0.5,    # 关键词匹配
        }
        
        # 触发阈值
        self.trigger_threshold = 0.5
        
        # 历史指标存储
        self.metrics_history: Dict[str, List[TriggerMetrics]] = {}
    
    # ============== 核心功能 ==============
    
    def analyze_trigger_effectiveness(
        self,
        skill_name: str,
        skill_description: str,
        triggers: List[str],
        positive_samples: List[str],
        negative_samples: List[str],
        test_cases: Optional[List[TriggerTestCase]] = None
    ) -> TriggerAnalysis:
        """
        分析技能的触发效果
        
        Args:
            skill_name: 技能名称
            skill_description: 技能描述
            triggers: 触发词列表
            positive_samples: 应该触发的样本列表
            negative_samples: 不该触发的样本列表
            test_cases: 可选的额外测试用例
            
        Returns:
            TriggerAnalysis: 详细的触发效果分析
        """
        self.logger.info(f"🔍 开始分析技能触发效果: {skill_name}")
        self.logger.info(f"  正样本: {len(positive_samples)}个, 负样本: {len(negative_samples)}个")
        
        analysis = TriggerAnalysis(
            skill_name=skill_name,
            positive_sample_count=len(positive_samples),
            negative_sample_count=len(negative_samples)
        )
        
        # 构建触发器
        trigger_matcher = TriggerMatcher(triggers, skill_description)
        
        # 测试正样本（应该触发）
        for prompt in positive_samples:
            result = self._test_prompt(
                prompt, 
                expected=True,
                matcher=trigger_matcher
            )
            analysis.test_results.append(result)
            
            if result.passed:
                analysis.tp_count += 1
                analysis.true_positives.append(prompt)
            else:
                analysis.fn_count += 1
                analysis.false_negatives.append(prompt)
        
        # 测试负样本（不该触发）
        for prompt in negative_samples:
            result = self._test_prompt(
                prompt,
                expected=False,
                matcher=trigger_matcher
            )
            analysis.test_results.append(result)
            
            if result.passed:
                analysis.tn_count += 1
                analysis.true_negatives.append(prompt)
            else:
                analysis.fp_count += 1
                analysis.false_positives.append(prompt)
        
        # 测试额外的测试用例
        if test_cases:
            for tc in test_cases:
                result = self._test_prompt(
                    tc.prompt,
                    expected=tc.should_trigger,
                    matcher=trigger_matcher
                )
                analysis.test_results.append(result)
        
        # 计算统计数据
        analysis.total_tests = len(analysis.test_results)
        analysis.passed_tests = sum(1 for r in analysis.test_results if r.passed)
        analysis.failed_tests = analysis.total_tests - analysis.passed_tests
        
        # 计算指标
        self._calculate_metrics(analysis)
        
        # 生成建议
        analysis.suggestions = self._generate_suggestions(analysis, triggers)
        
        self.logger.info(f"✅ 触发分析完成: Precision={analysis.precision:.2f}, Recall={analysis.recall:.2f}, F1={analysis.f1_score:.2f}")
        
        # 保存历史
        self._save_metrics(analysis)
        
        return analysis
    
    def _test_prompt(
        self,
        prompt: str,
        expected: bool,
        matcher: 'TriggerMatcher'
    ) -> TriggerTestResult:
        """测试单个提示是否触发"""
        match_result = matcher.match(prompt)
        actual = match_result['should_trigger']
        passed = (actual == expected)
        
        return TriggerTestResult(
            prompt=prompt,
            expected=expected,
            actual=actual,
            passed=passed,
            confidence=match_result.get('confidence', 1.0),
            matched_triggers=match_result.get('matched_triggers', [])
        )
    
    def _calculate_metrics(self, analysis: TriggerAnalysis):
        """计算触发效果指标"""
        total_positive = analysis.tp_count + analysis.fp_count
        total_expected = analysis.tp_count + analysis.fn_count
        total_negative = analysis.tn_count + analysis.fp_count
        
        # Accuracy (准确率)
        if analysis.total_tests > 0:
            analysis.accuracy = (analysis.tp_count + analysis.tn_count) / analysis.total_tests
        
        # Precision (精确率) - 在所有触发中，有多少是应该触发的
        if total_positive > 0:
            analysis.precision = analysis.tp_count / total_positive
        
        # Recall (召回率) - 在所有应该触发的中，有多少实际触发了
        if total_expected > 0:
            analysis.recall = analysis.tp_count / total_expected
        
        # F1 Score
        if analysis.precision + analysis.recall > 0:
            analysis.f1_score = 2 * analysis.precision * analysis.recall / (analysis.precision + analysis.recall)
        
        # 计算比率
        if len(analysis.true_positives) + len(analysis.false_positives) > 0:
            analysis.fp_rate = analysis.fp_count / (analysis.fp_count + analysis.tp_count)
        
        if len(analysis.true_positives) + len(analysis.false_negatives) > 0:
            analysis.fn_rate = analysis.fn_count / (analysis.fn_count + analysis.tp_count)
        
        analysis.tp_rate = analysis.tp_count / analysis.total_tests if analysis.total_tests > 0 else 0
        analysis.tn_rate = analysis.tn_count / analysis.total_tests if analysis.total_tests > 0 else 0
    
    def _generate_suggestions(
        self,
        analysis: TriggerAnalysis,
        current_triggers: List[str]
    ) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        # 1. 总体评估
        if analysis.f1_score >= 0.9:
            suggestions.append("✅ 触发效果优秀，无需优化")
        elif analysis.f1_score >= 0.7:
            suggestions.append("⚠️ 触发效果一般，有改进空间")
        else:
            suggestions.append("❌ 触发效果较差，需要优化")
        
        # 2. 过度触发建议
        if analysis.fp_count > 0:
            fp_rate_pct = analysis.fp_rate * 100
            suggestions.append(
                f"🔴 过度触发: {analysis.fp_count}个提示不该触发但触发了 ({fp_rate_pct:.1f}%)"
            )
            
            # 分析共同特征
            common_words = self._extract_common_keywords(analysis.false_positives)
            if common_words:
                suggestions.append(
                    f"   → 共同特征: {', '.join(common_words[:5])}"
                )
            
            # 具体建议
            if len(analysis.false_positives) <= 5:
                suggestions.append("   → 建议在description中添加排除条件")
                for fp in analysis.false_positives[:3]:
                    suggestions.append(f"     • '{fp[:50]}...' 不该触发")
            else:
                suggestions.append("   → 建议收紧触发条件，增加更具体的触发词")
        
        # 3. 触发不足建议
        if analysis.fn_count > 0:
            fn_rate_pct = analysis.fn_rate * 100
            suggestions.append(
                f"🟡 触发不足: {analysis.fn_count}个提示应该触发但没触发 ({fn_rate_pct:.1f}%)"
            )
            
            # 提取缺失的意图
            missing_intents = self._extract_intents(analysis.false_negatives)
            if missing_intents:
                suggestions.append(
                    f"   → 建议添加触发词: {', '.join(missing_intents[:5])}"
                )
        
        # 4. 精确率优化
        if analysis.precision < 0.8 and analysis.fp_count > 0:
            suggestions.append(
                "💡 优化方向: 增加触发词的特异性，减少泛化触发词"
            )
        
        # 5. 召回率优化
        if analysis.recall < 0.8 and analysis.fn_count > 0:
            suggestions.append(
                "💡 优化方向: 添加更多同义词和变体作为触发词"
            )
        
        # 6. 触发词数量建议
        if len(current_triggers) < 3:
            suggestions.append(
                "💡 提示: 触发词数量较少，建议添加5-10个相关触发词"
            )
        elif len(current_triggers) > 20:
            suggestions.append(
                "💡 提示: 触发词数量较多，建议精简到15个以内"
            )
        
        return suggestions
    
    # ============== 触发词优化 ==============
    
    def optimize_triggers(
        self,
        skill_name: str,
        skill_description: str,
        current_triggers: List[str],
        positive_samples: List[str],
        negative_samples: List[str],
        target_precision: float = 0.9,
        target_recall: float = 0.85
    ) -> OptimizedTriggerConfig:
        """
        自动优化触发词
        
        Args:
            skill_name: 技能名称
            skill_description: 技能描述
            current_triggers: 当前触发词列表
            positive_samples: 正样本
            negative_samples: 负样本
            target_precision: 目标精确率
            target_recall: 目标召回率
            
        Returns:
            OptimizedTriggerConfig: 优化后的配置
        """
        self.logger.info(f"🎯 开始优化技能触发词: {skill_name}")
        
        # 首先分析当前效果
        analysis = self.analyze_trigger_effectiveness(
            skill_name, skill_description, current_triggers,
            positive_samples, negative_samples
        )
        
        # 如果已经满足目标，返回当前配置
        if analysis.f1_score >= 0.9:
            return OptimizedTriggerConfig(
                skill_name=skill_name,
                current_triggers=current_triggers,
                current_description=skill_description,
                recommended_triggers=current_triggers,
                confidence=analysis.f1_score,
                reason="触发效果已满足要求，无需优化"
            )
        
        # 生成优化的触发词
        recommended_triggers = self._generate_optimized_triggers(
            analysis, current_triggers, positive_samples, negative_samples
        )
        
        # 生成排除模式
        exclusion_patterns = self._generate_exclusion_patterns(
            analysis.false_positives
        )
        
        # 生成描述补充
        description_additions = self._generate_description_additions(
            analysis, exclusion_patterns
        )
        
        # 计算预期改进
        expected_improvement = {
            'precision': max(0, target_precision - analysis.precision),
            'recall': max(0, target_recall - analysis.recall),
            'f1': max(0, (2 * target_precision * target_recall / (target_precision + target_recall) if (target_precision + target_recall) > 0 else 0) - analysis.f1_score)
        }
        
        return OptimizedTriggerConfig(
            skill_name=skill_name,
            current_triggers=current_triggers,
            current_description=skill_description,
            recommended_triggers=recommended_triggers,
            recommended_description_additions=description_additions,
            exclusion_patterns=exclusion_patterns,
            confidence=analysis.f1_score,
            expected_improvement=expected_improvement,
            reason=f"基于{len(positive_samples)}个正样本和{len(negative_samples)}个负样本分析"
        )
    
    def _generate_optimized_triggers(
        self,
        analysis: TriggerAnalysis,
        current_triggers: List[str],
        positive_samples: List[str],
        negative_samples: List[str]
    ) -> List[str]:
        """生成优化后的触发词"""
        
        # 1. 从正确触发的样本中提取高频词
        tp_keywords = self._extract_keywords_from_samples(analysis.true_positives)
        
        # 2. 从错误触发的样本中提取要避免的词
        fp_keywords = self._extract_keywords_from_samples(analysis.false_positives)
        
        # 3. 从触发不足的样本中提取缺失的词
        fn_keywords = self._extract_keywords_from_samples(analysis.false_negatives)
        
        # 4. 生成新触发词列表
        recommended = []
        
        # 添加在正样本中高频出现但不在负样本中的词
        for word, count in tp_keywords.items():
            # 跳过已经在列表中的
            if word in current_triggers:
                continue
            # 跳过在负样本中频繁出现的
            if word in fp_keywords and fp_keywords[word] >= 2:
                continue
            # 添加高频词
            if count >= 2:
                recommended.append(word)
        
        # 添加缺失的触发词（从fn样本中）
        for word in fn_keywords.keys():
            if word not in recommended and word not in current_triggers:
                recommended.append(word)
        
        # 保留一些原有的高效触发词
        for trigger in current_triggers:
            if len(recommended) >= 15:
                break
            # 检查这个触发词在正样本中的效果
            for tp in analysis.true_positives:
                if trigger.lower() in tp.lower():
                    if trigger not in recommended:
                        recommended.append(trigger)
                    break
        
        # 限制数量
        return recommended[:20]
    
    def _generate_exclusion_patterns(self, false_positives: List[str]) -> List[str]:
        """生成排除模式"""
        if not false_positives:
            return []
        
        # 找出共同的负面特征
        common_words = self._extract_common_keywords(false_positives)
        
        # 生成排除模式
        patterns = []
        for word in common_words[:5]:
            patterns.append(f"不适用于{word}")
            patterns.append(f"当涉及{word}时不使用")
        
        return patterns[:10]
    
    def _generate_description_additions(
        self,
        analysis: TriggerAnalysis,
        exclusion_patterns: List[str]
    ) -> List[str]:
        """生成描述补充建议"""
        additions = []
        
        if analysis.fp_count > 0:
            additions.append("### 排除场景")
            additions.append("以下情况下不应使用此技能：")
            for pattern in exclusion_patterns[:3]:
                additions.append(f"- {pattern}")
        
        if analysis.fn_count > 0:
            additions.append("### 适用场景")
            additions.append("此技能适用于：")
            # 从false_negatives提取
            for fn in analysis.false_negatives[:3]:
                additions.append(f"- {fn[:60]}...")
        
        return additions
    
    # ============== 辅助方法 ==============
    
    def _extract_keywords_from_samples(self, samples: List[str]) -> Counter:
        """从样本中提取关键词"""
        keywords = Counter()
        
        for sample in samples:
            # 简单分词
            words = re.findall(r'\b[\w]{2,}\b', sample.lower())
            
            # 过滤停用词
            stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                        'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                        'can', 'need', 'to', 'of', 'in', 'for', 'on', 'with', 'at',
                        'by', 'from', 'as', 'into', 'through', 'during', 'before',
                        'after', 'above', 'below', 'between', 'under', 'again',
                        'further', 'then', 'once', 'here', 'there', 'when', 'where',
                        'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other',
                        'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
                        'so', 'than', 'too', 'very', 'just', 'and', 'but', 'if',
                        'or', 'because', 'until', 'while', 'this', 'that', 'these',
                        'those', '我', '你', '他', '她', '它', '们', '的', '是',
                        '在', '有', '和', '与', '就', '不', '也', '都', '要', '会'}
            
            filtered = [w for w in words if w not in stopwords and len(w) >= 2]
            keywords.update(filtered)
        
        return keywords
    
    def _extract_common_keywords(self, samples: List[str]) -> List[str]:
        """提取共同关键词"""
        keywords = self._extract_keywords_from_samples(samples)
        return [word for word, count in keywords.most_common(10)]
    
    def _extract_intents(self, samples: List[str]) -> List[str]:
        """提取意图关键词"""
        # 简化版本：直接提取关键词
        return self._extract_common_keywords(samples)
    
    def _save_metrics(self, analysis: TriggerAnalysis):
        """保存指标到历史"""
        if analysis.skill_name not in self.metrics_history:
            self.metrics_history[analysis.skill_name] = []
        
        metrics = TriggerMetrics(
            skill_name=analysis.skill_name,
            timestamp=analysis.analyzed_at,
            precision=analysis.precision,
            recall=analysis.recall,
            f1_score=analysis.f1_score,
            total_tests=analysis.total_tests,
            fp_count=analysis.fp_count,
            fn_count=analysis.fn_count
        )
        
        self.metrics_history[analysis.skill_name].append(metrics)
        
        # 只保留最近20条
        if len(self.metrics_history[analysis.skill_name]) > 20:
            self.metrics_history[analysis.skill_name] = \
                self.metrics_history[analysis.skill_name][-20:]
    
    def get_metrics_history(self, skill_name: str) -> List[TriggerMetrics]:
        """获取指标历史"""
        return self.metrics_history.get(skill_name, [])


# ============== 触发匹配器 ==============

class TriggerMatcher:
    """触发词匹配器"""
    
    def __init__(self, triggers: List[str], description: str = ""):
        self.triggers = [t.lower().strip() for t in triggers]
        self.description = description.lower() if description else ""
        
        # 预处理触发词
        self.trigger_words: Dict[str, Set[str]] = {}
        for trigger in self.triggers:
            words = set(trigger.split())
            self.trigger_words[trigger] = words
    
    def match(self, prompt: str) -> Dict[str, Any]:
        """判断提示是否应该触发"""
        prompt_lower = prompt.lower()
        
        matched_triggers = []
        match_scores = []
        
        for trigger in self.triggers:
            score = 0.0
            matched = False
            
            # 1. 精确匹配
            if trigger in prompt_lower:
                score += 3.0
                matched = True
            
            # 2. 部分匹配
            elif any(word in prompt_lower for word in trigger.split()):
                score += 1.0
                matched = True
            
            # 3. 关键词匹配
            else:
                trigger_words = trigger.split()
                matches = sum(1 for word in trigger_words if word in prompt_lower)
                if matches > 0:
                    score += matches * 0.5
                    matched = matches >= len(trigger_words) * 0.5
            
            if matched:
                matched_triggers.append(trigger)
                match_scores.append(score)
        
        # 计算置信度
        total_score = sum(match_scores) if match_scores else 0
        should_trigger = total_score >= 1.0  # 阈值
        
        return {
            'should_trigger': should_trigger,
            'confidence': min(total_score / 5.0, 1.0),
            'matched_triggers': matched_triggers,
            'total_score': total_score
        }


# ============== 便捷函数 ==============

def get_trigger_optimizer() -> SkillTriggerOptimizer:
    """获取触发优化器单例"""
    return SkillTriggerOptimizer()


# ============== 测试 ==============

async def main():
    """测试触发优化器"""
    logging.basicConfig(level=logging.INFO)
    
    optimizer = SkillTriggerOptimizer()
    
    # 测试技能配置
    skill_name = "pdf-generator"
    skill_description = "用于从零创建PDF文档，生成报告"
    triggers = ["pdf", "文档", "生成", "创建", "create pdf", "document"]
    
    # 正样本（应该触发）
    positive_samples = [
        "帮我创建一个PDF文件",
        "生成一个PDF报告",
        "我想制作PDF文档",
        "创建一个PDF表格",
        "生成PDF发票",
    ]
    
    # 负样本（不该触发）
    negative_samples = [
        "帮我写一段代码",
        "分析这个数据",
        "帮我搜索一下",
        "今天天气怎么样",
        "给我讲个笑话",
    ]
    
    print("=" * 60)
    print("技能触发效果分析")
    print("=" * 60)
    
    # 分析触发效果
    analysis = optimizer.analyze_trigger_effectiveness(
        skill_name, skill_description, triggers,
        positive_samples, negative_samples
    )
    
    print(f"\n📊 分析结果:")
    print(f"  技能名称: {analysis.skill_name}")
    print(f"  总测试数: {analysis.total_tests}")
    print(f"  通过测试: {analysis.passed_tests}")
    print(f"  失败测试: {analysis.failed_tests}")
    
    print(f"\n📈 指标:")
    print(f"  准确率 (Accuracy): {analysis.accuracy:.2%}")
    print(f"  精确率 (Precision): {analysis.precision:.2%}")
    print(f"  召回率 (Recall): {analysis.recall:.2%}")
    print(f"  F1 Score: {analysis.f1_score:.2f}")
    
    print(f"\n🔴 过度触发 ({analysis.fp_count}个):")
    for fp in analysis.false_positives[:3]:
        print(f"  - {fp}")
    
    print(f"\n🟡 触发不足 ({analysis.fn_count}个):")
    for fn in analysis.false_negatives[:3]:
        print(f"  - {fn}")
    
    print(f"\n💡 优化建议:")
    for suggestion in analysis.suggestions:
        print(f"  {suggestion}")
    
    # 优化触发词
    print("\n" + "=" * 60)
    print("触发词优化")
    print("=" * 60)
    
    optimized = optimizer.optimize_triggers(
        skill_name, skill_description, triggers,
        positive_samples, negative_samples
    )
    
    print(f"\n🎯 优化结果:")
    print(f"  当前触发词: {optimized.current_triggers}")
    print(f"  推荐触发词: {optimized.recommended_triggers}")
    print(f"  置信度: {optimized.confidence:.2f}")
    
    if optimized.exclusion_patterns:
        print(f"\n🚫 排除模式:")
        for pattern in optimized.exclusion_patterns[:3]:
            print(f"  - {pattern}")
    
    print("\n✅ 测试完成")


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
