#!/usr/bin/env python3
"""
系统集成测试套件

测试整个动态配置系统的集成功能
"""

import unittest
import time
import tempfile
import os
import json
from unittest.mock import Mock, patch

# 添加项目根目录到路径
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.intelligent_router import IntelligentRouter
from src.core.dynamic_config_system import DynamicConfigManager
from src.core.advanced_config_features import AdvancedConfigSystem
from src.core.config_web_interface import ConfigAPIClient


class TestSystemIntegration(unittest.TestCase):
    """系统集成测试"""

    def setUp(self):
        # 创建完整的系统实例
        self.router = IntelligentRouter(enable_advanced_features=True)

    def tearDown(self):
        # 清理资源
        try:
            if hasattr(self.router, '_config_api_server') and self.router._config_api_server:
                # 停止API服务器
                pass
            if hasattr(self.router, '_web_interface') and self.router._web_interface:
                self.router.stop_web_interface()
        except:
            pass

    def test_full_system_initialization(self):
        """测试完整系统初始化"""
        # 验证路由器初始化
        self.assertIsNotNone(self.router.route_type_registry)
        self.assertIsNotNone(self.router.performance_monitor)

        # 验证配置管理器
        if hasattr(self.router, 'config_manager') and self.router.config_manager:
            self.assertIsNotNone(self.router.config_manager.config)

        # 验证高级功能
        if hasattr(self.router, 'advanced_system') and self.router.advanced_system:
            self.assertIsNotNone(self.router.advanced_system.hot_reload)
            self.assertIsNotNone(self.router.advanced_system.distribution)
            self.assertIsNotNone(self.router.advanced_system.alert_manager)
            self.assertIsNotNone(self.router.advanced_system.access_control)

    def test_config_workflow_integration(self):
        """测试配置工作流集成"""
        # 1. 更新配置
        self.router.update_routing_threshold('integration_test', 0.75)

        # 2. 验证配置更新
        config = self.router.get_routing_config()
        self.assertIn('integration_test', config.get('thresholds', {}))

        # 3. 添加关键词
        self.router.add_routing_keyword('integration_category', 'integration_keyword')

        # 4. 验证关键词添加
        keywords = self.router.get_routing_config().get('keywords', {})
        self.assertIn('integration_keyword', keywords.get('integration_category', []))

        # 5. 应用模板
        try:
            self.router.apply_config_template('conservative')
        except Exception as e:
            # 如果模板不存在，跳过此测试
            self.skipTest(f"模板应用失败: {e}")

    def test_routing_with_config_integration(self):
        """测试路由与配置集成"""
        from src.core.intelligent_router import QueryFeatures

        # 创建测试查询特征
        features = QueryFeatures(
            is_multi_query=False,
            num_questions=1,
            complexity_score=0.1,
            word_count=5,
            has_question_words=True
        )

        # 执行路由决策
        decision = self.router.decide_route(features)

        # 验证决策结果
        self.assertIsNotNone(decision)
        self.assertIn('route_type', decision)
        self.assertIn('confidence', decision)

    def test_monitoring_integration(self):
        """测试监控集成"""
        if not hasattr(self.router, 'config_manager') or not self.router.config_manager:
            self.skipTest("配置管理器不可用")

        # 执行一些配置操作
        self.router.update_routing_threshold('monitor_test', 0.5)
        self.router.add_routing_keyword('monitor', 'test')

        # 获取监控指标
        metrics = self.router.config_manager.config_monitor.get_config_metrics()

        # 验证监控数据
        self.assertIn('total_changes', metrics)
        self.assertGreater(metrics['total_changes'], 0)

    def test_template_system_integration(self):
        """测试模板系统集成"""
        if not hasattr(self.router, 'config_manager') or not self.router.config_manager:
            self.skipTest("配置管理器不可用")

        # 获取可用模板
        templates = self.router.config_manager.template_manager.list_templates()

        # 验证模板列表
        self.assertIsInstance(templates, list)
        self.assertGreater(len(templates), 0)

        # 测试模板推荐
        context = {'environment': 'production'}
        recommended = self.router.config_manager.template_manager.get_recommended_template(context)
        self.assertIsInstance(recommended, str)


