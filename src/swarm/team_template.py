"""
Swarm 团队模板系统

支持 TOML 模板定义团队，一键启动:
- research.toml - AI 研究团队
- dev.toml - 开发团队
- hedgefund.toml - 投研团队
"""

import os
import toml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class MemberTemplate:
    """成员模板"""
    name: str
    agent_type: str = "default"
    prompt: str = ""
    specialization: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TeamTemplate:
    """团队模板"""
    name: str
    description: str = ""
    leader: Dict[str, str] = field(default_factory=dict)
    members: List[MemberTemplate] = field(default_factory=list)
    default_goal: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: dict) -> "TeamTemplate":
        """从字典创建模板"""
        # 解析 leader
        leader_data = data.get("leader", {})
        leader = {
            "agent_type": leader_data.get("agent_type", "chief"),
            "prompt": leader_data.get("prompt", ""),
        }
        
        # 解析 members
        members = []
        for m in data.get("members", []):
            members.append(MemberTemplate(
                name=m.get("name", ""),
                agent_type=m.get("agent_type", "default"),
                prompt=m.get("prompt", ""),
                specialization=m.get("specialization", ""),
                metadata=m.get("metadata", {}),
            ))
        
        return cls(
            name=data.get("name", data.get("team", {}).get("name", "")),
            description=data.get("description", data.get("team", {}).get("description", "")),
            leader=leader,
            members=members,
            default_goal=data.get("default_goal", ""),
            metadata=data.get("metadata", {}),
        )


class TemplateRegistry:
    """模板注册表"""
    
    # 内置模板目录
    DEFAULT_TEMPLATES_DIR = Path(__file__).parent / "templates"
    
    def __init__(self, custom_dir: Optional[str] = None):
        self.custom_dir = Path(custom_dir) if custom_dir else None
        self._templates: Dict[str, TeamTemplate] = {}
        self._load_builtins()
    
    def _load_builtins(self):
        """加载内置模板"""
        # Research 团队
        self._templates["research"] = TeamTemplate(
            name="research",
            description="AI 研究团队 - 多个研究员并行实验",
            leader={
                "agent_type": "chief",
                "prompt": "你是一个研究团队的Leader，负责协调团队工作，监控实验进度，融合发现。",
            },
            members=[
                MemberTemplate(
                    name="researcher1",
                    agent_type="reasoning",
                    prompt="你是一个深度学习研究员，专注于模型架构优化。",
                    specialization="model_architecture",
                ),
                MemberTemplate(
                    name="researcher2",
                    agent_type="reasoning",
                    prompt="你是一个数据科学家，专注于超参数调优。",
                    specialization="hyperparameter",
                ),
                MemberTemplate(
                    name="coder",
                    agent_type="engineering",
                    prompt="你是一个全栈工程师，负责实现实验代码。",
                    specialization="implementation",
                ),
            ],
            default_goal="探索新的模型架构和训练策略",
        )
        
        # Dev 团队
        self._templates["dev"] = TeamTemplate(
            name="dev",
            description="软件开发团队 - 前后端分离开发",
            leader={
                "agent_type": "architect",
                "prompt": "你是一个软件开发团队的架构师，负责系统设计和任务分配。",
            },
            members=[
                MemberTemplate(
                    name="backend",
                    agent_type="engineering",
                    prompt="你是一个后端工程师，负责 API 和数据库开发。",
                    specialization="backend",
                ),
                MemberTemplate(
                    name="frontend",
                    agent_type="engineering",
                    prompt="你是一个前端工程师，负责 UI 开发。",
                    specialization="frontend",
                ),
                MemberTemplate(
                    name="tester",
                    agent_type="testing",
                    prompt="你是一个测试工程师，负责编写测试用例。",
                    specialization="testing",
                ),
            ],
            default_goal="开发完整功能模块",
        )
        
        # Hedge Fund 团队
        self._templates["hedgefund"] = TeamTemplate(
            name="hedgefund",
            description="AI 投资研究团队 - 7 人投研团",
            leader={
                "agent_type": "portfolio_manager",
                "prompt": "你是一个投资组合经理，负责整合所有分析师的意见，做出最终投资决策。",
            },
            members=[
                MemberTemplate(
                    name="buffett_analyst",
                    agent_type="fundamental",
                    prompt="你是一个价值投资分析师，参考巴菲特的投资理念，分析公司的护城河和长期价值。",
                    specialization="value_investing",
                ),
                MemberTemplate(
                    name="growth_analyst",
                    agent_type="fundamental",
                    prompt="你是一个成长股分析师，专注于分析公司的增长潜力和市场空间。",
                    specialization="growth_investing",
                ),
                MemberTemplate(
                    name="technical_analyst",
                    agent_type="technical",
                    prompt="你是一个技术分析师，通过 K 线、均线、RSI 等指标分析股价走势。",
                    specialization="technical_analysis",
                ),
                MemberTemplate(
                    name="sentiment_analyst",
                    agent_type="sentiment",
                    prompt="你是一个舆情分析师，分析新闻、社交媒体对股价的影响。",
                    specialization="sentiment_analysis",
                ),
                MemberTemplate(
                    name="risk_manager",
                    agent_type="risk",
                    prompt="你是一个风险控制员，负责评估投资风险和仓位管理。",
                    specialization="risk_management",
                ),
            ],
            default_goal="分析投资标的，给出买入/卖出/持有建议",
        )
    
    def load_from_file(self, path: str) -> TeamTemplate:
        """从文件加载模板"""
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"模板文件不存在: {path}")
        
        with open(path, encoding="utf-8") as f:
            data = toml.load(f)
        
        return TeamTemplate.from_dict(data)
    
    def register(self, name: str, template: TeamTemplate):
        """注册模板"""
        self._templates[name] = template
    
    def get(self, name: str) -> Optional[TeamTemplate]:
        """获取模板"""
        return self._templates.get(name)
    
    def list_templates(self) -> List[str]:
        """列出所有模板"""
        return list(self._templates.keys())
    
    def list_templates_with_info(self) -> List[Dict[str, str]]:
        """列出所有模板及信息"""
        return [
            {
                "name": name,
                "description": tmpl.description,
                "member_count": len(tmpl.members) + 1,  # +1 for leader
            }
            for name, tmpl in self._templates.items()
        ]


