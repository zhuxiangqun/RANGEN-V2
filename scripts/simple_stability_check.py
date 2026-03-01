#!/usr/bin/env python3
"""
简化的系统稳定性检查
只检查Agent替换率设置
"""

import sys
import time
from pathlib import Path

def check_replacement_rates():
    """检查替换率设置"""
    print("🔍 系统稳定性检查报告")
    print("=" * 60)
    print(f"检查时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"\n🔄 检查Agent替换率设置")
    print("-" * 40)

    wrapper_files = [
        'src/agents/answer_generation_agent_wrapper.py',
        'src/agents/learning_system_wrapper.py',
        'src/agents/strategic_chief_agent_wrapper.py',
        'src/agents/prompt_engineering_agent_wrapper.py',
        'src/agents/context_engineering_agent_wrapper.py',
        'src/agents/optimized_knowledge_retrieval_agent_wrapper.py'
    ]

    all_rates_correct = True

    for filepath in wrapper_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # 查找替换率设置
            import re

            # 首先尝试函数参数默认值模式（支持0.x和1.0）
            match = re.search(r'initial_replacement_rate:\s*float\s*=\s*(0\.\d+|1\.0)', content)
            if match:
                rate = float(match.group(1))
            else:
                # 尝试max函数模式
                match = re.search(r'max\(initial_replacement_rate,\s*(0\.\d+)\)', content)
                if match:
                    rate = float(match.group(1))
                else:
                    # 尝试直接赋值模式
                    match = re.search(r'replacement_rate = (0\.\d+)', content)
                    if match:
                        rate = float(match.group(1))
                    else:
                        print(f"  ❌ {Path(filepath).stem}: 未找到替换率设置")
                        all_rates_correct = False
                        continue

            agent_name = Path(filepath).stem.replace('_agent_wrapper', '').replace('_', ' ').title()
            status = "✅" if rate >= 0.1 else "⚠️"
            print(f"  {status} {agent_name}: {rate:.1%}")
            if rate < 0.1:
                all_rates_correct = False

        except Exception as e:
            print(f"  ❌ 检查 {Path(filepath).stem} 失败: {str(e)[:50]}")
            all_rates_correct = False

    print(f"\n📊 检查结果")
    print("-" * 30)
    if all_rates_correct:
        print("✅ 所有Agent替换率设置正确 (≥10%)")
        print("✅ 系统稳定性检查通过")
        print("\n💡 后续建议:")
        print("  • 继续监控系统运行状态")
        print("  • 定期检查Agent性能指标")
        print("  • 观察替换率调整效果")
        return True
    else:
        print("⚠️ 部分Agent替换率设置需要调整")
        print("❌ 系统稳定性检查发现问题")
        print("\n💡 建议:")
        print("  • 检查并调整替换率设置")
        print("  • 验证Agent初始化是否正常")
        print("  • 查看系统日志了解详细错误")
        return False

def main():
    """主函数"""
    success = check_replacement_rates()

    print(f"\n{'='*60}")
    print("🔍 检查完成")
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
