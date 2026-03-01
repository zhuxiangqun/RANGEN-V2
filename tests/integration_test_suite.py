"""
RANGEN系统综合测试套件
测试新架构的完整工作流程和依赖注入系统
"""
import sys
import os
import time
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.bootstrap.application_bootstrap import bootstrap_application, get_service, shutdown_application
from src.interfaces.core_interfaces import IAgent, IConfigManager, IThresholdManager
from src.utils.performance_monitor import PerformanceMonitor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegrationTestSuite:
    """综合测试套件"""
    
    def __init__(self):
        self.test_results = {}
        self.performance_monitor = PerformanceMonitor()
        self.test_count = 0
        self.passed_count = 0
        self.failed_count = 0
        
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始运行RANGEN系统综合测试套件...")
        
        # 测试应用启动
        self._test_application_bootstrap()
        
        # 测试核心服务
        self._test_core_services()
        
        # 测试智能体系统
        self._test_agent_system()
        
        # 测试工具模块
        self._test_tool_modules()
        
        # 测试性能
        self._test_performance()
        
        # 测试错误处理
        self._test_error_handling()
        
        # 生成测试报告
        self._generate_test_report()
        
        return self.test_results
    
    def _test_application_bootstrap(self):
        """测试应用启动"""
        logger.info("🧪 测试应用启动...")
        
        try:
            # 测试应用启动
            start_time = time.time()
            success = bootstrap_application()
            bootstrap_time = time.time() - start_time
            
            if success:
                self._record_test_result("应用启动", True, f"启动成功，耗时: {bootstrap_time:.4f}s")
                logger.info(f"✅ 应用启动成功，耗时: {bootstrap_time:.4f}s")
            else:
                self._record_test_result("应用启动", False, "启动失败")
                logger.error("❌ 应用启动失败")
                
        except Exception as e:
            self._record_test_result("应用启动", False, f"启动异常: {str(e)}")
            logger.error(f"❌ 应用启动异常: {e}")
    
    def _test_core_services(self):
        """测试核心服务"""
        logger.info("🧪 测试核心服务...")
        
        services_to_test = [
            ("配置管理器", IConfigManager),
            ("阈值管理器", IThresholdManager),
        ]
        
        for service_name, service_type in services_to_test:
            try:
                start_time = time.time()
                service = get_service(service_type)
                get_time = time.time() - start_time
                
                if service is not None:
                    self._record_test_result(f"获取{service_name}", True, f"获取成功，耗时: {get_time:.4f}s")
                    logger.info(f"✅ 获取{service_name}成功，耗时: {get_time:.4f}s")
                else:
                    self._record_test_result(f"获取{service_name}", False, "服务为None")
                    logger.error(f"❌ 获取{service_name}失败: 服务为None")
                    
            except Exception as e:
                self._record_test_result(f"获取{service_name}", False, f"获取异常: {str(e)}")
                logger.error(f"❌ 获取{service_name}异常: {e}")
    
    def _test_agent_system(self):
        """测试智能体系统"""
        logger.info("🧪 测试智能体系统...")
        
        try:
            # 获取智能体服务
            start_time = time.time()
            agent = get_service(IAgent)
            get_time = time.time() - start_time
            
            if agent is not None:
                self._record_test_result("获取智能体", True, f"获取成功，耗时: {get_time:.4f}s")
                logger.info(f"✅ 获取智能体成功，耗时: {get_time:.4f}s")
                
                # 测试智能体执行
                self._test_agent_execution(agent)
            else:
                self._record_test_result("获取智能体", False, "智能体为None")
                logger.error("❌ 获取智能体失败: 智能体为None")
                
        except Exception as e:
            self._record_test_result("获取智能体", False, f"获取异常: {str(e)}")
            logger.error(f"❌ 获取智能体异常: {e}")
    
    def _test_agent_execution(self, agent):
        """测试智能体执行"""
        try:
            # 准备测试任务
            test_task = {
                'task_type': 'test',
                'query': '这是一个测试任务',
                'parameters': {'test_param': 'test_value'}
            }
            
            # 测试同步执行
            start_time = time.time()
            sync_result = agent.execute(test_task)
            sync_time = time.time() - start_time
            
            if sync_result and isinstance(sync_result, dict):
                self._record_test_result("智能体同步执行", True, f"执行成功，耗时: {sync_time:.4f}s")
                logger.info(f"✅ 智能体同步执行成功，耗时: {sync_time:.4f}s")
            else:
                self._record_test_result("智能体同步执行", False, "执行结果无效")
                logger.error("❌ 智能体同步执行失败: 执行结果无效")
            
            # 测试异步执行（如果支持）
            if hasattr(agent, 'execute_async'):
                try:
                    import asyncio
                    start_time = time.time()
                    
                    # 创建新的事件循环进行测试
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        async_result = loop.run_until_complete(agent.execute_async(test_task))
                        async_time = time.time() - start_time
                        
                        if async_result and isinstance(async_result, dict):
                            self._record_test_result("智能体异步执行", True, f"执行成功，耗时: {async_time:.4f}s")
                            logger.info(f"✅ 智能体异步执行成功，耗时: {async_time:.4f}s")
                        else:
                            self._record_test_result("智能体异步执行", False, "执行结果无效")
                            logger.error("❌ 智能体异步执行失败: 执行结果无效")
                    finally:
                        loop.close()
                        
                except Exception as e:
                    self._record_test_result("智能体异步执行", False, f"执行异常: {str(e)}")
                    logger.error(f"❌ 智能体异步执行异常: {e}")
            else:
                self._record_test_result("智能体异步执行", True, "不支持异步执行（跳过）")
                logger.info("ℹ️ 智能体不支持异步执行，跳过测试")
                
        except Exception as e:
            self._record_test_result("智能体执行", False, f"执行异常: {str(e)}")
            logger.error(f"❌ 智能体执行异常: {e}")
    
    def _test_tool_modules(self):
        """测试工具模块"""
        logger.info("🧪 测试工具模块...")
        
        # 测试一些关键工具模块
        tools_to_test = [
            ("智能策略融合工具", "src.utils.intelligent_strategy_fusion", "IntelligentStrategyFusion"),
            ("真正智能学习工具", "src.utils.truly_intelligent_learning", "TrulyIntelligentLearning"),
            ("统一智能评分器", "src.utils.unified_intelligent_scorer", "UnifiedIntelligentScorer"),
        ]
        
        for tool_name, module_path, class_name in tools_to_test:
            try:
                start_time = time.time()
                
                # 动态导入模块
                module = __import__(module_path, fromlist=[class_name])
                tool_class = getattr(module, class_name)
                tool_instance = tool_class()
                
                test_time = time.time() - start_time
                
                self._record_test_result(f"工具模块: {tool_name}", True, f"测试成功，耗时: {test_time:.4f}s")
                logger.info(f"✅ 工具模块 {tool_name} 测试成功，耗时: {test_time:.4f}s")
                
            except Exception as e:
                self._record_test_result(f"工具模块: {tool_name}", False, f"测试失败: {str(e)}")
                logger.error(f"❌ 工具模块 {tool_name} 测试失败: {e}")
    
    def _test_performance(self):
        """测试性能"""
        logger.info("🧪 测试系统性能...")
        
        try:
            # 测试服务获取性能
            start_time = time.time()
            config_manager = get_service(IConfigManager)
            threshold_manager = get_service(IThresholdManager)
            agent = get_service(IAgent)
            get_time = time.time() - start_time
            
            if all([config_manager, threshold_manager, agent]):
                self._record_test_result("批量服务获取", True, f"获取成功，耗时: {get_time:.4f}s")
                logger.info(f"✅ 批量服务获取成功，耗时: {get_time:.4f}s")
            else:
                self._record_test_result("批量服务获取", False, "部分服务获取失败")
                logger.error("❌ 批量服务获取失败: 部分服务为None")
                
        except Exception as e:
            self._record_test_result("批量服务获取", False, f"获取异常: {str(e)}")
            logger.error(f"❌ 批量服务获取异常: {e}")
    
    def _test_error_handling(self):
        """测试错误处理"""
        logger.info("🧪 测试错误处理...")
        
        try:
            # 测试获取不存在的服务
            start_time = time.time()
            try:
                # 尝试获取一个不存在的服务类型
                non_existent_service = get_service(type("NonExistentService", (), {}))
                if non_existent_service is None:
                    self._record_test_result("错误处理: 不存在服务", True, "正确处理了不存在的服务")
                    logger.info("✅ 错误处理测试通过: 正确处理了不存在的服务")
                else:
                    self._record_test_result("错误处理: 不存在服务", False, "应该返回None")
                    logger.error("❌ 错误处理测试失败: 应该返回None")
            except Exception as e:
                self._record_test_result("错误处理: 不存在服务", True, f"正确处理了异常: {str(e)}")
                logger.info(f"✅ 错误处理测试通过: 正确处理了异常: {e}")
                
        except Exception as e:
            self._record_test_result("错误处理测试", False, f"测试异常: {str(e)}")
            logger.error(f"❌ 错误处理测试异常: {e}")
    
    def _record_test_result(self, test_name: str, success: bool, message: str):
        """记录测试结果"""
        self.test_count += 1
        if success:
            self.passed_count += 1
        else:
            self.failed_count += 1
            
        self.test_results[test_name] = {
            'success': success,
            'message': message,
            'timestamp': time.time()
        }
    
    def _generate_test_report(self):
        """生成测试报告"""
        logger.info("📊 生成测试报告...")
        
        total_tests = self.test_count
        passed_tests = self.passed_count
        failed_tests = self.failed_count
        success_rate = (passed_tests / total_tests * get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit"))) if total_tests > 0 else 0
        
        logger.info("=" * 60)
        logger.info("📋 综合测试报告")
        logger.info("=" * 60)
        logger.info(f"总测试数: {total_tests}")
        logger.info(f"通过测试: {passed_tests}")
        logger.info(f"失败测试: {failed_tests}")
        logger.info(f"成功率: {success_rate:.1f}%")
        logger.info("=" * 60)
        
        # 详细结果
        for test_name, result in self.test_results.items():
            status = "✅" if result['success'] else "❌"
            logger.info(f"{status} {test_name}: {result['message']}")
        
        logger.info("=" * 60)
        
        # 总结
        if success_rate >= 90:
            logger.info("🎉 测试结果优秀！系统运行稳定。")
        elif success_rate >= 80:
            logger.info("👍 测试结果良好，系统基本稳定。")
        elif success_rate >= 70:
            logger.info("⚠️ 测试结果一般，建议进一步优化。")
        else:
            logger.error("❌ 测试结果较差，需要重点关注和修复。")
    
    def cleanup(self):
        """清理资源"""
        try:
            shutdown_application()
            logger.info("🧹 测试完成，已清理资源")
        except Exception as e:
            logger.warning(f"清理资源时出现警告: {e}")

def run_integration_tests():
    """运行综合测试"""
    test_suite = IntegrationTestSuite()
    
    try:
        results = test_suite.run_all_tests()
        return results
    finally:
        test_suite.cleanup()

if __name__ == "__main__":
    run_integration_tests()
