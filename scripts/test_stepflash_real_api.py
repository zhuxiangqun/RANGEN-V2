#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step-3.5-Flash 真实API密钥测试脚本

该脚本使用真实API密钥测试Step-3.5-Flash集成，验证：
1. 环境变量配置是否正确
2. StepFlashAdapter能否成功连接API
3. 三种部署模式（OpenRouter/NVIDIA NIM/vLLM）的可用性
4. 模型响应质量

使用方法:
  1. 设置环境变量: export STEPSFLASH_API_KEY="your_api_key"
  2. 运行测试: python scripts/test_stepflash_real_api.py

注意:
  - OpenRouter: 免费层可用，需要注册获取API密钥
  - NVIDIA NIM: 需要NVIDIA API密钥和访问权限
  - vLLM: 需要本地部署，设置本地API端点

参考: https://openrouter.ai/keys
"""

import os
import sys
import time
import json
from pathlib import Path

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(src_path))

from src.services.stepflash_adapter import StepFlashAdapter, StepFlashDeploymentType
from src.observability.metrics import record_llm_call, record_llm_tokens

# 测试配置
TEST_CONFIGS = [
    {
        "name": "OpenRouter (推荐)",
        "deployment_type": StepFlashDeploymentType.OPENROUTER,
        "model": "stepfun-ai/step-3-5-flash",
        "env_var_required": "STEPSFLASH_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "description": "通过OpenRouter API访问Step-3.5-Flash，免费层可用"
    },
    {
        "name": "NVIDIA NIM",
        "deployment_type": StepFlashDeploymentType.NVIDIA_NIM,
        "model": "stepfun-ai/step-3-5-flash",
        "env_var_required": "STEPSFLASH_API_KEY",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "description": "通过NVIDIA NIM API访问，需要NVIDIA API密钥"
    },
    {
        "name": "vLLM 本地部署",
        "deployment_type": StepFlashDeploymentType.VLLM,
        "model": "stepfun-ai/step-3-5-flash",
        "env_var_required": "STEPSFLASH_API_KEY",
        "base_url": "http://localhost:8000/v1",  # 本地vLLM服务默认端口
        "description": "通过本地vLLM服务访问，需要本地部署Step-3.5-Flash"
    }
]

# 测试消息
TEST_MESSAGES = [
    {"role": "system", "content": "你是一个乐于助人的AI助手。"},
    {"role": "user", "content": "请用中文介绍一下Step-3.5-Flash模型的特点。"}
]

def check_environment():
    """检查环境变量配置"""
    print("=" * 60)
    print("Step-3.5-Flash 环境变量检查")
    print("=" * 60)
    
    api_key = os.getenv("STEPSFLASH_API_KEY")
    if not api_key:
        print("❌ 错误: STEPSFLASH_API_KEY 环境变量未设置")
        print("\n请按照以下步骤设置:")
        print("1. 访问 https://openrouter.ai/keys 注册并获取API密钥")
        print("2. 设置环境变量:")
        print("   export STEPSFLASH_API_KEY='your_api_key_here'")
        print("3. 或者创建 .env 文件并添加:")
        print("   STEPSFLASH_API_KEY=your_api_key_here")
        return False
    
    print(f"✅ STEPSFLASH_API_KEY 已设置 (长度: {len(api_key)} 字符)")
    print(f"   密钥前缀: {api_key[:10]}...")
    return True

def test_deployment(config):
    """测试特定部署配置"""
    print(f"\n{'=' * 60}")
    print(f"测试: {config['name']}")
    print(f"描述: {config['description']}")
    print(f"{'=' * 60}")
    
    # 检查环境变量
    api_key = os.getenv(config['env_var_required'])
    if not api_key:
        print(f"❌ 跳过: {config['env_var_required']} 环境变量未设置")
        return {"success": False, "reason": f"环境变量 {config['env_var_required']} 未设置"}
    
    try:
        # 创建适配器实例
        adapter = StepFlashAdapter(
            deployment_type=config['deployment_type'],
            model=config['model'],
            api_key=api_key,
            base_url=config.get('base_url'),
            max_retries=1,  # 测试时只重试一次
            retry_delay=1
        )
        
        print(f"✅ 适配器创建成功")
        print(f"   部署类型: {adapter.deployment_type.value}")
        print(f"   模型: {adapter.model}")
        print(f"   API基础URL: {adapter.base_url}")
        
        # 发送测试请求
        print(f"📨 发送测试请求...")
        start_time = time.time()
        
        response = adapter.chat_completion(
            messages=TEST_MESSAGES,
            temperature=0.7,
            max_tokens=500
        )
        
        duration = time.time() - start_time
        
        if response.get("success"):
            print(f"✅ 测试成功!")
            print(f"   响应时间: {duration:.2f} 秒")
            print(f"   模型: {response.get('model', '未知')}")
            print(f"   完成原因: {response.get('finish_reason', '未知')}")
            
            # 显示响应内容（截断）
            content = response.get("response", "")
            preview = content[:200] + "..." if len(content) > 200 else content
            print(f"   响应预览: {preview}")
            
            # 显示token使用情况
            usage = response.get("usage", {})
            if usage:
                print(f"   Token使用:")
                print(f"     输入Token: {usage.get('prompt_tokens', 'N/A')}")
                print(f"     输出Token: {usage.get('completion_tokens', 'N/A')}")
                print(f"     总Token: {usage.get('total_tokens', 'N/A')}")
            
            # 记录指标（可选）
            try:
                record_llm_call(
                    provider="stepflash",
                    model=adapter.model,
                    endpoint=adapter.deployment_type.value,
                    duration=duration,
                    success=True
                )
                
                if usage:
                    if "prompt_tokens" in usage:
                        record_llm_tokens(
                            provider="stepflash",
                            model=adapter.model,
                            token_type="input",
                            token_count=usage["prompt_tokens"]
                        )
                    if "completion_tokens" in usage:
                        record_llm_tokens(
                            provider="stepflash",
                            model=adapter.model,
                            token_type="output",
                            token_count=usage["completion_tokens"]
                        )
            except Exception as e:
                print(f"⚠️  指标记录失败: {e}")
            
            return {
                "success": True,
                "deployment": config['name'],
                "duration": duration,
                "response": response,
                "adapter": adapter
            }
        else:
            print(f"❌ 测试失败!")
            print(f"   错误: {response.get('error', '未知错误')}")
            print(f"   详情: {response.get('details', '无详情')}")
            print(f"   重试次数: {response.get('retry_attempts', 0)}")
            
            # 记录失败指标
            try:
                record_llm_call(
                    provider="stepflash",
                    model=adapter.model,
                    endpoint=adapter.deployment_type.value,
                    duration=duration,
                    success=False,
                    error_type=response.get('error', 'unknown')
                )
            except Exception as e:
                print(f"⚠️  指标记录失败: {e}")
            
            return {
                "success": False,
                "deployment": config['name'],
                "error": response.get('error'),
                "details": response.get('details')
            }
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "deployment": config['name'],
            "error": str(e),
            "exception": True
        }

def generate_report(results):
    """生成测试报告"""
    print(f"\n{'=' * 60}")
    print("测试报告摘要")
    print(f"{'=' * 60}")
    
    total = len(results)
    successful = sum(1 for r in results if r.get("success"))
    failed = total - successful
    
    print(f"总测试配置: {total}")
    print(f"成功: {successful}")
    print(f"失败: {failed}")
    
    if successful > 0:
        print(f"\n✅ 成功的部署:")
        for result in results:
            if result.get("success"):
                print(f"  - {result['deployment']}: {result.get('duration', 0):.2f}秒")
    
    if failed > 0:
        print(f"\n❌ 失败的部署:")
        for result in results:
            if not result.get("success"):
                error = result.get('error', '未知错误')
                print(f"  - {result['deployment']}: {error}")
    
    # 提供建议
    print(f"\n📋 建议:")
    
    # 检查是否有成功的OpenRouter测试
    openrouter_success = any(
        r.get("success") and "OpenRouter" in r.get("deployment", "") 
        for r in results
    )
    
    if openrouter_success:
        print("  ✅ OpenRouter部署成功，建议在生产环境中使用此模式")
    elif os.getenv("STEPSFLASH_API_KEY"):
        print("  ⚠️  OpenRouter测试失败，请检查:")
        print("     1. API密钥是否正确")
        print("     2. 网络连接是否正常")
        print("     3. 账户是否有足够额度")
    else:
        print("  🔧 请先设置STEPSFLASH_API_KEY环境变量")
    
    # 保存详细报告
    report_file = project_root / "logs" / "stepflash_test_report.json"
    report_file.parent.mkdir(exist_ok=True)
    
    report_data = {
        "timestamp": time.time(),
        "total_tests": total,
        "successful_tests": successful,
        "failed_tests": failed,
        "results": [
            {
                "deployment": r.get("deployment"),
                "success": r.get("success"),
                "duration": r.get("duration"),
                "error": r.get("error"),
                "response_preview": r.get("response", {}).get("response", "")[:100] if r.get("response") else None
            }
            for r in results
        ]
    }
    
    try:
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        print(f"\n📄 详细报告已保存到: {report_file}")
    except Exception as e:
        print(f"⚠️  报告保存失败: {e}")

def main():
    """主测试函数"""
    print("Step-3.5-Flash 真实API密钥测试")
    print("版本: 1.0")
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查环境变量
    if not check_environment():
        print("\n请先设置环境变量，然后重新运行测试。")
        return 1
    
    # 测试所有部署配置
    results = []
    for config in TEST_CONFIGS:
        result = test_deployment(config)
        results.append(result)
        # 短暂的延迟，避免API限流
        time.sleep(1)
    
    # 生成报告
    generate_report(results)
    
    # 返回退出码
    successful = sum(1 for r in results if r.get("success"))
    if successful == 0:
        print("\n❌ 所有测试都失败了，请检查配置。")
        return 1
    elif successful == len(TEST_CONFIGS):
        print("\n✅ 所有测试都成功了!")
        return 0
    else:
        print(f"\n⚠️  部分测试成功 ({successful}/{len(TEST_CONFIGS)})")
        return 0

if __name__ == "__main__":
    sys.exit(main())