def launch_team_from_template(
    template_name: str,
    team_name: str,
    goal: str,
    coordinator: Any,
    custom_template_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    从模板启动团队
    
    Args:
        template_name: 模板名 (research/dev/hedgefund)
        team_name: 团队名
        goal: 团队目标
        coordinator: SwarmCoordinator 实例
        custom_template_path: 自定义模板路径
        
    Returns:
        启动结果
    """
    # 获取模板
    registry = TemplateRegistry()
    
    if custom_template_path:
        template = registry.load_from_file(custom_template_path)
    else:
        template = registry.get(template_name)
        if not template:
            return {
                "success": False,
                "error": f"模板 '{template_name}' 不存在。可用模板: {registry.list_templates()}"
            }
    
    # 创建团队
    result = coordinator.create_team(team_name, f"{template.description} - {goal}")
    if not result.get("success"):
        return result
    
    # 启动 Leader
    leader_name = "leader"
    coordinator.spawn_agent(
        team=team_name,
        name=leader_name,
        task=f"协调团队完成目标: {goal}",
        agent_type=template.leader.get("agent_type", "chief"),
    )
    
    # 启动成员
    spawned_members = []
    for member in template.members:
        coordinator.spawn_agent(
            team=team_name,
            name=member.name,
            task=f"负责 {member.specialization}: {goal}",
            agent_type=member.agent_type,
        )
        spawned_members.append(member.name)
    
    return {
        "success": True,
        "team": team_name,
        "leader": leader_name,
        "members": spawned_members,
        "template": template_name,
        "goal": goal,
        "member_count": len(spawned_members) + 1,
    }


# =============================================================================
# 内置模板文件
# =============================================================================

def get_builtin_templates_dir() -> Path:
    """获取内置模板目录"""
    return TemplateRegistry.DEFAULT_TEMPLATES_DIR


def create_template_file(name: str, content: str):
    """创建模板文件"""
    templates_dir = get_builtin_templates_dir()
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = templates_dir / f"{name}.toml"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return file_path


# 默认创建 research.toml
create_template_file("research", """
name = "research"
description = "AI 研究团队"

[leader]
agent_type = "chief"
prompt = "你是一个研究团队的Leader，负责协调团队工作"

[[members]]
name = "researcher1"
agent_type = "reasoning"
prompt = "你是一个深度学习研究员"
specialization = "model_optimization"

[[members]]
name = "researcher2"
agent_type = "reasoning"
prompt = "你是一个数据科学家"
specialization = "data_analysis"

[[members]]
name = "coder"
agent_type = "engineering"
prompt = "你是一个全栈工程师"
specialization = "implementation"
""")

# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    from src.swarm.coordinator import get_coordinator
    
    registry = TemplateRegistry()
    
    print("可用模板:")
    for info in registry.list_templates_with_info():
        print(f"  • {info['name']}: {info['description']} ({info['member_count']}人)")
    
    print("\n从模板启动团队:")
    coord = get_coordinator("/tmp/.swarm-test")
    
    result = launch_team_from_template(
        template_name="research",
        team_name="my-research",
        goal="优化 transformer 架构",
        coordinator=coord,
    )
    print(f"启动结果: {result}")
    
    print("\n看板状态:")
    board = coord.get_board_state("my-research")
    print(f"团队: {board['team']['name']}")
    print(f"成员数: {board['team']['member_count']}")
