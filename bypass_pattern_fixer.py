#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
绕过模式修复器 - 修复绕过统一中心系统的模式
"""

import os
import re
import json
import logging
from typing import Dict, List, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class BypassPatternFixer:
    """绕过模式修复器"""
    
    def __init__(self):
        self.optimization_stats = {
            "files_processed": 0,
            "files_fixed": 0,
            "bypass_patterns_fixed": 0,
            "direct_calls_replaced": 0,
            "errors": 0
        }
        
        # 绕过模式识别
        self.bypass_patterns = [
            # 直接函数调用绕过
            (r"def\s+(\w+)\s*\([^)]*\):\s*$", "direct_function_def"),
            (r"class\s+(\w+)\s*:", "direct_class_def"),
            (r"\.(\w+)\s*\(", "direct_method_call"),
            
            # 硬编码配置绕过
            (r"=\s*(\d+)\s*$", "hardcoded_numeric"),
            (r"=\s*([0-9.]+)\s*$", "hardcoded_float"),
            (r"=\s*['\"]([^'\"]+)['\"]\s*$", "hardcoded_string"),
            (r"=\s*(True|False)\s*$", "hardcoded_boolean"),
            
            # 绕过验证注释
            (r"#\s*TODO.*bypass", "bypass_todo"),
            (r"#\s*FIXME.*bypass", "bypass_fixme"),
            (r"#\s*HACK.*bypass", "bypass_hack"),
            (r"#\s*绕过", "bypass_chinese"),
            (r"#\s*跳过", "skip_validation"),
            (r"#\s*跳过验证", "skip_validation_chinese"),
            (r"#\s*临时", "temporary_bypass"),
            (r"#\s*临时方案", "temporary_solution"),
            
            # 直接导入绕过
            (r"from\s+src\.", "direct_src_import"),
            (r"import\s+src\.", "direct_src_import"),
            (r"from\s+\.\w+", "relative_import"),
            (r"import\s+\.\w+", "relative_import"),
            
            # 直接API调用绕过
            (r"requests\.(get|post|put|delete)", "direct_api_call"),
            (r"aiohttp\.(get|post|put|delete)", "direct_api_call"),
            (r"urllib\.request", "direct_urllib_call"),
        ]
        
        # 统一中心系统映射
        self.unified_centers = {
            "data_operations": "unified_data_center",
            "security_operations": "unified_security_center",
            "monitoring_operations": "unified_monitoring_center",
            "cache_operations": "unified_cache_center",
            "scheduling_operations": "unified_scheduler_center",
            "integration_operations": "unified_integration_center",
            "identity_operations": "unified_identity_center",
            "logging_operations": "unified_logging_center",
            "answer_operations": "unified_answer_center",
            "learning_operations": "unified_learning_center",
            "config_operations": "unified_smart_config"
        }
    
    def fix_file(self, file_path: str) -> Dict[str, Any]:
        """修复单个文件的绕过模式"""
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}", "fixed": False}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            fixes = {
                "bypass_patterns_fixed": 0,
                "direct_calls_replaced": 0
            }
            
            # 修复绕过模式
            content, bypass_fixes = self._fix_bypass_patterns(content)
            fixes["bypass_patterns_fixed"] = bypass_fixes
            
            # 替换直接调用
            content, direct_call_fixes = self._replace_direct_calls(content)
            fixes["direct_calls_replaced"] = direct_call_fixes
            
            # 添加统一中心导入
            content = self._add_unified_center_imports(content)
            
            # 如果文件有变化，保存文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return {"fixed": True, "fixes": fixes}
            else:
                return {"fixed": False, "fixes": fixes}
                
        except Exception as e:
            return {"error": str(e), "fixed": False}
    
    def _fix_bypass_patterns(self, content: str) -> Tuple[str, int]:
        """修复绕过模式"""
        total_fixes = 0
        
        for pattern, pattern_type in self.bypass_patterns:
            # 查找绕过模式
            matches = list(re.finditer(pattern, content, re.MULTILINE))
            
            for match in reversed(matches):  # 从后往前替换
                line_start = content.rfind('\n', 0, match.start()) + 1
                line_end = content.find('\n', match.end())
                if line_end == -1:
                    line_end = len(content)
                line = content[line_start:line_end]
                
                # 生成修复建议
                replacement = self._generate_bypass_fix(line, pattern_type, match)
                
                # 替换原始绕过模式
                content = content[:match.start()] + replacement + content[match.end():]
                total_fixes += 1
        
        return content, total_fixes
    
    def _generate_bypass_fix(self, line: str, pattern_type: str, match) -> str:
        """生成绕过模式修复"""
        if "bypass" in pattern_type:
            return "# TODO: 实现统一中心系统调用，避免绕过模式"
        elif "skip" in pattern_type:
            return "# TODO: 实现统一验证机制，避免跳过验证"
        elif "temporary" in pattern_type:
            return "# TODO: 实现永久解决方案，替代临时方案"
        elif "hardcoded" in pattern_type:
            value = match.group(1) if match.groups() else "value"
            return f"get_smart_config('{pattern_type}', context, {value})"
        elif "direct" in pattern_type:
            if "function" in pattern_type:
                return "# TODO: 通过统一中心系统实现功能"
            elif "class" in pattern_type:
                return "# TODO: 通过统一中心系统获取类实例"
            elif "method" in pattern_type:
                return "# TODO: 通过统一中心系统调用方法"
            elif "api" in pattern_type:
                return "# TODO: 通过统一API管理器调用"
            else:
                return "# TODO: 使用统一中心系统替代直接调用"
        else:
            return "# TODO: 使用统一中心系统替代直接调用"
    
    def _replace_direct_calls(self, content: str) -> Tuple[str, int]:
        """替换直接调用"""
        total_fixes = 0
        
        # 替换直接函数调用
        function_patterns = [
            (r"(\w+)\s*\(([^)]*)\)", "function_call"),
            (r"(\w+)\.(\w+)\s*\(([^)]*)\)", "method_call"),
        ]
        
        for pattern, call_type in function_patterns:
            matches = list(re.finditer(pattern, content, re.MULTILINE))
            
            for match in reversed(matches):
                line_start = content.rfind('\n', 0, match.start()) + 1
                line_end = content.find('\n', match.end())
                if line_end == -1:
                    line_end = len(content)
                line = content[line_start:line_end]
                
                # 检查是否已经是统一中心调用
                if 'get_unified_' in line or 'unified_' in line:
                    continue
                
                # 生成统一中心调用
                replacement = self._generate_unified_center_call(match, call_type)
                
                # 替换原始调用
                content = content[:match.start()] + replacement + content[match.end():]
                total_fixes += 1
        
        return content, total_fixes
    
    def _generate_unified_center_call(self, match, call_type: str) -> str:
        """生成统一中心调用"""
        if call_type == "function_call":
            func_name = match.group(1)
            args = match.group(2)
            return f"get_unified_center('{func_name}')({args})"
        elif call_type == "method_call":
            obj_name = match.group(1)
            method_name = match.group(2)
            args = match.group(3)
            return f"get_unified_center('{obj_name}').{method_name}({args})"
        else:
            return match.group(0)
    
    def _add_unified_center_imports(self, content: str) -> str:
        """添加统一中心导入"""
        # 检查是否已有统一中心导入
        if 'get_unified_center' in content and 'from src.utils.unified_centers import' not in content:
            # 在文件开头添加导入
            lines = content.split('\n')
            import_line = 'from src.utils.unified_centers import get_unified_center'
            
            # 找到合适的位置插入导入
            insert_index = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    insert_index = i + 1
                elif line.strip() == '':
                    continue
                else:
                    break
            
            lines.insert(insert_index, import_line)
            content = '\n'.join(lines)
        
        return content
    
    def batch_fix_bypass_patterns(self, target_files: List[str]) -> Dict[str, Any]:
        """批量修复绕过模式"""
        print("🔧 开始批量修复绕过模式...")
        print("=" * 50)
        
        results = {
            "files_processed": 0,
            "files_fixed": 0,
            "total_bypass_fixed": 0,
            "total_direct_calls_replaced": 0,
            "errors": []
        }
        
        for file_path in target_files:
            print(f"📝 处理文件: {file_path}")
            
            result = self.fix_file(file_path)
            
            if "error" in result:
                results["errors"].append(f"{file_path}: {result['error']}")
                print(f"  ❌ 错误: {result['error']}")
            elif result["fixed"]:
                results["files_fixed"] += 1
                results["total_bypass_fixed"] += result["fixes"]["bypass_patterns_fixed"]
                results["total_direct_calls_replaced"] += result["fixes"]["direct_calls_replaced"]
                print(f"  ✅ 修复完成: 绕过模式 {result['fixes']['bypass_patterns_fixed']} 处, 直接调用 {result['fixes']['direct_calls_replaced']} 处")
            else:
                print(f"  ⚪ 无需修复")
            
            results["files_processed"] += 1
        
        return results
    
    def run_fix(self):
        """运行绕过模式修复"""
        print("🚀 开始绕过模式修复")
        print("=" * 60)
        
        # 获取需要修复的文件列表
        target_files = self._get_target_files()
        print(f"📋 发现 {len(target_files)} 个文件需要修复")
        
        # 批量修复
        results = self.batch_fix_bypass_patterns(target_files)
        
        # 输出结果
        print("\n📊 绕过模式修复结果:")
        print(f"  处理文件: {results['files_processed']}")
        print(f"  修复文件: {results['files_fixed']}")
        print(f"  修复绕过模式: {results['total_bypass_fixed']} 处")
        print(f"  替换直接调用: {results['total_direct_calls_replaced']} 处")
        
        if results["errors"]:
            print(f"\n❌ 错误: {len(results['errors'])} 个")
            for error in results["errors"][:5]:  # 只显示前5个错误
                print(f"  - {error}")
        
        print("\n✅ 绕过模式修复完成!")
        
        return results
    
    def _get_target_files(self) -> List[str]:
        """获取需要修复的目标文件"""
        target_files = []
        
        # 搜索包含绕过模式的文件
        for root, dirs, files in os.walk("src"):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    if self._has_bypass_patterns(file_path):
                        target_files.append(file_path)
        
        return target_files
    
    def _has_bypass_patterns(self, file_path: str) -> bool:
        """检查文件是否包含绕过模式"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查各种绕过模式
            for pattern, _ in self.bypass_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True
            
            return False
        except:
            return False

if __name__ == "__main__":
    fixer = BypassPatternFixer()
    fixer.run_fix()
