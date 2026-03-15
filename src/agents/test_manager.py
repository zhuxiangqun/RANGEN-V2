#!/usr/bin/env python3
"""
测试经理 (Test Manager)
负责测试计划制定、测试执行、缺陷管理和质量评估
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging


logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """测试用例"""
    case_id: str
    title: str
    description: str
    test_type: str  # unit, integration, e2e, performance, security
    priority: str  # critical, high, medium, low
    preconditions: List[str]
    test_steps: List[str]
    expected_results: List[str]
    automated: bool = False
    assigned_to: str = ""
    status: str = "draft"  # draft, ready, in_progress, passed, failed, blocked


@dataclass
class TestPlan:
    """测试计划"""
    plan_id: str
    name: str
    description: str
    scope: str
    test_strategy: str
    test_environment: str
    test_cases: List[TestCase] = field(default_factory=list)
    start_date: str = ""
    end_date: str = ""
    resources: Dict[str, Any] = field(default_factory=dict)
    risks: List[str] = field(default_factory=list)


@dataclass
class Defect:
    """缺陷"""
    defect_id: str
    title: str
    description: str
    severity: str  # critical, major, minor, trivial
    priority: str  # urgent, high, medium, low
    status: str  # open, in_progress, resolved, closed, rejected
    test_case_id: str
    steps_to_reproduce: List[str]
    actual_result: str
    expected_result: str
    assigned_to: str = ""
    created_by: str = ""
    created_at: str = ""
    resolved_at: str = ""


@dataclass
class QualityMetrics:
    """质量指标"""
    test_coverage: float  # 测试覆盖率
    pass_rate: float  # 通过率
    defect_count: int  # 缺陷数量
    critical_defects: int  # 严重缺陷
    reopened_defects: int  # 重新打开的缺陷
    execution_time: float  # 执行时间
    automation_rate: float  # 自动化率


class TestManager:
    """测试经理 - 负责测试全生命周期管理"""
    
    def __init__(self):
        self.agent_id = "test_manager"
        self.role_name = "テストマネージャー"
        self.role_name_en = "Test Manager"
        self.domain_expertise = "テスト管理 / 品質保証 / テスト自動化"
        
        # 工作成果
        self.test_plans: Dict[str, TestPlan] = {}
        self.defects: Dict[str, Defect] = {}
        self.quality_metrics: Optional[QualityMetrics] = None
        
        logger.info(f"TestManager initialized: {self.agent_id}")
    
    def get_system_prompt(self) -> str:
        """获取系统提示"""
        return f"""
{self.role_name}（{self.role_name_en}）として動作してください。

【役割】
あなたの任務は、ソフトウェア品質を保証するためのテスト管理を行うことです。

【具体的な業務】
1. テスト計画制定
   - テスト戦略の策定
   - テスト範囲の定義
   - リソース計画
   - リスク評価

2. テスト実行管理
   - テストケースの作成・管理
   - テストスケジュールの管理
   - テスト環境の準備
   - テスト進捗の追跡

3. 欠陥管理
   - 欠陥の報告と追跡
   - 重大度の評価
   - 解決状況の管理

4. 品質評価
   - テストCoverage分析
   - 品質メトリクスの算出
   - 改善提案

【必須遵守事項】
1. 全ての出力は日本語で行ってください
2. テスト管理のベストプラクティスに従ってください
3. 正確なメトリクスと分析を提供してください

【対応可能なタスク】
- テスト計画の作成
- テストケースの設計
- テスト実行の管理
- 欠陥の追跡
- 品質評価レポートの作成
"""
    
    # ==================== 测试计划制定 ====================
    
    def create_test_plan(
        self,
        name: str,
        description: str,
        scope: str,
        test_strategy: str,
        test_environment: str,
        start_date: str = "",
        end_date: str = ""
    ) -> TestPlan:
        """创建测试计划"""
        plan_id = f"TP-{len(self.test_plans) + 1:04d}"
        
        test_plan = TestPlan(
            plan_id=plan_id,
            name=name,
            description=description,
            scope=scope,
            test_strategy=test_strategy,
            test_environment=test_environment,
            start_date=start_date or datetime.now().strftime("%Y-%m-%d"),
            end_date=end_date
        )
        
        self.test_plans[plan_id] = test_plan
        logger.info(f"Created test plan: {plan_id}")
        
        return test_plan
    
    def add_test_case(
        self,
        plan_id: str,
        title: str,
        description: str,
        test_type: str,
        priority: str,
        preconditions: List[str],
        test_steps: List[str],
        expected_results: List[str],
        automated: bool = False
    ) -> Optional[TestCase]:
        """添加测试用例"""
        if plan_id not in self.test_plans:
            logger.error(f"Test plan not found: {plan_id}")
            return None
        
        plan = self.test_plans[plan_id]
        case_id = f"{plan_id}-TC-{len(plan.test_cases) + 1:03d}"
        
        test_case = TestCase(
            case_id=case_id,
            title=title,
            description=description,
            test_type=test_type,
            priority=priority,
            preconditions=preconditions,
            test_steps=test_steps,
            expected_results=expected_results,
            automated=automated,
            status="ready"
        )
        
        plan.test_cases.append(test_case)
        logger.info(f"Added test case: {case_id}")
        
        return test_case
    
    # ==================== 测试执行 ====================
    
    def execute_test_case(self, case_id: str, actual_results: Dict[str, Any]) -> Dict[str, Any]:
        """执行测试用例"""
        # 查找测试用例
        test_case = None
        for plan in self.test_plans.values():
            for tc in plan.test_cases:
                if tc.case_id == case_id:
                    test_case = tc
                    break
        
        if not test_case:
            return {"error": f"Test case not found: {case_id}"}
        
        # 验证结果
        passed = True
        for i, expected in enumerate(test_case.expected_results):
            if i < len(actual_results.get("results", [])):
                actual = actual_results["results"][i]
                if str(actual) != str(expected):
                    passed = False
                    break
        
        # 更新状态
        test_case.status = "passed" if passed else "failed"
        
        # 如果失败，创建缺陷
        if not passed:
            defect = self.create_defect(
                title=f"テスト失敗: {test_case.title}",
                description=actual_results.get("error", "期待結果と実際の結果が一致しません"),
                severity="major" if test_case.priority == "critical" else "minor",
                priority="high" if test_case.priority == "critical" else "medium",
                test_case_id=case_id,
                steps_to_reproduce=test_case.test_steps,
                actual_result=str(actual_results.get("results", [])),
                expected_result=str(test_case.expected_results)
            )
            return {
                "status": "failed",
                "test_case": test_case,
                "defect_id": defect.defect_id if defect else None
            }
        
        return {
            "status": "passed",
            "test_case": test_case
        }
    
    def get_test_execution_summary(self, plan_id: str) -> Dict[str, Any]:
        """获取测试执行摘要"""
        if plan_id not in self.test_plans:
            return {"error": f"Test plan not found: {plan_id}"}
        
        plan = self.test_plans[plan_id]
        
        total = len(plan.test_cases)
        passed = sum(1 for tc in plan.test_cases if tc.status == "passed")
        failed = sum(1 for tc in plan.test_cases if tc.status == "failed")
        blocked = sum(1 for tc in plan.test_cases if tc.status == "blocked")
        not_executed = sum(1 for tc in plan.test_cases if tc.status in ["draft", "ready"])
        
        return {
            "plan_id": plan_id,
            "total": total,
            "passed": passed,
            "failed": failed,
            "blocked": blocked,
            "not_executed": not_executed,
            "pass_rate": (passed / total * 100) if total > 0 else 0
        }
    
    # ==================== 缺陷管理 ====================
    
    def create_defect(
        self,
        title: str,
        description: str,
        severity: str,
        priority: str,
        test_case_id: str,
        steps_to_reproduce: List[str],
        actual_result: str,
        expected_result: str
    ) -> Defect:
        """创建缺陷"""
        defect_id = f"DEF-{len(self.defects) + 1:04d}"
        
        defect = Defect(
            defect_id=defect_id,
            title=title,
            description=description,
            severity=severity,
            priority=priority,
            status="open",
            test_case_id=test_case_id,
            steps_to_reproduce=steps_to_reproduce,
            actual_result=actual_result,
            expected_result=expected_result,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        self.defects[defect_id] = defect
        logger.info(f"Created defect: {defect_id}")
        
        return defect
    
    def update_defect_status(self, defect_id: str, status: str) -> bool:
        """更新缺陷状态"""
        if defect_id not in self.defects:
            return False
        
        self.defects[defect_id].status = status
        
        if status == "resolved":
            self.defects[defect_id].resolved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        logger.info(f"Updated defect {defect_id} status to: {status}")
        return True
    
    def get_defect_summary(self) -> Dict[str, Any]:
        """获取缺陷汇总"""
        total = len(self.defects)
        open_defects = sum(1 for d in self.defects.values() if d.status == "open")
        in_progress = sum(1 for d in self.defects.values() if d.status == "in_progress")
        resolved = sum(1 for d in self.defects.values() if d.status == "resolved")
        
        critical = sum(1 for d in self.defects.values() if d.severity == "critical")
        major = sum(1 for d in self.defects.values() if d.severity == "major")
        
        return {
            "total": total,
            "open": open_defects,
            "in_progress": in_progress,
            "resolved": resolved,
            "critical": critical,
            "major": major
        }
    
    # ==================== 质量评估 ====================
    
    def calculate_quality_metrics(self, plan_id: str, total_lines: int = 0, covered_lines: int = 0) -> QualityMetrics:
        """计算质量指标"""
        if plan_id not in self.test_plans:
            return QualityMetrics(0, 0, 0, 0, 0, 0, 0)
        
        plan = self.test_plans[plan_id]
        total = len(plan.test_cases)
        
        if total == 0:
            return QualityMetrics(0, 0, 0, 0, 0, 0, 0)
        
        passed = sum(1 for tc in plan.test_cases if tc.status == "passed")
        failed = sum(1 for tc in plan.test_cases if tc.status == "failed")
        
        # 计算测试覆盖率
        coverage = (covered_lines / total_lines * 100) if total_lines > 0 else 0
        
        # 计算通过率
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        # 计算自动化率
        automated = sum(1 for tc in plan.test_cases if tc.automated)
        automation_rate = (automated / total * 100) if total > 0 else 0
        
        # 统计缺陷
        defect_count = len(self.defects)
        critical_defects = sum(1 for d in self.defects.values() if d.severity == "critical")
        
        self.quality_metrics = QualityMetrics(
            test_coverage=coverage,
            pass_rate=pass_rate,
            defect_count=defect_count,
            critical_defects=critical_defects,
            reopened_defects=0,
            execution_time=0,
            automation_rate=automation_rate
        )
        
        return self.quality_metrics
    
    def generate_quality_report(self, plan_id: str) -> str:
        """生成质量报告"""
        if plan_id not in self.test_plans:
            return "テスト計画が見つかりません"
        
        plan = self.test_plans[plan_id]
        execution_summary = self.get_test_execution_summary(plan_id)
        defect_summary = self.get_defect_summary()
        
        metrics = self.quality_metrics or self.calculate_quality_metrics(plan_id)
        
        report = f"""
