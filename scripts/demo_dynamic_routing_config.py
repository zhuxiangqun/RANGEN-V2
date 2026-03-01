#!/usr/bin/env python3
"""
演示真正的动态路由配置系统

展示运行时动态配置、学习优化、API管理的能力
"""

import sys
import os
import time
import requests
import json
import threading
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.intelligent_router import (
    DynamicRoutingManager,
    DatabaseConfigSource,
    APIConfigSource,
    LearningConfigSource,
    PluginConfigSource,
    DynamicRouteTypeRegistry
)

def demo_runtime_route_type_registration():
    """演示运行时路由类型注册"""
    print("🔄 演示运行时路由类型注册")
    print("-" * 50)

    manager = DynamicRoutingManager()

    # 查看初始路由类型
    initial_types = manager.route_type_registry.get_all_route_types()
    print(f"初始路由类型数量: {len(initial_types)}")
    for rt in initial_types:
        print(f"  - {rt.name}: {rt.description}")

    # 运行时注册新的路由类型
    print("\n📝 注册新的路由类型...")
    manager.register_route_type(
        name="voice_assistant",
        description="语音助手专用查询",
        priority=6,
        voice_optimized=True
    )

    manager.register_route_type(
        name="code_review",
        description="代码审查查询",
        priority=7,
        code_focused=True
    )

    # 查看更新后的路由类型
    updated_types = manager.route_type_registry.get_all_route_types()
    print(f"注册后路由类型数量: {len(updated_types)}")
    for rt in updated_types:
        print(f"  - {rt.name}: {rt.description} (优先级: {rt.priority})")

    print("✅ 运行时路由类型注册演示完成\n")

def demo_dynamic_threshold_adjustment():
    """演示动态阈值调整"""
    print("🎚️ 演示动态阈值调整")
    print("-" * 50)

    manager = DynamicRoutingManager()

    # 查看初始阈值
    initial_thresholds = manager.config.thresholds
    print("初始阈值:")
    for key, value in list(initial_thresholds.items())[:5]:  # 显示前5个
        print(f"  {key}: {value}")

    # 运行时调整阈值
    print("\n⚙️ 动态调整阈值...")
    manager.update_routing_threshold('simple_max_complexity', 0.02)
    manager.update_routing_threshold('complex_min_complexity', 0.25)
    manager.update_routing_threshold('medium_max_words', 8)

    # 查看调整后的阈值
    updated_thresholds = manager.config.thresholds
    print("调整后阈值:")
    for key in ['simple_max_complexity', 'complex_min_complexity', 'medium_max_words']:
        print(f"  {key}: {updated_thresholds[key]}")

    print("✅ 动态阈值调整演示完成\n")

def demo_keyword_management():
    """演示关键词管理"""
    print("🔤 演示关键词管理")
    print("-" * 50)

    manager = DynamicRoutingManager()

    # 查看初始关键词
    initial_keywords = manager.config.keywords.get('question_words', [])
    print(f"初始问题词数量: {len(initial_keywords)}")
    print(f"前5个问题词: {initial_keywords[:5]}")

    # 运行时添加关键词
    print("\n➕ 添加新的关键词...")
    manager.add_routing_keyword('question_words', '啥时候')
    manager.add_routing_keyword('question_words', '如何做')
    manager.add_routing_keyword('complexity_indicators', '优化')
    manager.add_routing_keyword('complexity_indicators', '性能')

    # 查看更新后的关键词
    updated_keywords = manager.config.keywords.get('question_words', [])
    print(f"更新后问题词数量: {len(updated_keywords)}")
    print(f"新增的问题词: {updated_keywords[-2:]}")

    complexity_indicators = manager.config.keywords.get('complexity_indicators', [])
    print(f"复杂度指标词数量: {len(complexity_indicators)}")
    print(f"新增的复杂度指标: {complexity_indicators[-2:]}")

    print("✅ 关键词管理演示完成\n")

def demo_config_api():
    """演示配置API"""
    print("🌐 演示配置API")
    print("-" * 50)

    manager = DynamicRoutingManager()

    # 等待API服务器启动
    time.sleep(2)

    try:
        # 获取当前配置
        print("📡 获取当前路由配置...")
        response = requests.get("http://localhost:8080/config", timeout=5)
        if response.status_code == 200:
            config = response.json()
            print(f"路由类型数量: {len(config.get('route_types', []))}")
            print(f"阈值数量: {len(config.get('thresholds', {}))}")
            print("✅ 配置获取成功")
        # 获取路由类型列表
        print("\n📋 获取路由类型列表...")
        response = requests.get("http://localhost:8080/route-types", timeout=5)
        if response.status_code == 200:
            route_types = response.json()
            print(f"当前路由类型: {[rt['name'] for rt in route_types]}")

        # 注册新的路由类型
        print("\n📝 通过API注册新路由类型...")
        new_route_type = {
            "name": "api_test",
            "description": "API测试路由类型",
            "priority": 8,
            "metadata": {"test": True}
        }
        response = requests.post(
            "http://localhost:8080/route-types",
            json=new_route_type,
            timeout=5
        )
        if response.status_code == 200:
            print("✅ 新路由类型注册成功")

        # 更新阈值
        print("\n⚙️ 通过API更新阈值...")
        new_thresholds = {
            "api_test_threshold": 0.5,
            "another_threshold": 0.8
        }
        response = requests.post(
            "http://localhost:8080/thresholds",
            json=new_thresholds,
            timeout=5
        )
        if response.status_code == 200:
            print("✅ 阈值更新成功")

        # 添加关键词
        print("\n🔤 通过API添加关键词...")
        new_keyword = {
            "category": "test_keywords",
            "keyword": "测试词"
        }
        response = requests.post(
            "http://localhost:8080/keywords",
            json=new_keyword,
            timeout=5
        )
        if response.status_code == 200:
            print("✅ 关键词添加成功")

    except requests.exceptions.RequestException as e:
        print(f"❌ API调用失败: {e}")
        print("请确保API服务器正在运行")

    print("✅ 配置API演示完成\n")

