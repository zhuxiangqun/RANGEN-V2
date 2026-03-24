"""
静态代码分析评估器

仅用于2个维度：
1. architecture - 架构合理性
2. code_quality - 代码质量
"""

import ast
import re
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class StaticCheckResult:
    """静态检查结果"""
    check_name: str
    passed: bool
    score: float
    message: str
    evidence: List[str] = None


class StaticEvaluator:
    """静态代码分析评估器"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.source_path = self.config.get('source_path', '/Users/apple/workdata/person/zy/RANGEN-main(syu-python)/src')
        self.max_sample_count = self.config.get('max_sample_count', 100)
    
    async def evaluate(self, dimension: str) -> Dict[str, Any]:
        """
        评估单个维度
        
        Args:
            dimension: 维度名称 ('architecture' 或 'code_quality')
            
        Returns:
            评估结果
        """
        if dimension == 'architecture':
            return await self._evaluate_architecture()
        elif dimension == 'code_quality':
            return await self._evaluate_code_quality()
        else:
            return {
                'dimension': dimension,
                'score': 0.0,
                'status': 'failed',
                'error': f'Unknown dimension: {dimension}'
            }
    
    async def _evaluate_architecture(self) -> Dict[str, Any]:
        """评估架构合理性"""
        checks = []
        
        # 1. 模块结构检查
        checks.append(self._check_module_structure())
        
        # 2. 分层架构检查
        checks.append(self._check_layered_architecture())
        
        # 3. 设计模式检查
        checks.append(self._check_design_patterns())
        
        # 4. 依赖关系检查
        checks.append(self._check_dependencies())
        
        # 5. 接口一致性检查
        checks.append(self._check_interface_consistency())
        
        # 计算总分
        total_score = sum(c.score for c in checks)
        avg_score = total_score / len(checks) if checks else 0.0
        
        return {
            'dimension': 'architecture',
            'score': avg_score,
            'status': 'completed',
            'checks': [
                {
                    'name': c.check_name,
                    'passed': c.passed,
                    'score': c.score,
                    'message': c.message,
                    'evidence': c.evidence
                }
                for c in checks
            ]
        }
    
    async def _evaluate_code_quality(self) -> Dict[str, Any]:
        """评估代码质量"""
        checks = []
        
        # 1. 复杂度检查
        checks.append(self._check_complexity())
        
        # 2. 重复代码检查
        checks.append(self._check_duplication())
        
        # 3. 文档覆盖检查
        checks.append(self._check_documentation())
        
        # 4. 测试覆盖检查
        checks.append(self._check_test_coverage())
        
        # 5. 命名规范检查
        checks.append(self._check_naming_conventions())
        
        # 计算总分
        total_score = sum(c.score for c in checks)
        avg_score = total_score / len(checks) if checks else 0.0
        
        return {
            'dimension': 'code_quality',
            'score': avg_score,
            'status': 'completed',
            'checks': [
                {
                    'name': c.check_name,
                    'passed': c.passed,
                    'score': c.score,
                    'message': c.message,
                    'evidence': c.evidence
                }
                for c in checks
            ]
        }
    
    def _check_module_structure(self) -> StaticCheckResult:
        """检查模块结构"""
        src_path = Path(self.source_path)
        
        # 检查关键目录是否存在
        expected_dirs = ['services', 'orchestration', 'agents', 'utils']
        found_dirs = [d for d in expected_dirs if (src_path / d).exists()]
        
        score = len(found_dirs) / len(expected_dirs) if expected_dirs else 0.0
        
        return StaticCheckResult(
            check_name='module_structure',
            passed=len(found_dirs) >= 3,
            score=score,
            message=f'找到 {len(found_dirs)}/{len(expected_dirs)} 个关键目录',
            evidence=found_dirs
        )
    
    def _check_layered_architecture(self) -> StaticCheckResult:
        """检查分层架构"""
        src_path = Path(self.source_path)
        
        # 检查是否有清晰的层级划分
        layers = {
            'api': list(src_path.rglob('*api*.py')) + list(src_path.rglob('*router*.py')),
            'service': list(src_path.rglob('*service*.py')),
            'model': list(src_path.rglob('*model*.py')) + list(src_path.rglob('*schema*.py')),
            'repository': list(src_path.rglob('*repo*.py')) + list(src_path.rglob('*dao*.py')),
        }
        
        # 计算得分
        found_layers = sum(1 for files in layers.values() if len(files) > 0)
        score = found_layers / len(layers) if layers else 0.0
        
        return StaticCheckResult(
            check_name='layered_architecture',
            passed=found_layers >= 2,
            score=score,
            message=f'找到 {found_layers}/{len(layers)} 个层级',
            evidence=[f'{k}: {len(v)} files' for k, v in layers.items() if len(v) > 0]
        )
    
    def _check_design_patterns(self) -> StaticCheckResult:
        """检查设计模式使用"""
        src_path = Path(self.source_path)
        
        patterns = {
            'singleton': list(src_path.rglob('*get_*.py')) + list(src_path.rglob('*singleton*.py')),
            'factory': list(src_path.rglob('*factory*.py')),
            'observer': list(src_path.rglob('*observer*.py')) + list(src_path.rglob('*event*.py')),
            'strategy': list(src_path.rglob('*strategy*.py')),
        }
        
        found_patterns = sum(1 for files in patterns.values() if len(files) > 0)
        score = min(found_patterns / 4, 1.0)
        
        return StaticCheckResult(
            check_name='design_patterns',
            passed=found_patterns >= 2,
            score=score,
            message=f'使用 {found_patterns} 种设计模式',
            evidence=[k for k, v in patterns.items() if len(v) > 0]
        )
    
    def _check_dependencies(self) -> StaticCheckResult:
        """检查依赖关系"""
        src_path = Path(self.source_path)
        
        # 检查循环依赖
        py_files = list(src_path.rglob('*.py'))[:50]  # 限制检查文件数
        
        # 简单检查：是否有过深的导入
        deep_imports = 0
        for f in py_files:
            try:
                content = f.read_text()
                imports = content.count('import ') + content.count('from ')
                if imports > 30:
                    deep_imports += 1
            except:
                pass
        
        # 计算得分
        score = 1.0 - (deep_imports / len(py_files) if py_files else 0)
        
        return StaticCheckResult(
            check_name='dependencies',
            passed=score >= 0.8,
            score=max(0, score),
            message=f'{len(py_files)} 个文件中，{deep_imports} 个有过多导入',
            evidence=[f'过多导入文件数: {deep_imports}']
        )
    
    def _check_interface_consistency(self) -> StaticCheckResult:
        """检查接口一致性"""
        src_path = Path(self.source_path)
        
        # 检查API文件
        api_files = list(src_path.rglob('*api*.py')) + list(src_path.rglob('*router*.py'))
        
        consistent = 0
        for f in api_files:
            try:
                content = f.read_text()
                # 检查是否有统一的响应格式
                if 'response' in content.lower() or 'result' in content.lower():
                    consistent += 1
            except:
                pass
        
        score = consistent / len(api_files) if api_files else 0.5
        
        return StaticCheckResult(
            check_name='interface_consistency',
            passed=score >= 0.6,
            score=score,
            message=f'{consistent}/{len(api_files)} 个API文件有统一响应格式',
            evidence=[f'一致文件数: {consistent}']
        )
    
    def _check_complexity(self) -> StaticCheckResult:
        """检查代码复杂度"""
        src_path = Path(self.source_path)
        
        py_files = list(src_path.rglob('*.py'))[:100]
        
        high_complexity = 0
        total_functions = 0
        
        for f in py_files:
            try:
                content = f.read_text()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_functions += 1
                        # 简单复杂度估计：基于函数长度和分支数
                        func_lines = node.end_lineno - node.lineno if node.end_lineno else 10
                        if func_lines > 50:
                            high_complexity += 1
            except:
                pass
        
        # 计算得分
        if total_functions == 0:
            score = 0.5
        else:
            score = 1.0 - (high_complexity / total_functions)
        
        return StaticCheckResult(
            check_name='complexity',
            passed=score >= 0.8,
            score=max(0, score),
            message=f'{total_functions} 个函数中，{high_complexity} 个过于复杂',
            evidence=[f'高复杂度函数: {high_complexity}']
        )
    
    def _check_duplication(self) -> StaticCheckResult:
        """检查重复代码"""
        src_path = Path(self.source_path)
        
        py_files = list(src_path.rglob('*.py'))[:50]
        
        # 简单检查：查找相似的函数名
        function_names = []
        for f in py_files:
            try:
                content = f.read_text()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        function_names.append(node.name)
            except:
                pass
        
        # 计算重复率
        unique_names = set(n.lower() for n in function_names)
        if len(function_names) == 0:
            score = 0.5
        else:
            duplication_rate = 1.0 - (len(unique_names) / len(function_names))
            score = max(0, 1.0 - duplication_rate)
        
        return StaticCheckResult(
            check_name='duplication',
            passed=score >= 0.7,
            score=score,
            message=f'{len(function_names)} 个函数，{len(unique_names)} 个唯一',
            evidence=[f'重复率: {(1-score)*100:.1f}%']
        )
    
    def _check_documentation(self) -> StaticCheckResult:
        """检查文档覆盖"""
        src_path = Path(self.source_path)
        
        py_files = list(src_path.rglob('*.py'))[:50]
        
        documented = 0
        for f in py_files:
            try:
                content = f.read_text()
                tree = ast.parse(content)
                
                # 检查模块级文档
                if (isinstance(tree.body[0], ast.Expr) and 
                    isinstance(tree.body[0].value, (ast.Str, ast.Constant))):
                    documented += 1
            except:
                pass
        
        score = documented / len(py_files) if py_files else 0.0
        
        return StaticCheckResult(
            check_name='documentation',
            passed=score >= 0.5,
            score=score,
            message=f'{documented}/{len(py_files)} 个文件有文档',
            evidence=[f'文档覆盖率: {score*100:.1f}%']
        )
    
    def _check_test_coverage(self) -> StaticCheckResult:
        """检查测试覆盖"""
        src_path = Path(self.source_path)
        
        # 统计源文件和测试文件
        src_files = len(list(src_path.rglob('*.py')))
        
        # 查找tests目录
        tests_dir = src_path.parent / 'tests'
        if tests_dir.exists():
            test_files = len(list(tests_dir.rglob('test_*.py')))
        else:
            test_files = 0
        
        # 计算覆盖率估计
        coverage = test_files / src_files if src_files > 0 else 0
        score = min(coverage * 5, 1.0)  # 假设1:5的源测试比
        
        return StaticCheckResult(
            check_name='test_coverage',
            passed=score >= 0.3,
            score=score,
            message=f'{src_files} 个源文件，{test_files} 个测试文件',
            evidence=[f'覆盖率估计: {coverage*100:.1f}%']
        )
    
    def _check_naming_conventions(self) -> StaticCheckResult:
        """检查命名规范"""
        src_path = Path(self.source_path)
        
        py_files = list(src_path.rglob('*.py'))[:30]
        
        compliant = 0
        for f in py_files:
            try:
                content = f.read_text()
                # 检查是否使用snake_case命名
                snake_case_vars = len(re.findall(r'\b[a-z][a-z0-9_]*\s*=', content))
                camel_case_vars = len(re.findall(r'\b[a-z][A-Z][a-zA-Z]*\s*=', content))
                
                if snake_case_vars > camel_case_vars:
                    compliant += 1
            except:
                pass
        
        score = compliant / len(py_files) if py_files else 0.5
        
        return StaticCheckResult(
            check_name='naming_conventions',
            passed=score >= 0.7,
            score=score,
            message=f'{compliant}/{len(py_files)} 个文件符合命名规范',
            evidence=[f'合规率: {score*100:.1f}%']
        )
