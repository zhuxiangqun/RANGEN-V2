#!/usr/bin/env python3
"""
Agent迁移管理脚本
统一管理所有Agent的迁移工作
"""

import asyncio
import sys
import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# 设置项目环境
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
    print('✅ 已加载环境变量')
except ImportError:
    print('⚠️ python-dotenv未安装')

@dataclass
class MigrationTask:
    """迁移任务"""
    agent_name: str
    target_agent: str
    priority: str  # P1, P2
    status: str  # pending, in_progress, completed, failed
    adapter_created: bool = False
    wrapper_created: bool = False
    code_replaced: bool = False
    gradual_replacement_started: bool = False
    replacement_rate: float = 0.0
    last_updated: Optional[datetime] = None
    notes: str = ""

@dataclass
class MigrationDashboard:
    """迁移仪表板"""
    tasks: List[MigrationTask]
    overall_progress: float
    completed_count: int
    in_progress_count: int
    pending_count: int
    last_updated: datetime

class AgentMigrationManager:
    """Agent迁移管理器"""

    def __init__(self):
        self.state_file = Path("data/migration_state.json")
        self.migration_tasks = self._load_or_initialize_migration_tasks()
        self.dashboard = self._create_dashboard()

    def _load_or_initialize_migration_tasks(self) -> List[MigrationTask]:
        """加载或初始化迁移任务"""
        # 尝试从文件加载
        if self.state_file.exists():
            try:
                loaded_tasks = self._load_migration_state()
                if loaded_tasks:
                    print("✅ 已加载保存的迁移状态")
                    return loaded_tasks
            except Exception as e:
                print(f"⚠️ 加载迁移状态失败，使用默认状态: {e}")

        # 使用默认初始化
        print("ℹ️ 使用默认迁移状态初始化")
        return self._initialize_migration_tasks()

    def _load_migration_state(self) -> Optional[List[MigrationTask]]:
        """从文件加载迁移状态"""
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            tasks = []
            for task_data in data.get('tasks', []):
                # 将字符串日期转换回datetime对象
                last_updated = None
                if task_data.get('last_updated'):
                    try:
                        last_updated = datetime.fromisoformat(task_data['last_updated'])
                    except:
                        pass

                task = MigrationTask(
                    agent_name=task_data['agent_name'],
                    target_agent=task_data['target_agent'],
                    priority=task_data['priority'],
                    status=task_data['status'],
                    adapter_created=task_data.get('adapter_created', False),
                    wrapper_created=task_data.get('wrapper_created', False),
                    code_replaced=task_data.get('code_replaced', False),
                    gradual_replacement_started=task_data.get('gradual_replacement_started', False),
                    replacement_rate=task_data.get('replacement_rate', 0.0),
                    last_updated=last_updated,
                    notes=task_data.get('notes', '')
                )
                tasks.append(task)

            return tasks
        except Exception as e:
            print(f"❌ 加载迁移状态文件失败: {e}")
            return None

    def _save_migration_state(self):
        """保存迁移状态到文件"""
        try:
            # 确保目录存在
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            # 转换为可序列化的格式
            data = {
                'timestamp': datetime.now().isoformat(),
                'tasks': []
            }

            for task in self.migration_tasks:
                task_data = asdict(task)
                # 将datetime对象转换为字符串
                if task_data.get('last_updated'):
                    task_data['last_updated'] = task_data['last_updated'].isoformat()
                data['tasks'].append(task_data)

            # 保存到文件
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print("✅ 迁移状态已保存")
        except Exception as e:
            print(f"❌ 保存迁移状态失败: {e}")

    def _initialize_migration_tasks(self) -> List[MigrationTask]:
        """初始化迁移任务"""
        tasks = [
            # P1优先级任务
            MigrationTask(
                agent_name="ReActAgent",
                target_agent="ReasoningExpert",
                priority="P1",
                status="in_progress",
                adapter_created=True,
                wrapper_created=True,
                code_replaced=True,
                gradual_replacement_started=True,
                replacement_rate=0.01,
                notes="逐步替换进行中，当前替换率1%"
            ),
            MigrationTask(
                agent_name="KnowledgeRetrievalAgent",
                target_agent="RAGExpert",
                priority="P1",
                status="completed",
                adapter_created=True,
                wrapper_created=True,
                code_replaced=True,
                gradual_replacement_started=False,
                replacement_rate=0.0,
                notes="迁移测试验证通过"
            ),
            MigrationTask(
                agent_name="RAGAgent",
                target_agent="RAGExpert",
                priority="P1",
                status="completed",
                adapter_created=True,
                wrapper_created=True,
                code_replaced=True,
                gradual_replacement_started=False,
                replacement_rate=0.0,
                notes="迁移测试验证通过"
            ),

            # P2优先级任务
            MigrationTask(
                agent_name="CitationAgent",
                target_agent="QualityController",
                priority="P2",
                status="completed",
                adapter_created=True,
                wrapper_created=True,
                code_replaced=True,
                gradual_replacement_started=False,
                replacement_rate=0.0,
                notes="试点项目，已验证完成"
            ),
            MigrationTask(
                agent_name="ChiefAgent",
                target_agent="AgentCoordinator",
                priority="P2",
                status="pending",
                adapter_created=True,
                wrapper_created=True,
                code_replaced=True,
                gradual_replacement_started=False,
                replacement_rate=0.0,
                notes="适配器和包装器已创建，等待开始迁移"
            ),
            MigrationTask(
                agent_name="AnswerGenerationAgent",
                target_agent="RAGExpert",
                priority="P2",
                status="pending",
                adapter_created=True,
                wrapper_created=True,
                code_replaced=True,
                gradual_replacement_started=False,
                replacement_rate=0.0,
                notes="适配器和包装器已创建，等待开始迁移"
            ),
            MigrationTask(
                agent_name="PromptEngineeringAgent",
                target_agent="ToolOrchestrator",
                priority="P2",
                status="pending",
                adapter_created=True,
                wrapper_created=True,
                code_replaced=True,
                gradual_replacement_started=False,
                replacement_rate=0.0,
                notes="适配器和包装器已创建，等待开始迁移"
            )
        ]

        return tasks

    def _create_dashboard(self) -> MigrationDashboard:
        """创建迁移仪表板"""
        completed_count = sum(1 for task in self.migration_tasks if task.status == "completed")
        in_progress_count = sum(1 for task in self.migration_tasks if task.status == "in_progress")
        pending_count = sum(1 for task in self.migration_tasks if task.status == "pending")

        total_tasks = len(self.migration_tasks)
        overall_progress = (completed_count / total_tasks) * 100 if total_tasks > 0 else 0

        return MigrationDashboard(
            tasks=self.migration_tasks,
            overall_progress=overall_progress,
            completed_count=completed_count,
            in_progress_count=in_progress_count,
            pending_count=pending_count,
            last_updated=datetime.now()
        )

    def show_migration_dashboard(self):
        """显示迁移仪表板"""
        print("🚀 RANGEN Agent迁移管理仪表板")
        print("=" * 60)

        dashboard = self.dashboard

        # 总体进度
        print("📊 总体进度:")
        print(f"   总任务数: {len(dashboard.tasks)}")
        print(f"   已完成: {dashboard.completed_count:.1f}")
        print(f"   进行中: {dashboard.in_progress_count}")
        print(f"   进行中: {dashboard.in_progress_count}")
        print(f"   待开始: {dashboard.pending_count}")

        # 按优先级分组显示
        p1_tasks = [t for t in dashboard.tasks if t.priority == "P1"]
        p2_tasks = [t for t in dashboard.tasks if t.priority == "P2"]

        print(f"\n🎯 P1优先级任务 ({len(p1_tasks)}个):")
        for task in p1_tasks:
            status_icon = self._get_status_icon(task.status)
            print(f"   {status_icon} {task.agent_name} → {task.target_agent}")
            print(f"      状态: {task.status} | 替换率: {task.replacement_rate:.1%}")
            if task.notes:
                print(f"      备注: {task.notes}")

        print(f"\n📋 P2优先级任务 ({len(p2_tasks)}个):")
        for task in p2_tasks:
            status_icon = self._get_status_icon(task.status)
            print(f"   {status_icon} {task.agent_name} → {task.target_agent}")
            print(f"      状态: {task.status} | 替换率: {task.replacement_rate:.1%}")
            if task.notes:
                print(f"      备注: {task.notes}")

        print("\n💡 可用操作:")
        print("   1. 启动下一个P1任务")
        print("   2. 启动下一个P2任务")
        print("   3. 查看详细任务状态")
        print("   4. 调整替换率")
        print("   5. 动态更新运行中Agent的替换率")
        print("   6. 生成迁移报告")
        print("   7. 退出")

    def _get_status_icon(self, status: str) -> str:
        """获取状态图标"""
        icons = {
            "completed": "✅",
            "in_progress": "🔄",
            "pending": "⏳",
            "failed": "❌"
        }
        return icons.get(status, "❓")

    def get_next_pending_task(self, priority: str = "P1") -> Optional[MigrationTask]:
        """获取下一个待处理任务"""
        pending_tasks = [
            task for task in self.migration_tasks
            if task.status == "pending" and task.priority == priority
        ]

        if pending_tasks:
            return pending_tasks[0]
        return None

    async def start_next_migration_task(self, priority: str = "P1"):
        """启动下一个迁移任务"""
        next_task = self.get_next_pending_task(priority)

        if not next_task:
            print(f"⚠️ 没有待处理的{priority}优先级任务")
            return

        print(f"🚀 启动{priority}任务: {next_task.agent_name} → {next_task.target_agent}")

        # 更新任务状态
        next_task.status = "in_progress"
        next_task.last_updated = datetime.now()

        # 这里可以添加实际的启动逻辑
        # 比如启动逐步替换、运行测试等

        print(f"✅ 任务 {next_task.agent_name} 启动成功")

    def adjust_replacement_rate(self, agent_name: str, new_rate: float):
        """调整替换率"""
        for task in self.migration_tasks:
            if task.agent_name == agent_name:
                old_rate = task.replacement_rate
                task.replacement_rate = min(max(new_rate, 0.0), 1.0)
                task.last_updated = datetime.now()
                # 动态更新备注信息
                task.notes = f"逐步替换进行中，当前替换率{task.replacement_rate:.1%}"
                # 重新创建仪表板以反映最新状态
                self.dashboard = self._create_dashboard()
                # 保存状态到文件
                self._save_migration_state()
                print(f"   替换率从 {old_rate:.1%} 调整为 {task.replacement_rate:.1%}")
                return

        print(f"❌ 未找到Agent: {agent_name}")

    def update_running_agent_replacement_rate(self, agent_name: str, new_rate: float) -> bool:
        """
        动态更新运行中Agent的替换率

        Args:
            agent_name: Agent名称
            new_rate: 新的替换率 (0.0-1.0)

        Returns:
            bool: 是否更新成功
        """
        try:
            # 标准化替换率
            new_rate = min(max(new_rate, 0.0), 1.0)

            # 查找对应的任务
            task = None
            for t in self.migration_tasks:
                if t.agent_name == agent_name:
                    task = t
                    break

            if not task:
                print(f"❌ 未找到Agent: {agent_name}")
                return False

            # 尝试动态更新运行中的Agent
            if agent_name == "ReActAgent":
                # 尝试获取ReActAgentWrapper实例并更新替换率
                success = self._update_react_agent_replacement_rate(new_rate)
                if success:
                    # 同步更新任务状态
                    task.replacement_rate = new_rate
                    task.notes = f"逐步替换进行中，当前替换率{new_rate:.1%}"
                    self.dashboard = self._create_dashboard()
                    return True
                else:
                    print("⚠️ ReActAgent不支持动态更新，请重启应用以应用新替换率")
                    return False
            else:
                print(f"⚠️ {agent_name}暂不支持动态替换率更新")
                return False

        except Exception as e:
            print(f"❌ 动态更新失败: {e}")
            return False

    def _update_react_agent_replacement_rate(self, new_rate: float) -> bool:
        """
        更新ReActAgent的替换率

        注意：这个方法需要根据实际的应用架构来实现
        可能需要通过某种方式获取运行中的ReActAgentWrapper实例
        """
        try:
            # 这里需要根据实际的应用架构来获取ReActAgentWrapper实例
            # 可能的实现方式：
            # 1. 通过全局注册表
            # 2. 通过依赖注入容器
            # 3. 通过特定的管理接口

            # 目前暂时返回False，表示不支持动态更新
            # 在实际应用中，需要实现具体的更新逻辑

            return False

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"更新ReActAgent替换率失败: {e}")
            return False

    def generate_migration_report(self):
        """生成迁移报告"""
        print("📝 生成迁移报告...")

        report = {
            'timestamp': datetime.now().isoformat(),
            'dashboard': {
                'overall_progress': self.dashboard.overall_progress,
                'completed_count': self.dashboard.completed_count,
                'in_progress_count': self.dashboard.in_progress_count,
                'pending_count': self.dashboard.pending_count
            },
            'tasks': [
                {
                    'agent_name': task.agent_name,
                    'target_agent': task.target_agent,
                    'priority': task.priority,
                    'status': task.status,
                    'replacement_rate': task.replacement_rate,
                    'adapter_created': task.adapter_created,
                    'wrapper_created': task.wrapper_created,
                    'code_replaced': task.code_replaced,
                    'gradual_replacement_started': task.gradual_replacement_started,
                    'notes': task.notes,
                    'last_updated': task.last_updated.isoformat() if task.last_updated else None
                }
                for task in self.migration_tasks
            ],
            'recommendations': self._generate_recommendations()
        }

        # 保存报告
        report_path = project_root / 'reports' / 'agent_migration_report.json'
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"✅ 迁移报告已保存: {report_path}")

        # 打印摘要
        self._print_report_summary(report)

    def _generate_recommendations(self) -> List[str]:
        """生成建议"""
        recommendations = []

        # 检查进行中的任务
        in_progress_tasks = [t for t in self.migration_tasks if t.status == "in_progress"]
        if in_progress_tasks:
            recommendations.append(f"继续推进进行中的任务: {[t.agent_name for t in in_progress_tasks]}")

        # 检查待处理任务
        pending_p1 = [t for t in self.migration_tasks if t.status == "pending" and t.priority == "P1"]
        if pending_p1:
            recommendations.append(f"优先启动P1任务: {[t.agent_name for t in pending_p1]}")

        # 检查替换率低的进行中任务
        low_rate_tasks = [t for t in self.migration_tasks if t.status == "in_progress" and t.replacement_rate < 0.5]
        if low_rate_tasks:
            recommendations.append(f"考虑增加替换率: {[t.agent_name for t in low_rate_tasks]}")

        return recommendations

    def _print_report_summary(self, report: Dict[str, Any]):
        """打印报告摘要"""
        print("\n📊 迁移报告摘要")
        print("-" * 30)
        print(f"总任务: {report['dashboard']['total_count']}")
        print(f"已完成: {report['dashboard']['completed_count']}")
        print(f"进行中: {report['dashboard']['in_progress_count']}")
        print(f"待处理: {report['dashboard']['pending_count']}")

        if report['recommendations']:
            print("\n💡 建议:")
            for rec in report['recommendations']:
                print(f"   • {rec}")

