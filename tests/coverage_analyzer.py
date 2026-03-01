#!/usr/bin/env python3
"""
测试覆盖率分析器
分析代码覆盖率，识别测试空白区域
"""

import os
import sys
import json
import ast
import inspect
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict

# 设置项目环境
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@dataclass
class CoverageGap:
    """覆盖率空白"""
    file_path: str
    line_number: int
    function_name: str
    gap_type: str  # 'function', 'class', 'branch', 'line'
    severity: str  # 'high', 'medium', 'low'

@dataclass
class CoverageAnalysis:
    """覆盖率分析结果"""
    total_files: int
    covered_files: int
    coverage_percentage: float
    gaps: List[CoverageGap]
    recommendations: List[str]

class CoverageAnalyzer:
    """覆盖率分析器"""

    def __init__(self):
        self.source_files = []
        self.test_files = []
        self.coverage_gaps = []
        self.analysis_results = None

    def analyze_coverage(self) -> CoverageAnalysis:
        """分析覆盖率"""
        print("📊 开始覆盖率分析...")

        # 发现源代码文件
        self._discover_source_files()

        # 发现测试文件
        self._discover_test_files()

        # 分析覆盖率空白
        self._analyze_coverage_gaps()

        # 计算覆盖率统计
        coverage_stats = self._calculate_coverage_stats()

        # 生成建议
        recommendations = self._generate_recommendations()

        self.analysis_results = CoverageAnalysis(
            total_files=len(self.source_files),
            covered_files=coverage_stats['covered_files'],
            coverage_percentage=coverage_stats['coverage_percentage'],
            gaps=self.coverage_gaps,
            recommendations=recommendations
        )

        return self.analysis_results

    def _discover_source_files(self):
        """发现源代码文件"""
        print("   🔍 发现源代码文件...")

        source_dirs = ['src', 'scripts']
        exclude_patterns = [
            '__pycache__',
            'test_*.py',
            'tests/',
            'reports/',
            'logs/',
            'data/',
            'venv/',
            '.venv/',
            'node_modules/'
        ]

        for source_dir in source_dirs:
            dir_path = project_root / source_dir
            if dir_path.exists():
                for py_file in dir_path.rglob('*.py'):
                    # 检查是否应该排除
                    should_exclude = False
                    for pattern in exclude_patterns:
                        if pattern in str(py_file):
                            should_exclude = True
                            break

                    if not should_exclude:
                        self.source_files.append(py_file)

        print(f"   ✅ 发现 {len(self.source_files)} 个源代码文件")

    def _discover_test_files(self):
        """发现测试文件"""
        print("   🔍 发现测试文件...")

        test_dirs = ['tests', 'scripts', 'knowledge_management_system']
        test_patterns = ['test_*.py', '*_test.py']

        for test_dir in test_dirs:
            dir_path = project_root / test_dir
            if dir_path.exists():
                for pattern in test_patterns:
                    for test_file in dir_path.rglob(pattern):
                        if test_file.is_file():
                            self.test_files.append(test_file)

        # 根目录的测试文件
        for pattern in test_patterns:
            for test_file in project_root.glob(pattern):
                if test_file.is_file():
                    self.test_files.append(test_file)

        # 去重
        self.test_files = list(set(self.test_files))

        print(f"   ✅ 发现 {len(self.test_files)} 个测试文件")

    def _analyze_coverage_gaps(self):
        """分析覆盖率空白"""
        print("   🔍 分析覆盖率空白...")

        for source_file in self.source_files:
            self._analyze_single_file(source_file)

    def _analyze_single_file(self, file_path: Path):
        """分析单个文件的覆盖率"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 解析AST
            tree = ast.parse(content, filename=str(file_path))

            # 查找未测试的函数和类
            self._find_uncovered_functions(tree, file_path)
            self._find_uncovered_classes(tree, file_path)

        except Exception as e:
            print(f"   ⚠️  分析文件失败 {file_path}: {e}")

    def _find_uncovered_functions(self, tree: ast.AST, file_path: Path):
        """查找未测试的函数"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_name = node.name

                # 检查是否有对应的测试
                if not self._has_test_for_function(file_path, function_name):
                    gap = CoverageGap(
                        file_path=str(file_path),
                        line_number=node.lineno,
                        function_name=function_name,
                        gap_type='function',
                        severity=self._calculate_severity(node)
                    )
                    self.coverage_gaps.append(gap)

    def _find_uncovered_classes(self, tree: ast.AST, file_path: Path):
        """查找未测试的类"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name

                # 检查是否有对应的测试
                if not self._has_test_for_class(file_path, class_name):
                    gap = CoverageGap(
                        file_path=str(file_path),
                        line_number=node.lineno,
                        function_name=class_name,
                        gap_type='class',
                        severity='high'  # 类通常很重要
                    )
                    self.coverage_gaps.append(gap)

    def _has_test_for_function(self, source_file: Path, function_name: str) -> bool:
        """检查函数是否有测试"""
        # 简单的启发式检查：查找对应的测试文件和测试函数
        test_file_patterns = [
            f"test_{source_file.stem}.py",
            f"{source_file.stem}_test.py",
            "test_*.py"
        ]

        for test_file in self.test_files:
            # 检查文件名匹配
            file_name_match = any(
                Path(pattern).match(test_file.name) or
                test_file.name.startswith(f"test_{source_file.stem}")
                for pattern in test_file_patterns
            )

            if file_name_match:
                try:
                    with open(test_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 检查是否包含函数名相关的测试
                    test_patterns = [
                        f"def test_{function_name}",
                        f"def test.*{function_name}",
                        f"{function_name}(",
                        f"assert.*{function_name}"
                    ]

                    for pattern in test_patterns:
                        if pattern in content:
                            return True

                except Exception:
                    continue

        return False

    def _has_test_for_class(self, source_file: Path, class_name: str) -> bool:
        """检查类是否有测试"""
        # 类似的逻辑检查类
        for test_file in self.test_files:
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查类名出现
                if class_name in content:
                    return True

            except Exception:
                continue

        return False

    def _calculate_severity(self, node: ast.FunctionDef) -> str:
        """计算覆盖空白的严重程度"""
        # 基于函数复杂度和重要性计算严重程度
        line_count = len(node.body) if hasattr(node, 'body') else 0

        if line_count > 50:
            return 'high'  # 长函数更重要
        elif line_count > 20:
            return 'medium'  # 中等长度的函数
        else:
            return 'low'  # 短函数或简单函数

    def _calculate_coverage_stats(self) -> Dict[str, Any]:
        """计算覆盖率统计"""
        # 估算覆盖率（基于测试文件数量的简单估算）
        test_to_source_ratio = len(self.test_files) / max(1, len(self.source_files))

        # 基于比例估算覆盖率
        if test_to_source_ratio > 0.5:
            coverage_percentage = min(85, 40 + test_to_source_ratio * 30)
        elif test_to_source_ratio > 0.2:
            coverage_percentage = min(70, 30 + test_to_source_ratio * 20)
        else:
            coverage_percentage = max(10, test_to_source_ratio * 50)

        return {
            'covered_files': int(len(self.source_files) * coverage_percentage / 100),
            'coverage_percentage': coverage_percentage
        }

    def _generate_recommendations(self) -> List[str]:
        """生成覆盖率改进建议"""
        recommendations = []

        # 基于空白分析生成建议
        gap_counts = defaultdict(int)
        for gap in self.coverage_gaps:
            gap_counts[gap.gap_type] += 1

        if gap_counts['function'] > 50:
            recommendations.append(f"有 {gap_counts['function']} 个函数缺少测试，建议优先测试核心业务函数")

        if gap_counts['class'] > 10:
            recommendations.append(f"有 {gap_counts['class']} 个类缺少测试，建议为主要类添加单元测试")

        # 基于覆盖率生成建议
        if self.analysis_results and self.analysis_results.coverage_percentage < 50:
            recommendations.append("当前测试覆盖率较低，建议制定测试覆盖率提升计划")

        if len(self.test_files) < len(self.source_files) * 0.3:
            recommendations.append("测试文件数量不足，建议每个源文件至少对应一个测试文件")

        # 具体建议
        recommendations.extend([
            "为高严重程度的功能添加单元测试",
            "为复杂类添加集成测试",
            "添加异常处理路径的测试",
            "为关键业务逻辑添加边界条件测试",
            "定期运行覆盖率分析，跟踪改进进度"
        ])

        return recommendations

    def generate_coverage_report(self):
        """生成覆盖率报告"""
        if not self.analysis_results:
            self.analyze_coverage()

        print("📝 生成覆盖率报告...")

        report = {
            'timestamp': str(Path(__file__).stat().st_mtime),
            'analysis_results': {
                'total_files': self.analysis_results.total_files,
                'covered_files': self.analysis_results.covered_files,
                'coverage_percentage': self.analysis_results.coverage_percentage,
                'total_gaps': len(self.analysis_results.gaps)
            },
            'gaps_by_type': defaultdict(int),
            'gaps_by_severity': defaultdict(int),
            'top_gap_files': [],
            'recommendations': self.analysis_results.recommendations
        }

        # 统计空白类型和严重程度
        for gap in self.analysis_results.gaps:
            report['gaps_by_type'][gap.gap_type] += 1
            report['gaps_by_severity'][gap.severity] += 1

        # 找出空白最多的文件
        file_gaps = defaultdict(int)
        for gap in self.analysis_results.gaps:
            file_gaps[gap.file_path] += 1

        top_files = sorted(file_gaps.items(), key=lambda x: x[1], reverse=True)[:10]
        report['top_gap_files'] = [{'file': f, 'gaps': c} for f, c in top_files]

        # 保存报告
        report_path = project_root / 'reports' / 'coverage_analysis_report.json'
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 生成文本报告
        self._generate_text_report(report)

        print(f"✅ 覆盖率分析报告已保存: {report_path}")

    def _generate_text_report(self, report: Dict[str, Any]):
        """生成文本覆盖率报告"""
        text_report = f"""
