#!/usr/bin/env python3
"""
API密钥真实性验证测试
验证DEEPSEEK_API_KEY是否能真正用于LLM调用
"""

import asyncio
import time
import sys
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class APIKeyValidator:
    """API密钥验证器"""

    def __init__(self):
        self.test_queries = [
            "Hello, can you respond with a simple greeting?",
            "What is 2+2?",
            "Say 'test successful' if you can read this."
        ]

    def validate_api_key_access(self) -> Dict[str, Any]:
        """验证API密钥访问机制"""

        print("🔐 API密钥访问验证")
        print("=" * 50)

        results = {}

        # 测试1: 环境变量读取
        print("\n📋 测试1: 环境变量读取")
        env_key = os.getenv('DEEPSEEK_API_KEY', '')
        results['env_var'] = {
            'has_key': bool(env_key),
            'key_length': len(env_key) if env_key else 0,
            'key_prefix': env_key[:10] + '...' if env_key else 'None'
        }
        print(f"   环境变量DEEPSEEK_API_KEY: {'✅ 设置' if env_key else '❌ 未设置'}")
        if env_key:
            print(f"   密钥长度: {len(env_key)}")
            print(f"   密钥前缀: {env_key[:10]}...")

        # 测试2: 配置中心读取
        print("\n📋 测试2: 配置中心读取")
        try:
            from src.utils.unified_centers import get_unified_config_center
            config_center = get_unified_config_center()
            config_key = config_center.get_env_config('llm', 'DEEPSEEK_API_KEY', '')
            results['config_center'] = {
                'has_key': bool(config_key),
                'key_length': len(config_key) if config_key else 0,
                'matches_env': config_key == env_key
            }
            print(f"   配置中心读取: {'✅ 成功' if config_key else '❌ 失败'}")
            if config_key:
                print(f"   密钥长度: {len(config_key)}")
                print(f"   与环境变量一致: {'✅ 是' if config_key == env_key else '❌ 否'}")
        except Exception as e:
            results['config_center'] = {'error': str(e)}
            print(f"   配置中心读取异常: {e}")

        # 测试3: 智能配置加载器
        print("\n📋 测试3: 智能配置加载器")
        try:
            from src.core.config_loader import get_deepseek_api_key
            loader_key = get_deepseek_api_key()
            results['smart_loader'] = {
                'has_key': bool(loader_key),
                'key_length': len(loader_key) if loader_key else 0,
                'matches_env': loader_key == env_key
            }
            print(f"   智能加载器读取: {'✅ 成功' if loader_key else '❌ 失败'}")
            if loader_key:
                print(f"   密钥长度: {len(loader_key)}")
                print(f"   与环境变量一致: {'✅ 是' if loader_key == env_key else '❌ 否'}")
        except Exception as e:
            results['smart_loader'] = {'error': str(e)}
            print(f"   智能加载器异常: {e}")

        return results

    async def test_real_api_calls(self) -> Dict[str, Any]:
        """测试真实的API调用"""

        print("\n🔗 API真实调用测试")
        print("=" * 50)

        # 首先验证密钥访问
        access_results = self.validate_api_key_access()

        # 如果没有密钥，直接返回
        if not access_results.get('env_var', {}).get('has_key'):
            print("❌ 跳过API调用测试：没有可用的API密钥")
            return {'error': 'No API key available'}

        try:
            # 初始化LLM集成
            from src.core.llm_integration import LLMIntegration

            config = {
                'llm_provider': 'deepseek',
                'api_key': os.getenv('DEEPSEEK_API_KEY'),  # 使用完整的API密钥
                'model': 'deepseek-chat',
                'base_url': 'https://api.deepseek.com/v1'
            }

            print("\n🚀 初始化LLM集成...")
            llm_client = LLMIntegration(config)

            if not llm_client.api_key:
                print("❌ LLM集成初始化失败：API密钥为空")
                return {'error': 'LLM integration failed: empty API key'}

            print("✅ LLM集成初始化成功")

            # 测试简单调用
            print("\n📤 测试简单API调用...")
            test_query = "Say 'API test successful' in exactly those words."

            start_time = time.time()
            try:
                response = llm_client._call_llm(test_query, max_tokens_override=50)
                end_time = time.time()

                success = bool(response and 'successful' in response.lower())
                response_time = end_time - start_time

                results = {
                    'api_call_success': success,
                    'response_time': response_time,
                    'response_length': len(response) if response else 0,
                    'response_preview': response[:100] if response else 'None',
                    'error': None
                }

                if success:
                    print(f"✅ API调用成功！响应时间: {response_time:.2f}s")
                    print(f"   响应预览: {response[:100]}...")
                else:
                    print(f"❌ API调用失败或响应不符合预期")
                    print(f"   响应内容: {response}")

                return results

            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time

                print(f"❌ API调用异常: {e}")
                return {
                    'api_call_success': False,
                    'response_time': response_time,
                    'error': str(e)
                }

        except Exception as e:
            print(f"❌ 测试设置异常: {e}")
            return {'error': str(e)}

    def generate_validation_report(self, access_results: Dict, api_results: Dict) -> None:
        """生成验证报告"""

        print("\n🎯 API密钥验证报告")
        print("=" * 50)

        # 密钥访问状态
        print("🔑 密钥访问状态:")
        env_ok = access_results.get('env_var', {}).get('has_key', False)
        config_ok = access_results.get('config_center', {}).get('has_key', False)
        loader_ok = access_results.get('smart_loader', {}).get('has_key', False)

        print(f"   环境变量: {'✅' if env_ok else '❌'}")
        print(f"   配置中心: {'✅' if config_ok else '❌'}")
        print(f"   智能加载器: {'✅' if loader_ok else '❌'}")

        # API调用状态
        if 'error' in api_results:
            print(f"\n❌ API测试失败: {api_results['error']}")
            api_success = False
        else:
            api_success = api_results.get('api_call_success', False)
            response_time = api_results.get('response_time', 0)

            print(f"\n🔗 API调用状态:")
            print(f"   调用成功: {'✅' if api_success else '❌'}")
            if api_success:
                print(".2f")
            else:
                print(f"   错误信息: {api_results.get('error', 'Unknown')}")

        # 总体评估
        print("\n🏆 总体评估:")
        if env_ok and api_success:
            print("   ✅ API密钥完全可用！系统可以正常进行LLM调用")
            print("   💡 建议：可以安全地禁用轻量级模式，启用完整功能")
        elif env_ok and not api_success:
            print("   ⚠️ API密钥可访问但调用失败")
            print("   💡 建议：检查网络连接、API额度或密钥有效性")
        elif not env_ok:
            print("   ❌ API密钥无法访问")
            print("   💡 建议：设置环境变量或修复配置加载器")
        else:
            print("   ❓ 状态不明确，需要进一步诊断")

    async def run_full_validation(self) -> Dict[str, Any]:
        """运行完整的验证流程"""

        print("🚀 开始API密钥完整验证")
        print("=" * 60)

        # 1. 验证密钥访问
        access_results = self.validate_api_key_access()

        # 2. 测试真实API调用
        api_results = await self.test_real_api_calls()

        # 3. 生成报告
        self.generate_validation_report(access_results, api_results)

        return {
            'access_validation': access_results,
            'api_test': api_results
        }

def main():
    """主函数"""
    validator = APIKeyValidator()

    # 运行异步验证
    results = asyncio.run(validator.run_full_validation())

    print("\n🎉 API密钥验证完成！")
    print("基于验证结果，可以确定是否需要启用轻量级模式降级。")

if __name__ == "__main__":
    main()
