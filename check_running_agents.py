#!/usr/bin/env python3
"""
检查当前运行中的Agent实例
"""

import sys
import os
import importlib.util
import inspect
from typing import Dict, Any, List

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_global_instances():
    """检查可能的全局Agent实例"""
    print("🔍 检查全局Agent实例...")

    running_agents = []

    # 检查可能的全局变量
    modules_to_check = [
        'src.agents.react_agent',
        'src.agents.rag_agent',
        'src.agents.knowledge_retrieval_agent',
        'src.agents.react_agent_wrapper',
        'src.agents.multi_agent_coordinator'
    ]

    for module_name in modules_to_check:
        try:
            module = importlib.import_module(module_name)

            # 检查模块级别的全局变量
            for name, obj in inspect.getmembers(module):
                if name.startswith('_') and 'agent' in name.lower():
                    if hasattr(obj, '__class__') and 'Agent' in obj.__class__.__name__:
                        running_agents.append({
                            'name': name,
                            'module': module_name,
                            'class': obj.__class__.__name__,
                            'instance': obj
                        })

        except ImportError as e:
            print(f"⚠️ 无法导入模块 {module_name}: {e}")
        except Exception as e:
            print(f"❌ 检查模块 {module_name} 时出错: {e}")

    return running_agents

def check_process_instances():
    """检查进程中的Agent实例"""
    print("\n🔍 检查进程中的Agent实例...")

    import psutil
    import os

    current_pid = os.getpid()
    process = psutil.Process(current_pid)

    # 检查进程内存中的对象（这只是一个基本检查）
    print(f"当前进程PID: {current_pid}")
    print(f"进程内存使用: {process.memory_info().rss / 1024 / 1024:.1f} MB")

    # 这是一个简化的检查，实际上很难从外部检查Python进程中的具体对象实例
    return []

def check_agent_registry():
    """检查Agent注册表"""
    print("\n🔍 检查Agent注册表...")

    try:
        from src.agents.enhanced_task_executor_registry import EnhancedTaskExecutorRegistry
        registry = EnhancedTaskExecutorRegistry()
        executors = registry.list_executors()

        print(f"找到 {len(executors)} 个已注册的执行器:")
        for executor in executors:
            print(f"  - {executor.get('name', 'Unknown')}")

    except Exception as e:
        print(f"❌ 检查执行器注册表失败: {e}")

def main():
    print("🚀 检查运行中的Agent实例")
    print("=" * 50)

    # 1. 检查全局实例
    global_agents = check_global_instances()

    # 2. 检查进程实例
    process_agents = check_process_instances()

    # 3. 检查注册表
    check_agent_registry()

    # 汇总结果
    print("\n" + "=" * 50)
    print("📊 检查结果汇总:")

    total_agents = len(global_agents) + len(process_agents)

    if total_agents == 0:
        print("❌ 未发现运行中的Agent实例")
        print("\n💡 可能的原因:")
        print("  - Agent服务尚未启动")
        print("  - Agent实例使用惰性加载")
        print("  - Agent存储在不同的位置")
        print("  - 需要实际的API调用或用户请求来触发Agent实例化")
    else:
        print(f"✅ 发现 {total_agents} 个运行中的Agent实例")

        if global_agents:
            print("
全局Agent实例:"            for agent in global_agents:
                print(f"  - {agent['name']} ({agent['class']}) in {agent['module']}")

        if process_agents:
            print("
进程Agent实例:"            for agent in process_agents:
                print(f"  - {agent}")

    print("\n💡 建议:")
    print("  - 如果需要动态更新替换率，可能需要在应用启动时注册Agent实例")
    print("  - 考虑添加Agent生命周期管理器来跟踪运行中的实例")
    print("  - 可以通过实际的API调用来触发Agent实例化")

if __name__ == "__main__":
    main()
