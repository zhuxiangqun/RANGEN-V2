#!/usr/bin/env python3
"""
日本市场Agent基类
为进入日本市场提供专业Agent角色基础
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
class JapanAgentConfig:
    """日本市场Agent配置"""
    agent_id: str
    role_name: str  # 角色名称（日语）
    role_name_en: str  # 角色名称（英语）
    domain_expertise: str  # 专业领域
    expertise_jp: str  # 日语专业描述
    capabilities: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    language: str = "ja-JP"
    cultural_awareness: bool = True  # 文化意识


# 日本市场Agent基类
class JapanMarketAgent(ExpertAgent):
    """日本市场专业Agent基类"""
    
    def __init__(
        self,
        agent_id: str,
        role_name: str,
        role_name_en: str,
        domain_expertise: str,
        expertise_jp: str,
        config: Optional[JapanAgentConfig] = None
    ):
        super().__init__(
            agent_id=agent_id,
            domain_expertise=domain_expertise,
            capability_level=0.9,
            collaboration_style="collaborator"
        )
        
        self.role_name = role_name
        self.role_name_en = role_name_en
        self.expertise_jp = expertise_jp
        self.language = "ja-JP"
        
        # 初始化能力组件
        self.memory = get_agent_memory_system()
        self.reasoning = get_structured_reasoning_engine()
        
        # 工作成果
        self.deliverables: Dict[str, Any] = {}
        
        # 设置系统提示
        self._setup_system_prompt()
    
    def _setup_system_prompt(self):
        """设置日语系统提示"""
        base_prompt = f"""
{self.role_name}（{self.role_name_en}）として動作してください。

【役割】
{self.expertise_jp}

【必須遵守事項】
1. 全ての出力は日本語で行ってください
2. 日本のビジネス文化に合わせてください（敬語を使用）
3. 曖昧さを避け、具体的な数値やデータを含めてください
4. 段階的に思考し、論理的に説明してください

【出力形式】
- 見出しを付けて構造化してください
- 必要に応じて表やリストを使用してください
- 出典や参照先があれば明記してください
"""
    
    def _get_service(self):
        """日本市场Agent不直接使用Service，此方法仅为满足抽象基类要求。"""
        return None

    
    def store_deliverable(self, key: str, content: Any):
        """存储工作成果"""
        self.deliverables[key] = {
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "agent": self.agent_id
        }
        # 同时存入共享记忆
        self.memory.add_working(f"{self.agent_id}_{key}", content)
    
    def get_deliverable(self, key: str) -> Optional[Any]:
        """获取工作成果"""
        return self.deliverables.get(key, {}).get("content")
    
    def get_all_deliverables(self) -> Dict[str, Any]:
        """获取所有工作成果"""
        return self.deliverables
    
    def create_report(self, title: str, sections: Dict[str, str]) -> str:
        """创建标准格式报告"""
        report = f"""
{'='*60}
{title}
{'='*60}
作成者: {self.role_name}
作成日: {datetime.now().strftime('%Y年%m月%d日')}

"""
        for section_title, content in sections.items():
            report += f"""
{'-'*40}
{section_title}
{'-'*40}
{content}

"""
        return report


# 角色工厂
class JapanAgentFactory:
    """日本市场Agent工厂"""
    
    @staticmethod
    def create_researcher() -> 'JapanMarketResearcher':
        from .market_researcher import JapanMarketResearcher
        return JapanMarketResearcher()
    
    @staticmethod
    def create_planner() -> 'JapanSolutionPlanner':
        from .solution_planner import JapanSolutionPlanner
        return JapanSolutionPlanner()
    
    @staticmethod
    def create_rnd_manager() -> 'JapanRNDManager':
        from .rnd_manager import JapanRNDManager
        return JapanRNDManager()
    
    @staticmethod
    def create_customer_manager() -> 'JapanCustomerManager':
        from .customer_manager import JapanCustomerManager
        return JapanCustomerManager()
    
    @staticmethod
    def create_team() -> Dict[str, JapanMarketAgent]:
        """创建完整团队"""
        return {
            "researcher": JapanAgentFactory.create_researcher(),
            "planner": JapanAgentFactory.create_planner(),
            "rnd_manager": JapanAgentFactory.create_rnd_manager(),
            "customer_manager": JapanAgentFactory.create_customer_manager()
        }
