#!/usr/bin/env python3
"""
Guardrail Tests - 护栏机制自动化测试套件

测试基于文章洞见实现的护栏机制：
1. Builder/Reviewer 角色分离
2. ADR 决策记录
3. Review Pipeline 分级评审
4. 工具加载策略
"""
import sys
import asyncio
import unittest
from typing import Any, Dict

sys.path.insert(0, '/Users/apple/workdata/person/zy/RANGEN-main(syu-python)')


class TestAgentRoleRegistry(unittest.TestCase):
    """测试 Agent 角色注册"""
    
    def setUp(self):
        from src.core.agent_role_registry import AgentRoleRegistry
        # Reset singleton
        AgentRoleRegistry._instance = None
        self.registry = AgentRoleRegistry()
    
    def test_role_summary(self):
        """测试角色统计"""
        summary = self.registry.get_role_summary()
        
        self.assertIn('builders', summary)
        self.assertIn('reviewers', summary)
        self.assertIn('coordinators', summary)
        
        self.assertEqual(summary['builders'], 23)
        self.assertEqual(summary['reviewers'], 4)
        self.assertEqual(summary['coordinators'], 3)
        self.assertEqual(summary['total'], 30)
    
    def test_is_reviewer(self):
        """测试是否为 Reviewer"""
        self.assertTrue(self.registry.is_reviewer("validation_agent"))
        self.assertTrue(self.registry.is_reviewer("quality_controller"))
        self.assertTrue(self.registry.is_reviewer("citation_agent"))
        self.assertTrue(self.registry.is_reviewer("audit_agent"))
        
        # Builder 不应该是 Reviewer
        self.assertFalse(self.registry.is_reviewer("reasoning_agent"))
        self.assertFalse(self.registry.is_reviewer("engineering_agent"))
    
    def test_is_builder(self):
        """测试是否为 Builder"""
        self.assertTrue(self.registry.is_builder("reasoning_agent"))
        self.assertTrue(self.registry.is_builder("engineering_agent"))
        self.assertTrue(self.registry.is_builder("design_agent"))
        
        # Reviewer 不应该是 Builder
        self.assertFalse(self.registry.is_builder("validation_agent"))
        self.assertFalse(self.registry.is_builder("quality_controller"))
    
    def test_get_agents_by_role(self):
        """测试按角色获取 Agent"""
        reviewers = self.registry.get_reviewers()
        reviewer_names = [r.agent_name for r in reviewers]
        
        self.assertIn("validation_agent", reviewer_names)
        self.assertIn("quality_controller", reviewer_names)
        self.assertIn("citation_agent", reviewer_names)
        self.assertIn("audit_agent", reviewer_names)
        
        builders = self.registry.get_builders()
        self.assertEqual(len(builders), 23)
    
    def test_get_classification(self):
        """测试获取完整分类信息"""
        classification = self.registry.get_classification("validation_agent")
        
        self.assertIsNotNone(classification)
        self.assertEqual(classification.agent_name, "validation_agent")
        self.assertEqual(classification.role.value, "reviewer")


class TestADRSystem(unittest.TestCase):
    """测试 ADR 决策记录系统"""
    
    def setUp(self):
        from src.core.adr_registry import ADRRegistry, ADRStatus
        # Reset singleton
        ADRRegistry._instance = None
        self.registry = ADRRegistry()
    
    def test_create_adr(self):
        """测试创建 ADR"""
        from src.core.adr_registry import create_adr, ADRStatus
        
        adr = create_adr(
            adr_id="TEST-001",
            title="Test ADR",
            background="Test background",
            decision="Test decision",
            consequences="Test consequences"
        )
        
        self.assertEqual(adr.adr_id, "TEST-001")
        self.assertEqual(adr.status, ADRStatus.PROPOSED)
        self.registry.add(adr)
        
        retrieved = self.registry.get("TEST-001")
        self.assertEqual(retrieved.title, "Test ADR")
    
    def test_get_active_adrs(self):
        """测试获取活跃 ADR"""
        from src.core.adr_registry import create_adr, ADRStatus
        
        # 添加不同状态的 ADR
        adr1 = create_adr("TEST-001", "Active", "bg", "dec", "cons")
        adr1.status = ADRStatus.ACCEPTED
        
        adr2 = create_adr("TEST-002", "Proposed", "bg", "dec", "cons")
        
        adr3 = create_adr("TEST-003", "Deprecated", "bg", "dec", "cons")
        adr3.status = ADRStatus.DEPRECATED
        
        self.registry.add(adr1)
        self.registry.add(adr2)
        self.registry.add(adr3)
        
        active = self.registry.get_active()
        self.assertEqual(len(active), 2)
    
    def test_search_adrs(self):
        """测试搜索 ADR"""
        from src.core.adr_registry import create_adr
        
        adr1 = create_adr(
            "TEST-001", "Tool Loading Decision",
            "Background about tools", "Use skill first", "Good performance"
        )
        adr2 = create_adr(
            "TEST-002", "Role Separation",
            "Background about roles", "Split builders and reviewers", "Clear boundaries"
        )
        
        self.registry.add(adr1)
        self.registry.add(adr2)
        
        results = self.registry.search("skill")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].adr_id, "TEST-001")
        
        results = self.registry.search("builders")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].adr_id, "TEST-002")


class TestReviewPipeline(unittest.TestCase):
    """测试评审流水线"""
    
    def setUp(self):
        from src.core.review_pipeline import ReviewPipeline, ReviewLevel
        self.pipeline = ReviewPipeline(name="test")
        self.ReviewLevel = ReviewLevel
    
    def test_default_criteria(self):
        """测试默认评审标准"""
        self.assertIn(self.ReviewLevel.L0_AUTO, self.pipeline.criteria)
        self.assertIn(self.ReviewLevel.L1_SELF, self.pipeline.criteria)
        self.assertIn(self.ReviewLevel.L2_PEER, self.pipeline.criteria)
        self.assertIn(self.ReviewLevel.L3_EXPERT, self.pipeline.criteria)
        
        # L0 应有 3 个标准
        l0_criteria = self.pipeline.criteria[self.ReviewLevel.L0_AUTO]
        self.assertGreaterEqual(len(l0_criteria), 3)
    
    async def test_basic_review(self):
        """测试基本评审"""
        from src.core.review_pipeline import ReviewLevel, ReviewResult
        
        # 模拟一个待评审的产物
        artifact = {
            "name": "test_code.py",
            "content": "def hello(): print('world')",
            "format": "python"
        }
        
        report = await self.pipeline.review(
            artifact_name="test_code.py",
            artifact_content=artifact,
            level=ReviewLevel.L0_AUTO,
            intent_statement="Create a simple hello function",
            temp_implementation=""
        )
        
        self.assertIsNotNone(report)
        self.assertEqual(report.artifact_name, "test_code.py")
        self.assertEqual(report.review_level, ReviewLevel.L0_AUTO)
        self.assertIn(report.result, [ReviewResult.PASS, ReviewResult.PASS_WITH_WARNINGS])
    
    def test_review_summary(self):
        """测试评审统计"""
        summary = self.pipeline.get_summary()
        
        self.assertIn('total', summary)
        self.assertEqual(summary['total'], 0)


class TestBuilderReviewerWorkflow(unittest.TestCase):
    """测试 Builder/Reviewer 工作流集成"""
    
    def test_role_based_routing(self):
        """测试基于角色的路由"""
        from src.core.agent_role_registry import (
            AgentRoleRegistry, AgentRole, is_builder, is_reviewer
        )
        
        # 验证角色判断函数
        self.assertTrue(is_builder("reasoning_agent"))
        self.assertFalse(is_builder("validation_agent"))
        
        self.assertTrue(is_reviewer("validation_agent"))
        self.assertFalse(is_reviewer("reasoning_agent"))
    
    def test_reviewer_agents_exist(self):
        """测试 Reviewer Agent 都存在"""
        from src.core.agent_role_registry import AgentRoleRegistry, AgentRole
        
        registry = AgentRoleRegistry()
        
        # 4 个核心 Reviewer
        core_reviewers = [
            "validation_agent",
            "quality_controller", 
            "citation_agent",
            "audit_agent"
        ]
        
        for name in core_reviewers:
            role = registry.get_role(name)
            self.assertEqual(role, AgentRole.REVIEWER, f"{name} should be REVIEWER")


class TestGuardrailIntegration(unittest.TestCase):
    """测试护栏机制集成"""
    
    def test_pipeline_with_registry(self):
        """测试 Pipeline 与 Registry 集成"""
        from src.core.review_pipeline import ReviewPipeline, ReviewLevel
        from src.core.agent_role_registry import get_agent_role_registry, AgentRole
        
        pipeline = ReviewPipeline(name="integration_test")
        registry = get_agent_role_registry()
        
        # 验证 Reviewer 可用于 L2 评审
        reviewers = registry.get_reviewers()
        self.assertGreater(len(reviewers), 0)
        
        # 验证 Reviewer 数量足以支撑评审
        self.assertGreaterEqual(len(reviewers), 2)
    
    def test_adr_documents_review_criteria(self):
        """测试 ADR 记录了评审标准"""
        from src.core.adr_examples import initialize_sample_adrs
        from src.core.adr_registry import get_adr_registry, ADRStatus
        
        initialize_sample_adrs()
        registry = get_adr_registry()
        
        # ADR-003 应该是关于评审的
        adr_003 = registry.get("ADR-003")
        self.assertIsNotNone(adr_003)
        self.assertIn("评审", adr_003.title)


def run_tests():
    """运行所有测试"""
    # 初始化 ADR 示例
    from src.core.adr_examples import initialize_sample_adrs
    initialize_sample_adrs()
    
    # 运行测试
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestAgentRoleRegistry))
    suite.addTests(loader.loadTestsFromTestCase(TestADRSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestReviewPipeline))
    suite.addTests(loader.loadTestsFromTestCase(TestBuilderReviewerWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestGuardrailIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    if success:
        print("\n✅ 所有护栏机制测试通过!")
    else:
        print("\n❌ 部分测试失败")
        sys.exit(1)
