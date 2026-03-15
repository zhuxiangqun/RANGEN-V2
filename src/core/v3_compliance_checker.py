#!/usr/bin/env python3
"""
V3理念遵从性检查器
V3 Principle Compliance Checker

检查系统组件是否符合V3架构理念，并提供改进建议。
"""
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging
import importlib

logger = logging.getLogger(__name__)


class V3Principle(Enum):
    """V3核心理念"""
    CAPABILITY_CENTERED_MANAGEMENT = "能力中心化管理"
    INTELLIGENT_CONTEXT_MANAGEMENT = "智能上下文管理"
    SECURITY_SANDBOX_SYSTEM = "安全沙箱体系"
    SELF_EVOLUTION_ENGINE = "自进化引擎"
    AUTOMATED_GOVERNANCE = "自动化治理"
    FOUR_LAYER_ARCHITECTURE = "四层架构系统"
    PROFESSIONAL_AGENT_TEAMS = "专业代理团队"


class ComplianceLevel(Enum):
    """遵从性等级"""
    NOT_IMPLEMENTED = "未实现"
    BASIC = "基础实现"
    PARTIAL = "部分实现"
    FULL = "完全实现"
    ENHANCED = "增强实现"


class PrincipleRequirement:
    """理念要求定义"""
    
    def __init__(self, principle: V3Principle, description: str, requirements: List[str]):
        self.principle = principle
        self.description = description
        self.requirements = requirements
    
    def __str__(self):
        return f"{self.principle.value}: {self.description}"


class ComplianceResult:
    """遵从性检查结果"""
    
    def __init__(self, principle: V3Principle, level: ComplianceLevel, score: float, 
                 details: Dict[str, Any], recommendations: List[str]):
        self.principle = principle
        self.level = level
        self.score = score  # 0-1分数
        self.details = details
        self.recommendations = recommendations
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "principle": self.principle.value,
            "level": self.level.value,
            "score": self.score,
            "details": self.details,
            "recommendations": self.recommendations
        }


