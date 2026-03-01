#!/usr/bin/env python3
"""
动态配置系统测试套件

完整的单元测试、集成测试和性能测试
"""

import unittest
import time
import json
import tempfile
import os
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# 添加项目根目录到路径
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.dynamic_config_system import (
    DynamicConfigManager, ConfigValidator, ConfigMonitor,
    ConfigTemplateManager, FileConfigStore
)
from src.core.advanced_config_features import (
    HotReloadManager, ConfigDistributionManager,
    AlertManager, AccessControlManager
)


class TestConfigValidator(unittest.TestCase):
    """配置验证器测试"""

    def setUp(self):
        self.validator = ConfigValidator()

    def test_valid_config(self):
        """测试有效配置"""
        config = {
            'thresholds': {
                'simple_max_complexity': 0.05,
                'medium_max_complexity': 0.25,
                'complex_min_complexity': 0.25
            },
            'keywords': {
                'question_words': ['what', 'why', 'how'],
                'complexity_indicators': ['explain', 'analyze']
            }
        }

        result = self.validator.validate(config)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)

    def test_invalid_thresholds(self):
        """测试无效阈值"""
        config = {
            'thresholds': {
                'simple_max_complexity': 1.5,  # 超出范围
                'medium_max_complexity': 0.25
            }
        }

        result = self.validator.validate(config)
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)

    def test_dependency_validation(self):
        """测试依赖关系验证"""
        config = {
            'thresholds': {
                'simple_max_complexity': 0.8,
                'medium_min_complexity': 0.3,  # 违反依赖关系
                'medium_max_complexity': 0.25,
                'complex_min_complexity': 0.25
            }
        }

        result = self.validator.validate(config)
        self.assertFalse(result.is_valid)
        self.assertIn('依赖关系错误', ' '.join(result.errors))


class TestConfigMonitor(unittest.TestCase):
    """配置监控器测试"""

    def setUp(self):
        self.monitor = ConfigMonitor("test_changes.log")

    def tearDown(self):
        # 清理测试文件
        if os.path.exists("test_changes.log"):
            os.remove("test_changes.log")

    def test_record_change(self):
        """测试记录配置变更"""
        config = {'thresholds': {'test': 0.5}}

        self.monitor.record_config_change(config, "test_user", "测试变更")

        history = self.monitor.get_change_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].author, "test_user")
        self.assertEqual(history[0].description, "测试变更")

    def test_change_query(self):
        """测试变更查询"""
        # 添加多个变更
        configs = [
            ({'thresholds': {'a': 1}}, "user1", "变更1"),
            ({'thresholds': {'b': 2}}, "user2", "变更2"),
            ({'thresholds': {'c': 3}}, "user1", "变更3")
        ]

        for config, author, desc in configs:
            self.monitor.record_config_change(config, author, desc)

        # 按作者查询
        user1_changes = self.monitor.query_changes({'author': 'user1'})
        self.assertEqual(len(user1_changes), 2)

        # 按描述查询
        desc_changes = self.monitor.query_changes({'description_contains': '变更2'})
        self.assertEqual(len(desc_changes), 1)

    def test_metrics_calculation(self):
        """测试指标计算"""
        # 添加一些测试数据
        for i in range(5):
            config = {'thresholds': {f'test_{i}': i * 0.1}}
            self.monitor.record_config_change(config, f"user{i%2+1}")

        metrics = self.monitor.get_config_metrics()
        self.assertIn('total_changes', metrics)
        self.assertIn('author_stats', metrics)
        self.assertIn('health_score', metrics)
        self.assertGreater(metrics['total_changes'], 0)


