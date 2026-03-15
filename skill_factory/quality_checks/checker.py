"""
Skill Factory 质量检查 Python 包装器

提供Python接口调用自动化质量检查脚本，并解析检查结果。
"""

import os
import subprocess
import sys
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json


class CheckStatus(Enum):
    """检查状态"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class CheckResult:
    """单个检查项结果"""
    name: str
    status: CheckStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityReport:
    """质量检查报告"""
    skill_dir: str
    overall_status: CheckStatus
    checks: List[CheckResult] = field(default_factory=list)
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)


class SkillQualityChecker:
    """技能质量检查器
    
    封装bash检查脚本，提供Python友好的接口。
    """
    
    def __init__(self, script_path: Optional[str] = None):
        """初始化检查器
        
        Args:
            script_path: 检查脚本路径，如果为None则使用默认路径
        """
        if script_path is None:
            # 默认脚本路径
            script_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(script_dir, "skill_check.sh")
        
        self.script_path = script_path
        if not os.path.exists(self.script_path):
            raise FileNotFoundError(f"检查脚本不存在: {self.script_path}")
        
        # 确保脚本有执行权限
        if not os.access(self.script_path, os.X_OK):
            os.chmod(self.script_path, 0o755)
    
    def check_skill(self, skill_dir: str) -> QualityReport:
        """检查技能目录
        
        Args:
            skill_dir: 技能目录路径
            
        Returns:
            QualityReport: 质量检查报告
        """
        if not os.path.isdir(skill_dir):
            raise ValueError(f"技能目录不存在: {skill_dir}")
        
        # 执行检查脚本
        try:
            result = subprocess.run(
                [self.script_path, skill_dir],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30  # 30秒超时
            )
            
            # 解析输出
            return self._parse_output(skill_dir, result)
            
        except subprocess.TimeoutExpired:
            return self._create_error_report(
                skill_dir, 
                "检查脚本执行超时（30秒）",
                CheckStatus.FAILED
            )
        except Exception as e:
            return self._create_error_report(
                skill_dir,
                f"检查脚本执行失败: {str(e)}",
                CheckStatus.FAILED
            )
    
    def _parse_output(self, skill_dir: str, result: subprocess.CompletedProcess) -> QualityReport:
        """解析脚本输出
        
        Args:
            skill_dir: 技能目录路径
            result: 子进程执行结果
            
        Returns:
            QualityReport: 解析后的报告
        """
        checks = []
        overall_status = CheckStatus.PASSED
        summary = ""
        recommendations = []
        
        # 按行解析输出
        lines = result.stdout.split('\n')
        error_lines = result.stderr.split('\n')
        
        # 收集所有行用于分析
        all_lines = lines + error_lines
        
        # 检查关键错误信息
        has_critical_error = False
        for line in all_lines:
            if "[ERROR]" in line:
                has_critical_error = True
                # 提取错误信息
                error_msg = line.split("[ERROR]", 1)[1].strip()
                checks.append(CheckResult(
                    name="关键检查",
                    status=CheckStatus.FAILED,
                    message=error_msg
                ))
            elif "[WARNING]" in line:
                # 提取警告信息
                warning_msg = line.split("[WARNING]", 1)[1].strip()
                checks.append(CheckResult(
                    name="警告检查",
                    status=CheckStatus.WARNING,
                    message=warning_msg
                ))
            elif "[SUCCESS]" in line:
                # 提取成功信息
                success_msg = line.split("[SUCCESS]", 1)[1].strip()
                checks.append(CheckResult(
                    name="成功检查",
                    status=CheckStatus.PASSED,
                    message=success_msg
                ))
        
        # 确定总体状态
        if result.returncode != 0 or has_critical_error:
            overall_status = CheckStatus.FAILED
            summary = "质量检查未通过"
            recommendations = [
                "修复所有[ERROR]级别的问题",
                "重新运行检查脚本确认修复"
            ]
        else:
            overall_status = CheckStatus.PASSED
            summary = "质量检查通过"
            recommendations = [
                "可以进入下一开发阶段",
                "建议完善文档和测试用例"
            ]
        
        # 如果没有检查项，添加默认检查项
        if not checks:
            checks.append(CheckResult(
                name="脚本执行",
                status=CheckStatus.PASSED if result.returncode == 0 else CheckStatus.FAILED,
                message=f"脚本执行完成，退出码: {result.returncode}"
            ))
        
        return QualityReport(
            skill_dir=skill_dir,
            overall_status=overall_status,
            checks=checks,
            summary=summary,
            recommendations=recommendations
        )
    
    def _create_error_report(self, skill_dir: str, error_message: str, status: CheckStatus) -> QualityReport:
        """创建错误报告
        
        Args:
            skill_dir: 技能目录路径
            error_message: 错误信息
            status: 检查状态
            
        Returns:
            QualityReport: 错误报告
        """
        return QualityReport(
            skill_dir=skill_dir,
            overall_status=status,
            checks=[
                CheckResult(
                    name="脚本执行",
                    status=status,
                    message=error_message
                )
            ],
            summary=f"检查失败: {error_message}",
            recommendations=[
                "检查脚本路径和权限",
                "确保Python环境正确",
                "检查技能目录是否存在"
            ]
        )
    
    def check_multiple_skills(self, skill_dirs: List[str]) -> Dict[str, QualityReport]:
        """批量检查多个技能
        
        Args:
            skill_dirs: 技能目录路径列表
            
        Returns:
            Dict[str, QualityReport]: 技能路径到报告的映射
        """
        reports = {}
        for skill_dir in skill_dirs:
            try:
                report = self.check_skill(skill_dir)
                reports[skill_dir] = report
            except Exception as e:
                reports[skill_dir] = self._create_error_report(
                    skill_dir,
                    f"检查过程中发生异常: {str(e)}",
                    CheckStatus.FAILED
                )
        
        return reports
    
    def generate_json_report(self, report: QualityReport) -> str:
        """生成JSON格式的报告
        
        Args:
            report: 质量检查报告
            
        Returns:
            str: JSON格式的报告
        """
        report_dict = {
            "skill_dir": report.skill_dir,
            "overall_status": report.overall_status.value,
            "summary": report.summary,
            "checks": [
                {
                    "name": check.name,
                    "status": check.status.value,
                    "message": check.message,
                    "details": check.details
                }
                for check in report.checks
            ],
            "recommendations": report.recommendations,
            "timestamp": os.path.getmtime(report.skill_dir) if os.path.exists(report.skill_dir) else None
        }
        
        return json.dumps(report_dict, ensure_ascii=False, indent=2)


# 快速使用示例
if __name__ == "__main__":
    # 测试现有技能
    checker = SkillQualityChecker()
    
    # 测试用例
    test_dirs = [
        "src/agents/skills/bundled/answer-generation",
        "src/agents/skills/bundled/rag-retrieval",
        "skill_factory"  # 这个应该会失败
    ]
    
    print("🧪 开始技能质量检查测试")
    print("=" * 50)
    
    for skill_dir in test_dirs:
        if os.path.exists(skill_dir):
            print(f"\n📁 检查技能: {skill_dir}")
            try:
                report = checker.check_skill(skill_dir)
                
                # 显示结果
                status_emoji = "✅" if report.overall_status == CheckStatus.PASSED else "❌"
                print(f"   总体状态: {status_emoji} {report.overall_status.value}")
                print(f"   总结: {report.summary}")
                
                # 显示检查项
                for check in report.checks[:3]:  # 只显示前3个
                    check_emoji = "✅" if check.status == CheckStatus.PASSED else "⚠️" if check.status == CheckStatus.WARNING else "❌"
                    print(f"   {check_emoji} {check.name}: {check.message[:80]}...")
                
                if len(report.checks) > 3:
                    print(f"   ... 还有 {len(report.checks) - 3} 个检查项")
                    
                # 生成JSON报告
                json_report = checker.generate_json_report(report)
                report_file = f"{skill_dir.replace('/', '_')}_quality_report.json"
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(json_report)
                print(f"   📄 JSON报告已保存到: {report_file}")
                
            except Exception as e:
                print(f"   ❌ 检查失败: {str(e)}")
        else:
            print(f"\n📁 技能目录不存在: {skill_dir}")
    
    print("\n" + "=" * 50)
    print("🎉 技能质量检查测试完成")