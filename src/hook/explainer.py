#!/usr/bin/env python3
"""
Hook解释器模块
为系统事件提供人类可读的解释和洞察
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

from .hook_types import HookEvent, HookEventType


class ExplanationType(Enum):
    """解释类型"""
    AGENT_DECISION = "agent_decision"  # 智能体决策解释
    EVOLUTION_PLAN = "evolution_plan"  # 进化计划解释
    HAND_EXECUTION = "hand_execution"  # Hand执行解释
    ERROR_ANALYSIS = "error_analysis"  # 错误分析
    SYSTEM_STATE = "system_state"  # 系统状态解释
    CONSTITUTION_CHECK = "constitution_check"  # 宪法检查解释
    MODEL_REVIEW = "model_review"  # 模型审查解释


class HookExplainer:
    """Hook解释器"""
    
    def __init__(self, system_name: str = "rangen_system"):
        self.logger = logging.getLogger(__name__)
        self.system_name = system_name
        
        # 解释模板
        self.templates = self._load_templates()
        
        # 知识库（可扩展）
        self.knowledge_base = self._initialize_knowledge_base()
        
        self.logger.info(f"Hook解释器初始化: {system_name}")
    
    def _load_templates(self) -> Dict[ExplanationType, Dict[str, str]]:
        """加载解释模板"""
        return {
            ExplanationType.AGENT_DECISION: {
                "template": """智能体 {agent} 做出了决策:
• **决策类型**: {decision_type}
• **目标**: {goal}
• **考虑因素**: {considerations}
• **最终选择**: {choice}
• **预期影响**: {expected_impact}""",
                "simple": "智能体 {agent} 选择了 {choice} 以实现 {goal}"
            },
            ExplanationType.EVOLUTION_PLAN: {
                "template": """系统提出了进化计划:
• **计划ID**: {plan_id}
• **目标**: {goal}
• **变更类型**: {change_type}
• **影响范围**: {impact_scope}
• **风险评估**: {risk_assessment}
• **预计完成时间**: {estimated_time}
• **成功指标**: {success_metrics}""",
                "simple": "进化计划 {plan_id}: {goal} ({change_type})"
            },
            ExplanationType.HAND_EXECUTION: {
                "template": """执行了Hand能力:
• **Hand名称**: {hand_name}
• **执行结果**: {result}
• **用时**: {execution_time}
• **消耗资源**: {resource_usage}
• **产出**: {output}
• **状态**: {status}""",
                "simple": "执行 {hand_name}: {result} ({status})"
            },
            ExplanationType.ERROR_ANALYSIS: {
                "template": """系统发生错误:
• **错误类型**: {error_type}
• **错误信息**: {error_message}
• **发生位置**: {location}
• **可能原因**: {possible_causes}
• **影响范围**: {impact_scope}
• **解决方案**: {solutions}
• **预防措施**: {prevention_measures}""",
                "simple": "错误: {error_type} - {error_message}"
            },
            ExplanationType.CONSTITUTION_CHECK: {
                "template": """宪法检查结果:
• **检查对象**: {target}
• **检查标准**: {criteria}
• **合规性**: {compliance} ({score}/10)
• **关键问题**: {key_issues}
• **建议**: {recommendations}
• **最终决定**: {decision}""",
                "simple": "宪法检查: {compliance} ({score}/10) - {decision}"
            },
            ExplanationType.MODEL_REVIEW: {
                "template": """模型审查结果:
• **审查模型**: {model_name}
• **审查维度**: {dimensions}
• **总体评分**: {overall_score}/10
• **优势**: {strengths}
• **风险**: {risks}
• **使用建议**: {usage_recommendations}""",
                "simple": "模型审查: {model_name} ({overall_score}/10)"
            },
            ExplanationType.SYSTEM_STATE: {
                "template": """系统状态变化:
