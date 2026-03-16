#!/usr/bin/env python3
"""
Agent Role Registry - Builder/Reviewer 角色分类系统

根据文章洞见实现角色分离:
- Builder: 创建、生成、实现 (reasoning, code, designs)
- Reviewer: 验证、检查、核实、控制质量
- Coordinator: 编排、路由、管理其他 Agent

核心原则: 瓶颈从"实现"转向"评审"
"""
from enum import Enum
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from functools import wraps


class AgentRole(Enum):
    """Agent 角色分类"""
    BUILDER = "builder"      # 创建/生成/实现
    REVIEWER = "reviewer"    # 验证/检查/质量控制
    COORDINATOR = "coordinator"  # 编排/协调


@dataclass
class AgentClassification:
    """Agent 角色分类信息"""
    agent_name: str
    role: AgentRole
    description: str
    tags: List[str] = field(default_factory=list)


class AgentRoleRegistry:
    """
    Agent 角色注册中心
    
    提供基于角色的 Agent 查询和管理
    """
    
    _instance: Optional['AgentRoleRegistry'] = None
    _classifications: Dict[str, AgentClassification] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_defaults()
        return cls._instance
    
    def _initialize_defaults(self):
        """初始化默认分类"""
        # === REVIEWER (评审/验证) - 最重要 ===
        self.register("validation_agent", AgentRole.REVIEWER, 
                     "验证声明、检查幻觉、事实核查", ["validation", "fact-check"])
        self.register("quality_controller", AgentRole.REVIEWER,
                     "多维度质量评估、自动化验证、错误检测", ["quality", "evaluation"])
        self.register("citation_agent", AgentRole.REVIEWER,
                     "证据溯源、引用生成、来源核查", ["citation", "evidence"])
        self.register("audit_agent", AgentRole.REVIEWER,
                     "安全审计、合规检查、风险评估", ["audit", "security"])
        
        # === BUILDER (创建/生成) ===
        # Core reasoning agents
        self.register("reasoning_agent", AgentRole.BUILDER,
                     "ReAct 推理循环、复杂问题求解", ["reasoning", "react"])
        self.register("react_agent", AgentRole.BUILDER,
                     "基础 ReAct 模式执行", ["react", "basic"])
        self.register("enhanced_react_agent", AgentRole.BUILDER,
                     "增强版 ReAct，带反思能力", ["react", "enhanced"])
        self.register("level3_agent", AgentRole.BUILDER,
                     "L3 高级认知 Agent", ["reasoning", "advanced"])
        self.register("langgraph_react_agent", AgentRole.BUILDER,
                     "LangGraph ReAct 实现", ["react", "langgraph"])
        self.register("hooked_react_agent", AgentRole.BUILDER,
                     "带 Hook 拦截点的 ReAct", ["react", "hooks"])
        
        # Professional teams - Builder
        self.register("engineering_agent", AgentRole.BUILDER,
                     "技术实现、代码开发、系统架构", ["engineering", "code"])
        self.register("design_agent", AgentRole.BUILDER,
                     "设计实现、UI/UX 原型", ["design", "ui"])
        self.register("marketing_agent", AgentRole.BUILDER,
                     "营销内容生成、市场策略", ["marketing", "content"])
        self.register("testing_agent", AgentRole.BUILDER,
                     "测试用例生成、测试执行", ["testing", "qa"])
        
        # Knowledge agents
        self.register("expert_agent", AgentRole.BUILDER,
                     "专家知识调用、领域知识", ["expert", "knowledge"])
        self.register("rag_agent", AgentRole.BUILDER,
                     "RAG 检索增强生成", ["rag", "retrieval"])
        self.register("retrieval_agent", AgentRole.BUILDER,
                     "知识检索、向量搜索", ["retrieval", "search"])
        
        # Japan market agents - Builder
        self.register("hr_specialist", AgentRole.BUILDER,
                     "人力资源解决方案", ["hr", "japan"])
        self.register("financial_expert", AgentRole.BUILDER,
                     "金融领域咨询", ["finance", "japan"])
        self.register("legal_advisor", AgentRole.BUILDER,
                     "法律咨询", ["legal", "japan"])
        self.register("entrepreneur", AgentRole.BUILDER,
                     "创业指导", ["entrepreneur", "japan"])
        self.register("customer_manager", AgentRole.BUILDER,
                     "客户管理", ["crm", "japan"])
        self.register("rnd_manager", AgentRole.BUILDER,
                     "研发管理", ["rnd", "japan"])
        self.register("solution_planner", AgentRole.BUILDER,
                     "方案规划", ["solution", "planning"])
        self.register("project_coordinator", AgentRole.BUILDER,
                     "项目协调", ["project", "coordination"])
        self.register("market_researcher", AgentRole.BUILDER,
                     "市场研究", ["market", "research"])
        
        # Learning agents - Builder
        self.register("self_learning_agent", AgentRole.BUILDER,
                     "自学习能力、持续优化", ["learning", "self"])
        
        # === COORDINATOR (编排/协调) ===
        self.register("chief_agent", AgentRole.COORDINATOR,
                     "首席 Agent、全局协调", ["chief", "leader"])
        self.register("base_agent", AgentRole.COORDINATOR,
                     "Agent 基类、基础架构", ["base", "foundation"])
        self.register("multi_agent_coordinator", AgentRole.COORDINATOR,
                     "多 Agent 协调、任务分发", ["multi", "coordination"])
    
    def register(self, agent_name: str, role: AgentRole, 
                 description: str, tags: List[str] = None):
        """注册 Agent 角色"""
        classification = AgentClassification(
            agent_name=agent_name,
            role=role,
            description=description,
            tags=tags or []
        )
        self._classifications[agent_name] = classification
    
    def get_role(self, agent_name: str) -> Optional[AgentRole]:
        """获取 Agent 角色"""
        classification = self._classifications.get(agent_name)
        return classification.role if classification else None
    
    def get_classification(self, agent_name: str) -> Optional[AgentClassification]:
        """获取 Agent 完整分类信息"""
        return self._classifications.get(agent_name)
    
    def get_agents_by_role(self, role: AgentRole) -> List[AgentClassification]:
        """获取指定角色的所有 Agent"""
        return [
            c for c in self._classifications.values()
            if c.role == role
        ]
    
    def get_all_classifications(self) -> List[AgentClassification]:
        """获取所有 Agent 分类"""
        return list(self._classifications.values())
    
    def get_builders(self) -> List[AgentClassification]:
        """获取所有 Builder Agent"""
        return self.get_agents_by_role(AgentRole.BUILDER)
    
    def get_reviewers(self) -> List[AgentClassification]:
        """获取所有 Reviewer Agent"""
        return self.get_agents_by_role(AgentRole.REVIEWER)
    
    def get_coordinators(self) -> List[AgentClassification]:
        """获取所有 Coordinator Agent"""
        return self.get_agents_by_role(AgentRole.COORDINATOR)
    
    def is_builder(self, agent_name: str) -> bool:
        """检查是否为 Builder"""
        return self.get_role(agent_name) == AgentRole.BUILDER
    
    def is_reviewer(self, agent_name: str) -> bool:
        """检查是否为 Reviewer"""
        return self.get_role(agent_name) == AgentRole.REVIEWER
    
    def is_coordinator(self, agent_name: str) -> bool:
        """检查是否为 Coordinator"""
        return self.get_role(agent_name) == AgentRole.COORDINATOR
    
    def get_role_summary(self) -> Dict[str, int]:
        """获取角色统计"""
        return {
            "builders": len(self.get_builders()),
            "reviewers": len(self.get_reviewers()),
            "coordinators": len(self.get_coordinators()),
            "total": len(self._classifications)
        }


