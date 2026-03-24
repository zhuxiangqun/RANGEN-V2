"""
代码质量分析器

静态扫描代码文件，分析代码质量指标
"""

import ast
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple
from .base_analyzer import BaseAnalyzer


class CodeQualityAnalyzer(BaseAnalyzer):
    """代码质量分析器 - 静态扫描"""
    
    def __init__(self, source_path: str = None):
        super().__init__("CodeQualityAnalyzer")
        self.source_path = source_path or "/Users/apple/workdata/person/zy/RANGEN-main(syu-python)/src"
    
    def analyze(self, log_content: str = None) -> Dict[str, Any]:
        """分析代码质量"""
        results = {
            "file_count": self._analyze_file_count(),
            "complexity": self._analyze_complexity(),
            "type_annotations": self._analyze_type_annotations(),
            "docstrings": self._analyze_docstrings(),
            "naming": self._analyze_naming(),
            "test_coverage": self._analyze_test_coverage(),
        }
        
        scores = [r["score"] for r in results.values() if r.get("score") is not None]
        overall_score = sum(scores) / len(scores) if scores else 0.0
        
        return {
            "overall_score": overall_score,
            "metrics": results,
            "passed_count": sum(1 for r in results.values() if r.get("score", 0) >= 0.7),
            "total_count": len(results),
        }
    
    def _get_py_files(self) -> List[Path]:
        """获取所有Python文件"""
        py_files = list(Path(self.source_path).rglob("*.py"))
        py_files = [f for f in py_files if "__pycache__" not in str(f) and ".venv" not in str(f)]
        return py_files
    
    def _analyze_file_count(self) -> Dict[str, Any]:
        """分析文件数量"""
        py_files = self._get_py_files()
        count = len(py_files)
        
        if 50 <= count <= 200:
            score = 1.0
        elif count < 50:
            score = count / 50
        else:
            score = max(0.5, 1.0 - (count - 200) / 500)
        
        return {
            "score": score,
            "count": count,
            "evidence": f"Python文件: {count}个",
            "status": "good" if score >= 0.7 else "poor"
        }
    
    def _analyze_complexity(self) -> Dict[str, Any]:
        """分析代码复杂度"""
        total_complexity = 0
        file_count = 0
        high_complexity_files = []
        
        for p in self._get_py_files():
            try:
                with open(p, encoding="utf-8") as f:
                    tree = ast.parse(f.read())
                complexity = self._calculate_complexity(tree)
                total_complexity += complexity
                file_count += 1
                if complexity > 20:
                    high_complexity_files.append({"file": str(p), "complexity": complexity})
            except:
                continue
        
        avg_complexity = total_complexity / file_count if file_count > 0 else 0
        
        if avg_complexity <= 10:
            score = 1.0
        elif avg_complexity <= 20:
            score = 0.8
        elif avg_complexity <= 30:
            score = 0.5
        else:
            score = max(0.2, 0.3 - (avg_complexity - 30) / 100)
        
        return {
            "score": score,
            "avg_complexity": round(avg_complexity, 2),
            "high_complexity_count": len(high_complexity_files),
            "evidence": f"平均复杂度: {avg_complexity:.1f}",
            "status": "good" if score >= 0.7 else "poor"
        }
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """计算圈复杂度"""
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity
    
    def _analyze_type_annotations(self) -> Dict[str, Any]:
        """分析类型注解覆盖率"""
        total_functions = 0
        typed_functions = 0
        
        for p in self._get_py_files():
            try:
                with open(p, encoding="utf-8") as f:
                    tree = ast.parse(f.read())
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_functions += 1
                        if node.returns is not None or any(arg.annotation for arg in node.args.args):
                            typed_functions += 1
            except:
                continue
        
        coverage = typed_functions / total_functions if total_functions > 0 else 0
        
        if coverage >= 0.7:
            score = 1.0
        elif coverage >= 0.5:
            score = 0.8
        elif coverage >= 0.3:
            score = 0.6
        else:
            score = max(0.2, coverage)
        
        return {
            "score": score,
            "coverage": round(coverage, 2),
            "typed_count": typed_functions,
            "total_count": total_functions,
            "evidence": f"类型注解覆盖率: {coverage:.1%}",
            "status": "good" if score >= 0.7 else "poor"
        }
    
    def _analyze_docstrings(self) -> Dict[str, Any]:
        """分析文档字符串覆盖率"""
        total_functions = 0
        documented_functions = 0
        
        for p in self._get_py_files():
            try:
                with open(p, encoding="utf-8") as f:
                    tree = ast.parse(f.read())
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        total_functions += 1
                        if ast.get_docstring(node):
                            documented_functions += 1
            except:
                continue
        
        coverage = documented_functions / total_functions if total_functions > 0 else 0
        
        if coverage >= 0.5:
            score = 1.0
        elif coverage >= 0.3:
            score = 0.8
        elif coverage >= 0.1:
            score = 0.5
        else:
            score = 0.3
        
        return {
            "score": score,
            "coverage": round(coverage, 2),
            "documented_count": documented_functions,
            "total_count": total_functions,
            "evidence": f"文档覆盖率: {coverage:.1%}",
            "status": "good" if score >= 0.7 else "poor"
        }
    
    def _analyze_naming(self) -> Dict[str, Any]:
        """分析命名规范"""
        import re
        violations = []
        
        for p in self._get_py_files():
            try:
                with open(p, encoding="utf-8") as f:
                    content = f.read()
                    tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if re.match(r'^[A-Z]', node.name):
                            violations.append(f"{node.name} (函数)")
                    elif isinstance(node, ast.ClassDef):
                        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                            violations.append(f"{node.name} (类)")
            except:
                continue
        
        violation_rate = len(violations) / max(len(self._get_py_files()), 1)
        score = max(0.3, 1.0 - violation_rate)
        
        return {
            "score": score,
            "violation_count": len(violations),
            "evidence": f"命名规范违规: {len(violations)}处",
            "status": "good" if score >= 0.7 else "poor"
        }
    
    def _analyze_test_coverage(self) -> Dict[str, Any]:
        """分析测试覆盖率"""
        py_files = self._get_py_files()
        test_files = [f for f in py_files if "test_" in f.name or "_test.py" in f.name or "/tests/" in str(f)]
        
        total_files = len(py_files)
        test_count = len(test_files)
        coverage = test_count / total_files if total_files > 0 else 0
        
        if coverage >= 0.2:
            score = 1.0
        elif coverage >= 0.1:
            score = 0.8
        elif coverage >= 0.05:
            score = 0.5
        else:
            score = max(0.2, coverage * 5)
        
        return {
            "score": score,
            "coverage": round(coverage, 2),
            "test_count": test_count,
            "total_count": total_files,
            "evidence": f"测试覆盖率: {coverage:.1%}",
            "status": "good" if score >= 0.7 else "poor"
        }
