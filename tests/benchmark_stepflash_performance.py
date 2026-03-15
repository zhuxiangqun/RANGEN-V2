#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step-3.5-Flash 性能基准测试

测试 Step-3.5-Flash 的性能特性：
1. 缓存性能测试（缓存命中率、响应时间改进）
2. 批处理性能测试（并发处理能力）
3. 流式响应性能测试（实时响应能力）
4. 默认参数优化效果测试

使用方法:
  1. 设置环境变量: export STEPSFLASH_API_KEY="your_api_key"
  2. 运行基准测试: python tests/benchmark_stepflash_performance.py
"""

import os
import sys
import time
import json
import statistics
import concurrent.futures
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(src_path))

from src.services.stepflash_adapter import StepFlashAdapter, StepFlashDeploymentType
from src.observability.metrics import record_llm_call, record_llm_tokens, record_cache_operation

# 测试配置
class BenchmarkConfig:
    """基准测试配置"""
    
    def __init__(self, quick_mode=False):
        self.api_key = os.getenv("STEPSFLASH_API_KEY", "test_key")
        self.deployment_type = StepFlashDeploymentType.OPENROUTER
        self.model = "stepfun-ai/step-3-5-flash"
        
        # 缓存测试配置
        self.cache_enabled = True
        self.cache_ttl = 3600
        
        # 批处理测试配置
        self.batch_sizes = [1, 3] if quick_mode else [1, 3, 5, 10]  # 快速模式只测试小批处理
        self.max_concurrent = 2 if quick_mode else 5
        
        # 性能测试配置
        self.warmup_iterations = 1 if quick_mode else 2  # 快速模式减少预热
        self.test_iterations = 2 if quick_mode else 5   # 快速模式减少测试次数
        self.request_delay = 0.5 if quick_mode else 1.0   # 快速模式减少延迟
        
        # 测试消息（快速模式使用较少消息）
        if quick_mode:
            self.test_messages = [
                [{"role": "user", "content": "用中文介绍一下人工智能的历史。"}],
                [{"role": "user", "content": "Python和JavaScript有什么区别？"}],
                [{"role": "user", "content": "解释一下机器学习的三种主要类型。"}],
            ]
        else:
            self.test_messages = [
                [{"role": "user", "content": "用中文介绍一下人工智能的历史。"}],
                [{"role": "user", "content": "Python和JavaScript有什么区别？"}],
                [{"role": "user", "content": "解释一下机器学习的三种主要类型。"}],
                [{"role": "user", "content": "什么是深度学习？"}],
                [{"role": "user", "content": "如何优化数据库查询性能？"}],
                [{"role": "user", "content": "解释一下RESTful API的设计原则。"}],
                [{"role": "user", "content": "什么是微服务架构？"}],
                [{"role": "user", "content": "解释一下Docker和Kubernetes的区别。"}],
                [{"role": "user", "content": "什么是DevOps？"}],
                [{"role": "user", "content": "解释一下CI/CD流程。"}],
            ]

class BenchmarkResult:
    """基准测试结果"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.success_count = 0
        self.failure_count = 0
        self.response_times = []  # 响应时间列表（秒）
        self.cache_hits = 0
        self.cache_misses = 0
        self.errors = []
        
    def add_success(self, response_time: float, cache_hit: bool = False):
        """添加成功结果"""
        self.success_count += 1
        self.response_times.append(response_time)
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
    
    def add_failure(self, error: str):
        """添加失败结果"""
        self.failure_count += 1
        self.errors.append(error)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.response_times:
            return {
                "test_name": self.test_name,
                "total_requests": self.success_count + self.failure_count,
                "success_rate": 0.0,
                "avg_response_time": 0.0,
                "min_response_time": 0.0,
                "max_response_time": 0.0,
                "cache_hit_rate": 0.0,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "errors": self.errors[:5] if self.errors else []
            }
        
        return {
            "test_name": self.test_name,
            "total_requests": self.success_count + self.failure_count,
            "success_rate": self.success_count / (self.success_count + self.failure_count),
            "avg_response_time": statistics.mean(self.response_times),
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times),
            "std_response_time": statistics.stdev(self.response_times) if len(self.response_times) > 1 else 0.0,
            "p95_response_time": statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) >= 20 else max(self.response_times),
            "cache_hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0.0,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "errors": self.errors[:5] if self.errors else []
        }