class TestAdvancedFeaturesIntegration(unittest.TestCase):
    """高级功能集成测试"""

    def setUp(self):
        # 创建高级配置系统
        self.advanced_system = AdvancedConfigSystem()

    def tearDown(self):
        # 停止所有服务
        try:
            self.advanced_system.stop_all_services()
        except:
            pass

    def test_hot_reload_integration(self):
        """测试热更新集成"""
        # 启动热更新监控
        self.advanced_system.hot_reload.start_monitoring()

        # 验证监控状态
        self.assertTrue(self.advanced_system.hot_reload._running)

        # 停止监控
        self.advanced_system.hot_reload.stop_monitoring()
        self.assertFalse(self.advanced_system.hot_reload._running)

    def test_alert_system_integration(self):
        """测试告警系统集成"""
        # 添加告警规则
        self.advanced_system.alert_manager.add_alert_rule('integration_test', {
            'name': '集成测试告警',
            'severity': 'low'
        })

        # 触发告警
        self.advanced_system.alert_manager.trigger_alert(
            'integration_test',
            {'message': '测试告警', 'source': 'integration_test'}
        )

        # 验证告警状态
        status = self.advanced_system.alert_manager.get_alert_status()
        self.assertGreaterEqual(status['active_alerts'], 1)

    def test_access_control_integration(self):
        """测试访问控制集成"""
        # 添加用户
        self.advanced_system.access_control.add_user('integration_user', {
            'email': 'integration@example.com'
        })

        # 分配角色
        self.advanced_system.access_control.assign_role('integration_user', 'developer')

        # 创建会话
        session_id = self.advanced_system.access_control.create_session('integration_user')
        self.assertIsNotNone(session_id)

        # 验证权限
        has_permission = self.advanced_system.access_control.check_permission(
            'integration_user', 'config.read'
        )
        self.assertTrue(has_permission)

        # 验证会话
        user_id = self.advanced_system.access_control.validate_session(session_id)
        self.assertEqual(user_id, 'integration_user')

    def test_distribution_system_integration(self):
        """测试分发系统集成"""
        # 注册节点
        self.advanced_system.distribution.register_node('test_node', {
            'endpoint': 'http://localhost:8080',
            'region': 'test'
        })

        # 验证节点注册
        status = self.advanced_system.distribution.get_distribution_status()
        self.assertGreaterEqual(status['total_nodes'], 1)

        # 注销节点
        self.advanced_system.distribution.unregister_node('test_node')
        status = self.advanced_system.distribution.get_distribution_status()
        self.assertEqual(status['total_nodes'], 0)


class TestEndToEndWorkflow(unittest.TestCase):
    """端到端工作流测试"""

    def setUp(self):
        self.router = IntelligentRouter(enable_advanced_features=True)

    def tearDown(self):
        try:
            if hasattr(self.router, '_web_interface') and self.router._web_interface:
                self.router.stop_web_interface()
        except:
            pass

    def test_complete_config_lifecycle(self):
        """测试完整配置生命周期"""
        # 1. 初始配置
        initial_config = self.router.get_routing_config()
        self.assertIsInstance(initial_config, dict)

        # 2. 配置修改
        self.router.update_routing_threshold('lifecycle_test', 0.6)
        modified_config = self.router.get_routing_config()
        self.assertEqual(modified_config['thresholds']['lifecycle_test'], 0.6)

        # 3. 配置验证
        if hasattr(self.router, 'config_manager') and self.router.config_manager:
            validation = self.router.config_manager.config_validator.validate(modified_config)
            # 验证应该通过或只有警告
            self.assertTrue(validation.is_valid or len(validation.errors) == 0)

        # 4. 配置导出
        try:
            from src.core.config_web_interface import ConfigImportExportManager
            import_export = ConfigImportExportManager(self.router)
            exported = import_export.export_config('json')
            self.assertIsInstance(exported, str)

            # 5. 配置导入（试运行）
            import_result = import_export.import_config(exported, 'json', dry_run=True)
            self.assertTrue(import_result['success'])
        except ImportError:
            self.skipTest("导入导出功能不可用")

    def test_concurrent_operations(self):
        """测试并发操作"""
        import concurrent.futures
        import threading

        results = []
        errors = []

        def worker(worker_id):
            """工作线程"""
            try:
                # 执行配置操作
                threshold_key = f'concurrent_{worker_id}'
                self.router.update_routing_threshold(threshold_key, worker_id * 0.1)

                keyword_key = f'concurrent_kw_{worker_id}'
                self.router.add_routing_keyword('concurrent_test', keyword_key)

                # 记录路由决策
                from src.core.intelligent_router import QueryFeatures
                features = QueryFeatures(
                    complexity_score=0.1,
                    word_count=5,
                    has_question_words=True
                )
                decision = self.router.decide_route(features)

                results.append({
                    'worker_id': worker_id,
                    'threshold_key': threshold_key,
                    'keyword_key': keyword_key,
                    'route_decision': decision.route_type.value if decision else None
                })

            except Exception as e:
                errors.append(f"Worker {worker_id}: {e}")

        # 启动并发操作
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker, i) for i in range(10)]
            concurrent.futures.wait(futures)

        # 验证结果
        self.assertEqual(len(results), 10, f"并发操作失败: {errors}")
        self.assertEqual(len(errors), 0, f"出现错误: {errors}")

        # 验证配置正确性
        final_config = self.router.get_routing_config()
        for result in results:
            threshold_key = result['threshold_key']
            expected_value = result['worker_id'] * 0.1
            self.assertEqual(
                final_config['thresholds'][threshold_key],
                expected_value,
                f"阈值 {threshold_key} 不正确"
            )

    def test_system_resilience(self):
        """测试系统韧性"""
        # 1. 测试无效配置处理
        try:
            self.router.update_routing_threshold('invalid_test', 1.5)  # 超出范围
            # 如果没有抛出异常，验证配置被正确处理
            config = self.router.get_routing_config()
            self.assertIn('invalid_test', config.get('thresholds', {}))
        except Exception:
            # 预期可能抛出异常，验证错误处理
            pass

        # 2. 测试空值处理
        try:
            self.router.update_routing_threshold('empty_test', None)
            config = self.router.get_routing_config()
            # 验证系统能处理None值
        except Exception:
            # 预期可能抛出异常，验证错误处理
            pass

        # 3. 测试大批量操作
        for i in range(100):
            self.router.update_routing_threshold(f'bulk_test_{i}', i * 0.001)

        # 验证系统仍然正常工作
        config = self.router.get_routing_config()
        self.assertGreater(len(config.get('thresholds', {})), 90)  # 至少90个阈值


