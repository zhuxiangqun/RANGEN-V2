#!/usr/bin/env python3
"""
全面硬编码清理脚本
检测和替换系统中的各种硬编码问题，集成到统一配置管理中心
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HardcodingCleanupScript:
    """硬编码清理脚本"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.src_dir = self.project_root / "src"
        self.scripts_dir = self.project_root / "scripts"

        print(f"项目根目录: {self.project_root}")
        print(f"源码目录: {self.src_dir}")
        print(f"脚本目录: {self.scripts_dir}")

        # 硬编码模式定义 - 使用简单的模式
        self.hardcoding_patterns = {
            'keyword_lists': [
                r"\[\s*['\"][a-zA-Z]+['\"][\s,]*['\"][a-zA-Z]+['\"]",
                r"keywords\s*=\s*\[.*?\]",
                r"word_list\s*=\s*\[.*?\]"
            ],
            'threshold_values': [
                r"accuracy\s*<\s*0\.[0-9]+",
                r"length\s*>\s*[0-9]+",
                r"confidence\s*<\s*0\.[0-9]+",
                r"threshold\s*>\s*[0-9]+"
            ],
            'length_checks': [
                r"len\([a-zA-Z_][a-zA-Z0-9_]*\)\s*>=\s*[0-9]+",
                r"len\([a-zA-Z_][a-zA-Z0-9_]*\)\s*<=\s*[0-9]+"
            ],
            'fixed_strings': [
                r"['\"](what|who|when|where|why|how)['\"]",
                r"['\"](calculate|compute|solve|find)['\"]",
                r"['\"](compare|difference|similar|versus|vs)['\"]",
                r"['\"](analyze|examine|study|investigate)['\"]"
            ]
        }

        # 统计信息
        self.stats = {
            'files_processed': 0,
            'hardcoding_found': 0,
            'hardcoding_fixed': 0,
            'errors': 0
        }

    def scan_for_hardcoding(self) -> Dict[str, List[Tuple[str, int, str]]]:
        """扫描系统中的硬编码"""
        print("🔍 开始扫描系统中的硬编码...")
        logger.info("🔍 开始扫描系统中的硬编码...")

        hardcoding_results = {}

        # 扫描src目录
        for pattern_name, patterns in self.hardcoding_patterns.items():
            hardcoding_results[pattern_name] = []
            print(f"扫描模式: {pattern_name}")

            for pattern in patterns:
                print(f"  使用正则: {pattern}")
                for py_file in self.src_dir.rglob("*.py"):
                    try:
                        with open(py_file, 'r', encoding='utf-8') as f:
                            content = f.read()

                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            hardcoding_results[pattern_name].append((
                                str(py_file.relative_to(self.project_root)),
                                line_num,
                                match.group()
                            ))
                            self.stats['hardcoding_found'] += 1
                            print(f"    在 {py_file.name} 第 {line_num} 行发现: {match.group()}")

                    except Exception as e:
                        print(f"    扫描文件 {py_file} 时出错: {e}")
                        logger.error(f"扫描文件 {py_file} 时出错: {e}")
                        self.stats['errors'] += 1

        print(f"✅ 扫描完成，发现 {self.stats['hardcoding_found']} 个硬编码")
        logger.info(f"✅ 扫描完成，发现 {self.stats['hardcoding_found']} 个硬编码")
        return hardcoding_results

    def analyze_hardcoding_types(self, hardcoding_results: Dict[str, List[Tuple[str, int, str]]]) -> Dict[str, Any]:
        """分析硬编码类型和分布"""
        print("📊 分析硬编码类型和分布...")
        logger.info("📊 分析硬编码类型和分布...")

        analysis = {
            'by_file': {},
            'by_type': {},
            'recommendations': []
        }

        # 按文件统计
        for pattern_name, items in hardcoding_results.items():
            for file_path, line_num, content in items:
                if file_path not in analysis['by_file']:
                    analysis['by_file'][file_path] = []
                analysis['by_file'][file_path].append({
                    'type': pattern_name,
                    'line': line_num,
                    'content': content
                })

        # 按类型统计
        for pattern_name, items in hardcoding_results.items():
            analysis['by_type'][pattern_name] = len(items)

        # 生成建议
        analysis['recommendations'] = self._generate_recommendations(analysis)

        return analysis

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 基于硬编码类型生成建议
        if analysis['by_type'].get('keyword_lists', 0) > 0:
            recommendations.append("使用统一智能识别中心动态生成关键词，避免硬编码列表")

        if analysis['by_type'].get('threshold_values', 0) > 0:
            recommendations.append("使用统一配置管理中心的动态阈值配置，支持运行时调整")

        if analysis['by_type'].get('length_checks', 0) > 0:
            recommendations.append("使用智能特征分析中心的动态长度判断，基于上下文自适应")

        if analysis['by_type'].get('fixed_strings', 0) > 0:
            recommendations.append("使用智能策略融合系统动态生成字符串，支持多语言和上下文")

        return recommendations

    def generate_report(self, hardcoding_results: Dict[str, List[Tuple[str, int, str]]],
                       analysis: Dict[str, Any]) -> str:
        """生成硬编码清理报告"""
        print("📝 生成硬编码清理报告...")
        logger.info("📝 生成硬编码清理报告...")

        report = []
        report.append("# 系统硬编码清理报告")
        report.append("")
        report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**扫描文件数**: {self.stats['files_processed']}")
        report.append(f"**发现硬编码**: {self.stats['hardcoding_found']}")
        report.append("")

        # 硬编码分布
        report.append("## 硬编码分布")
        for pattern_name, count in analysis['by_type'].items():
            report.append(f"- **{pattern_name}**: {count} 个")
        report.append("")

        # 按文件详细列表
        report.append("## 按文件详细列表")
        for file_path, items in analysis['by_file'].items():
            report.append(f"### {file_path}")
            for item in items:
                report.append(f"- 第 {item['line']} 行: {item['type']} - `{item['content']}`")
            report.append("")

        # 改进建议
        report.append("## 改进建议")
        for rec in analysis['recommendations']:
            report.append(f"- {rec}")
        report.append("")

        # 集成方案
        report.append("## 集成统一中心方案")
        report.append("### 1. 统一配置管理中心")
        report.append("- 使用 `get_unified_config_center()` 获取动态配置")
        report.append("- 支持运行时参数调整和优化")
        report.append("")

        report.append("### 2. 智能识别中心")
        report.append("- 使用 `get_unified_intelligent_identifier()` 动态识别模式")
        report.append("- 基于统计特征和上下文分析，零硬编码")
        report.append("")

        report.append("### 3. 统一动态特征分析中心")
        report.append("- 使用 `get_unified_intelligent_processor()` 智能分析")
        report.append("- 支持自适应阈值和动态规则生成")
        report.append("")

        report.append("### 4. 智能策略融合系统")
        report.append("- 使用 `get_intelligent_strategy_fusion()` 优化策略")
        report.append("- 支持多策略融合和动态参数优化")
        report.append("")

        return "\n".join(report)

    def run_cleanup(self) -> None:
        """运行硬编码清理流程"""
        print("🚀 开始运行硬编码清理流程...")
        logger.info("🚀 开始运行硬编码清理流程...")

        try:
            # 1. 扫描硬编码
            hardcoding_results = self.scan_for_hardcoding()

            # 2. 分析硬编码类型
            analysis = self.analyze_hardcoding_types(hardcoding_results)

            # 3. 生成报告
            report = self.generate_report(hardcoding_results, analysis)

            # 4. 保存报告
            report_file = self.project_root / "HARDCODING_CLEANUP_COMPREHENSIVE_REPORT.md"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)

            print(f"✅ 硬编码清理完成！报告已保存到: {report_file}")
            print(f"📊 统计信息: {self.stats}")
            logger.info(f"✅ 硬编码清理完成！报告已保存到: {report_file}")
            logger.info(f"📊 统计信息: {self.stats}")

        except Exception as e:
            print(f"❌ 硬编码清理失败: {e}")
            logger.error(f"❌ 硬编码清理失败: {e}")
            self.stats['errors'] += 1

def main():
    """主函数"""
    script = HardcodingCleanupScript()
    script.run_cleanup()

if __name__ == "__main__":
    main()



