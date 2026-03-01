#!/usr/bin/env python3
"""
应用AnswerGenerationAgent逐步替换

将代码中的AnswerGenerationAgent替换为使用逐步替换策略的包装器。
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def find_answer_generation_agent_imports(file_path: Path) -> List[Tuple[int, str]]:
    """查找AnswerGenerationAgent的导入语句"""
    imports = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                if 'from' in line and 'AnswerGenerationAgent' in line and 'import' in line:
                    imports.append((i, line.strip()))
    except Exception as e:
        print(f"⚠️ 读取文件失败 {file_path}: {e}")
    return imports


def find_answer_generation_agent_instantiations(file_path: Path) -> List[Tuple[int, str]]:
    """查找AnswerGenerationAgent的实例化语句"""
    instantiations = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                if 'AnswerGenerationAgent(' in line:
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
        # from src.agents.expert_agents import AnswerGenerationAgent
        # -> from src.agents.answer_generation_agent_wrapper import AnswerGenerationAgentWrapper as AnswerGenerationAgent
        pattern1a = r'from\s+src\.agents\.expert_agents\s+import\s+AnswerGenerationAgent\b'
        replacement1a = 'from src.agents.answer_generation_agent_wrapper import AnswerGenerationAgentWrapper as AnswerGenerationAgent'
        pattern1b = r'from\s+\.expert_agents\s+import\s+AnswerGenerationAgent\b'
        replacement1b = 'from .answer_generation_agent_wrapper import AnswerGenerationAgentWrapper as AnswerGenerationAgent'
        
        if re.search(pattern1a, content):
            content = re.sub(pattern1a, replacement1a, content)
            modified = True
            print(f"  ✅ 替换导入语句（绝对路径）")
        if re.search(pattern1b, content):
            content = re.sub(pattern1b, replacement1b, content)
            modified = True
            print(f"  ✅ 替换导入语句（相对路径）")
        
        # 替换实例化语句
        # AnswerGenerationAgent() -> AnswerGenerationAgentWrapper(enable_gradual_replacement=True)
        pattern2 = r'\bAnswerGenerationAgent\s*\(([^)]*)\)'
        def replace_instantiation(match):
            params = match.group(1).strip()
            if params:
                # 如果已有参数，添加enable_gradual_replacement
                if 'enable_gradual_replacement' not in params:
                    return f'AnswerGenerationAgentWrapper({params}, enable_gradual_replacement=True)'
                else:
                    return match.group(0)  # 已经存在，不替换
            else:
                # 没有参数，添加enable_gradual_replacement
                return 'AnswerGenerationAgentWrapper(enable_gradual_replacement=True)'
        
        if re.search(pattern2, content):
            new_content = re.sub(pattern2, replace_instantiation, content)
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
            else:
                print(f"  🔍 [DRY RUN] 将更新文件: {file_path}")
        
        return modified
        
    except Exception as e:
        print(f"  ❌ 处理文件失败 {file_path}: {e}")
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="应用AnswerGenerationAgent逐步替换")
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
    print("AnswerGenerationAgent逐步替换应用")
    print("=" * 80)
    print(f"模式: {'🔍 DRY RUN (预览模式)' if args.dry_run else '✏️ 实际修改'}")
    print("=" * 80)
    
    # 需要处理的文件列表
    target_files = []
    
    if args.file:
        target_files.append(Path(args.file))
    else:
        # 默认处理所有相关文件
        target_files = [
            Path("src/unified_research_system.py"),
            Path("src/agents/rag_agent.py"),
        ]
    
    total_modified = 0
    
    for file_path in target_files:
        if not file_path.exists():
            print(f"\n⚠️ 文件不存在: {file_path}")
            continue
        
        print(f"\n📄 处理文件: {file_path}")
        
        # 查找导入和实例化
        imports = find_answer_generation_agent_imports(file_path)
        instantiations = find_answer_generation_agent_instantiations(file_path)
        
        if imports:
            print(f"  找到 {len(imports)} 个导入语句:")
            for line_num, line in imports:
                print(f"    行 {line_num}: {line}")
        
        if instantiations:
            print(f"  找到 {len(instantiations)} 个实例化语句:")
            for line_num, line in instantiations:
                print(f"    行 {line_num}: {line}")
        
        if not imports and not instantiations:
            print(f"  ℹ️ 未找到AnswerGenerationAgent的使用")
            continue
        
        # 应用替换
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
        print("📝 下一步:")
        print("   1. 检查修改的文件")
        print("   2. 运行测试验证功能")
        print("   3. 启动逐步替换监控: python3 scripts/start_gradual_replacement.py --source AnswerGenerationAgent")


if __name__ == "__main__":
    main()

