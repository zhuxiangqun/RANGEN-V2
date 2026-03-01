"""
代码变更检测系统

检测代码变更并触发文档同步更新，确保文档与代码始终保持同步。
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import subprocess
import json
import time
from concurrent.futures import ThreadPoolExecutor

from .documentation_sync_system import CodeEntity, DocumentationSyncSystem, get_sync_system

logger = logging.getLogger(__name__)


@dataclass
class FileChange:
    """文件变更"""
    file_path: str
    change_type: str  # modified, added, deleted, renamed
    old_content_hash: Optional[str] = None
    new_content_hash: Optional[str] = None
    timestamp: datetime = None
    affected_entities: List[str] = field(default_factory=list)


@dataclass
class ChangeBatch:
    """变更批次"""
    batch_id: str
    changes: List[FileChange]
    start_time: datetime
    end_time: Optional[datetime] = None
    processed: bool = False


@dataclass
class DetectionConfig:
    """检测配置"""
    watch_dirs: List[str]
    ignored_patterns: List[str]
    detection_interval: int = 30  # 秒
    batch_timeout: int = 300  # 秒，批处理超时时间
    enable_git_detection: bool = True
    enable_filesystem_watch: bool = True


class GitChangeDetector:
    """Git变更检测器"""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.last_commit_hash: Optional[str] = None

    async def detect_git_changes(self) -> List[FileChange]:
        """检测Git变更"""
        try:
            # 获取当前HEAD
            current_hash = await self._run_git_command("git rev-parse HEAD")

            if self.last_commit_hash is None:
                # 首次运行，记录当前状态
                self.last_commit_hash = current_hash
                return []

            if current_hash == self.last_commit_hash:
                # 没有新提交
                return []

            # 获取变更文件
            changed_files = await self._get_changed_files(self.last_commit_hash, current_hash)

            # 转换为FileChange对象
            changes = []
            for file_info in changed_files:
                change = FileChange(
                    file_path=file_info['path'],
                    change_type=file_info['status'],
                    timestamp=datetime.now()
                )

                # 计算内容哈希（如果文件存在）
                if change.change_type != 'deleted' and Path(file_info['path']).exists():
                    change.new_content_hash = await self._calculate_file_hash(file_info['path'])

                changes.append(change)

            # 更新最后提交哈希
            self.last_commit_hash = current_hash

            logger.info(f"Git检测到 {len(changes)} 个文件变更")
            return changes

        except Exception as e:
            logger.error(f"Git变更检测失败: {e}")
            return []

    async def _run_git_command(self, command: str) -> str:
        """运行Git命令"""
        def run_cmd():
            result = subprocess.run(
                command.split(),
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            result.check_returncode()
            return result.stdout.strip()

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, run_cmd)

    async def _get_changed_files(self, old_hash: str, new_hash: str) -> List[Dict[str, Any]]:
        """获取变更文件列表"""
        try:
            # 使用git diff获取变更
            diff_output = await self._run_git_command(f"git diff --name-status {old_hash} {new_hash}")

            files = []
            for line in diff_output.splitlines():
                if line.strip():
                    parts = line.split('\t', 1)
                    if len(parts) >= 2:
                        status, path = parts[0], parts[1]
                        files.append({
                            'path': path,
                            'status': self._normalize_git_status(status)
                        })

            return files

        except Exception as e:
            logger.error(f"获取变更文件失败: {e}")
            return []

    def _normalize_git_status(self, git_status: str) -> str:
        """标准化Git状态"""
        status_map = {
            'A': 'added',
            'M': 'modified',
            'D': 'deleted',
            'R': 'renamed',
            'C': 'copied',
            'U': 'unmerged',
            'T': 'type_changed'
        }
        return status_map.get(git_status, 'modified')

    async def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            return hashlib.md5(content).hexdigest()
        except Exception:
            return ""


class FilesystemWatcher:
    """文件系统监听器"""

    def __init__(self, watch_dirs: List[str], ignored_patterns: List[str] = None):
        self.watch_dirs = [Path(d) for d in watch_dirs]
        self.ignored_patterns = ignored_patterns or []
        self.file_hashes: Dict[str, str] = {}
        self.last_scan_time = datetime.now()

    async def scan_for_changes(self) -> List[FileChange]:
        """扫描文件变更"""
        changes = []
        current_hashes = {}

        for watch_dir in self.watch_dirs:
            if not watch_dir.exists():
                continue

            # 递归扫描目录
            for file_path in watch_dir.rglob('*'):
                if not file_path.is_file():
                    continue

                file_str = str(file_path)

                # 检查是否应该忽略
                if self._should_ignore_file(file_str):
                    continue

                try:
                    # 计算文件哈希
                    file_hash = await self._calculate_file_hash(file_path)
                    current_hashes[file_str] = file_hash

                    # 检测变更
                    if file_str not in self.file_hashes:
                        # 新增文件
                        changes.append(FileChange(
                            file_path=file_str,
                            change_type='added',
                            new_content_hash=file_hash,
                            timestamp=datetime.now()
                        ))
                    elif self.file_hashes[file_str] != file_hash:
                        # 修改文件
                        changes.append(FileChange(
                            file_path=file_str,
                            change_type='modified',
                            old_content_hash=self.file_hashes[file_str],
                            new_content_hash=file_hash,
                            timestamp=datetime.now()
                        ))

                except Exception as e:
                    logger.error(f"处理文件失败 {file_str}: {e}")

        # 检测删除的文件
        for old_file in self.file_hashes.keys():
            if old_file not in current_hashes:
                changes.append(FileChange(
                    file_path=old_file,
                    change_type='deleted',
                    old_content_hash=self.file_hashes[old_file],
                    timestamp=datetime.now()
                ))

        # 更新哈希缓存
        self.file_hashes = current_hashes
        self.last_scan_time = datetime.now()

        logger.info(f"文件系统扫描完成，检测到 {len(changes)} 个变更")
        return changes

    def _should_ignore_file(self, file_path: str) -> bool:
        """检查是否应该忽略文件"""
        # 检查忽略模式
        for pattern in self.ignored_patterns:
            if pattern in file_path:
                return True

        # 检查文件扩展名
        ignored_extensions = ['.pyc', '.pyo', '.tmp', '.bak', '.log']
        for ext in ignored_extensions:
            if file_path.endswith(ext):
                return True

        # 检查目录
        ignored_dirs = ['__pycache__', '.git', '.pytest_cache', 'node_modules']
        for ignored_dir in ignored_dirs:
            if ignored_dir in file_path:
                return True

        return False

    async def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            return hashlib.md5(content).hexdigest()
        except Exception:
            return ""


class ChangeProcessor:
    """变更处理器"""

    def __init__(self, sync_system: DocumentationSyncSystem):
        self.sync_system = sync_system
        self.entity_cache: Dict[str, CodeEntity] = {}

    async def process_changes(self, file_changes: List[FileChange]) -> Dict[str, Any]:
        """处理变更"""
        try:
            logger.info(f"开始处理 {len(file_changes)} 个文件变更")

            # 过滤相关变更
            relevant_changes = self._filter_relevant_changes(file_changes)

            if not relevant_changes:
                logger.info("没有相关的代码或文档变更")
                return {'processed': 0, 'triggered_sync': False}

            # 分析受影响的实体
            affected_entities = await self._analyze_affected_entities(relevant_changes)

            # 决定是否触发同步
            should_sync = self._should_trigger_sync(affected_entities)

            if should_sync:
                logger.info("检测到重要变更，触发文档同步")

                # 执行同步检查
                report = await self.sync_system.perform_sync_check()

                # 执行自动更新
                update_result = await self.sync_system.perform_auto_update(report)

                return {
                    'processed': len(relevant_changes),
                    'affected_entities': len(affected_entities),
                    'triggered_sync': True,
                    'sync_report': report,
                    'update_result': update_result
                }
            else:
                logger.info("变更不重要，跳过同步")
                return {
                    'processed': len(relevant_changes),
                    'affected_entities': len(affected_entities),
                    'triggered_sync': False
                }

        except Exception as e:
            logger.error(f"处理变更失败: {e}")
            return {'error': str(e), 'processed': 0, 'triggered_sync': False}

    def _filter_relevant_changes(self, changes: List[FileChange]) -> List[FileChange]:
        """过滤相关变更"""
        relevant_changes = []

        for change in changes:
            file_path = Path(change.file_path)

            # 检查是否是源代码文件
            if any(file_path.match(f"*{ext}") for ext in ['.py', '.md', '.rst', '.txt']):
                relevant_changes.append(change)

            # 检查是否是配置或文档文件
            elif any(part in str(file_path) for part in ['docs/', 'config/', 'README']):
                relevant_changes.append(change)

        return relevant_changes

    async def _analyze_affected_entities(self, changes: List[FileChange]) -> Set[str]:
        """分析受影响的实体"""
        affected_entities = set()

        for change in changes:
            file_path = change.file_path

            # 如果是Python文件，分析其中的实体
            if file_path.endswith('.py'):
                entities = await self._analyze_python_file_entities(file_path)
                affected_entities.update(entities)

            # 如果是文档文件，分析引用的实体
            elif any(file_path.endswith(ext) for ext in ['.md', '.rst', '.txt']):
                entities = await self._analyze_document_entities(file_path)
                affected_entities.update(entities)

        return affected_entities

    async def _analyze_python_file_entities(self, file_path: str) -> Set[str]:
        """分析Python文件中的实体"""
        entities = set()

        try:
            # 这里可以重用CodeAnalyzer的逻辑
            # 暂时使用简单的正则匹配
            import re

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 匹配类定义
            class_matches = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
            entities.update(class_matches)

            # 匹配函数定义
            func_matches = re.findall(r'^def\s+(\w+)', content, re.MULTILINE)
            entities.update(func_matches)

            # 匹配异步函数定义
            async_matches = re.findall(r'^async\s+def\s+(\w+)', content, re.MULTILINE)
            entities.update(async_matches)

        except Exception as e:
            logger.error(f"分析Python文件实体失败 {file_path}: {e}")

        return entities

    async def _analyze_document_entities(self, file_path: str) -> Set[str]:
        """分析文档文件中的实体引用"""
        entities = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 使用简单的正则匹配查找代码引用
            import re

            # 匹配反引号包围的代码引用
            code_refs = re.findall(r'`([^`]+)`', content)
            entities.update(code_refs)

            # 匹配类名模式（大写字母开头的单词）
            class_refs = re.findall(r'\b[A-Z][a-zA-Z0-9_]*\b', content)
            entities.update(class_refs)

        except Exception as e:
            logger.error(f"分析文档实体失败 {file_path}: {e}")

        return entities

    def _should_trigger_sync(self, affected_entities: Set[str]) -> bool:
        """判断是否应该触发同步"""
        if not affected_entities:
            return False

        # 检查是否有重要的实体变更
        important_entities = {
            'ChiefAgent', 'BaseAgent', 'StrategicChiefAgent', 'TacticalOptimizer',
            'ExecutionCoordinator', 'CapabilityAssessmentMatrix', 'DynamicCollaborationCoordinator'
        }

        # 如果有重要实体变更，一定要同步
        if affected_entities & important_entities:
            return True

        # 如果变更数量超过阈值，也要同步
        if len(affected_entities) > 10:
            return True

        # 检查是否有新增的实体
        # 这里可以添加更复杂的逻辑

        return True  # 默认触发同步


class ChangeDetectionSystem:
    """变更检测系统"""

    def __init__(self, config: DetectionConfig = None):
        self.config = config or DetectionConfig(
            watch_dirs=['src', 'docs'],
            ignored_patterns=['__pycache__', '.git', '*.pyc']
        )

        self.git_detector = GitChangeDetector()
        self.filesystem_watcher = FilesystemWatcher(
            self.config.watch_dirs,
            self.config.ignored_patterns
        )
        self.change_processor = ChangeProcessor(get_sync_system())

        self.is_running = False
        self.pending_batches: Dict[str, ChangeBatch] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def start_detection(self):
        """启动变更检测"""
        if self.is_running:
            logger.warning("检测系统已在运行")
            return

        self.is_running = True
        logger.info("启动变更检测系统")

        try:
            while self.is_running:
                await self._perform_detection_cycle()
                await asyncio.sleep(self.config.detection_interval)

        except Exception as e:
            logger.error(f"检测系统异常: {e}")
        finally:
            self.is_running = False

    def stop_detection(self):
        """停止变更检测"""
        self.is_running = False
        self.executor.shutdown(wait=False)
        logger.info("停止变更检测系统")

    async def _perform_detection_cycle(self):
        """执行检测周期"""
        try:
            changes = []

            # Git变更检测
            if self.config.enable_git_detection:
                git_changes = await self.git_detector.detect_git_changes()
                changes.extend(git_changes)

            # 文件系统变更检测
            if self.config.enable_filesystem_watch:
                fs_changes = await self.filesystem_watcher.scan_for_changes()
                changes.extend(fs_changes)

            # 去重处理
            unique_changes = self._deduplicate_changes(changes)

            if unique_changes:
                logger.info(f"检测到 {len(unique_changes)} 个变更")

                # 处理变更
                result = await self.change_processor.process_changes(unique_changes)

                # 记录处理结果
                await self._log_detection_result(unique_changes, result)

        except Exception as e:
            logger.error(f"检测周期执行失败: {e}")

    def _deduplicate_changes(self, changes: List[FileChange]) -> List[FileChange]:
        """去重变更"""
        seen = set()
        unique_changes = []

        for change in changes:
            key = (change.file_path, change.change_type)
            if key not in seen:
                seen.add(key)
                unique_changes.append(change)

        return unique_changes

    async def _log_detection_result(self, changes: List[FileChange], result: Dict[str, Any]):
        """记录检测结果"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'changes_count': len(changes),
                'processed_count': result.get('processed', 0),
                'triggered_sync': result.get('triggered_sync', False),
                'changes': [
                    {
                        'file': c.file_path,
                        'type': c.change_type,
                        'timestamp': c.timestamp.isoformat() if c.timestamp else None
                    } for c in changes[:5]  # 只记录前5个
                ]
            }

            # 写入日志文件
            log_file = Path('logs/change_detection.log')
            log_file.parent.mkdir(exist_ok=True)

            with open(log_file, 'a', encoding='utf-8') as f:
                json.dump(log_entry, f, ensure_ascii=False)
                f.write('\n')

        except Exception as e:
            logger.error(f"记录检测结果失败: {e}")

    async def force_sync_check(self) -> Dict[str, Any]:
        """强制执行同步检查"""
        logger.info("执行强制同步检查")

        try:
            # 手动触发完整扫描
            fs_changes = await self.filesystem_watcher.scan_for_changes()

            # 处理变更
            result = await self.change_processor.process_changes(fs_changes)

            return {
                'status': 'completed',
                'changes_found': len(fs_changes),
                'sync_triggered': result.get('triggered_sync', False),
                'details': result
            }

        except Exception as e:
            logger.error(f"强制同步检查失败: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def get_detection_stats(self) -> Dict[str, Any]:
        """获取检测统计信息"""
        return {
            'is_running': self.is_running,
            'config': {
                'watch_dirs': self.config.watch_dirs,
                'detection_interval': self.config.detection_interval,
                'git_detection_enabled': self.config.enable_git_detection,
                'filesystem_watch_enabled': self.config.enable_filesystem_watch
            },
            'filesystem_watcher': {
                'files_tracked': len(self.filesystem_watcher.file_hashes),
                'last_scan': self.filesystem_watcher.last_scan_time.isoformat()
            },
            'pending_batches': len(self.pending_batches)
        }


# 全局单例实例
_detection_system = None

def get_change_detection_system() -> ChangeDetectionSystem:
    """获取变更检测系统实例"""
    global _detection_system
    if _detection_system is None:
        _detection_system = ChangeDetectionSystem()
    return _detection_system
