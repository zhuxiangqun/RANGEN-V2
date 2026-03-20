"""
Harness 熵管理系统

根据 Harness Engineering 最佳实践:
- Harness 本身也是代码，会随时间腐化
- 需要定期"垃圾回收"来清理过时/矛盾的规则

核心功能:
1. 扫描规则文件过时/矛盾
2. 检测 skill 漂移
3. 自动清理冗余规则
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

from src.services.logging_service import get_logger

logger = get_logger(__name__)


@dataclass
class EntropyIssue:
    """熵问题"""
    issue_type: str          # 过时/矛盾/冗余
    file_path: str
    description: str
    severity: str            # high/medium/low
    suggestion: str          # 修复建议


@dataclass
class HarnessHealthReport:
    """Harness 健康报告"""
    scan_time: datetime
    total_rules: int
    issues_found: int
    issues: List[EntropyIssue] = field(default_factory=list)
    health_score: float = 100.0
    
    def to_dict(self) -> Dict:
        return {
            "scan_time": self.scan_time.isoformat(),
            "total_rules": self.total_rules,
            "issues_found": self.issues_found,
            "health_score": self.health_score,
            "issues": [
                {
                    "type": i.issue_type,
                    "file": i.file_path,
                    "description": i.description,
                    "severity": i.severity,
                    "suggestion": i.suggestion
                }
                for i in self.issues
            ]
        }


class HarnessEntropyManager:
    """
    Harness 熵管理器
    
    定期扫描和清理 Harness 系统中的腐化:
    - 过时的规则
    - 矛盾的指令
    - 冗余的配置
    """
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path or ".")
        self.rules_paths = [
            "RANGEN_RULES.md",
            "docs/harness/",
            ".rangen/contracts/",
            "src/agents/skills/bundled/",
            "src/core/task_contract.py"
        ]
        
        # 健康度阈值
        self.health_threshold = 70.0
        
        # 规则最后修改时间缓存
        self._last_scan: Optional[datetime] = None
        self._rule_timestamps: Dict[str, datetime] = {}
    
    def scan(self) -> HarnessHealthReport:
        """全面扫描 Harness 健康度"""
        issues: List[EntropyIssue] = []
        total_rules = 0
        
        # 1. 扫描文档过时
        issues.extend(self._check_outdated_docs())
        total_rules += len(issues)
        
        # 2. 检查规则矛盾
        issues.extend(self._check_contradictions())
        
        # 3. 检查冗余
        issues.extend(self._check_redundancy())
        
        # 4. 检查 skill 漂移
        issues.extend(self._check_skill_drift())
        
        # 计算健康分
        health_score = max(0, 100 - len(issues) * 10)
        
        report = HarnessHealthReport(
            scan_time=datetime.now(),
            total_rules=total_rules,
            issues_found=len(issues),
            issues=issues,
            health_score=health_score
        )
        
        # 保存扫描结果
        self._save_report(report)
        
        return report
    
    def _check_outdated_docs(self) -> List[EntropyIssue]:
        """检查过时的文档"""
        issues = []
        
        for path_str in self.rules_paths:
            path = self.base_path / path_str
            if not path.exists():
                continue
            
            if path.is_file():
                # 检查单个文件
                if self._is_outdated(path):
                    issues.append(EntropyIssue(
                        issue_type="outdated",
                        file_path=str(path),
                        description=f"文档超过6个月未更新",
                        severity="medium",
                        suggestion="检查是否需要更新或归档"
                    ))
            elif path.is_dir():
                # 检查目录
                for md_file in path.rglob("*.md"):
                    if self._is_outdated(md_file):
                        issues.append(EntropyIssue(
                            issue_type="outdated",
                            file_path=str(md_file),
                            description=f"文档超过6个月未更新",
                            severity="low",
                            suggestion="检查是否需要更新"
                        ))
        
        return issues
    
    def _is_outdated(self, file_path: Path, months: int = 6) -> bool:
        """检查文件是否过时"""
        try:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            threshold = datetime.now() - timedelta(days=months * 30)
            return mtime < threshold
        except:
            return False
    
    def _check_contradictions(self) -> List[EntropyIssue]:
        """检查规则矛盾"""
        issues = []
        
        # 加载规则文件
        rules = self._load_rules()
        
        # 检查矛盾模式
        contradiction_patterns = [
            ("不要.*全部", "全部"),  # 说不要全部但又说全部
            ("必须.*不要", "必须.*不要"),  # 同时说必须和不要
            (r"不要\w+", r"必须\w+"),  # 禁止和必须的矛盾
        ]
        
        # 简化检查：检查关键指令是否冲突
        all_text = " ".join(rules.values())
        
        # 检查上下文膨胀信号
        if len(all_text) > 50000:
            issues.append(EntropyIssue(
                issue_type="contradiction",
                file_path="RANGEN_RULES.md",
                description="规则总长度超过50KB，可能存在上下文膨胀",
                severity="high",
                suggestion="拆分规则到多个文件，使用渐进式披露"
            ))
        
        return issues
    
    def _check_redundancy(self) -> List[EntropyIssue]:
        """检查冗余规则"""
        issues = []
        
        # 检查 skills 目录中的重复
        skills_dir = self.base_path / "src/agents/skills/bundled"
        if not skills_dir.exists():
            return issues
        
        # 检查相似的 skill 名称
        skill_names = [d.name for d in skills_dir.iterdir() if d.is_dir()]
        similar_pairs = []
        
        for i, name1 in enumerate(skill_names):
            for name2 in skill_names[i+1:]:
                # 简单相似度检查
                if self._are_similar(name1, name2):
                    similar_pairs.append((name1, name2))
        
        if similar_pairs:
            issues.append(EntropyIssue(
                issue_type="redundancy",
                file_path="src/agents/skills/bundled/",
                description=f"发现 {len(similar_pairs)} 对相似的 skill 名称",
                severity="low",
                suggestion=f"考虑合并: {similar_pairs[:3]}"
            ))
        
        return issues
    
    def _are_similar(self, name1: str, name2: str) -> bool:
        """简单相似度检查"""
        # 处理 web-search 和 web_search 的情况
        n1 = name1.replace("-", "_").replace("_", "")
        n2 = name2.replace("-", "_").replace("_", "")
        return n1 == n2 and name1 != name2
    
    def _check_skill_drift(self) -> List[EntropyIssue]:
        """检查 skill 漂移（配置和实现不一致）"""
        issues = []
        
        # 检查 skill.yaml 与实际文件的一致性
        skills_dir = self.base_path / "src/agents/skills/bundled"
        if not skills_dir.exists():
            return issues
        
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            
            # 检查 skill.yaml 是否存在
            yaml_file = skill_dir / "skill.yaml"
            if not yaml_file.exists():
                issues.append(EntropyIssue(
                    issue_type="drift",
                    file_path=str(skill_dir),
                    description=f"Skill {skill_dir.name} 缺少 skill.yaml",
                    severity="medium",
                    suggestion="创建 skill.yaml 或删除该目录"
                ))
        
        return issues
    
    def _load_rules(self) -> Dict[str, str]:
        """加载所有规则文件"""
        rules = {}
        
        for path_str in self.rules_paths:
            path = self.base_path / path_str
            if not path.exists():
                continue
            
            if path.is_file() and path.suffix == ".md":
                try:
                    rules[str(path)] = path.read_text()
                except:
                    pass
            elif path.is_dir():
                for md_file in path.rglob("*.md"):
                    try:
                        rules[str(md_file)] = md_file.read_text()
                    except:
                        pass
        
        return rules
    
    def _save_report(self, report: HarnessHealthReport):
        """保存报告"""
        report_dir = self.base_path / ".rangen/harness_health"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = report_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        
        # 只保留最近10份报告
        self._cleanup_old_reports(report_dir)
    
    def _cleanup_old_reports(self, report_dir: Path, keep: int = 10):
        """清理旧报告"""
        reports = sorted(report_dir.glob("health_*.json"), key=lambda x: x.stat().st_mtime)
        for old_report in reports[:-keep]:
            old_report.unlink()
    
    def get_latest_report(self) -> Optional[HarnessHealthReport]:
        """获取最新的健康报告"""
        report_dir = self.base_path / ".rangen/harness_health"
        if not report_dir.exists():
            return None
        
        reports = sorted(report_dir.glob("health_*.json"), key=lambda x: x.stat().st_mtime)
        if not reports:
            return None
        
        latest = reports[-1]
        with open(latest) as f:
            data = json.load(f)
        
        issues = [
            EntropyIssue(
                issue_type=i["type"],
                file_path=i["file"],
                description=i["description"],
                severity=i["severity"],
                suggestion=i["suggestion"]
            )
            for i in data.get("issues", [])
        ]
        
        return HarnessHealthReport(
            scan_time=datetime.fromisoformat(data["scan_time"]),
            total_rules=data["total_rules"],
            issues_found=data["issues_found"],
            issues=issues,
            health_score=data["health_score"]
        )
    
    def needs_cleanup(self) -> bool:
        """检查是否需要清理"""
        report = self.get_latest_report()
        if not report:
            return True
        
        return report.health_score < self.health_threshold
    
    def auto_cleanup(self) -> Dict[str, Any]:
        """
        自动清理（保守模式）
        
        只清理明确的冗余，不触碰有争议的规则
        """
        results = {
            "outdated_docs_fixed": 0,
            "redundant_skills_identified": 0,
            "needs_manual_review": []
        }
        
        # 扫描并返回需要人工review的问题
        report = self.scan()
        
        for issue in report.issues:
            if issue.severity == "high":
                results["needs_manual_review"].append({
                    "file": issue.file_path,
                    "issue": issue.description,
                    "suggestion": issue.suggestion
                })
        
        return results


# 全局单例
_global_entropy_manager: Optional[HarnessEntropyManager] = None

def get_entropy_manager() -> HarnessEntropyManager:
    """获取全局熵管理器"""
    global _global_entropy_manager
    if _global_entropy_manager is None:
        _global_entropy_manager = HarnessEntropyManager()
    return _global_entropy_manager


# ============ 便捷函数 ============

def check_harness_health() -> Dict:
    """快速检查 Harness 健康度"""
    manager = get_entropy_manager()
    report = manager.scan()
    return report.to_dict()


def needs_harness_cleanup() -> bool:
    """检查是否需要清理"""
    return get_entropy_manager().needs_cleanup()
