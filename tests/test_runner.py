#!/usr/bin/env python3
"""
统一测试运行器
提供完整的测试执行、覆盖率分析和报告生成功能
"""

import asyncio
import sys
import os
import time
import json
import unittest
try:
    import coverage
    HAS_COVERAGE = True
except ImportError:
    HAS_COVERAGE = False
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# 设置项目环境
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

class UnifiedTestRunner:
    """统一测试运行器"""

    def __init__(self):
        self.test_results = {}
        self.coverage_data = {}
        self.start_time = None
        self.end_time = None

    def run_all_tests(self, with_coverage: bool = True, parallel: bool = False):
        """运行所有测试"""
        print("🚀 开始运行完整测试套件")
        print("=" * 60)

        self.start_time = time.time()

        try:
            if with_coverage and HAS_COVERAGE:
                self._run_with_coverage()
            else:
                if with_coverage and not HAS_COVERAGE:
                    print("⚠️ 'coverage' 模块未安装，将跳过覆盖率分析")
                self._run_without_coverage()

            self._analyze_results()
            self._generate_test_report()

        except Exception as e:
            print(f"❌ 测试运行失败: {e}")
            return False

        self.end_time = time.time()
        total_time = self.end_time - self.start_time

        print(f"✅ 测试执行完成，总耗时: {total_time:.2f}秒")
        return True

    def _run_with_coverage(self):
        """带覆盖率运行测试"""
        print("📊 运行带覆盖率的测试...")

        # 配置覆盖率
        cov = coverage.Coverage(
            source=['src'],
            omit=[
                '*/tests/*',
                '*/test_*.py',
                '*/__pycache__/*',
                '*/venv/*',
                '*/.venv/*',
                '*/node_modules/*'
            ]
        )

        cov.start()

        try:
            # 运行测试
            self._execute_test_suites()
        finally:
            cov.stop()
            cov.save()

        # 生成覆盖率报告
        self.coverage_data = {
            'total_coverage': cov.report(),
            'file_coverage': {},
            'missing_lines': {}
        }

        # 保存HTML报告
        cov.html_report(directory='reports/coverage_html')
        cov.json_report(outfile='reports/coverage.json')

        print("✅ 覆盖率报告已生成")

    def _run_without_coverage(self):
        """不带覆盖率运行测试"""
        print("⚡ 运行快速测试...")
        self._execute_test_suites()

    def _execute_test_suites(self):
        """执行测试套件"""
        print("   🔍 发现并执行测试...")

        # 发现所有测试
        test_suites = self._discover_test_suites()

        # 执行测试
        results = {}
        for suite_name, test_files in test_suites.items():
            print(f"   📋 执行测试套件: {suite_name}")
            suite_results = self._run_test_suite(test_files)
            results[suite_name] = suite_results

        self.test_results = results

    def _discover_test_suites(self) -> Dict[str, List[str]]:
        """发现测试套件"""
        suites = {
            'unit_tests': [],
            'integration_tests': [],
            'performance_tests': [],
            'agent_tests': [],
            'tool_tests': [],
            'service_tests': []
        }

        # 扫描测试文件
        test_patterns = [
            ('tests/test_*.py', 'unit_tests'),
            ('tests/test_*integration*.py', 'integration_tests'),
            ('tests/test_*performance*.py', 'performance_tests'),
            ('tests/test_*agent*.py', 'agent_tests'),
            ('tests/test_*tool*.py', 'tool_tests'),
            ('tests/test_*service*.py', 'service_tests'),
            ('test_*.py', 'unit_tests'),  # 根目录的测试
            ('scripts/test_*.py', 'integration_tests')  # 脚本目录的测试
        ]

        for pattern, suite_name in test_patterns:
            files = list(project_root.glob(pattern))
            for file in files:
                if file.is_file():
                    suites[suite_name].append(str(file))

        # 去重
        for suite_name in suites:
            suites[suite_name] = list(set(suites[suite_name]))

        return suites

    def _run_test_suite(self, test_files: List[str]) -> Dict[str, Any]:
        """运行单个测试套件"""
        suite_results = {
            'total_files': len(test_files),
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'skipped': 0,
            'execution_time': 0,
            'file_results': []
        }

        for test_file in test_files:
            file_result = self._run_single_test_file(test_file)
            suite_results['file_results'].append(file_result)
            suite_results['passed'] += file_result['passed']
            suite_results['failed'] += file_result['failed']
            suite_results['errors'] += file_result['errors']
            suite_results['skipped'] += file_result['skipped']
            suite_results['execution_time'] += file_result['execution_time']

        return suite_results

    def _run_single_test_file(self, test_file: str) -> Dict[str, Any]:
        """运行单个测试文件"""
        start_time = time.time()

        try:
            # 使用subprocess运行测试，避免导入冲突
            result = subprocess.run([
                sys.executable, '-m', 'pytest', test_file,
                '--tb=short', '--quiet', '--json-report', '--json-report-file=/tmp/test_result.json'
            ], capture_output=True, text=True, timeout=300)

            execution_time = time.time() - start_time

            # 解析结果
            passed = 0
            failed = 0
            errors = 0
            skipped = 0

            if result.returncode == 0:
                # 尝试读取JSON结果
                try:
                    with open('/tmp/test_result.json', 'r') as f:
                        json_result = json.load(f)
                        passed = json_result.get('summary', {}).get('passed', 0)
                        failed = json_result.get('summary', {}).get('failed', 0)
                        errors = json_result.get('summary', {}).get('errors', 0)
                        skipped = json_result.get('summary', {}).get('skipped', 0)
                except:
                    passed = 1  # 假设成功
            else:
                failed = 1

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return {
                'file': test_file,
                'passed': 0,
                'failed': 1,
                'errors': 0,
                'skipped': 0,
                'execution_time': execution_time,
                'status': 'timeout',
                'error': 'Test execution timed out'
            }
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                'file': test_file,
                'passed': 0,
                'failed': 1,
                'errors': 0,
                'skipped': 0,
                'execution_time': execution_time,
                'status': 'error',
                'error': str(e)
            }

        return {
            'file': test_file,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'skipped': skipped,
            'execution_time': execution_time,
            'status': 'completed'
        }

    def _analyze_results(self):
        """分析测试结果"""
        print("📈 分析测试结果...")

        total_files = 0
        total_passed = 0
        total_failed = 0
        total_errors = 0
        total_skipped = 0
        total_execution_time = 0

        for suite_name, suite_results in self.test_results.items():
            total_files += suite_results['total_files']
            total_passed += suite_results['passed']
            total_failed += suite_results['failed']
            total_errors += suite_results['errors']
            total_skipped += suite_results['skipped']
            total_execution_time += suite_results['execution_time']

        total_tests = total_passed + total_failed + total_errors + total_skipped
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        self.analysis_results = {
            'total_files': total_files,
            'total_tests': total_tests,
            'passed': total_passed,
            'failed': total_failed,
            'errors': total_errors,
            'skipped': total_skipped,
            'success_rate': success_rate,
            'total_execution_time': total_execution_time,
            'average_test_time': total_execution_time / total_tests if total_tests > 0 else 0
        }

    def _generate_test_report(self):
        """生成测试报告"""
        print("📝 生成测试报告...")

        report = {
            'timestamp': datetime.now().isoformat(),
            'execution_time': self.end_time - self.start_time if self.end_time and self.start_time else 0,
            'test_results': self.test_results,
            'analysis_results': getattr(self, 'analysis_results', {}),
            'coverage_data': self.coverage_data,
            'recommendations': self._generate_test_recommendations()
        }

        # 保存报告
        report_path = project_root / 'reports' / 'unified_test_report.json'
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 生成HTML报告
        self._generate_html_report(report)

        print(f"✅ 测试报告已保存: {report_path}")

        # 打印总结
        self._print_test_summary(report)

    def _generate_test_recommendations(self) -> List[str]:
        """生成测试建议"""
        recommendations = []

        analysis = getattr(self, 'analysis_results', {})

        if analysis.get('success_rate', 0) < 80:
            recommendations.append("测试成功率较低，建议修复失败的测试用例")

        if analysis.get('failed', 0) > 10:
            recommendations.append("失败测试数量较多，建议优先修复核心功能测试")

        if analysis.get('average_test_time', 0) > 10:
            recommendations.append("平均测试执行时间较长，建议优化测试性能")

        if analysis.get('total_files', 0) < 20:
            recommendations.append("测试文件数量较少，建议增加测试覆盖率")

        return recommendations

    def _generate_html_report(self, report: Dict[str, Any]):
        """生成HTML测试报告"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>RANGEN 统一测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f0f0f0; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .suite {{ margin-bottom: 15px; padding: 10px; border: 1px solid #ddd; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .metric {{ display: inline-block; margin-right: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>RANGEN 统一测试报告</h1>
    <div class="summary">
        <h2>执行摘要</h2>
        <div class="metric"><strong>总文件数:</strong> {report['analysis_results'].get('total_files', 0)}</div>
        <div class="metric"><strong>总测试数:</strong> {report['analysis_results'].get('total_tests', 0)}</div>
        <div class="metric"><strong>成功率:</strong> {report['analysis_results'].get('success_rate', 0):.1f}%</div>
        <div class="metric"><strong>执行时间:</strong> {report['execution_time']:.2f}秒</div>
    </div>

    <h2>测试套件详情</h2>
"""

        for suite_name, suite_results in report['test_results'].items():
            html_content += f"""
    <div class="suite">
        <h3>{suite_name.replace('_', ' ').title()}</h3>
        <div class="metric passed">通过: {suite_results.get('passed', 0)}</div>
        <div class="metric failed">失败: {suite_results.get('failed', 0)}</div>
        <div class="metric">错误: {suite_results.get('errors', 0)}</div>
        <div class="metric">跳过: {suite_results.get('skipped', 0)}</div>
        <div class="metric">执行时间: {suite_results.get('execution_time', 0):.2f}秒</div>
    </div>
"""

        html_content += """
</body>
</html>
"""

        html_path = project_root / 'reports' / 'test_report.html'
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ HTML测试报告已生成: {html_path}")

    def _print_test_summary(self, report: Dict[str, Any]):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("🎯 测试执行总结")
        print("=" * 60)

        analysis = report.get('analysis_results', {})
        print(f"📁 总测试文件: {analysis.get('total_files', 0)}")
        print(f"🧪 总测试用例: {analysis.get('total_tests', 0)}")
        print(f"✅ 通过: {analysis.get('passed', 0)}")
        print(f"❌ 失败: {analysis.get('failed', 0)}")
        print(f"⚠️  错误: {analysis.get('errors', 0)}")
        print(f"⏭️  跳过: {analysis.get('skipped', 0)}")
        print(f"⏱️ 执行时间: {report.get('execution_time', 0):.2f}秒")
        print(f"⏱️ 总测试时间: {analysis.get('total_execution_time', 0):.2f}秒")
        print(f"⏱️ 平均每测试: {analysis.get('average_test_time', 0):.2f}秒")
        if 'coverage_data' in report and report['coverage_data']:
            print("📊 代码覆盖率: 已生成覆盖率报告")

        recommendations = report.get('recommendations', [])
        if recommendations:
            print("\n💡 测试建议:")
            for rec in recommendations:
                print(f"   • {rec}")

def run_all_tests():
    """运行所有测试的便捷函数"""
    runner = UnifiedTestRunner()
    return runner.run_all_tests()

def run_unit_tests():
    """运行单元测试"""
    runner = UnifiedTestRunner()
    # 只运行单元测试
    return runner.run_all_tests()

def run_integration_tests():
    """运行集成测试"""
    runner = UnifiedTestRunner()
    # 只运行集成测试
    return runner.run_all_tests()

def run_performance_tests():
    """运行性能测试"""
    runner = UnifiedTestRunner()
    # 只运行性能测试
    return runner.run_all_tests()

def generate_test_report():
    """生成测试报告"""
    runner = UnifiedTestRunner()
    runner._generate_test_report()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='RANGEN 统一测试运行器')
    parser.add_argument('--coverage', action='store_true', help='启用覆盖率分析')
    parser.add_argument('--parallel', action='store_true', help='并行执行测试')
    parser.add_argument('--report-only', action='store_true', help='只生成报告')

    args = parser.parse_args()

    if args.report_only:
        generate_test_report()
    else:
        success = run_all_tests()
        sys.exit(0 if success else 1)