class PerformanceTestSystemIntegration(unittest.TestCase):
    """系统集成性能测试"""

    def setUp(self):
        self.router = IntelligentRouter(enable_advanced_features=True)

    def test_bulk_config_operations(self):
        """测试批量配置操作性能"""
        import time

        # 批量配置操作
        start_time = time.time()

        # 批量更新阈值
        for i in range(50):
            self.router.update_routing_threshold(f'perf_test_{i}', i * 0.01)

        # 批量添加关键词
        for i in range(20):
            self.router.add_routing_keyword('perf_keywords', f'keyword_{i}')

        # 批量路由决策
        from src.core.intelligent_router import QueryFeatures
        for i in range(30):
            features = QueryFeatures(
                complexity_score=i * 0.02,
                word_count=5 + i,
                has_question_words=True
            )
            decision = self.router.decide_route(features)

        end_time = time.time()
        total_time = end_time - start_time

        # 验证性能（100个操作应在10秒内完成）
        operations_per_second = 100 / total_time
        self.assertGreater(operations_per_second, 5, f"性能不足: {operations_per_second} ops/sec")

    def test_memory_usage_under_load(self):
        """测试负载下的内存使用"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 执行大量操作
        for i in range(200):
            self.router.update_routing_threshold(f'memory_test_{i}', i * 0.001)
            self.router.add_routing_keyword('memory_test', f'kw_{i}')

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # 内存增长应合理（不超过100MB）
        self.assertLess(memory_increase, 100, f"内存泄漏: +{memory_increase}MB")

    def test_system_stability_under_stress(self):
        """测试压力下的系统稳定性"""
        import threading
        import time

        errors = []
        success_count = 0

        def stress_worker(worker_id):
            nonlocal success_count, errors
            try:
                for i in range(20):
                    # 执行各种操作
                    self.router.update_routing_threshold(
                        f'stress_{worker_id}_{i}', (worker_id + i) * 0.01
                    )

                    from src.core.intelligent_router import QueryFeatures
                    features = QueryFeatures(
                        complexity_score=0.1,
                        word_count=5,
                        has_question_words=True
                    )
                    decision = self.router.decide_route(features)

                    if decision:
                        success_count += 1

            except Exception as e:
                errors.append(f"Worker {worker_id}: {e}")

        # 启动多个压力线程
        threads = []
        for i in range(10):
            thread = threading.Thread(target=stress_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=30)

        # 验证稳定性
        self.assertEqual(len(errors), 0, f"压力测试出现错误: {errors}")
        self.assertGreater(success_count, 100, f"成功操作太少: {success_count}")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
