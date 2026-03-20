"""
RANGEN Swarm CLI

命令行接口:
- rangenswarm team create <name>
- rangenswarm spawn --team <team> --agent <name> --task <task>
- rangenswarm inbox send <team> <to> <message>
- rangenswarm task create <team> <title>
- rangenswarm board show <team>
"""

import sys
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import typer
    from rich.console import Console
    from rich.table import Table
    from rich import print as rprint
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    typer = None

from src.swarm.coordinator import get_coordinator
from src.swarm.task_store import TaskStatus


app = typer.Typer(
    name="rangenswarm",
    help="RANGEN Swarm CLI - Agent 蜂群协调工具",
)


# =============================================================================
# 辅助函数
# =============================================================================

def get_coord():
    """获取协调器"""
    return get_coordinator(".swarm")


def print_json(data):
    """打印 JSON"""
    console = Console()
    console.print_json(json.dumps(data, ensure_ascii=False, indent=2))


def print_table(title: str, headers: list, rows: list):
    """打印表格"""
    if not HAS_RICH:
        print(f"\n{title}")
        print(" | ".join(headers))
        print("-" * 50)
        for row in rows:
            print(" | ".join(str(c) for c in row))
        return
    
    console = Console()
    table = Table(title=title)
    
    for header in headers:
        table.add_column(header, style="cyan")
    
    for row in rows:
        table.add_row(*[str(c) for c in row])
    
    console.print(table)


# =============================================================================
# 团队命令
# =============================================================================

@app.command("team")
def team_command(
    action: str = typer.Argument(..., help="操作: create, delete, list, status"),
    name: str = typer.Option(None, "--name", "-n", help="团队名"),
    description: str = typer.Option("", "--description", "-d", help="团队描述"),
    force: bool = typer.Option(False, "--force", "-f", help="强制删除"),
    json_output: bool = typer.Option(False, "--json", help="JSON 输出"),
):
    """团队管理"""
    coord = get_coord()
    
    if action == "create":
        if not name:
            rprint("[red]错误: 需要指定 --name[/red]")
            raise typer.Exit(1)
        
        result = coord.create_team(name, description)
        if json_output:
            print_json(result)
        else:
            rprint(f"[green]✓[/green] 团队 {name} 创建成功")
    
    elif action == "delete":
        if not name:
            rprint("[red]错误: 需要指定 --name[/red]")
            raise typer.Exit(1)
        
        result = coord.delete_team(name, force)
        if json_output:
            print_json(result)
        else:
            if result["success"]:
                rprint(f"[green]✓[/green] 团队 {name} 已删除")
            else:
                rprint(f"[red]✗[/red] {result['error']}")
    
    elif action == "list":
        teams = coord.list_teams()
        if json_output:
            print_json(teams)
        else:
            if not teams:
                rprint("[yellow]暂无团队[/yellow]")
            else:
                rows = [[t["name"], t["description"], str(t["member_count"])] for t in teams]
                print_table("团队列表", ["名称", "描述", "成员数"], rows)
    
    elif action == "status":
        if not name:
            rprint("[red]错误: 需要指定 --name[/red]")
            raise typer.Exit(1)
        
        status = coord.get_team_status(name)
        if json_output:
            print_json(status)
        else:
            if not status.get("exists"):
                rprint(f"[red]团队 {name} 不存在[/red]")
            else:
                rprint(f"\n[bold]团队: {status['name']}[/bold]")
                rprint(f"描述: {status['description']}")
                rprint(f"Leader: {status['leader']}")
                rprint(f"成员数: {status['member_count']}")
                rprint(f"创建时间: {status['created_at']}")
    else:
        rprint(f"[red]未知操作: {action}[/red]")
        raise typer.Exit(1)


# =============================================================================
# Agent 命令
# =============================================================================

@app.command("spawn")
def spawn_command(
    team: str = typer.Option(..., "--team", "-t", help="团队名"),
    agent: str = typer.Option(..., "--agent", "-a", help="Agent 名"),
    task: str = typer.Option("", "--task", help="初始任务"),
    agent_type: str = typer.Option("default", "--type", help="Agent 类型"),
    json_output: bool = typer.Option(False, "--json", help="JSON 输出"),
):
    """启动 Agent"""
    coord = get_coord()
    result = coord.spawn_agent(team, agent, task, agent_type)
    
    if json_output:
        print_json(result)
    else:
        if result["success"]:
            rprint(f"[green]✓[/green] Agent {agent} 在团队 {team} 启动成功")
            if task:
                rprint(f"  任务: {task}")
        else:
            rprint(f"[red]✗[/red] {result['error']}")