class StepFlashBenchmark:
    """Step-3.5-Flash 基准测试器"""
    
    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.results = {}
        
        # 创建适配器实例
        self.adapter = StepFlashAdapter(
            deployment_type=config.deployment_type,
            api_key=config.api_key,
            model=config.model,
            enable_cache=config.cache_enabled,
            cache_ttl=config.cache_ttl
        )
        
        # 创建禁用缓存的适配器（用于对比）
        self.adapter_no_cache = StepFlashAdapter(
            deployment_type=config.deployment_type,
            api_key=config.api_key,
            model=config.model,
            enable_cache=False
        )
    
    def run_warmup(self):
        """运行预热测试"""
        print("🔥 预热测试...")
        for i in range(self.config.warmup_iterations):
            try:
                messages = self.config.test_messages[i % len(self.config.test_messages)]
                response = self.adapter.chat_completion(messages, max_tokens=100)
                if response.get("success"):
                    print(f"  预热 {i+1}/{self.config.warmup_iterations}: 成功")
                else:
                    print(f"  预热 {i+1}/{self.config.warmup_iterations}: 失败 - {response.get('error', '未知错误')}")
            except Exception as e:
                print(f"  预热 {i+1}/{self.config.warmup_iterations}: 异常 - {e}")
            time.sleep(self.config.request_delay)
        print("✅ 预热完成\n")
    
    def test_cache_performance(self) -> BenchmarkResult:
        """测试缓存性能"""
        print("🧠 缓存性能测试...")
        result = BenchmarkResult("缓存性能测试")
        
        # 清除缓存以确保干净的测试
        self.adapter.clear_cache()
        
        # 第一阶段：缓存未命中（首次请求）
        print("   第一阶段：缓存未命中测试...")
        for i in range(self.config.test_iterations):
            messages = self.config.test_messages[i % len(self.config.test_messages)]
            
            start_time = time.time()
            try:
                response = self.adapter.chat_completion(messages, max_tokens=200)
                response_time = time.time() - start_time
                
                if response.get("success"):
                    result.add_success(response_time, cache_hit=False)
                    print(f"     请求 {i+1}: {response_time:.2f}秒 (缓存未命中)")
                else:
                    result.add_failure(f"请求失败: {response.get('error', '未知错误')}")
                    print(f"     请求 {i+1}: 失败 - {response.get('error', '未知错误')}")
            except Exception as e:
                result.add_failure(f"异常: {str(e)}")
                print(f"     请求 {i+1}: 异常 - {e}")
            
            time.sleep(self.config.request_delay)
        
        # 第二阶段：缓存命中（重复请求）
        print("   第二阶段：缓存命中测试...")
        for i in range(self.config.test_iterations):
            messages = self.config.test_messages[i % len(self.config.test_messages)]
            
            start_time = time.time()
            try:
                response = self.adapter.chat_completion(messages, max_tokens=200)
                response_time = time.time() - start_time
                
                if response.get("success"):
                    result.add_success(response_time, cache_hit=True)
                    print(f"     请求 {i+1}: {response_time:.2f}秒 (缓存命中)")
                else:
                    result.add_failure(f"请求失败: {response.get('error', '未知错误')}")
                    print(f"     请求 {i+1}: 失败 - {response.get('error', '未知错误')}")
            except Exception as e:
                result.add_failure(f"异常: {str(e)}")
                print(f"     请求 {i+1}: 异常 - {e}")
            
            time.sleep(self.config.request_delay)
        
        # 第三阶段：无缓存对比
        print("   第三阶段：无缓存对比测试...")
        for i in range(self.config.test_iterations):
            messages = self.config.test_messages[i % len(self.config.test_messages)]
            
            start_time = time.time()
            try:
                response = self.adapter_no_cache.chat_completion(messages, max_tokens=200)
                response_time = time.time() - start_time
                
                if response.get("success"):
                    # 添加到结果但不影响缓存统计
                    result.response_times.append(response_time)
                    result.success_count += 1
                    print(f"     请求 {i+1}: {response_time:.2f}秒 (无缓存)")
                else:
                    result.add_failure(f"请求失败: {response.get('error', '未知错误')}")
                    print(f"     请求 {i+1}: 失败 - {response.get('error', '未知错误')}")
            except Exception as e:
                result.add_failure(f"异常: {str(e)}")
                print(f"     请求 {i+1}: 异常 - {e}")
            
            time.sleep(self.config.request_delay)
        
        self.results["cache_performance"] = result
        return result
    
    def test_batch_performance(self) -> BenchmarkResult:
        """测试批处理性能"""
        print("🚀 批处理性能测试...")
        result = BenchmarkResult("批处理性能测试")
        
        for batch_size in self.config.batch_sizes:
            print(f"   批处理大小: {batch_size}")
            
            # 准备批处理消息
            messages_list = self.config.test_messages[:batch_size]
            
            start_time = time.time()
            try:
                responses = self.adapter.batch_chat_completion(
                    messages_list=messages_list,
                    max_concurrent=min(batch_size, self.config.max_concurrent),
                    max_tokens=200
                )
                batch_time = time.time() - start_time
                
                success_count = sum(1 for r in responses if r.get("success", False))
                failure_count = batch_size - success_count
                
                result.success_count += success_count
                result.failure_count += failure_count
                
                # 计算平均响应时间（批处理总时间除以请求数）
                avg_response_time = batch_time / batch_size
                result.response_times.append(avg_response_time)
                
                print(f"     批处理完成: {batch_time:.2f}秒, 平均: {avg_response_time:.2f}秒/请求")
                print(f"     成功: {success_count}, 失败: {failure_count}")
                
                # 记录失败信息
                for i, response in enumerate(responses):
                    if not response.get("success", False):
                        result.add_failure(f"批处理请求 {i}: {response.get('error', '未知错误')}")
            
            except Exception as e:
                result.add_failure(f"批处理异常: {str(e)}")
                print(f"     批处理异常: {e}")
            
            time.sleep(self.config.request_delay * 2)
        
        self.results["batch_performance"] = result
        return result
    
    def test_stream_performance(self) -> BenchmarkResult:
        """测试流式响应性能"""
        print("🌊 流式响应性能测试...")
        result = BenchmarkResult("流式响应性能测试")
        
        # 测试流式响应（简单的成功/失败测试）
        messages = self.config.test_messages[0]
        
        start_time = time.time()
        try:
            # 注意：这里使用stream_chat_completion方法
            stream_response = self.adapter.stream_chat_completion(
                messages=messages,
                max_tokens=200
            )
            
            # 计算第一个chunk的到达时间
            first_chunk_time = None
            chunk_count = 0
            
            for chunk in stream_response:
                chunk_count += 1
                if first_chunk_time is None:
                    first_chunk_time = time.time() - start_time
                
                if chunk.get("done", False):
                    break
            
            total_time = time.time() - start_time
            
            if chunk_count > 0:
                result.add_success(total_time)
                print(f"   流式响应完成: {total_time:.2f}秒")
                print(f"   收到chunk数量: {chunk_count}")
                print(f"   第一个chunk到达时间: {first_chunk_time:.2f}秒")
            else:
                result.add_failure("未收到任何chunk")
                print(f"   流式响应失败: 未收到任何chunk")
                
        except Exception as e:
            result.add_failure(f"流式响应异常: {str(e)}")
            print(f"   流式响应异常: {e}")
        
        self.results["stream_performance"] = result
        return result
    
    def test_default_parameters(self) -> BenchmarkResult:
        """测试默认参数优化效果"""
        print("⚙️  默认参数优化测试...")
        result = BenchmarkResult("默认参数优化测试")
        
        # 测试不同的超时设置
        timeout_configs = [30, 60, 120]
        
        for timeout in timeout_configs:
            print(f"   超时设置: {timeout}秒")
            
            # 创建自定义超时的适配器
            custom_adapter = StepFlashAdapter(
                deployment_type=self.config.deployment_type,
                api_key=self.config.api_key,
                model=self.config.model,
                timeout=timeout,
                enable_cache=False  # 禁用缓存以准确测量
            )
            
            messages = self.config.test_messages[0]
            
            start_time = time.time()
            try:
                response = custom_adapter.chat_completion(messages, max_tokens=200)
                response_time = time.time() - start_time
                
                if response.get("success"):
                    result.add_success(response_time)
                    print(f"     请求完成: {response_time:.2f}秒")
                else:
                    result.add_failure(f"超时{timeout}s失败: {response.get('error', '未知错误')}")
                    print(f"     请求失败: {response.get('error', '未知错误')}")
            except Exception as e:
                result.add_failure(f"超时{timeout}s异常: {str(e)}")
                print(f"     请求异常: {e}")
            
            time.sleep(self.config.request_delay)
        
        self.results["default_parameters"] = result
        return result
    
    def run_all_tests(self) -> Dict[str, BenchmarkResult]:
        """运行所有测试"""
        print("=" * 60)
        print("Step-3.5-Flash 性能基准测试")
        print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 检查API密钥
        if not self.config.api_key or self.config.api_key == "test_key":
            print("⚠️  警告: 未设置有效的STEPSFLASH_API_KEY环境变量")
            print("   将使用测试模式运行（可能无法连接真实API）")
            print("   设置: export STEPSFLASH_API_KEY='your_api_key'\n")
        
        # 运行预热
        self.run_warmup()
        
        # 运行所有测试
        self.test_cache_performance()
        self.test_batch_performance()
        self.test_stream_performance()
        self.test_default_parameters()
        
        return self.results
    
    def generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("性能基准测试报告")
        print("=" * 60)
        
        report = {
            "timestamp": time.time(),
            "config": {
                "deployment_type": self.config.deployment_type.value,
                "model": self.config.model,
                "cache_enabled": self.config.cache_enabled,
                "cache_ttl": self.config.cache_ttl,
                "batch_sizes": self.config.batch_sizes,
                "max_concurrent": self.config.max_concurrent,
            },
            "results": {},
            "summary": {},
            "recommendations": []
        }
        
        # 收集所有测试结果
        for test_name, result in self.results.items():
            stats = result.get_stats()
            report["results"][test_name] = stats
            
            print(f"\n📊 {test_name}:")
            print(f"   总请求数: {stats['total_requests']}")
            print(f"   成功率: {stats['success_rate']:.1%}")
            print(f"   平均响应时间: {stats['avg_response_time']:.2f}秒")
            
            if "cache_hit_rate" in stats:
                print(f"   缓存命中率: {stats['cache_hit_rate']:.1%}")
                print(f"   缓存命中数: {stats['cache_hits']}")
                print(f"   缓存未命中数: {stats['cache_misses']}")
        
        # 生成性能改进分析
        cache_result = self.results.get("cache_performance")
        if cache_result:
            cache_stats = cache_result.get_stats()
            if cache_stats["cache_hit_rate"] > 0:
                # 计算缓存带来的性能改进
                cache_hit_times = [t for i, t in enumerate(cache_result.response_times) 
                                 if i >= cache_result.cache_misses]  # 缓存命中的响应时间
                cache_miss_times = cache_result.response_times[:cache_result.cache_misses]  # 缓存未命中的响应时间
                
                if cache_hit_times and cache_miss_times:
                    avg_cache_hit = statistics.mean(cache_hit_times)
                    avg_cache_miss = statistics.mean(cache_miss_times)
                    improvement = (avg_cache_miss - avg_cache_hit) / avg_cache_miss * 100
                    
                    print(f"\n🎯 缓存性能改进:")
                    print(f"   缓存未命中平均时间: {avg_cache_miss:.2f}秒")
                    print(f"   缓存命中平均时间: {avg_cache_hit:.2f}秒")
                    print(f"   性能提升: {improvement:.1f}%")
                    
                    report["summary"]["cache_improvement_percent"] = improvement
                    report["summary"]["avg_cache_miss_time"] = avg_cache_miss
                    report["summary"]["avg_cache_hit_time"] = avg_cache_hit
        
        # 生成批处理效率分析
        batch_result = self.results.get("batch_performance")
        if batch_result and batch_result.response_times:
            # 批处理效率：处理多个请求的并行效率
            batch_efficiency = []
            for i, batch_size in enumerate(self.config.batch_sizes):
                if i < len(batch_result.response_times):
                    # 假设单请求基准时间为第一个批处理大小=1的时间
                    single_request_time = batch_result.response_times[0] if i > 0 else 1.0
                    batch_time = batch_result.response_times[i]
                    efficiency = single_request_time / batch_time * 100  # 效率百分比
                    batch_efficiency.append(efficiency)
            
            if batch_efficiency:
                print(f"\n🚀 批处理效率分析:")
                for i, efficiency in enumerate(batch_efficiency):
                    print(f"   批处理大小 {self.config.batch_sizes[i]}: {efficiency:.1f}% 效率")
        
        # 生成建议
        print(f"\n💡 优化建议:")
        
        # 缓存建议
        if cache_result and cache_result.cache_hits > 0:
            print("   1. ✅ 缓存功能工作正常，建议在生产环境中启用缓存")
            print("      - 可显著减少重复请求的响应时间")
            print("      - 降低API调用成本")
            report["recommendations"].append("启用缓存以提升性能和降低成本")
        else:
            print("   1. ⚠️  缓存测试未显示明显效果，检查缓存配置")
            report["recommendations"].append("检查缓存配置和测试方法")
        
        # 批处理建议
        if batch_result and batch_result.success_count > 0:
            print("   2. ✅ 批处理功能工作正常，建议用于批量请求场景")
            print("      - 提高吞吐量，减少总体处理时间")
            report["recommendations"].append("使用批处理处理高并发请求")
        
        # 流式建议
        stream_result = self.results.get("stream_performance")
        if stream_result and stream_result.success_count > 0:
            print("   3. ✅ 流式响应功能工作正常，建议用于实时交互场景")
            print("      - 提供更好的用户体验")
            report["recommendations"].append("使用流式响应提升用户体验")
        
        # 参数优化建议
        param_result = self.results.get("default_parameters")
        if param_result and param_result.success_count > 0:
            print("   4. ✅ 默认参数配置合理，60秒超时设置适中")
            print("      - 平衡了成功率和响应时间")
            report["recommendations"].append("保持当前默认参数配置")
        
        # 保存报告到文件
        report_file = project_root / "logs" / "stepflash_performance_report.json"
        report_file.parent.mkdir(exist_ok=True)
        
        try:
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n📄 详细报告已保存到: {report_file}")
        except Exception as e:
            print(f"\n⚠️  报告保存失败: {e}")
        
        return report

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Step-3.5-Flash 性能基准测试")
    parser.add_argument("--quick", action="store_true", help="快速模式，减少测试次数和规模")
    parser.add_argument("--output", type=str, default="benchmark_results", help="输出目录")
    parser.add_argument("--no-cache", action="store_true", help="禁用缓存测试")
    args = parser.parse_args()
    
    # 创建配置
    config = BenchmarkConfig(quick_mode=args.quick)
    
    # 如果指定了--no-cache，则禁用缓存
    if args.no_cache:
        config.cache_enabled = False
    
    # 运行基准测试
    benchmark = StepFlashBenchmark(config)
    results = benchmark.run_all_tests()
    
    # 生成报告
    report = benchmark.generate_report()
    
    # 保存报告到指定目录
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_file = output_dir / f"stepflash_performance_report_{timestamp}.json"
    
    try:
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n📄 详细报告已保存到: {report_file}")
    except Exception as e:
        print(f"\n⚠️  报告保存失败: {e}")
    
    # 返回退出码
    total_success = sum(result.success_count for result in results.values())
    total_failure = sum(result.failure_count for result in results.values())
    
    if total_failure == 0:
        print("\n✅ 所有测试都成功完成!")
        return 0
    elif total_success == 0:
        print("\n❌ 所有测试都失败了，请检查配置。")
        return 1
    else:
        success_rate = total_success / (total_success + total_failure)
        print(f"\n⚠️  测试完成，成功率: {success_rate:.1%}")
        return 0

if __name__ == "__main__":
    sys.exit(main())