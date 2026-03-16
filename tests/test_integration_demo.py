#!/usr/bin/env python3
"""
Demo: 完整系统验证测试

验证所有组件协同工作:
1. Agent 角色分类
2. ADR 决策记录
3. Review Pipeline 分级评审
4. 上下文传递协议
5. 判断力评价体系
"""
import sys
import asyncio

sys.path.insert(0, '/Users/apple/workdata/person/zy/RANGEN-main(syu-python)')


def test_1_agent_role_classification():
    """测试 1: Agent 角色分类"""
    print("\n" + "="*50)
    print("测试 1: Agent 角色分类")
    print("="*50)
    
    from src.core.agent_role_registry import get_agent_role_registry, AgentRole
    
    registry = get_agent_role_registry()
    summary = registry.get_role_summary()
    
    print(f"✅ Builder: {summary['builders']}")
    print(f"✅ Reviewer: {summary['reviewers']}")
    print(f"✅ Coordinator: {summary['coordinators']}")
    print(f"✅ Total: {summary['total']}")
    
    # 验证关键 Agent
    print("\n关键 Agent 角色验证:")
    print(f"  validation_agent -> {registry.get_role('validation_agent').value}")
    print(f"  reasoning_agent -> {registry.get_role('reasoning_agent').value}")
    print(f"  chief_agent -> {registry.get_role('chief_agent').value}")
    
    return True


def test_2_adr_system():
    """测试 2: ADR 决策记录"""
    print("\n" + "="*50)
    print("测试 2: ADR 决策记录")
    print("="*50)
    
    from src.core.adr_examples import initialize_sample_adrs
    from src.core.adr_registry import get_adr_registry
    
    initialize_sample_adrs()
    registry = get_adr_registry()
    
    active = registry.get_active()
    print(f"✅ 活跃 ADR: {len(active)}")
    
    for adr in active:
        print(f"  - {adr.adr_id}: {adr.title[:40]}... [{adr.status.value}]")
    
    # 测试搜索
    results = registry.search("skill")
    print(f"\n✅ 搜索 'skill': {len(results)} 条")
    
    return True


def test_3_review_pipeline():
    """测试 3: Review Pipeline"""
    print("\n" + "="*50)
    print("测试 3: Review Pipeline")
    print("="*50)
    
    from src.core.review_pipeline import ReviewPipeline, ReviewLevel
    
    pipeline = ReviewPipeline(name="demo")
    
    # 模拟一个产物
    artifact = {
        "name": "demo_code.py",
        "content": "def hello(): return 'world'",
        "format": "python"
    }
    
    # 执行 L0 评审
    async def run_review():
        report = await pipeline.review(
            artifact_name="demo_code.py",
            artifact_content=artifact,
            level=ReviewLevel.L0_AUTO,
            intent_statement="创建简单函数",
            temp_implementation="初始版本"
        )
        return report
    
    report = asyncio.run(run_review())
    
    print(f"✅ 评审结果: {report.result.value}")
    print(f"✅ 评分: {report.score:.1f}")
    print(f"✅ 发现: {len(report.findings)} 个")
    
    return True


def test_4_context_protocol():
    """测试 4: 上下文传递协议"""
    print("\n" + "="*50)
    print("测试 4: 上下文传递协议")
    print("="*50)
    
    from src.core.context_protocol import (
        ContextPassingProtocol, create_artifact_context
    )
    
    # 创建产物上下文
    context = create_artifact_context(
        name="demo_feature",
        type="code",
        problem="需要添加用户认证",
        goal="实现 JWT 认证",
        is_temp=False,
        criteria=["登录成功", "登出成功", "Token 有效期"]
    )
    
    # 验证上下文
    quality = ContextPassingProtocol.validate_context(context)
    print(f"✅ 上下文质量: {quality.value}")
    
    # 格式化为 Prompt
    prompt_part = ContextPassingProtocol.format_for_prompt(context)
    print(f"✅ Prompt 片段长度: {len(prompt_part)} 字符")
    
    # 模拟传递
    context.add_pass("Builder")
    context.add_pass("Reviewer")
    print(f"✅ 传递路径: {' -> '.join(context.passed_from)}")
    
    return True


