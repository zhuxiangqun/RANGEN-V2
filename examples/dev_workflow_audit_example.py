#!/usr/bin/env python3
"""
开发工作流审核 (DevWorkflowAudit) 使用示例

演示如何将代码审核能力集成到开发流程:
- 独立使用 DevWorkflowAudit 进行代码审核
- 危险模式检测与自定义规则
- 与 ChiefAgent 集成: 审核后执行、统计、自进化学习
"""

import asyncio
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def example_standalone_audit():
    """示例1: 独立使用 DevWorkflowAudit"""
    print("\n" + "=" * 60)
    print("示例1: 独立使用 DevWorkflowAudit")
    print("=" * 60)

    from src.core.dev_workflow_audit import (
        DevWorkflowAudit,
        AuditLevel,
        RiskLevel,
        get_dev_audit,
        quick_audit,
    )

    # 方式 A: 直接创建实例
    audit = DevWorkflowAudit(
        audit_level=AuditLevel.STANDARD,
        chief_agent=None,
        auto_sanitize=True,
    )

    safe_code = "x = 1 + 2\nprint(x)"
    result = await audit.audit_code(safe_code)
    print(f"安全代码审核: passed={result.passed}, risk={result.risk_level.value}")
    print(f"  建议: {result.suggestions}")

    dangerous_code = "import os; os.system('rm -rf /')"
    result2 = await audit.audit_code(dangerous_code)
    print(f"危险代码审核: passed={result2.passed}, risk={result2.risk_level.value}")
    for issue in result2.issues[:3]:
        print(f"  - [{issue.get('risk_level')}] {issue.get('description')}")

    # 方式 B: 快速审核 (默认单例)
    quick_result = await quick_audit("eval('1+1')")
    print(f"\nquick_audit(eval): passed={quick_result.passed}")


async def example_custom_rules():
    """示例2: 添加自定义审核规则"""
    print("\n" + "=" * 60)
    print("示例2: 自定义审核规则")
    print("=" * 60)

    from src.core.dev_workflow_audit import DevWorkflowAudit, AuditLevel

    audit = DevWorkflowAudit(audit_level=AuditLevel.STANDARD)

    audit.add_custom_rule(
        name="no_hardcoded_secret",
        pattern=r"password\s*=\s*['\"][^'\"]+['\"]",
        risk_level="high",
        description="禁止硬编码密码",
        suggestion="使用环境变量或配置中心",
    )

    code_with_secret = "password = 'my_secret_123'"
    result = await audit.audit_code(code_with_secret)
    print(f"含硬编码密码的代码: passed={result.passed}")
    for issue in result.issues:
        if issue.get("type") == "custom":
            print(f"  自定义规则命中: {issue.get('rule_name')} - {issue.get('description')}")


async def example_chief_agent_integration():
    """示例3: 与 ChiefAgent 集成 (审核 + 审核后执行)"""
    print("\n" + "=" * 60)
    print("示例3: ChiefAgent 集成")
    print("=" * 60)

    from src.agents.chief_agent import ChiefAgent

    chief = ChiefAgent(enable_audit=True, enable_quality_control=False)
    if not chief.is_dev_audit_enabled():
        print("  (开发审核未启用，跳过)")
        return

    # 仅审核
    code = "result = 2 + 2"
    audit_result = await chief.audit_code(code)
    if audit_result:
        print(f"ChiefAgent.audit_code: passed={audit_result.passed}, risk={audit_result.risk_level.value}")

    # 审核并执行 (演示: 执行函数仅返回代码长度)
    def dummy_execute(safe_code: str, ctx: dict):
        return {"length": len(safe_code), "preview": safe_code[:80]}

    run_result = await chief.audit_and_execute(
        code="x = 1",
        execute_func=dummy_execute,
        context={},
    )
    print(f"audit_and_execute 结果: success={run_result.get('success')}, result={run_result.get('result')}")

    # 统计
    stats = chief.get_dev_audit_stats()
    print(f"开发审核统计: {stats}")


async def example_audit_levels():
    """示例4: 不同审核级别"""
    print("\n" + "=" * 60)
    print("示例4: 审核级别 (BASIC / STANDARD / STRICT)")
    print("=" * 60)

    from src.core.dev_workflow_audit import DevWorkflowAudit, AuditLevel

    code = "from os import *\nprint('hello')"  # import * 在 STANDARD 会报质量建议

    for level in [AuditLevel.BASIC, AuditLevel.STANDARD]:
        audit = DevWorkflowAudit(audit_level=level)
        result = await audit.audit_code(code)
        issues_count = len(result.issues)
        print(f"  {level.value}: passed={result.passed}, issues={issues_count}")


async def example_learn_from_rejection():
    """示例5: 从拒绝中学习 (自进化集成)"""
    print("\n" + "=" * 60)
    print("示例5: learn_from_rejection (自进化)")
    print("=" * 60)

    from src.core.dev_workflow_audit import DevWorkflowAudit, AuditLevel

    audit = DevWorkflowAudit(audit_level=AuditLevel.STANDARD, chief_agent=None)
    initial_rules = len(audit.custom_rules)

    await audit.learn_from_rejection(
        rejected_code="dangerous_custom_op()",
        reason="该操作在历史运行中导致故障",
    )
    print(f"  学习前自定义规则数: {initial_rules}, 学习后: {len(audit.custom_rules)}")


def example_linter_checks():
    """示例6: 运行 Linter 发现项目中的静态检查错误

    说明: audit_code() 只对「即将执行的代码片段」做危险/规范检查，不会跑 pylint。
    项目里已有的 linter 错误需用 run_linter_checks() 或 CI 中 pylint src/ 发现。
    """
    print("\n" + "=" * 60)
    print("示例6: run_linter_checks (发现项目 linter 错误)")
    print("=" * 60)

    from src.core.dev_workflow_audit import DevWorkflowAudit

    audit = DevWorkflowAudit()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = [os.path.join(root, "src", "core", "dev_workflow_audit.py")]
    result = audit.run_linter_checks(paths, linters=["pylint"])
    total = result["summary"]["total"]
    print(f"  扫描: {paths[0]}")
    print(f"  pylint 问题数: {total}")
    if result["issues"]:
        for i in result["issues"][:5]:
            print(f"    - L{i.get('line')} [{i.get('symbol')}] {i.get('message', '')[:60]}")
    else:
        print("  (无问题或 pylint 未安装)")


async def main():
    print("\n🔒 DevWorkflowAudit 开发工作流审核 - 使用示例")
    await example_standalone_audit()
    await example_custom_rules()
    await example_audit_levels()
    await example_learn_from_rejection()
    example_linter_checks()
    await example_chief_agent_integration()
    print("\n✅ 示例运行完成\n")


if __name__ == "__main__":
    asyncio.run(main())