def demo_learning_optimization():
    """演示学习优化"""
    print("🧠 演示学习优化")
    print("-" * 50)

    # 创建学习配置源
    learning_source = LearningConfigSource("test_performance.json")

    # 模拟一些性能数据
    print("📊 模拟性能数据...")
    sample_data = [
        {"expected_route": "simple", "correct": True, "confidence": 0.95},
        {"expected_route": "simple", "correct": False, "confidence": 0.85},
        {"expected_route": "complex", "correct": True, "confidence": 0.90},
        {"expected_route": "complex", "correct": False, "confidence": 0.70},
        {"expected_route": "multi_agent", "correct": True, "confidence": 0.95},
        {"expected_route": "multi_agent", "correct": True, "confidence": 0.98},
    ]

    for data in sample_data:
        learning_source.record_performance(data)

    # 获取学习优化的配置
    print("🎯 生成学习优化配置...")
    optimized_config = learning_source.load_config()

    if optimized_config:
        print("学习优化建议的阈值调整:")
        thresholds = optimized_config.get('thresholds', {})
        for key, value in thresholds.items():
            print(f"  {key}: {value}")

        metadata = optimized_config.get('learning_metadata', {})
        print(f"基于 {metadata.get('sample_count', 0)} 个样本优化")
    else:
        print("样本不足，无法生成优化配置")

    print("✅ 学习优化演示完成\n")

def demo_plugin_system():
    """演示插件系统"""
    print("🔌 演示插件系统")
    print("-" * 50)

    # 创建插件目录
    plugin_dir = "routing_plugins"
    os.makedirs(plugin_dir, exist_ok=True)

    # 创建示例插件
    plugin_content = '''
def get_routing_config():
    """返回插件的路由配置"""
    return {
        "thresholds": {
            "plugin_custom_threshold": 0.75,
            "plugin_complexity_boost": 1.2
        },
        "keywords": {
            "plugin_question_words": ["插件问题词1", "插件问题词2"],
            "plugin_complexity_indicators": ["插件指标1", "插件指标2"]
        },
        "routing_rules": [
            {
                "name": "plugin_rule_1",
                "condition": "complexity > 0.8",
                "action": "route_to_custom_type"
            }
        ]
    }
'''

    plugin_file = os.path.join(plugin_dir, "example_plugin.py")
    with open(plugin_file, 'w', encoding='utf-8') as f:
        f.write(plugin_content)

    # 加载插件配置
    print("🔌 加载插件配置...")
    plugin_source = PluginConfigSource(plugin_dir)
    plugin_config = plugin_source.load_config()

    if plugin_config:
        print("插件提供的配置:")
        thresholds = plugin_config.get('thresholds', {})
        for key, value in thresholds.items():
            print(f"  阈值 - {key}: {value}")

        keywords = plugin_config.get('keywords', {})
        for category, words in keywords.items():
            print(f"  关键词 - {category}: {words}")

        rules = plugin_config.get('routing_rules', [])
        print(f"  路由规则数量: {len(rules)}")

    # 清理插件文件
    if os.path.exists(plugin_file):
        os.remove(plugin_file)
    if os.path.exists(plugin_dir):
        os.rmdir(plugin_dir)

    print("✅ 插件系统演示完成\n")

def main():
    """主演示函数"""
    print("🚀 真正的动态路由配置系统演示")
    print("=" * 60)
    print("这个演示展示了真正的运行时动态配置能力，而非硬编码！")
    print("=" * 60)

    try:
        # 演示各个功能
        demo_runtime_route_type_registration()
        demo_dynamic_threshold_adjustment()
        demo_keyword_management()
        demo_learning_optimization()
        demo_plugin_system()
        demo_config_api()

        print("=" * 60)
        print("🎉 所有演示完成！")
        print("\n💡 关键特性总结:")
        print("  ✅ 运行时注册/注销路由类型")
        print("  ✅ 动态调整阈值")
        print("  ✅ 实时添加关键词")
        print("  ✅ 基于学习的自动优化")
        print("  ✅ 插件化扩展")
        print("  ✅ REST API管理")
        print("  ✅ 热更新无重启")
        print("\n🎯 这才是真正的动态配置，而非硬编码！")

    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