@app.command("agents")
def agents_command(
    team: str = typer.Argument(..., help="团队名"),
    json_output: bool = typer.Option(False, "--json", help="JSON 输出"),
):
    """列出团队 Agent"""
    coord = get_coord()
    agents = coord.list_agents(team)
    
    if json_output:
        print_json(agents)
    else:
        if not agents:
            rprint(f"[yellow]团队 {team} 没有 Agent[/yellow]")
        else:
            rows = [[a["name"], a["status"], a["task"] or "-"] for a in agents]
            print_table(f"团队 {team} 的 Agent", ["名称", "状态", "当前任务"], rows)


# =============================================================================
# 任务命令
# =============================================================================

@app.command("task")
def task_command(
    action: str = typer.Argument(..., help="操作: create, list, update, stats"),
    team: str = typer.Option(..., "--team", "-t", help="团队名"),
    title: str = typer.Option("", "--title", help="任务标题"),
    task_id: str = typer.Option("", "--id", help="任务ID"),
    status: str = typer.Option("", "--status", "-s", help="任务状态"),
    result: str = typer.Option("", "--result", "-r", help="执行结果"),
    owner: str = typer.Option("", "--owner", "-o", help="负责人"),
    blocked_by: str = typer.Option("", "--blocked-by", help="依赖任务ID (逗号分隔)"),
    json_output: bool = typer.Option(False, "--json", help="JSON 输出"),
):
    """任务管理"""
    coord = get_coord()
    
    if action == "create":
        if not title:
            rprint("[red]错误: 需要指定 --title[/red]")
            raise typer.Exit(1)
        
        blocked_list = [b.strip() for b in blocked_by.split(",") if b.strip()] if blocked_by else None
        result = coord.create_task(team, title, owner, blocked_list)
        
        if json_output:
            print_json(result)
        else:
            rprint(f"[green]✓[/green] 任务创建成功")
            rprint(f"  ID: {result['task_id']}")
            rprint(f"  标题: {result['title']}")
            rprint(f"  状态: {result['status']}")
            if result.get("blocked_by"):
                rprint(f"  依赖: {result['blocked_by']}")
    
    elif action == "list":
        tasks = coord.list_tasks(team)
        
        if json_output:
            print_json(tasks)
        else:
            if not tasks:
                rprint(f"[yellow]团队 {team} 没有任务[/yellow]")
            else:
                status_icon = {
                    "pending": "⏳",
                    "in_progress": "🔄",
                    "completed": "✅",
                    "blocked": "🚫",
                    "failed": "❌",
                }
                rows = [
                    [t["id"], t["title"][:30], t["owner"] or "-", status_icon.get(t["status"], "❓")]
                    for t in tasks
                ]
                print_table(f"团队 {team} 的任务", ["ID", "标题", "负责人", "状态"], rows)
    
    elif action == "update":
        if not task_id:
            rprint("[red]错误: 需要指定 --id[/red]")
            raise typer.Exit(1)
        if not status:
            rprint("[red]错误: 需要指定 --status[/red]")
            raise typer.Exit(1)
        
        result = coord.update_task_status(team, task_id, status, result)
        
        if json_output:
            print_json(result)
        else:
            if result["success"]:
                rprint(f"[green]✓[/green] 任务 {task_id} 状态已更新为 {status}")
            else:
                rprint(f"[red]✗[/red] {result['error']}")
    
    elif action == "stats":
        stats = coord.get_task_stats(team)
        
        if json_output:
            print_json(stats)
        else:
            rprint(f"\n[bold]团队 {team} 任务统计[/bold]")
            rprint(f"  总计: {stats['total']}")
            rprint(f"  ⏳ 待处理: {stats['pending']}")
            rprint(f"  🔄 进行中: {stats['in_progress']}")
            rprint(f"  🚫 阻塞: {stats['blocked']}")
            rprint(f"  ✅ 完成: {stats['completed']}")
            rprint(f"  ❌ 失败: {stats['failed']}")
    
    else:
        rprint(f"[red]未知操作: {action}[/red]")
        raise typer.Exit(1)


# =============================================================================
# 消息命令
# =============================================================================

