#!/usr/bin/env python3
"""
简化的DeepSeek专用系统验证脚本
只验证配置和Agent初始化，不涉及网络调用
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_deepseek_configuration():
    """测试DeepSeek配置"""
    print("🚀 DeepSeek专用系统验证")
    print("=" * 50)
    
    # 检查环境变量
    print("📋 环境变量检查:")
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    llm_provider = os.getenv('LLM_PROVIDER', 'deepseek')
    
    print(f"• LLM提供商: {llm_provider}")
    print(f"• DeepSeek密钥: {'✅ 已配置' if deepseek_key else '❌ 未配置'}")
    print(f"• OpenAI密钥: {'✅ 未配置（符合要求）' if not openai_key else 'ℹ️ 已配置（可选）'}")
    
    return {
        'deepseek_configured': bool(deepseek_key),
        'openai_not_configured': not bool(openai_key),
        'llm_provider_correct': llm_provider == 'deepseek'
    }

def test_agent_initialization():
    """测试Agent初始化"""
    print("\n🏗️ Agent初始化测试:")
    
    results = {}
    
    try:
        from src.agents.rag_agent import RAGExpert
        rag_agent = RAGExpert()
        results['RAGExpert'] = True
        print("• ✅ RAGExpert初始化成功")
    except Exception as e:
        results['RAGExpert'] = False
        print(f"• ❌ RAGExpert初始化失败: {str(e)[:50]}")
    
    try:
        from src.agents.reasoning_expert import ReasoningExpert
        reasoning_agent = ReasoningExpert()
        results['ReasoningExpert'] = True
        print("• ✅ ReasoningExpert初始化成功")
    except Exception as e:
        results['ReasoningExpert'] = False
        print(f"• ❌ ReasoningExpert初始化失败: {str(e)[:50]}")
    
    try:
        from src.agents.agent_coordinator import AgentCoordinator
        coordinator = AgentCoordinator()
        results['AgentCoordinator'] = True
        print("• ✅ AgentCoordinator初始化成功")
    except Exception as e:
        results['AgentCoordinator'] = False
        print(f"• ❌ AgentCoordinator初始化失败: {str(e)[:50]}")
    
    return results

def test_unified_centers():
    """测试统一中心系统"""
    print("\n🎛️ 统一中心系统测试:")
    
    results = {}
    
    try:
        from src.utils.unified_centers import get_unified_config_center
        config_center = get_unified_config_center()
        results['config_center'] = True
        print("• ✅ 配置中心初始化成功")
    except Exception as e:
        results['config_center'] = False
        print(f"• ❌ 配置中心初始化失败: {str(e)[:50]}")
    
    try:
        from src.utils.unified_threshold_manager import get_unified_threshold_manager
        threshold_manager = get_unified_threshold_manager()
        results['threshold_manager'] = True
        print("• ✅ 阈值管理器初始化成功")
    except Exception as e:
        results['threshold_manager'] = False
        print(f"• ❌ 阈值管理器初始化失败: {str(e)[:50]}")
    
    return results

def generate_report(config_results, agent_results, center_results):
    """生成验证报告"""
    print("\n📊 验证报告")
    print("=" * 30)
    
    # 配置检查
    config_score = sum(config_results.values())
    print(f"🔑 配置检查: {config_score}/3")
    
    # Agent初始化
    agent_score = sum(agent_results.values())
    print(f"🏗️ Agent初始化: {agent_score}/3")
    
    # 统一中心
    center_score = sum(center_results.values())
    print(f"🎛️ 统一中心: {center_score}/2")
    
    # 总体评分
    total_score = config_score + agent_score + center_score
    total_possible = 8
    success_rate = total_score / total_possible * 100
    
    print(f"🎯 总体成功率: {success_rate:.1f}%")
    
    # 结果判断
    if success_rate >= 87.5:  # 7/8
        print("🎉 DeepSeek专用系统验证通过！")
        print("   💡 系统已正确配置为仅使用DeepSeek")
        return True
    elif success_rate >= 62.5:  # 5/8
        print("⚠️ 系统基本正常，但有小问题需要关注")
        return True
    else:
        print("❌ 系统存在问题，需要修复")
        return False

def main():
    """主函数"""
    # 测试配置
    config_results = test_deepseek_configuration()
    
    # 测试Agent初始化
    agent_results = test_agent_initialization()
    
    # 测试统一中心
    center_results = test_unified_centers()
    
    # 生成报告
    success = generate_report(config_results, agent_results, center_results)
    
    print(f"\n{'='*50}")
    if success:
        print("✅ DeepSeek专用系统验证完成")
        sys.exit(0)
    else:
        print("❌ 系统验证失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