• **变化类型**: {change_type}
• **触发因素**: {trigger}
• **当前状态**: {current_state}
• **之前状态**: {previous_state}
• **影响组件**: {affected_components}
• **恢复时间**: {recovery_time}""",
                "simple": "系统状态: {current_state} (由 {trigger} 触发)"
            }
        }
    
    def _initialize_knowledge_base(self) -> Dict[str, Any]:
        """初始化知识库"""
        return {
            "agent_decisions": {
                "planning": "智能体正在制定计划或策略",
                "execution": "智能体正在执行任务",
                "evaluation": "智能体正在评估结果",
                "adaptation": "智能体正在适应变化",
                "learning": "智能体正在学习新知识"
            },
            "error_categories": {
                "network": "网络连接问题，可能由于API服务不可用或网络延迟导致",
                "permission": "权限问题，需要检查访问权限或认证信息",
                "validation": "数据验证失败，输入数据不符合预期格式或约束",
                "execution": "执行错误，代码逻辑问题或运行时异常",
                "resource": "资源限制，如内存不足或磁盘空间不足",
                "integration": "集成问题，组件间通信或数据格式不匹配"
            },
            "hand_capabilities": {
                "file": "文件操作能力，包括读取、写入、移动、删除文件",
                "code": "代码操作能力，包括分析、修改、生成代码",
                "api": "API调用能力，包括发送请求、处理响应",
                "research": "研究能力，包括搜索、分析、总结信息",
                "planning": "规划能力，包括制定策略、分解任务",
                "communication": "沟通能力，包括生成报告、发送消息"
            },
            "system_states": {
                "healthy": "系统运行正常，所有组件状态良好",
                "degraded": "系统性能下降，部分功能受影响",
                "critical": "系统关键功能故障，需要立即关注",
                "evolving": "系统正在自我进化，某些功能可能暂时不可用",
                "learning": "系统正在学习新知识，处理能力可能受限",
                "maintenance": "系统处于维护模式，仅限基本操作"
            }
        }
    
    async def explain_event(self, event: HookEvent) -> Optional[Dict[str, Any]]:
        """解释事件"""
        try:
            # 根据事件类型选择解释器
            explanation_type = self._map_event_type_to_explanation(event.event_type)
            if not explanation_type:
                return None
            
            # 生成解释
            explanation_data = await self._generate_explanation(explanation_type, event)
            if not explanation_data:
                return None
            
            # 格式化解释
            formatted_explanation = self._format_explanation(explanation_type, explanation_data)
            
            result = {
                "explanation_type": explanation_type.value,
                "explanation": formatted_explanation,
                "simple_explanation": explanation_data.get("simple", ""),
                "insights": explanation_data.get("insights", []),
                "recommendations": explanation_data.get("recommendations", []),
                "confidence": explanation_data.get("confidence", 0.8),
                "generated_at": datetime.now().isoformat(),
                "event_id": event.event_id
            }
            
            self.logger.info(f"生成事件解释: {event.event_id} ({explanation_type.value})")
            return result
            
        except Exception as e:
            self.logger.error(f"解释事件失败: {e}")
            return None
    
    def _map_event_type_to_explanation(self, event_type: HookEventType) -> Optional[ExplanationType]:
        """映射事件类型到解释类型"""
        mapping = {
            HookEventType.AGENT_DECISION: ExplanationType.AGENT_DECISION,
            HookEventType.EVOLUTION_PLAN: ExplanationType.EVOLUTION_PLAN,
            HookEventType.HAND_EXECUTION: ExplanationType.HAND_EXECUTION,
            HookEventType.ERROR_OCCURRED: ExplanationType.ERROR_ANALYSIS,
            HookEventType.CONSTITUTION_CHECK: ExplanationType.CONSTITUTION_CHECK,
            HookEventType.MODEL_REVIEW: ExplanationType.MODEL_REVIEW,
            HookEventType.SYSTEM_STATE_CHANGE: ExplanationType.SYSTEM_STATE,
            HookEventType.WORKFLOW_STEP: ExplanationType.AGENT_DECISION,  # 工作流步骤类似智能体决策
            HookEventType.BACKGROUND_THINKING: ExplanationType.AGENT_DECISION,
            HookEventType.GIT_OPERATION: ExplanationType.HAND_EXECUTION
        }
        
        return mapping.get(event_type)
    
    async def _generate_explanation(self, explanation_type: ExplanationType, event: HookEvent) -> Dict[str, Any]:
        """生成解释数据"""
        if explanation_type == ExplanationType.AGENT_DECISION:
            return await self._explain_agent_decision(event)
        elif explanation_type == ExplanationType.EVOLUTION_PLAN:
            return await self._explain_evolution_plan(event)
        elif explanation_type == ExplanationType.HAND_EXECUTION:
            return await self._explain_hand_execution(event)
        elif explanation_type == ExplanationType.ERROR_ANALYSIS:
            return await self._explain_error(event)
        elif explanation_type == ExplanationType.CONSTITUTION_CHECK:
            return await self._explain_constitution_check(event)
        elif explanation_type == ExplanationType.MODEL_REVIEW:
            return await self._explain_model_review(event)
        elif explanation_type == ExplanationType.SYSTEM_STATE:
            return await self._explain_system_state(event)
        else:
            return {}
    
    async def _explain_agent_decision(self, event: HookEvent) -> Dict[str, Any]:
        """解释智能体决策"""
        data = event.data
        
        agent = data.get("agent", "unknown")
        decision = data.get("decision", {})
        context = data.get("context", {})
        
        # 提取决策信息
        decision_type = decision.get("type", "unknown")
        goal = decision.get("goal", "未指定目标")
        choice = decision.get("choice", "未指定选择")
        reasoning = decision.get("reasoning", "未提供推理过程")
        
        # 分析考虑因素
        considerations = self._extract_considerations(decision, context)
        
        # 预期影响分析
        expected_impact = self._assess_decision_impact(decision, context)
        
        # 生成洞察
        insights = self._generate_insights_for_decision(decision, context)
        
        # 建议
        recommendations = self._generate_recommendations_for_decision(decision, context)
        
        explanation_data = {
            "agent": agent,
            "decision_type": decision_type,
            "goal": goal,
            "considerations": ", ".join(considerations) if considerations else "未指定",
            "choice": str(choice),
            "reasoning": reasoning,
            "expected_impact": expected_impact,
            "insights": insights,
            "recommendations": recommendations,
            "confidence": 0.85
        }
        
        # 简单解释
        explanation_data["simple"] = f"智能体 {agent} 选择了 {choice} 以实现 {goal}"
        
        return explanation_data
    
    async def _explain_evolution_plan(self, event: HookEvent) -> Dict[str, Any]:
        """解释进化计划"""
        data = event.data
        plan = data.get("plan", {})
        
        plan_id = plan.get("id", "unknown")
        goal = plan.get("goal", "未指定目标")
        changes = plan.get("changes", [])
        status = data.get("status", "proposed")
        
        # 分析变更类型
        change_types = self._analyze_change_types(changes)
        change_type = ", ".join(change_types) if change_types else "未知"
        
        # 影响范围
        impact_scope = self._assess_impact_scope(changes)
        
        # 风险评估
        risk_assessment = self._assess_plan_risk(changes)
        
        # 预计完成时间
        estimated_time = plan.get("estimated_duration", "未知")
        
        # 成功指标
        success_metrics = plan.get("success_metrics", ["完成变更"])
        
        explanation_data = {
            "plan_id": plan_id,
            "goal": goal,
            "change_type": change_type,
            "impact_scope": impact_scope,
            "risk_assessment": risk_assessment,
            "estimated_time": estimated_time,
            "success_metrics": ", ".join(success_metrics),
            "change_count": len(changes),
            "status": status,
            "confidence": 0.8
        }
        
        # 简单解释
        explanation_data["simple"] = f"进化计划 {plan_id}: {goal} ({change_type})"
        
        return explanation_data
    
    async def _explain_hand_execution(self, event: HookEvent) -> Dict[str, Any]:
        """解释Hand执行"""
        data = event.data
        
        hand_name = data.get("hand", "unknown")
        result = data.get("result", {})
        parameters = data.get("parameters", {})
        
        # 分析执行结果
        success = result.get("success", False)
        output = result.get("output", "无输出")
        error = result.get("error")
        execution_time = result.get("execution_time", "未知")
        
        # 资源使用
        resource_usage = result.get("resource_usage", {})
        
        # 状态
        status = "成功" if success else "失败"
        
        # 执行分析
        analysis = self._analyze_hand_execution(hand_name, result, parameters)
        
        explanation_data = {
            "hand_name": hand_name,
            "result": "成功" if success else f"失败: {error}" if error else "失败",
            "execution_time": execution_time,
            "resource_usage": str(resource_usage) if resource_usage else "未记录",
            "output": str(output)[:100] + "..." if len(str(output)) > 100 else str(output),
            "status": status,
            "analysis": analysis,
            "confidence": 0.9 if success else 0.6
        }
        
        # 简单解释
        explanation_data["simple"] = f"执行 {hand_name}: {status}"
        
        return explanation_data
    
    async def _explain_error(self, event: HookEvent) -> Dict[str, Any]:
        """解释错误"""
        data = event.data
        
        error_type = data.get("error_type", "unknown")
        error_message = data.get("error_message", "未指定错误信息")
        context = data.get("context", {})
        
        # 分析错误位置
        location = context.get("location", "未知位置")
        
        # 可能原因
        possible_causes = self._analyze_error_causes(error_type, error_message, context)
        
        # 影响范围
        impact_scope = self._assess_error_impact(error_type, context)
        
        # 解决方案
        solutions = self._suggest_error_solutions(error_type, error_message)
        
        # 预防措施
        prevention_measures = self._suggest_prevention_measures(error_type, context)
        
        # 错误分类
        error_category = self._categorize_error(error_type)
        
        explanation_data = {
            "error_type": error_type,
            "error_message": error_message,
            "location": location,
            "possible_causes": ", ".join(possible_causes) if possible_causes else "未知",
            "impact_scope": impact_scope,
            "solutions": ", ".join(solutions) if solutions else "需要人工检查",
            "prevention_measures": ", ".join(prevention_measures) if prevention_measures else "未指定",
            "error_category": error_category,
            "confidence": 0.75
        }
        
        # 简单解释
        explanation_data["simple"] = f"错误: {error_type} - {error_message[:50]}..."
        
        return explanation_data
    
    async def _explain_constitution_check(self, event: HookEvent) -> Dict[str, Any]:
        """解释宪法检查"""
        data = event.data
        
        plan_id = data.get("plan_id", "unknown")
        check_result = data.get("check_result", {})
        
        # 提取检查结果
        compliance = check_result.get("compliance", False)
        score = check_result.get("score", 0)
        issues = check_result.get("issues", [])
        recommendations = check_result.get("recommendations", [])
        decision = "通过" if compliance else "拒绝"
        
        # 关键问题
        key_issues = issues[:3] if issues else ["无问题"]
        
        explanation_data = {
            "target": plan_id,
            "criteria": "系统宪法规范",
            "compliance": "符合" if compliance else "不符合",
            "score": score,
            "key_issues": ", ".join(key_issues),
            "recommendations": ", ".join(recommendations) if recommendations else "无建议",
            "decision": decision,
            "issue_count": len(issues),
            "confidence": 0.9
        }
        
        # 简单解释
        explanation_data["simple"] = f"宪法检查: {'通过' if compliance else '拒绝'} ({score}/10)"
        
        return explanation_data
    
    async def _explain_model_review(self, event: HookEvent) -> Dict[str, Any]:
        """解释模型审查"""
        data = event.data
        
        # 假设数据格式
        model_name = data.get("model", "unknown")
        review_result = data.get("result", {})
        
        # 提取审查结果
        overall_score = review_result.get("overall_score", 0)
        dimensions = review_result.get("dimensions", {})
        strengths = review_result.get("strengths", [])
        risks = review_result.get("risks", [])
        recommendations = review_result.get("recommendations", [])
        
        # 分析维度
        dimension_list = list(dimensions.keys())
        
        explanation_data = {
            "model_name": model_name,
            "dimensions": ", ".join(dimension_list) if dimension_list else "未指定",
            "overall_score": overall_score,
            "strengths": ", ".join(strengths[:3]) if strengths else "未指定",
            "risks": ", ".join(risks[:3]) if risks else "未发现风险",
            "usage_recommendations": ", ".join(recommendations[:3]) if recommendations else "无建议",
            "dimension_count": len(dimension_list),
            "confidence": 0.85
        }
        
        # 简单解释
        explanation_data["simple"] = f"模型审查: {model_name} ({overall_score}/10)"
        
        return explanation_data
    
    async def _explain_system_state(self, event: HookEvent) -> Dict[str, Any]:
        """解释系统状态变化"""
        data = event.data
        
        change_type = data.get("change_type", "unknown")
        previous_state = data.get("previous_state", "unknown")
        current_state = data.get("current_state", "unknown")
        trigger = data.get("trigger", "unknown")
        
        # 分析影响组件
        affected_components = data.get("affected_components", [])
        
        # 估计恢复时间
        recovery_time = self._estimate_recovery_time(change_type, current_state)
        
        # 状态变化影响
        impact = self._assess_state_change_impact(previous_state, current_state)
        
        explanation_data = {
            "change_type": change_type,
            "trigger": trigger,
            "current_state": current_state,
            "previous_state": previous_state,
            "affected_components": ", ".join(affected_components) if affected_components else "全局",
            "recovery_time": recovery_time,
            "impact": impact,
            "confidence": 0.8
        }
        
        # 简单解释
        explanation_data["simple"] = f"系统状态: {current_state} (由 {trigger} 触发)"
        
        return explanation_data
    
    def _format_explanation(self, explanation_type: ExplanationType, data: Dict[str, Any]) -> str:
        """格式化解释"""
        template_info = self.templates.get(explanation_type)
        if not template_info:
            return f"无法生成解释: {explanation_type.value}"
        
        template = template_info.get("template", "")
        
        try:
            # 替换模板中的占位符
            formatted = template.format(**data)
            return formatted
        except KeyError as e:
            self.logger.warning(f"模板格式化缺少参数: {e}")
            # 使用简单模板
            simple_template = template_info.get("simple", "解释生成失败")
            try:
                return simple_template.format(**data)
            except KeyError:
                return f"事件解释: {explanation_type.value}"
    
    def _extract_considerations(self, decision: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """提取考虑因素"""
        considerations = []
        
        # 从决策中提取
        if "considerations" in decision:
            if isinstance(decision["considerations"], list):
                considerations.extend(decision["considerations"])
            else:
                considerations.append(str(decision["considerations"]))
        
        # 从上下文中推断
        if "constraints" in context:
            considerations.append(f"约束: {context['constraints']}")
        
        if "resources" in context:
            considerations.append(f"资源: {context['resources']}")
        
        if "timeline" in context:
            considerations.append(f"时间线: {context['timeline']}")
        
        return considerations
    
    def _assess_decision_impact(self, decision: Dict[str, Any], context: Dict[str, Any]) -> str:
        """评估决策影响"""
        # 简单实现：根据决策类型评估
        decision_type = decision.get("type", "")
        
        impact_map = {
            "strategic": "高影响 - 战略层面",
            "tactical": "中影响 - 战术层面",
            "operational": "低影响 - 操作层面",
            "emergency": "紧急影响 - 需要立即处理"
        }
        
        return impact_map.get(decision_type, "未知影响")
    
    def _generate_insights_for_decision(self, decision: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """为决策生成洞察"""
        insights = []
        
        # 简单实现：基于决策特征生成洞察
        if "risk_level" in decision:
            risk_level = decision["risk_level"]
            if risk_level == "high":
                insights.append("这是一个高风险决策，需要谨慎评估")
            elif risk_level == "low":
                insights.append("这是一个低风险决策，可以快速执行")
        
        if "novelty" in decision and decision["novelty"]:
            insights.append("这是一个创新性决策，可能带来新机会")
        
        if "alignment" in context:
            insights.append(f"决策与目标对齐度: {context['alignment']}")
        
        return insights
    
    def _generate_recommendations_for_decision(self, decision: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """为决策生成建议"""
        recommendations = []
        
        # 简单实现
        decision_type = decision.get("type", "")
        
        if decision_type == "strategic":
            recommendations.append("建议进行小规模试点验证")
            recommendations.append("建议制定应对计划以降低风险")
        
        if "uncertainty" in context and context["uncertainty"] > 0.5:
            recommendations.append("建议收集更多信息以减少不确定性")
        
        return recommendations
    
    def _analyze_change_types(self, changes: List[Dict[str, Any]]) -> List[str]:
        """分析变更类型"""
        change_types = []
        
        for change in changes:
            change_type = change.get("type", "unknown")
            if change_type not in change_types:
                change_types.append(change_type)
        
        return change_types
    
    def _assess_impact_scope(self, changes: List[Dict[str, Any]]) -> str:
        """评估影响范围"""
        if not changes:
            return "无影响"
        
        # 简单评估
        component_count = len(set(change.get("component", "unknown") for change in changes))
        
        if component_count == 1:
            return "局部影响"
        elif component_count <= 3:
            return "中等影响"
        else:
            return "广泛影响"
    
    def _assess_plan_risk(self, changes: List[Dict[str, Any]]) -> str:
        """评估计划风险"""
        if not changes:
            return "无风险"
        
        # 简单风险评估
        risk_levels = []
        for change in changes:
            risk = change.get("risk", "low")
            risk_levels.append(risk)
        
        if "high" in risk_levels:
            return "高风险 - 包含高风险变更"
        elif "medium" in risk_levels:
            return "中等风险 - 需要谨慎执行"
        else:
            return "低风险 - 可以安全执行"
    
    def _analyze_hand_execution(self, hand_name: str, result: Dict[str, Any], parameters: Dict[str, Any]) -> str:
        """分析Hand执行"""
        success = result.get("success", False)
        
        if success:
            # 成功执行分析
            execution_time = result.get("execution_time", 0)
            
            if execution_time < 1:
                efficiency = "极高效率"
            elif execution_time < 5:
                efficiency = "高效率"
            elif execution_time < 30:
                efficiency = "正常效率"
            else:
                efficiency = "低效率"
            
            return f"执行成功，{efficiency}"
        else:
            # 失败分析
            error = result.get("error", "未知错误")
            
            # 错误分类
            if "permission" in error.lower():
                return "执行失败：权限问题"
            elif "timeout" in error.lower():
                return "执行失败：超时问题"
            elif "validation" in error.lower():
                return "执行失败：数据验证失败"
            elif "network" in error.lower():
                return "执行失败：网络问题"
            else:
                return f"执行失败：{error[:50]}..."
    
    def _analyze_error_causes(self, error_type: str, error_message: str, context: Dict[str, Any]) -> List[str]:
        """分析错误原因"""
        causes = []
        
        # 基于错误类型
        if "network" in error_type.lower() or "connection" in error_type.lower():
            causes.append("网络连接不稳定")
            causes.append("目标服务不可用")
            causes.append("防火墙或代理限制")
        
        elif "permission" in error_type.lower() or "access" in error_type.lower():
            causes.append("权限配置错误")
            causes.append("认证信息过期")
            causes.append("访问控制限制")
        
        elif "validation" in error_type.lower():
            causes.append("输入数据格式错误")
            causes.append("缺少必需字段")
            causes.append("数据约束不满足")
        
        elif "timeout" in error_type.lower():
            causes.append("响应时间过长")
            causes.append("资源不足")
            causes.append("处理任务过于复杂")
        
        # 基于错误信息
        if "memory" in error_message.lower():
            causes.append("内存不足")
        
        if "disk" in error_message.lower() or "space" in error_message.lower():
            causes.append("磁盘空间不足")
        
        if "import" in error_message.lower() or "module" in error_message.lower():
            causes.append("依赖包缺失或版本不兼容")
        
        # 基于上下文
        if "retry_count" in context and context["retry_count"] > 3:
            causes.append("多次重试失败，可能为持续性问题")
        
        return causes
    
    def _assess_error_impact(self, error_type: str, context: Dict[str, Any]) -> str:
        """评估错误影响"""
        # 简单实现
        if "critical" in error_type.lower():
            return "关键影响 - 系统核心功能不可用"
        elif "major" in error_type.lower():
            return "重大影响 - 主要功能受限"
        elif "minor" in error_type.lower():
            return "次要影响 - 边缘功能受影响"
        else:
            return "未知影响 - 需要进一步分析"
    
    def _suggest_error_solutions(self, error_type: str, error_message: str) -> List[str]:
        """建议错误解决方案"""
        solutions = []
        
        # 基于错误类型
        if "network" in error_type.lower():
            solutions.append("检查网络连接")
            solutions.append("验证目标服务状态")
            solutions.append("调整超时设置")
        
        elif "permission" in error_type.lower():
            solutions.append("检查权限配置")
            solutions.append("更新认证信息")
            solutions.append("联系管理员调整访问控制")
        
        elif "validation" in error_type.lower():
            solutions.append("验证输入数据格式")
            solutions.append("检查必需字段")
            solutions.append("调整数据约束")
        
        elif "timeout" in error_type.lower():
            solutions.append("增加超时时间")
            solutions.append("优化处理逻辑")
            solutions.append("减少任务复杂度")
        
        # 通用解决方案
        solutions.append("查看详细日志获取更多信息")
        solutions.append("尝试重启相关服务")
        solutions.append("回滚到之前稳定版本")
        
        return solutions
    
    def _suggest_prevention_measures(self, error_type: str, context: Dict[str, Any]) -> List[str]:
        """建议预防措施"""
        measures = []
        
        if "network" in error_type.lower():
            measures.append("实现网络连接健康检查")
            measures.append("添加自动重试机制")
            measures.append("配置备用服务节点")
        
        elif "permission" in error_type.lower():
            measures.append("定期检查权限配置")
            measures.append("实现权限变更审计")
            measures.append("添加权限验证测试")
        
        elif "validation" in error_type.lower():
            measures.append("加强输入数据验证")
            measures.append("添加数据完整性检查")
            measures.append("实现数据格式标准化")
        
        return measures
    
    def _categorize_error(self, error_type: str) -> str:
        """分类错误"""
        categories = self.knowledge_base.get("error_categories", {})
        
        for category, description in categories.items():
            if category in error_type.lower():
                return category
        
        return "unknown"
    
    def _estimate_recovery_time(self, change_type: str, current_state: str) -> str:
        """估计恢复时间"""
        if current_state == "healthy":
            return "已恢复"
        
        # 简单估计
        if "degraded" in current_state:
            return "5-15分钟"
        elif "critical" in current_state:
            return "15-60分钟"
        elif "evolving" in current_state or "learning" in current_state:
            return "30-120分钟"
        else:
            return "未知"
    
    def _assess_state_change_impact(self, previous_state: str, current_state: str) -> str:
        """评估状态变化影响"""
        # 简单实现
        if previous_state == "healthy" and current_state != "healthy":
            return "服务降级"
        elif previous_state != "healthy" and current_state == "healthy":
            return "服务恢复"
        elif "critical" in current_state:
            return "服务中断"
        else:
            return "状态波动"
    
    def add_knowledge(self, category: str, key: str, value: Any):
        """添加知识"""
        if category not in self.knowledge_base:
            self.knowledge_base[category] = {}
        
        self.knowledge_base[category][key] = value
        self.logger.info(f"添加知识: {category}.{key}")
    
    def add_template(self, explanation_type: ExplanationType, template: str, simple_template: str):
        """添加模板"""
        self.templates[explanation_type] = {
            "template": template,
            "simple": simple_template
        }
        self.logger.info(f"添加解释模板: {explanation_type.value}")
    
    def __str__(self):
        return f"HookExplainer({self.system_name})"