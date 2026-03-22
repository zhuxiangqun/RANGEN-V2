#!/usr/bin/env python3
"""
测试技能质量感知协作功能
验证第一阶段实施：技能质量数据结构和协作方法
"""

import sys
import os
import asyncio
import logging
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_skill_quality_data_structures():
    """测试技能质量数据结构"""
    logger.info("测试技能质量数据结构...")
    
    try:
        # 导入相关类
        from src.core.enhanced_collaboration_coordinator import (
            SkillQualityInfo,
            CollaborationMessage,
            EnhancedCollaborationMode
        )
        
        # 测试SkillQualityInfo数据类
        skill_quality = SkillQualityInfo(
            skill_id="python_programming",
            quality_score=0.85,
            confidence_score=0.9,
            evaluation_dimensions={"practicality": 0.8, "accuracy": 0.9}
        )
        
        assert skill_quality.skill_id == "python_programming"
        assert skill_quality.quality_score == 0.85
        assert skill_quality.confidence_score == 0.9
        assert "practicality" in skill_quality.evaluation_dimensions
        assert skill_quality.evaluated_at is not None
        
        logger.info(f"✓ SkillQualityInfo测试通过: {skill_quality}")
        
        # 测试CollaborationMessage包含技能质量字段
        message = CollaborationMessage(
            message_id="test_message_001",
            sender_id="test_sender",
            message_type="skill_quality_report",
            payload={"test": "data"},
            skill_quality=skill_quality,
            confidence_score=0.8
        )
        
        assert message.message_id == "test_message_001"
        assert message.skill_quality == skill_quality
        assert message.confidence_score == 0.8
        assert message.sender_id == "test_sender"
        
        logger.info(f"✓ CollaborationMessage技能质量字段测试通过")
        
        return True
        
    except Exception as e:
        logger.error(f"技能质量数据结构测试失败: {e}", exc_info=True)
        return False

async def test_skill_quality_agent_selection():
    """测试技能质量Agent筛选"""
    logger.info("测试技能质量Agent筛选...")
    
    try:
        from src.core.enhanced_collaboration_coordinator import (
            EnhancedCollaborationCoordinator,
            get_enhanced_collaboration_coordinator
        )
        
        # 创建协调器实例
        coordinator = EnhancedCollaborationCoordinator(
            enable_real_time_communication=False  # 禁用实时通信简化测试
        )
        
        # 测试技能质量筛选
        required_skills = ["python_programming", "data_analysis"]
        
        qualified_agents = await coordinator._select_agents_by_skill_quality(
            required_skills=required_skills,
            min_quality_score=0.7,
            min_confidence_score=0.6
        )
        
        # 验证返回结果
        assert isinstance(qualified_agents, list)
        logger.info(f"技能质量筛选结果: {qualified_agents}")
        
        # 根据模拟数据，agent_001应该被选中（具备python_programming和data_analysis）
        # agent_002应该不被选中（缺少data_analysis）
        assert "agent_001" in qualified_agents
        assert len(qualified_agents) >= 1
        
        # 测试更高阈值
        high_threshold_agents = await coordinator._select_agents_by_skill_quality(
            required_skills=["python_programming"],
            min_quality_score=0.9,  # 更高阈值
            min_confidence_score=0.8
        )
        
        logger.info(f"高阈值筛选结果: {high_threshold_agents}")
        
        # 清理
        await coordinator.cleanup()
        
        logger.info("✓ 技能质量Agent筛选测试通过")
        return True
        
    except Exception as e:
        logger.error(f"技能质量Agent筛选测试失败: {e}", exc_info=True)
        return False

