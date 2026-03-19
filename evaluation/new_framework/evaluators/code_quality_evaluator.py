"""
代码质量评估器 - 改进版

不检查关键词，而是检查实际的代码质量指标
"""

import os
import ast
from typing import Dict, Any, List, Optional
from pathlib import Path
from base_evaluator import BaseEvaluator, EvaluationResult, EvaluationStatus


class CodeQualityEvaluator(BaseEvaluator):
    """代码质量评估 - 改进版"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.source_path = self.config.get("source_path", "src")
    
    @property
    def dimension_name(self) -> str:
        return "code_quality"
    
    @property
    def weight(self) -> float:
        return 0.15
    
    async def evaluate(self) -> EvaluationResult:
        results = {
            "test_coverage": await self._check_test_coverage(),
            "complexity": await self._check_complexity(),
            "documentation": await self._check_documentation()
        }
        
        scores = [r["score"] for r in results.values() if r.get("score") is not None]
        overall_score = sum(scores) / len(scores) if scores else 0.5
        
        return {
            "dimension": self.dimension_name,
            "score": self._safe_score(overall_score),
            "status": EvaluationStatus.COMPLETED,
            "metrics": results,
            "details": f"测试覆盖: {results['test_coverage'].get('coverage', 0):.0f}%, "
                   f"复杂度: {results['complexity'].get('avg_complexity', 'N/A')}"
        }
    
    async def _check_test_coverage(self) -> Dict[str, Any]:
        try:
            test_dirs = ["tests", "test", "test_"]
            src_files = self._count_python_files(self.source_path)
            test_files = sum(1 for d in test_dirs for _ in Path(d).rglob("test_*.py"))
            
            if src_files > 0:
                coverage = test_files / (src_files / 10)
                return {
                    "score": min(coverage, 1.0),
                    "coverage": coverage * 100,
                    "test_files": test_files,
                    "src_files": src_files
                }
        except Exception:
            pass
        
        return {"score": 0.3, "coverage": 0, "note": "无法计算测试覆盖"}
    
    async def _check_complexity(self) -> Dict[str, Any]:
        total_complexity = 0
        file_count = 0
        max_complexity = 0
        
        try:
            for py_file in Path(self.source_path).rglob("*.py"):
                try:
                    with open(py_file) as f:
                        tree = ast.parse(f.read())
                    
                    complexity = self._calculate_complexity(tree)
                    total_complexity += complexity
                    file_count += 1
                    max_complexity = max(max_complexity, complexity)
                except Exception:
                    pass
            
            if file_count > 0:
                avg_complexity = total_complexity / file_count
                score = max(0, 1 - avg_complexity / 20)
                return {
                    "score": score,
                    "avg_complexity": avg_complexity,
                    "max_complexity": max_complexity,
                    "files_analyzed": file_count
                }
        except Exception:
            pass
        
        return {"score": 0.5, "avg_complexity": "未知"}
    
    async def _check_documentation(self) -> Dict[str, Any]:
        documented = 0
        total = 0
        
        try:
            for py_file in Path(self.source_path).rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                try:
                    with open(py_file) as f:
                        content = f.read()
                        tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                            total += 1
                            if ast.get_docstring(node):
                                documented += 1
                except Exception:
                    pass
            
            if total > 0:
                score = documented / total
                return {"score": score, "documented": documented, "total": total}
        except Exception:
            pass
        
        return {"score": 0.3, "note": "无法计算文档覆盖"}
    
    def _count_python_files(self, path: str) -> int:
        count = 0
        try:
            for p in Path(path).rglob("*.py"):
                if "__pycache__" not in str(p):
                    count += 1
        except Exception:
            pass
        return count
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity
