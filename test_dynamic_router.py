#!/usr/bin/env python3
"""
测试 DynamicRoutingManager
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_dynamic_router():
    """测试动态路由管理器"""
    print("测试 DynamicRoutingManager...")

    try:
        from src.core.intelligent_router import DynamicRoutingManager

        # 创建路由管理器（禁用高级功能以避免依赖问题）
        router = DynamicRoutingManager(enable_advanced_features=False)
        print("✅ DynamicRoutingManager 创建成功")

        # 测试配置更新
        router.update_routing_threshold('simple_max_complexity', 0.08)
        print("✅ 配置更新成功")

        # 测试关键词添加
        router.add_routing_keyword('question_words', 'what')
        print("✅ 关键词添加成功")

        # 测试配置获取
        config = router.get_routing_config()
        print(f"✅ 配置获取成功: {len(config.get('thresholds', {}))} 个阈值")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_dynamic_router()
    if success:
        print("\n🎉 所有测试通过！")
    else:
        print("\n💥 测试失败！")
        sys.exit(1)
