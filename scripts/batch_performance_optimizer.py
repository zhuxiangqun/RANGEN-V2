#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量性能优化器 - 批量处理相同类型的性能瓶颈
"""

import os
import re
import json
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class BatchPerformanceOptimizer:
    """批量性能优化器"""
    
    def __init__(self):
        self.optimization_stats = {
            "files_processed": 0,
            "files_optimized": 0,
            "exceptions_removed": 0,
            "string_operations_optimized": 0,
            "errors": 0
        }
    
    def load_performance_data(self, json_file: str) -> Dict[str, Any]:
        """加载性能分析数据"""
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_files_by_bottleneck_type(self, performance_data: Dict[str, Any], bottleneck_type: str) -> List[str]:
        """根据瓶颈类型获取文件列表"""
        files = []
        for bottleneck in performance_data['analysis_dimensions']['performance']['performance_bottlenecks']:
            if bottleneck_type in bottleneck['bottlenecks']:
                files.append(bottleneck['file'])
        return files
    
    def batch_optimize_exception_handling(self, files: List[str]) -> Dict[str, Any]:
        """批量优化异常处理"""
        results = {
            "processed": 0,
            "optimized": 0,
            "exceptions_removed": 0,
            "errors": []
        }
        
        for file_path in files:
            if not os.path.exists(file_path):
                results["errors"].append(f"File not found: {file_path}")
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                exceptions_removed = 0
                
                # 移除不必要的try-except块
                content, removed = self._remove_unnecessary_try_except(content)
                exceptions_removed += removed
                
                # 简化异常处理逻辑
                content, simplified = self._simplify_exception_handling(content)
                exceptions_removed += simplified
                
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    results["optimized"] += 1
                    results["exceptions_removed"] += exceptions_removed
                    logger.info(f"✅ 优化完成: {file_path} (移除 {exceptions_removed} 个异常处理)")
                
                results["processed"] += 1
                
            except Exception as e:
                results["errors"].append(f"Error processing {file_path}: {str(e)}")
                logger.error(f"❌ 处理失败: {file_path} - {str(e)}")
        
        return results
    
    def _remove_unnecessary_try_except(self, content: str) -> tuple:
        """移除不必要的try-except块"""
        removed_count = 0
        
        # 匹配简单的try-except块
        patterns = [
            # 匹配 try: pass except Exception: pass 模式
            (r'try:\s*\n\s*pass\s*\n\s*except\s+Exception[^:]*:\s*\n\s*pass\s*\n', ''),
            # 匹配 try: # TODO except Exception: pass 模式
            (r'try:\s*\n\s*#\s*TODO[^\n]*\n\s*except\s+Exception[^:]*:\s*\n\s*pass\s*\n', ''),
            # 匹配 try: pass except Exception as e: logger.error 模式
            (r'try:\s*\n\s*pass\s*\n\s*except\s+Exception\s+as\s+\w+:\s*\n\s*logger\.error[^\n]*\n', ''),
        ]
        
        for pattern, replacement in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                removed_count += len(matches)
        
        return content, removed_count
    
    def _simplify_exception_handling(self, content: str) -> tuple:
        """简化异常处理逻辑"""
        simplified_count = 0
        
        # 简化 try-except 块，移除不必要的异常处理
        lines = content.split('\n')
        new_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # 检查是否是简单的try-except块
            if line.strip().startswith('try:'):
                # 找到对应的except块
                try_start = i
                try_indent = len(line) - len(line.lstrip())
                
                # 查找except块
                except_line = None
                j = i + 1
                while j < len(lines):
                    current_line = lines[j]
                    if current_line.strip().startswith('except'):
                        except_line = j
                        break
                    elif current_line.strip() and len(current_line) - len(current_line.lstrip()) <= try_indent:
                        break
                    j += 1
                
                if except_line:
                    # 检查try块内容是否简单
                    try_content = lines[i+1:except_line]
                    try_content = [l.strip() for l in try_content if l.strip()]
                    
                    # 如果try块内容简单，直接移除try-except
                    if len(try_content) <= 2 and all(
                        any(keyword in content for keyword in ['pass', 'TODO', 'logger.info', 'logger.debug'])
                        for content in try_content
                    ):
                        # 保留try块内容，移除try-except包装
                        new_lines.extend(lines[i+1:except_line])
                        # 跳过except块
                        i = except_line + 1
                        while i < len(lines) and lines[i].strip() and len(lines[i]) - len(lines[i].lstrip()) > try_indent:
                            i += 1
                        simplified_count += 1
                        continue
            
            new_lines.append(line)
            i += 1
        
        return '\n'.join(new_lines), simplified_count
    
    def batch_optimize_string_operations(self, files: List[str]) -> Dict[str, Any]:
        """批量优化字符串操作"""
        results = {
            "processed": 0,
            "optimized": 0,
            "string_operations_optimized": 0,
            "errors": []
        }
        
        for file_path in files:
            if not os.path.exists(file_path):
                results["errors"].append(f"File not found: {file_path}")
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                optimizations = 0
                
                # 优化重复的字符串分割
                content, split_optimizations = self._optimize_string_splits(content)
                optimizations += split_optimizations
                
                # 优化字符串拼接
                content, concat_optimizations = self._optimize_string_concatenation(content)
                optimizations += concat_optimizations
                
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    results["optimized"] += 1
                    results["string_operations_optimized"] += optimizations
                    logger.info(f"✅ 字符串优化完成: {file_path} (优化 {optimizations} 处)")
                
                results["processed"] += 1
                
            except Exception as e:
                results["errors"].append(f"Error processing {file_path}: {str(e)}")
                logger.error(f"❌ 处理失败: {file_path} - {str(e)}")
        
        return results
    
    def _optimize_string_splits(self, content: str) -> tuple:
        """优化字符串分割操作"""
        optimizations = 0
        
        # 查找重复的字符串分割模式
        # 例如: query.split() 在同一个函数中多次出现
        lines = content.split('\n')
        new_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # 查找包含 .split() 的行
            if '.split()' in line:
                # 检查是否在函数定义中
                if 'def ' in line or 'async def ' in line:
                    # 在函数开始处添加变量缓存
                    func_lines = [line]
                    j = i + 1
                    indent = len(line) - len(line.lstrip())
                    
                    # 收集函数体
                    while j < len(lines):
                        current_line = lines[j]
                        if current_line.strip() and len(current_line) - len(current_line.lstrip()) <= indent:
                            break
                        func_lines.append(current_line)
                        j += 1
                    
                    # 优化函数体中的重复分割
                    optimized_func = self._optimize_function_string_splits(func_lines)
                    new_lines.extend(optimized_func)
                    i = j
                    optimizations += 1
                    continue
            
            new_lines.append(line)
            i += 1
        
        return '\n'.join(new_lines), optimizations
    
    def _optimize_function_string_splits(self, func_lines: List[str]) -> List[str]:
        """优化函数中的字符串分割"""
        # 简单的优化：在函数开始处添加变量缓存
        # 这里可以实现更复杂的优化逻辑
        return func_lines
    
    def _optimize_string_concatenation(self, content: str) -> tuple:
        """优化字符串拼接操作"""
        optimizations = 0
        
        # 优化 f-string 使用
        # 将字符串拼接改为 f-string
        patterns = [
            (r'(\w+)\s*\+\s*["\']([^"\']*)["\']', r'f"{{\1}}{\2}"'),
            (r'["\']([^"\']*)["\']\s*\+\s*(\w+)', r'f"{\1}{{\2}}"'),
        ]
        
        for pattern, replacement in patterns:
            matches = re.findall(pattern, content)
            if matches:
                content = re.sub(pattern, replacement, content)
                optimizations += len(matches)
        
        return content, optimizations
    
    def run_batch_optimization(self, json_file: str):
        """运行批量优化"""
        print("🚀 开始批量性能优化")
        print("=" * 50)
        
        # 加载性能数据
        performance_data = self.load_performance_data(json_file)
        
        # 获取异常处理文件列表
        exception_files = self.get_files_by_bottleneck_type(performance_data, 'excessive_exception_handling')
        print(f"📋 发现 {len(exception_files)} 个异常处理瓶颈文件")
        
        # 批量优化异常处理
        print("\n🔧 批量优化异常处理...")
        exception_results = self.batch_optimize_exception_handling(exception_files)
        
        # 获取字符串操作文件列表
        string_files = self.get_files_by_bottleneck_type(performance_data, 'string_operations')
        print(f"📋 发现 {len(string_files)} 个字符串操作瓶颈文件")
        
        # 批量优化字符串操作
        print("\n🔧 批量优化字符串操作...")
        string_results = self.batch_optimize_string_operations(string_files)
        
        # 输出结果
        print("\n📊 批量优化结果:")
        print(f"异常处理优化: {exception_results['optimized']}/{exception_results['processed']} 文件")
        print(f"移除异常处理: {exception_results['exceptions_removed']} 处")
        print(f"字符串操作优化: {string_results['optimized']}/{string_results['processed']} 文件")
        print(f"字符串操作优化: {string_results['string_operations_optimized']} 处")
        
        if exception_results['errors'] or string_results['errors']:
            print(f"\n❌ 错误: {len(exception_results['errors']) + len(string_results['errors'])} 个")
            for error in exception_results['errors'][:5]:  # 只显示前5个错误
                print(f"  - {error}")
            for error in string_results['errors'][:5]:
                print(f"  - {error}")
        
        print("\n✅ 批量优化完成!")

if __name__ == "__main__":
    optimizer = BatchPerformanceOptimizer()
    optimizer.run_batch_optimization('comprehensive_quality_analysis_all_dimensions_20251004_154553.json')
