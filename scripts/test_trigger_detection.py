#!/usr/bin/env python3
"""
技能触发器检测测试
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agents.skills.skill_trigger import get_skill_trigger

def main():
    trigger = get_skill_trigger()
    
    test_cases = [
        ("我想创建一个数据分析工作流", True),
        ("帮我开发一个机器学习预测模型", True),
        ("需要添加一个新的技能来处理图片", True),
        ("分析一下这段代码的性能", False),
        ("帮我查一下资料", False),
        ("create a new skill for data visualization", True),
        ("add skill to process documents", True),
        ("how to use existing skills", False)
    ]
    
    print("技能触发器检测测试:")
    print("=" * 60)
    
    correct = 0
    total = len(test_cases)
    
    for input_text, expected in test_cases:
        result = trigger.trigger(input_text)
        detected = "skill_factory_suggestion" in result.triggered_skills
        
        status = "✓" if detected == expected else "✗"
        correct += 1 if detected == expected else 0
        
        print(f"{status} '{input_text}'")
        print(f"  检测: {detected}, 期望: {expected}")
        print(f"  触发技能: {result.triggered_skills}")
        print(f"  推理: {result.reasoning}")
        print()
    
    accuracy = correct / total
    print(f"准确率: {correct}/{total} ({accuracy:.1%})")
    
    return correct == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)