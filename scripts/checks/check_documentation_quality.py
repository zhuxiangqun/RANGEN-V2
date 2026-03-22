#!/usr/bin/env python3
"""
文档质量检查工具
检查文档的完整性、准确性和一致性
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from datetime import datetime

# 设置项目环境
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@dataclass
class DocumentationIssue:
    """文档问题"""
    file_path: str
    line_number: int
    issue_type: str  # 'missing', 'outdated', 'inconsistent', 'formatting'
    severity: str  # 'high', 'medium', 'low'
    description: str
    suggestion: str

@dataclass
class DocumentationQualityReport:
    """文档质量报告"""
    total_files: int
    issues_found: int
    quality_score: float
    issues: List[DocumentationIssue]
    recommendations: List[str]

class DocumentationQualityChecker:
    """文档质量检查器"""

    def __init__(self):
        self.doc_files = []
        self.issues = []
        self.quality_metrics = {}

    def check_documentation_quality(self) -> DocumentationQualityReport:
        """检查文档质量"""
        print("📋 开始文档质量检查...")

        # 发现文档文件
        self._discover_documentation_files()

        # 执行各种检查
        self._check_file_structure()
        self._check_content_completeness()
        self._check_cross_references()
        self._check_formatting_consistency()
        self._check_update_freshness()

        # 计算质量评分
        quality_score = self._calculate_quality_score()

        # 生成建议
        recommendations = self._generate_recommendations()

        report = DocumentationQualityReport(
            total_files=len(self.doc_files),
            issues_found=len(self.issues),
            quality_score=quality_score,
            issues=self.issues,
            recommendations=recommendations
        )

        return report

    def _discover_documentation_files(self):
        """发现文档文件"""
        print("   🔍 发现文档文件...")

        doc_dirs = ['docs', 'README.md', 'CONTRIBUTING.md', 'CHANGELOG.md']
        exclude_patterns = ['__pycache__', '.git', 'node_modules']

        for doc_dir in doc_dirs:
            path = project_root / doc_dir
            if path.is_file():
                self.doc_files.append(path)
            elif path.exists():
                for md_file in path.rglob('*.md'):
                    should_exclude = False
                    for pattern in exclude_patterns:
                        if pattern in str(md_file):
                            should_exclude = True
                            break
                    if not should_exclude:
                        self.doc_files.append(md_file)

        print(f"   ✅ 发现 {len(self.doc_files)} 个文档文件")

    def _check_file_structure(self):
        """检查文件结构"""
        print("   🔍 检查文件结构...")

        required_files = [
            'README.md',
            'docs/README.md',
            'docs/architecture/',
            'docs/usage/',
            'docs/api/'
        ]

        for required_file in required_files:
            path = project_root / required_file
            if not path.exists():
                self.issues.append(DocumentationIssue(
                    file_path=str(path),
                    line_number=0,
                    issue_type='missing',
                    severity='high',
                    description=f"缺少必需的文档文件: {required_file}",
                    suggestion=f"创建 {required_file} 文件"
                ))

    def _check_content_completeness(self):
        """检查内容完整性"""
        print("   🔍 检查内容完整性...")

        required_sections = [
            ('README.md', ['项目概述', '快速开始', '安装指南']),
            ('docs/README.md', ['文档导航', '快速开始', '架构与设计']),
        ]

        for file_path, sections in required_sections:
            full_path = project_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    for section in sections:
                        if section not in content:
                            self.issues.append(DocumentationIssue(
                                file_path=str(full_path),
                                line_number=0,
                                issue_type='missing',
                                severity='medium',
                                description=f"文档缺少必需章节: {section}",
                                suggestion=f"在 {file_path} 中添加 {section} 章节"
                            ))
                except Exception as e:
                    self.issues.append(DocumentationIssue(
                        file_path=str(full_path),
                        line_number=0,
                        issue_type='inconsistent',
                        severity='medium',
                        description=f"无法读取文档文件: {e}",
                        suggestion="检查文件编码和格式"
                    ))

    def _check_cross_references(self):
        """检查交叉引用"""
        print("   🔍 检查交叉引用...")

        for doc_file in self.doc_files:
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                for line_num, line in enumerate(lines, 1):
                    # 检查损坏的链接
                    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
                    matches = re.findall(link_pattern, line)

                    for match in matches:
                        link_text, link_url = match
                        if link_url.startswith('./') or link_url.startswith('../'):
                            # 检查相对链接是否存在
                            link_path = (doc_file.parent / link_url).resolve()
                            if not link_path.exists() and not link_url.endswith('/'):
                                self.issues.append(DocumentationIssue(
                                    file_path=str(doc_file),
                                    line_number=line_num,
                                    issue_type='inconsistent',
                                    severity='medium',
                                    description=f"损坏的相对链接: {link_url}",
                                    suggestion=f"修复或移除损坏的链接 {link_url}"
                                ))

            except Exception as e:
                self.issues.append(DocumentationIssue(
                    file_path=str(doc_file),
                    line_number=0,
                    issue_type='inconsistent',
                    severity='low',
                    description=f"检查交叉引用时出错: {e}",
                    suggestion="检查文件格式"
                ))

    def _check_formatting_consistency(self):
        """检查格式一致性"""
        print("   🔍 检查格式一致性...")

        for doc_file in self.doc_files:
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                # 检查标题格式
                for line_num, line in enumerate(lines, 1):
                    if line.startswith('#'):
                        # 检查标题下是否有空行（除非是文档末尾）
                        if line_num < len(lines) and lines[line_num].strip() and not lines[line_num].startswith('#'):
                            next_line = lines[line_num]
                            if next_line.strip() and not next_line.startswith(' ') and not next_line.startswith('\t'):
                                self.issues.append(DocumentationIssue(
                                    file_path=str(doc_file),
                                    line_number=line_num + 1,
                                    issue_type='formatting',
                                    severity='low',
                                    description="标题后缺少空行",
                                    suggestion="在标题后添加空行以提高可读性"
                                ))

                # 检查代码块格式
                in_code_block = False
                for line_num, line in enumerate(lines, 1):
                    if line.strip().startswith('```'):
                        in_code_block = not in_code_block
                    elif in_code_block and line.startswith(' ') and not line.startswith('   ') and not line.startswith('    '):
                        self.issues.append(DocumentationIssue(
                            file_path=str(doc_file),
                            line_number=line_num,
                            issue_type='formatting',
                            severity='low',
                            description="代码块缩进不一致",
                            suggestion="使用4个空格缩进代码块内容"
                        ))

            except Exception as e:
                self.issues.append(DocumentationIssue(
                    file_path=str(doc_file),
                    line_number=0,
                    issue_type='inconsistent',
                    severity='low',
                    description=f"检查格式时出错: {e}",
                    suggestion="检查文件格式"
                ))

    def _check_update_freshness(self):
        """检查更新时效性"""
        print("   🔍 检查更新时效性...")

        # 检查关键文档的更新时间
        critical_files = ['README.md', 'docs/README.md']
        current_time = datetime.now().timestamp()

        for file_name in critical_files:
            file_path = project_root / file_name
            if file_path.exists():
                file_mtime = file_path.stat().st_mtime
                days_since_update = (current_time - file_mtime) / (24 * 3600)

                if days_since_update > 30:  # 30天未更新
                    self.issues.append(DocumentationIssue(
                        file_path=str(file_path),
                        line_number=0,
                        issue_type='outdated',
                        severity='low',
                        description=".1f"
                        suggestion="更新文档以反映最新变化"
                    ))

    def _calculate_quality_score(self) -> float:
        """计算质量评分"""
        if not self.doc_files:
            return 0.0

        base_score = 100.0
        penalty_per_issue = {
            'high': 10.0,
            'medium': 5.0,
            'low': 1.0
        }

        for issue in self.issues:
            base_score -= penalty_per_issue.get(issue.severity, 1.0)

        # 确保分数不低于0
        return max(0.0, min(100.0, base_score))

    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 基于问题类型统计
        issue_types = {}
        for issue in self.issues:
            issue_types[issue.issue_type] = issue_types.get(issue.issue_type, 0) + 1

        if issue_types.get('missing', 0) > 0:
            recommendations.append(f"补充缺少的文档文件和章节 (发现 {issue_types['missing']} 个缺失项)")

        if issue_types.get('inconsistent', 0) > 0:
            recommendations.append(f"修复不一致的格式和链接 (发现 {issue_types['inconsistent']} 个问题)")

        if issue_types.get('formatting', 0) > 0:
            recommendations.append(f"统一文档格式规范 (发现 {issue_types['formatting']} 个格式问题)")

        # 通用建议
        recommendations.extend([
            "建立文档维护计划，定期更新和审查",
            "为主要功能添加使用示例和代码片段",
            "创建文档贡献指南，规范文档编写流程",
            "添加文档自动检查到CI/CD流程",
            "建立文档反馈机制，收集用户意见"
        ])

        return recommendations

    def generate_quality_report(self):
        """生成质量报告"""
        report = self.check_documentation_quality()

        print("📝 生成文档质量报告...")

        # 统计数据
        severity_counts = {'high': 0, 'medium': 0, 'low': 0}
        type_counts = {}

        for issue in report.issues:
            severity_counts[issue.severity] += 1
            type_counts[issue.issue_type] = type_counts.get(issue.issue_type, 0) + 1

        # 生成JSON报告
        json_report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_files': report.total_files,
                'issues_found': report.issues_found,
                'quality_score': report.quality_score,
                'severity_distribution': severity_counts,
                'type_distribution': type_counts
            },
            'issues': [
                {
                    'file': issue.file_path,
                    'line': issue.line_number,
                    'type': issue.issue_type,
                    'severity': issue.severity,
                    'description': issue.description,
                    'suggestion': issue.suggestion
                }
                for issue in report.issues
            ],
            'recommendations': report.recommendations
        }

        # 保存报告
        report_path = project_root / 'reports' / 'documentation_quality_report.json'
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, ensure_ascii=False, indent=2)

        # 生成文本报告
        self._generate_text_report(json_report)

        print(f"✅ 文档质量报告已保存: {report_path}")

    def _generate_text_report(self, json_report: Dict[str, Any]):
        """生成文本质量报告"""
        text_report = ".2f"".1f"f"""
