#!/usr/bin/env python3
"""
检查LangGraph节点函数的docstring是否符合规范

使用方法:
    python scripts/check_node_docstrings.py
    python scripts/check_node_docstrings.py --fix  # 自动修复格式问题
"""
import ast
import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import argparse

# 节点文件路径模式
NODE_FILE_PATTERNS = [
    "src/core/langgraph_*.py",
    "src/core/*_nodes.py",
]

# docstring格式正则表达式
DOCSTRING_PATTERN = re.compile(r'^"""(.+?)\s*-\s*(.+?)"""$')


class NodeDocstringChecker:
    """节点docstring检查器"""
    
    def __init__(self, fix: bool = False):
        self.fix = fix
        self.issues: List[Tuple[str, int, str]] = []
        self.fixed_count = 0
    
    def check_file(self, file_path: Path) -> bool:
        """检查单个文件的节点docstring"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if self._is_node_function(node):
                        self._check_node_docstring(file_path, node, content)
            
            return len(self.issues) == 0
        except Exception as e:
            print(f"❌ 检查文件 {file_path} 时出错: {e}")
            return False
    
    def _is_node_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """判断是否是节点函数"""
        # 检查函数名是否以_node结尾
        if node.name.endswith('_node'):
            return True
        
        # 检查参数是否包含state: ResearchSystemState
        for arg in node.args.args:
            if arg.arg == 'state':
                # 检查类型注解
                if arg.annotation:
                    ann_str = ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else str(arg.annotation)
                    if 'ResearchSystemState' in ann_str:
                        return True
        
        return False
    
    def _check_node_docstring(self, file_path: Path, node: ast.FunctionDef | ast.AsyncFunctionDef, content: str):
        """检查节点函数的docstring"""
        # 获取docstring
        docstring = ast.get_docstring(node)
        
        if not docstring:
            self.issues.append((
                str(file_path),
                node.lineno,
                f"节点函数 '{node.name}' 缺少docstring"
            ))
            return
        
        # 检查docstring格式
        docstring_lines = docstring.strip().split('\n')
        first_line = docstring_lines[0].strip()
        
        # 检查是否是单行格式
        if len(docstring_lines) > 1:
            self.issues.append((
                str(file_path),
                node.lineno,
                f"节点函数 '{node.name}' 的docstring应该是单行格式，当前是多行格式"
            ))
            return
        
        # 检查格式是否符合规范：节点名称 - 功能说明
        if ' - ' not in first_line:
            self.issues.append((
                str(file_path),
                node.lineno,
                f"节点函数 '{node.name}' 的docstring格式不正确，应该是 '节点名称 - 功能说明'"
            ))
            if self.fix:
                # 尝试修复：如果没有" - "，添加默认格式
                # 这里只是示例，实际修复需要更智能的逻辑
                pass
        
        # 检查是否以节点名称开头
        node_name_match = re.match(r'^(.+?)\s*-\s*(.+)$', first_line)
        if not node_name_match:
            self.issues.append((
                str(file_path),
                node.lineno,
                f"节点函数 '{node.name}' 的docstring格式不正确，应该是 '节点名称 - 功能说明'"
            ))
    
    def check_all_files(self) -> bool:
        """检查所有节点文件"""
        project_root = Path(__file__).parent.parent
        node_files = []
        
        for pattern in NODE_FILE_PATTERNS:
            for file_path in project_root.glob(pattern):
                if file_path.is_file() and file_path.suffix == '.py':
                    node_files.append(file_path)
        
        print(f"🔍 找到 {len(node_files)} 个节点文件")
        
        for file_path in sorted(node_files):
            self.check_file(file_path)
        
        return len(self.issues) == 0
    
    def print_report(self):
        """打印检查报告"""
        if not self.issues:
            print("✅ 所有节点函数的docstring都符合规范！")
            return
        
        print(f"\n⚠️ 发现 {len(self.issues)} 个问题：\n")
        
        current_file = None
        for file_path, line_no, issue in self.issues:
            if file_path != current_file:
                print(f"\n📄 {file_path}:")
                current_file = file_path
            print(f"  第 {line_no} 行: {issue}")
        
        print(f"\n💡 提示：")
        print(f"  - 节点函数docstring格式：\"\"\"节点名称 - 功能说明\"\"\"")
        print(f"  - 修改节点功能时，记得同步更新docstring")
        print(f"  - 使用 'lgnode' 代码片段快速创建符合规范的节点函数")


def main():
    parser = argparse.ArgumentParser(description="检查LangGraph节点函数的docstring")
    parser.add_argument('--fix', action='store_true', help='自动修复格式问题（实验性）')
    args = parser.parse_args()
    
    checker = NodeDocstringChecker(fix=args.fix)
    success = checker.check_all_files()
    checker.print_report()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