class TestFileConfigStore(unittest.TestCase):
    """文件配置存储测试"""

    def setUp(self):
        self.test_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.test_file.close()
        self.store = FileConfigStore(self.test_file.name)

    def tearDown(self):
        # 清理测试文件
        try:
            os.unlink(self.test_file.name)
            for f in os.listdir(self.store.versions_dir):
                if f.endswith('.json'):
                    os.unlink(os.path.join(self.store.versions_dir, f))
            os.rmdir(self.store.versions_dir)
            for f in os.listdir(self.store.branches_dir):
                if f.endswith('.json'):
                    os.unlink(os.path.join(self.store.branches_dir, f))
            os.rmdir(self.store.branches_dir)
            for f in os.listdir(self.store.tags_dir):
                if f.endswith('.json'):
                    os.unlink(os.path.join(self.store.tags_dir, f))
            os.rmdir(self.store.tags_dir)
        except:
            pass

    def test_save_and_load_config(self):
        """测试保存和加载配置"""
        config = {'test': 'data', 'number': 42}

        version = self.store.save_config(config)
        self.assertIsNotNone(version)

        loaded_config = self.store.load_config()
        self.assertEqual(loaded_config, config)

    def test_version_management(self):
        """测试版本管理"""
        # 保存多个版本
        configs = [
            {'version': 1, 'data': 'first'},
            {'version': 2, 'data': 'second'},
            {'version': 3, 'data': 'third'}
        ]

        versions = []
        for config in configs:
            version = self.store.save_config(config)
            versions.append(version)

        # 验证版本数量
        all_versions = self.store.get_config_versions()
        self.assertGreaterEqual(len(all_versions), len(configs))

        # 测试回滚
        rollback_config = self.store.rollback_to_version(versions[0])
        self.assertEqual(rollback_config, configs[0])

    def test_branch_management(self):
        """测试分支管理"""
        # 保存初始配置
        config = {'branch_test': True}
        self.store.save_config(config)

        # 创建分支
        success = self.store.create_branch('feature_branch')
        self.assertTrue(success)

        # 切换分支
        success = self.store.switch_branch('feature_branch')
        self.assertTrue(success)

        # 验证分支配置
        loaded_config = self.store.load_config()
        self.assertEqual(loaded_config, config)


class TestConfigTemplateManager(unittest.TestCase):
    """配置模板管理器测试"""

    def setUp(self):
        self.manager = ConfigTemplateManager()

    def test_get_template(self):
        """测试获取模板"""
        template = self.manager.get_template('conservative')
        self.assertIsNotNone(template)
        self.assertIn('thresholds', template)
        self.assertIn('environment', template)

    def test_template_inheritance(self):
        """测试模板继承"""
        template = self.manager.get_template('conservative', resolve_inheritance=True)
        self.assertIsNotNone(template)
        self.assertIn('extends', template)
        self.assertIn('inheritance_chain', template)

    def test_recommended_template(self):
        """测试推荐模板"""
        context = {'environment': 'production', 'accuracy_requirement': 'high'}
        recommended = self.manager.get_recommended_template(context)
        self.assertEqual(recommended, 'high_precision')

    def test_create_custom_template(self):
        """测试创建自定义模板"""
        customizations = {
            'thresholds': {'custom_threshold': 0.75},
            'description': '自定义测试模板'
        }

        success = self.manager.create_custom_template(
            'custom_test', 'base', customizations, '测试自定义模板'
        )
        self.assertTrue(success)

        # 验证模板创建
        template = self.manager.get_template('custom_test')
        self.assertIsNotNone(template)
        self.assertEqual(template['thresholds']['custom_threshold'], 0.75)


class TestHotReloadManager(unittest.TestCase):
    """热更新管理器测试"""

    def setUp(self):
        self.config_system = Mock()
        self.reload_manager = HotReloadManager(self.config_system, check_interval=1)

    def tearDown(self):
        self.reload_manager.stop_monitoring()

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_file_change_detection(self, mock_open, mock_exists):
        """测试文件变更检测"""
        mock_exists.return_value = True

        # 模拟文件内容变化
        mock_open.return_value.read.return_value = "changed_content"

        # 记录初始哈希
        self.reload_manager._check_config_files_changed()

        # 修改文件内容
        mock_open.return_value.read.return_value = "new_content"

        # 检测变更
        changed = self.reload_manager._check_config_files_changed()
        self.assertTrue(changed)


class TestAlertManager(unittest.TestCase):
    """告警管理器测试"""

    def setUp(self):
        self.alert_manager = AlertManager()

    def test_alert_rule_trigger(self):
        """测试告警规则触发"""
        # 添加告警规则
        self.alert_manager.add_alert_rule('test_rule', {
            'name': '测试告警',
            'severity': 'medium'
        })

        # 模拟触发告警
        alert_data = {'message': '测试告警信息', 'severity': 'medium'}
        self.alert_manager.trigger_alert('test_rule', alert_data)

        # 验证告警状态
        status = self.alert_manager.get_alert_status()
        self.assertGreater(status['active_alerts'], 0)

    def test_alert_channels(self):
        """测试告警通道"""
        alerts_received = []

        def mock_channel(message, context):
            alerts_received.append((message, context))

        self.alert_manager.add_alert_channel('test_channel', mock_channel)

        # 触发告警
        self.alert_manager.trigger_alert('test_alert', {'data': 'test'})

        # 验证告警发送
        self.assertEqual(len(alerts_received), 1)
        self.assertIn('test_alert', alerts_received[0][0])