async def test_skill_quality_aware_collaboration():
    """测试技能质量感知协作"""
    logger.info("测试技能质量感知协作...")
    
    try:
        from src.core.enhanced_collaboration_coordinator import (
            EnhancedCollaborationCoordinator,
            EnhancedCollaborationMode
        )
        
        # 创建协调器实例
        coordinator = EnhancedCollaborationCoordinator(
            enable_real_time_communication=False  # 禁用实时通信简化测试
        )
        
        # 测试技能质量感知协作
        task_description = "测试任务：使用Python进行数据分析"
        required_skills = ["python_programming", "data_analysis"]
        
        result = await coordinator.coordinate_skill_quality_aware_collaboration(
            task_description=task_description,
            required_skills=required_skills,
            collaboration_mode=EnhancedCollaborationMode.ADAPTIVE,
            timeout=10.0  # 短超时
        )
        
        # 验证返回结果结构
        assert isinstance(result, dict)
        assert "collaboration_id" in result
        assert "skill_quality_aware" in result
        assert result["skill_quality_aware"] is True
        assert "required_skills" in result
        assert result["required_skills"] == required_skills
        assert "qualified_agents" in result
        
        logger.info(f"技能质量感知协作结果:")
        logger.info(f"  协作ID: {result.get('collaboration_id')}")
        logger.info(f"  成功: {result.get('success', False)}")
        logger.info(f"  符合条件的Agent: {result.get('qualified_agents', [])}")
        logger.info(f"  所需技能: {result.get('required_skills', [])}")
        
        # 测试无匹配技能的情况
        no_match_result = await coordinator.coordinate_skill_quality_aware_collaboration(
            task_description="需要不存在技能的任务",
            required_skills=["non_existent_skill"],
            collaboration_mode=EnhancedCollaborationMode.ADAPTIVE,
            timeout=5.0
        )
        
        assert no_match_result.get("success", True) is False  # 应该失败
        assert "error" in no_match_result
        logger.info(f"无匹配技能测试: {no_match_result.get('error', 'N/A')}")
        
        # 清理
        await coordinator.cleanup()
        
        logger.info("✓ 技能质量感知协作测试通过")
        return True
        
    except Exception as e:
        logger.error(f"技能质量感知协作测试失败: {e}", exc_info=True)
        return False

async def test_integration_with_existing_system():
    """测试与现有系统集成"""
    logger.info("测试与现有系统集成...")
    
    try:
        # 测试导入和实例化
        from src.core.enhanced_collaboration_coordinator import (
            EnhancedCollaborationCoordinator,
            SkillQualityInfo,
            CollaborationMessage,
            EnhancedCollaborationMode
        )
        
        # 测试全局实例获取
        from src.core.enhanced_collaboration_coordinator import (
            get_enhanced_collaboration_coordinator
        )
        
        coordinator = get_enhanced_collaboration_coordinator(
            enable_real_time_communication=False
        )
        
        assert coordinator is not None
        logger.info(f"✓ 全局协调器实例获取成功")
        
        # 测试数据结构兼容性
        message = CollaborationMessage(
            message_id="integration_test",
            sender_id="test",
            message_type="test",
            payload={}
        )
        
        # 验证新增字段默认值
        assert message.skill_quality is None
        assert message.confidence_score == 0.0
        
        logger.info("✓ 数据结构向后兼容性测试通过")
        
        return True
        
    except Exception as e:
        logger.error(f"系统集成测试失败: {e}", exc_info=True)
        return False

async def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("技能质量感知协作 - 第一阶段实施测试")
    logger.info("=" * 60)
    
    test_results = []
    
    # 运行测试
    test_results.append(("数据结构测试", await test_skill_quality_data_structures()))
    test_results.append(("Agent筛选测试", await test_skill_quality_agent_selection()))
    test_results.append(("协作功能测试", await test_skill_quality_aware_collaboration()))
    test_results.append(("系统集成测试", await test_integration_with_existing_system()))
    
    # 汇总结果
    logger.info("=" * 60)
    logger.info("测试结果汇总:")
    
    all_passed = True
    for test_name, passed in test_results:
        status = "✅ 通过" if passed else "❌ 失败"
        logger.info(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        logger.info("🎉 所有测试通过！第一阶段实施成功。")
        logger.info("")
        logger.info("下一步建议:")
        logger.info("1. 实现技能质量数据库集成")
        logger.info("2. 扩展技能质量评估维度")
        logger.info("3. 优化协作消息中的技能质量字段")
        logger.info("4. 集成到现有Skill Factory工作流")
    else:
        logger.error("⚠️ 部分测试失败，需要检查实现。")
    
    return all_passed

if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    
    # 根据测试结果退出
    sys.exit(0 if success else 1)