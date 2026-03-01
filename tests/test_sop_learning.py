#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOP学习系统测试

测试GenericAgent理念实现的SOP学习机制，包括：
1. SOP学习系统核心功能
2. SOP学习集成器
3. 增强版Hand执行器
"""

import os
import sys
import unittest
import asyncio
import json
import tempfile
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入测试框架
from tests.test_framework import RANGENTestCase

# 导入SOP学习相关模块
from src.core.sop_learning import (
    SOPLearningSystem, StandardOperatingProcedure, SOPStep,
    SOPLevel, SOPCategory, get_sop_learning_system
)
from src.integration.sop_learning_integrator import (
    SOPLearningIntegrator, ExecutionRecord, get_sop_learning_integrator
)
from src.hands.enhanced_executor import (
    EnhancedHandExecutor, create_enhanced_executor, enable_sop_learning_for_executor
)
from src.hands.executor import HandExecutor, HandExecutionResult
from src.hands.base import BaseHand


class TestSOPLearningSystem(RANGENTestCase):
    """测试SOP学习系统核心功能"""
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
        
        # 创建临时持久化文件路径
        self.persistence_path = os.path.join(self.temp_dir, "test_sops.pkl")
        
        # 创建测试SOP学习系统
        self.sop_system = SOPLearningSystem(self.persistence_path)
        
        # 创建测试SOP
        self.test_sop = self._create_test_sop()
        
    def tearDown(self):
        """测试后清理"""
        # 删除持久化文件
        if os.path.exists(self.persistence_path):
            os.remove(self.persistence_path)
        super().tearDown()
    
    def _create_test_sop(self) -> StandardOperatingProcedure:
        """创建测试SOP"""
        sop = StandardOperatingProcedure(
            sop_id="test_sop_001",
            name="测试SOP - 文件处理",
            description="测试文件处理的SOP",
            category=SOPCategory.SYSTEM_OPERATION,
            level=SOPLevel.L3_TASK,
            version="1.0.0"
        )
        
        # 添加步骤
        sop.add_step(SOPStep(
            step_id="step1",
            hand_name="file_read_hand",
            parameters={"file_path": "/path/to/file.txt", "encoding": "utf-8"},
            description="读取文件内容"
        ))
        
        sop.add_step(SOPStep(
            step_id="step2",
            hand_name="data_process_hand",
            parameters={"operation": "clean", "remove_empty_lines": True},
            description="处理数据"
        ))
        
        sop.add_step(SOPStep(
            step_id="step3",
            hand_name="file_write_hand",
            parameters={"file_path": "/path/to/output.txt", "content": "processed_data"},
            description="写入处理结果"
        ))
        
        return sop
    
    def test_sop_creation_and_validation(self):
        """测试SOP创建和验证"""
        # 测试SOP验证
        is_valid, errors = self.test_sop.validate()
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # 测试SOP属性
        self.assertEqual(self.test_sop.name, "测试SOP - 文件处理")
        self.assertEqual(self.test_sop.category, SOPCategory.SYSTEM_OPERATION)
        self.assertEqual(self.test_sop.level, SOPLevel.L3_TASK)
        self.assertEqual(len(self.test_sop.steps), 3)
        
        # 测试SOP摘要
        summary = self.test_sop.get_summary()
        self.assertEqual(summary["name"], "测试SOP - 文件处理")
        self.assertEqual(summary["step_count"], 3)
        self.assertEqual(summary["category"], "system_operation")
        self.assertEqual(summary["level"], "l3_task")
    
    def test_sop_similarity_calculation(self):
        """测试SOP相似度计算"""
        from src.core.sop_learning import SOPSimilarityMetric
        
        # 创建另一个相似的SOP
        similar_sop = self._create_test_sop()
        similar_sop.name = "测试SOP - 文件处理2"
        
        # 计算相似度
        similarity = SOPSimilarityMetric.calculate_sop_similarity(
            self.test_sop, similar_sop
        )
        
        # 应该高度相似
        self.assertGreater(similarity, 0.8)
        
        # 创建不同的SOP
        different_sop = StandardOperatingProcedure(
            sop_id="test_sop_different",
            name="API调用SOP",
            description="调用API的SOP",
            category=SOPCategory.API_INTEGRATION,
            level=SOPLevel.L3_TASK
        )
        different_sop.add_step(SOPStep(
            step_id="step1",
            hand_name="api_call_hand",
            parameters={"url": "https://api.example.com", "method": "GET"},
            description="调用API"
        ))
        
        # 计算不同SOP的相似度
        different_similarity = SOPSimilarityMetric.calculate_sop_similarity(
            self.test_sop, different_sop
        )
        
        # 应该较低相似度
        self.assertLess(different_similarity, 0.5)
    
    def test_learn_from_execution(self):
        """测试从执行历史学习SOP"""
        # 创建模拟执行步骤
        execution_steps = [
            {
                "hand_name": "file_read_hand",
                "parameters": {"file_path": "/tmp/test.txt"},
                "description": "读取测试文件"
            },
            {
                "hand_name": "data_clean_hand",
                "parameters": {"operation": "trim", "chars": " \t\n"},
                "description": "清理数据"
            }
        ]
        
        # 学习SOP
        sop_id = self.sop_system.learn_from_execution(
            task_name="文件清理任务",
            execution_steps=execution_steps,
            success=True,
            execution_id="test_exec_001",
            importance=1.0
        )
        
        self.assertIsNotNone(sop_id)
        
        # 验证SOP已创建
        created_sop = self.sop_system.get_sop(sop_id)
        self.assertIsNotNone(created_sop)
        self.assertEqual(created_sop.name, "文件清理任务_sop_")
        self.assertEqual(len(created_sop.steps), 2)
        self.assertEqual(created_sop.source_execution_ids, ["test_exec_001"])
        self.assertEqual(created_sop.learning_count, 1)
        self.assertEqual(created_sop.execution_count, 1)
        self.assertEqual(created_sop.success_rate, 1.0)
    
    def test_recall_sop(self):
        """测试SOP回忆功能"""
        # 添加测试SOP到系统
        self.sop_system.sops[self.test_sop.sop_id] = self.test_sop
        self.sop_system._index_sop(self.test_sop)
        
        # 回忆相关SOP
        relevant_sops = self.sop_system.recall_sop(
            task_description="处理文件数据",
            context=None
        )
        
        # 应该找到测试SOP
        self.assertGreaterEqual(len(relevant_sops), 1)
        
        # 检查回忆结果结构
        sop_info = relevant_sops[0]
        self.assertIn("sop", sop_info)
        self.assertIn("relevance", sop_info)
        self.assertIn("summary", sop_info)
        
        # 检查SOP匹配
        recalled_sop = sop_info["sop"]
        self.assertEqual(recalled_sop.sop_id, self.test_sop.sop_id)
        
        # 测试不相关任务
        irrelevant_sops = self.sop_system.recall_sop(
            task_description="完全不相关的任务",
            context=None
        )
        
        # 可能返回空列表或相关性很低的SOP
        if irrelevant_sops:
            self.assertLess(irrelevant_sops[0]["relevance"], 0.3)
    
    def test_sop_quality_analysis(self):
        """测试SOP质量分析"""
        # 添加测试SOP到系统
        self.sop_system.sops[self.test_sop.sop_id] = self.test_sop
        
        # 分析SOP质量
        quality_analysis = self.sop_system.analyze_sop_quality(self.test_sop.sop_id)
        
        # 检查质量分析结构
        self.assertIn("sop_id", quality_analysis)
        self.assertIn("sop_name", quality_analysis)
        self.assertIn("quality_score", quality_analysis)
        self.assertIn("step_completeness", quality_analysis)
        self.assertIn("learning_count", quality_analysis)
        self.assertIn("execution_count", quality_analysis)
        self.assertIn("success_rate", quality_analysis)
        self.assertIn("is_valid", quality_analysis)
        self.assertIn("validation_errors", quality_analysis)
        
        # 检查质量分数范围
        self.assertGreaterEqual(quality_analysis["quality_score"], 0.0)
        self.assertLessEqual(quality_analysis["quality_score"], 1.0)
        
        # 检查步骤完整性
        self.assertEqual(quality_analysis["step_completeness"], 1.0)
        
        # 测试无效SOP
        invalid_sop = StandardOperatingProcedure(
            sop_id="invalid_sop",
            name="",
            description="",
            category=SOPCategory.CUSTOM,
            level=SOPLevel.L3_TASK
        )
        self.sop_system.sops[invalid_sop.sop_id] = invalid_sop
        
        invalid_analysis = self.sop_system.analyze_sop_quality(invalid_sop.sop_id)
        self.assertFalse(invalid_analysis.get("is_valid", True))
    
    def test_sop_persistence(self):
        """测试SOP持久化"""
        # 添加测试SOP到系统
        self.sop_system.sops[self.test_sop.sop_id] = self.test_sop
        
        # 保存SOP
        self.sop_system._save_sops()
        
        # 验证文件存在
        self.assertTrue(os.path.exists(self.persistence_path))
        
        # 创建新系统实例加载SOP
        new_system = SOPLearningSystem(self.persistence_path)
        
        # 验证SOP已加载
        loaded_sop = new_system.get_sop(self.test_sop.sop_id)
        self.assertIsNotNone(loaded_sop)
        self.assertEqual(loaded_sop.sop_id, self.test_sop.sop_id)
        self.assertEqual(loaded_sop.name, self.test_sop.name)
        self.assertEqual(len(loaded_sop.steps), len(self.test_sop.steps))
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        # 获取单例实例
        instance1 = get_sop_learning_system()
        instance2 = get_sop_learning_system()
        
        # 应该是同一个实例
        self.assertIs(instance1, instance2)
        
        # 测试不同持久化路径
        different_path = os.path.join(self.temp_dir, "different.pkl")
        instance3 = get_sop_learning_system(different_path)
        
        # 不同路径应该创建新实例
        self.assertIsNot(instance1, instance3)


class TestSOPLearningIntegrator(RANGENTestCase):
    """测试SOP学习集成器"""
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
        
        # 创建模拟Hand执行器
        self.mock_executor = Mock(spec=HandExecutor)
        self.mock_executor.registry = Mock()
        self.mock_executor.registry.get_all_hands = Mock(return_value=[])
        
        # 创建SOP学习集成器
        self.integrator = SOPLearningIntegrator(
            hand_executor=self.mock_executor,
            auto_learn=True
        )
        
        # 创建模拟执行结果
        self.mock_results = [
            HandExecutionResult(
                hand_name="test_hand_1",
                success=True,
                output={"result": "success", "data": "test_data_1"},
                error=None,
                execution_time=0.1
            ),
            HandExecutionResult(
                hand_name="test_hand_2",
                success=True,
                output={"result": "success", "data": "test_data_2"},
                error=None,
                execution_time=0.2
            )
        ]
    
    def test_record_execution(self):
        """测试执行记录功能"""
        # 记录执行
        record_id = asyncio.run(self.integrator.record_execution(
            task_name="测试任务",
            hand_results=self.mock_results,
            context={"env": "test"},
            tags=["test", "integration"]
        ))
        
        self.assertIsNotNone(record_id)
        self.assertGreater(len(record_id), 0)
        
        # 验证执行记录
        self.assertEqual(len(self.integrator.execution_history), 1)
        record = self.integrator.execution_history[0]
        
        self.assertEqual(record.task_name, "测试任务")
        self.assertEqual(record.success, True)
        self.assertEqual(len(record.hand_results), 2)
        self.assertEqual(record.context.get("env"), "test")
        self.assertIn("test", record.tags)
        self.assertIn("integration", record.tags)
    
    def test_learn_from_execution(self):
        """测试从执行学习"""
        # 创建执行记录
        record = ExecutionRecord(
            record_id="test_record_001",
            task_name="学习测试任务",
            execution_time=time.time(),
            success=True,
            hand_results=[
                {
                    "hand_name": "test_hand_1",
                    "success": True,
                    "parameters": {"param1": "value1"},
                    "execution_time": 0.1
                },
                {
                    "hand_name": "test_hand_2", 
                    "success": True,
                    "parameters": {"param2": "value2"},
                    "execution_time": 0.2
                }
            ],
            tags=["learning_test"]
        )
        
        # 模拟SOP学习系统的learn_from_execution方法
        with patch.object(self.integrator.sop_system, 'learn_from_execution') as mock_learn:
            mock_learn.return_value = "learned_sop_001"
            
            # 从执行记录学习
            sop_id = asyncio.run(self.integrator.learn_from_execution(record))
            
            # 验证学习被调用
            self.assertEqual(sop_id, "learned_sop_001")
            mock_learn.assert_called_once()
            
            # 检查调用参数
            call_args = mock_learn.call_args
            self.assertEqual(call_args[0][0], "学习测试任务")  # task_name
            self.assertEqual(len(call_args[0][1]), 2)  # execution_steps
            self.assertTrue(call_args[0][2])  # success
            self.assertEqual(call_args[0][3], "test_record_001")  # execution_id
    
    def test_recall_sops(self):
        """测试SOP回忆"""
        # 模拟SOP学习系统的recall_sop方法
        with patch.object(self.integrator.sop_system, 'recall_sop') as mock_recall:
            mock_sop = Mock(spec=StandardOperatingProcedure)
            mock_sop.sop_id = "test_sop_001"
            mock_sop.name = "测试SOP"
            mock_sop.description = "测试SOP描述"
            mock_sop.success_rate = 0.9
            mock_sop.execution_count = 5
            mock_sop.steps = []
            
            mock_recall.return_value = [
                {
                    "sop": mock_sop,
                    "relevance": 0.8,
                    "summary": {"name": "测试SOP", "success_rate": 0.9}
                }
            ]
            
            # 回忆SOP
            relevant_sops = asyncio.run(self.integrator.recall_sops(
                task_description="测试任务描述",
                context={"env": "test"},
                limit=3
            ))
            
            # 验证结果
            self.assertEqual(len(relevant_sops), 1)
            self.assertEqual(relevant_sops[0]["sop"].sop_id, "test_sop_001")
            
            # 验证调用参数
            mock_recall.assert_called_once_with("测试任务描述", {"env": "test"})
    
    def test_execute_with_sop_guidance(self):
        """测试SOP指导执行"""
        # 模拟SOP回忆结果
        mock_sop = Mock(spec=StandardOperatingProcedure)
        mock_sop.sop_id = "test_sop_001"
        mock_sop.name = "测试SOP"
        mock_sop.steps = [
            Mock(spec=SOPStep, hand_name="test_hand_1", parameters={"param1": "value1"}),
            Mock(spec=SOPStep, hand_name="test_hand_2", parameters={"param2": "value2"})
        ]
        
        # 模拟Hand执行结果
        mock_hand_results = [
            HandExecutionResult(hand_name="test_hand_1", success=True, output={}),
            HandExecutionResult(hand_name="test_hand_2", success=True, output={})
        ]
        
        # 模拟方法调用
        with patch.object(self.integrator, 'recall_sops') as mock_recall, \
             patch.object(self.integrator, 'record_execution') as mock_record:
            
            mock_recall.return_value = [{"sop": mock_sop, "relevance": 0.9}]
            mock_record.return_value = "record_id_001"
            
            # 模拟Hand执行器的execute_hand方法
            self.mock_executor.execute_hand = Mock(side_effect=mock_hand_results)
            
            # 执行SOP指导的任务
            results = asyncio.run(self.integrator.execute_with_sop_guidance(
                task_description="测试任务",
                context={"env": "test"}
            ))
            
            # 验证结果
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0].hand_name, "test_hand_1")
            self.assertEqual(results[1].hand_name, "test_hand_2")
            
            # 验证Hand执行器被调用正确次数
            self.assertEqual(self.mock_executor.execute_hand.call_count, 2)
            
            # 验证执行记录被调用
            mock_record.assert_called_once()
    
    def test_analyze_task(self):
        """测试任务分析"""
        # 模拟SOP回忆结果
        mock_sop = Mock(spec=StandardOperatingProcedure)
        mock_sop.sop_id = "test_sop_001"
        mock_sop.name = "测试SOP"
        mock_sop.description = "测试SOP描述"
        mock_sop.success_rate = 0.9
        mock_sop.execution_count = 10
        mock_sop.steps = [
            Mock(spec=SOPStep, hand_name="test_hand_1", parameters={"param1": "value1"}, description="步骤1"),
            Mock(spec=SOPStep, hand_name="test_hand_2", parameters={"param2": "value2"}, description="步骤2")
        ]
        
        # 模拟质量分析结果
        mock_quality_analysis = {
            "quality_score": 0.8,
            "step_completeness": 1.0,
            "is_valid": True
        }
        
        # 模拟方法调用
        with patch.object(self.integrator, 'recall_sops') as mock_recall, \
             patch.object(self.integrator.sop_system, 'analyze_sop_quality') as mock_analyze:
            
            mock_recall.return_value = [
                {"sop": mock_sop, "relevance": 0.9}
            ]
            mock_analyze.return_value = mock_quality_analysis
            
            # 分析任务
            analysis = asyncio.run(self.integrator.analyze_task(
                task_description="测试任务描述",
                context={"env": "test"}
            ))
            
            # 验证分析结果结构
            self.assertEqual(analysis["task_description"], "测试任务描述")
            self.assertTrue(analysis["has_related_sops"])
            self.assertEqual(analysis["sop_count"], 1)
            
            # 验证SOP信息
            top_sops = analysis["top_sops"]
            self.assertEqual(len(top_sops), 1)
            self.assertEqual(top_sops[0]["sop_id"], "test_sop_001")
            self.assertEqual(top_sops[0]["name"], "测试SOP")
            self.assertEqual(top_sops[0]["success_rate"], 0.9)
            self.assertEqual(top_sops[0]["execution_count"], 10)
            
            # 验证建议
            suggestions = analysis["suggestions"]
            self.assertGreater(len(suggestions), 0)
            
            # 验证执行计划
            execution_plan = analysis["execution_plan"]
            self.assertEqual(execution_plan["strategy"], "sop_guided")
            self.assertEqual(execution_plan["recommended_sop"], "test_sop_001")
            self.assertEqual(len(execution_plan["steps"]), 2)
    
    def test_integrator_statistics(self):
        """测试集成器统计"""
        # 添加一些执行记录
        record1 = ExecutionRecord(
            record_id="record1",
            task_name="任务1",
            execution_time=time.time() - 3600,
            success=True,
            hand_results=[{"hand_name": "hand1"}],
            tags=["test"]
        )
        
        record2 = ExecutionRecord(
            record_id="record2",
            task_name="任务2",
            execution_time=time.time() - 1800,
            success=False,
            hand_results=[{"hand_name": "hand2"}],
            tags=["test", "failed"]
        )
        
        self.integrator.execution_history = [record1, record2]
        
        # 获取统计信息
        stats = self.integrator.get_integrator_stats()
        
        # 验证统计结构
        self.assertEqual(stats["execution_records_count"], 2)
        self.assertTrue(stats["auto_learn_enabled"])
        self.assertEqual(stats["min_steps_for_learning"], 2)
        self.assertTrue(stats["hand_executor_set"])
        self.assertTrue(stats["sop_system_available"])
        
        # 验证最近执行记录
        recent_executions = stats["recent_executions"]
        self.assertEqual(len(recent_executions), 2)
        self.assertEqual(recent_executions[0]["task_name"], "任务2")  # 按时间倒序
        self.assertEqual(recent_executions[1]["task_name"], "任务1")


class TestEnhancedHandExecutor(RANGENTestCase):
    """测试增强版Hand执行器"""
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
        
        # 创建模拟注册表
        self.mock_registry = Mock()
        self.mock_registry.get_hand = Mock(return_value=None)
        self.mock_registry.get_all_hands = Mock(return_value=[])
        
        # 创建增强版Hand执行器
        self.enhanced_executor = EnhancedHandExecutor(
            registry=self.mock_registry,
            enable_sop_learning=True,
            auto_record_executions=True
        )
        
        # 模拟SOP集成器
        self.mock_integrator = Mock(spec=SOPLearningIntegrator)
        self.mock_integrator.record_execution = Mock(return_value="test_record_id")
        self.mock_integrator.recall_sops = Mock(return_value=[])
        self.mock_integrator.execute_with_sop_guidance = Mock(return_value=[])
        self.mock_integrator.analyze_task = Mock(return_value={})
        self.mock_integrator.get_integrator_stats = Mock(return_value={"test": "stats"})
        
        self.enhanced_executor.sop_integrator = self.mock_integrator
    
    def test_enhanced_executor_creation(self):
        """测试增强版执行器创建"""
        # 测试基本属性
        self.assertTrue(self.enhanced_executor.enable_sop_learning)
        self.assertTrue(self.enhanced_executor.auto_record_executions)
        self.assertTrue(self.enhanced_executor.sop_guidance_enabled)
        
        # 测试SOP集成器设置
        self.assertIsNotNone(self.enhanced_executor.sop_integrator)
        
        # 测试禁用SOP学习
        executor_no_sop = EnhancedHandExecutor(
            registry=self.mock_registry,
            enable_sop_learning=False
        )
        self.assertFalse(executor_no_sop.enable_sop_learning)
        self.assertIsNone(executor_no_sop.sop_integrator)
    
    def test_enhanced_execute_hand(self):
        """测试增强版Hand执行"""
        # 创建模拟Hand
        mock_hand = Mock(spec=BaseHand)
        mock_hand.execute = Mock(return_value={"result": "success"})
        
        # 设置注册表返回模拟Hand
        self.mock_registry.get_hand = Mock(return_value=mock_hand)
        
        # 模拟父类execute_hand方法
        with patch.object(HandExecutor, 'execute_hand') as mock_parent_execute:
            mock_result = HandExecutionResult(
                hand_name="test_hand",
                success=True,
                output={"result": "success"}
            )
            mock_parent_execute.return_value = mock_result
            
            # 执行Hand
            result = asyncio.run(self.enhanced_executor.execute_hand(
                hand_name="test_hand",
                param1="value1",
                param2="value2",
                task_name="测试任务",
                tags=["test"]
            ))
            
            # 验证结果
            self.assertEqual(result.hand_name, "test_hand")
            self.assertTrue(result.success)
            
            # 验证父类方法被调用
            mock_parent_execute.assert_called_once_with("test_hand", param1="value1", param2="value2")
            
            # 验证执行记录被调用
            self.mock_integrator.record_execution.assert_called_once()
            
            # 检查记录调用的参数
            call_args = self.mock_integrator.record_execution.call_args
            self.assertEqual(call_args[0][0], "测试任务")  # task_name
            self.assertEqual(len(call_args[0][1]), 1)  # hand_results
            self.assertIn("test", call_args[0][3])  # tags
    
    def test_execute_with_sop_guidance(self):
        """测试SOP指导执行"""
        # 模拟SOP指导执行结果
        mock_results = [
            HandExecutionResult(hand_name="hand1", success=True, output={}),
            HandExecutionResult(hand_name="hand2", success=True, output={})
        ]
        
        self.mock_integrator.execute_with_sop_guidance = Mock(return_value=mock_results)
        
        # 执行SOP指导任务
        results = asyncio.run(self.enhanced_executor.execute_with_sop_guidance(
            task_description="测试任务描述",
            context={"env": "test"},
            sop_id="test_sop_001"
        ))
        
        # 验证结果
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].hand_name, "hand1")
        self.assertEqual(results[1].hand_name, "hand2")
        
        # 验证SOP集成器被调用
        self.mock_integrator.execute_with_sop_guidance.assert_called_once_with(
            task_description="测试任务描述",
            context={"env": "test"}
        )
    
    def test_analyze_task(self):
        """测试任务分析"""
        # 模拟任务分析结果
        mock_analysis = {
            "task_description": "测试任务描述",
            "has_related_sops": True,
            "suggestions": [{"type": "use_existing_sop", "priority": "high"}],
            "execution_plan": {"strategy": "sop_guided"}
        }
        
        self.mock_integrator.analyze_task = Mock(return_value=mock_analysis)
        
        # 分析任务
        analysis = asyncio.run(self.enhanced_executor.analyze_task(
            task_description="测试任务描述",
            context={"env":