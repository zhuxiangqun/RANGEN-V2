#!/usr/bin/env python3
"""
中国市场Agent基类
为进入中国市场提供专业Agent角色基础
"""

import os
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from ..expert_agent import ExpertAgent
from ..capabilities import (
    get_agent_memory_system,
    get_structured_reasoning_engine,
    ReasoningType
)


@dataclass
class ChinaAgentConfig:
    """中国市场Agent配置"""
    agent_id: str
    role_name: str  # 角色名称（中文）
    role_name_en: str  # 角色名称（英语）
    domain_expertise: str  # 专业领域
    expertise_cn: str  # 中文专业描述
    capabilities: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    language: str = "zh-CN"
    cultural_awareness: bool = True  # 文化意识
    understand_regulations: bool = True  # 法规理解


# 中国市场Agent基类
class ChinaMarketAgent(ExpertAgent):
    """中国市场专业Agent基类"""
    
    def __init__(
        self,
        agent_id: str,
        role_name: str,
        role_name_en: str,
        domain_expertise: str,
        expertise_cn: str,
        config: Optional[ChinaAgentConfig] = None
    ):
        super().__init__(
            agent_id=agent_id,
            domain_expertise=domain_expertise,
            capability_level=0.9,
            collaboration_style="collaborator"
        )
        
        self.role_name = role_name
        self.role_name_en = role_name_en
        self.expertise_cn = expertise_cn
        self.language = "zh-CN"
        
        # 初始化能力组件
        self.memory = get_agent_memory_system()
        self.reasoning = get_structured_reasoning_engine()
        
        # 工作成果
        self.deliverables: Dict[str, Any] = {}
        
        # 设置系统提示
        self._setup_system_prompt()
    
    def _setup_system_prompt(self):
        """设置中文系统提示"""
        base_prompt = f"""
{self.role_name}（{self.role_name_en}）作为角色进行工作。

【角色定位】
{self.expertise_cn}

【必须遵守事项】
1. 所有输出使用中文（简体）
2. 符合中国商务文化规范
3. 考虑中国市场的法律法规要求
4. 重视关系建设和长期合作
5. 理解中国消费者的独特需求和行为模式

【专业领域】
• 中国市场进入策略
• 中国消费者行为分析
• 中国商业法律法规
• 中文市场传播策略
• 中国供应链管理
• 本土化产品适配

【沟通风格】
• 专业、务实、高效
• 尊重中国商业礼仪
• 清晰表达，避免歧义
• 考虑文化敏感性

请根据上述要求提供专业、准确、实用的建议。
"""
        self.system_prompt = base_prompt
    
    async def process_task(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """处理任务"""
        context = context or {}
        
        # 记录任务开始
        task_start = datetime.now()
        
        # 使用推理引擎处理任务
        reasoning_result = await self.reasoning.reason_async(
            task=task,
            context=context,
            reasoning_type=ReasoningType.ANALYTICAL,
            domain_knowledge=self.domain_expertise
        )
        
        # 更新记忆
        await self.memory.store_memory(
            agent_id=self.agent_id,
            content=f"处理任务: {task}",
            metadata={
                "task": task,
                "context": context,
                "reasoning_result": reasoning_result,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # 生成交付物
        deliverable_id = f"deliverable_{int(datetime.now().timestamp())}"
        deliverable = {
            "task": task,
            "result": reasoning_result,
            "generated_at": datetime.now().isoformat(),
            "agent_role": self.role_name
        }
        
        self.deliverables[deliverable_id] = deliverable
        
        # 计算执行时间
        execution_time = (datetime.now() - task_start).total_seconds()
        
        return {
            "success": True,
            "result": reasoning_result,
            "deliverable_id": deliverable_id,
            "execution_time": execution_time,
            "agent_role": self.role_name
        }
    
    def get_deliverables(self) -> List[Dict[str, Any]]:
        """获取所有交付物"""
        return list(self.deliverables.values())
    
    def clear_deliverables(self):
        """清空交付物"""
        self.deliverables.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "agent_id": self.agent_id,
            "role_name": self.role_name,
            "role_name_en": self.role_name_en,
            "domain_expertise": self.domain_expertise,
            "language": self.language,
            "deliverables_count": len(self.deliverables)
        }


class ChinaAgentFactory:
    """中国市场Agent工厂"""
    
    @staticmethod
    def create_agent(config: ChinaAgentConfig) -> ChinaMarketAgent:
        """创建Agent"""
        return ChinaMarketAgent(
            agent_id=config.agent_id,
            role_name=config.role_name,
            role_name_en=config.role_name_en,
            domain_expertise=config.domain_expertise,
            expertise_cn=config.expertise_cn,
            config=config
        )
    
    @staticmethod
    def create_market_researcher() -> ChinaMarketAgent:
        """创建市场调研员"""
        config = ChinaAgentConfig(
            agent_id="china_market_researcher_001",
            role_name="中国市场调研专家",
            role_name_en="China Market Researcher",
            domain_expertise="中国市场调研与分析",
            expertise_cn="专注于中国市场趋势分析、消费者行为研究、竞争对手分析，为企业进入中国市场提供数据支持。",
            capabilities=["市场调研", "数据分析", "竞品分析", "消费者洞察"],
            tools=["数据收集工具", "分析框架", "调研问卷"]
        )
        return ChinaAgentFactory.create_agent(config)
    
    @staticmethod
    def create_solution_planner() -> ChinaMarketAgent:
        """创建解决方案规划师"""
        config = ChinaAgentConfig(
            agent_id="china_solution_planner_001",
            role_name="中国解决方案规划师",
            role_name_en="China Solution Planner",
            domain_expertise="中国市场解决方案规划",
            expertise_cn="基于中国市场特点，制定产品本地化策略、定价策略、渠道策略和营销策略。",
            capabilities=["策略规划", "产品本地化", "渠道规划", "营销策略"],
            tools=["策略框架", "本地化工具", "市场分析模型"]
        )
        return ChinaAgentFactory.create_agent(config)
    
    @staticmethod
    def create_regulatory_expert() -> ChinaMarketAgent:
        """创建法规专家"""
        config = ChinaAgentConfig(
            agent_id="china_regulatory_expert_001",
            role_name="中国法规与合规专家",
            role_name_en="China Regulatory Expert",
            domain_expertise="中国商业法规与合规",
            expertise_cn="精通中国商业法律法规、行业监管政策、数据安全法、网络安全法等合规要求。",
            capabilities=["法规解读", "合规评估", "许可证申请", "风险规避"],
            tools=["法律数据库", "合规检查表", "风险评估框架"]
        )
        return ChinaAgentFactory.create_agent(config)