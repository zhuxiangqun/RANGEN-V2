"""
文档与代码同步更新系统

确保分析文档始终反映最新的系统状态，实现文档与代码的自动同步。
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import inspect
import importlib.util
import ast
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from .cache_system import get_cache_system

logger = logging.getLogger(__name__)


@dataclass
class CodeEntity:
    """代码实体"""
    name: str
    type: str  # class, function, module
    file_path: str
    line_number: int
    content_hash: str
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_modified: datetime = None


@dataclass
class DocumentationEntity:
    """文档实体"""
    title: str
    file_path: str
    content_hash: str
    references: List[str] = field(default_factory=list)  # 引用的代码实体
    last_updated: datetime = None
    version: str = "1.0"


@dataclass
class SyncChange:
    """同步变更"""
    change_type: str  # add, modify, delete
    entity_type: str  # code, documentation
    entity_name: str
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None
    timestamp: datetime = None


@dataclass
class SyncReport:
    """同步报告"""
    scan_time: datetime
    code_entities: Dict[str, CodeEntity]
    doc_entities: Dict[str, DocumentationEntity]
    changes: List[SyncChange]
    conflicts: List[Dict[str, Any]]
    recommendations: List[str]
    sync_status: str  # synced, out_of_sync, conflicts


class CodeAnalyzer:
    """代码分析器"""

    def __init__(self, source_dirs: List[str]):
        self.source_dirs = [Path(d) for d in source_dirs]
        self.ignored_patterns = [
            '__pycache__',
            '.git',
            'node_modules',
            '*.pyc',
            '*.pyo',
            '.pytest_cache'
        ]
        self.cache = get_cache_system()
        self.executor = ThreadPoolExecutor(max_workers=min(os.cpu_count() or 4, 8))  # 限制最大并发数

    async def analyze_codebase(self) -> Dict[str, CodeEntity]:
        """分析整个代码库（支持缓存和并行处理）"""
        entities = {}
        files_to_analyze = []

        # 收集所有需要分析的文件
        for source_dir in self.source_dirs:
            if not source_dir.exists():
                logger.warning(f"源目录不存在: {source_dir}")
                continue

            # 递归扫描Python文件
            for py_file in source_dir.rglob('*.py'):
                if not self._should_ignore_file(py_file):
                    files_to_analyze.append(py_file)

        logger.info(f"发现 {len(files_to_analyze)} 个Python文件待分析")

        # 并行分析文件
        if files_to_analyze:
            # 将文件分组进行批处理
            batch_size = 10
            for i in range(0, len(files_to_analyze), batch_size):
                batch_files = files_to_analyze[i:i + batch_size]
                batch_results = await self._analyze_files_batch(batch_files)

                for file_entities in batch_results:
                    entities.update(file_entities)

        logger.info(f"代码分析完成，共发现 {len(entities)} 个实体")
        return entities

    async def _analyze_files_batch(self, files: List[Path]) -> List[Dict[str, CodeEntity]]:
        """批量分析文件（并行处理）"""
        loop = asyncio.get_event_loop()
        tasks = []

        for file_path in files:
            # 检查缓存
            cache_key = f"code_analysis_{file_path}_{file_path.stat().st_mtime}"
            cached_result = self.cache.get(cache_key)

            if cached_result:
                # 使用缓存结果
                tasks.append(asyncio.create_task(self._return_cached_result(cached_result)))
            else:
                # 需要重新分析
                task = loop.run_in_executor(
                    self.executor,
                    self._analyze_python_file_sync,
                    file_path
                )
                tasks.append(task)

        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for i, result in enumerate(results):
            file_path = files[i]

            if isinstance(result, Exception):
                logger.error(f"分析文件失败 {file_path}: {result}")
                processed_results.append({})
            else:
                processed_results.append(result)

                # 缓存结果
                cache_key = f"code_analysis_{file_path}_{file_path.stat().st_mtime}"
                self.cache.set(cache_key, result, ttl=3600)  # 缓存1小时

        return processed_results

    async def _return_cached_result(self, cached_result: Dict[str, CodeEntity]) -> Dict[str, CodeEntity]:
        """返回缓存结果"""
        return cached_result

    def _analyze_python_file_sync(self, file_path: Path) -> Dict[str, CodeEntity]:
        """同步分析Python文件（用于在线程池中执行）"""
        try:
            return asyncio.run(self._analyze_python_file(file_path))
        except Exception as e:
            logger.error(f"同步分析文件失败 {file_path}: {e}")
            return {}

    def _should_ignore_file(self, file_path: Path) -> bool:
        """检查是否应该忽略文件"""
        file_str = str(file_path)

        for pattern in self.ignored_patterns:
            if pattern.startswith('*'):
                if file_path.name.endswith(pattern[1:]):
                    return True
            elif pattern in file_str:
                return True

        return False

    async def _analyze_python_file(self, file_path: Path) -> Dict[str, CodeEntity]:
        """分析Python文件"""
        entities = {}

        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 解析AST
            tree = ast.parse(content, filename=str(file_path))

            # 提取类和函数
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    entity = self._create_entity_from_class(node, file_path, content)
                    entities[entity.name] = entity

                elif isinstance(node, ast.FunctionDef) and not isinstance(node, ast.AsyncFunctionDef):
                    # 只处理顶级函数，忽略嵌套函数
                    if not any(isinstance(parent, (ast.ClassDef, ast.FunctionDef))
                             for parent in self._get_node_parents(tree, node)):
                        entity = self._create_entity_from_function(node, file_path, content)
                        entities[entity.name] = entity

                elif isinstance(node, ast.AsyncFunctionDef):
                    # 处理异步函数
                    if not any(isinstance(parent, (ast.ClassDef, ast.AsyncFunctionDef))
                             for parent in self._get_node_parents(tree, node)):
                        entity = self._create_entity_from_async_function(node, file_path, content)
                        entities[entity.name] = entity

        except SyntaxError as e:
            logger.error(f"语法错误，无法解析 {file_path}: {e}")
        except Exception as e:
            logger.error(f"分析文件失败 {file_path}: {e}")

        return entities

    def _create_entity_from_class(self, node: ast.ClassDef, file_path: Path, content: str) -> CodeEntity:
        """从AST类节点创建实体"""
        # 获取类定义的源代码
        class_content = self._get_node_source(content, node)

        # 分析继承关系
        base_classes = [self._get_full_name(base) for base in node.bases]

        # 分析方法
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)

        return CodeEntity(
            name=self._get_full_name(node),
            type='class',
            file_path=str(file_path),
            line_number=node.lineno,
            content_hash=hashlib.md5(class_content.encode()).hexdigest(),
            dependencies=base_classes,
            metadata={
                'methods': methods,
                'docstring': self._extract_docstring(node),
                'is_abstract': any(isinstance(base, ast.Name) and base.id == 'ABC' for base in node.bases)
            },
            last_modified=datetime.fromtimestamp(file_path.stat().st_mtime)
        )

    def _create_entity_from_function(self, node: ast.FunctionDef, file_path: Path, content: str) -> CodeEntity:
        """从AST函数节点创建实体"""
        func_content = self._get_node_source(content, node)

        return CodeEntity(
            name=self._get_full_name(node),
            type='function',
            file_path=str(file_path),
            line_number=node.lineno,
            content_hash=hashlib.md5(func_content.encode()).hexdigest(),
            metadata={
                'args': [arg.arg for arg in node.args.args],
                'docstring': self._extract_docstring(node),
                'is_async': False
            },
            last_modified=datetime.fromtimestamp(file_path.stat().st_mtime)
        )

    def _create_entity_from_async_function(self, node: ast.AsyncFunctionDef, file_path: Path, content: str) -> CodeEntity:
        """从AST异步函数节点创建实体"""
        func_content = self._get_node_source(content, node)

        return CodeEntity(
            name=self._get_full_name(node),
            type='function',
            file_path=str(file_path),
            line_number=node.lineno,
            content_hash=hashlib.md5(func_content.encode()).hexdigest(),
            metadata={
                'args': [arg.arg for arg in node.args.args],
                'docstring': self._extract_docstring(node),
                'is_async': True
            },
            last_modified=datetime.fromtimestamp(file_path.stat().st_mtime)
        )

    def _get_full_name(self, node: ast.AST) -> str:
        """获取节点的完整名称"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            return node.name
        elif hasattr(node, 'attr'):
            return f"{self._get_full_name(node.value)}.{node.attr}"
        else:
            return str(node)

    def _get_node_source(self, content: str, node: ast.AST) -> str:
        """获取AST节点的源代码"""
        if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
            lines = content.splitlines()
            return '\n'.join(lines[node.lineno-1:node.end_lineno])
        return ""

    def _extract_docstring(self, node: ast.AST) -> Optional[str]:
        """提取文档字符串"""
        if hasattr(node, 'body') and node.body:
            first_stmt = node.body[0]
            if isinstance(first_stmt, ast.Expr) and isinstance(first_stmt.value, ast.Str):
                return first_stmt.value.s
        return None

    def _get_node_parents(self, tree: ast.AST, target_node: ast.AST) -> List[ast.AST]:
        """获取节点的父节点列表"""
        parents = []

        def visit_node(node, parent_stack):
            if node == target_node:
                parents.extend(parent_stack)
                return

            parent_stack.append(node)
            for child in ast.iter_child_nodes(node):
                visit_node(child, parent_stack)
            parent_stack.pop()

        visit_node(tree, [])
        return parents