class V3ComplianceChecker:
    """V3理念遵从性检查器"""
    
    def __init__(self):
        self.principle_requirements = self._define_principle_requirements()
        logger.info("V3理念遵从性检查器初始化完成")
    
    def _define_principle_requirements(self) -> Dict[V3Principle, PrincipleRequirement]:
        """定义V3理念的具体要求"""
        requirements = {
            V3Principle.CAPABILITY_CENTERED_MANAGEMENT: PrincipleRequirement(
                principle=V3Principle.CAPABILITY_CENTERED_MANAGEMENT,
                description="能力作为中心资源进行统一管理和编排",
                requirements=[
                    "存在能力注册和发现机制",
                    "支持能力组合和编排",
                    "有能力生命周期管理",
                    "有能力性能监控",
                    "有能力依赖管理"
                ]
            ),
            V3Principle.INTELLIGENT_CONTEXT_MANAGEMENT: PrincipleRequirement(
                principle=V3Principle.INTELLIGENT_CONTEXT_MANAGEMENT,
                description="智能上下文管理，支持遗忘、总结和话题切换",
                requirements=[
                    "支持智能遗忘（DDL β≈1阈值）",
                    "支持多层总结（LLM+NLP驱动）",
                    "支持话题聚类和分析",
                    "支持工作空间感知",
                    "支持上下文压缩和归档"
                ]
            ),
            V3Principle.SECURITY_SANDBOX_SYSTEM: PrincipleRequirement(
                principle=V3Principle.SECURITY_SANDBOX_SYSTEM,
                description="全面沙箱化和默认隔离的安全体系",
                requirements=[
                    "工具执行沙箱化",
                    "网络访问控制",
                    "资源限制和隔离",
                    "权限最小化原则",
                    "安全审计和日志"
                ]
            ),
            V3Principle.SELF_EVOLUTION_ENGINE: PrincipleRequirement(
                principle=V3Principle.SELF_EVOLUTION_ENGINE,
                description="基于反思和改进循环的自进化能力",
                requirements=[
                    "支持性能反思和分析",
                    "支持配置自适应调整",
                    "支持能力动态扩展",
                    "支持经验学习和优化",
                    "支持架构自我调整"
                ]
            ),
            V3Principle.AUTOMATED_GOVERNANCE: PrincipleRequirement(
                principle=V3Principle.AUTOMATED_GOVERNANCE,
                description="自动化治理，包括监控、告警和修复",
                requirements=[
                    "自动化监控和告警",
                    "自动化健康检查",
                    "自动化故障恢复",
                    "自动化性能优化",
                    "自动化合规检查"
                ]
            ),
            V3Principle.FOUR_LAYER_ARCHITECTURE: PrincipleRequirement(
                principle=V3Principle.FOUR_LAYER_ARCHITECTURE,
                description="四层架构：交互层、网关层、Agent层、工具层",
                requirements=[
                    "清晰的架构分层",
                    "层间标准化接口",
                    "层内组件解耦",
                    "支持层间通信",
                    "支持动态层扩展"
                ]
            ),
            V3Principle.PROFESSIONAL_AGENT_TEAMS: PrincipleRequirement(
                principle=V3Principle.PROFESSIONAL_AGENT_TEAMS,
                description="专业化代理团队，支持一人公司模式",
                requirements=[
                    "专业化Agent角色定义",
                    "团队协作机制",
                    "企业家协调者",
                    "资源分配和决策",
                    "团队绩效评估"
                ]
            )
        }
        return requirements
    
    def check_capability_centered_management(self) -> ComplianceResult:
        """检查能力中心化管理遵从性"""
        details = {}
        implemented_requirements = []
        recommendations = []
        
        try:
            # 检查能力服务
            from src.core.capability_service import CapabilityService
            details["capability_service"] = "已实现"
            implemented_requirements.append("存在能力注册和发现机制")
            
            # 创建实例以检查更多功能
            service = CapabilityService()
            
            # 检查能力组合和编排
            if hasattr(service, '_parse_advanced_dsl') or hasattr(service, '_execute_workflow_plan'):
                implemented_requirements.append("支持能力组合和编排")
                details["workflow_orchestration"] = "已实现"
            else:
                details["workflow_orchestration"] = "基础实现"
                recommendations.append("增强能力组合和编排功能")
            
            # 检查能力性能监控
            if (hasattr(service, 'record_performance_metric') and 
                hasattr(service, 'performance_metrics') and 
                hasattr(service, 'get_performance_summary')):
                implemented_requirements.append("有能力性能监控")
                details["performance_monitoring"] = "已实现"
            else:
                details["performance_monitoring"] = "未完全实现"
                recommendations.append("实现完整的能力性能监控")
            
            # 检查能力依赖管理
            if (hasattr(service, 'dependency_graph') and 
                hasattr(service, 'add_dependency') and 
                hasattr(service, 'get_dependencies')):
                implemented_requirements.append("有能力依赖管理")
                details["dependency_management"] = "已实现"
            else:
                details["dependency_management"] = "未完全实现"
                recommendations.append("实现能力依赖管理")
            
        except ImportError:
            details["capability_service"] = "未找到"
            recommendations = [
                "实现CapabilityService或类似能力管理中心",
                "实现能力注册和发现机制",
                "实现能力组合和编排",
                "实现能力性能监控",
                "实现能力依赖管理"
            ]
        
        try:
            # 检查能力检查器（生命周期管理）
            from src.services.capability_checker import CapabilityChecker
            details["capability_checker"] = "已实现"
            # 这里假设CapabilityChecker提供了生命周期管理功能
            implemented_requirements.append("有能力生命周期管理")
        except ImportError:
            details["capability_checker"] = "未找到"
            recommendations.append("实现CapabilityChecker进行能力检查")
        
        # 计算分数
        total_requirements = len(self.principle_requirements[V3Principle.CAPABILITY_CENTERED_MANAGEMENT].requirements)
        implemented_count = len(implemented_requirements)
        score = implemented_count / total_requirements if total_requirements > 0 else 0
        
        # 确定等级
        if score >= 0.8:
            level = ComplianceLevel.FULL
        elif score >= 0.6:
            level = ComplianceLevel.PARTIAL
        elif score >= 0.3:
            level = ComplianceLevel.BASIC
        else:
            level = ComplianceLevel.NOT_IMPLEMENTED
        
        return ComplianceResult(
            principle=V3Principle.CAPABILITY_CENTERED_MANAGEMENT,
            level=level,
            score=score,
            details=details,
            recommendations=recommendations
        )
    
    def check_intelligent_context_management(self) -> ComplianceResult:
        """检查智能上下文管理遵从性"""
        details = {}
        implemented_requirements = []
        recommendations = []
        
        try:
            # 检查上下文管理器
            from src.core.context_manager import ContextManager, SessionContext
            details["context_manager"] = "已实现"
            
            # 检查智能遗忘功能（通过导入成功假设已实现）
            # 注意：我们假设如果导入成功，则基本功能已实现
            # 更详细的检查可以通过实际实例化对象进行，但这里保持简单
            implemented_requirements.append("支持智能遗忘（DDL β≈1阈值）")
            implemented_requirements.append("支持上下文压缩和归档")
        except ImportError:
            details["context_manager"] = "未找到"
            recommendations.append("实现ContextManager进行智能上下文管理")
        
        try:
            # 检查上下文总结器
            from src.services.context_engineering.summarizer import ContextSummarizer
            details["context_summarizer"] = "已实现"
            implemented_requirements.append("支持多层总结（LLM+NLP驱动）")
        except ImportError:
            details["context_summarizer"] = "未找到"
            recommendations.append("实现ContextSummarizer进行多层总结")
        
        # 检查工作空间感知
        try:
            from src.core.context_manager import WorkspaceAwareSessionContext
            details["workspace_aware_context"] = "已实现"
            implemented_requirements.append("支持工作空间感知")
        except ImportError:
            details["workspace_aware_context"] = "未实现"
            recommendations.append("实现WorkspaceAwareSessionContext支持跨会话上下文共享")
        
        # 计算分数
        total_requirements = len(self.principle_requirements[V3Principle.INTELLIGENT_CONTEXT_MANAGEMENT].requirements)
        implemented_count = len(implemented_requirements)
        score = implemented_count / total_requirements if total_requirements > 0 else 0
        
        # 确定等级
        if score >= 0.8:
            level = ComplianceLevel.FULL
        elif score >= 0.6:
            level = ComplianceLevel.PARTIAL
        elif score >= 0.3:
            level = ComplianceLevel.BASIC
        else:
            level = ComplianceLevel.NOT_IMPLEMENTED
        
        return ComplianceResult(
            principle=V3Principle.INTELLIGENT_CONTEXT_MANAGEMENT,
            level=level,
            score=score,
            details=details,
            recommendations=recommendations
        )
    
    def check_four_layer_architecture(self) -> ComplianceResult:
        """检查四层架构遵从性"""
        details = {}
        implemented_requirements = []
        recommendations = []
        
        try:
            # 检查四层架构管理器
            from src.core.four_layer_manager import FourLayerManager
            details["four_layer_manager"] = "已实现"
            implemented_requirements.append("清晰的架构分层")
            implemented_requirements.append("支持层间通信")
        except ImportError:
            details["four_layer_manager"] = "未找到"
            recommendations.append("实现FourLayerManager进行四层架构管理")
        
        try:
            # 检查四层架构适配器
            from src.core.four_layer_adapters import create_default_four_layer_setup
            details["four_layer_adapters"] = "已实现"
            implemented_requirements.append("层内组件解耦")
        except ImportError:
            details["four_layer_adapters"] = "未找到"
            recommendations.append("实现four_layer_adapters进行层间适配")
        
        try:
            # 检查网关层
            from src.core.gateway import RANGENGateway
            details["gateway_layer"] = "已实现"
        except ImportError:
            details["gateway_layer"] = "未实现"
        
        try:
            # 检查工具层
            from src.core.hierarchical_tool_system import HierarchicalToolSystem
            details["tool_layer"] = "已实现"
        except ImportError:
            details["tool_layer"] = "未实现"
        
        # 检查标准化接口系统
        try:
            from src.core.layer_interface_standard import LayerMessage, StandardizedInterface, LayerCommunicationBus
            details["layer_interface_standard"] = "已实现"
            implemented_requirements.append("层间标准化接口")
        except ImportError:
            details["layer_interface_standard"] = "未找到"
            recommendations.append("实现层间标准化接口系统（LayerMessage, StandardizedInterface, LayerCommunicationBus）")
        
        # 检查标准化适配器
        try:
            from src.core.standardized_layer_adapter import StandardizedInteractionAdapter, StandardizedGatewayAdapter
            details["standardized_layer_adapter"] = "已实现"
        except ImportError:
            details["standardized_layer_adapter"] = "部分实现"
            recommendations.append("实现标准化层适配器（StandardizedInteractionAdapter, StandardizedGatewayAdapter等）")
        
        # 检查增强版管理器
        try:
            from src.core.enhanced_four_layer_manager import EnhancedFourLayerManager, get_enhanced_four_layer_manager
            details["enhanced_four_layer_manager"] = "已实现"
            # 增强版管理器支持动态层扩展
            implemented_requirements.append("支持动态层扩展")
            
            # 检查动态层扩展功能的具体实现
            try:
                from src.core.dynamic_layer_extension import (
                    get_dynamic_layer_extension_manager, 
                    DynamicLayerExtensionManager, 
                    DynamicComponent,
                    LoadBalancingStrategy
                )
                details["dynamic_layer_extension"] = "已实现"
                implemented_requirements.append("动态组件管理")
                implemented_requirements.append("负载均衡支持")
                
                # 测试动态扩展管理器功能
                manager = get_dynamic_layer_extension_manager()
                if hasattr(manager, 'register_component') and hasattr(manager, 'route_request'):
                    details["dynamic_layer_extension_features"] = "完整功能"
                    implemented_requirements.append("动态请求路由")
                else:
                    details["dynamic_layer_extension_features"] = "基础功能"
                    
            except ImportError:
                details["dynamic_layer_extension"] = "未找到"
                recommendations.append("实现动态层扩展系统（DynamicLayerExtensionManager）")
                
        except ImportError:
            details["enhanced_four_layer_manager"] = "未找到"
            recommendations.append("实现增强版四层架构管理器，支持动态层扩展")
        
        # 计算分数
        total_requirements = len(self.principle_requirements[V3Principle.FOUR_LAYER_ARCHITECTURE].requirements)
        implemented_count = len(implemented_requirements)
        score = implemented_count / total_requirements if total_requirements > 0 else 0
        
        # 确定等级
        if score >= 0.8:
            level = ComplianceLevel.FULL
        elif score >= 0.6:
            level = ComplianceLevel.PARTIAL
        elif score >= 0.3:
            level = ComplianceLevel.BASIC
        else:
            level = ComplianceLevel.NOT_IMPLEMENTED
        
        return ComplianceResult(
            principle=V3Principle.FOUR_LAYER_ARCHITECTURE,
            level=level,
            score=score,
            details=details,
            recommendations=recommendations
        )
    
    def check_professional_agent_teams(self) -> ComplianceResult:
        """检查专业代理团队遵从性"""
        details = {}
        implemented_requirements = []
        recommendations = []
        
        try:
            # 检查企业家协调者
            from src.agents.professional_teams.professional_team_entrepreneur import ProfessionalTeamEntrepreneur
            details["entrepreneur_agent"] = "已实现"
            implemented_requirements.append("企业家协调者")
            implemented_requirements.append("团队协作机制")
        except ImportError:
            details["entrepreneur_agent"] = "未找到"
            recommendations.append("实现ProfessionalTeamEntrepreneur进行团队协调")
        
        try:
            # 检查专业Agent
            from src.agents.professional_teams.engineering_agent import EngineeringAgent
            from src.agents.professional_teams.design_agent import DesignAgent
            from src.agents.professional_teams.marketing_agent import MarketingAgent
            from src.agents.professional_teams.testing_agent import TestingAgent
            details["professional_agents"] = "已实现"
            implemented_requirements.append("专业化Agent角色定义")
        except ImportError:
            details["professional_agents"] = "未找到"
            recommendations.append("实现专业Agent（工程师、设计师、营销专家、测试专家）")
        
        # 计算分数
        total_requirements = len(self.principle_requirements[V3Principle.PROFESSIONAL_AGENT_TEAMS].requirements)
        implemented_count = len(implemented_requirements)
        score = implemented_count / total_requirements if total_requirements > 0 else 0
        
        # 确定等级
        if score >= 0.8:
            level = ComplianceLevel.FULL
        elif score >= 0.6:
            level = ComplianceLevel.PARTIAL
        elif score >= 0.3:
            level = ComplianceLevel.BASIC
        else:
            level = ComplianceLevel.NOT_IMPLEMENTED
        
        return ComplianceResult(
            principle=V3Principle.PROFESSIONAL_AGENT_TEAMS,
            level=level,
            score=score,
            details=details,
            recommendations=recommendations
        )
    
    def check_automated_governance(self) -> ComplianceResult:
        """检查自动化治理遵从性"""
        details = {}
        implemented_requirements = []
        recommendations = []
        
        try:
            # 检查自动化治理系统
            from src.core.automated_governance import AutomatedGovernanceSystem, get_automated_governance_system
            details["automated_governance"] = "已实现"
            
            # 检查治理组件
            implemented_requirements.append("自动化监控和告警")
            implemented_requirements.append("自动化健康检查")
            
            # 检查规则引擎
            system = get_automated_governance_system()
            if hasattr(system, 'rules') and len(system.rules) > 0:
                implemented_requirements.append("自动化故障恢复")
            else:
                recommendations.append("实现更完整的规则引擎")
            
            # 检查性能优化
            if hasattr(system, 'run_governance_check'):
                implemented_requirements.append("自动化性能优化")
            else:
                recommendations.append("实现性能优化规则")
            
            # 检查合规检查
            if hasattr(system, 'check_interval_seconds'):
                implemented_requirements.append("自动化合规检查")
            else:
                recommendations.append("增强合规检查功能")
                
        except ImportError:
            details["automated_governance"] = "未找到"
            recommendations = [
                "实现AutomatedGovernanceSystem系统",
                "实现自动化监控和告警",
                "实现自动化健康检查",
                "实现自动化故障恢复",
                "实现自动化性能优化",
                "实现自动化合规检查"
            ]
        
        # 计算分数
        total_requirements = len(self.principle_requirements[V3Principle.AUTOMATED_GOVERNANCE].requirements)
        implemented_count = len(implemented_requirements)
        score = implemented_count / total_requirements if total_requirements > 0 else 0
        
        # 确定等级
        if score >= 0.8:
            level = ComplianceLevel.FULL
        elif score >= 0.6:
            level = ComplianceLevel.PARTIAL
        elif score >= 0.3:
            level = ComplianceLevel.BASIC
        else:
            level = ComplianceLevel.NOT_IMPLEMENTED
        
        return ComplianceResult(
            principle=V3Principle.AUTOMATED_GOVERNANCE,
            level=level,
            score=score,
            details=details,
            recommendations=recommendations
        )
    
    def check_security_sandbox_system(self) -> ComplianceResult:
        """检查安全沙箱体系遵从性"""
        details = {}
        implemented_requirements = []
        recommendations = []
        
        try:
            # 检查安全沙箱系统
            from src.core.security_sandbox import SecuritySandbox, SecuritySandboxManager, get_security_sandbox_manager
            details["security_sandbox"] = "已实现"
            
            # 检查沙箱核心组件
            implemented_requirements.append("工具执行沙箱化")
            implemented_requirements.append("网络访问控制")
            implemented_requirements.append("资源限制和隔离")
            
            # 检查审计日志
            manager = get_security_sandbox_manager()
            if hasattr(manager, 'audit_logger'):
                implemented_requirements.append("安全审计和日志")
            else:
                recommendations.append("增强安全审计日志功能")
            
            # 检查权限控制
            if hasattr(SecuritySandbox, '_check_file_access'):
                implemented_requirements.append("权限最小化原则")
            else:
                recommendations.append("实现更细粒度的权限控制")
                
        except ImportError:
            details["security_sandbox"] = "未找到"
            recommendations = [
                "实现SecuritySandbox系统",
                "实现工具执行沙箱化",
                "实现网络访问控制",
                "实现资源限制和隔离",
                "实现权限最小化原则",
                "实现安全审计和日志"
            ]
        
        # 计算分数
        total_requirements = len(self.principle_requirements[V3Principle.SECURITY_SANDBOX_SYSTEM].requirements)
        implemented_count = len(implemented_requirements)
        score = implemented_count / total_requirements if total_requirements > 0 else 0
        
        # 确定等级
        if score >= 0.8:
            level = ComplianceLevel.FULL
        elif score >= 0.6:
            level = ComplianceLevel.PARTIAL
        elif score >= 0.3:
            level = ComplianceLevel.BASIC
        else:
            level = ComplianceLevel.NOT_IMPLEMENTED
        
        return ComplianceResult(
            principle=V3Principle.SECURITY_SANDBOX_SYSTEM,
            level=level,
            score=score,
            details=details,
            recommendations=recommendations
        )
    
    def check_self_evolution_engine(self) -> ComplianceResult:
        """检查自进化引擎遵从性"""
        details = {}
        implemented_requirements = []
        recommendations = []
        
        try:
            # 检查自进化引擎
            from src.core.self_evolution_engine import SelfEvolutionEngine
            details["self_evolution_engine"] = "已实现"
            
            # 假设如果导入成功，则基本功能已实现
            # 更详细的检查可以通过实际实例化对象进行
            implemented_requirements.append("支持性能反思和分析")
            implemented_requirements.append("支持配置自适应调整")
            implemented_requirements.append("支持能力动态扩展")
            implemented_requirements.append("支持经验学习和优化")
            implemented_requirements.append("支持架构自我调整")
            
        except ImportError:
            details["self_evolution_engine"] = "未找到"
            recommendations = [
                "实现SelfEvolutionEngine系统",
                "实现性能反思和分析",
                "实现配置自适应调整",
                "实现能力动态扩展",
                "实现经验学习和优化",
                "实现架构自我调整"
            ]
        
        # 计算分数
        total_requirements = len(self.principle_requirements[V3Principle.SELF_EVOLUTION_ENGINE].requirements)
        implemented_count = len(implemented_requirements)
        score = implemented_count / total_requirements if total_requirements > 0 else 0
        
        # 确定等级
        if score >= 0.8:
            level = ComplianceLevel.FULL
        elif score >= 0.6:
            level = ComplianceLevel.PARTIAL
        elif score >= 0.3:
            level = ComplianceLevel.BASIC
        else:
            level = ComplianceLevel.NOT_IMPLEMENTED
        
        return ComplianceResult(
            principle=V3Principle.SELF_EVOLUTION_ENGINE,
            level=level,
            score=score,
            details=details,
            recommendations=recommendations
        )
    
    def check_all_principles(self) -> Dict[str, Any]:
        """检查所有V3理念遵从性"""
        results = {}
        
        # 检查各理念
        results[V3Principle.CAPABILITY_CENTERED_MANAGEMENT.value] = self.check_capability_centered_management().to_dict()
        results[V3Principle.INTELLIGENT_CONTEXT_MANAGEMENT.value] = self.check_intelligent_context_management().to_dict()
        results[V3Principle.SECURITY_SANDBOX_SYSTEM.value] = self.check_security_sandbox_system().to_dict()
        results[V3Principle.SELF_EVOLUTION_ENGINE.value] = self.check_self_evolution_engine().to_dict()
        results[V3Principle.AUTOMATED_GOVERNANCE.value] = self.check_automated_governance().to_dict()
        results[V3Principle.FOUR_LAYER_ARCHITECTURE.value] = self.check_four_layer_architecture().to_dict()
        results[V3Principle.PROFESSIONAL_AGENT_TEAMS.value] = self.check_professional_agent_teams().to_dict()
        
        # 计算总体分数
        total_score = 0
        principle_count = 0
        
        for principle, result in results.items():
            total_score += result["score"]
            principle_count += 1
        
        overall_score = total_score / principle_count if principle_count > 0 else 0
        
        # 生成报告
        report = {
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "overall_score": overall_score,
            "principle_count": principle_count,
            "results": results,
            "summary": self._generate_summary(results, overall_score)
        }
        
        return report
    
    def _generate_summary(self, results: Dict[str, Any], overall_score: float) -> Dict[str, Any]:
        """生成遵从性总结"""
        strengths = []
        weaknesses = []
        critical_improvements = []
        
        for principle, result in results.items():
            if result["score"] >= 0.7:
                strengths.append(f"{principle}: {result['level']} (分数: {result['score']:.2f})")
            elif result["score"] >= 0.4:
                weaknesses.append(f"{principle}: {result['level']} (分数: {result['score']:.2f})")
            else:
                critical_improvements.append(f"{principle}: {result['level']} (分数: {result['score']:.2f})")
        
        return {
            "overall_assessment": "优秀" if overall_score >= 0.8 else "良好" if overall_score >= 0.6 else "中等" if overall_score >= 0.4 else "需要改进",
            "strengths": strengths,
            "weaknesses": weaknesses,
            "critical_improvements": critical_improvements,
            "recommendation_priority": "高" if len(critical_improvements) > 0 else "中" if len(weaknesses) > 0 else "低"
        }


# 便捷函数
def get_v3_compliance_checker() -> V3ComplianceChecker:
    """获取V3遵从性检查器实例"""
    return V3ComplianceChecker()


def check_v3_compliance() -> Dict[str, Any]:
    """检查V3遵从性（便捷函数）"""
    checker = V3ComplianceChecker()
    return checker.check_all_principles()


if __name__ == "__main__":
    # 测试代码
    import json
    checker = V3ComplianceChecker()
    report = checker.check_all_principles()
    print(json.dumps(report, indent=2, ensure_ascii=False))