@app.command("inbox")
def inbox_command(
    action: str = typer.Argument(..., help="操作: send, receive, peek, broadcast"),
    team: str = typer.Option(..., "--team", "-t", help="团队名"),
    to: str = typer.Option("", "--to", help="接收者"),
    message: str = typer.Option("", "--message", "-m", help="消息内容"),
    from_agent: str = typer.Option("user", "--from", help="发送者"),
    limit: int = typer.Option(50, "--limit", "-l", help="消息数量"),
    json_output: bool = typer.Option(False, "--json", help="JSON 输出"),
):
    """消息管理"""
    coord = get_coord()
    
    if action == "send":
        if not to or not message:
            rprint("[red]错误: 需要指定 --to 和 --message[/red]")
            raise typer.Exit(1)
        
        result = coord.send_message(team, to, message, from_agent)
        
        if json_output:
            print_json(result)
        else:
            rprint(f"[green]✓[/green] 消息已发送给 {to}")
            rprint(f"  消息ID: {result['message_id']}")
    
    elif action == "receive":
        if not to:
            rprint("[red]错误: 需要指定 --to[/red]")
            raise typer.Exit(1)
        
        messages = coord.receive_messages(team, to, limit)
        
        if json_output:
            print_json(messages)
        else:
            if not messages:
                rprint(f"[yellow]{to} 没有新消息[/yellow]")
            else:
                for msg in messages:
                    rprint(f"\n[bold]来自: {msg['from_agent']}[/bold]")
                    rprint(f"  {msg['content']}")
                    rprint(f"  时间: {msg['timestamp']}")
    
    elif action == "peek":
        if not to:
            rprint("[red]错误: 需要指定 --to[/red]")
            raise typer.Exit(1)
        
        messages = coord.peek_messages(team, to, limit)
        
        if json_output:
            print_json(messages)
        else:
            if not messages:
                rprint(f"[yellow]{to} 没有消息[/yellow]")
            else:
                for msg in messages:
                    rprint(f"\n[bold]来自: {msg['from_agent']}[/bold]")
                    rprint(f"  {msg['content']}")
    
    elif action == "broadcast":
        if not message:
            rprint("[red]错误: 需要指定 --message[/red]")
            raise typer.Exit(1)
        
        result = coord.broadcast(team, message, from_agent)
        
        if json_output:
            print_json(result)
        else:
            rprint(f"[green]✓[/green] 广播已发送")
            rprint(f"  消息ID: {result['message_id']}")
    
    else:
        rprint(f"[red]未知操作: {action}[/red]")
        raise typer.Exit(1)


# =============================================================================
# 看板命令
# =============================================================================

@app.command("board")
def board_command(
    team: str = typer.Argument(..., help="团队名"),
    action: str = typer.Option("show", "--action", "-a", help="操作: show, live"),
    json_output: bool = typer.Option(False, "--json", help="JSON 输出"),
):
    """监控面板"""
    coord = get_coord()
    board = coord.get_board_state(team)
    
    if json_output:
        print_json(board)
    else:
        # 打印团队状态
        team_info = board["team"]
        rprint(f"\n[bold cyan]🦞 团队: {team_info['name']}[/bold cyan]")
        rprint(f"描述: {team_info['description']}")
        rprint(f"成员数: {team_info['member_count']}")
        
        # 打印任务统计
        tasks = board["tasks"]
        rprint(f"\n[bold]📋 任务统计[/bold]")
        rprint(f"  ⏳ 待处理: {tasks['pending']}  |  🔄 进行中: {tasks['in_progress']}  |  🚫 阻塞: {tasks['blocked']}")
        rprint(f"  ✅ 完成: {tasks['completed']}  |  ❌ 失败: {tasks['failed']}")
        
        # 打印 Agent 状态
        agents = board["agents"]
        if agents:
            rprint(f"\n[bold]🤖 Agent 状态[/bold]")
            for agent in agents:
                status_color = {
                    "idle": "yellow",
                    "working": "green",
                    "completed": "blue",
                    "failed": "red",
                }.get(agent["status"], "white")
                rprint(f"  • {agent['name']} [{status_color}]{agent['status']}[/{status_color}]")
                if agent["task"]:
                    rprint(f"    任务: {agent['task']}")


# =============================================================================
# 主入口
# =============================================================================

@app.callback()
def main():
    """
    RANGEN Swarm CLI - Agent 蜂群协调工具
    
    示例:
      rangenswarm team create my-team
      rangenswarm spawn --team my-team --agent worker1 --task "实现功能"
      rangenswarm task create --team my-team --title "设计API"
      rangenswarm inbox send --team my-team --to worker1 --message "任务完成"
      rangenswarm board my-team
    """
    pass


if __name__ == "__main__":
    app()
