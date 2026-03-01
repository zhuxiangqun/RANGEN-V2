#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent使用情况分析脚本

分析代码库中Agent的真实使用情况，为迁移决策提供数据支持。
"""

import ast
import os
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


class AgentUsageAnalyzer:
    """Agent使用情况分析器"""
    
    def __init__(self, codebase_path: str = "src/"):
        self.codebase_path = Path(codebase_path)
        self.agent_imports = Counter()
        self.agent_instantiations = Counter()
        self.agent_method_calls = Counter()
        self.agent_locations = {}  # Agent -> [文件路径列表]
        self.file_agent_map = {}  # 文件路径 -> [Agent列表]
        
    def analyze(self) -> Dict[str, Any]:
        """分析整个代码库中的Agent使用情况"""
        print(f"🔍 开始分析代码库: {self.codebase_path}")
        
        # 遍历所有Python文件
        python_files = list(self.codebase_path.rglob("*.py"))
        total_files = len(python_files)
        
        for idx, filepath in enumerate(python_files, 1):
            if idx % 10 == 0:
                print(f"  处理进度: {idx}/{total_files} ({idx*100//total_files}%)")
            self._analyze_file(filepath)
        
        print(f"✅ 分析完成，共处理 {total_files} 个文件")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "codebase_path": str(self.codebase_path),
            "total_files": total_files,
            "imports": dict(self.agent_imports),
            "instantiations": dict(self.agent_instantiations),
            "method_calls": dict(self.agent_method_calls),
            "agent_locations": self.agent_locations,
            "file_agent_map": self.file_agent_map,
            "total_agent_references": sum(self.agent_imports.values()),
            "unique_agents": len(self.agent_imports),
        }
    
    def _analyze_file(self, filepath: Path):
        """分析单个文件"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(filepath))
            file_agents = set()
            
            # 遍历AST节点
            for node in ast.walk(tree):
                # 1. 查找import语句
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        agent_name = self._extract_agent_name(alias.name)
                        if agent_name:
                            self.agent_imports[agent_name] += 1
                            file_agents.add(agent_name)
                            self._add_location(agent_name, filepath)
                
                # 2. 查找from import语句
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        agent_name = self._extract_agent_name(node.module)
                        if agent_name:
                            self.agent_imports[agent_name] += 1
                            file_agents.add(agent_name)
                            self._add_location(agent_name, filepath)
                    
                    # 检查导入的类名
                    for alias in node.names:
                        agent_name = self._extract_agent_name(alias.name)
                        if agent_name:
                            self.agent_imports[agent_name] += 1
                            file_agents.add(agent_name)
                            self._add_location(agent_name, filepath)
                
                # 3. 查找类实例化
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        agent_name = self._extract_agent_name(node.func.id)
                        if agent_name:
                            self.agent_instantiations[agent_name] += 1
                            file_agents.add(agent_name)
                            self._add_location(agent_name, filepath)
                    elif isinstance(node.func, ast.Attribute):
                        agent_name = self._extract_agent_name(node.func.attr)
                        if agent_name:
                            self.agent_instantiations[agent_name] += 1
                            file_agents.add(agent_name)
                            self._add_location(agent_name, filepath)
                
                # 4. 查找方法调用
                elif isinstance(node, ast.Attribute):
                    agent_name = self._extract_agent_name(node.attr)
                    if agent_name:
                        self.agent_method_calls[agent_name] += 1
                        file_agents.add(agent_name)
                        self._add_location(agent_name, filepath)
            
            # 记录文件中的Agent
            if file_agents:
                self.file_agent_map[str(filepath)] = list(file_agents)
                
        except SyntaxError as e:
            print(f"⚠️  语法错误，跳过文件: {filepath} - {e}")
        except Exception as e:
            print(f"⚠️  分析文件失败: {filepath} - {e}")
    
    def _extract_agent_name(self, name: str) -> str:
        """从名称中提取Agent名称"""
        if not name:
            return None
        
        name_lower = name.lower()
        
        # 检查是否是Agent相关
        if "agent" in name_lower:
            # 提取Agent类名
            if name.endswith("Agent"):
                return name
            elif "agent" in name_lower:
                # 尝试从模块路径中提取
                parts = name.split(".")
                for part in parts:
                    if part.endswith("Agent"):
                        return part
        
        return None
    
    def _add_location(self, agent_name: str, filepath: Path):
        """添加Agent位置信息"""
        filepath_str = str(filepath)
        if agent_name not in self.agent_locations:
            self.agent_locations[agent_name] = []
        if filepath_str not in self.agent_locations[agent_name]:
            self.agent_locations[agent_name].append(filepath_str)
    
    def generate_report(self, output_file: str = "agent_usage_analysis.json"):
        """生成分析报告"""
        results = self.analyze()
        
        # 保存JSON报告
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 分析报告已保存: {output_file}")
        
        # 打印Top 10 Agent
        print("\n📈 Top 10 使用频率最高的Agent:")
        sorted_imports = sorted(
            results["imports"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        for idx, (agent, count) in enumerate(sorted_imports, 1):
            print(f"  {idx:2d}. {agent:40s} - {count:4d} 次导入")
        
        return results


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="分析Agent使用情况")
    parser.add_argument(
        "--codebase-path",
        type=str,
        default="src/",
        help="代码库路径（默认: src/）"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="agent_usage_analysis.json",
        help="输出文件路径（默认: agent_usage_analysis.json）"
    )
    
    args = parser.parse_args()
    
    analyzer = AgentUsageAnalyzer(codebase_path=args.codebase_path)
    results = analyzer.generate_report(output_file=args.output)
    
    print(f"\n✅ 分析完成！")
    print(f"   - 总文件数: {results['total_files']}")
    print(f"   - 唯一Agent数: {results['unique_agents']}")
    print(f"   - 总引用次数: {results['total_agent_references']}")


if __name__ == "__main__":
    main()