class DocumentationAnalyzer:
    """文档分析器"""

    def __init__(self, doc_dirs: List[str], filter_config: Dict[str, Any] = None):
        self.doc_dirs = [Path(d) for d in doc_dirs]
        self.supported_formats = ['.md', '.rst', '.txt']
        self.filter_config = filter_config or {}
        self.filter_mode = self.filter_config.get('doc_filter_mode', 'all')
        self.cache = get_cache_system()
        self.executor = ThreadPoolExecutor(max_workers=min(os.cpu_count() or 4, 6))

    async def analyze_documentation(self) -> Dict[str, DocumentationEntity]:
        """分析文档库（支持缓存和并行处理）"""
        entities = {}
        docs_to_analyze = []

        # 收集需要分析的文档文件
        for doc_dir in self.doc_dirs:
            if not doc_dir.exists():
                continue

            for doc_file in doc_dir.rglob('*'):
                if doc_file.suffix.lower() in self.supported_formats:
                    # 检查是否应该监控此文档
                    if self._should_monitor_document(doc_file):
                        docs_to_analyze.append(doc_file)

        logger.info(f"发现 {len(docs_to_analyze)} 个文档文件待分析")

        # 并行分析文档
        if docs_to_analyze:
            # 将文档分组进行批处理
            batch_size = 8
            for i in range(0, len(docs_to_analyze), batch_size):
                batch_docs = docs_to_analyze[i:i + batch_size]
                batch_results = await self._analyze_docs_batch(batch_docs)

                for doc_entity in batch_results:
                    if doc_entity:
                        entities[doc_entity.title] = doc_entity

        logger.info(f"文档分析完成，共发现 {len(entities)} 个文档实体")
        return entities

    async def _analyze_docs_batch(self, docs: List[Path]) -> List[Optional[DocumentationEntity]]:
        """批量分析文档（并行处理）"""
        loop = asyncio.get_event_loop()
        tasks = []

        for doc_file in docs:
            # 检查缓存
            cache_key = f"doc_analysis_{doc_file}_{doc_file.stat().st_mtime}"
            cached_result = self.cache.get(cache_key)

            if cached_result:
                # 使用缓存结果
                tasks.append(asyncio.create_task(self._return_cached_doc_result(cached_result)))
            else:
                # 需要重新分析
                task = loop.run_in_executor(
                    self.executor,
                    self._analyze_document_file_sync,
                    doc_file
                )
                tasks.append(task)

        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for i, result in enumerate(results):
            doc_file = docs[i]

            if isinstance(result, Exception):
                logger.error(f"分析文档失败 {doc_file}: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)

                # 缓存结果（如果有结果）
                if result:
                    cache_key = f"doc_analysis_{doc_file}_{doc_file.stat().st_mtime}"
                    self.cache.set(cache_key, result, ttl=1800)  # 缓存30分钟

        return processed_results

    async def _return_cached_doc_result(self, cached_result: DocumentationEntity) -> DocumentationEntity:
        """返回缓存的文档结果"""
        return cached_result

    def _analyze_document_file_sync(self, file_path: Path) -> Optional[DocumentationEntity]:
        """同步分析文档文件（用于在线程池中执行）"""
        try:
            # 创建新的事件循环来运行异步函数
            import nest_asyncio
            nest_asyncio.apply()

            async def run_analysis():
                return await self._analyze_document_file(file_path)

            return asyncio.run(run_analysis())
        except Exception as e:
            logger.error(f"同步分析文档失败 {file_path}: {e}")
            return None

    def _should_monitor_document(self, file_path: Path) -> bool:
        """检查是否应该监控此文档"""
        file_str = str(file_path)

        if self.filter_mode == 'all':
            # 监控所有文档
            return True

        elif self.filter_mode == 'selective':
            # 选择性监控
            selective_docs = self.filter_config.get('selective_docs', [])
            return file_str in selective_docs

        elif self.filter_mode == 'categorized':
            # 按类别监控 - 默认监控高优先级和中优先级
            categorized_docs = self.filter_config.get('categorized_docs', {})

            # 检查高优先级
            high_priority = categorized_docs.get('high_priority', [])
            if any(self._matches_pattern(file_str, pattern) for pattern in high_priority):
                return True

            # 检查中优先级
            medium_priority = categorized_docs.get('medium_priority', [])
            if any(self._matches_pattern(file_str, pattern) for pattern in medium_priority):
                return True

            # 检查低优先级 (默认不监控，除非明确指定)
            low_priority = categorized_docs.get('low_priority', [])
            if any(self._matches_pattern(file_str, pattern) for pattern in low_priority):
                return True

            # 默认不监控
            return False

        else:
            # 默认监控所有
            return True

    def _matches_pattern(self, file_path: str, pattern: str) -> bool:
        """检查文件路径是否匹配模式"""
        import fnmatch

        if '*' in pattern:
            # 通配符匹配
            return fnmatch.fnmatch(file_path, pattern)
        else:
            # 精确匹配
            return file_path == pattern

    async def _analyze_document_file(self, file_path: Path) -> Optional[DocumentationEntity]:
        """分析文档文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 计算内容哈希
            content_hash = hashlib.md5(content.encode()).hexdigest()

            # 提取标题
            title = self._extract_title(content, file_path)

            # 提取代码引用
            references = self._extract_code_references(content)

            return DocumentationEntity(
                title=title,
                file_path=str(file_path),
                content_hash=content_hash,
                references=references,
                last_updated=datetime.fromtimestamp(file_path.stat().st_mtime)
            )

        except Exception as e:
            logger.error(f"分析文档文件失败 {file_path}: {e}")
            return None

    def _extract_title(self, content: str, file_path: Path) -> str:
        """提取文档标题"""
        lines = content.splitlines()

        # Markdown标题
        for line in lines[:10]:  # 检查前10行
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()

        # 文件名作为标题
        return file_path.stem.replace('_', ' ').title()

    def _extract_code_references(self, content: str) -> List[str]:
        """提取代码引用"""
        references = []

        # 匹配类名、函数名等
        # 简单的正则匹配，实际可以更复杂
        patterns = [
            r'class\s+(\w+)',
            r'def\s+(\w+)',
            r'`([A-Z]\w+)`',  # 大写开头的可能类名
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            references.extend(matches)

        return list(set(references))  # 去重


class ChangeDetector:
    """变更检测器"""

    def __init__(self):
        self.previous_scan: Optional[SyncReport] = None

    def detect_changes(self, current_code: Dict[str, CodeEntity],
                      current_docs: Dict[str, DocumentationEntity],
                      previous_report: Optional[SyncReport] = None) -> List[SyncChange]:
        """检测变更"""
        changes = []

        if not previous_report:
            # 首次扫描，所有实体都是新增
            for entity in current_code.values():
                changes.append(SyncChange(
                    change_type='add',
                    entity_type='code',
                    entity_name=entity.name,
                    new_hash=entity.content_hash,
                    timestamp=datetime.now()
                ))

            for entity in current_docs.values():
                changes.append(SyncChange(
                    change_type='add',
                    entity_type='documentation',
                    entity_name=entity.title,
                    new_hash=entity.content_hash,
                    timestamp=datetime.now()
                ))

            return changes

        # 检测代码变更
        changes.extend(self._detect_code_changes(current_code, previous_report.code_entities))

        # 检测文档变更
        changes.extend(self._detect_doc_changes(current_docs, previous_report.doc_entities))

        return changes

    def _detect_code_changes(self, current: Dict[str, CodeEntity],
                           previous: Dict[str, CodeEntity]) -> List[SyncChange]:
        """检测代码变更"""
        changes = []

        # 检测新增和修改
        for name, entity in current.items():
            if name not in previous:
                changes.append(SyncChange(
                    change_type='add',
                    entity_type='code',
                    entity_name=name,
                    new_hash=entity.content_hash,
                    timestamp=datetime.now()
                ))
            elif entity.content_hash != previous[name].content_hash:
                changes.append(SyncChange(
                    change_type='modify',
                    entity_type='code',
                    entity_name=name,
                    old_hash=previous[name].content_hash,
                    new_hash=entity.content_hash,
                    timestamp=datetime.now()
                ))

        # 检测删除
        for name in previous.keys():
            if name not in current:
                changes.append(SyncChange(
                    change_type='delete',
                    entity_type='code',
                    entity_name=name,
                    old_hash=previous[name].content_hash,
                    timestamp=datetime.now()
                ))

        return changes

    def _detect_doc_changes(self, current: Dict[str, DocumentationEntity],
                          previous: Dict[str, DocumentationEntity]) -> List[SyncChange]:
        """检测文档变更"""
        changes = []

        # 检测新增和修改
        for title, entity in current.items():
            if title not in previous:
                changes.append(SyncChange(
                    change_type='add',
                    entity_type='documentation',
                    entity_name=title,
                    new_hash=entity.content_hash,
                    timestamp=datetime.now()
                ))
            elif entity.content_hash != previous[title].content_hash:
                changes.append(SyncChange(
                    change_type='modify',
                    entity_type='documentation',
                    entity_name=title,
                    old_hash=previous[title].content_hash,
                    new_hash=entity.content_hash,
                    timestamp=datetime.now()
                ))

        # 检测删除
        for title in previous.keys():
            if title not in current:
                changes.append(SyncChange(
                    change_type='delete',
                    entity_type='documentation',
                    entity_name=title,
                    old_hash=previous[title].content_hash,
                    timestamp=datetime.now()
                ))

        return changes


class DocumentationUpdater:
    """文档更新器"""

    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)

    async def generate_sync_report(self, code_entities: Dict[str, CodeEntity],
                                 doc_entities: Dict[str, DocumentationEntity],
                                 changes: List[SyncChange]) -> SyncReport:
        """生成同步报告"""
        conflicts = await self._detect_conflicts(code_entities, doc_entities, changes)
        recommendations = await self._generate_recommendations(conflicts, changes)
        sync_status = self._determine_sync_status(conflicts, changes)

        return SyncReport(
            scan_time=datetime.now(),
            code_entities=code_entities,
            doc_entities=doc_entities,
            changes=changes,
            conflicts=conflicts,
            recommendations=recommendations,
            sync_status=sync_status
        )

    async def update_outdated_documentation(self, report: SyncReport) -> List[str]:
        """更新过时的文档"""
        updated_files = []

        # 识别需要更新的文档
        docs_to_update = await self._identify_docs_to_update(report)

        for doc_title in docs_to_update:
            try:
                updated = await self._update_single_document(doc_title, report)
                if updated:
                    updated_files.append(doc_title)
            except Exception as e:
                logger.error(f"更新文档失败 {doc_title}: {e}")

        return updated_files

    async def _detect_conflicts(self, code_entities: Dict[str, CodeEntity],
                              doc_entities: Dict[str, DocumentationEntity],
                              changes: List[SyncChange]) -> List[Dict[str, Any]]:
        """检测冲突"""
        conflicts = []

        # 检查文档中引用的代码是否存在
        for doc_entity in doc_entities.values():
            for ref in doc_entity.references:
                if ref not in code_entities:
                    conflicts.append({
                        'type': 'missing_reference',
                        'document': doc_entity.title,
                        'missing_entity': ref,
                        'severity': 'warning'
                    })

        # 检查代码变更是否有对应文档
        code_changes = [c for c in changes if c.entity_type == 'code' and c.change_type in ['add', 'modify']]
        for change in code_changes:
            # 检查是否有文档引用这个代码实体
            referenced_in_docs = any(
                change.entity_name in doc.references
                for doc in doc_entities.values()
            )

            if not referenced_in_docs:
                conflicts.append({
                    'type': 'undocumented_change',
                    'code_entity': change.entity_name,
                    'change_type': change.change_type,
                    'severity': 'info'
                })

        return conflicts

    async def _generate_recommendations(self, conflicts: List[Dict[str, Any]],
                                      changes: List[SyncChange]) -> List[str]:
        """生成推荐建议"""
        recommendations = []

        # 基于冲突生成建议
        missing_refs = [c for c in conflicts if c['type'] == 'missing_reference']
        if missing_refs:
            recommendations.append(
                f"发现 {len(missing_refs)} 个文档引用了不存在的代码实体，建议检查文档准确性"
            )

        undocumented_changes = [c for c in conflicts if c['type'] == 'undocumented_change']
        if undocumented_changes:
            recommendations.append(
                f"发现 {len(undocumented_changes)} 个代码变更缺少文档说明，建议及时更新文档"
            )

        # 基于变更生成建议
        code_additions = [c for c in changes if c.entity_type == 'code' and c.change_type == 'add']
        if code_additions:
            recommendations.append(
                f"新增了 {len(code_additions)} 个代码实体，建议为其添加相应的文档说明"
            )

        code_modifications = [c for c in changes if c.entity_type == 'code' and c.change_type == 'modify']
        if code_modifications:
            recommendations.append(
                f"修改了 {len(code_modifications)} 个代码实体，建议同步更新相关文档"
            )

        return recommendations

    def _determine_sync_status(self, conflicts: List[Dict[str, Any]],
                             changes: List[SyncChange]) -> str:
        """确定同步状态"""
        critical_conflicts = [c for c in conflicts if c.get('severity') == 'error']

        if critical_conflicts:
            return 'conflicts'
        elif changes:
            return 'out_of_sync'
        else:
            return 'synced'

    async def _identify_docs_to_update(self, report: SyncReport) -> List[str]:
        """识别需要更新的文档"""
        docs_to_update = []

        # 检查哪些文档引用了变更的代码
        changed_code_entities = {
            change.entity_name for change in report.changes
            if change.entity_type == 'code'
        }

        for doc_entity in report.doc_entities.values():
            # 如果文档引用了变更的代码实体
            if any(ref in changed_code_entities for ref in doc_entity.references):
                docs_to_update.append(doc_entity.title)

        return docs_to_update

    async def _update_single_document(self, doc_title: str, report: SyncReport) -> bool:
        """更新单个文档"""
        # 这里实现具体的文档更新逻辑
        # 可以根据模板自动生成或更新文档内容

        doc_entity = report.doc_entities.get(doc_title)
        if not doc_entity:
            return False

        # 生成更新后的文档内容
        updated_content = await self._generate_updated_content(doc_title, doc_entity, report)

        # 写入文件
        try:
            with open(doc_entity.file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)

            logger.info(f"文档已更新: {doc_title}")
            return True

        except Exception as e:
            logger.error(f"写入文档失败 {doc_title}: {e}")
            return False

    async def _generate_updated_content(self, title: str, doc_entity: DocumentationEntity,
                                      report: SyncReport) -> str:
        """生成更新后的文档内容"""
        # 加载现有内容
        try:
            with open(doc_entity.file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
        except:
            current_content = ""

        # 这里应该实现智能的文档更新逻辑
        # 暂时只是添加更新标记
        update_marker = f"\n---\n*文档最后同步更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

        if current_content and not current_content.endswith(update_marker.strip()):
            return current_content + update_marker
        else:
            return current_content


class DocumentationSyncSystem:
    """文档同步系统"""

    def __init__(self, source_dirs: List[str] = None, doc_dirs: List[str] = None, filter_config: Dict[str, Any] = None):
        self.source_dirs = source_dirs or ['src']
        self.doc_dirs = doc_dirs or ['docs']
        self.filter_config = filter_config or {}

        self.code_analyzer = CodeAnalyzer(self.source_dirs)
        self.doc_analyzer = DocumentationAnalyzer(self.doc_dirs, self.filter_config)
        self.change_detector = ChangeDetector()
        self.doc_updater = DocumentationUpdater()

        # 状态存储
        self.last_report: Optional[SyncReport] = None
        self.is_running = False

    async def perform_sync_check(self) -> SyncReport:
        """执行同步检查"""
        logger.info("开始执行文档与代码同步检查...")

        try:
            # 分析代码
            code_entities = await self.code_analyzer.analyze_codebase()

            # 分析文档
            doc_entities = await self.doc_analyzer.analyze_documentation()

            # 检测变更
            changes = self.change_detector.detect_changes(code_entities, doc_entities, self.last_report)

            # 生成报告
            report = await self.doc_updater.generate_sync_report(code_entities, doc_entities, changes)

            # 保存报告
            self.last_report = report

            logger.info(f"同步检查完成，状态: {report.sync_status}")
            return report

        except Exception as e:
            logger.error(f"同步检查失败: {e}")
            raise

    async def perform_auto_update(self, report: SyncReport) -> Dict[str, Any]:
        """执行自动更新"""
        logger.info("开始执行自动文档更新...")

        try:
            if report.sync_status == 'synced':
                logger.info("文档与代码已同步，无需更新")
                return {'updated': [], 'status': 'no_action_needed'}

            # 更新文档
            updated_docs = await self.doc_updater.update_outdated_documentation(report)

            result = {
                'updated': updated_docs,
                'total_changes': len(report.changes),
                'conflicts': len(report.conflicts),
                'recommendations': report.recommendations,
                'status': 'completed'
            }

            logger.info(f"自动更新完成，更新了 {len(updated_docs)} 个文档")
            return result

        except Exception as e:
            logger.error(f"自动更新失败: {e}")
            return {'error': str(e), 'status': 'failed'}

    async def start_continuous_monitoring(self, interval_minutes: int = 30):
        """启动持续监控"""
        if self.is_running:
            logger.warning("监控已运行中")
            return

        self.is_running = True
        logger.info(f"启动持续监控，检查间隔: {interval_minutes} 分钟")

        try:
            while self.is_running:
                await self.perform_sync_check()
                await asyncio.sleep(interval_minutes * 60)

        except Exception as e:
            logger.error(f"持续监控异常: {e}")
        finally:
            self.is_running = False

    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        logger.info("停止持续监控")

    async def generate_sync_report_markdown(self, report: SyncReport) -> str:
        """生成同步报告的Markdown格式"""
        lines = []

        lines.append("# 文档与代码同步报告")
        lines.append("")
        lines.append(f"**扫描时间**: {report.scan_time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**同步状态**: {report.sync_status}")
        lines.append("")

        # 统计信息
        lines.append("## 📊 统计信息")
        lines.append("")
        lines.append(f"- 代码实体数量: {len(report.code_entities)}")
        lines.append(f"- 文档实体数量: {len(report.doc_entities)}")
        lines.append(f"- 变更数量: {len(report.changes)}")
        lines.append(f"- 冲突数量: {len(report.conflicts)}")
        lines.append("")

        # 变更详情
        if report.changes:
            lines.append("## 🔄 变更详情")
            lines.append("")

            for change in report.changes[:20]:  # 最多显示20个变更
                icon = {"add": "➕", "modify": "🔄", "delete": "➖"}.get(change.change_type, "❓")
                lines.append(f"- {icon} {change.entity_type}: {change.entity_name}")
            lines.append("")

            if len(report.changes) > 20:
                lines.append(f"*... 还有 {len(report.changes) - 20} 个变更*")
                lines.append("")

        # 冲突详情
        if report.conflicts:
            lines.append("## ⚠️ 冲突详情")
            lines.append("")

            for conflict in report.conflicts[:10]:  # 最多显示10个冲突
                severity_icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(
                    conflict.get('severity', 'info'), "❓")
                lines.append(f"- {severity_icon} {conflict['type']}: {conflict.get('description', '无描述')}")
            lines.append("")

        # 推荐建议
        if report.recommendations:
            lines.append("## 💡 推荐建议")
            lines.append("")

            for rec in report.recommendations:
                lines.append(f"- {rec}")
            lines.append("")

        return "\n".join(lines)

    async def export_report(self, report: SyncReport, output_path: str):
        """导出报告"""
        markdown_content = await self.generate_sync_report_markdown(report)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        logger.info(f"同步报告已导出到: {output_path}")


# 全局单例实例
_sync_system = None

def get_sync_system() -> DocumentationSyncSystem:
    """获取同步系统实例"""
    global _sync_system
    if _sync_system is None:
        _sync_system = DocumentationSyncSystem()
    return _sync_system
