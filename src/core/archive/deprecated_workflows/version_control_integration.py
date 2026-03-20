"""
版本控制集成系统

将文档同步系统与Git等版本控制系统集成，确保文档版本与代码版本保持一致。
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import json
import re
from concurrent.futures import ThreadPoolExecutor

from .documentation_sync_system import SyncReport
from .quality_assurance_system import QualityReport

logger = logging.getLogger(__name__)


@dataclass
class VersionInfo:
    """版本信息"""
    commit_hash: str
    branch: str
    author: str
    timestamp: datetime
    message: str
    affected_files: List[str]


@dataclass
class DocumentationCommit:
    """文档提交"""
    commit_hash: str
    sync_report: SyncReport
    quality_report: Optional[QualityReport]
    commit_message: str
    timestamp: datetime
    triggered_by: str  # manual, automatic, webhook


@dataclass
class VersionSyncStatus:
    """版本同步状态"""
    current_commit: str
    last_sync_commit: Optional[str]
    docs_behind: int  # 文档落后多少个提交
    code_ahead: int   # 代码领先多少个提交
    last_sync_time: Optional[datetime]
    sync_status: str  # synced, docs_behind, code_ahead, diverged


class GitIntegration:
    """Git集成"""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def get_current_version_info(self) -> VersionInfo:
        """获取当前版本信息"""
        try:
            # 获取当前HEAD信息
            commit_hash = await self._run_git_command("git rev-parse HEAD")
            branch = await self._run_git_command("git rev-parse --abbrev-ref HEAD")
            author = await self._run_git_command("git log -1 --format='%an'")
            timestamp_str = await self._run_git_command("git log -1 --format='%ai'")
            message = await self._run_git_command("git log -1 --format='%s'")

            # 解析时间戳
            timestamp = datetime.fromisoformat(timestamp_str.replace(' ', 'T').split('+')[0])

            # 获取变更文件
            affected_files = await self._get_changed_files("HEAD~1", "HEAD")

            return VersionInfo(
                commit_hash=commit_hash,
                branch=branch,
                author=author,
                timestamp=timestamp,
                message=message,
                affected_files=affected_files
            )

        except Exception as e:
            logger.error(f"获取版本信息失败: {e}")
            raise

    async def get_version_history(self, limit: int = 10) -> List[VersionInfo]:
        """获取版本历史"""
        try:
            # 获取最近的提交信息
            log_output = await self._run_git_command(
                f"git log -{limit} --format='%H|%an|%ai|%s'"
            )

            versions = []
            for line in log_output.splitlines():
                if '|' in line:
                    parts = line.split('|', 3)
                    if len(parts) >= 4:
                        commit_hash, author, timestamp_str, message = parts

                        # 解析时间戳
                        timestamp = datetime.fromisoformat(timestamp_str.replace(' ', 'T').split('+')[0])

                        # 获取变更文件（简化版）
                        affected_files = []  # 这里可以进一步获取

                        versions.append(VersionInfo(
                            commit_hash=commit_hash,
                            branch="",  # 暂时为空
                            author=author,
                            timestamp=timestamp,
                            message=message,
                            affected_files=affected_files
                        ))

            return versions

        except Exception as e:
            logger.error(f"获取版本历史失败: {e}")
            return []

    async def check_sync_status(self, last_sync_commit: Optional[str] = None) -> VersionSyncStatus:
        """检查同步状态"""
        try:
            current_commit = await self._run_git_command("git rev-parse HEAD")

            if not last_sync_commit:
                return VersionSyncStatus(
                    current_commit=current_commit,
                    last_sync_commit=None,
                    docs_behind=0,
                    code_ahead=0,
                    last_sync_time=None,
                    sync_status="never_synced"
                )

            # 检查最后同步的提交是否存在
            try:
                await self._run_git_command(f"git cat-file -t {last_sync_commit}")
            except:
                return VersionSyncStatus(
                    current_commit=current_commit,
                    last_sync_commit=last_sync_commit,
                    docs_behind=0,
                    code_ahead=0,
                    last_sync_time=None,
                    sync_status="invalid_sync_commit"
                )

            # 计算文档落后的提交数
            try:
                docs_behind_output = await self._run_git_command(
                    f"git rev-list --count {last_sync_commit}..HEAD"
                )
                docs_behind = int(docs_behind_output.strip())
            except:
                docs_behind = 0

            # 计算代码领先的提交数（通常为0，因为文档同步是响应代码变更）
            code_ahead = 0

            # 确定同步状态
            if docs_behind == 0:
                sync_status = "synced"
            elif docs_behind > 0:
                sync_status = "docs_behind"
            else:
                sync_status = "diverged"

            return VersionSyncStatus(
                current_commit=current_commit,
                last_sync_commit=last_sync_commit,
                docs_behind=docs_behind,
                code_ahead=code_ahead,
                last_sync_time=datetime.now(),  # 这里应该从历史记录中获取
                sync_status=sync_status
            )

        except Exception as e:
            logger.error(f"检查同步状态失败: {e}")
            return VersionSyncStatus(
                current_commit="unknown",
                last_sync_commit=last_sync_commit,
                docs_behind=0,
                code_ahead=0,
                last_sync_time=None,
                sync_status="error"
            )

    async def commit_documentation_changes(self, message: str, files: List[str]) -> str:
        """提交文档变更"""
        try:
            # 添加文件到暂存区
            for file_path in files:
                if Path(file_path).exists():
                    await self._run_git_command(f"git add {file_path}")

            # 检查是否有变更
            status_output = await self._run_git_command("git status --porcelain")
            if not status_output.strip():
                logger.info("没有文档变更需要提交")
                return ""

            # 提交变更
            commit_hash = await self._run_git_command(f"git commit -m '{message}'")

            logger.info(f"文档变更已提交: {commit_hash}")
            return commit_hash

        except Exception as e:
            logger.error(f"提交文档变更失败: {e}")
            return ""

    async def create_sync_tag(self, sync_report: SyncReport, commit_hash: str) -> bool:
        """创建同步标签"""
        try:
            tag_name = f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            tag_message = f"""Documentation Sync Tag