def get_agent_role_registry() -> AgentRoleRegistry:
    """获取 Agent 角色注册中心单例"""
    return AgentRoleRegistry()


def agent_role(role: AgentRole, description: str = ""):
    """
    装饰器: 标记 Agent 角色
    
    用法:
        @agent_role(AgentRole.REVIEWER, "质量验证")
        class MyAgent:
            ...
    """
    def decorator(cls_or_func: Callable) -> Callable:
        cls_name = cls_or_func.__name__.lower()
        registry = get_agent_role_registry()
        registry.register(cls_name, role, description)
        
        @wraps(cls_or_func)
        def wrapper(*args, **kwargs):
            return cls_or_func(*args, **kwargs)
        
        return wrapper
    return decorator


# === 便捷函数 ===

def is_builder(agent_name: str) -> bool:
    """检查是否为 Builder"""
    return get_agent_role_registry().is_builder(agent_name)

def is_reviewer(agent_name: str) -> bool:
    """检查是否为 Reviewer"""
    return get_agent_role_registry().is_reviewer(agent_name)

def get_role(agent_name: str) -> Optional[AgentRole]:
    """获取 Agent 角色"""
    return get_agent_role_registry().get_role(agent_name)

def get_reviewers() -> List[AgentClassification]:
    """获取所有 Reviewer"""
    return get_agent_role_registry().get_reviewers()

def get_builders() -> List[AgentClassification]:
    """获取所有 Builder"""
    return get_agent_role_registry().get_builders()
