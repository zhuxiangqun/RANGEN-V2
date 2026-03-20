"""
Swarm Mixin - 为 Agent 添加蜂群协调能力

让 Agent 可以:
- 创建和管理团队
- 启动子 Agent
- 发送/接收消息
- 查看看板状态
"""

import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class SwarmCapability:
    """Swarm 能力描述"""
    enabled: bool = False
    current_team: Optional[str] = None
    agent_name: Optional[str] = None


class SwarmMixin:
    """
    Swarm 混入类
    
    使用方式:
        class MyAgent(SwarmMixin, BaseAgent):
            def __init__(self):
                super().__init__()
                self.init_swarm()
    """
    
    SWARM_PATTERNS = {
        "create_team": [
            r"创建团队", r"新建团队", r"建立团队",
            r"create.*team", r"new.*team",
        ],
        "spawn_agent": [
            r"启动.*agent", r"创建.*agent", r"添加.*成员",
            r"spawn.*agent", r"add.*member",
        ],
        "send_message": [
            r"发送消息", r"通知.*", r"告诉.*",
            r"send.*message", r"notify.*",
        ],
        "check_board": [
            r"查看.*状态", r"看板", r"团队状态",
            r"check.*status", r"board", r"team.*status",
        ],
        "create_task": [
            r"创建.*任务", r"添加.*任务",
            r"create.*task", r"add.*task",
        ],
        "complete_task": [
            r"完成.*任务", r"任务完成",
            r"complete.*task", r"task.*done",
        ],
        "launch_template": [
            r"启动.*模板", r"使用.*团队",
            r"launch.*template", r"use.*team",
        ],
    }
    
    def __init__(self):
        self._swarm_capability = SwarmCapability()
        self._swarm_coordinator = None
    
    def init_swarm(
        self,
        agent_name: str = "agent",
        team: Optional[str] = None,
        base_dir: str = ".swarm"
    ):
        """
        初始化 Swarm 能力
        
        Args:
            agent_name: Agent 名称
            team: 所属团队
            base_dir: Swarm 数据目录
        """
        self._swarm_capability.enabled = True
        self._swarm_capability.agent_name = agent_name
        self._swarm_capability.current_team = team
        
        from src.swarm.coordinator import SwarmCoordinator
        self._swarm_coordinator = SwarmCoordinator(base_dir)
    
    def detect_swarm_intent(self, query: str) -> Optional[str]:
        """
        检测 Swarm 相关意图
        
        Returns:
            intent type or None
        """
        query_lower = query.lower()
        
        for intent, patterns in self.SWARM_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return intent
        
        return None
    
    async def execute_swarm_action(
        self,
        intent: str,
        query: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行 Swarm 操作
        
        Args:
            intent: 意图类型
            query: 原始查询
            context: 上下文
            
        Returns:
            执行结果
        """
        if not self._swarm_capability.enabled:
            return {
                "success": False,
                "response": "Swarm 功能未启用"
            }
        
        coord = self._swarm_coordinator
        
        if intent == "create_team":
            team_name = self._extract_team_name(query)
            if team_name:
                result = coord.create_team(team_name, f"由 {self._swarm_capability.agent_name} 创建")
                return {
                    "success": True,
                    "response": f"✅ 团队 '{team_name}' 创建成功！\n\n可以使用以下命令：\n- /swarm spawn {team_name} worker1 \"任务\" 启动 Agent\n- /swarm board {team_name} 查看看板"
                }
            return {"success": False, "response": "请提供团队名称"}
        
        elif intent == "spawn_agent":
            return await self._handle_spawn_agent(query, context)
        
        elif intent == "send_message":
            return await self._handle_send_message(query)
        
        elif intent == "check_board":
            team = self._extract_team_name(query) or self._swarm_capability.current_team
            if team:
                board = coord.get_board_state(team)
                return self._format_board_response(board)
            return {"success": False, "response": "请指定团队名称"}
        
        elif intent == "launch_template":
            return await self._handle_launch_template(query)
        
        elif intent == "create_task":
            return await self._handle_create_task(query)
        
        elif intent == "complete_task":
            return await self._handle_complete_task(query)
        
        return {"success": False, "response": "未知 Swarm 操作"}
    
    def _extract_team_name(self, query: str) -> Optional[str]:
        """提取团队名称"""
        patterns = [
            r"团队[：:]\s*(\S+)",
            r"team[：:]\s*(\S+)",
            r"named?\s+(\S+)",
            r"叫\s*(\S+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    async def _handle_spawn_agent(self, query: str, context: Dict) -> Dict[str, Any]:
        """处理启动 Agent"""
        coord = self._swarm_coordinator
        
        # 提取 Agent 名称和任务
        agent_match = re.search(r"(?:agent|worker|member)[：:\s]+(\w+)", query, re.IGNORECASE)
        task_match = re.search(r"""["'](.+?)["']|任务[：:]\s*(.+)""", query)
        
        agent_name = agent_match.group(1) if agent_match else None
        task = task_match.group(1) or task_match.group(2) if task_match else "未指定任务"
        
        team = self._extract_team_name(query) or self._swarm_capability.current_team
        if not team:
            return {"success": False, "response": "请先创建团队或指定团队名称"}
        
        if not agent_name:
            return {"success": False, "response": "请提供 Agent 名称"}
        
        result = coord.spawn_agent(team, agent_name, task)
        
        if result.get("success"):
            return {
                "success": True,
                "response": f"✅ Agent '{agent_name}' 在团队 '{team}' 启动成功！\n任务: {task}\n\n使用 /swarm board {team} 查看进度"
            }
        
        return {"success": False, "response": f"启动失败: {result.get('error', '未知错误')}"}
    
    async def _handle_send_message(self, query: str) -> Dict[str, Any]:
        """处理发送消息"""
        coord = self._swarm_coordinator
        
        to_match = re.search(r"(?:给|to)[：:\s]+(\w+)", query)
        content_match = re.search(r"""["'](.+?)["']|内容[：:]\s*(.+)""", query)
        
        to_agent = to_match.group(1) if to_match else None
        content = content_match.group(1) or content_match.group(2) if content_match else query
        
        team = self._swarm_capability.current_team
        if not team:
            return {"success": False, "response": "请先加入团队"}
        
        if not to_agent:
            return {"success": False, "response": "请指定接收者"}
        
        result = coord.send_message(team, to_agent, content, self._swarm_capability.agent_name or "agent")
        
        if result.get("success"):
            return {
                "success": True,
                "response": f"✅ 消息已发送给 '{to_agent}'"
            }
        
        return {"success": False, "response": "发送失败"}
    
    async def _handle_launch_template(self, query: str) -> Dict[str, Any]:
        """处理启动模板"""
        from src.swarm.team_template import launch_team_from_template
        
        templates = ["research", "dev", "hedgefund"]
        template_name = None
        
        for t in templates:
            if t in query.lower():
                template_name = t
                break
        
        if not template_name:
            return {
                "success": False,
                "response": "请指定模板: research (研究), dev (开发), hedgefund (投研)"
            }
        
        team_name = self._extract_team_name(query) or f"{template_name}-team"
        goal_match = re.search(r"""目标[：:]\s*(.+)""", query)
        goal = goal_match.group(1) if goal_match else "完成目标任务"
        
        result = launch_team_from_template(
            template_name,
            team_name,
            goal,
            self._swarm_coordinator
        )
        
        if result.get("success"):
            members = ", ".join(result.get("members", []))
            return {
                "success": True,
                "response": f"✅ {template_name} 团队 '{team_name}' 启动成功！\n\n成员: {members}\n目标: {goal}\n\n使用 /swarm board {team_name} 查看进度"
            }
        
        return {"success": False, "response": f"启动失败: {result.get('error', '未知错误')}"}
    
    async def _handle_create_task(self, query: str) -> Dict[str, Any]:
        """处理创建任务"""
        coord = self._swarm_coordinator
        
        task_match = re.search(r"""["'](.+?)["']|任务[：:]\s*(.+)""", query)
        task_title = task_match.group(1) or task_match.group(2) if task_match else query
        
        team = self._swarm_capability.current_team
        if not team:
            return {"success": False, "response": "请先加入团队"}
        
        owner_match = re.search(r"(?:owner|负责人)[：:\s]+(\w+)", query, re.IGNORECASE)
        owner = owner_match.group(1) if owner_match else self._swarm_capability.agent_name
        
        result = coord.create_task(team, task_title, owner)
        
        if result.get("success"):
            task_id = result.get("task_id")
            return {
                "success": True,
                "response": f"✅ 任务创建成功！\n\nID: {task_id}\n标题: {task_title}\n负责人: {owner}\n\n使用 /swarm task update {task_id} --status completed 完成任务"
            }
        
        return {"success": False, "response": "创建失败"}
    
    async def _handle_complete_task(self, query: str) -> Dict[str, Any]:
        """处理完成任务"""
        coord = self._swarm_coordinator
        
        task_match = re.search(r"(?:task|task\s*id|id)[：:\s]*([A-Z0-9]+)", query, re.IGNORECASE)
        task_id = task_match.group(1) if task_match else None
        
        team = self._swarm_capability.current_team
        if not team:
            return {"success": False, "response": "请先加入团队"}
        
        if not task_id:
            return {"success": False, "response": "请提供任务 ID"}
        
        from src.swarm.task_store import TaskStatus
        result = coord.update_task_status(team, task_id, TaskStatus.COMPLETED)
        
        if result.get("success"):
            return {
                "success": True,
                "response": f"✅ 任务 {task_id} 已标记完成！"
            }
        
        return {"success": False, "response": f"更新失败: {result.get('error', '未知错误')}"}
    
    def _format_board_response(self, board: Dict[str, Any]) -> Dict[str, Any]:
        """格式化看板响应"""
        team_info = board.get("team", {})
        tasks = board.get("tasks", {})
        agents = board.get("agents", [])
        
        response = f"""🦞 团队: {team_info.get('name', 'N/A')}
👥 成员数: {team_info.get('member_count', 0)}

📋 任务统计:
  ⏳ 待处理: {tasks.get('pending', 0)}
  🔄 进行中: {tasks.get('in_progress', 0)}
  ✅ 已完成: {tasks.get('completed', 0)}
  🚫 阻塞: {tasks.get('blocked', 0)}

🤖 Agent 状态:"""
        
        for agent in agents:
            status_emoji = {"idle": "💤", "working": "⚡", "completed": "✅"}.get(agent.get("status"), "❓")
            response += f"\n  {status_emoji} {agent.get('name', 'N/A')}: {agent.get('status', 'unknown')}"
        
        return {"success": True, "response": response}


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    import asyncio
    
    class DemoAgent(SwarmMixin):
        def __init__(self):
            super().__init__()
            self.init_swarm(agent_name="assistant", team="demo-team")
    
    async def test():
        agent = DemoAgent()
        
        queries = [
            "创建团队 test-team",
            "启动一个 agent 叫 worker1",
            "查看团队状态",
            "启动 research 模板团队 my-research",
        ]
        
        for query in queries:
            intent = agent.detect_swarm_intent(query)
            print(f"\n📝 Query: {query}")
            print(f"   Intent: {intent}")
            
            if intent:
                result = await agent.execute_swarm_action(intent, query, {})
                print(f"   Response: {result.get('response', result.get('error'))[:100]}...")
    
    asyncio.run(test())
