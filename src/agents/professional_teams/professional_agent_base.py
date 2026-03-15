#!/usr/bin/env python3
"""
专业化Agent基类
为专业化Agent团队提供基础能力
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod

from ..expert_agent import ExpertAgent
from ..capabilities import (
    get_agent_memory_system,
    get_structured_reasoning_engine,
    ReasoningType
)


logger = logging.getLogger(__name__)


@dataclass
class ProfessionalAgentConfig:
    """专业化Agent配置"""
    agent_id: str
    role_name: str                     # 角色名称（中文）
    role_name_en: str                  # 角色名称（英文）
    domain_expertise: str              # 专业领域
    expertise_description: str         # 专业描述
    capabilities: List[str] = field(default_factory=list)  # 核心能力
    tools: List[str] = field(default_factory=list)         # 可用工具
    collaboration_style: str = "collaborator"              # 协作风格
    capability_level: float = 0.9                          # 能力水平 (0-1)
    language: str = "zh-CN"                                # 默认语言


class ProfessionalAgentBase(ExpertAgent):
    """专业化Agent基类"""
    
    def __init__(
        self,
        agent_id: str,
        role_name: str,
        role_name_en: str,
        domain_expertise: str,
        expertise_description: str,
        config: Optional[ProfessionalAgentConfig] = None
    ):
        """初始化专业化Agent
        
        Args:
            agent_id: Agent唯一标识符
            role_name: 角色名称（中文）
            role_name_en: 角色名称（英文）
            domain_expertise: 专业领域
            expertise_description: 专业描述
            config: 配置对象（可选）
        """
        if config is None:
            config = ProfessionalAgentConfig(
                agent_id=agent_id,
                role_name=role_name,
                role_name_en=role_name_en,
                domain_expertise=domain_expertise,
                expertise_description=expertise_description,
                capabilities=[domain_expertise, "collaboration"],
                tools=[],
                collaboration_style="collaborator",
                capability_level=0.9,
                language="zh-CN"
            )
        
        super().__init__(
            agent_id=agent_id,
            domain_expertise=domain_expertise,
            capability_level=config.capability_level,
            collaboration_style=config.collaboration_style
        )
        
        self.role_name = role_name
        self.role_name_en = role_name_en
        self.expertise_description = expertise_description
        self.language = config.language
        
        # 初始化能力组件
        self.memory = get_agent_memory_system()
        self.reasoning = get_structured_reasoning_engine()
        
        # 工作成果存储
        self.deliverables: Dict[str, Any] = {}
        
        # 角色特定配置
        self.capabilities = config.capabilities
        self.tools = config.tools
        
        # 设置系统提示
        self._setup_system_prompt()
        
        logger.info(f"初始化专业化Agent: {role_name} ({role_name_en}), ID: {agent_id}")
    
    def _setup_system_prompt(self):
        """设置系统提示"""
        self.system_prompt = f"""
你是一个专业化的AI Agent，角色是：{self.role_name} ({self.role_name_en})

【角色职责】
{self.expertise_description}

【核心能力】
{chr(10).join(f'- {cap}' for cap in self.capabilities)}

【工作要求】
1. 专注于你的专业领域，提供专业、精准的分析和建议
2. 与团队成员协作时，清晰表达你的专业观点
3. 遵循标准工作流程和交付规范
4. 确保所有输出符合专业标准和质量要求

【输出规范】
- 使用清晰的结构化格式
- 重要数据使用表格或列表展示
- 关键结论和推荐项明确标注
- 提供可执行的建议和实施方案

【协作原则】
- 尊重其他专业角色的意见
- 在跨领域问题上主动寻求协作
- 及时共享工作进展和发现
- 保持专业和建设性的沟通风格
"""
    
    def store_deliverable(self, key: str, content: Any, metadata: Optional[Dict[str, Any]] = None):
        """存储工作成果
        
        Args:
            key: 成果标识符
            content: 成果内容
            metadata: 元数据（可选）
        """
        deliverable = {
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.agent_id,
            "role_name": self.role_name,
            "role_name_en": self.role_name_en,
            "metadata": metadata or {}
        }
        
        self.deliverables[key] = deliverable
        
        # 同时存入共享记忆
        memory_key = f"{self.agent_id}_{key}"
        self.memory.add_working(memory_key, content)
        
        logger.info(f"Agent {self.agent_id} 存储工作成果: {key}")
    
    def get_deliverable(self, key: str) -> Optional[Any]:
        """获取工作成果
        
        Args:
            key: 成果标识符
            
        Returns:
            成果内容，如果不存在则返回None
        """
        deliverable = self.deliverables.get(key)
        return deliverable.get("content") if deliverable else None
    
    def get_all_deliverables(self) -> Dict[str, Any]:
        """获取所有工作成果
        
        Returns:
            所有成果的字典
        """
        return self.deliverables
    
    def create_report(self, title: str, sections: Dict[str, str], summary: Optional[str] = None) -> str:
        """创建标准格式报告
        
        Args:
            title: 报告标题
            sections: 报告章节字典 {章节标题: 内容}
            summary: 执行摘要（可选）
            
        Returns:
            格式化报告字符串
        """
        report = f"""
{'='*60}
{title}
{'='*60}
角色: {self.role_name} ({self.role_name_en})
生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
报告ID: {self.agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}

