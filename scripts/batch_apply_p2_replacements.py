#!/usr/bin/env python3
"""
批量应用P2优先级Agent代码替换

批量应用剩余P2优先级Agent的代码替换。
"""

import sys
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Agent配置：Agent名称 -> (导入模式列表, 实例化模式, 目标文件列表)
AGENT_REPLACEMENT_CONFIGS = {
    "LearningSystem": {
        "import_patterns": [
            (r'from\s+src\.agents\.learning_system\s+import\s+LearningSystem\b', 
             'from src.agents.learning_system_wrapper import LearningSystemWrapper as LearningSystem'),
            (r'from\s+\.learning_system\s+import\s+LearningSystem\b',
             'from .learning_system_wrapper import LearningSystemWrapper as LearningSystem'),
        ],
        "instantiation_pattern": r'(?<!class\s)\bLearningSystem\s*\(([^)]*)\)',
        "wrapper_class": "LearningSystemWrapper",
        "target_files": [
            "src/unified_research_system.py",
            "src/core/langgraph_learning_nodes.py",
        ]
    },
    "StrategicChiefAgent": {
        "import_patterns": [
            (r'from\s+src\.agents\.strategic_chief_agent\s+import\s+StrategicChiefAgent\b',
             'from src.agents.strategic_chief_agent_wrapper import StrategicChiefAgentWrapper as StrategicChiefAgent'),
            (r'from\s+\.\.agents\.strategic_chief_agent\s+import\s+StrategicChiefAgent\b',
             'from ..agents.strategic_chief_agent_wrapper import StrategicChiefAgentWrapper as StrategicChiefAgent'),
        ],
        "instantiation_pattern": r'\bStrategicChiefAgent\s*\(([^)]*)\)',
        "wrapper_class": "StrategicChiefAgentWrapper",
        "target_files": [
            "src/core/layered_architecture_adapter.py",
            "src/core/langgraph_layered_workflow_fixed.py",
            "src/core/simplified_layered_workflow.py",
            "src/core/langgraph_layered_workflow.py",
        ]
    },
    "EnhancedAnalysisAgent": {
        "import_patterns": [
            (r'from\s+\.agents\.enhanced_analysis_agent\s+import\s+EnhancedAnalysisAgent\b',
             'from .agents.enhanced_analysis_agent_wrapper import EnhancedAnalysisAgentWrapper as EnhancedAnalysisAgent'),
        ],
        "instantiation_pattern": r'\bEnhancedAnalysisAgent\s*\(([^)]*)\)',
        "wrapper_class": "EnhancedAnalysisAgentWrapper",
        "target_files": [
            "src/async_research_integrator.py",
        ]
    },
    "IntelligentStrategyAgent": {
        "import_patterns": [
            (r'from\s+\.agents\.intelligent_strategy_agent\s+import\s+IntelligentStrategyAgent\b',
             'from .agents.intelligent_strategy_agent_wrapper import IntelligentStrategyAgentWrapper as IntelligentStrategyAgent'),
            (r'from\s+src\.agents\.intelligent_strategy_agent\s+import\s+IntelligentStrategyAgent\b',
             'from src.agents.intelligent_strategy_agent_wrapper import IntelligentStrategyAgentWrapper as IntelligentStrategyAgent'),
        ],
        "instantiation_pattern": r'\bIntelligentStrategyAgent\s*\(([^)]*)\)',
        "wrapper_class": "IntelligentStrategyAgentWrapper",
        "target_files": [
            "src/async_research_integrator.py",
            "src/agents/agent_builder.py",
        ]
    },
    "OptimizedKnowledgeRetrievalAgent": {
        "import_patterns": [
            (r'from\s+src\.agents\.optimized_knowledge_retrieval_agent\s+import\s+OptimizedKnowledgeRetrievalAgent\b',
             'from src.agents.optimized_knowledge_retrieval_agent_wrapper import OptimizedKnowledgeRetrievalAgentWrapper as OptimizedKnowledgeRetrievalAgent'),
        ],
        "instantiation_pattern": r'\bOptimizedKnowledgeRetrievalAgent\s*\(([^)]*)\)',
        "wrapper_class": "OptimizedKnowledgeRetrievalAgentWrapper",
        "target_files": [
            "src/core/reasoning/engine.py",
        ]
    },
}


def apply_replacement_for_agent(agent_name: str, config: Dict, dry_run: bool = True) -> int:
    """为指定Agent应用替换"""
    modified_count = 0
    
    print(f"\n{'='*80}")
    print(f"处理 {agent_name}")
    print(f"{'='*80}")
    
    for file_path_str in config["target_files"]:
        file_path = Path(file_path_str)
        if not file_path.exists():
            print(f"⚠️ 文件不存在: {file_path}")
            continue
        
        print(f"\n📄 处理文件: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            modified = False
            
            # 替换导入语句
            for pattern, replacement in config["import_patterns"]:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    modified = True
                    print(f"  ✅ 替换导入语句")
            
            # 替换实例化语句
            wrapper_class = config["wrapper_class"]
            pattern = config["instantiation_pattern"]
            
            def replace_instantiation(match):
                params = match.group(1).strip()
                if params:
                    if 'enable_gradual_replacement' not in params:
                        return f'{wrapper_class}({params}, enable_gradual_replacement=True)'
                    else:
                        return match.group(0)
                else:
                    return f'{wrapper_class}(enable_gradual_replacement=True)'
            
            if re.search(pattern, content):
                new_content = re.sub(pattern, replace_instantiation, content)
                if new_content != content:
                    content = new_content
                    modified = True
                    print(f"  ✅ 替换实例化语句")
            
            if modified:
                if not dry_run:
                    # 备份原文件
                    backup_path = file_path.with_suffix(file_path.suffix + '.backup')
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(original_content)
                    print(f"  📝 备份文件: {backup_path}")
                    
                    # 写入新内容
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"  ✅ 文件已更新: {file_path}")
                    modified_count += 1
                else:
                    print(f"  🔍 [DRY RUN] 将更新文件: {file_path}")
                    modified_count += 1
        
        except Exception as e:
            print(f"  ❌ 处理文件失败 {file_path}: {e}")
    
    return modified_count


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="批量应用P2优先级Agent代码替换")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="干运行模式：只显示将要进行的更改，不实际修改文件"
    )
    parser.add_argument(
        "--agent",
        help="指定要处理的Agent名称（可选，默认处理所有）"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("批量应用P2优先级Agent代码替换")
    print("=" * 80)
    print(f"模式: {'🔍 DRY RUN (预览模式)' if args.dry_run else '✏️ 实际修改'}")
    print("=" * 80)
    
    agents_to_process = [args.agent] if args.agent else list(AGENT_REPLACEMENT_CONFIGS.keys())
    
    total_modified = 0
    
    for agent_name in agents_to_process:
        if agent_name not in AGENT_REPLACEMENT_CONFIGS:
            print(f"⚠️ 未知的Agent: {agent_name}")
            continue
        
        config = AGENT_REPLACEMENT_CONFIGS[agent_name]
        modified = apply_replacement_for_agent(agent_name, config, dry_run=args.dry_run)
        total_modified += modified
    
    print("\n" + "=" * 80)
    print("批量替换完成")
    print("=" * 80)
    print(f"处理Agent数: {len(agents_to_process)}")
    print(f"修改文件数: {total_modified}")
    
    if args.dry_run:
        print("\n💡 提示: 使用 --dry-run=false 来实际应用更改")
    else:
        print("\n✅ 替换已应用")


if __name__ == "__main__":
    main()

