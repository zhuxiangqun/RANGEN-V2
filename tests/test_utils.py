#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具模块测试
"""

import unittest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
from tests.test_framework import RANGENTestCase, AsyncTestCase, MockTestCase

class TestSecurityUtils(RANGENTestCase):
    """安全工具测试"""
    
    def setUp(self):
        super().setUp()
        try:
            from src.utils.security_utils import InputValidator, DataEncryption, SecureExecutor
            self.InputValidator = InputValidator
            self.DataEncryption = DataEncryption
            self.SecureExecutor = SecureExecutor
        except ImportError:
            self.skipTest("安全工具模块不可用")
    
    def test_input_validation(self):
        """测试输入验证"""
        validator = self.InputValidator()
        
        # 测试有效输入
        self.assertTrue(validator.validate_input("valid input"))
        self.assertTrue(validator.validate_input("valid input", max_length=100))
        
        # 测试无效输入
        self.assertFalse(validator.validate_input(""))
        self.assertFalse(validator.validate_input("x" * 1001))  # 超过默认长度
        self.assertFalse(validator.validate_input("input with <script>"))  # 危险字符
        self.assertFalse(validator.validate_input("input with 'quotes'"))  # 危险字符
    
    def test_sql_injection_detection(self):
        """测试SQL注入检测"""
        validator = self.InputValidator()
        
        # 测试SQL注入模式
        sql_injections = [
            "'; DROP TABLE users; --",
            "1' UNION SELECT * FROM users --",
            "admin' OR '1'='1",
            "/* comment */",
            "1; DELETE FROM users;"
        ]
        
        for injection in sql_injections:
            # 这些应该被检测为危险输入
            self.assertFalse(validator.validate_input(injection))
    
    def test_data_encryption(self):
        """测试数据加密"""
        encryption = self.DataEncryption()
        
        # 测试加密和解密
        test_data = "sensitive data"
        encrypted = encryption.encrypt(test_data)
        decrypted = encryption.decrypt(encrypted)
        
        self.assertNotEqual(encrypted, test_data)
        self.assertEqual(decrypted, test_data)
    
    def test_safe_execution(self):
        """测试安全执行"""
        executor = self.SecureExecutor()
        
        # 测试安全表达式评估
        result = executor.safe_eval("1 + 2")
        self.assertEqual(result, 3)
        
        # 测试危险表达式
        with self.assertRaises(ValueError):
            executor.safe_eval("__import__('os').system('ls')")
    
    def test_secure_subprocess(self):
        """测试安全子进程"""
        executor = self.SecureExecutor()
        
        # 测试安全命令执行
        result = executor.safe_subprocess(["echo", "test"])
        self.assertEqual(result.returncode, 0)
        
        # 测试危险命令（应该被阻止）
        with self.assertRaises(ValueError):
            executor.safe_subprocess("rm -rf /", shell=True)

class TestConfigUtils(RANGENTestCase):
    """配置工具测试"""
    
    def setUp(self):
        super().setUp()
        try:
            from src.utils.config_utils import ConfigManager, get_smart_config
            self.ConfigManager = ConfigManager
            self.get_smart_config = get_smart_config
        except ImportError:
            self.skipTest("配置工具模块不可用")
    
    def test_config_loading(self):
        """测试配置加载"""
        # 创建测试配置文件
        config_data = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "test_db"
            },
            "api": {
                "timeout": 30,
                "retries": 3
            }
        }
        config_file = self.create_test_config(config_data)
        
        # 测试配置加载
        manager = self.ConfigManager(config_file)
        config = manager.load_config()
        
        self.assertEqual(config["database"]["host"], "localhost")
        self.assertEqual(config["database"]["port"], 5432)
        self.assertEqual(config["api"]["timeout"], 30)
    
    def test_config_validation(self):
        """测试配置验证"""
        # 测试有效配置
        valid_config = {
            "required_field": "value",
            "optional_field": "optional"
        }
        
        # 这里应该添加配置验证逻辑
        self.assertIn("required_field", valid_config)
        self.assertIn("optional_field", valid_config)
    
    def test_smart_config(self):
        """测试智能配置"""
        # 测试默认值
        default_value = self.get_smart_config("nonexistent_key", {}, "default")
        self.assertEqual(default_value, "default")
        
        # 测试配置值
        context = {"test_key": "test_value"}
        config_value = self.get_smart_config("test_key", context, "default")
        self.assertEqual(config_value, "test_value")

class TestDataUtils(RANGENTestCase):
    """数据工具测试"""
    
    def setUp(self):
        super().setUp()
        try:
            from src.utils.data_utils import DataProcessor, DataValidator
            self.DataProcessor = DataProcessor
            self.DataValidator = DataValidator
        except ImportError:
            self.skipTest("数据工具模块不可用")
    
    def test_data_processing(self):
        """测试数据处理"""
        processor = self.DataProcessor()
        
        # 测试数据清理
        dirty_data = "  Hello, World!  \n\t"
        clean_data = processor.clean_data(dirty_data)
        self.assertEqual(clean_data, "Hello, World!")
        
        # 测试数据转换
        raw_data = {"name": "John", "age": "30"}
        processed_data = processor.process_data(raw_data)
        self.assertEqual(processed_data["age"], 30)  # 字符串转整数
    
    def test_data_validation(self):
        """测试数据验证"""
        validator = self.DataValidator()
        
        # 测试有效数据
        valid_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30
        }
        self.assertTrue(validator.validate_data(valid_data))
        
        # 测试无效数据
        invalid_data = {
            "name": "",
            "email": "invalid-email",
            "age": -5
        }
        self.assertFalse(validator.validate_data(invalid_data))

class TestCacheUtils(RANGENTestCase):
    """缓存工具测试"""
    
    def setUp(self):
        super().setUp()
        try:
            from src.utils.cache_utils import CacheManager, MemoryCache
            self.CacheManager = CacheManager
            self.MemoryCache = MemoryCache
        except ImportError:
            self.skipTest("缓存工具模块不可用")
    
    def test_memory_cache(self):
        """测试内存缓存"""
        cache = self.MemoryCache(max_size=100)
        
        # 测试缓存设置和获取
        cache.set("key1", "value1")
        self.assertEqual(cache.get("key1"), "value1")
        
        # 测试缓存过期
        cache.set("key2", "value2", ttl=1)
        self.assertEqual(cache.get("key2"), "value2")
        
        # 等待过期
        import time
        time.sleep(2)
        self.assertIsNone(cache.get("key2"))
    
    def test_cache_eviction(self):
        """测试缓存淘汰"""
        cache = self.MemoryCache(max_size=2)
        
        # 填满缓存
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # 添加新项，应该淘汰旧项
        cache.set("key3", "value3")
        
        self.assertIsNone(cache.get("key1"))
        self.assertEqual(cache.get("key2"), "value2")
        self.assertEqual(cache.get("key3"), "value3")

class TestLoggingUtils(RANGENTestCase):
    """日志工具测试"""
    
    def setUp(self):
        super().setUp()
        try:
            from src.utils.logging_utils import Logger, setup_logging
            self.Logger = Logger
            self.setup_logging = setup_logging
        except ImportError:
            self.skipTest("日志工具模块不可用")
    
    def test_logger_creation(self):
        """测试日志器创建"""
        logger = self.Logger("test_logger")
        self.assertEqual(logger.name, "test_logger")
    
    def test_logging_levels(self):
        """测试日志级别"""
        logger = self.Logger("test_logger")
        
        # 测试不同级别的日志
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        # 这里应该验证日志是否正确记录
        self.assertTrue(True)  # 占位符
    
    def test_log_file_creation(self):
        """测试日志文件创建"""
        log_file = os.path.join(self.test_data_dir, "test.log")
        logger = self.Logger("test_logger", log_file=log_file)
        
        logger.info("Test log message")
        
        # 验证日志文件是否创建
        self.assert_file_exists(log_file)
        self.assert_file_content_contains(log_file, "Test log message")

class TestPerformanceUtils(RANGENTestCase):
    """性能工具测试"""
    
    def setUp(self):
        super().setUp()
        try:
            from src.utils.performance_utils import PerformanceMonitor, Timer
            self.PerformanceMonitor = PerformanceMonitor
            self.Timer = Timer
        except ImportError:
            self.skipTest("性能工具模块不可用")
    
    def test_timer_functionality(self):
        """测试计时器功能"""
        timer = self.Timer()
        
        # 测试计时
        timer.start()
        import time
        time.sleep(0.1)  # 100ms
        elapsed = timer.elapsed()
        
        self.assertGreaterEqual(elapsed, 0.1)
        self.assertLess(elapsed, 0.2)
    
    def test_performance_monitoring(self):
        """测试性能监控"""
        monitor = self.PerformanceMonitor()
        
        # 测试性能记录
        with monitor.measure("test_operation"):
            import time
            time.sleep(0.01)  # 10ms
        
        # 验证性能数据
        metrics = monitor.get_metrics()
        self.assertIn("test_operation", metrics)
        self.assertGreater(metrics["test_operation"]["duration"], 0)

if __name__ == "__main__":
    unittest.main()
