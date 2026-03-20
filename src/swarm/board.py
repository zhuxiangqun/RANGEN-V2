"""
Swarm 终端看板

实时监控团队状态:
- 任务看板 (Kanban)
- Agent 状态
- 消息收件箱
- 实时刷新
"""

import sys
import time
from typing import Optional, Dict, Any, List
from pathlib import Path

# Rich 库用于终端美化
try:
    from rich.console import Console
    from rich.table import Table
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.live import Live
    from rich.progress import Progress, SpinnerColumn, TextColumn
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from .coordinator import SwarmCoordinator


class SwarmBoard:
    """
    Swarm 终端看板
    
    实时显示:
    - 团队信息
    - 任务状态 (Kanban)
    - Agent 状态
    - 最新消息
    
    使用方式:
        board = SwarmBoard(coordinator)
        board.show()          # 一次性显示
        board.watch(interval=2)  # 实时监控
    """
    
    def __init__(self, coordinator: Optional[SwarmCoordinator] = None, base_dir: str = ".swarm"):
        self.coordinator = coordinator or SwarmCoordinator(base_dir)
        self.console = Console() if HAS_RICH else None
    
    def _format_status(self, status: str) -> str:
        """格式化状态"""
        icons = {
            "pending": "⏳",
            "in_progress": "🔄",
            "completed": "✅",
            "blocked": "🚫",
            "failed": "❌",
            "idle": "💤",
            "working": "⚡",
        }
        return icons.get(status, f"[{status}]")
    
    def _get_color(self, status: str) -> str:
        """获取状态颜色"""
        colors = {
            "pending": "yellow",
            "in_progress": "cyan",
            "completed": "green",
            "blocked": "red",
            "failed": "red bold",
            "idle": "dim",
            "working": "green",
        }
        return colors.get(status, "white")
    
    def show(self, team: str):
        """显示看板"""
        board = self.coordinator.get_board_state(team)
        
        if not board.get("team", {}).get("exists"):
            print(f"团队 '{team}' 不存在")
            return
        
        team_info = board["team"]
        tasks_stats = board["tasks"]
        agents = board["agents"]
        tasks = board.get("recent_tasks", [])
        
        # 打印团队信息
        print("\n" + "=" * 60)
        print(f"  🦞 团队: {team_info['name']}")
        print(f"  📝 描述: {team_info['description']}")
        print(f"  👥 成员: {team_info['member_count']} 人")
        print("=" * 60)
        
        # 打印任务统计
        print("\n📋 任务统计:")
        stats = f"  ⏳ 待处理: {tasks_stats['pending']}  |  🔄 进行中: {tasks_stats['in_progress']}  |  🚫 阻塞: {tasks_stats['blocked']}"
        print(stats)
        stats2 = f"  ✅ 完成: {tasks_stats['completed']}  |  ❌ 失败: {tasks_stats['failed']}  |  总计: {tasks_stats['total']}"
        print(stats2)
        
        # 打印任务列表
        if tasks:
            print("\n📋 任务列表:")
            print("-" * 60)
            print(f"{'ID':<8} {'标题':<30} {'负责人':<12} {'状态'}")
            print("-" * 60)
            for task in tasks:
                task_id = task["id"]
                title = task["title"][:28] + ".." if len(task["title"]) > 30 else task["title"]
                owner = task["owner"] or "-"
                status = self._format_status(task["status"])
                blocked_by = f" → {task['blocked_by']}" if task.get("blocked_by") else ""
                print(f"{task_id:<8} {title:<30} {owner:<12} {status}{blocked_by}")
        
        # 打印 Agent 状态
        if agents:
            print("\n🤖 Agent 状态:")
            print("-" * 60)
            for agent in agents:
                status = self._format_status(agent["status"])
                color = self._get_color(agent["status"])
                task = agent["task"] or "无任务"
                task_display = task[:35] + ".." if len(task) > 37 else task
                print(f"  {agent['name']:<15} {status}  {task_display}")
        
        print()
    
    def watch(self, team: str, interval: int = 3, max_iterations: Optional[int] = None):
        """
        实时监控看板
        
        Args:
            team: 团队名
            interval: 刷新间隔 (秒)
            max_iterations: 最大迭代次数 (None 表示无限)
        """
        if not HAS_RICH:
            print("需要安装 rich 库: pip install rich")
            return
        
        iteration = 0
        
        with Live(self._build_layout(team), refresh_per_second=1, screen=True) as live:
            while True:
                time.sleep(interval)
                live.update(self._build_layout(team))
                iteration += 1
                
                if max_iterations and iteration >= max_iterations:
                    break
    
    def _build_layout(self, team: str) -> "Layout":
        """构建布局"""
        from rich.layout import Layout
        from rich.panel import Panel
        
        board = self.coordinator.get_board_state(team)
        
        if not board.get("team", {}).get("exists"):
            return Layout(Panel("团队不存在"))
        
        layout = Layout()
        
        # 上: 团队信息
        layout.split_column(
            Layout(Panel(
                f"🦞 {board['team']['name']}  |  👥 {board['team']['member_count']} 人  |  📝 {board['team']['description']}",
                title="团队信息"
            ), size=3),
            Layout(name="main"),
        )
        
        # 下: 任务和 Agent
        layout["main"].split_row(
            Layout(name="tasks"),
            Layout(name="agents"),
        )
        
        # 任务面板
        tasks_table = Table(title="📋 任务", show_header=True)
        tasks_table.add_column("ID", style="cyan", width=8)
        tasks_table.add_column("标题", style="white")
        tasks_table.add_column("负责人", style="yellow", width=12)
        tasks_table.add_column("状态", width=10)
        
        for task in board.get("recent_tasks", []):
            status = self._format_status(task["status"])
            tasks_table.add_row(
                task["id"],
                task["title"][:30],
                task["owner"] or "-",
                status
            )
        
        layout["tasks"].update(Panel(tasks_table, title="📋 任务"))
        
        # Agent 面板
        agents_table = Table(title="🤖 Agent", show_header=True)
        agents_table.add_column("名称", style="cyan")
        agents_table.add_column("状态", width=12)
        agents_table.add_column("当前任务", style="white")
        
        for agent in board.get("agents", []):
            status = self._format_status(agent["status"])
            agents_table.add_row(
                agent["name"],
                status,
                (agent["task"] or "无任务")[:25]
            )
        
        layout["agents"].update(Panel(agents_table, title="🤖 Agent"))
        
        return layout
    
    def attach_tmux(self, team: str):
        """
        在 tmux 中显示看板
        
        在新 tmux 窗口中持续显示看板
        """
        import subprocess
        
        # 创建新窗口
        cmd = [
            "tmux",
            "new-window",
            "-n", f"swarm-{team}",
            "-t", f"swarm-{team}:0",
        ]
        
        try:
            subprocess.run(cmd, check=True)
            
            # 发送命令
            cmd = [
                "tmux",
                "send-keys",
                "-t", f"swarm-{team}",
                f"cd {Path.cwd()} && python3 -c \"from src.swarm.board import SwarmBoard; SwarmBoard().watch('{team}')\"",
                "Enter"
            ]
            subprocess.run(cmd)
            
            print(f"已在 tmux 窗口 'swarm-{team}' 启动看板")
            
        except subprocess.CalledProcessError:
            print("tmux 不可用或未安装")
            print("替代方案: python3 -m src.swarm.board --watch <team>")


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RANGEN Swarm Board - 终端看板")
    parser.add_argument("team", help="团队名")
    parser.add_argument("--watch", "-w", action="store_true", help="实时监控")
    parser.add_argument("--interval", "-i", type=int, default=3, help="刷新间隔 (秒)")
    parser.add_argument("--tmux", "-t", action="store_true", help="在 tmux 中显示")
    
    args = parser.parse_args()
    
    board = SwarmBoard()
    
    if args.tmux:
        board.attach_tmux(args.team)
    elif args.watch:
        board.watch(args.team, interval=args.interval)
    else:
        board.show(args.team)


if __name__ == "__main__":
    main()
