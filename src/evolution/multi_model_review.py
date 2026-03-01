#!/usr/bin/env python3
"""
多模型审查和安全护栏
使用多个LLM模型对进化计划进行独立审查，确保安全和质量
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ReviewStatus(Enum):
    """审查状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_MODIFICATION = "needs_modification"


class ReviewSeverity(Enum):
    """问题严重性"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ReviewIssue:
    """审查问题"""
    issue_id: str
    description: str
    severity: ReviewSeverity
    category: str  # safety, quality, performance, etc.
    location: Optional[str] = None
    suggestion: Optional[str] = None
    model_source: Optional[str] = None


@dataclass
class ModelReviewResult:
    """单个模型审查结果"""
    model_name: str
    status: ReviewStatus
    confidence: float  # 0.0-1.0
    issues: List[ReviewIssue]
    summary: str
    timestamp: str
    review_duration: float  # seconds


class MultiModelReview:
    """多模型审查器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 配置的模型列表（模拟，实际项目中会集成真实LLM API）
        self.available_models = [
            {"name": "safety_model", "role": "安全检查专家", "focus": ["安全", "风险", "合规"]},
            {"name": "quality_model", "role": "代码质量专家", "focus": ["代码质量", "架构", "可维护性"]},
            {"name": "business_model", "role": "商业价值专家", "focus": ["商业价值", "ROI", "用户价值"]},
            {"name": "technical_model", "role": "技术可行性专家", "focus": ["技术可行性", "复杂度", "实现难度"]}
        ]
        
        # 审查历史
        self.review_history: List[Dict[str, Any]] = []
        self.max_history = 100
        
        # 安全护栏配置
        self.safety_guardrails = {
            "max_risk_score": 0.7,  # 最大风险评分阈值
            "required_approvals": 2,  # 最少批准数
            "critical_issue_threshold": 1,  # 关键问题阈值
            "consensus_threshold": 0.75  # 共识阈值
        }
        
        self.logger.info(f"多模型审查器初始化完成，可用模型: {len(self.available_models)}个")
    
    async def single_model_review(self, plan: Any) -> Dict[str, Any]:
        """单模型审查（用于中等影响级别）"""
        self.logger.info(f"执行单模型审查: {getattr(plan, 'plan_id', 'unknown')}")
        
        # 使用质量模型进行审查
        model = self.available_models[1]  # quality_model
        result = await self._review_with_model(plan, model)
        
        # 生成综合结果
        approved = result.status == ReviewStatus.APPROVED
        issues_count = len(result.issues)
        critical_issues = len([i for i in result.issues if i.severity in [ReviewSeverity.ERROR, ReviewSeverity.CRITICAL]])
        
        review_result = {
            "model_used": model["name"],
            "approved": approved,
            "confidence": result.confidence,
            "issues_count": issues_count,
            "critical_issues_count": critical_issues,
            "summary": result.summary,
            "timestamp": result.timestamp,
            "review_duration": result.review_duration
        }
        
        if not approved and result.issues:
            review_result["reason"] = result.issues[0].description
            review_result["suggestion"] = result.issues[0].suggestion
        
        # 记录审查历史
        self._record_review(review_result, "single", plan)
        
        return review_result
    
    async def multi_model_review(self, plan: Any) -> Dict[str, Any]:
        """多模型审查（用于重大影响级别）"""
        self.logger.info(f"执行多模型审查: {getattr(plan, 'plan_id', 'unknown')}")
        
        # 并行运行多个模型审查
        review_tasks = []
        for model in self.available_models:
            task = self._review_with_model(plan, model)
            review_tasks.append(task)
        
        results = await asyncio.gather(*review_tasks)
        
        # 分析审查结果
        analysis = await self._analyze_review_results(results)
        
        # 应用安全护栏
        final_decision = await self._apply_safety_guardrails(analysis, plan)
        
        # 生成综合报告
        comprehensive_report = await self._generate_comprehensive_report(results, analysis, final_decision)
        
        review_result = {
            "review_type": "multi_model",
            "models_used": [model["name"] for model in self.available_models],
            "total_reviews": len(results),
            "approval_rate": analysis["approval_rate"],
            "consensus_level": analysis["consensus_level"],
            "critical_issues_total": analysis["critical_issues_total"],
            "final_decision": final_decision["decision"],
            "final_approved": final_decision["approved"],
            "confidence_score": final_decision["confidence"],
            "risk_score": final_decision["risk_score"],
            "comprehensive_report": comprehensive_report,
            "timestamp": datetime.now().isoformat(),
            "review_duration": sum(r.review_duration for r in results)
        }
        
        # 记录审查历史
        self._record_review(review_result, "multi", plan)
        
        return review_result
    
    async def _review_with_model(self, plan: Any, model_config: Dict[str, Any]) -> ModelReviewResult:
        """使用特定模型进行审查"""
        model_name = model_config["name"]
        model_role = model_config["role"]
        focus_areas = model_config["focus"]
        
        self.logger.debug(f"开始模型审查: {model_name} ({model_role})")
        start_time = datetime.now()
        
        try:
            # 模拟模型审查过程
            # 在实际项目中，这里会调用真正的LLM API
            
            # 提取计划信息
            plan_id = getattr(plan, 'plan_id', 'unknown')
            description = getattr(plan, 'description', '')
            impact_level = getattr(plan, 'impact_level', None)
            target_files = getattr(plan, 'target_files', [])
            expected_benefits = getattr(plan, 'expected_benefits', [])
            risks = getattr(plan, 'risks', [])
            
            # 根据模型角色生成审查结果
            if model_name == "safety_model":
                result = await self._safety_model_review(
                    plan_id, description, target_files, risks, impact_level
                )
            elif model_name == "quality_model":
                result = await self._quality_model_review(
                    plan_id, description, target_files, expected_benefits
                )
            elif model_name == "business_model":
                result = await self._business_model_review(
                    plan_id, description, expected_benefits, risks
                )
            elif model_name == "technical_model":
                result = await self._technical_model_review(
                    plan_id, description, target_files, expected_benefits
                )
            else:
                result = await self._generic_model_review(
                    plan_id, description, focus_areas
                )
            
            # 计算审查持续时间
            duration = (datetime.now() - start_time).total_seconds()
            
            return ModelReviewResult(
                model_name=model_name,
                status=result["status"],
                confidence=result["confidence"],
                issues=result["issues"],
                summary=result["summary"],
                timestamp=datetime.now().isoformat(),
                review_duration=duration
            )
            
        except Exception as e:
            self.logger.error(f"模型审查失败 ({model_name}): {e}")
            duration = (datetime.now() - start_time).total_seconds()
            
            # 返回错误结果
            return ModelReviewResult(
                model_name=model_name,
                status=ReviewStatus.REJECTED,
                confidence=0.0,
                issues=[
                    ReviewIssue(
                        issue_id=f"error_{model_name}",
                        description=f"模型审查过程中发生错误: {str(e)}",
                        severity=ReviewSeverity.CRITICAL,
                        category="system_error",
                        model_source=model_name
                    )
                ],
                summary=f"{model_role}审查失败: {str(e)}",
                timestamp=datetime.now().isoformat(),
                review_duration=duration
            )
    
    async def _safety_model_review(
        self, 
        plan_id: str, 
        description: str, 
        target_files: List[str], 
        risks: List[str],
        impact_level: Any
    ) -> Dict[str, Any]:
        """安全检查模型"""
        issues = []
        description_lower = description.lower()
        
        # 检查危险操作
        dangerous_patterns = [
            ("删除.*系统", "尝试删除系统文件", ReviewSeverity.CRITICAL),
            ("格式化", "尝试格式化操作", ReviewSeverity.CRITICAL),
            ("支付", "涉及支付操作", ReviewSeverity.CRITICAL),
            ("资金转移", "涉及资金转移", ReviewSeverity.CRITICAL),
            ("执行命令", "执行系统命令", ReviewSeverity.ERROR),
            ("修改密码", "修改密码操作", ReviewSeverity.ERROR),
            ("清空数据", "清空数据操作", ReviewSeverity.ERROR)
        ]
        
        for pattern, issue_desc, severity in dangerous_patterns:
            if pattern in description_lower:
                issues.append(ReviewIssue(
                    issue_id=f"safety_{len(issues)}",
                    description=f"安全检查: {issue_desc}",
                    severity=severity,
                    category="safety",
                    suggestion="移除或修改涉及危险操作的代码",
                    model_source="safety_model"
                ))
        
        # 检查目标文件安全性
        sensitive_paths = [
            "/etc/", "/bin/", "/usr/", "/var/", "/root/",
            "C:\\Windows\\", "C:\\Program Files\\", "constitution/"
        ]
        
        for file_path in target_files:
            for sensitive_path in sensitive_paths:
                if file_path.startswith(sensitive_path):
                    issues.append(ReviewIssue(
                        issue_id=f"safety_{len(issues)}",
                        description=f"目标文件位于敏感目录: {file_path}",
                        severity=ReviewSeverity.CRITICAL,
                        category="safety",
                        suggestion="修改目标文件路径，避免敏感目录",
                        model_source="safety_model"
                    ))
                    break
        
        # 评估风险描述
        if not risks or "无风险" in " ".join(risks):
            issues.append(ReviewIssue(
                issue_id=f"safety_{len(issues)}",
                description="风险描述不足或过于乐观",
                severity=ReviewSeverity.WARNING,
                category="risk_assessment",
                suggestion="提供更详细的风险评估",
                model_source="safety_model"
            ))
        
        # 根据影响级别调整严格度
        risk_score = self._calculate_risk_score(issues, impact_level)
        
        # 决定批准状态
        critical_issues = len([i for i in issues if i.severity in [ReviewSeverity.ERROR, ReviewSeverity.CRITICAL]])
        approved = critical_issues == 0 and risk_score < 0.6
        
        return {
            "status": ReviewStatus.APPROVED if approved else ReviewStatus.REJECTED,
            "confidence": max(0.0, 1.0 - risk_score),
            "issues": issues,
            "summary": f"安全检查完成，发现{len(issues)}个问题，其中{critical_issues}个关键问题。风险评分: {risk_score:.2f}"
        }
    
    async def _quality_model_review(
        self,
        plan_id: str,
        description: str,
        target_files: List[str],
        expected_benefits: List[str]
    ) -> Dict[str, Any]:
        """代码质量模型"""
        issues = []
        
        # 检查目标文件类型
        code_files = [f for f in target_files if f.endswith(('.py', '.js', '.ts', '.java', '.cpp'))]
        non_code_files = [f for f in target_files if not f.endswith(('.py', '.js', '.ts', '.java', '.cpp'))]
        
        if code_files:
            # 检查是否有测试文件
            test_files = [f for f in code_files if 'test' in f.lower()]
            if not test_files and len(code_files) > 1:
                issues.append(ReviewIssue(
                    issue_id=f"quality_{len(issues)}",
                    description="修改代码文件但未包含测试文件",
                    severity=ReviewSeverity.WARNING,
                    category="testing",
                    suggestion="添加或修改对应的测试文件",
                    model_source="quality_model"
                ))
        
        # 检查预期收益是否具体
        if expected_benefits:
            measurable_benefits = 0
            for benefit in expected_benefits:
                if any(keyword in benefit for keyword in ["提高", "降低", "减少", "增加", "优化", "改进"]):
                    measurable_benefits += 1
            
            if measurable_benefits < len(expected_benefits) * 0.5:
                issues.append(ReviewIssue(
                    issue_id=f"quality_{len(issues)}",
                    description="预期收益不够具体或可衡量",
                    severity=ReviewSeverity.WARNING,
                    category="measurement",
                    suggestion="使用具体指标描述预期收益（如：提高性能20%）",
                    model_source="quality_model"
                ))
        
        # 检查描述是否具体
        if len(description) < 20:
            issues.append(ReviewIssue(
                issue_id=f"quality_{len(issues)}",
                description="计划描述过于简略",
                severity=ReviewSeverity.INFO,
                category="documentation",
                suggestion="提供更详细的计划描述",
                model_source="quality_model"
            ))
        
        # 质量评分
        quality_score = self._calculate_quality_score(issues, code_files, expected_benefits)
        approved = quality_score > 0.4
        
        return {
            "status": ReviewStatus.APPROVED if approved else ReviewStatus.NEEDS_MODIFICATION,
            "confidence": quality_score,
            "issues": issues,
            "summary": f"代码质量审查完成，发现{len(issues)}个问题。质量评分: {quality_score:.2f}"
        }
    
    async def _business_model_review(
        self,
        plan_id: str,
        description: str,
        expected_benefits: List[str],
        risks: List[str]
    ) -> Dict[str, Any]:
        """商业价值模型"""
        issues = []
        
        # 检查是否对齐创业者价值
        entrepreneur_keywords = ["创业者", "日本市场", "效率", "性能", "准确性", "用户体验", "收入", "成本"]
        description_lower = description.lower()
        
        has_entrepreneur_value = any(keyword in description_lower for keyword in entrepreneur_keywords)
        if not has_entrepreneur_value:
            issues.append(ReviewIssue(
                issue_id=f"business_{len(issues)}",
                description="计划未明确体现对创业者的商业价值",
                severity=ReviewSeverity.WARNING,
                category="business_value",
                suggestion="明确说明计划如何为创业者创造价值",
                model_source="business_model"
            ))
        
        # 检查预期收益
        if not expected_benefits:
            issues.append(ReviewIssue(
                issue_id=f"business_{len(issues)}",
                description="未提供预期商业收益",
                severity=ReviewSeverity.ERROR,
                category="business_value",
                suggestion="提供具体的预期商业收益",
                model_source="business_model"
            ))
        else:
            # 检查收益是否具体
            specific_benefits = 0
            for benefit in expected_benefits:
                if any(word in benefit for word in ["%", "提高", "降低", "减少", "增加", "节省", "提升"]):
                    specific_benefits += 1
            
            if specific_benefits < len(expected_benefits) * 0.5:
                issues.append(ReviewIssue(
                    issue_id=f"business_{len(issues)}",
                    description="预期收益不够具体",
                    severity=ReviewSeverity.WARNING,
                    category="measurement",
                    suggestion="使用具体数字或百分比描述收益",
                    model_source="business_model"
                ))
        
        # 检查风险评估
        if not risks:
            issues.append(ReviewIssue(
                issue_id=f"business_{len(issues)}",
                description="未提供风险评估",
                severity=ReviewSeverity.WARNING,
                category="risk_management",
                suggestion="提供详细的风险评估",
                model_source="business_model"
            ))
        
        # 商业价值评分
        business_value_score = self._calculate_business_value_score(issues, expected_benefits)
        approved = business_value_score > 0.3 and has_entrepreneur_value
        
        return {
            "status": ReviewStatus.APPROVED if approved else ReviewStatus.NEEDS_MODIFICATION,
            "confidence": business_value_score,
            "issues": issues,
            "summary": f"商业价值审查完成，发现{len(issues)}个问题。商业价值评分: {business_value_score:.2f}"
        }
    
    async def _technical_model_review(
        self,
        plan_id: str,
        description: str,
        target_files: List[str],
        expected_benefits: List[str]
    ) -> Dict[str, Any]:
        """技术可行性模型"""
        issues = []
        
        # 检查技术可行性
        technical_terms = ["实现", "开发", "编码", "重构", "优化", "修复", "集成"]
        description_lower = description.lower()
        
        has_technical_content = any(term in description_lower for term in technical_terms)
        if not has_technical_content and target_files:
            issues.append(ReviewIssue(
                issue_id=f"technical_{len(issues)}",
                description="计划描述缺少技术细节",
                severity=ReviewSeverity.WARNING,
                category="technical_detail",
                suggestion="提供更多技术实现细节",
                model_source="technical_model"
            ))
        
        # 检查文件类型一致性
        if target_files:
            file_extensions = set()
            for file_path in target_files:
                if '.' in file_path:
                    ext = file_path.split('.')[-1]
                    file_extensions.add(ext)
            
            if len(file_extensions) > 3:
                issues.append(ReviewIssue(
                    issue_id=f"technical_{len(issues)}",
                    description="修改的文件类型过多，可能过于复杂",
                    severity=ReviewSeverity.WARNING,
                    category="complexity",
                    suggestion="考虑分阶段修改，减少每次修改的文件类型",
                    model_source="technical_model"
                ))
        
        # 检查技术债务
        tech_debt_keywords = ["技术债务", "重构", "清理", "优化", "改进"]
        addresses_tech_debt = any(keyword in description_lower for keyword in tech_debt_keywords)
        
        if addresses_tech_debt:
            # 技术债务修复是积极的
            pass
        else:
            # 检查是否可能增加技术债务
            risky_keywords = ["快速修复", "临时方案", "绕过", "hack"]
            may_increase_debt = any(keyword in description_lower for keyword in risky_keywords)
            
            if may_increase_debt:
                issues.append(ReviewIssue(
                    issue_id=f"technical_{len(issues)}",
                    description="可能增加技术债务",
                    severity=ReviewSeverity.WARNING,
                    category="technical_debt",
                    suggestion="考虑更可持续的解决方案",
                    model_source="technical_model"
                ))
        
        # 技术可行性评分
        feasibility_score = self._calculate_feasibility_score(issues, target_files, has_technical_content)
        approved = feasibility_score > 0.4
        
        return {
            "status": ReviewStatus.APPROVED if approved else ReviewStatus.NEEDS_MODIFICATION,
            "confidence": feasibility_score,
            "issues": issues,
            "summary": f"技术可行性审查完成，发现{len(issues)}个问题。可行性评分: {feasibility_score:.2f}"
        }
    
    async def _generic_model_review(
        self,
        plan_id: str,
        description: str,
        focus_areas: List[str]
    ) -> Dict[str, Any]:
        """通用模型审查"""
        # 这是一个简单的通用审查实现
        issues = []
        
        # 基本检查
        if not description or len(description.strip()) < 10:
            issues.append(ReviewIssue(
                issue_id="generic_001",
                description="计划描述太短或为空",
                severity=ReviewSeverity.WARNING,
                category="completeness",
                suggestion="提供更详细的计划描述",
                model_source="generic_model"
            ))
        
        # 检查是否涉及焦点领域
        description_lower = description.lower()
        has_focus_content = any(focus.lower() in description_lower for focus in focus_areas)
        
        if not has_focus_content:
            issues.append(ReviewIssue(
                issue_id="generic_002",
                description=f"计划未涉及模型关注的领域: {', '.join(focus_areas)}",
                severity=ReviewSeverity.INFO,
                category="relevance",
                suggestion=f"考虑计划与{', '.join(focus_areas)}的相关性",
                model_source="generic_model"
            ))
        
        approved = len(issues) == 0 or all(i.severity == ReviewSeverity.INFO for i in issues)
        
        return {
            "status": ReviewStatus.APPROVED if approved else ReviewStatus.NEEDS_MODIFICATION,
            "confidence": 0.7 if approved else 0.3,
            "issues": issues,
            "summary": f"通用审查完成，发现{len(issues)}个问题"
        }
    
    def _calculate_risk_score(self, issues: List[ReviewIssue], impact_level: Any) -> float:
        """计算风险评分"""
        if not issues:
            return 0.0
        
        severity_weights = {
            ReviewSeverity.INFO: 0.1,
            ReviewSeverity.WARNING: 0.3,
            ReviewSeverity.ERROR: 0.6,
            ReviewSeverity.CRITICAL: 1.0
        }
        
        # 基础风险评分
        base_score = sum(severity_weights.get(issue.severity, 0.0) for issue in issues) / len(issues)
        
        # 根据影响级别调整
        impact_multiplier = {
            "minor": 0.5,
            "moderate": 1.0,
            "major": 1.5,
            "architectural": 2.0
        }
        
        impact_key = getattr(impact_level, 'value', 'moderate')
        multiplier = impact_multiplier.get(impact_key, 1.0)
        
        return min(1.0, base_score * multiplier)
    
    def _calculate_quality_score(self, issues: List[ReviewIssue], code_files: List[str], expected_benefits: List[str]) -> float:
        """计算质量评分"""
        # 基础分
        score = 0.5
        
        # 问题扣分
        severity_penalties = {
            ReviewSeverity.INFO: -0.05,
            ReviewSeverity.WARNING: -0.1,
            ReviewSeverity.ERROR: -0.2,
            ReviewSeverity.CRITICAL: -0.4
        }
        
        for issue in issues:
            score += severity_penalties.get(issue.severity, 0.0)
        
        # 代码文件加分
        if code_files:
            score += 0.1
        
        # 预期收益加分
        if expected_benefits:
            score += 0.1
            # 具体收益额外加分
            specific_count = sum(1 for b in expected_benefits if any(kw in b for kw in ["%", "提高", "降低", "减少", "增加"]))
            if specific_count > 0:
                score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_business_value_score(self, issues: List[ReviewIssue], expected_benefits: List[str]) -> float:
        """计算商业价值评分"""
        # 基础分
        score = 0.3
        
        # 问题扣分
        for issue in issues:
            if issue.severity == ReviewSeverity.ERROR:
                score -= 0.2
            elif issue.severity == ReviewSeverity.WARNING:
                score -= 0.1
            elif issue.severity == ReviewSeverity.INFO:
                score -= 0.05
        
        # 预期收益加分
        if expected_benefits:
            score += 0.2
            # 具体收益额外加分
            specific_count = sum(1 for b in expected_benefits if any(kw in b for kw in ["%", "万元", "用户", "收入", "成本"]))
            if specific_count > 0:
                score += 0.1 * min(3, specific_count)  # 最多加0.3分
        
        return max(0.0, min(1.0, score))
    
    def _calculate_feasibility_score(self, issues: List[ReviewIssue], target_files: List[str], has_technical_content: bool) -> float:
        """计算可行性评分"""
        # 基础分
        score = 0.4
        
        # 问题扣分
        for issue in issues:
            if issue.severity == ReviewSeverity.ERROR:
                score -= 0.2
            elif issue.severity == ReviewSeverity.WARNING:
                score -= 0.1
            elif issue.severity == ReviewSeverity.INFO:
                score -= 0.05
        
        # 技术内容加分
        if has_technical_content:
            score += 0.1
        
        # 目标文件合理加分
        if target_files and len(target_files) <= 10:  # 不超过10个文件
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    async def _analyze_review_results(self, results: List[ModelReviewResult]) -> Dict[str, Any]:
        """分析审查结果"""
        if not results:
            return {
                "approval_rate": 0.0,
                "consensus_level": 0.0,
                "critical_issues_total": 0,
                "average_confidence": 0.0,
                "model_results": []
            }
        
        # 统计批准情况
        approved_count = sum(1 for r in results if r.status == ReviewStatus.APPROVED)
        approval_rate = approved_count / len(results)
        
        # 计算共识水平（基于置信度加权）
        total_confidence = sum(r.confidence for r in results)
        average_confidence = total_confidence / len(results) if results else 0.0
        
        # 统计关键问题
        all_issues = []
        for result in results:
            all_issues.extend(result.issues)
        
        critical_issues = len([i for i in all_issues if i.severity in [ReviewSeverity.ERROR, ReviewSeverity.CRITICAL]])
        
        # 计算共识水平
        consensus_level = approval_rate * average_confidence
        
        return {
            "approval_rate": approval_rate,
            "consensus_level": consensus_level,
            "critical_issues_total": critical_issues,
            "average_confidence": average_confidence,
            "model_results": [
                {
                    "model_name": r.model_name,
                    "status": r.status.value,
                    "confidence": r.confidence,
                    "issues_count": len(r.issues),
                    "critical_issues_count": len([i for i in r.issues if i.severity in [ReviewSeverity.ERROR, ReviewSeverity.CRITICAL]])
                }
                for r in results
            ]
        }
    
    async def _apply_safety_guardrails(self, analysis: Dict[str, Any], plan: Any) -> Dict[str, Any]:
        """应用安全护栏"""
        approval_rate = analysis["approval_rate"]
        consensus_level = analysis["consensus_level"]
        critical_issues = analysis["critical_issues_total"]
        
        # 检查安全护栏
        passes_guardrails = (
            approval_rate >= self.safety_guardrails["consensus_threshold"] and
            critical_issues <= self.safety_guardrails["critical_issue_threshold"] and
            consensus_level >= 0.5
        )
        
        # 计算风险评分
        risk_score = min(1.0, critical_issues * 0.2 + (1.0 - approval_rate) * 0.5)
        
        # 获取影响级别
        impact_level = getattr(plan, 'impact_level', None)
        impact_key = getattr(impact_level, 'value', 'moderate') if impact_level else 'moderate'
        
        # 根据影响级别调整决策
        impact_strictness = {
            "minor": 0.6,
            "moderate": 0.7,
            "major": 0.8,
            "architectural": 0.9
        }
        
        required_approval = impact_strictness.get(impact_key, 0.7)
        actually_approved = approval_rate >= required_approval and passes_guardrails
        
        return {
            "decision": "approved" if actually_approved else "rejected",
            "approved": actually_approved,
            "confidence": consensus_level,
            "risk_score": risk_score,
            "guardrail_check": {
                "approval_rate": approval_rate,
                "required_approval": required_approval,
                "critical_issues": critical_issues,
                "max_critical_issues": self.safety_guardrails["critical_issue_threshold"],
                "consensus_level": consensus_level,
                "min_consensus": 0.5,
                "passes_all": passes_guardrails
            }
        }
    
    async def _generate_comprehensive_report(
        self, 
        results: List[ModelReviewResult], 
        analysis: Dict[str, Any],
        final_decision: Dict[str, Any]
    ) -> str:
        """生成综合报告"""
        report_parts = [
            "📊 多模型审查综合报告",
            "=" * 60,
            f"审查时间: {datetime.now().isoformat()}",
            f"参与模型数: {len(results)}",
            ""
        ]
        
        # 总体统计
        report_parts.append("📈 总体统计:")
        report_parts.append(f"  批准率: {analysis['approval_rate']*100:.1f}%")
        report_parts.append(f"  共识水平: {analysis['consensus_level']*100:.1f}%")
        report_parts.append(f"  关键问题数: {analysis['critical_issues_total']}")
        report_parts.append(f"  平均置信度: {analysis['average_confidence']*100:.1f}%")
        report_parts.append("")
        
        # 各模型结果
        report_parts.append("🤖 各模型审查结果:")
        for model_result in analysis["model_results"]:
            status_emoji = "✅" if model_result["status"] == "approved" else "⚠️" if model_result["status"] == "needs_modification" else "❌"
            report_parts.append(
                f"  {status_emoji} {model_result['model_name']}: "
                f"{model_result['status']} (置信度: {model_result['confidence']*100:.0f}%, "
                f"问题数: {model_result['issues_count']}, "
                f"关键问题: {model_result['critical_issues_count']})"
            )
        report_parts.append("")
        
        # 安全护栏检查
        guardrail = final_decision["guardrail_check"]
        report_parts.append("🛡️ 安全护栏检查:")
        report_parts.append(f"  批准率检查: {guardrail['approval_rate']*100:.1f}% >= {guardrail['required_approval']*100:.0f}%: {'✅' if guardrail['approval_rate'] >= guardrail['required_approval'] else '❌'}")
        report_parts.append(f"  关键问题检查: {guardrail['critical_issues']} <= {guardrail['max_critical_issues']}: {'✅' if guardrail['critical_issues'] <= guardrail['max_critical_issues'] else '❌'}")
        report_parts.append(f"  共识水平检查: {guardrail['consensus_level']*100:.1f}% >= {guardrail['min_consensus']*100:.0f}%: {'✅' if guardrail['consensus_level'] >= guardrail['min_consensus'] else '❌'}")
        report_parts.append(f"  所有护栏通过: {'✅' if guardrail['passes_all'] else '❌'}")
        report_parts.append("")
        
        # 最终决定
        decision_emoji = "✅" if final_decision["approved"] else "❌"
        report_parts.append(f"{decision_emoji} 最终决定: {final_decision['decision'].upper()}")
        report_parts.append(f"  风险评分: {final_decision['risk_score']*100:.1f}%")
        report_parts.append(f"  置信度: {final_decision['confidence']*100:.1f}%")
        
        # 关键问题汇总（如果有）
        all_issues = []
        for result in results:
            all_issues.extend(result.issues)
        
        critical_issues = [i for i in all_issues if i.severity in [ReviewSeverity.ERROR, ReviewSeverity.CRITICAL]]
        if critical_issues:
            report_parts.append("")
            report_parts.append("🚨 关键问题汇总:")
            for i, issue in enumerate(critical_issues[:5], 1):  # 只显示前5个
                severity_emoji = "🔴" if issue.severity == ReviewSeverity.CRITICAL else "🟠"
                report_parts.append(f"  {severity_emoji} {i}. [{issue.model_source}] {issue.description}")
                if issue.suggestion:
                    report_parts.append(f"      💡 建议: {issue.suggestion}")
        
        return "\n".join(report_parts)
    
    def _record_review(self, review_result: Dict[str, Any], review_type: str, plan: Any):
        """记录审查历史"""
        record = {
            "review_type": review_type,
            "plan_id": getattr(plan, 'plan_id', 'unknown'),
            "timestamp": datetime.now().isoformat(),
            "result": review_result
        }
        
        self.review_history.append(record)
        if len(self.review_history) > self.max_history:
            self.review_history.pop(0)
        
        # 保存到文件
        review_log_path = Path(__file__).parent.parent.parent / "evolution_logs" / "model_reviews.json"
        review_log_path.parent.mkdir(exist_ok=True)
        
        try:
            existing_data = []
            if review_log_path.exists():
                with open(review_log_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            existing_data.append(record)
            
            with open(review_log_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"审查记录已保存到: {review_log_path}")
        except Exception as e:
            self.logger.error(f"保存审查记录失败: {e}")
    
    async def get_review_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取审查历史"""
        return self.review_history[-limit:] if self.review_history else []
    
    async def get_safety_status(self) -> Dict[str, Any]:
        """获取安全状态"""
        return {
            "guardrails": self.safety_guardrails,
            "available_models": len(self.available_models),
            "review_history_count": len(self.review_history),
            "recent_reviews": self.review_history[-5:] if self.review_history else []
        }


# 便捷函数
async def review_evolution_plan(plan: Any, review_type: str = "single") -> Dict[str, Any]:
    """审查进化计划（便捷函数）"""
    reviewer = MultiModelReview()
    
    if review_type == "multi":
        return await reviewer.multi_model_review(plan)
    else:
        return await reviewer.single_model_review(plan)


if __name__ == "__main__":
    # 测试多模型审查器
    import asyncio
    logging.basicConfig(level=logging.INFO)
    
    # 模拟进化计划
    @dataclass
    class TestPlan:
        plan_id: str
        description: str
        impact_level: Any
        target_files: List[str]
        expected_benefits: List[str]
        risks: List[str]
    
    async def test():
        print("🧪 测试多模型审查器")
        print("=" * 60)
        
        reviewer = MultiModelReview()
        
        # 测试1: 正常的进化计划
        good_plan = TestPlan(
            plan_id="test_good_001",
            description="优化日本市场分析模块，提高响应速度和准确性",
            impact_level=type('obj', (object,), {'value': 'minor'})(),
            target_files=["src/agents/japan_market/market_researcher.py", "tests/test_market_researcher.py"],
            expected_benefits=["提高市场分析准确性20%", "减少响应时间30%", "改善用户体验"],
            risks=["低风险，主要是代码优化", "需要更新测试用例"]
        )
        
        print("测试单模型审查...")
        single_result = await reviewer.single_model_review(good_plan)
        print(f"单模型审查结果: 批准={single_result['approved']}")
        print(f"置信度: {single_result['confidence']*100:.1f}%")
        print(f"问题数: {single_result['issues_count']}")
        
        print("\n测试多模型审查...")
        multi_result = await reviewer.multi_model_review(good_plan)
        print(f"多模型审查结果: 批准={multi_result['final_approved']}")
        print(f"批准率: {multi_result['approval_rate']*100:.1f}%")
        print(f"风险评分: {multi_result['risk_score']*100:.1f}%")
        
        # 测试2: 危险的进化计划
        bad_plan = TestPlan(
            plan_id="test_bad_001",
            description="删除系统配置文件以节省空间，并执行支付操作",
            impact_level=type('obj', (object,), {'value': 'major'})(),
            target_files=["/etc/config.json", "constitution/identity.md"],
            expected_benefits=["节省磁盘空间"],
            risks=["系统可能无法启动", "数据丢失"]
        )
        
        print("\n测试危险计划的审查...")
        bad_result = await reviewer.multi_model_review(bad_plan)
        print(f"危险计划审查结果: 批准={bad_result['final_approved']}")
        print(f"批准率: {bad_result['approval_rate']*100:.1f}%")
        print(f"关键问题数: {bad_result['critical_issues_total']}")
        
        # 获取安全状态
        safety_status = await reviewer.get_safety_status()
        print(f"\n安全状态: {safety_status['available_models']}个可用模型")
        print(f"审查历史记录数: {safety_status['review_history_count']}")
    
    asyncio.run(test())