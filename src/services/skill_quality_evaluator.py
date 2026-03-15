#!/usr/bin/env python3
"""
技能质量评估器 - 基于Anthropic skill-creator原理的三元评估体系
实现Analyzer/Comparator/Grader三个核心评估代理，提供完整的技能质量评估能力
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import uuid
import json

logger = logging.getLogger(__name__)


@dataclass
class SkillData:
    """技能数据模型"""
    skill_id: str
    name: str
    description: str
    category: str
    complexity: str  # simple, moderate, complex
    input_format: Optional[Dict[str, Any]] = None
    output_format: Optional[Dict[str, Any]] = None
    examples: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class AnalysisResult:
    """分析器结果"""
    structural_integrity: float  # 结构完整性评分 (0-1)
    functional_completeness: float  # 功能完整性评分 (0-1)
    boundary_conditions: Dict[str, Any]  # 边界条件分析
    error_handling_quality: float  # 错误处理质量 (0-1)
    dependencies_analysis: Dict[str, float]  # 依赖分析
    performance_indicators: Dict[str, float]  # 性能指标
    issues_found: List[Dict[str, Any]] = field(default_factory=list)  # 发现的问题
    recommendations: List[str] = field(default_factory=list)  # 改进建议
    analysis_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ComparisonResult:
    """比较器结果"""
    functional_overlap: Dict[str, float]  # 功能重叠度 {skill_id: overlap_score}
    overall_overlap_score: float  # 总体重叠度评分 (0-1)
    differentiation_score: float  # 差异化评分 (0-1)
    innovation_value: float  # 创新价值评分 (0-1)
    merge_candidates: List[str]  # 可合并的技能ID列表
    recommended_changes: List[Dict[str, Any]] = field(default_factory=list)  # 建议的修改
    uniqueness_assessment: str = ""  # 独特性评估
    comparison_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class GradeResult:
    """评分器结果"""
    scores: Dict[str, float]  # 各维度评分
    overall_grade: float  # 综合评分 (0-1)
    quality_level: str  # 质量等级 (poor, fair, good, excellent)
    certification: Optional[str] = None  # 认证等级
    strengths: List[str] = field(default_factory=list)  # 优点
    weaknesses: List[str] = field(default_factory=list)  # 缺点
    critical_issues: List[str] = field(default_factory=list)  # 关键问题
    grading_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class QualityReport:
    """完整质量报告"""
    skill_id: str
    skill_name: str
    evaluation_id: str
    analysis_result: AnalysisResult
    comparison_result: ComparisonResult
    grade_result: GradeResult
    overall_score: float  # 总体质量分数 (0-100)
    quality_status: str  # 质量状态 (rejected, needs_improvement, approved, certified)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)  # 整体建议
    evaluation_timestamp: datetime = field(default_factory=datetime.now)
    evaluator_version: str = "v1.0"


class SkillAnalyzer:
    """技能分析器 (Analyzer Agent) - 分析技能结构和功能完整性"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SkillAnalyzer")
    
    async def analyze_skill(self, skill_data: SkillData) -> AnalysisResult:
        """分析技能结构和功能完整性"""
        self.logger.info(f"开始分析技能: {skill_data.name} ({skill_data.skill_id})")
        
        try:
            # 1. 结构完整性分析
            structural_integrity = await self._analyze_structure(skill_data)
            
            # 2. 功能完整性分析
            functional_completeness = await self._analyze_functionality(skill_data)
            
            # 3. 边界条件分析
            boundary_conditions = await self._analyze_boundary_conditions(skill_data)
            
            # 4. 错误处理质量分析
            error_handling_quality = await self._analyze_error_handling(skill_data)
            
            # 5. 依赖分析
            dependencies_analysis = await self._analyze_dependencies(skill_data)
            
            # 6. 性能指标预估
            performance_indicators = await self._estimate_performance(skill_data)
            
            # 7. 问题检测
            issues_found = await self._detect_issues(skill_data)
            
            # 8. 生成建议
            recommendations = await self._generate_recommendations(
                skill_data, issues_found
            )
            
            result = AnalysisResult(
                structural_integrity=structural_integrity,
                functional_completeness=functional_completeness,
                boundary_conditions=boundary_conditions,
                error_handling_quality=error_handling_quality,
                dependencies_analysis=dependencies_analysis,
                performance_indicators=performance_indicators,
                issues_found=issues_found,
                recommendations=recommendations
            )
            
            self.logger.info(f"技能分析完成: {skill_data.name}, 结构完整性={structural_integrity:.2f}")
            return result
            
        except Exception as e:
            self.logger.error(f"技能分析失败 {skill_data.skill_id}: {e}", exc_info=True)
            # 返回基本分析结果
            return AnalysisResult(
                structural_integrity=0.3,
                functional_completeness=0.3,
                boundary_conditions={"error": str(e)},
                error_handling_quality=0.2,
                dependencies_analysis={},
                performance_indicators={},
                issues_found=[{"type": "analysis_error", "description": f"分析过程出错: {e}"}],
                recommendations=["修复分析错误", "检查技能数据结构"]
            )
    
    async def _analyze_structure(self, skill_data: SkillData) -> float:
        """分析结构完整性"""
        score = 0.5  # 基础分
        
        # 检查必要字段
        required_fields = ["skill_id", "name", "description", "category"]
        for field in required_fields:
            if getattr(skill_data, field, None):
                score += 0.1
        
        # 检查描述质量
        if skill_data.description and len(skill_data.description.strip()) > 20:
            score += 0.1
        
        # 检查示例
        if skill_data.examples and len(skill_data.examples) > 0:
            score += 0.1
        
        # 检查输入输出格式
        if skill_data.input_format and skill_data.output_format:
            score += 0.2
        
        return min(score, 1.0)  # 确保不超过1.0
    
    async def _analyze_functionality(self, skill_data: SkillData) -> float:
        """分析功能完整性"""
        score = 0.4  # 基础分
        
        # 基于描述分析功能完整性
        description = skill_data.description.lower()
        
        # 检查是否包含触发条件
        trigger_keywords = ["当", "如果", "当用户", "在...时", "trigger", "when"]
        if any(keyword in description for keyword in trigger_keywords):
            score += 0.2
        
        # 检查是否包含使用示例
        if skill_data.examples:
            score += 0.2
        
        # 检查是否明确输入输出
        if skill_data.input_format and skill_data.output_format:
            score += 0.2
        
        return min(score, 1.0)
    
    async def _analyze_boundary_conditions(self, skill_data: SkillData) -> Dict[str, Any]:
        """分析边界条件"""
        boundaries = {
            "input_constraints": {},
            "output_constraints": {},
            "assumptions": [],
            "limitations": []
        }
        
        # 从描述中提取边界条件
        description = skill_data.description.lower()
        
        # 检测常见边界关键词
        boundary_keywords = ["限制", "要求", "前提", "假设", "只能", "不能", "必须", 
                           "limitation", "requirement", "assumption", "constraint"]
        
        for keyword in boundary_keywords:
            if keyword in description:
                boundaries["assumptions"].append(f"检测到边界关键词: {keyword}")
        
        # 从元数据中提取边界条件
        if "constraints" in skill_data.metadata:
            boundaries["input_constraints"] = skill_data.metadata.get("constraints", {})
        
        return boundaries
    
    async def _analyze_error_handling(self, skill_data: SkillData) -> float:
        """分析错误处理质量"""
        score = 0.3  # 基础分
        
        # 检查元数据中的错误处理信息
        metadata = skill_data.metadata
        
        if "error_handling" in metadata:
            score += 0.3
        
        # 检查描述中是否提到错误处理
        description = skill_data.description.lower()
        error_keywords = ["错误", "异常", "失败", "回退", "备用", 
                         "error", "exception", "fallback", "retry"]
        
        keyword_count = sum(1 for keyword in error_keywords if keyword in description)
        if keyword_count > 0:
            score += min(0.3, keyword_count * 0.1)
        
        # 检查是否有示例包含错误情况
        for example in skill_data.examples:
            if "error" in example or "failure" in example:
                score += 0.2
                break
        
        return min(score, 1.0)
    
    async def _analyze_dependencies(self, skill_data: SkillData) -> Dict[str, float]:
        """分析依赖关系"""
        dependencies = {}
        
        for dep in skill_data.dependencies:
            # 简单评分：依赖越多，复杂度越高，但可用性可能降低
            if "core" in dep or "base" in dep:
                dependencies[dep] = 0.9  # 核心依赖，高可靠性
            elif "external" in dep or "api" in dep:
                dependencies[dep] = 0.6  # 外部依赖，中等可靠性
            else:
                dependencies[dep] = 0.7  # 普通依赖
        
        return dependencies
    
    async def _estimate_performance(self, skill_data: SkillData) -> Dict[str, float]:
        """预估性能指标"""
        performance = {
            "execution_speed": 0.7,  # 执行速度预估
            "resource_usage": 0.6,   # 资源使用预估
            "scalability": 0.5,      # 可扩展性
            "reliability": 0.8       # 可靠性
        }
        
        # 基于复杂度调整
        if skill_data.complexity == "simple":
            performance["execution_speed"] = 0.9
            performance["resource_usage"] = 0.8
        elif skill_data.complexity == "complex":
            performance["execution_speed"] = 0.5
            performance["resource_usage"] = 0.4
            performance["scalability"] = 0.3
        
        # 基于依赖数量调整
        dep_count = len(skill_data.dependencies)
        if dep_count > 5:
            performance["reliability"] *= 0.8
            performance["execution_speed"] *= 0.8
        
        return performance
    
    async def _detect_issues(self, skill_data: SkillData) -> List[Dict[str, Any]]:
        """检测问题"""
        issues = []
        
        # 检查描述长度
        if len(skill_data.description.strip()) < 30:
            issues.append({
                "type": "description_too_short",
                "severity": "medium",
                "description": "技能描述过短，可能无法清晰说明功能",
                "suggestion": "扩展描述，包括功能、触发条件、使用示例"
            })
        
        # 检查缺少示例
        if not skill_data.examples:
            issues.append({
                "type": "no_examples",
                "severity": "low",
                "description": "技能缺少使用示例",
                "suggestion": "添加至少一个使用示例"
            })
        
        # 检查输入输出格式
        if not skill_data.input_format or not skill_data.output_format:
            issues.append({
                "type": "missing_io_format",
                "severity": "medium",
                "description": "缺少明确的输入输出格式定义",
                "suggestion": "定义清晰的输入输出格式"
            })
        
        # 检查依赖过多
        if len(skill_data.dependencies) > 10:
            issues.append({
                "type": "too_many_dependencies",
                "severity": "high",
                "description": f"技能依赖过多({len(skill_data.dependencies)}个)，可能影响可靠性",
                "suggestion": "考虑减少依赖或模块化设计"
            })
        
        return issues
    
    async def _generate_recommendations(self, skill_data: SkillData, 
                                       issues: List[Dict[str, Any]]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于问题的建议
        for issue in issues:
            if "suggestion" in issue:
                recommendations.append(issue["suggestion"])
        
        # 通用建议
        if skill_data.complexity == "complex" and len(skill_data.dependencies) > 5:
            recommendations.append("考虑将复杂技能拆分为多个简单技能")
        
        if not any("测试" in rec or "test" in rec for rec in recommendations):
            recommendations.append("添加测试用例确保技能可靠性")
        
        return list(set(recommendations))  # 去重


class SkillComparator:
    """技能比较器 (Comparator Agent) - 比较技能差异和去重"""
    
    def __init__(self, existing_skills: List[SkillData]):
        self.existing_skills = existing_skills
        self.logger = logging.getLogger(f"{__name__}.SkillComparator")
    
    async def compare_skill(self, new_skill: SkillData) -> ComparisonResult:
        """比较新技能与现有技能"""
        self.logger.info(f"开始比较技能: {new_skill.name} (已有{len(self.existing_skills)}个技能)")
        
        try:
            # 1. 功能重叠度分析
            functional_overlap = await self._calculate_functional_overlap(new_skill)
            
            # 2. 总体重叠度评分
            overall_overlap_score = await self._calculate_overall_overlap(functional_overlap)
            
            # 3. 差异化评分
            differentiation_score = await self._assess_differentiation(new_skill)
            
            # 4. 创新价值评估
            innovation_value = await self._evaluate_innovation(new_skill)
            
            # 5. 可合并技能识别
            merge_candidates = await self._find_merge_candidates(new_skill, functional_overlap)
            
            # 6. 建议的修改
            recommended_changes = await self._suggest_changes(new_skill, functional_overlap)
            
            # 7. 独特性评估
            uniqueness_assessment = await self._assess_uniqueness(
                new_skill, overall_overlap_score, differentiation_score
            )
            
            result = ComparisonResult(
                functional_overlap=functional_overlap,
                overall_overlap_score=overall_overlap_score,
                differentiation_score=differentiation_score,
                innovation_value=innovation_value,
                merge_candidates=merge_candidates,
                recommended_changes=recommended_changes,
                uniqueness_assessment=uniqueness_assessment
            )
            
            self.logger.info(f"技能比较完成: {new_skill.name}, 重叠度={overall_overlap_score:.2f}, 差异化={differentiation_score:.2f}")
            return result
            
        except Exception as e:
            self.logger.error(f"技能比较失败 {new_skill.skill_id}: {e}", exc_info=True)
            return ComparisonResult(
                functional_overlap={},
                overall_overlap_score=0.0,
                differentiation_score=0.5,
                innovation_value=0.3,
                merge_candidates=[],
                recommended_changes=[{"error": str(e)}],
                uniqueness_assessment="比较过程出错"
            )
    
    async def _calculate_functional_overlap(self, new_skill: SkillData) -> Dict[str, float]:
        """计算功能重叠度"""
        overlaps = {}
        
        for existing_skill in self.existing_skills:
            if existing_skill.skill_id == new_skill.skill_id:
                continue
            
            # 基于名称相似度
            name_similarity = self._calculate_similarity(
                new_skill.name.lower(), 
                existing_skill.name.lower()
            )
            
            # 基于描述相似度
            desc_similarity = self._calculate_similarity(
                new_skill.description.lower(), 
                existing_skill.description.lower()
            )
            
            # 基于分类相似度
            category_similarity = 1.0 if new_skill.category == existing_skill.category else 0.3
            
            # 综合重叠度
            overlap_score = (name_similarity * 0.4 + 
                           desc_similarity * 0.4 + 
                           category_similarity * 0.2)
            
            if overlap_score > 0.3:  # 只记录显著重叠
                overlaps[existing_skill.skill_id] = overlap_score
        
        return overlaps
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简化版）"""
        if not text1 or not text2:
            return 0.0
        
        # 简单基于共享词汇的相似度计算
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def _calculate_overall_overlap(self, functional_overlap: Dict[str, float]) -> float:
        """计算总体重叠度评分"""
        if not functional_overlap:
            return 0.0
        
        # 取最高重叠度作为总体评分
        max_overlap = max(functional_overlap.values())
        
        # 如果有多个高度重叠的技能，提高总体重叠度
        high_overlap_count = sum(1 for score in functional_overlap.values() if score > 0.7)
        if high_overlap_count > 1:
            max_overlap = min(max_overlap + 0.1 * high_overlap_count, 1.0)
        
        return max_overlap
    
    async def _assess_differentiation(self, new_skill: SkillData) -> float:
        """评估差异化程度"""
        if not self.existing_skills:
            return 1.0  # 如果没有现有技能，完全差异化
        
        # 检查新技能的独特特征
        unique_features = []
        
        # 检查名称独特性
        existing_names = [s.name.lower() for s in self.existing_skills]
        if new_skill.name.lower() not in existing_names:
            unique_features.append("name")
        
        # 检查分类独特性
        existing_categories = [s.category for s in self.existing_skills]
        if new_skill.category not in existing_categories:
            unique_features.append("category")
        
        # 检查功能描述独特性
        new_desc_words = set(new_skill.description.lower().split())
        all_desc_words = set()
        for skill in self.existing_skills:
            all_desc_words.update(skill.description.lower().split())
        
        unique_words = new_desc_words - all_desc_words
        if len(unique_words) > 5:
            unique_features.append("description")
        
        # 基于独特特征数量计算差异化评分
        base_score = 0.3
        feature_score = len(unique_features) * 0.2
        
        return min(base_score + feature_score, 1.0)
    
    async def _evaluate_innovation(self, new_skill: SkillData) -> float:
        """评估创新价值"""
        innovation_score = 0.5  # 基础分
        
        # 基于分类的创新性
        common_categories = ["utility", "helper", "tool", "processor"]
        if new_skill.category not in common_categories:
            innovation_score += 0.2
        
        # 基于复杂度的创新性
        if new_skill.complexity == "complex":
            innovation_score += 0.1
        
        # 基于依赖的创新性（使用新技术/库）
        innovation_keywords = ["ai", "ml", "neural", "transformer", "llm", "deep"]
        for dep in new_skill.dependencies:
            if any(keyword in dep.lower() for keyword in innovation_keywords):
                innovation_score += 0.1
        
        # 基于描述的创新性
        innovation_desc_keywords = ["创新", "新型", "首创", "先进", "智能", 
                                  "innovative", "novel", "advanced", "intelligent"]
        description = new_skill.description.lower()
        keyword_count = sum(1 for keyword in innovation_desc_keywords if keyword in description)
        innovation_score += min(keyword_count * 0.05, 0.2)
        
        return min(innovation_score, 1.0)
    
    async def _find_merge_candidates(self, new_skill: SkillData, 
                                   functional_overlap: Dict[str, float]) -> List[str]:
        """识别可合并的技能"""
        candidates = []
        
        for skill_id, overlap_score in functional_overlap.items():
            if overlap_score > 0.7:  # 高度重叠
                candidates.append(skill_id)
            elif overlap_score > 0.5 and len(new_skill.dependencies) < 5:
                # 中等重叠且新技能依赖较少，适合合并
                candidates.append(skill_id)
        
        return candidates
    
    async def _suggest_changes(self, new_skill: SkillData, 
                             functional_overlap: Dict[str, float]) -> List[Dict[str, Any]]:
        """建议修改以避免重复"""
        suggestions = []
        
        for skill_id, overlap_score in functional_overlap.items():
            if overlap_score > 0.8:
                suggestions.append({
                    "type": "high_overlap",
                    "skill_id": skill_id,
                    "overlap_score": overlap_score,
                    "suggestion": "考虑重新设计技能功能或与现有技能合并",
                    "urgency": "high"
                })
            elif overlap_score > 0.6:
                suggestions.append({
                    "type": "moderate_overlap",
                    "skill_id": skill_id,
                    "overlap_score": overlap_score,
                    "suggestion": "明确区分与现有技能的功能边界",
                    "urgency": "medium"
                })
        
        return suggestions
    
    async def _assess_uniqueness(self, new_skill: SkillData, 
                               overlap_score: float, 
                               differentiation_score: float) -> str:
        """评估独特性"""
        if overlap_score < 0.3 and differentiation_score > 0.7:
            return "高度独特 - 与现有技能明显不同"
        elif overlap_score < 0.5 and differentiation_score > 0.5:
            return "较为独特 - 有一定的差异化"
        elif overlap_score > 0.7:
            return "高度重叠 - 与现有技能功能相似"
        else:
            return "中等重叠 - 需要进一步差异化"


class SkillGrader:
    """技能评分器 (Grader Agent) - 综合质量评分和认证"""
    
    # 评分维度权重
    DIMENSION_WEIGHTS = {
        "practicality": 0.25,      # 实用性
        "accuracy": 0.20,          # 准确性
        "usability": 0.15,         # 易用性
        "reliability": 0.15,       # 可靠性
        "maintainability": 0.10,   # 可维护性
        "performance": 0.10,       # 性能
        "innovation": 0.05         # 创新性
    }
    
    # 质量等级阈值
    QUALITY_THRESHOLDS = {
        "excellent": 0.85,
        "good": 0.70,
        "fair": 0.55,
        "poor": 0.0
    }
    
    # 认证等级
    CERTIFICATION_LEVELS = {
        "platinum": 0.90,
        "gold": 0.80,
        "silver": 0.70,
        "bronze": 0.60
    }
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SkillGrader")
    
    async def grade_skill(self, skill_data: SkillData, 
                         analysis_result: AnalysisResult,
                         comparison_result: ComparisonResult) -> GradeResult:
        """综合评分技能质量"""
        self.logger.info(f"开始评分技能: {skill_data.name}")
        
        try:
            # 1. 计算各维度评分
            scores = await self._calculate_dimension_scores(
                skill_data, analysis_result, comparison_result
            )
            
            # 2. 计算综合评分
            overall_grade = await self._calculate_overall_grade(scores)
            
            # 3. 确定质量等级
            quality_level = await self._determine_quality_level(overall_grade)
            
            # 4. 颁发认证
            certification = await self._issue_certification(overall_grade)
            
            # 5. 识别优点和缺点
            strengths, weaknesses = await self._identify_strengths_weaknesses(scores)
            
            # 6. 识别关键问题
            critical_issues = await self._identify_critical_issues(
                skill_data, analysis_result, scores
            )
            
            result = GradeResult(
                scores=scores,
                overall_grade=overall_grade,
                quality_level=quality_level,
                certification=certification,
                strengths=strengths,
                weaknesses=weaknesses,
                critical_issues=critical_issues
            )
            
            self.logger.info(f"技能评分完成: {skill_data.name}, 综合评分={overall_grade:.2f}, 等级={quality_level}")
            return result
            
        except Exception as e:
            self.logger.error(f"技能评分失败 {skill_data.skill_id}: {e}", exc_info=True)
            return GradeResult(
                scores={"error": 0.0},
                overall_grade=0.3,
                quality_level="poor",
                certification=None,
                strengths=[],
                weaknesses=["评分过程出错"],
                critical_issues=[f"评分错误: {e}"]
            )
    
    async def _calculate_dimension_scores(self, skill_data: SkillData,
                                        analysis_result: AnalysisResult,
                                        comparison_result: ComparisonResult) -> Dict[str, float]:
        """计算各维度评分"""
        scores = {}
        
        # 1. 实用性评分
        scores["practicality"] = await self._score_practicality(
            skill_data, analysis_result
        )
        
        # 2. 准确性评分
        scores["accuracy"] = await self._score_accuracy(
            skill_data, analysis_result
        )
        
        # 3. 易用性评分
        scores["usability"] = await self._score_usability(
            skill_data, analysis_result
        )
        
        # 4. 可靠性评分
        scores["reliability"] = await self._score_reliability(
            skill_data, analysis_result
        )
        
        # 5. 可维护性评分
        scores["maintainability"] = await self._score_maintainability(
            skill_data, analysis_result
        )
        
        # 6. 性能评分
        scores["performance"] = await self._score_performance(
            skill_data, analysis_result
        )
        
        # 7. 创新性评分
        scores["innovation"] = await self._score_innovation(
            skill_data, comparison_result
        )
        
        return scores
    
    async def _score_practicality(self, skill_data: SkillData,
                                analysis_result: AnalysisResult) -> float:
        """评分实用性"""
        score = 0.5  # 基础分
        
        # 基于功能完整性
        score += analysis_result.functional_completeness * 0.3
        
        # 基于问题数量
        issue_count = len(analysis_result.issues_found)
        if issue_count == 0:
            score += 0.2
        elif issue_count <= 3:
            score += 0.1
        
        # 基于示例质量
        if skill_data.examples:
            score += 0.1
        
        return min(score, 1.0)
    
    async def _score_accuracy(self, skill_data: SkillData,
                            analysis_result: AnalysisResult) -> float:
        """评分准确性"""
        score = 0.6  # 基础分
        
        # 基于错误处理质量
        score += analysis_result.error_handling_quality * 0.2
        
        # 基于边界条件清晰度
        if analysis_result.boundary_conditions.get("assumptions"):
            score += 0.1
        
        # 基于依赖可靠性
        if analysis_result.dependencies_analysis:
            avg_dep_score = sum(analysis_result.dependencies_analysis.values()) / len(analysis_result.dependencies_analysis)
            score += avg_dep_score * 0.1
        
        return min(score, 1.0)
    
    async def _score_usability(self, skill_data: SkillData,
                             analysis_result: AnalysisResult) -> float:
        """评分易用性"""
        score = 0.5  # 基础分
        
        # 基于描述质量
        if len(skill_data.description.strip()) > 50:
            score += 0.2
        
        # 基于示例数量
        example_count = len(skill_data.examples)
        if example_count >= 3:
            score += 0.2
        elif example_count >= 1:
            score += 0.1
        
        # 基于输入输出格式
        if skill_data.input_format and skill_data.output_format:
            score += 0.1
        
        return min(score, 1.0)
    
    async def _score_reliability(self, skill_data: SkillData,
                               analysis_result: AnalysisResult) -> float:
        """评分可靠性"""
        score = 0.7  # 基础分（假设技能基本可靠）
        
        # 基于结构完整性
        score += analysis_result.structural_integrity * 0.1
        
        # 基于性能指标
        perf_score = analysis_result.performance_indicators.get("reliability", 0.5)
        score += perf_score * 0.1
        
        # 基于问题严重性
        critical_issues = [i for i in analysis_result.issues_found 
                          if i.get("severity") == "high"]
        if not critical_issues:
            score += 0.1
        
        # 基于依赖数量（依赖越少越可靠）
        dep_count = len(skill_data.dependencies)
        if dep_count == 0:
            score += 0.1
        elif dep_count > 10:
            score -= 0.1
        
        return max(0.0, min(score, 1.0))  # 确保在0-1范围内
    
    async def _score_maintainability(self, skill_data: SkillData,
                                   analysis_result: AnalysisResult) -> float:
        """评分可维护性"""
        score = 0.5  # 基础分
        
        # 基于文档完整性
        if skill_data.metadata.get("documentation"):
            score += 0.2
        
        # 基于复杂度
        if skill_data.complexity == "simple":
            score += 0.2
        elif skill_data.complexity == "complex":
            score += 0.1  # 复杂技能维护难度大
        
        # 基于依赖清晰度
        if skill_data.dependencies:
            # 有明确依赖比没有依赖更容易维护
            score += 0.1
        
        return min(score, 1.0)
    
    async def _score_performance(self, skill_data: SkillData,
                               analysis_result: AnalysisResult) -> float:
        """评分性能"""
        # 直接使用性能预估指标
        perf_indicators = analysis_result.performance_indicators
        
        if not perf_indicators:
            return 0.5
        
        # 计算平均性能评分
        performance_keys = ["execution_speed", "resource_usage", "scalability"]
        valid_scores = [perf_indicators.get(k, 0.5) for k in performance_keys]
        
        if valid_scores:
            return sum(valid_scores) / len(valid_scores)
        else:
            return 0.5
    
    async def _score_innovation(self, skill_data: SkillData,
                              comparison_result: ComparisonResult) -> float:
        """评分创新性"""
        # 直接使用比较器中的创新价值评分
        return comparison_result.innovation_value
    
    async def _calculate_overall_grade(self, scores: Dict[str, float]) -> float:
        """计算综合评分"""
        if not scores:
            return 0.0
        
        overall_grade = 0.0
        total_weight = 0.0
        
        for dimension, weight in self.DIMENSION_WEIGHTS.items():
            if dimension in scores:
                overall_grade += scores[dimension] * weight
                total_weight += weight
        
        # 如果某些维度缺失，按比例调整
        if total_weight > 0:
            overall_grade /= total_weight
        
        return overall_grade
    
    async def _determine_quality_level(self, overall_grade: float) -> str:
        """确定质量等级"""
        for level, threshold in self.QUALITY_THRESHOLDS.items():
            if overall_grade >= threshold:
                return level
        return "poor"
    
    async def _issue_certification(self, overall_grade: float) -> Optional[str]:
        """颁发认证"""
        for level, threshold in self.CERTIFICATION_LEVELS.items():
            if overall_grade >= threshold:
                return level
        return None
    
    async def _identify_strengths_weaknesses(self, scores: Dict[str, float]) -> Tuple[List[str], List[str]]:
        """识别优点和缺点"""
        strengths = []
        weaknesses = []
        
        dimension_names = {
            "practicality": "实用性",
            "accuracy": "准确性",
            "usability": "易用性",
            "reliability": "可靠性",
            "maintainability": "可维护性",
            "performance": "性能",
            "innovation": "创新性"
        }
        
        for dimension, score in scores.items():
            if score >= 0.8:
                strengths.append(f"{dimension_names.get(dimension, dimension)}优秀({score:.2f})")
            elif score <= 0.4:
                weaknesses.append(f"{dimension_names.get(dimension, dimension)}不足({score:.2f})")
        
        return strengths, weaknesses
    
    async def _identify_critical_issues(self,
                                      skill_data: SkillData,
                                      analysis_result: AnalysisResult,
                                      scores: Dict[str, float]) -> List[str]:
        """识别关键问题"""
        critical_issues = []
        
        # 检查评分低的关键维度
        critical_dimensions = ["reliability", "accuracy", "practicality"]
        for dimension in critical_dimensions:
            if scores.get(dimension, 1.0) < 0.4:
                critical_issues.append(f"关键维度'{dimension}'评分过低({scores[dimension]:.2f})")
        
        # 检查分析中的高严重性问题
        high_severity_issues = [issue for issue in analysis_result.issues_found 
                               if issue.get("severity") == "high"]
        for issue in high_severity_issues:
            critical_issues.append(f"高严重性问题: {issue.get('description', 'N/A')}")
        
        # 检查结构完整性
        if analysis_result.structural_integrity < 0.5:
            critical_issues.append(f"结构完整性不足({analysis_result.structural_integrity:.2f})")
        
        # 检查错误处理
        if analysis_result.error_handling_quality < 0.4:
            critical_issues.append(f"错误处理质量不足({analysis_result.error_handling_quality:.2f})")
        
        return critical_issues


class SkillQualityEvaluator:
    """技能质量评估器主类 - 协调三元评估代理工作流程"""
    
    def __init__(self, existing_skills: Optional[List[SkillData]] = None):
        self.analyzer = SkillAnalyzer()
        self.comparator = SkillComparator(existing_skills or [])
        self.grader = SkillGrader()
        self.logger = logging.getLogger(f"{__name__}.SkillQualityEvaluator")
        self.evaluation_history: Dict[str, QualityReport] = {}
    
    async def evaluate_skill(self, skill_data: SkillData) -> QualityReport:
        """执行完整的技能质量评估"""
        evaluation_id = f"eval_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        
        self.logger.info(f"🎯 开始技能质量评估: {skill_data.name} ({skill_data.skill_id})")
        self.logger.info(f"  评估ID: {evaluation_id}")
        
        try:
            # 1. 结构分析阶段
            self.logger.info("🔍 阶段1: 技能结构分析")
            analysis_result = await self.analyzer.analyze_skill(skill_data)
            
            # 2. 比较分析阶段
            self.logger.info("🔍 阶段2: 技能比较分析")
            comparison_result = await self.comparator.compare_skill(skill_data)
            
            # 3. 综合评分阶段
            self.logger.info("🔍 阶段3: 综合质量评分")
            grade_result = await self.grader.grade_skill(
                skill_data, analysis_result, comparison_result
            )
            
            # 4. 生成最终质量报告
            overall_score = grade_result.overall_grade * 100  # 转换为0-100分
            
            # 确定质量状态
            quality_status = self._determine_quality_status(
                overall_score, 
                grade_result.quality_level,
                analysis_result.issues_found
            )
            
            # 生成整体建议
            recommendations = self._generate_overall_recommendations(
                analysis_result, comparison_result, grade_result
            )
            
            report = QualityReport(
                skill_id=skill_data.skill_id,
                skill_name=skill_data.name,
                evaluation_id=evaluation_id,
                analysis_result=analysis_result,
                comparison_result=comparison_result,
                grade_result=grade_result,
                overall_score=overall_score,
                quality_status=quality_status,
                recommendations=recommendations
            )
            
            # 保存到历史记录
            self.evaluation_history[evaluation_id] = report
            
            self.logger.info(f"✅ 技能质量评估完成: {skill_data.name}")
            self.logger.info(f"  综合评分: {overall_score:.1f}/100")
            self.logger.info(f"  质量状态: {quality_status}")
            self.logger.info(f"  质量等级: {grade_result.quality_level}")
            
            return report
            
        except Exception as e:
            self.logger.error(f"❌ 技能质量评估失败 {skill_data.skill_id}: {e}", exc_info=True)
            # 返回错误报告
            return QualityReport(
                skill_id=skill_data.skill_id,
                skill_name=skill_data.name,
                evaluation_id=evaluation_id,
                analysis_result=AnalysisResult(
                    structural_integrity=0.0,
                    functional_completeness=0.0,
                    boundary_conditions={"error": str(e)},
                    error_handling_quality=0.0,
                    dependencies_analysis={},
                    performance_indicators={},
                    issues_found=[{"type": "evaluation_error", "description": f"评估过程出错: {e}"}],
                    recommendations=["重新运行评估"]
                ),
                comparison_result=ComparisonResult(
                    functional_overlap={},
                    overall_overlap_score=0.0,
                    differentiation_score=0.0,
                    innovation_value=0.0,
                    merge_candidates=[],
                    recommended_changes=[{"error": str(e)}],
                    uniqueness_assessment="评估过程出错"
                ),
                grade_result=GradeResult(
                    scores={"error": 0.0},
                    overall_grade=0.0,
                    quality_level="poor",
                    certification=None,
                    strengths=[],
                    weaknesses=["评估过程出错"],
                    critical_issues=[f"评估错误: {e}"]
                ),
                overall_score=0.0,
                quality_status="rejected",
                recommendations=[{"type": "system_error", "action": "联系系统管理员"}]
            )
    
    def _determine_quality_status(self, overall_score: float, 
                                quality_level: str,
                                issues_found: List[Dict[str, Any]]) -> str:
        """确定质量状态"""
        if overall_score < 50:
            return "rejected"
        elif overall_score < 70:
            return "needs_improvement"
        elif any(issue.get("severity") == "high" for issue in issues_found):
            return "needs_improvement"
        elif overall_score >= 85:
            return "certified"
        else:
            return "approved"
    
    def _generate_overall_recommendations(self,
                                        analysis_result: AnalysisResult,
                                        comparison_result: ComparisonResult,
                                        grade_result: GradeResult) -> List[Dict[str, Any]]:
        """生成整体建议"""
        recommendations = []
        
        # 来自分析器的建议
        for rec in analysis_result.recommendations:
            recommendations.append({
                "source": "analyzer",
                "type": "improvement",
                "description": rec,
                "priority": "medium"
            })
        
        # 来自比较器的建议
        for change in comparison_result.recommended_changes:
            recommendations.append({
                "source": "comparator",
                "type": change.get("type", "differentiation"),
                "description": change.get("suggestion", ""),
                "priority": change.get("urgency", "medium"),
                "related_skill": change.get("skill_id")
            })
        
        # 来自评分器的关键问题
        for issue in grade_result.critical_issues:
            recommendations.append({
                "source": "grader",
                "type": "critical",
                "description": f"关键问题: {issue}",
                "priority": "high"
            })
        
        # 基于质量等级的建议
        if grade_result.quality_level == "poor":
            recommendations.append({
                "source": "grader",
                "type": "overall",
                "description": "技能质量较差，建议重新设计或大幅改进",
                "priority": "high"
            })
        elif grade_result.quality_level == "excellent" and not grade_result.certification:
            recommendations.append({
                "source": "grader",
                "type": "certification",
                "description": "技能质量优秀，建议申请高级认证",
                "priority": "low"
            })
        
        return recommendations
    
    async def evaluate_multiple_skills(self, skills_data: List[SkillData]) -> Dict[str, QualityReport]:
        """批量评估多个技能"""
        results = {}
        
        self.logger.info(f"开始批量评估 {len(skills_data)} 个技能")
        
        for skill_data in skills_data:
            try:
                report = await self.evaluate_skill(skill_data)
                results[skill_data.skill_id] = report
            except Exception as e:
                self.logger.error(f"批量评估失败 {skill_data.skill_id}: {e}")
        
        self.logger.info(f"批量评估完成: {len(results)}/{len(skills_data)} 个技能成功")
        
        return results
    
    def get_evaluation_history(self, skill_id: Optional[str] = None) -> List[QualityReport]:
        """获取评估历史记录"""
        if skill_id:
            return [report for report in self.evaluation_history.values() 
                   if report.skill_id == skill_id]
        else:
            return list(self.evaluation_history.values())
    
    def clear_evaluation_history(self):
        """清空评估历史记录"""
        self.evaluation_history.clear()
        self.logger.info("评估历史记录已清空")


# 工具函数
def create_skill_data_from_dict(data: Dict[str, Any]) -> SkillData:
    """从字典创建SkillData对象"""
    return SkillData(
        skill_id=data.get("skill_id", f"skill_{uuid.uuid4().hex[:8]}"),
        name=data.get("name", "未命名技能"),
        description=data.get("description", ""),
        category=data.get("category", "general"),
        complexity=data.get("complexity", "moderate"),
        input_format=data.get("input_format"),
        output_format=data.get("output_format"),
        examples=data.get("examples", []),
        dependencies=data.get("dependencies", []),
        metadata=data.get("metadata", {}),
        created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
        updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
    )


async def main():
    """主函数 - 测试技能质量评估器"""
    import sys
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建测试技能
    test_skill = SkillData(
        skill_id="test_python_analyzer",
        name="Python代码分析器",
        description="分析Python代码质量，检查代码规范、潜在问题和优化建议。当用户提交Python代码时自动触发分析。",
        category="code_analysis",
        complexity="moderate",
        input_format={"type": "python_code", "format": "string"},
        output_format={"type": "analysis_report", "format": "json"},
        examples=[
            {"input": "def foo(): pass", "output": {"issues": ["函数名不符合规范"]}},
            {"input": "x = 10\ny = x + 5", "output": {"issues": []}}
        ],
        dependencies=["python_parser", "code_style_rules"],
        metadata={"version": "1.0", "author": "test"}
    )
    
    # 创建现有技能（用于比较）
    existing_skills = [
        SkillData(
            skill_id="existing_code_review",
            name="代码审查助手",
            description="审查代码质量和规范",
            category="code_analysis",
            complexity="simple",
            examples=[],
            dependencies=[]
        )
    ]
    
    # 创建评估器
    evaluator = SkillQualityEvaluator(existing_skills=existing_skills)
    
    # 执行评估
    print("🚀 开始技能质量评估测试...")
    report = await evaluator.evaluate_skill(test_skill)
    
    # 打印结果
    print(f"\n📊 评估结果:")
    print(f"  技能: {report.skill_name} ({report.skill_id})")
    print(f"  综合评分: {report.overall_score:.1f}/100")
    print(f"  质量状态: {report.quality_status}")
    print(f"  质量等级: {report.grade_result.quality_level}")
    
    if report.grade_result.certification:
        print(f"  认证等级: {report.grade_result.certification}")
    
    print(f"\n📈 各维度评分:")
    for dimension, score in report.grade_result.scores.items():
        print(f"  {dimension}: {score:.2f}")
    
    print(f"\n✅ 优点:")
    for strength in report.grade_result.strengths:
        print(f"  • {strength}")
    
    print(f"\n⚠️ 缺点:")
    for weakness in report.grade_result.weaknesses:
        print(f"  • {weakness}")
    
    print(f"\n🚨 关键问题:")
    for issue in report.grade_result.critical_issues:
        print(f"  • {issue}")
    
    print(f"\n💡 改进建议:")
    for i, rec in enumerate(report.recommendations, 1):
        print(f"  {i}. [{rec.get('source')}] {rec.get('description')}")
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))