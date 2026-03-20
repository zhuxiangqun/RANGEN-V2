"""
质量保证系统

确保文档与代码同步的质量，包括验证准确性、检查完整性、评估一致性。
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import re
import json

from .documentation_sync_system import CodeEntity, DocumentationEntity, SyncReport

logger = logging.getLogger(__name__)


@dataclass
class QualityIssue:
    """质量问题"""
    issue_id: str
    issue_type: str  # accuracy, completeness, consistency, formatting
    severity: str  # critical, major, minor, info
    title: str
    description: str
    file_path: str
    line_number: Optional[int] = None
    suggested_fix: Optional[str] = None
    related_entities: List[str] = field(default_factory=list)
    detected_at: datetime = None


@dataclass
class QualityReport:
    """质量报告"""
    report_id: str
    generated_at: datetime
    overall_score: float  # 0-100
    total_issues: int
    issues_by_severity: Dict[str, int]
    issues_by_type: Dict[str, int]
    quality_issues: List[QualityIssue]
    recommendations: List[str]
    compliance_score: float  # 符合度评分


class DocumentationValidator:
    """文档验证器"""

    def __init__(self):
        self.validation_rules = self._load_validation_rules()

    async def validate_documentation_quality(self, report: SyncReport) -> QualityReport:
        """验证文档质量"""
        try:
            logger.info("开始文档质量验证")

            issues = []

            # 1. 验证准确性
            accuracy_issues = await self._validate_accuracy(report)
            issues.extend(accuracy_issues)

            # 2. 验证完整性
            completeness_issues = await self._validate_completeness(report)
            issues.extend(completeness_issues)

            # 3. 验证一致性
            consistency_issues = await self._validate_consistency(report)
            issues.extend(consistency_issues)

            # 4. 验证格式
            formatting_issues = await self._validate_formatting(report)
            issues.extend(formatting_issues)

            # 计算质量评分
            overall_score = self._calculate_overall_score(issues)
            compliance_score = self._calculate_compliance_score(issues)

            # 生成统计信息
            issues_by_severity = {}
            issues_by_type = {}

            for issue in issues:
                issues_by_severity[issue.severity] = issues_by_severity.get(issue.severity, 0) + 1
                issues_by_type[issue.issue_type] = issues_by_type.get(issue.issue_type, 0) + 1

            # 生成建议
            recommendations = await self._generate_recommendations(issues, report)

            quality_report = QualityReport(
                report_id=f"quality_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                generated_at=datetime.now(),
                overall_score=overall_score,
                total_issues=len(issues),
                issues_by_severity=issues_by_severity,
                issues_by_type=issues_by_type,
                quality_issues=issues,
                recommendations=recommendations,
                compliance_score=compliance_score
            )

            logger.info(f"文档质量验证完成: 总体评分 {overall_score:.1f}, 发现 {len(issues)} 个问题")
            return quality_report

        except Exception as e:
            logger.error(f"文档质量验证失败: {e}")
            raise

    async def _validate_accuracy(self, report: SyncReport) -> List[QualityIssue]:
        """验证准确性"""
        issues = []

        # 检查文档中引用的代码实体是否存在
        for doc_entity in report.doc_entities.values():
            doc_path = Path(doc_entity.file_path)

            try:
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 查找代码引用
                code_references = self._extract_code_references(content)

                for ref in code_references:
                    if ref not in report.code_entities:
                        issues.append(QualityIssue(
                            issue_id=f"accuracy_{len(issues)}",
                            issue_type="accuracy",
                            severity="major",
                            title="文档引用不存在的代码实体",
                            description=f"文档 '{doc_entity.title}' 引用了不存在的代码实体 '{ref}'",
                            file_path=doc_entity.file_path,
                            related_entities=[ref],
                            detected_at=datetime.now(),
                            suggested_fix=f"检查代码实体 '{ref}' 是否存在，或更新文档引用"
                        ))

            except Exception as e:
                issues.append(QualityIssue(
                    issue_id=f"accuracy_file_error_{len(issues)}",
                    issue_type="accuracy",
                    severity="critical",
                    title="文档文件读取失败",
                    description=f"无法读取文档文件 '{doc_entity.file_path}': {e}",
                    file_path=doc_entity.file_path,
                    detected_at=datetime.now()
                ))

        # 检查代码实体的文档覆盖
        documented_entities = set()
        for doc_entity in report.doc_entities.values():
            documented_entities.update(doc_entity.references)

        for code_name, code_entity in report.code_entities.items():
            if code_name not in documented_entities and self._should_be_documented(code_entity):
                issues.append(QualityIssue(
                    issue_id=f"accuracy_undocumented_{len(issues)}",
                    issue_type="accuracy",
                    severity="minor",
                    title="重要代码实体缺少文档",
                    description=f"代码实体 '{code_name}' ({code_entity.type}) 缺少相应的文档说明",
                    file_path=code_entity.file_path,
                    line_number=code_entity.line_number,
                    related_entities=[code_name],
                    detected_at=datetime.now(),
                    suggested_fix=f"为 {code_entity.type} '{code_name}' 添加文档说明"
                ))

        return issues

    async def _validate_completeness(self, report: SyncReport) -> List[QualityIssue]:
        """验证完整性"""
        issues = []

        # 检查关键文档是否存在
        required_docs = {
            'architecture_overview': '架构总览',
            'api_reference': 'API参考',
            'user_guide': '用户指南',
            'developer_guide': '开发者指南'
        }

        existing_doc_titles = {doc.title.lower() for doc in report.doc_entities.values()}

        for doc_key, doc_name in required_docs.items():
            found = any(doc_key in title or doc_name.lower() in title for title in existing_doc_titles)
            if not found:
                issues.append(QualityIssue(
                    issue_id=f"completeness_missing_{len(issues)}",
                    issue_type="completeness",
                    severity="major",
                    title="缺少关键文档",
                    description=f"项目缺少关键文档: {doc_name}",
                    file_path="docs/",
                    detected_at=datetime.now(),
                    suggested_fix=f"创建 {doc_name} 文档"
                ))

        # 检查API文档覆盖率
        api_entities = [e for e in report.code_entities.values() if e.type in ['class', 'function']]
        documented_apis = set()

        for doc_entity in report.doc_entities.values():
            if 'api' in doc_entity.title.lower() or 'reference' in doc_entity.title.lower():
                documented_apis.update(doc_entity.references)

        undocumented_apis = [e.name for e in api_entities if e.name not in documented_apis]
        if len(undocumented_apis) > len(api_entities) * 0.5:  # 超过50%的API未文档化
            issues.append(QualityIssue(
                issue_id=f"completeness_api_coverage_{len(issues)}",
                issue_type="completeness",
                severity="major",
                title="API文档覆盖不完整",
                description=f"{len(undocumented_apis)}/{len(api_entities)} 个API实体缺少文档",
                file_path="docs/",
                related_entities=undocumented_apis[:10],  # 只显示前10个
                detected_at=datetime.now(),
                suggested_fix="完善API文档，提高覆盖率"
            ))

        return issues

    async def _validate_consistency(self, report: SyncReport) -> List[QualityIssue]:
        """验证一致性"""
        issues = []

        # 检查术语一致性
        terminology_violations = await self._check_terminology_consistency(report)
        issues.extend(terminology_violations)

        # 检查版本一致性
        version_inconsistencies = await self._check_version_consistency(report)
        issues.extend(version_inconsistencies)

        # 检查引用一致性
        reference_issues = await self._check_reference_consistency(report)
        issues.extend(reference_issues)

        return issues

    async def _validate_formatting(self, report: SyncReport) -> List[QualityIssue]:
        """验证格式"""
        issues = []

        for doc_entity in report.doc_entities.values():
            doc_path = Path(doc_entity.file_path)

            try:
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.splitlines()

                # 检查Markdown格式
                if doc_path.suffix.lower() == '.md':
                    formatting_issues = self._check_markdown_formatting(lines, doc_entity.file_path)
                    issues.extend(formatting_issues)

                # 检查文档长度
                if len(content.strip()) < 100:  # 文档过短
                    issues.append(QualityIssue(
                        issue_id=f"formatting_too_short_{len(issues)}",
                        issue_type="formatting",
                        severity="minor",
                        title="文档内容过短",
                        description=f"文档 '{doc_entity.title}' 内容过短 ({len(content)} 字符)",
                        file_path=doc_entity.file_path,
                        detected_at=datetime.now(),
                        suggested_fix="完善文档内容，提供更详细的信息"
                    ))

                # 检查是否有TODO或FIXME标记
                todo_count = content.upper().count('TODO') + content.upper().count('FIXME')
                if todo_count > 0:
                    issues.append(QualityIssue(
                        issue_id=f"formatting_todos_{len(issues)}",
                        issue_type="formatting",
                        severity="info",
                        title="文档包含待办事项",
                        description=f"文档 '{doc_entity.title}' 包含 {todo_count} 个TODO/FIXME标记",
                        file_path=doc_entity.file_path,
                        detected_at=datetime.now(),
                        suggested_fix="处理文档中的待办事项，或将其移到专门的任务列表"
                    ))

            except Exception as e:
                issues.append(QualityIssue(
                    issue_id=f"formatting_read_error_{len(issues)}",
                    issue_type="formatting",
                    severity="critical",
                    title="文档格式检查失败",
                    description=f"无法检查文档 '{doc_entity.title}' 的格式: {e}",
                    file_path=doc_entity.file_path,
                    detected_at=datetime.now()
                ))

        return issues

    def _check_markdown_formatting(self, lines: List[str], file_path: str) -> List[QualityIssue]:
        """检查Markdown格式"""
        issues = []

        # 检查标题层级
        heading_levels = []
        for i, line in enumerate(lines):
            if line.strip().startswith('#'):
                level = len(line.split()[0]) if line.split() else 0
                heading_levels.append((level, i + 1, line.strip()))

        # 检查标题层级跳跃
        for i in range(1, len(heading_levels)):
            current_level = heading_levels[i][0]
            prev_level = heading_levels[i-1][0]

            if current_level > prev_level + 1:
                issues.append(QualityIssue(
                    issue_id=f"formatting_heading_jump_{len(issues)}",
                    issue_type="formatting",
                    severity="minor",
                    title="标题层级跳跃",
                    description=f"第 {heading_levels[i][1]} 行的标题从级别 {prev_level} 跳跃到级别 {current_level}",
                    file_path=file_path,
                    line_number=heading_levels[i][1],
                    detected_at=datetime.now(),
                    suggested_fix="调整标题层级，确保层级递进合理"
                ))

        # 检查是否有孤立的代码块
        in_code_block = False
        for i, line in enumerate(lines):
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
            elif in_code_block and not line.strip() and i > 0 and not lines[i-1].strip().startswith('```'):
                # 代码块中的空行，可能影响格式
                pass

        return issues

    async def _check_terminology_consistency(self, report: SyncReport) -> List[QualityIssue]:
        """检查术语一致性"""
        issues = []

        # 定义标准术语映射
        standard_terms = {
            '智能体': ['agent', '智能代理', 'AI代理'],
            '架构': ['architecture', '系统架构'],
            '同步': ['sync', 'synchronization'],
            '质量': ['quality', '品质']
        }

        # 检查文档中的术语使用
        for doc_entity in report.doc_entities.values():
            try:
                with open(doc_entity.file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                for standard_term, variants in standard_terms.items():
                    # 检查是否混用不同变体
                    found_variants = []
                    for variant in variants:
                        if variant.lower() in content.lower():
                            found_variants.append(variant)

                    if len(found_variants) > 1:
                        issues.append(QualityIssue(
                            issue_id=f"consistency_terminology_{len(issues)}",
                            issue_type="consistency",
                            severity="minor",
                            title="术语使用不一致",
                            description=f"文档 '{doc_entity.title}' 中混用了术语 '{standard_term}' 的不同变体: {', '.join(found_variants)}",
                            file_path=doc_entity.file_path,
                            detected_at=datetime.now(),
                            suggested_fix=f"统一使用术语 '{standard_term}'，避免混用变体"
                        ))

            except Exception as e:
                logger.error(f"检查术语一致性失败 {doc_entity.file_path}: {e}")

        return issues

    async def _check_version_consistency(self, report: SyncReport) -> List[QualityIssue]:
        """检查版本一致性"""
        issues = []

        # 这里可以检查不同文档中版本号的一致性
        # 暂时跳过实现
        return issues

    async def _check_reference_consistency(self, report: SyncReport) -> List[QualityIssue]:
        """检查引用一致性"""
        issues = []

        # 检查文档间的交叉引用
        doc_references = {}
        for doc_entity in report.doc_entities.values():
            doc_references[doc_entity.title] = doc_entity.references

        # 检查是否有文档引用了不存在的其他文档
        for doc_title, references in doc_references.items():
            doc_entity = report.doc_entities.get(doc_title)
            if not doc_entity:
                continue

            for ref in references:
                # 如果引用看起来像文档标题，但不在文档列表中
                if ref.endswith('.md') or '文档' in ref:
                    if ref not in report.doc_entities and not Path(ref).exists():
                        issues.append(QualityIssue(
                            issue_id=f"consistency_broken_ref_{len(issues)}",
                            issue_type="consistency",
                            severity="major",
                            title="文档引用不存在",
                            description=f"文档 '{doc_title}' 引用了不存在的文档 '{ref}'",
                            file_path=doc_entity.file_path,
                            detected_at=datetime.now(),
                            suggested_fix=f"检查文档引用 '{ref}' 是否正确，或创建相应的文档"
                        ))

        return issues

    def _extract_code_references(self, content: str) -> List[str]:
        """提取代码引用"""
        references = []

        # 正则表达式匹配各种代码引用模式
        patterns = [
            r'`([A-Za-z_][A-Za-z0-9_]*)`',  # `ClassName` 或 `function_name`
            r'class\s+([A-Za-z_][A-Za-z0-9_]*)',  # class ClassName
            r'def\s+([A-Za-z_][A-Za-z0-9_]*)',  # def function_name
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            references.extend(matches)

        return list(set(references))  # 去重

    def _should_be_documented(self, entity: CodeEntity) -> bool:
        """判断实体是否应该被文档化"""
        # 公开类和函数应该被文档化
        if entity.type == 'class' and not entity.name.startswith('_'):
            return True
        if entity.type == 'function' and not entity.name.startswith('_'):
            return True

        # 重要的内部实现也可能需要文档
        important_patterns = ['Agent', 'Manager', 'System', 'Coordinator']
        for pattern in important_patterns:
            if pattern in entity.name:
                return True

        return False

    def _calculate_overall_score(self, issues: List[QualityIssue]) -> float:
        """计算总体质量评分"""
        if not issues:
            return 100.0

        # 根据问题严重程度计算扣分
        severity_weights = {
            'critical': 10,
            'major': 5,
            'minor': 2,
            'info': 0.5
        }

        total_deduction = sum(severity_weights.get(issue.severity, 1) for issue in issues)
        score = max(0, 100 - total_deduction)

        return round(score, 1)

    def _calculate_compliance_score(self, issues: List[QualityIssue]) -> float:
        """计算符合度评分"""
        # 基于文档标准和最佳实践的符合度
        critical_issues = [i for i in issues if i.severity == 'critical']
        major_issues = [i for i in issues if i.severity == 'major']

        if critical_issues:
            return 20.0  # 有严重问题
        elif major_issues:
            return 60.0  # 有主要问题
        elif issues:
            return 85.0  # 只有小问题
        else:
            return 100.0  # 完全符合

    async def _generate_recommendations(self, issues: List[QualityIssue], report: SyncReport) -> List[str]:
        """生成建议"""
        recommendations = []

        # 根据问题类型生成建议
        accuracy_issues = [i for i in issues if i.issue_type == 'accuracy']
        if accuracy_issues:
            recommendations.append(f"解决 {len(accuracy_issues)} 个准确性问题，确保文档引用正确的代码实体")

        completeness_issues = [i for i in issues if i.issue_type == 'completeness']
        if completeness_issues:
            recommendations.append(f"完善文档完整性，补充 {len(completeness_issues)} 个缺失的关键文档")

        consistency_issues = [i for i in issues if i.issue_type == 'consistency']
        if consistency_issues:
            recommendations.append(f"统一术语和格式，确保文档一致性")

        formatting_issues = [i for i in issues if i.issue_type == 'formatting']
        if formatting_issues:
            recommendations.append(f"改进文档格式和结构，提供更好的阅读体验")

        # 基于同步状态生成建议
        if report.sync_status == 'out_of_sync':
            recommendations.append("定期执行文档同步，确保文档与代码保持最新")

        if report.conflicts:
            recommendations.append(f"解决 {len(report.conflicts)} 个同步冲突，保持文档准确性")

        return recommendations

    def _load_validation_rules(self) -> Dict[str, Any]:
        """加载验证规则"""
        # 这里可以从配置文件加载验证规则
        return {
            'required_documentation': [
                'architecture_overview',
                'api_reference',
                'user_guide',
                'developer_guide'
            ],
            'terminology_standards': {
                '智能体': ['agent', '智能代理'],
                '架构': ['architecture'],
                '同步': ['sync', 'synchronization']
            },
            'quality_thresholds': {
                'min_document_length': 100,
                'max_todo_items': 5,
                'required_api_coverage': 0.8
            }
        }


class QualityAssuranceSystem:
    """质量保证系统"""

    def __init__(self):
        self.validator = DocumentationValidator()
        self.quality_history: List[QualityReport] = []
        self.baseline_score = 80.0  # 质量基准分数

    async def perform_quality_check(self, sync_report: SyncReport) -> QualityReport:
        """执行质量检查"""
        try:
            logger.info("开始质量保证检查")

            # 执行质量验证
            quality_report = await self.validator.validate_documentation_quality(sync_report)

            # 保存到历史
            self.quality_history.append(quality_report)

            # 记录质量趋势
            await self._record_quality_trends(quality_report)

            # 检查是否需要告警
            await self._check_quality_alerts(quality_report)

            logger.info(f"质量检查完成: 总体评分 {quality_report.overall_score:.1f}")
            return quality_report

        except Exception as e:
            logger.error(f"质量检查失败: {e}")
            raise

    async def get_quality_trends(self, days: int = 30) -> Dict[str, Any]:
        """获取质量趋势"""
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)

        recent_reports = [
            report for report in self.quality_history
            if report.generated_at.timestamp() > cutoff_date
        ]

        if not recent_reports:
            return {'error': '没有足够的历史数据'}

        # 计算趋势
        scores = [r.overall_score for r in recent_reports]
        trend = 'stable'

        if len(scores) >= 2:
            if scores[-1] > scores[0] + 5:
                trend = 'improving'
            elif scores[-1] < scores[0] - 5:
                trend = 'declining'

        return {
            'period_days': days,
            'reports_count': len(recent_reports),
            'current_score': scores[-1] if scores else 0,
            'average_score': sum(scores) / len(scores) if scores else 0,
            'trend': trend,
            'score_range': {
                'min': min(scores) if scores else 0,
                'max': max(scores) if scores else 0
            }
        }

    async def generate_quality_report_markdown(self, quality_report: QualityReport) -> str:
        """生成质量报告的Markdown格式"""
        lines = []

        lines.append("# 文档质量报告")
        lines.append("")
        lines.append(f"**报告ID**: {quality_report.report_id}")
        lines.append(f"**生成时间**: {quality_report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**总体评分**: {quality_report.overall_score:.1f}/100")
        lines.append(f"**符合度评分**: {quality_report.compliance_score:.1f}/100")
        lines.append("")

        lines.append("## 📊 问题统计")
        lines.append("")
        lines.append(f"- 总问题数: {quality_report.total_issues}")
        lines.append("")

        if quality_report.issues_by_severity:
            lines.append("### 按严重程度")
            for severity, count in quality_report.issues_by_severity.items():
                severity_icon = {"critical": "🔴", "major": "🟠", "minor": "🟡", "info": "ℹ️"}.get(severity, "❓")
                lines.append(f"- {severity_icon} {severity}: {count}")
            lines.append("")

        if quality_report.issues_by_type:
            lines.append("### 按问题类型")
            for issue_type, count in quality_report.issues_by_type.items():
                lines.append(f"- {issue_type}: {count}")
            lines.append("")

        if quality_report.quality_issues:
            lines.append("## 🔍 详细问题")
            lines.append("")

            # 按严重程度排序
            sorted_issues = sorted(quality_report.quality_issues,
                                 key=lambda x: ['critical', 'major', 'minor', 'info'].index(x.severity))

            for issue in sorted_issues[:20]:  # 最多显示20个问题
                severity_icon = {"critical": "🔴", "major": "🟠", "minor": "🟡", "info": "ℹ️"}.get(issue.severity, "❓")
                lines.append(f"### {severity_icon} {issue.title}")
                lines.append("")
                lines.append(f"**文件**: {issue.file_path}")
                if issue.line_number:
                    lines.append(f"**行号**: {issue.line_number}")
                lines.append(f"**严重程度**: {issue.severity}")
                lines.append(f"**描述**: {issue.description}")
                if issue.suggested_fix:
                    lines.append(f"**建议修复**: {issue.suggested_fix}")
                if issue.related_entities:
                    lines.append(f"**相关实体**: {', '.join(issue.related_entities)}")
                lines.append("")

            if len(quality_report.quality_issues) > 20:
                lines.append(f"*... 还有 {len(quality_report.quality_issues) - 20} 个问题*")
                lines.append("")

        if quality_report.recommendations:
            lines.append("## 💡 改进建议")
            lines.append("")
            for rec in quality_report.recommendations:
                lines.append(f"- {rec}")
            lines.append("")

        # 评分解释
        lines.append("## 📋 评分说明")
        lines.append("")
        if quality_report.overall_score >= 90:
            lines.append("🎉 **优秀**: 文档质量很高，基本符合所有标准")
        elif quality_report.overall_score >= 75:
            lines.append("✅ **良好**: 文档质量良好，存在少量可改进之处")
        elif quality_report.overall_score >= 60:
            lines.append("⚠️ **一般**: 文档质量一般，需要重点改进")
        else:
            lines.append("❌ **较差**: 文档质量需要大幅改进")
        lines.append("")

        return "\n".join(lines)

    async def _record_quality_trends(self, report: QualityReport):
        """记录质量趋势"""
        try:
            trend_file = Path('data/quality_trends.jsonl')

            trend_record = {
                'timestamp': report.generated_at.isoformat(),
                'overall_score': report.overall_score,
                'compliance_score': report.compliance_score,
                'total_issues': report.total_issues,
                'issues_by_severity': report.issues_by_severity,
                'issues_by_type': report.issues_by_type
            }

            with open(trend_file, 'a', encoding='utf-8') as f:
                json.dump(trend_record, f, ensure_ascii=False)
                f.write('\n')

        except Exception as e:
            logger.error(f"记录质量趋势失败: {e}")

    async def _check_quality_alerts(self, report: QualityReport):
        """检查质量告警"""
        alerts = []

        # 严重问题告警
        critical_issues = report.issues_by_severity.get('critical', 0)
        if critical_issues > 0:
            alerts.append(f"🚨 发现 {critical_issues} 个严重质量问题，需要立即处理")

        # 评分下降告警
        if len(self.quality_history) >= 2:
            prev_score = self.quality_history[-2].overall_score
            current_score = report.overall_score

            if current_score < prev_score - 10:
                alerts.append(f"⚠️ 文档质量评分下降 {prev_score - current_score:.1f} 分")

        # 低于基准分数告警
        if report.overall_score < self.baseline_score:
            alerts.append(f"⚠️ 文档质量评分 {report.overall_score:.1f} 低于基准分数 {self.baseline_score}")

        # 输出告警
        for alert in alerts:
            logger.warning(alert)

    async def export_quality_report(self, quality_report: QualityReport, output_path: str):
        """导出质量报告"""
        markdown_content = await self.generate_quality_report_markdown(quality_report)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        logger.info(f"质量报告已导出到: {output_path}")


# 全局单例实例
_quality_assurance = None

def get_quality_assurance_system() -> QualityAssuranceSystem:
    """获取质量保证系统实例"""
    global _quality_assurance
    if _quality_assurance is None:
        _quality_assurance = QualityAssuranceSystem()
    return _quality_assurance
