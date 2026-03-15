"""
Capability Checker Service - Check existing capabilities before creating new agents
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from src.services.database import get_database
from src.services.logging_service import get_logger

logger = get_logger(__name__)


@dataclass
class CheckResult:
    """能力检查结果"""
    satisfied: bool
    missing: List[str]
    available: List[str]
    message: str


@dataclass
class Suggestion:
    """能力组合建议"""
    agents: List[Dict[str, Any]]
    skills: List[Dict[str, Any]]
    tools: List[Dict[str, Any]]
    message: str


class CapabilityChecker:
    """能力检查器 - 创建新Agent前检查现有能力"""
    
    def __init__(self):
        self.db = get_database()
    
    def check_tools(self, requirements: List[str]) -> CheckResult:
        """检查现有Tools是否满足需求"""
        all_tools = self.db.get_all_tools(status='active')
        available_tool_ids = {t['id'] for t in all_tools}
        available_names = {t['name'].lower(): t['id'] for t in all_tools}
        
        missing = []
        available = []
        
        for req in requirements:
            req_lower = req.lower()
            # 尝试匹配ID或名称
            if req in available_tool_ids:
                available.append(req)
            elif req_lower in available_names:
                available.append(available_names[req_lower])
            else:
                missing.append(req)
        
        return CheckResult(
            satisfied=len(missing) == 0,
            missing=missing,
            available=available,
            message=f"Tools检查: {len(available)}/{len(requirements)} 可用" if missing else "所有Tool需求已满足"
        )
    
    def check_skills(self, requirements: List[str]) -> CheckResult:
        """检查现有Skills是否满足需求"""
        all_skills = self.db.get_all_skills(status='active')
        available_skill_ids = {s['id'] for s in all_skills}
        available_names = {s['name'].lower(): s['id'] for s in all_skills}
        
        missing = []
        available = []
        
        for req in requirements:
            req_lower = req.lower()
            if req in available_skill_ids:
                available.append(req)
            elif req_lower in available_names:
                available.append(available_names[req_lower])
            else:
                missing.append(req)
        
        return CheckResult(
            satisfied=len(missing) == 0,
            missing=missing,
            available=available,
            message=f"Skills检查: {len(available)}/{len(requirements)} 可用" if missing else "所有Skill需求已满足"
        )
    
    def check_agents(self, requirements: List[str]) -> CheckResult:
        """检查现有Agents是否满足需求"""
        all_agents = self.db.get_all_agents(status='active')
        available_agent_ids = {a['id'] for a in all_agents}
        available_names = {a['name'].lower(): a['id'] for a in all_agents}
        
        missing = []
        available = []
        
        for req in requirements:
            req_lower = req.lower()
            if req in available_agent_ids:
                available.append(req)
            elif req_lower in available_names:
                available.append(available_names[req_lower])
            else:
                missing.append(req)
        
        return CheckResult(
            satisfied=len(missing) == 0,
            missing=missing,
            available=available,
            message=f"Agents检查: {len(available)}/{len(requirements)} 可用" if missing else "所有Agent需求已满足"
        )
    
    def check_all(self, requirements: Dict[str, List[str]]) -> Dict[str, CheckResult]:
        """检查所有类型的能力"""
        results = {}
        
        if 'tools' in requirements:
            results['tools'] = self.check_tools(requirements['tools'])
        
        if 'skills' in requirements:
            results['skills'] = self.check_skills(requirements['skills'])
        
        if 'agents' in requirements:
            results['agents'] = self.check_agents(requirements['agents'])
        
        return results
    
    def suggest_combination(self, requirements: Dict[str, List[str]]) -> Suggestion:
        """建议能力组合方案"""
        suggestions = {
            'agents': [],
            'skills': [],
            'tools': [],
            'message': ''
        }
        
        # 检查现有能力
        all_agents = self.db.get_all_agents(status='active')
        all_skills = self.db.get_all_skills(status='active')
        all_tools = self.db.get_all_tools(status='active')
        
        # 简单匹配逻辑
        if 'tools' in requirements:
            req_tools = set(req.lower() for req in requirements['tools'])
            for tool in all_tools:
                if tool['name'].lower() in req_tools:
                    suggestions['tools'].append(tool)
        
        if 'skills' in requirements:
            req_skills = set(req.lower() for req in requirements['skills'])
            for skill in all_skills:
                if skill['name'].lower() in req_skills:
                    suggestions['skills'].append(skill)
        
        # 生成消息
        total_suggestions = len(suggestions['agents']) + len(suggestions['skills']) + len(suggestions['tools'])
        suggestions['message'] = f"找到 {total_suggestions} 个可用的现有能力"
        
        return Suggestion(**suggestions)
    
    def can_create_agent(self, required_tools: List[str], required_skills: List[str]) -> tuple[bool, str]:
        """判断是否可以创建Agent"""
        tool_check = self.check_tools(required_tools)
        skill_check = self.check_skills(required_skills)
        
        if tool_check.satisfied and skill_check.satisfied:
            return True, "所有能力需求已满足"
        
        issues = []
        if tool_check.missing:
            issues.append(f"缺少Tools: {', '.join(tool_check.missing)}")
        if skill_check.missing:
            issues.append(f"缺少Skills: {', '.join(skill_check.missing)}")
        
        return False, "; ".join(issues)


def get_capability_checker() -> CapabilityChecker:
    """获取能力检查器实例"""
    return CapabilityChecker()