============================================
        品質評価レポート
============================================

【テスト計画】
- 計画ID: {plan.plan_id}
- 名前: {plan.name}
- 説明: {plan.description}

【テスト実行サマリー】
- 総テストケース: {execution_summary['total']}
- 合格: {execution_summary['passed']}
- 失敗: {execution_summary['failed']}
- 未実行: {execution_summary['not_executed']}
- 合格率: {execution_summary['pass_rate']:.1f}%

【欠陥サマリー】
- 総欠陥数: {defect_summary['total']}
- オープン: {defect_summary['open']}
- 進行中: {defect_summary['in_progress']}
- 解決済み: {defect_summary['resolved']}
- 重大: {defect_summary['critical']}
- 主要: {defect_summary['major']}

【品質メトリクス】
- テストCoverage: {metrics.test_coverage:.1f}%
- 自動化率: {metrics.automation_rate:.1f}%
- 合格率: {metrics.pass_rate:.1f}%
- 重大欠陥数: {metrics.critical_defects}

============================================
"""
        return report
    
    # ==================== 快速演示 ====================
    
    def demo(self):
        """演示测试管理功能"""
        # 创建测试计划
        plan = self.create_test_plan(
            name="ユーザー管理システム テスト計画",
            description="ユーザー管理システムの品質保証",
            scope="ログイン機能、ユーザーCRUD、パスワード管理",
            test_strategy="ブラックボックステスト主体",
            test_environment="開発環境",
            start_date="2026-04-01",
            end_date="2026-04-30"
        )
        
        # 添加测试用例
        tc1 = self.add_test_case(
            plan_id=plan.plan_id,
            title="ユーザーログintest",
            description="有効な 자격 증명으로ログインできることを確認",
            test_type="integration",
            priority="critical",
            preconditions=["ユーザーが登録されている"],
            test_steps=["ログインページを開く", "ユーザー名を入力", "パスワードを入力", "ログインボタンをクリック"],
            expected_results=["ダッシュボードに表示される"],
            automated=True
        )
        
        tc2 = self.add_test_case(
            plan_id=plan.plan_id,
            title="ユーザー作成",
            description="新規ユーザーを作成できることを確認",
            test_type="integration",
            priority="high",
            preconditions=["管理者がログインしている"],
            test_steps=["ユーザー一覧を開く", "新規作成をクリック", "情報を入力", "保存をクリック"],
            expected_results=["ユーザーが追加される"],
            automated=True
        )
        
        # 执行测试
        result1 = self.execute_test_case(tc1.case_id, {"results": ["ダッシュボードに表示される"]})
        result2 = self.execute_test_case(tc2.case_id, {"results": [], "error": "システムエラー"})
        
        # 输出报告
        print(self.generate_quality_report(plan.plan_id))


# 全局实例
_test_manager: Optional[TestManager] = None


def get_test_manager() -> TestManager:
    """获取测试管理器实例"""
    global _test_manager
    if _test_manager is None:
        _test_manager = TestManager()
    return _test_manager