def test_5_judgment_evaluation():
    """测试 5: 判断力评价"""
    print("\n" + "="*50)
    print("测试 5: 判断力评价")
    print("="*50)
    
    from src.core.judgment_evaluation import (
        JudgmentEvaluationSystem, JudgmentType
    )
    
    system = JudgmentEvaluationSystem()
    
    # 模拟判断记录
    system.record_judgment(
        agent_id="validation_agent",
        period="demo",
        judgment_type=JudgmentType.BLOCK,
        artifact_name="bad_code",
        reason="存在安全漏洞",
        is_correct=True
    )
    
    system.record_judgment(
        agent_id="validation_agent",
        period="demo",
        judgment_type=JudgmentType.APPROVE,
        artifact_name="good_code",
        reason="代码质量良好"
    )
    
    evaluation = system.get_evaluation("validation_agent", "demo")
    
    print(f"✅ 判断次数: {evaluation.judgments_made}")
    print(f"✅ 拦截次数: {evaluation.blocks_count}")
    print(f"✅ 批准次数: {evaluation.approvals_count}")
    print(f"✅ 判断准确率: {evaluation.judgment_accuracy:.1%}")
    
    # 生成报告
    report = system.generate_report("demo")
    print(f"\n{report[:200]}...")
    
    return True


def test_6_integration():
    """测试 6: 集成测试"""
    print("\n" + "="*50)
    print("测试 6: 完整集成")
    print("="*50)
    
    import asyncio
    
    from src.core.agent_role_registry import get_agent_role_registry, AgentRole
    from src.core.adr_examples import initialize_sample_adrs
    from src.core.review_pipeline import ReviewPipeline, ReviewLevel
    from src.core.judgment_evaluation import JudgmentEvaluationSystem, JudgmentType
    
    # 1. 获取 Reviewer Agents
    registry = get_agent_role_registry()
    reviewers = registry.get_reviewers()
    print(f"✅ 可用 Reviewers: {len(reviewers)}")
    
    # 2. 初始化 ADR
    initialize_sample_adrs()
    print("✅ ADR 已加载")
    
    # 3. 执行评审
    pipeline = ReviewPipeline(name="integration")
    
    async def run():
        return await pipeline.review(
            artifact_name="integration_test",
            artifact_content={"test": "data"},
            level=ReviewLevel.L2_PEER
        )
    
    report = asyncio.run(run())
    print(f"✅ 评审完成: {report.result.value}")
    
    # 4. 记录判断
    system = JudgmentEvaluationSystem()
    system.record_judgment(
        agent_id="integration_test",
        period="demo",
        judgment_type=JudgmentType.APPROVE,
        artifact_name="integration_result",
        reason="测试通过"
    )
    print(f"✅ 判断已记录")
    
    return True


def main():
    """运行所有测试"""
    print("\n" + "#"*50)
    print("# RANGEN 系统验证测试")
    print("#"*50)
    
    tests = [
        ("Agent 角色分类", test_1_agent_role_classification),
        ("ADR 决策记录", test_2_adr_system),
        ("Review Pipeline", test_3_review_pipeline),
        ("上下文传递协议", test_4_context_protocol),
        ("判断力评价", test_5_judgment_evaluation),
        ("完整集成", test_6_integration),
    ]
    
    results = []
    
    for name, test_fn in tests:
        try:
            result = test_fn()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} 失败: {e}")
            results.append((name, False))
    
    # 汇总
    print("\n" + "#"*50)
    print("# 测试结果汇总")
    print("#"*50)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过! 系统运行正常.")
    else:
        print("\n⚠️ 部分测试失败，请检查.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
