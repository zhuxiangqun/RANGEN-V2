"""
Team 执行引擎

允许用户使用自动创建的 Team 来执行任务
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class TeamExecutionRequest:
    """团队执行请求"""
    team_id: str
    task: str
    context: Dict[str, Any]


@dataclass
class TeamExecutionResult:
    """团队执行结果"""
    success: bool
    team_id: str
    task: str
    result: Any
    steps: List[Dict[str, Any]]
    error: Optional[str] = None


class TeamExecutor:
    """
    Team 执行引擎
    
    负责:
    1. 加载已创建的 Team
    2. 分配任务给 Team 成员
    3. 协调执行
    4. 聚合结果
    """
    
    def __init__(self):
        self.teams_file = self._get_teams_file()
    
    def _get_teams_file(self) -> Path:
        """获取 teams 文件路径"""
        project_root = Path(__file__).parent.parent.parent
        return project_root / 'data' / 'auto_teams.json'
    
    def load_teams(self) -> List[Dict[str, Any]]:
        """加载所有已创建的 Team"""
        if not self.teams_file.exists():
            return []
        
        with open(self.teams_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        """获取指定 Team"""
        teams = self.load_teams()
        for team in teams:
            if team.get('id') == team_id:
                return team
        return None
    
    async def execute(self, request: TeamExecutionRequest) -> TeamExecutionResult:
        """
        执行 Team 任务
        
        流程:
        1. 找到对应的 Team
        2. 加载 Team 成员 (Agents/Skills)
        3. 协调执行
        4. 返回结果
        """
        steps = []
        
        # 1. 加载 Team
        team = self.get_team(request.team_id)
        if not team:
            return TeamExecutionResult(
                success=False,
                team_id=request.team_id,
                task=request.task,
                result=None,
                steps=steps,
                error=f"Team not found: {request.team_id}"
            )
        
        steps.append({
            'step': 'load_team',
            'status': 'completed',
            'detail': f"Loaded team: {team.get('name')}"
        })
        
        # 2. 获取 Team 角色
        roles = team.get('roles', [])
        created_agents = team.get('created_agents', [])
        created_skills = team.get('created_skills', [])
        
        steps.append({
            'step': 'analyze_roles',
            'status': 'completed',
            'detail': f"Roles: {roles}, Agents: {created_agents}, Skills: {created_skills}"
        })
        
        # 3. 执行任务（使用协调机制）
        result = await self._execute_with_team(
            team=team,
            task=request.task,
            context=request.context,
            steps=steps
        )
        
        return result
    
    async def _execute_with_team(
        self,
        team: Dict[str, Any],
        task: str,
        context: Dict[str, Any],
        steps: List[Dict[str, Any]]
    ) -> TeamExecutionResult:
        """使用 Team 执行任务"""
        
        try:
            # 使用 MultiAgentCoordinator 或创建临时协调器
            from src.agents.multi_agent_coordinator import MultiAgentCoordinator
            
            coordinator = MultiAgentCoordinator()
            
            # 构建协作任务
            from src.agents.multi_agent_coordinator import CollaborationTask
            
            collab_task = CollaborationTask(
                task_id=f"team_{team.get('id')}_task",
                description=task,
                complexity="moderate",
                subtasks=[
                    {"id": f"subtask_{i}", "description": role}
                    for i, role in enumerate(team.get('roles', []))
                ]
            )
            
            steps.append({
                'step': 'task_planning',
                'status': 'completed',
                'detail': f"Created {len(collab_task.subtasks)} subtasks"
            })
            
            # 执行协作任务
            result = await coordinator.execute_collaboration(collab_task)
            
            steps.append({
                'step': 'execution',
                'status': 'completed',
                'detail': "Team execution completed"
            })
            
            return TeamExecutionResult(
                success=True,
                team_id=team.get('id'),
                task=task,
                result=result,
                steps=steps
            )
            
        except Exception as e:
            # 如果 MultiAgentCoordinator 不可用，使用简单的执行方式
            return await self._execute_simple(team, task, context, steps)
    
    async def _execute_simple(
        self,
        team: Dict[str, Any],
        task: str,
        context: Dict[str, Any],
        steps: List[Dict[str, Any]]
    ) -> TeamExecutionResult:
        """简单执行方式 - 使用 ExecutionCoordinator"""
        
        from src.core.execution_coordinator import ExecutionCoordinator
        
        coordinator = ExecutionCoordinator()
        
        # 添加 Team 上下文
        enhanced_context = {
            **context,
            'team_name': team.get('name'),
            'team_roles': team.get('roles', []),
            'created_agents': team.get('created_agents', []),
            'created_skills': team.get('created_skills', [])
        }
        
        result = await coordinator.run_task(
            task=task,
            context=enhanced_context
        )
        
        steps.append({
            'step': 'simple_execution',
            'status': 'completed',
            'detail': "Executed with ExecutionCoordinator"
        })
        
        return TeamExecutionResult(
            success=not result.get('error'),
            team_id=team.get('id'),
            task=task,
            result=result.get('final_answer'),
            steps=steps,
            error=result.get('error')
        )
    
    def list_teams(self) -> List[Dict[str, Any]]:
        """列出所有可用的 Team"""
        return self.load_teams()


# 全局实例
_team_executor: Optional[TeamExecutor] = None


def get_team_executor() -> TeamExecutor:
    """获取 Team 执行器实例"""
    global _team_executor
    if _team_executor is None:
        _team_executor = TeamExecutor()
    return _team_executor
