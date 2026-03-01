#!/usr/bin/env python3
"""
应用MemoryAgent逐步替换

将代码中的MemoryAgent替换为使用逐步替换策略的包装器。
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def find_memory_agent_imports(file_path: Path) -> List[Tuple[int, str]]:
    """查找MemoryAgent的导入语句"""
    imports = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                if 'from' in line and 'MemoryAgent' in line and 'import' in line:
                    imports.append((i, line.strip()))
    except Exception as e:
        print(f"⚠️ 读取文件失败 {file_path}: {e}")
    return imports


def find_memory_agent_instantiations(file_path: Path) -> List[Tuple[int, str]]:
    """查找MemoryAgent的实例化语句"""
    instantiations = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                if 'MemoryAgent(' in line and 'class' not in line:
                    instantiations.append((i, line.strip()))
    except Exception as e:
        print(f"⚠️ 读取文件失败 {file_path}: {e}")
    return instantiations


def apply_replacement(file_path: Path, dry_run: bool = True) -> bool:
    """应用替换"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        modified = False
        
        # 替换导入语句
        pattern1a = r'from\s+src\.agents\.expert_agents\s+import\s+.*\bMemoryAgent\b'
        pattern1b = r'from\s+\.expert_agents\s+import\s+.*\bMemoryAgent\b'
        
        # 处理包含多个导入的情况
        def replace_import(match):
            line = match.group(0)
            if 'MemoryAgentWrapper' in line:
                return line  # 已经替换过了
            # 如果MemoryAgent是单独导入的
            if re.search(r'\bMemoryAgent\b(?!\s*,\s*\w)', line):
                if 'from src.agents.expert_agents' in line:
                    return line.replace('from src.agents.expert_agents import', 'from src.agents.expert_agents import') + '\nfrom src.agents.memory_agent_wrapper import MemoryAgentWrapper as MemoryAgent'
                elif 'from .expert_agents' in line:
                    return line.replace('from .expert_agents import', 'from .expert_agents import') + '\nfrom .memory_agent_wrapper import MemoryAgentWrapper as MemoryAgent'
            # 如果MemoryAgent是多个导入中的一个
            else:
                # 移除MemoryAgent，添加单独的导入
                line = re.sub(r',\s*\bMemoryAgent\b', '', line)
                line = re.sub(r'\bMemoryAgent\b\s*,', '', line)
                if 'from src.agents.expert_agents' in line:
                    return line + '\nfrom src.agents.memory_agent_wrapper import MemoryAgentWrapper as MemoryAgent'
                elif 'from .expert_agents' in line:
                    return line + '\nfrom .memory_agent_wrapper import MemoryAgentWrapper as MemoryAgent'
            return line
        
        # 替换导入语句（简化版本：直接添加新导入）
        if re.search(pattern1a, content) or re.search(pattern1b, content):
            # 检查是否已经有wrapper导入
            if 'memory_agent_wrapper' not in content:
                # 在导入语句后添加wrapper导入
                content = re.sub(
                    r'(from\s+(?:src\.agents\.expert_agents|\.expert_agents)\s+import[^\n]+\n)',
                    r'\1from src.agents.memory_agent_wrapper import MemoryAgentWrapper as MemoryAgent\n',
                    content,
                    count=1
                )
                modified = True
                print(f"  ✅ 添加MemoryAgent包装器导入")
        
        # 替换实例化语句
        pattern2 = r'(?<!class\s)\bMemoryAgent\s*\(([^)]*)\)'
        def replace_instantiation(match):
            params = match.group(1).strip()
            if params:
                if 'enable_gradual_replacement' not in params:
                    return f'MemoryAgentWrapper({params}, enable_gradual_replacement=True)'
                else:
                    return match.group(0)
            else:
                return 'MemoryAgentWrapper(enable_gradual_replacement=True)'
        
        if re.search(pattern2, content):
            new_content = re.sub(pattern2, replace_instantiation, content)
            if new_content != content:
                content = new_content
                modified = True
                print(f"  ✅ 替换实例化语句")
        
        if modified:
            if not dry_run:
                backup_path = file_path.with_suffix(file_path.suffix + '.backup')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                print(f"  📝 备份文件: {backup_path}")
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  ✅ 文件已更新: {file_path}")
            else:
                print(f"  🔍 [DRY RUN] 将更新文件: {file_path}")
        
        return modified
        
    except Exception as e:
        print(f"  ❌ 处理文件失败 {file_path}: {e}")
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="应用MemoryAgent逐步替换")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="干运行模式：只显示将要进行的更改，不实际修改文件"
    )
    parser.add_argument(
        "--file",
        help="指定要处理的文件（可选，默认处理所有相关文件）"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("MemoryAgent逐步替换应用")
    print("=" * 80)
    print(f"模式: {'🔍 DRY RUN (预览模式)' if args.dry_run else '✏️ 实际修改'}")
    print("=" * 80)
    
    target_files = []
    
    if args.file:
        target_files.append(Path(args.file))
    else:
        target_files = [
            Path("src/core/langgraph_agent_nodes.py"),
            Path("src/agents/chief_agent.py"),
        ]
    
    total_modified = 0
    
    for file_path in target_files:
        if not file_path.exists():
            print(f"\n⚠️ 文件不存在: {file_path}")
            continue
        
        print(f"\n📄 处理文件: {file_path}")
        
        imports = find_memory_agent_imports(file_path)
        instantiations = find_memory_agent_instantiations(file_path)
        
        if imports:
            print(f"  找到 {len(imports)} 个导入语句:")
            for line_num, line in imports:
                print(f"    行 {line_num}: {line}")
        
        if instantiations:
            print(f"  找到 {len(instantiations)} 个实例化语句:")
            for line_num, line in instantiations:
                print(f"    行 {line_num}: {line}")
        
        if not imports and not instantiations:
            print(f"  ℹ️ 未找到MemoryAgent的使用")
            continue
        
        if apply_replacement(file_path, dry_run=args.dry_run):
            total_modified += 1
    
    print("\n" + "=" * 80)
    print("替换完成")
    print("=" * 80)
    print(f"处理文件数: {len(target_files)}")
    print(f"修改文件数: {total_modified}")
    
    if args.dry_run:
        print("\n💡 提示: 使用 --dry-run=false 来实际应用更改")
    else:
        print("\n✅ 替换已应用")


if __name__ == "__main__":
    main()