def main():
    """主函数"""
    manager = AgentMigrationManager()

    try:
        while True:
            manager.show_migration_dashboard()

            try:
                choice = input("\n请选择操作 (1-7): ").strip()

                if choice == "1":
                    asyncio.run(manager.start_next_migration_task("P1"))
                elif choice == "2":
                    asyncio.run(manager.start_next_migration_task("P2"))
                elif choice == "3":
                    # 显示详细状态
                    print("\n📋 详细任务状态:")
                    for task in manager.migration_tasks:
                        print(f"\n{task.agent_name} → {task.target_agent}:")
                        print(f"  优先级: {task.priority}")
                        print(f"  状态: {task.status}")
                        print(f"  替换率: {task.replacement_rate:.1%}")
                        print(f"  适配器: {'✅' if task.adapter_created else '❌'}")
                        print(f"  包装器: {'✅' if task.wrapper_created else '❌'}")
                        print(f"  代码替换: {'✅' if task.code_replaced else '❌'}")
                        print(f"  逐步替换: {'✅' if task.gradual_replacement_started else '❌'}")
                        if task.notes:
                            print(f"  备注: {task.notes}")
                elif choice == "4":
                    agent_name = input("输入Agent名称: ").strip()
                    try:
                        new_rate = float(input("输入新的替换率 (0.0-1.0): ").strip())
                        manager.adjust_replacement_rate(agent_name, new_rate)
                    except ValueError:
                        print("❌ 无效的替换率")
                elif choice == "5":
                    # 动态更新运行中Agent的替换率
                    agent_name = input("输入要更新的Agent名称: ").strip()
                    try:
                        new_rate = float(input("输入新的替换率 (0.0-1.0): ").strip())
                        success = manager.update_running_agent_replacement_rate(agent_name, new_rate)
                        if success:
                            print(f"✅ {agent_name}的替换率已动态更新为 {new_rate:.1%}")
                        else:
                            print(f"⚠️ {agent_name}动态更新失败，可能Agent未运行或不支持动态更新")
                    except ValueError:
                        print("❌ 无效的替换率")
                elif choice == "6":
                    manager.generate_migration_report()
                elif choice == "7":
                    print("👋 再见！")
                    break
                else:
                    print("❌ 无效选择，请重新输入")

            except KeyboardInterrupt:
                print("\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 操作失败: {e}")

            input("\n按Enter键继续...")

    except KeyboardInterrupt:
        print("\n👋 再见！")
    except Exception as e:
        print(f"❌ 程序异常退出: {e}")
    finally:
        # 退出时保存状态
        try:
            manager._save_migration_state()
            print("💾 迁移状态已保存")
        except Exception as e:
            print(f"⚠️ 保存状态失败: {e}")

if __name__ == "__main__":
    main()