class TestAccessControlManager(unittest.TestCase):
    """访问控制管理器测试"""

    def setUp(self):
        self.ac_manager = AccessControlManager()

    def test_user_role_assignment(self):
        """测试用户角色分配"""
        # 添加用户
        self.ac_manager.add_user('test_user', {'email': 'test@example.com'})

        # 分配角色
        self.ac_manager.assign_role('test_user', 'developer')

        # 验证权限
        has_permission = self.ac_manager.check_permission('test_user', 'config.read')
        self.assertTrue(has_permission)

        # 验证无权限
        has_no_permission = self.ac_manager.check_permission('test_user', 'admin.delete')
        self.assertFalse(has_no_permission)

    def test_session_management(self):
        """测试会话管理"""
        # 创建会话
        session_id = self.ac_manager.create_session('test_user', '127.0.0.1')
        self.assertIsNotNone(session_id)

        # 验证会话
        user_id = self.ac_manager.validate_session(session_id)
        self.assertEqual(user_id, 'test_user')

        # 销毁会话
        self.ac_manager.destroy_session(session_id)

        # 验证会话已销毁
        user_id = self.ac_manager.validate_session(session_id)
        self.assertIsNone(user_id)


class TestDynamicConfigManager(unittest.TestCase):
    """动态配置管理器集成测试"""

    def setUp(self):
        self.config_manager = DynamicConfigManager()

    def test_full_config_workflow(self):
        """测试完整配置工作流"""
        # 1. 更新配置
        self.config_manager.update_routing_threshold('test_threshold', 0.5)
        self.assertEqual(self.config_manager.config.thresholds['test_threshold'], 0.5)

        # 2. 添加关键词
        self.config_manager.add_routing_keyword('test_category', 'test_keyword')
        keywords = self.config_manager.config.keywords.get('test_category', [])
        self.assertIn('test_keyword', keywords)

        # 3. 应用模板
        self.config_manager.apply_template('conservative')

        # 4. 验证配置
        status = self.config_manager.get_config_status()
        self.assertIn('current_config', status)
        self.assertIn('change_metrics', status)


class PerformanceTestConfigSystem(unittest.TestCase):
    """配置系统性能测试"""

    def setUp(self):
        self.config_manager = DynamicConfigManager()

    def test_bulk_config_updates(self):
        """测试批量配置更新性能"""
        import time

        # 批量更新配置
        updates = {f'threshold_{i}': i * 0.01 for i in range(100)}

        start_time = time.time()
        for key, value in updates.items():
            self.config_manager.update_routing_threshold(key, value)
        end_time = time.time()

        # 验证性能（每秒至少10个更新）
        updates_per_second = len(updates) / (end_time - start_time)
        self.assertGreater(updates_per_second, 10)

        # 验证配置正确性
        for key, expected_value in updates.items():
            self.assertEqual(self.config_manager.config.thresholds[key], expected_value)

    def test_concurrent_access(self):
        """测试并发访问"""
        import threading
        import concurrent.futures

        results = []
        errors = []

        def worker(worker_id):
            try:
                # 每个工作线程执行配置操作
                threshold_key = f'worker_{worker_id}_threshold'
                self.config_manager.update_routing_threshold(threshold_key, worker_id * 0.1)

                keyword_key = f'worker_{worker_id}_keyword'
                self.config_manager.add_routing_keyword('test_keywords', keyword_key)

                results.append(worker_id)
            except Exception as e:
                errors.append(e)

        # 启动多个线程并发执行
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker, i) for i in range(10)]
            concurrent.futures.wait(futures)

        # 验证结果
        self.assertEqual(len(results), 10)
        self.assertEqual(len(errors), 0)

        # 验证配置正确性
        for i in range(10):
            threshold_key = f'worker_{i}_threshold'
            self.assertEqual(self.config_manager.config.thresholds[threshold_key], i * 0.1)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
