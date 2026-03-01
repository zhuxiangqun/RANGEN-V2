#!/usr/bin/env python3
"""
统一配置中心集成脚本
为8个核心Agent集成统一配置中心支持
"""

import sys
import os
from pathlib import Path

# 设置项目环境
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from typing import List, Dict, Any


def integrate_config_center_for_agent(agent_file: str, agent_name: str):
    """为指定Agent文件集成统一配置中心"""

    # 读取Agent文件
    with open(agent_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已经集成了配置中心
    if 'get_unified_config_center' in content:
        print(f"✅ {agent_name}: 已集成统一配置中心")
        return False

    # 添加导入语句
    import_lines = [
        "from ..utils.unified_centers import get_unified_config_center",
        "from ..utils.unified_threshold_manager import get_unified_threshold_manager"
    ]

    # 在现有导入语句后添加
    lines = content.split('\n')
    import_inserted = False

    for i, line in enumerate(lines):
        if line.startswith('from ') or line.startswith('import '):
            continue
        elif line.strip() == '' and not import_inserted:
            # 在第一个空行后插入导入语句
            lines.insert(i, '')
            for j, import_line in enumerate(reversed(import_lines)):
                lines.insert(i, import_line)
            import_inserted = True
            break

    # 在__init__方法中添加配置中心初始化
    init_pattern = "def __init__(self"
    config_init_code = '''
        # 初始化统一配置中心
        self.config_center = get_unified_config_center()
        self.threshold_manager = get_unified_threshold_manager()

        # 获取Agent特定配置
        self.agent_config = self.config_center.get_agent_config(self.__class__.__name__, {
            'enabled': True,
            'max_retries': 3,
            'timeout': 30,
            'debug_mode': False
        })

        # 获取阈值配置
        self.thresholds = self.threshold_manager.get_thresholds(self.__class__.__name__, {
            'performance_warning_threshold': 5.0,
            'error_rate_threshold': 0.1,
            'memory_usage_threshold': 80.0
        })
'''

    for i, line in enumerate(lines):
        if init_pattern in line:
            # 找到__init__方法的开始
            # 查找方法体的开始（通常是下一行的缩进）
            for j in range(i + 1, len(lines)):
                if lines[j].strip().startswith('"""') or lines[j].strip() == '':
                    continue
                elif lines[j].startswith('        ') or lines[j].startswith('    '):
                    # 找到方法体，在super().__init__()调用后插入配置代码
                    super_init_found = False
                    for k in range(j, len(lines)):
                        if 'super().__init__(' in lines[k]:
                            super_init_found = True
                            # 在super().__init__()后插入配置代码
                            insert_pos = k + 1
                            # 找到下一个非空行的位置
                            while insert_pos < len(lines) and lines[insert_pos].strip() == '':
                                insert_pos += 1

                            # 插入配置代码
                            config_lines = config_init_code.strip().split('\n')
                            for l, config_line in enumerate(reversed(config_lines)):
                                lines.insert(insert_pos, config_line)
                            break
                        elif lines[k].strip() == '' or lines[k].startswith('    ') and not lines[k].startswith('        '):
                            # 如果没有找到super().__init__()，在方法体开始处插入
                            if not super_init_found:
                                lines.insert(j, config_init_code.strip())
                            break
                    break
            break

    # 写回文件
    new_content = '\n'.join(lines)
    with open(agent_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✅ {agent_name}: 已集成统一配置中心")
    return True


def main():
    """主函数"""
    print("🔧 开始统一配置中心集成...")

    # 8个核心Agent文件映射
    core_agents = {
        'AgentCoordinator': 'src/agents/agent_coordinator.py',
        'ReasoningExpert': 'src/agents/reasoning_expert.py',
        'RAGExpert': 'src/agents/rag_agent.py',
        'ToolOrchestrator': 'src/agents/tool_orchestrator.py',
        'MemoryManager': 'src/agents/memory_manager.py',
        'LearningOptimizer': 'src/agents/learning_optimizer.py',
        'QualityController': 'src/agents/quality_controller.py',
        'SecurityGuardian': 'src/agents/security_guardian.py'
    }

    integrated_count = 0
    total_count = len(core_agents)

    for agent_name, agent_file in core_agents.items():
        if os.path.exists(agent_file):
            if integrate_config_center_for_agent(agent_file, agent_name):
                integrated_count += 1
        else:
            print(f"⚠️ {agent_name}: 文件不存在 - {agent_file}")

    print(f"\n📊 集成完成统计:")
    print(f"  总Agent数量: {total_count}")
    print(f"  已集成数量: {integrated_count}")
    print(f"  跳过数量: {total_count - integrated_count}")

    if integrated_count > 0:
        print("\n✅ 统一配置中心集成完成！")
        print("请检查代码是否正确编译，然后运行测试验证配置中心功能。")
    else:
        print("\nℹ️ 所有Agent都已集成统一配置中心。")


if __name__ == "__main__":
    main()
