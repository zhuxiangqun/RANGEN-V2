#!/usr/bin/env python3
"""
测试新创建的Hands导入
"""

import sys
from pathlib import Path

# 添加src目录到路径
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

try:
    print("测试SlackHand导入...")
    from hands.slack_hand import SlackHand
    print("✓ SlackHand导入成功")
    
    # 创建实例测试
    slack_hand = SlackHand()
    print(f"✓ SlackHand实例创建成功: {slack_hand.name}")
    print(f"  描述: {slack_hand.description}")
    print(f"  类别: {slack_hand.category}")
    print(f"  安全级别: {slack_hand.safety_level}")
    
except Exception as e:
    print(f"✗ SlackHand导入失败: {e}")

try:
    print("\n测试GitHubHand导入...")
    from hands.github_hand import GitHubHand
    print("✓ GitHubHand导入成功")
    
    # 创建实例测试
    github_hand = GitHubHand()
    print(f"✓ GitHubHand实例创建成功: {github_hand.name}")
    print(f"  描述: {github_hand.description}")
    print(f"  类别: {github_hand.category}")
    print(f"  安全级别: {github_hand.safety_level}")
    
except Exception as e:
    print(f"✗ GitHubHand导入失败: {e}")

try:
    print("\n测试NotionHand导入...")
    from hands.notion_hand import NotionHand
    print("✓ NotionHand导入成功")
    
    # 创建实例测试
    notion_hand = NotionHand()
    print(f"✓ NotionHand实例创建成功: {notion_hand.name}")
    print(f"  描述: {notion_hand.description}")
    print(f"  类别: {notion_hand.category}")
    print(f"  安全级别: {notion_hand.safety_level}")
    
except Exception as e:
    print(f"✗ NotionHand导入失败: {e}")

try:
    print("\n测试HandRegistry自动发现...")
    from hands.registry import HandRegistry
    
    registry = HandRegistry(auto_discover=True)
    print(f"✓ HandRegistry创建成功")
    print(f"  已注册Hands数量: {len(registry.hands)}")
    
    # 列出所有已注册的Hands
    if registry.hands:
        print("  已注册的Hands:")
        for hand_name, hand_instance in registry.hands.items():
            print(f"    - {hand_name}: {hand_instance.description}")
    else:
        print("  警告: 没有发现任何Hands")
        
except Exception as e:
    print(f"✗ HandRegistry测试失败: {e}")

print("\n测试完成！")