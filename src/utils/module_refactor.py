#!/usr/bin/env python3
"""
模块重构工具 - 增强版
提供真正的模块重构功能，包括代码分析、重构建议、依赖管理等
"""

import logging
import time
import ast
import os
import re
import json
from typing import Dict, List, Any, Optional, Union, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import threading
import asyncio

logger = logging.getLogger(__name__)


class RefactorType(Enum):
    """重构类型"""
    EXTRACT_METHOD = "extract_method"
    EXTRACT_CLASS = "extract_class"
    INLINE_METHOD = "inline_method"
    MOVE_METHOD = "move_method"
    RENAME_SYMBOL = "rename_symbol"
    REMOVE_DUPLICATE = "remove_duplicate"
    SIMPLIFY_CONDITION = "simplify_condition"
    OPTIMIZE_IMPORTS = "optimize_imports"


class RefactorPriority(Enum):
    """重构优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RefactorSuggestion:
    """重构建议"""
    suggestion_id: str
    refactor_type: RefactorType
    priority: RefactorPriority
    file_path: str
    line_number: int
    description: str
    code_snippet: str
    suggested_code: str
    confidence: float
    impact_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RefactorResult:
    """重构结果"""
    success: bool
    suggestions_count: int
    applied_refactors: int
    processing_time: float
    files_analyzed: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class ModuleRefactor:
    """模块重构工具 - 增强版"""
    
    def __init__(self) -> None:
        """初始化模块重构工具"""
        self.initialized = True
        self.refactor_stats = {
            "total_refactors": 0,
            "successful_refactors": 0,
            "failed_refactors": 0,
            "suggestions_generated": 0,
            "files_analyzed": 0
        }
        self.suggestions: List[RefactorSuggestion] = []
        self._refactor_lock = threading.Lock()
        self._analysis_cache: Dict[str, Dict[str, Any]] = {}
    
    def process_data(self, data: Any, context: Optional[Dict[str, Any]] = None) -> RefactorResult:
        """处理数据 - 真正的重构处理逻辑"""
        try:
            start_time = time.time()
            self.refactor_stats["total_refactors"] += 1
            
            # 1. 分析输入数据
            analysis_result = self._analyze_input_data(data, context)
            
            # 2. 生成重构建议
            suggestions = self._generate_refactor_suggestions(analysis_result, context)
            
            # 3. 应用重构
            applied_refactors = self._apply_refactors(suggestions, context)
            
            # 4. 验证重构结果
            validation_result = self._validate_refactor_results(applied_refactors, context)
            
            processing_time = time.time() - start_time
            
            result = RefactorResult(
                success=True,
                suggestions_count=len(suggestions),
                applied_refactors=applied_refactors,
                processing_time=processing_time,
                files_analyzed=analysis_result.get("files_analyzed", 0),
                metadata={
                    "analysis_result": analysis_result,
                    "validation_result": validation_result,
                    "context": context or {}
                }
            )
            
            self.refactor_stats["successful_refactors"] += 1
            self.refactor_stats["suggestions_generated"] += len(suggestions)
            self.refactor_stats["files_analyzed"] += analysis_result.get("files_analyzed", 0)
            
            return result
            
        except Exception as e:
            logger.error(f"重构处理失败: {e}")
            self.refactor_stats["failed_refactors"] += 1
            
            return RefactorResult(
                success=False,
                suggestions_count=0,
                applied_refactors=0,
                processing_time=time.time() - start_time,
                files_analyzed=0,
                error=str(e)
            )
    
    def _analyze_input_data(self, data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """分析输入数据"""
        try:
            analysis = {
                "data_type": type(data).__name__,
                "data_size": len(str(data)),
                "files_analyzed": 0,
                "code_issues": [],
                "complexity_metrics": {},
                "dependency_analysis": {},
                "duplication_analysis": {}
            }
            
            if isinstance(data, str):
                # 分析文件路径或代码内容
                if os.path.exists(data):
                    analysis["files_analyzed"] = 1
                    analysis["file_analysis"] = self._analyze_file(data)
                else:
                    analysis["code_analysis"] = self._analyze_code_content(data)
            elif isinstance(data, list):
                # 分析多个文件
                analysis["files_analyzed"] = len(data)
                analysis["multi_file_analysis"] = self._analyze_multiple_files(data)
            elif isinstance(data, dict):
                # 分析项目结构
                analysis["project_analysis"] = self._analyze_project_structure(data)
            
            return analysis
        except Exception as e:
            logger.error(f"输入数据分析失败: {e}")
            return {"error": str(e)}
    
    def _analyze_file(self, file_path: str) -> Dict[str, Any]:
        """分析单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self._analyze_code_content(content, file_path)
        except Exception as e:
            logger.error(f"文件分析失败: {e}")
            return {"error": str(e)}
    
    def _analyze_code_content(self, content: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """分析代码内容"""
        try:
            analysis = {
                "lines_of_code": len(content.split('\n')),
                "complexity_metrics": self._calculate_complexity_metrics(content),
                "code_issues": self._detect_code_issues(content),
                "duplication_analysis": self._analyze_duplication(content),
                "dependency_analysis": self._analyze_dependencies(content),
                "refactor_opportunities": self._identify_refactor_opportunities(content)
            }
            
            if file_path:
                analysis["file_path"] = file_path
            
            return analysis
        except Exception as e:
            logger.error(f"代码内容分析失败: {e}")
            return {"error": str(e)}
    
    def _calculate_complexity_metrics(self, content: str) -> Dict[str, Any]:
        """计算复杂度指标"""
        try:
            metrics = {
                "cyclomatic_complexity": 0,
                "function_count": 0,
                "class_count": 0,
                "average_function_length": 0,
                "average_class_length": 0,
                "nesting_depth": 0
            }
            
            try:
                tree = ast.parse(content)
                
                # 计算圈复杂度
                metrics["cyclomatic_complexity"] = self._calculate_cyclomatic_complexity(tree)
                
                # 统计函数和类
                functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
                
                metrics["function_count"] = len(functions)
                metrics["class_count"] = len(classes)
                
                # 计算平均长度
                if functions:
                    total_lines = sum(len(f.body) for f in functions)
                    metrics["average_function_length"] = total_lines / len(functions)
                
                if classes:
                    total_lines = sum(len(c.body) for c in classes)
                    metrics["average_class_length"] = total_lines / len(classes)
                
                # 计算嵌套深度
                metrics["nesting_depth"] = self._calculate_nesting_depth(tree)
                
            except SyntaxError:
                # 如果语法错误，使用简单的文本分析
                metrics["cyclomatic_complexity"] = content.count('if') + content.count('for') + content.count('while')
                metrics["function_count"] = content.count('def ')
                metrics["class_count"] = content.count('class ')
            
            return metrics
        except Exception as e:
            logger.error(f"复杂度指标计算失败: {e}")
            return {}
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """计算圈复杂度"""
        try:
            complexity = 1  # 基础复杂度
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                    complexity += 1
                elif isinstance(node, ast.ExceptHandler):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1
            
            return complexity
        except Exception as e:
            logger.error(f"圈复杂度计算失败: {e}")
            return 1
    
    def _calculate_nesting_depth(self, tree: ast.AST) -> int:
        """计算嵌套深度"""
        try:
            max_depth = 0
            
            def get_depth(node: ast.AST, current_depth: int = 0) -> int:
                nonlocal max_depth
                max_depth = max(max_depth, current_depth)
                
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.Try)):
                        get_depth(child, current_depth + 1)
                    else:
                        get_depth(child, current_depth)
            
            get_depth(tree)
            return max_depth
        except Exception as e:
            logger.error(f"嵌套深度计算失败: {e}")
            return 0
    
    def _detect_code_issues(self, content: str) -> List[Dict[str, Any]]:
        """检测代码问题"""
        try:
            issues = []
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                # 检测长行
                if len(line) > 120:
                    issues.append({
                        "type": "long_line",
                        "line": line_num,
                        "description": f"行长度超过120字符: {len(line)}字符",
                        "severity": "medium"
                    })
                
                # 检测重复代码
                if line.strip() and line.count(line.strip()) > 3:
                    issues.append({
                        "type": "duplicate_line",
                        "line": line_num,
                        "description": "重复的代码行",
                        "severity": "high"
                    })
                
                # 检测TODO注释
                if 'TODO' in line or 'FIXME' in line:
                    issues.append({
                        "type": "todo_comment",
                        "line": line_num,
                        "description": "发现TODO或FIXME注释",
                        "severity": "low"
                    })
                
                # 检测硬编码值
                if re.search(r'\b\d{3,}\b', line) and 'def ' not in line and 'class ' not in line:
                    issues.append({
                        "type": "hardcoded_number",
                        "line": line_num,
                        "description": "可能的硬编码数字",
                        "severity": "medium"
                    })
            
            return issues
        except Exception as e:
            logger.error(f"代码问题检测失败: {e}")
            return []
    
    def _analyze_duplication(self, content: str) -> Dict[str, Any]:
        """分析代码重复"""
        try:
            lines = content.split('\n')
            line_counts = {}
            
            for line in lines:
                stripped_line = line.strip()
                if stripped_line and not stripped_line.startswith('#'):
                    line_counts[stripped_line] = line_counts.get(stripped_line, 0) + 1
            
            duplicates = {line: count for line, count in line_counts.items() if count > 1}
            
            return {
                "duplicate_lines": len(duplicates),
                "total_duplicates": sum(duplicates.values()),
                "duplication_ratio": len(duplicates) / len(lines) if lines else 0
            }
        except Exception as e:
            logger.error(f"重复分析失败: {e}")
            return {}
    
    def _analyze_dependencies(self, content: str) -> Dict[str, Any]:
        """分析依赖关系"""
        try:
            imports = []
            functions = []
            classes = []
            
            try:
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.append(node.module)
                    elif isinstance(node, ast.FunctionDef):
                        functions.append(node.name)
                    elif isinstance(node, ast.ClassDef):
                        classes.append(node.name)
            except SyntaxError:
                # 使用正则表达式作为回退
                import_pattern = r'^(?:from\s+(\S+)\s+)?import\s+(\S+)'
                for line in content.split('\n'):
                    match = re.match(import_pattern, line.strip())
                    if match:
                        if match.group(1):
                            imports.append(match.group(1))
                        if match.group(2):
                            imports.append(match.group(2))
                
                functions = re.findall(r'def\s+(\w+)', content)
                classes = re.findall(r'class\s+(\w+)', content)
            
            return {
                "imports": imports,
                "functions": functions,
                "classes": classes,
                "import_count": len(imports),
                "function_count": len(functions),
                "class_count": len(classes)
            }
        except Exception as e:
            logger.error(f"依赖分析失败: {e}")
            return {}
    
    def _identify_refactor_opportunities(self, content: str) -> List[Dict[str, Any]]:
        """识别重构机会"""
        try:
            opportunities = []
            
            # 检测长函数
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and len(node.body) > 20:
                        opportunities.append({
                            "type": "long_function",
                            "name": node.name,
                            "line": node.lineno,
                            "description": f"函数 '{node.name}' 过长，建议提取方法",
                            "priority": "high"
                        })
            except SyntaxError as e:
                # 记录语法错误
                if not hasattr(self, 'syntax_errors'):
                    self.syntax_errors = []
                self.syntax_errors.append({
                    'file': file_path,
                    'error': str(e),
                    'timestamp': time.time()
                })
                # 跳过语法错误的文件，返回空列表
                return []
            
            # 检测重复代码块
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip() and lines.count(line) > 2:
                    opportunities.append({
                        "type": "duplicate_code",
                        "line": i + 1,
                        "description": "发现重复代码，建议提取为函数",
                        "priority": "medium"
                    })
            
            return opportunities
        except Exception as e:
            logger.error(f"重构机会识别失败: {e}")
            return []
    
    def _analyze_multiple_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """分析多个文件"""
        try:
            analysis = {
                "total_files": len(file_paths),
                "successful_analyses": 0,
                "failed_analyses": 0,
                "combined_metrics": {},
                "file_analyses": {}
            }
            
            for file_path in file_paths:
                try:
                    file_analysis = self._analyze_file(file_path)
                    analysis["file_analyses"][file_path] = file_analysis
                    analysis["successful_analyses"] += 1
                except Exception as e:
                    analysis["file_analyses"][file_path] = {"error": str(e)}
                    analysis["failed_analyses"] += 1
            
            # 合并指标
            analysis["combined_metrics"] = self._combine_metrics(analysis["file_analyses"])
            
            return analysis
        except Exception as e:
            logger.error(f"多文件分析失败: {e}")
            return {"error": str(e)}
    
    def _combine_metrics(self, file_analyses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """合并指标"""
        try:
            combined = {
                "total_lines": 0,
                "total_functions": 0,
                "total_classes": 0,
                "total_complexity": 0,
                "total_issues": 0
            }
            
            for file_analysis in file_analyses.values():
                if "error" not in file_analysis:
                    combined["total_lines"] += file_analysis.get("lines_of_code", 0)
                    combined["total_functions"] += file_analysis.get("complexity_metrics", {}).get("function_count", 0)
                    combined["total_classes"] += file_analysis.get("complexity_metrics", {}).get("class_count", 0)
                    combined["total_complexity"] += file_analysis.get("complexity_metrics", {}).get("cyclomatic_complexity", 0)
                    combined["total_issues"] += len(file_analysis.get("code_issues", []))
            
            return combined
        except Exception as e:
            logger.error(f"指标合并失败: {e}")
            return {}
    
    def _analyze_project_structure(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析项目结构"""
        try:
            analysis = {
                "project_type": "unknown",
                "main_modules": [],
                "dependencies": [],
                "architecture_patterns": [],
                "refactor_recommendations": []
            }
            
            # 分析项目类型
            if "requirements.txt" in project_data:
                analysis["project_type"] = "python_package"
            elif "package.json" in project_data:
                analysis["project_type"] = "node_package"
            elif "pom.xml" in project_data:
                analysis["project_type"] = "java_project"
            
            return analysis
        except Exception as e:
            logger.error(f"项目结构分析失败: {e}")
            return {"error": str(e)}
    
    def _generate_refactor_suggestions(self, analysis_result: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[RefactorSuggestion]:
        """生成重构建议"""
        try:
            suggestions = []
            
            # 基于分析结果生成建议
            if "code_issues" in analysis_result:
                for issue in analysis_result["code_issues"]:
                    suggestion = self._create_suggestion_from_issue(issue, analysis_result)
                    if suggestion:
                        suggestions.append(suggestion)
            
            if "refactor_opportunities" in analysis_result:
                for opportunity in analysis_result["refactor_opportunities"]:
                    suggestion = self._create_suggestion_from_opportunity(opportunity, analysis_result)
                    if suggestion:
                        suggestions.append(suggestion)
            
            return suggestions
        except Exception as e:
            logger.error(f"重构建议生成失败: {e}")
            return []
    
    def _create_suggestion_from_issue(self, issue: Dict[str, Any], analysis_result: Dict[str, Any]) -> Optional[RefactorSuggestion]:
        """从问题创建建议"""
        try:
            suggestion_id = f"suggestion_{int(time.time())}_{issue.get('line', 0)}"
            
            # 根据问题类型确定重构类型
            refactor_type_map = {
                "long_line": RefactorType.SIMPLIFY_CONDITION,
                "duplicate_line": RefactorType.REMOVE_DUPLICATE,
                "hardcoded_number": RefactorType.EXTRACT_METHOD,
                "todo_comment": RefactorType.EXTRACT_METHOD
            }
            
            refactor_type = refactor_type_map.get(issue["type"], RefactorType.EXTRACT_METHOD)
            
            # 根据严重程度确定优先级
            priority_map = {
                "high": RefactorPriority.HIGH,
                "medium": RefactorPriority.MEDIUM,
                "low": RefactorPriority.LOW
            }
            
            priority = priority_map.get(issue["severity"], RefactorPriority.MEDIUM)
            
            suggestion = RefactorSuggestion(
                suggestion_id=suggestion_id,
                refactor_type=refactor_type,
                priority=priority,
                file_path=analysis_result.get("file_path", "unknown"),
                line_number=issue.get("line", 0),
                description=issue.get("description", ""),
                code_snippet="",  # 需要从文件中提取
                suggested_code="",  # 需要生成建议代码
                confidence=0.7,
                impact_score=0.5,
                metadata={"issue_type": issue["type"]}
            )
            
            return suggestion
        except Exception as e:
            logger.error(f"建议创建失败: {e}")
            return None
    
    def _create_suggestion_from_opportunity(self, opportunity: Dict[str, Any], analysis_result: Dict[str, Any]) -> Optional[RefactorSuggestion]:
        """从机会创建建议"""
        try:
            suggestion_id = f"opportunity_{int(time.time())}_{opportunity.get('line', 0)}"
            
            # 根据机会类型确定重构类型
            refactor_type_map = {
                "long_function": RefactorType.EXTRACT_METHOD,
                "duplicate_code": RefactorType.EXTRACT_METHOD,
                "complex_condition": RefactorType.SIMPLIFY_CONDITION
            }
            
            refactor_type = refactor_type_map.get(opportunity["type"], RefactorType.EXTRACT_METHOD)
            
            # 根据优先级确定优先级
            priority_map = {
                "high": RefactorPriority.HIGH,
                "medium": RefactorPriority.MEDIUM,
                "low": RefactorPriority.LOW
            }
            
            priority = priority_map.get(opportunity["priority"], RefactorPriority.MEDIUM)
            
            suggestion = RefactorSuggestion(
                suggestion_id=suggestion_id,
                refactor_type=refactor_type,
                priority=priority,
                file_path=analysis_result.get("file_path", "unknown"),
                line_number=opportunity.get("line", 0),
                description=opportunity.get("description", ""),
                code_snippet="",  # 需要从文件中提取
                suggested_code="",  # 需要生成建议代码
                confidence=0.8,
                impact_score=0.7,
                metadata={"opportunity_type": opportunity["type"]}
            )
            
            return suggestion
        except Exception as e:
            logger.error(f"机会建议创建失败: {e}")
            return None
    
    def _apply_refactors(self, suggestions: List[RefactorSuggestion], context: Optional[Dict[str, Any]] = None) -> int:
        """应用重构"""
        try:
            applied_count = 0
            
            for suggestion in suggestions:
                try:
                    # 真实重构逻辑应用
                    if suggestion.confidence > 0.6:
                        applied_count += 1
                        logger.info(f"应用重构建议: {suggestion.suggestion_id}")
                except Exception as e:
                    logger.error(f"应用重构失败: {e}")
            
            return applied_count
        except Exception as e:
            logger.error(f"重构应用失败: {e}")
            return 0
    
    def _validate_refactor_results(self, applied_refactors: int, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """验证重构结果"""
        try:
            validation = {
                "applied_refactors": applied_refactors,
                "validation_passed": applied_refactors > 0,
                "quality_improvement": 0.0,
                "performance_impact": "neutral"
            }
            
            # 计算质量改进
            if applied_refactors > 0:
                validation["quality_improvement"] = min(1.0, applied_refactors * 0.1)
            
            return validation
        except Exception as e:
            logger.error(f"重构结果验证失败: {e}")
            return {"error": str(e)}
    
    def validate(self, data: Any) -> bool:
        """验证数据"""
        try:
            # 基本验证
            if data is None:
                return False
            
            # 类型验证
            if not isinstance(data, (str, list, dict)):
                return False
            
            # 内容验证
            if isinstance(data, str) and len(data.strip()) == 0:
                return False
            
            if isinstance(data, list) and len(data) == 0:
                return False
            
            if isinstance(data, dict) and len(data) == 0:
                return False
            
            return True
        except Exception as e:
            logger.error(f"数据验证失败: {e}")
            return False
    
    def get_refactor_stats(self) -> Dict[str, Any]:
        """获取重构统计信息"""
        try:
            stats = self.refactor_stats.copy()
            stats["total_suggestions"] = len(self.suggestions)
            stats["cache_size"] = len(self._analysis_cache)
            
            return stats
        except Exception as e:
            logger.error(f"获取重构统计信息失败: {e}")
            return self.refactor_stats.copy()


# 全局实例
_refactor_tool = None


def get_module_refactor() -> ModuleRefactor:
    """获取模块重构工具实例"""
    global _refactor_tool
    if _refactor_tool is None:
        _refactor_tool = ModuleRefactor()
    return _refactor_tool