RANGEN 文档质量检查报告
{'='*50}

检查时间: {json_report['timestamp']}

📊 总体概况
总文档文件: {json_report['summary']['total_files']}
发现问题: {json_report['summary']['issues_found']}
质量评分: {json_report['summary']['quality_score']:.1f}/100

🔍 问题分布
严重程度:
  高: {json_report['summary']['severity_distribution']['high']}
  中: {json_report['summary']['severity_distribution']['medium']}
  低: {json_report['summary']['severity_distribution']['low']}

问题类型:
"""

        for issue_type, count in json_report['summary']['type_distribution'].items():
            text_report += f"  {issue_type}: {count}\n"

        text_report += "\n⚠️  详细问题:\n"
        for i, issue in enumerate(json_report['issues'][:10], 1):  # 只显示前10个问题
            text_report += f"{i}. [{issue['severity'].upper()}] {issue['file']}:{issue['line']}\n"
            text_report += f"   {issue['description']}\n"
            text_report += f"   建议: {issue['suggestion']}\n\n"

        if len(json_report['issues']) > 10:
            text_report += f"   ... 还有 {len(json_report['issues']) - 10} 个问题\n"

        text_report += "\n💡 改进建议:\n"
        for i, rec in enumerate(json_report['recommendations'], 1):
            text_report += f"{i}. {rec}\n"

        # 保存文本报告
        text_path = project_root / 'reports' / 'documentation_quality_report.txt'
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text_report)

        print(f"✅ 文本质量报告已保存: {text_path}")

        # 打印关键指标
        print("\n" + "=" * 50)
        print("🎯 文档质量检查结果")
        print("=" * 50)
        print(".1f"
        print(f"📁 总文档文件: {json_report['summary']['total_files']}")
        print(f"⚠️  发现问题: {json_report['summary']['issues_found']}")

def main():
    """主函数"""
    checker = DocumentationQualityChecker()
    checker.generate_quality_report()

if __name__ == "__main__":
    main()