"""
        if summary:
            report += f"""
【执行摘要】
{summary}

"""
        
        for section_title, content in sections.items():
            report += f"""
{'━'*40}
{section_title}
{'━'*40}
{content}

"""
        
        report += f"""
{'='*60}
报告结束
{'='*60}
"""
        return report
    
    def analyze_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """分析需求（模板方法）
        
        Args:
            requirements: 需求描述
            
        Returns:
            分析结果
        """
        logger.info(f"Agent {self.agent_id} 开始分析需求")
        
        # 使用推理引擎分析需求
        analysis_result = self.reasoning.analyze(
            query=f"分析以下需求，从{self.role_name}的专业角度提供分析：{json.dumps(requirements, ensure_ascii=False)}",
            context=f"角色: {self.role_name}, 专业领域: {self.domain_expertise}",
            reasoning_type=ReasoningType.ANALYTICAL
        )
        
        result = {
            "agent_id": self.agent_id,
            "role_name": self.role_name,
            "analysis": analysis_result,
            "recommendations": [],
            "risks": [],
            "timeline_estimate": None,
            "resource_requirements": []
        }
        
        # 存储分析结果
        self.store_deliverable("requirements_analysis", result)
        
        return result
    
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务（模板方法）
        
        Args:
            task: 任务描述
            
        Returns:
            执行结果
        """
        logger.info(f"Agent {self.agent_id} 开始执行任务: {task.get('task_name', '未命名任务')}")
        
        # 这里应该调用具体的任务执行逻辑
        # 子类需要重写此方法
        
        result = {
            "agent_id": self.agent_id,
            "role_name": self.role_name,
            "task_id": task.get("task_id", "unknown"),
            "task_name": task.get("task_name", "未命名任务"),
            "status": "completed",
            "output": None,
            "metrics": {},
            "completion_time": datetime.now().isoformat()
        }
        
        self.store_deliverable(f"task_result_{task.get('task_id', 'unknown')}", result)
        
        return result
    
    def collaborate_with(self, other_agent_id: str, collaboration_request: Dict[str, Any]) -> Dict[str, Any]:
        """与其他Agent协作
        
        Args:
            other_agent_id: 协作Agent的ID
            collaboration_request: 协作请求
            
        Returns:
            协作响应
        """
        logger.info(f"Agent {self.agent_id} 与Agent {other_agent_id} 开始协作")
        
        # 记录协作请求
        collaboration_record = {
            "request_id": f"collab_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "from_agent": self.agent_id,
            "to_agent": other_agent_id,
            "request": collaboration_request,
            "request_time": datetime.now().isoformat(),
            "response": None,
            "status": "requested"
        }
        
        # 这里应该实现实际的协作逻辑
        # 简化实现：返回确认响应
        
        response = {
            "request_id": collaboration_record["request_id"],
            "from_agent": other_agent_id,
            "to_agent": self.agent_id,
            "response": {
                "acknowledged": True,
                "willing_to_collaborate": True,
                "availability": "immediate",
                "collaboration_plan": {
                    "communication_channel": "shared_memory",
                    "sync_frequency": "as_needed",
                    "decision_making": "consensus"
                }
            },
            "response_time": datetime.now().isoformat()
        }
        
        collaboration_record["response"] = response
        collaboration_record["status"] = "responded"
        
        self.store_deliverable(f"collaboration_{collaboration_record['request_id']}", collaboration_record)
        
        return response
    
    def _get_service(self):
        """获取对应的Service - 专业Agent基类默认实现"""
        # 专业Agent通常不需要特定的Service，返回None
        # 子类可以重写此方法以提供特定的Service
        return None