同步时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
代码提交: {commit_hash}
同步状态: {sync_report.sync_status}
变更数量: {len(sync_report.changes)}
冲突数量: {len(sync_report.conflicts)}

自动生成的文档同步标签
"""

            await self._run_git_command(f"git tag -a {tag_name} -m '{tag_message}'")

            logger.info(f"同步标签已创建: {tag_name}")
            return True

        except Exception as e:
            logger.error(f"创建同步标签失败: {e}")
            return False

    async def _run_git_command(self, command: str) -> str:
        """运行Git命令"""
        def run_cmd():
            result = subprocess.run(
                command.split(),
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            result.check_returncode()
            return result.stdout.strip()

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, run_cmd)

    async def _get_changed_files(self, from_commit: str, to_commit: str) -> List[str]:
        """获取变更文件"""
        try:
            diff_output = await self._run_git_command(
                f"git diff --name-only {from_commit} {to_commit}"
            )

            return diff_output.splitlines() if diff_output else []

        except Exception:
            return []


class DocumentationVersionManager:
    """文档版本管理器"""

    def __init__(self):
        self.git_integration = GitIntegration()
        self.version_history: List[DocumentationCommit] = []
        self.sync_state_file = Path("data/sync_state.json")

    async def record_sync_operation(self, sync_report: SyncReport,
                                  quality_report: Optional[QualityReport],
                                  triggered_by: str = "automatic") -> str:
        """记录同步操作"""
        try:
            # 获取当前版本信息
            version_info = await self.git_integration.get_current_version_info()

            # 生成提交消息
            commit_message = self._generate_sync_commit_message(sync_report, quality_report)

            # 记录同步提交
            doc_commit = DocumentationCommit(
                commit_hash=version_info.commit_hash,
                sync_report=sync_report,
                quality_report=quality_report,
                commit_message=commit_message,
                timestamp=datetime.now(),
                triggered_by=triggered_by
            )

            self.version_history.append(doc_commit)

            # 保存同步状态
            await self._save_sync_state(doc_commit)

            logger.info(f"同步操作已记录: {version_info.commit_hash}")
            return version_info.commit_hash

        except Exception as e:
            logger.error(f"记录同步操作失败: {e}")
            return ""

    async def get_sync_status(self) -> VersionSyncStatus:
        """获取同步状态"""
        try:
            # 加载最后同步状态
            last_sync_commit = await self._load_last_sync_commit()

            # 检查当前同步状态
            sync_status = await self.git_integration.check_sync_status(last_sync_commit)

            return sync_status

        except Exception as e:
            logger.error(f"获取同步状态失败: {e}")
            return VersionSyncStatus(
                current_commit="unknown",
                last_sync_commit=None,
                docs_behind=0,
                code_ahead=0,
                last_sync_time=None,
                sync_status="error"
            )

    async def perform_version_synced_commit(self, files: List[str],
                                          sync_report: SyncReport,
                                          quality_report: Optional[QualityReport]) -> bool:
        """执行版本同步提交"""
        try:
            # 生成提交消息
            commit_message = self._generate_sync_commit_message(sync_report, quality_report)

            # 提交文档变更
            commit_hash = await self.git_integration.commit_documentation_changes(commit_message, files)

            if commit_hash:
                # 记录同步操作
                await self.record_sync_operation(sync_report, quality_report, "automatic")

                # 创建同步标签
                await self.git_integration.create_sync_tag(sync_report, commit_hash)

                logger.info(f"版本同步提交完成: {commit_hash}")
                return True
            else:
                logger.warning("没有文档变更需要提交")
                return False

        except Exception as e:
            logger.error(f"版本同步提交失败: {e}")
            return False

    async def get_version_sync_history(self, limit: int = 20) -> List[DocumentationCommit]:
        """获取版本同步历史"""
        try:
            # 从文件加载历史记录
            history = await self._load_sync_history()

            # 返回最近的记录
            return history[-limit:] if limit > 0 else history

        except Exception as e:
            logger.error(f"获取版本同步历史失败: {e}")
            return []

    async def validate_version_consistency(self) -> Dict[str, Any]:
        """验证版本一致性"""
        try:
            validation_results = {
                'version_consistency': True,
                'issues': [],
                'recommendations': []
            }

            # 检查同步历史完整性
            history = await self.get_version_sync_history(limit=0)

            if not history:
                validation_results['issues'].append("没有找到同步历史记录")
                validation_results['recommendations'].append("执行首次文档同步以建立基准")
                return validation_results

            # 检查最近的同步状态
            sync_status = await self.get_sync_status()

            if sync_status.sync_status == "docs_behind":
                validation_results['issues'].append(
                    f"文档落后 {sync_status.docs_behind} 个提交"
                )
                validation_results['recommendations'].append("执行文档同步以跟上代码变更")

            # 检查同步频率
            recent_syncs = [commit for commit in history
                          if (datetime.now() - commit.timestamp).days <= 7]

            if len(recent_syncs) < 3:  # 一周内至少3次同步
                validation_results['issues'].append("同步频率过低")
                validation_results['recommendations'].append("增加自动同步频率或手动同步次数")

            # 检查质量趋势
            quality_trends = await self._analyze_quality_trends(history)

            if quality_trends.get('trend') == 'declining':
                validation_results['issues'].append("文档质量呈下降趋势")
                validation_results['recommendations'].append("检查同步过程并改进文档更新逻辑")

            return validation_results

        except Exception as e:
            logger.error(f"验证版本一致性失败: {e}")
            return {
                'version_consistency': False,
                'issues': [f"验证过程出错: {e}"],
                'recommendations': ["检查系统配置和日志"]
            }

    def _generate_sync_commit_message(self, sync_report: SyncReport,
                                    quality_report: Optional[QualityReport]) -> str:
        """生成同步提交消息"""
        lines = []

        lines.append("docs: sync documentation with code changes")
        lines.append("")
        lines.append(f"- Sync status: {sync_report.sync_status}")
        lines.append(f"- Changes detected: {len(sync_report.changes)}")
        lines.append(f"- Conflicts found: {len(sync_report.conflicts)}")

        if quality_report:
            lines.append(f"- Quality score: {quality_report.overall_score:.1f}/100")
            lines.append(f"- Issues found: {quality_report.total_issues}")

        if sync_report.recommendations:
            lines.append("")
            lines.append("Recommendations:")
            for rec in sync_report.recommendations[:3]:  # 最多显示3条
                lines.append(f"- {rec}")

        lines.append("")
        lines.append("Auto-generated by documentation sync system")

        return "\n".join(lines)

    async def _save_sync_state(self, doc_commit: DocumentationCommit):
        """保存同步状态"""
        try:
            self.sync_state_file.parent.mkdir(parents=True, exist_ok=True)

            state_data = {
                'last_sync_commit': doc_commit.commit_hash,
                'last_sync_time': doc_commit.timestamp.isoformat(),
                'sync_count': len(self.version_history),
                'last_quality_score': (
                    doc_commit.quality_report.overall_score
                    if doc_commit.quality_report else None
                )
            }

            with open(self.sync_state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"保存同步状态失败: {e}")

    async def _load_last_sync_commit(self) -> Optional[str]:
        """加载最后同步的提交"""
        try:
            if not self.sync_state_file.exists():
                return None

            with open(self.sync_state_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)

            return state_data.get('last_sync_commit')

        except Exception as e:
            logger.error(f"加载最后同步提交失败: {e}")
            return None

    async def _load_sync_history(self) -> List[DocumentationCommit]:
        """加载同步历史"""
        try:
            history_file = Path("data/sync_history.jsonl")

            if not history_file.exists():
                return []

            history = []
            with open(history_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        commit_data = json.loads(line)
                        # 这里需要将JSON数据转换为DocumentationCommit对象
                        # 暂时简化处理
                        history.append(commit_data)

            return history

        except Exception as e:
            logger.error(f"加载同步历史失败: {e}")
            return []

    async def _analyze_quality_trends(self, history: List[DocumentationCommit]) -> Dict[str, Any]:
        """分析质量趋势"""
        try:
            quality_scores = [
                commit.get('quality_report', {}).get('overall_score', 0)
                for commit in history
                if commit.get('quality_report')
            ]

            if len(quality_scores) < 2:
                return {'trend': 'insufficient_data'}

            # 计算趋势
            recent_avg = sum(quality_scores[-3:]) / min(3, len(quality_scores))
            earlier_avg = sum(quality_scores[:-3]) / max(1, len(quality_scores) - 3)

            if recent_avg > earlier_avg + 5:
                trend = 'improving'
            elif recent_avg < earlier_avg - 5:
                trend = 'declining'
            else:
                trend = 'stable'

            return {
                'trend': trend,
                'recent_avg': recent_avg,
                'earlier_avg': earlier_avg,
                'data_points': len(quality_scores)
            }

        except Exception as e:
            logger.error(f"分析质量趋势失败: {e}")
            return {'trend': 'error', 'error': str(e)}


class VersionControlIntegration:
    """版本控制集成系统"""

    def __init__(self):
        self.git_integration = GitIntegration()
        self.version_manager = DocumentationVersionManager()
        self.is_enabled = True

    async def initialize_version_control(self):
        """初始化版本控制集成"""
        try:
            # 检查Git仓库状态
            await self.git_integration.get_current_version_info()

            # 初始化数据目录
            Path("data").mkdir(exist_ok=True)

            logger.info("版本控制集成初始化完成")
            return True

        except Exception as e:
            logger.error(f"版本控制集成初始化失败: {e}")
            self.is_enabled = False
            return False

    async def perform_version_controlled_sync(self, sync_report: SyncReport,
                                            quality_report: Optional[QualityReport] = None) -> Dict[str, Any]:
        """执行版本控制的同步"""
        if not self.is_enabled:
            return {'status': 'disabled', 'message': '版本控制集成未启用'}

        try:
            logger.info("开始版本控制同步")

            # 检查同步状态
            sync_status = await self.version_manager.get_sync_status()

            result = {
                'status': 'completed',
                'sync_status': sync_status.sync_status,
                'docs_behind': sync_status.docs_behind,
                'actions_taken': []
            }

            # 如果文档落后，执行同步
            if sync_status.sync_status in ['docs_behind', 'never_synced']:
                # 这里应该确定需要更新的文件列表
                # 暂时使用模拟的文件列表
                files_to_commit = ["docs/"]  # 更新整个docs目录

                # 执行版本同步提交
                commit_success = await self.version_manager.perform_version_synced_commit(
                    files_to_commit, sync_report, quality_report
                )

                if commit_success:
                    result['actions_taken'].append('committed_changes')
                    result['commit_created'] = True
                else:
                    result['actions_taken'].append('no_changes_to_commit')

            # 记录同步操作
            sync_commit = await self.version_manager.record_sync_operation(
                sync_report, quality_report, "version_controlled"
            )

            if sync_commit:
                result['actions_taken'].append('sync_recorded')
                result['sync_commit'] = sync_commit

            logger.info(f"版本控制同步完成: {result['status']}")
            return result

        except Exception as e:
            logger.error(f"版本控制同步失败: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'actions_taken': []
            }

    async def get_version_control_status(self) -> Dict[str, Any]:
        """获取版本控制状态"""
        try:
            if not self.is_enabled:
                return {'enabled': False, 'status': 'disabled'}

            # 获取同步状态
            sync_status = await self.version_manager.get_sync_status()

            # 获取版本信息
            version_info = await self.git_integration.get_current_version_info()

            # 获取一致性验证结果
            consistency = await self.version_manager.validate_version_consistency()

            return {
                'enabled': True,
                'current_commit': version_info.commit_hash,
                'branch': version_info.branch,
                'sync_status': sync_status.sync_status,
                'docs_behind': sync_status.docs_behind,
                'last_sync_time': sync_status.last_sync_time.isoformat() if sync_status.last_sync_time else None,
                'version_consistency': consistency
            }

        except Exception as e:
            logger.error(f"获取版本控制状态失败: {e}")
            return {
                'enabled': self.is_enabled,
                'status': 'error',
                'error': str(e)
            }

    async def generate_version_report_markdown(self) -> str:
        """生成版本报告的Markdown格式"""
        try:
            status = await self.get_version_control_status()
            history = await self.version_manager.get_version_sync_history(limit=10)

            lines = []

            lines.append("# 文档版本控制报告")
            lines.append("")
            lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"**版本控制集成**: {'启用' if status.get('enabled', False) else '禁用'}")
            lines.append("")

            if status.get('enabled'):
                lines.append("## 📊 当前状态")
                lines.append("")
                lines.append(f"- 当前提交: {status.get('current_commit', 'unknown')[:8]}")
                lines.append(f"- 分支: {status.get('branch', 'unknown')}")
                lines.append(f"- 同步状态: {status.get('sync_status', 'unknown')}")
                lines.append(f"- 文档落后: {status.get('docs_behind', 0)} 个提交")

                last_sync = status.get('last_sync_time')
                if last_sync:
                    lines.append(f"- 最后同步: {last_sync}")
                lines.append("")

                # 一致性检查
                consistency = status.get('version_consistency', {})
                if consistency:
                    lines.append("## 🔍 一致性检查")
                    lines.append("")

                    if consistency.get('version_consistency', False):
                        lines.append("✅ 版本一致性正常")
                    else:
                        lines.append("❌ 发现一致性问题")

                    if consistency.get('issues'):
                        lines.append("")
                        lines.append("问题列表:")
                        for issue in consistency['issues']:
                            lines.append(f"- {issue}")

                    if consistency.get('recommendations'):
                        lines.append("")
                        lines.append("建议:")
                        for rec in consistency['recommendations']:
                            lines.append(f"- {rec}")

                    lines.append("")

            # 同步历史
            if history:
                lines.append("## 📚 同步历史")
                lines.append("")

                for i, commit in enumerate(history[-5:], 1):  # 显示最近5次
                    lines.append(f"### 同步 #{len(history) - 5 + i}")
                    lines.append("")
                    lines.append(f"- 提交: {commit.get('commit_hash', 'unknown')[:8]}")
                    lines.append(f"- 时间: {commit.get('timestamp', 'unknown')}")
                    lines.append(f"- 触发方式: {commit.get('triggered_by', 'unknown')}")
                    lines.append(f"- 变更数量: {len(commit.get('sync_report', {}).get('changes', []))}")
                    lines.append("")

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"生成版本报告失败: {e}")
            return f"# 版本报告生成失败\n\n错误: {e}"

    async def export_version_report(self, output_path: str):
        """导出版本报告"""
        markdown_content = await self.generate_version_report_markdown()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        logger.info(f"版本报告已导出到: {output_path}")


# 全局单例实例
_version_control = None

def get_version_control_integration() -> VersionControlIntegration:
    """获取版本控制集成实例"""
    global _version_control
    if _version_control is None:
        _version_control = VersionControlIntegration()
    return _version_control
