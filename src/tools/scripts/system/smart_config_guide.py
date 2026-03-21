#!/usr/bin/env python3
"""
智能配置使用指南
展示如何在现有代码中正确使用智能配置系统
"""

import sys
sys.path.append('src')

def show_config_examples():
    """展示智能配置的使用示例"""
    try:
        from src.utils.unified_smart_config import get_smart_config, ConfigContext
        
        print("📚 智能配置使用指南")
        print("=" * 60)
        
        # 示例1: 超时配置
        print("\\n1️⃣ 超时配置示例:")
        timeout_context = ConfigContext(
            query="api_timeout",
            quality_requirement=0.8,
            config_type="timeout"
        )
        timeout = get_smart_config("timeout", timeout_context)
        print(f"   ❌ 硬编码: timeout = 30")
        print(f"   ✅ 智能配置: timeout = get_smart_config('timeout', context) = {timeout}")
        
        # 示例2: 重试配置
        print("\\n2️⃣ 重试配置示例:")
        retry_context = ConfigContext(
            query="api_retry",
            quality_requirement=0.7,
            config_type="retry"
        )
        retry_count = get_smart_config("retry_count", retry_context)
        print(f"   ❌ 硬编码: max_retries = 3")
        print(f"   ✅ 智能配置: max_retries = get_smart_config('retry_count', context) = {retry_count}")
        
        # 示例3: 限制配置
        print("\\n3️⃣ 限制配置示例:")
        limit_context = ConfigContext(
            query="data_limit",
            quality_requirement=0.9,
            config_type="limit"
        )
        limit = get_smart_config("limit", limit_context)
        print(f"   ❌ 硬编码: limit = 100")
        print(f"   ✅ 智能配置: limit = get_smart_config('limit', context) = {limit}")
        
        print("\\n🎉 智能配置系统使用指南完成！")
        return True
        
    except Exception as e:
        print(f"❌ 配置指南错误: {e}")
        return False

def show_migration_examples():
    """展示如何迁移硬编码到智能配置"""
    print("\\n🔄 硬编码迁移示例")
    print("=" * 60)
    
    examples = [
        {
            "file": "example.py",
            "before": "timeout = 30",
            "after": "timeout = get_smart_config('timeout', context)"
        },
        {
            "file": "example.py", 
            "before": "max_retries = 3",
            "after": "max_retries = get_smart_config('retry_count', context)"
        },
        {
            "file": "example.py",
            "before": "limit = 100",
            "after": "limit = get_smart_config('limit', context)"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\\n{i}️⃣ 文件: {example['file']}")
        print(f"   ❌ 硬编码: {example['before']}")
        print(f"   ✅ 智能配置: {example['after']}")

def show_best_practices():
    """展示最佳实践"""
    print("\\n💡 最佳实践")
    print("=" * 60)
    
    practices = [
        "1. 总是使用ConfigContext来传递上下文信息",
        "2. 根据功能类型设置合适的config_type",
        "3. 根据质量要求设置quality_requirement",
        "4. 避免在代码中直接使用硬编码数值",
        "5. 使用有意义的配置键名",
        "6. 在函数开始时创建配置上下文",
        "7. 将配置获取集中在一个地方"
    ]
    
    for practice in practices:
        print(f"   {practice}")

def main():
    """主函数"""
    print("🚀 智能配置系统使用指南")
    print("=" * 80)
    
    # 显示配置示例
    config_ok = show_config_examples()
    
    # 显示迁移示例
    show_migration_examples()
    
    # 显示最佳实践
    show_best_practices()
    
    if config_ok:
        print("\\n🎯 总结: 智能配置系统已就绪，可以开始迁移硬编码！")
    else:
        print("\\n⚠️ 需要先修复智能配置系统")

if __name__ == "__main__":
    main()