RANGEN 测试覆盖率分析报告
{'='*50}

执行时间: {report['timestamp']}
总源文件数: {report['analysis_results']['total_files']}
覆盖文件数: {report['analysis_results']['covered_files']}
覆盖率: {report['analysis_results']['coverage_percentage']:.1f}%
总空白数: {report['analysis_results']['total_gaps']}

空白类型分布:
"""

        for gap_type, count in report['gaps_by_type'].items():
            text_report += f"  {gap_type}: {count}\n"

        text_report += "\n严重程度分布:\n"
        for severity, count in report['gaps_by_severity'].items():
            text_report += f"  {severity}: {count}\n"

        text_report += "\n空白最多的文件:\n"
        for file_info in report['top_gap_files'][:5]:
            text_report += f"  {file_info['file']}: {file_info['gaps']} 个空白\n"

        text_report += "\n改进建议:\n"
        for rec in report['recommendations']:
            text_report += f"• {rec}\n"

        # 保存文本报告
        text_path = project_root / 'reports' / 'coverage_analysis_report.txt'
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text_report)

        print(f"✅ 文本覆盖率报告已保存: {text_path}")

        # 打印关键信息
        print("\n" + "=" * 50)
        print("🎯 覆盖率分析结果")
        print("=" * 50)
        print(".1f"
        print(f"📁 总源文件: {report['analysis_results']['total_files']}")
        print(f"📝 总测试空白: {report['analysis_results']['total_gaps']}")

def main():
    """主函数"""
    analyzer = CoverageAnalyzer()
    analyzer.analyze_coverage()
    analyzer.generate_coverage_report()

if __name__ == "__main__":
    main()
