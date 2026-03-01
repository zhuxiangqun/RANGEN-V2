#!/usr/bin/env python3
"""
系统集成测试 - 验证改进后的核心系统
"""

import time
import logging
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json

# 导入核心组件
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.research_executor import ResearchExecutor, ResearchRequest
from core.performance_optimizer import PerformanceOptimizer
from core.security_enhancer import SecurityEnhancer
from core.code_quality_enhancer import CodeQualityEnhancer
from agents.agent_template import AgentTemplate
from utils.truly_intelligent_learning import TrulyIntelligentLearning
from utils.unified_synergy_manager import UnifiedSynergyManager


@dataclass
class TestResult:
    """测试结果"""
    test_name: str
    success: bool
    execution_time: float
    error_message: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None


class SystemIntegrationTest:
    """系统集成测试"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_results = []
        self.components = {}
        self.initialize_components()
    
    def initialize_components(self):
        """初始化测试组件"""
        try:
            # 初始化核心组件
            self.components['research_executor'] = ResearchExecutor()
            self.components['performance_optimizer'] = PerformanceOptimizer()
            self.components['security_enhancer'] = SecurityEnhancer()
            self.components['code_quality_enhancer'] = CodeQualityEnhancer()
            self.components['intelligent_learning'] = TrulyIntelligentLearning()
            self.components['synergy_manager'] = UnifiedSynergyManager()
            
            # 初始化智能体
            self.components['test_agent'] = AgentTemplate()
            
            self.logger.info("所有组件初始化完成")
        except Exception as e:
            self.logger.error(f"组件初始化失败: {e}")
            raise
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        self.logger.info("开始系统集成测试")
        start_time = time.time()
        
        # 运行各项测试
        tests = [
            self.test_component_initialization,
            self.test_research_executor,
            self.test_performance_optimizer,
            self.test_security_enhancer,
            self.test_code_quality_enhancer,
            self.test_intelligent_learning,
            self.test_agent_template,
            self.test_synergy_manager,
            self.test_integration_workflow,
            self.test_error_handling,
            self.test_performance_under_load
        ]
        
        for test_func in tests:
            try:
                test_func()
            except Exception as e:
                self.logger.error(f"测试 {test_func.__name__} 失败: {e}")
                self.test_results.append(TestResult(
                    test_name=test_func.__name__,
                    success=False,
                    execution_time=0.0,
                    error_message=str(e)
                ))
        
        # 生成测试报告
        total_time = time.time() - start_time
        success_count = sum(1 for result in self.test_results if result.success)
        total_count = len(self.test_results)
        
        report = {
            "total_tests": total_count,
            "successful_tests": success_count,
            "failed_tests": total_count - success_count,
            "success_rate": (success_count / total_count * 100) if total_count > 0 else 0,
            "total_execution_time": total_time,
            "test_results": [
                {
                    "test_name": result.test_name,
                    "success": result.success,
                    "execution_time": result.execution_time,
                    "error_message": result.error_message,
                    "metrics": result.metrics
                }
                for result in self.test_results
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        return report
    
    def test_component_initialization(self):
        """测试组件初始化"""
        start_time = time.time()
        
        try:
            # 验证所有组件都已正确初始化
            required_components = [
                'research_executor', 'performance_optimizer', 'security_enhancer',
                'code_quality_enhancer', 'intelligent_learning', 'synergy_manager', 'test_agent'
            ]
            
            for component_name in required_components:
                if component_name not in self.components:
                    raise ValueError(f"组件 {component_name} 未初始化")
                
                component = self.components[component_name]
                if component is None:
                    raise ValueError(f"组件 {component_name} 为 None")
            
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="test_component_initialization",
                success=True,
                execution_time=execution_time,
                metrics={"initialized_components": len(self.components)}
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="test_component_initialization",
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            ))
    
    def test_research_executor(self):
        """测试研究执行器"""
        start_time = time.time()
        
        try:
            executor = self.components['research_executor']
            
            # 初始化执行器
            if not executor.initialize():
                raise ValueError("研究执行器初始化失败")
            
            # 启动执行器
            if not executor.start():
                raise ValueError("研究执行器启动失败")
            
            # 测试执行研究任务
            request = ResearchRequest(
                query="测试查询",
                context={"test": True},
                user_id="test_user"
            )
            
            response = executor.execute_research(request)
            
            # 验证响应
            if not response or not response.result:
                raise ValueError("研究执行器返回无效响应")
            
            # 测试健康检查
            health = executor.health_check()
            if not health.get("healthy", False):
                raise ValueError("研究执行器健康检查失败")
            
            # 测试性能指标
            metrics = executor.get_metrics()
            if not metrics:
                raise ValueError("无法获取性能指标")
            
            # 停止执行器
            if not executor.stop():
                raise ValueError("研究执行器停止失败")
            
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="test_research_executor",
                success=True,
                execution_time=execution_time,
                metrics={
                    "response_confidence": response.confidence,
                    "processing_time": response.processing_time,
                    "health_status": health.get("healthy", False)
                }
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="test_research_executor",
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            ))
    
    def test_performance_optimizer(self):
        """测试性能优化器"""
        start_time = time.time()
        
        try:
            optimizer = self.components['performance_optimizer']
            
            # 启动性能监控
            optimizer.start_monitoring(interval=0.1)
            time.sleep(0.5)  # 等待监控数据
            
            # 测试函数优化
            def test_function(x):
                return x * x + 2 * x + 1
            
            result = optimizer.optimize_function(
                test_function, 
                optimizer.OptimizationStrategy.CACHING, 
                5
            )
            
            if not result.success:
                raise ValueError("性能优化失败")
            
            # 获取性能报告
            report = optimizer.get_performance_report()
            if not report:
                raise ValueError("无法获取性能报告")
            
            # 停止监控
            optimizer.stop_monitoring()
            
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="test_performance_optimizer",
                success=True,
                execution_time=execution_time,
                metrics={
                    "improvement_percentage": result.improvement_percentage,
                    "optimization_time": result.optimization_time
                }
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="test_performance_optimizer",
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            ))
    
    def test_security_enhancer(self):
        """测试安全增强器"""
        start_time = time.time()
        
        try:
            security = self.components['security_enhancer']
            
            # 测试输入验证
            test_inputs = [
                "正常输入",
                "<script>alert('xss')</script>",
                "SELECT * FROM users",
                "正常输入<script>alert('test')</script>"
            ]
            
            validation_results = []
            for test_input in test_inputs:
                result = security.validate_input(test_input)
                validation_results.append(result)
            
            # 测试数据加密
            test_data = "敏感数据"
            encrypted = security.encrypt_data(test_data)
            decrypted = security.decrypt_data(encrypted)
            
            if decrypted != test_data:
                raise ValueError("数据加密/解密失败")
            
            # 测试密码哈希
            password = "test_password"
            hash_result = security.hash_password(password)
            if not security.verify_password(password, hash_result["hash"], hash_result["salt"]):
                raise ValueError("密码哈希验证失败")
            
            # 测试令牌生成和验证
            token = security.generate_token("test_user", 3600)
            token_payload = security.verify_token(token)
            if not token_payload or token_payload["user_id"] != "test_user":
                raise ValueError("令牌验证失败")
            
            # 获取安全报告
            report = security.get_security_report()
            if not report:
                raise ValueError("无法获取安全报告")
            
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="test_security_enhancer",
                success=True,
                execution_time=execution_time,
                metrics={
                    "validation_tests": len(validation_results),
                    "encryption_success": True,
                    "password_hash_success": True,
                    "token_verification_success": True
                }
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="test_security_enhancer",
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            ))
    
    def test_code_quality_enhancer(self):
        """测试代码质量增强器"""
        start_time = time.time()
        
        try:
            quality_enhancer = self.components['code_quality_enhancer']
            
            # 测试文件分析
            test_file = "src/core/research_executor.py"
            metrics = quality_enhancer.analyze_file(test_file)
            
            if not metrics or metrics.quality_score < 0:
                raise ValueError("代码质量分析失败")
            
            # 测试目录分析
            directory_metrics = quality_enhancer.analyze_directory("src/core")
            if not directory_metrics or directory_metrics.get("status") == "no_data":
                raise ValueError("目录分析失败")
            
            # 测试代码修复
            fix_result = quality_enhancer.fix_common_issues(test_file)
            if not isinstance(fix_result, bool):
                raise ValueError("代码修复返回无效结果")
            
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="test_code_quality_enhancer",
                success=True,
                execution_time=execution_time,
                metrics={
                    "file_quality_score": metrics.quality_score,
                    "lines_of_code": metrics.lines_of_code,
                    "issues_count": metrics.issues_count,
                    "fix_success": fix_result
                }
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="test_code_quality_enhancer",
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            ))
    
    def test_intelligent_learning(self):
        """测试智能学习模块"""
        start_time = time.time()
        
        try:
            learning = self.components['intelligent_learning']
            
            # 测试学习功能
            test_data = [1, 2, 3, 4, 5, 4, 3, 2, 1]
            context = {"test": True, "sequence_type": "numeric"}
            
            result = learning.learn_from_data(test_data, context)
            
            if not result.success:
                raise ValueError("智能学习失败")
            
            # 测试预测功能
            prediction = learning.predict([1, 2, 3])
            if not prediction or "predictions" not in prediction:
                raise ValueError("预测功能失败")
            
            # 测试学习统计
            stats = learning.get_learning_stats()
            if not stats:
                raise ValueError("无法获取学习统计")
            
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="test_intelligent_learning",
                success=True,
                execution_time=execution_time,
                metrics={
                    "learning_confidence": result.confidence,
                    "patterns_learned": result.pattern_id,
                    "prediction_count": len(prediction.get("predictions", [])),
                    "total_patterns": stats.get("total_patterns", 0)
                }
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="test_intelligent_learning",
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            ))
    
    def test_agent_template(self):
        """测试智能体模板"""
        start_time = time.time()
        
        try:
            agent = self.components['test_agent']
            
            # 测试任务执行
            test_task = "测试任务"
            result = agent.execute_task(test_task)
            
            if not result:
                raise ValueError("智能体任务执行失败")
            
            # 测试性能指标
            metrics = agent.get_performance_metrics()
            if not metrics:
                raise ValueError("无法获取智能体性能指标")
            
            # 测试异步执行
            async_result = agent.async_execute_task(test_task)
            if not async_result:
                raise ValueError("异步任务执行失败")
            
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="test_agent_template",
                success=True,
                execution_time=execution_time,
                metrics={
                    "task_execution_success": True,
                    "async_execution_success": True,
                    "execution_stats": metrics.get("execution_stats", {})
                }
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="test_agent_template",
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            ))
    
    def test_synergy_manager(self):
        """测试协同管理器"""
        start_time = time.time()
        
        try:
            synergy_manager = self.components['synergy_manager']
            
            # 测试协同配置
            from src.utils.unified_synergy_manager import SynergyType, SynergyConfig
            
            config = SynergyConfig(
                synergy_type=SynergyType.ML_RL,
                parameters={"learning_rate": 0.01, "exploration_rate": 0.1}
            )
            
            if not synergy_manager.configure_synergy(SynergyType.ML_RL, config):
                raise ValueError("协同配置失败")
            
            # 测试协同历史
            history = synergy_manager.get_synergy_history(10)
            if not history:
                raise ValueError("无法获取协同历史")
            
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="test_synergy_manager",
                success=True,
                execution_time=execution_time,
                metrics={
                    "config_success": True,
                    "history_available": bool(history)
                }
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="test_synergy_manager",
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            ))
    
    def test_integration_workflow(self):
        """测试集成工作流"""
        start_time = time.time()
        
        try:
            # 模拟完整的工作流程
            executor = self.components['research_executor']
            security = self.components['security_enhancer']
            performance = self.components['performance_optimizer']
            
            # 1. 安全验证
            user_input = "用户查询：如何优化系统性能？"
            validation = security.validate_input(user_input)
            
            if not validation["valid"]:
                raise ValueError("输入验证失败")
            
            # 2. 性能优化
            def research_function(query):
                return f"研究结果：{query}"
            
            optimized_result = performance.optimize_function(
                research_function,
                performance.OptimizationStrategy.CACHING,
                user_input
            )
            
            # 3. 研究执行
            if not executor.initialize():
                raise ValueError("执行器初始化失败")
            
            if not executor.start():
                raise ValueError("执行器启动失败")
            
            request = ResearchRequest(
                query=user_input,
                context={"validated": True, "optimized": True}
            )
            
            response = executor.execute_research(request)
            
            if not response or not response.result:
                raise ValueError("研究执行失败")
            
            # 4. 清理
            executor.stop()
            
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="test_integration_workflow",
                success=True,
                execution_time=execution_time,
                metrics={
                    "validation_success": validation["valid"],
                    "optimization_success": optimized_result.success,
                    "research_success": bool(response and response.result),
                    "workflow_complete": True
                }
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="test_integration_workflow",
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            ))
    
    def test_error_handling(self):
        """测试错误处理"""
        start_time = time.time()
        
        try:
            executor = self.components['research_executor']
            
            # 测试无效输入
            invalid_request = ResearchRequest(
                query="",  # 空查询
                context=None
            )
            
            response = executor.execute_research(invalid_request)
            
            # 应该能够处理无效输入而不崩溃
            if not response:
                raise ValueError("无法处理无效输入")
            
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="test_error_handling",
                success=True,
                execution_time=execution_time,
                metrics={
                    "error_handling_success": True,
                    "graceful_degradation": True
                }
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="test_error_handling",
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            ))
    
    def test_performance_under_load(self):
        """测试负载下的性能"""
        start_time = time.time()
        
        try:
            executor = self.components['research_executor']
            performance = self.components['performance_optimizer']
            
            if not executor.initialize() or not executor.start():
                raise ValueError("执行器初始化失败")
            
            # 模拟负载测试
            test_requests = []
            for i in range(10):
                request = ResearchRequest(
                    query=f"负载测试查询 {i}",
                    context={"load_test": True, "request_id": i}
                )
                test_requests.append(request)
            
            # 并发执行
            results = []
            for request in test_requests:
                response = executor.execute_research(request)
                results.append(response)
            
            # 验证所有请求都得到响应
            successful_responses = [r for r in results if r and r.result]
            
            if len(successful_responses) < len(test_requests) * 0.8:  # 80%成功率
                raise ValueError("负载测试成功率过低")
            
            executor.stop()
            
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="test_performance_under_load",
                success=True,
                execution_time=execution_time,
                metrics={
                    "total_requests": len(test_requests),
                    "successful_responses": len(successful_responses),
                    "success_rate": len(successful_responses) / len(test_requests),
                    "average_response_time": sum(r.processing_time for r in successful_responses) / len(successful_responses) if successful_responses else 0
                }
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="test_performance_under_load",
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            ))
    
    def cleanup(self):
        """清理资源"""
        try:
            # 清理所有组件
            for component_name, component in self.components.items():
                if hasattr(component, 'cleanup'):
                    component.cleanup()
                elif hasattr(component, 'stop'):
                    component.stop()
            
            self.logger.info("系统集成测试清理完成")
        except Exception as e:
            self.logger.error(f"清理过程中发生错误: {e}")


def main():
    """主函数"""
    logging.basicConfig(level=logging.INFO)
    
    test = SystemIntegrationTest()
    try:
        report = test.run_all_tests()
        
        # 保存测试报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'system_integration_test_report_{timestamp}.json'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 系统集成测试完成！")
        print(f"📊 测试结果:")
        print(f"  总测试数: {report['total_tests']}")
        print(f"  成功数: {report['successful_tests']}")
        print(f"  失败数: {report['failed_tests']}")
        print(f"  成功率: {report['success_rate']:.1f}%")
        print(f"  总耗时: {report['total_execution_time']:.2f}秒")
        print(f"📄 详细报告已保存到: {report_file}")
        
    finally:
        test.cleanup()


if __name__ == "__main__":
    main()
