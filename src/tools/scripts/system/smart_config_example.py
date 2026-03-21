#!/usr/bin/env python3
"""
智能配置使用示例
展示如何正确使用智能配置系统
"""

import sys
sys.path.append('src')

def demonstrate_smart_config():
    """演示智能配置的使用"""
    try:
        from src.utils.unified_smart_config import get_smart_config, ConfigContext
        
        print("🔧 智能配置系统演示")
        print("=" * 50)
        
        # 创建配置上下文
        context = ConfigContext(
            query="demo_timeout",
            quality_requirement=0.9,
            config_type="timeout"
        )
        
        # 获取配置
        timeout = get_smart_config("timeout", context)
        print(f"✅ 超时配置: {timeout}")
        
        # 获取其他配置
        context2 = ConfigContext(
            query="demo_retry",
            quality_requirement=0.7,
            config_type="retry"
        )
        
        retry_count = get_smart_config("retry_count", context2)
        print(f"✅ 重试次数: {retry_count}")
        
        print("\\n🎉 智能配置系统工作正常！")
        return True
        
    except Exception as e:
        print(f"❌ 智能配置系统错误: {e}")
        return False

def demonstrate_optimizer():
    """演示代码优化器的使用"""
    try:
        from src.utils.integrated_code_optimizer import get_integrated_optimizer
        
        print("\\n🔧 代码优化器演示")
        print("=" * 50)
        
        optimizer = get_integrated_optimizer()
        print("✅ 代码优化器已就绪")
        
        # 这里可以添加更多演示代码
        print("🎉 代码优化器工作正常！")
        return True
        
    except Exception as e:
        print(f"❌ 代码优化器错误: {e}")
        return False

def main():
    """主函数"""
    print("🚀 智能系统功能演示")
    print("=" * 60)
    
    # 演示智能配置
    config_ok = demonstrate_smart_config()
    
    # 演示代码优化器
    optimizer_ok = demonstrate_optimizer()
    
    # 总结
    print("\\n📊 系统状态总结")
    print("=" * 60)
    print(f"智能配置系统: {'✅ 正常' if config_ok else '❌ 异常'}")
    print(f"代码优化器: {'✅ 正常' if optimizer_ok else '❌ 异常'}")
    
    if config_ok and optimizer_ok:
        print("\\n🎉 核心系统完全正常，可以开始使用！")
    else:
        print("\\n⚠️ 部分系统异常，需要进一步修复")

if __name__ == "__main__":
    main()
