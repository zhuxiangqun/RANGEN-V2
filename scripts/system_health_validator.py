#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统健康验证器 - 验证系统优化效果和健康状态
"""

import os
import re
import json
import logging
import time
from typing import Dict, List, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class SystemHealthValidator:
    """系统健康验证器"""
    
    def __init__(self):
        self.validation_results = {
            "total_files_checked": 0,
            "optimization_compliance": 0,
            "hardcode_issues": 0,
            "bypass_patterns": 0,
            "security_issues": 0,
            "performance_issues": 0,
            "documentation_coverage": 0,
            "integration_quality": 0,
            "errors": []
        }
        
        # 验证规则
        self.validation_rules = {
            "hardcode_patterns": [
                r'=\s*(\d+)\s*$',
                r'=\s*([0-9.]+)\s*$',
                r'=\s*["\']([^"\']+)["\']\s*$',
                r'=\s*(True|False)\s*$',
            ],
            "bypass_patterns": [
                r'#\s*TODO.*bypass',
                r'#\s*FIXME.*bypass',
                r'#\s*HACK.*bypass',
                r'#\s*绕过',
                r'#\s*跳过',
                r'#\s*临时',
            ],
            "security_patterns": [
                r'eval\s*\(',
                r'exec\s*\(',
                r'__import__\s*\(',
                r'os\.system\s*\(',
                r'subprocess\.call\s*\(',
            ],
            "performance_patterns": [
                r'try:\s*\n.*except\s+Exception:',
                r'for\s+\w+\s+in\s+.*:\s*\n.*for\s+\w+\s+in\s+.*:',
                r'\.split\(\)\s*\.split\(\)',
            ],
            "documentation_patterns": [
                r'def\s+\w+.*:\s*$',
                r'class\s+\w+.*:\s*$',
            ]
        }
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """验证单个文件"""
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}", "valid": False}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            validation_result = {
                "file_path": file_path,
                "hardcode_issues": 0,
                "bypass_patterns": 0,
                "security_issues": 0,
                "performance_issues": 0,
                "documentation_issues": 0,
                "has_unified_centers": False,
                "has_smart_config": False,
                "valid": True
            }
            
            # 检查硬编码问题
            for pattern in self.validation_rules["hardcode_patterns"]:
                matches = re.findall(pattern, content, re.MULTILINE)
                validation_result["hardcode_issues"] += len(matches)
            
            # 检查绕过模式
            for pattern in self.validation_rules["bypass_patterns"]:
                matches = re.findall(pattern, content, re.IGNORECASE)
                validation_result["bypass_patterns"] += len(matches)
            
            # 检查安全问题
            for pattern in self.validation_rules["security_patterns"]:
                matches = re.findall(pattern, content)
                validation_result["security_issues"] += len(matches)
            
            # 检查性能问题
            for pattern in self.validation_rules["performance_patterns"]:
                matches = re.findall(pattern, content, re.DOTALL)
                validation_result["performance_issues"] += len(matches)
            
            # 检查文档问题
            for pattern in self.validation_rules["documentation_patterns"]:
                matches = re.findall(pattern, content, re.MULTILINE)
                validation_result["documentation_issues"] += len(matches)
            
            # 检查统一中心系统使用
            validation_result["has_unified_centers"] = "unified_" in content and "center" in content
            validation_result["has_smart_config"] = "get_smart_config" in content or "unified_smart_config" in content
            
            return validation_result
            
        except Exception as e:
            return {"error": str(e), "valid": False}
    
    def batch_validate_system(self, target_files: List[str]) -> Dict[str, Any]:
        """批量验证系统"""
        print("🔍 开始系统健康验证...")
        print("=" * 50)
        
        results = {
            "total_files_checked": 0,
            "valid_files": 0,
            "total_hardcode_issues": 0,
            "total_bypass_patterns": 0,
            "total_security_issues": 0,
            "total_performance_issues": 0,
            "total_documentation_issues": 0,
            "files_with_unified_centers": 0,
            "files_with_smart_config": 0,
            "errors": []
        }
        
        for file_path in target_files:
            print(f"🔍 验证文件: {file_path}")
            
            result = self.validate_file(file_path)
            
            if "error" in result:
                results["errors"].append(f"{file_path}: {result['error']}")
                print(f"  ❌ 错误: {result['error']}")
            else:
                results["valid_files"] += 1
                results["total_hardcode_issues"] += result["hardcode_issues"]
                results["total_bypass_patterns"] += result["bypass_patterns"]
                results["total_security_issues"] += result["security_issues"]
                results["total_performance_issues"] += result["performance_issues"]
                results["total_documentation_issues"] += result["documentation_issues"]
                
                if result["has_unified_centers"]:
                    results["files_with_unified_centers"] += 1
                if result["has_smart_config"]:
                    results["files_with_smart_config"] += 1
                
                # 显示验证结果
                issues = []
                if result["hardcode_issues"] > 0:
                    issues.append(f"硬编码 {result['hardcode_issues']} 处")
                if result["bypass_patterns"] > 0:
                    issues.append(f"绕过模式 {result['bypass_patterns']} 处")
                if result["security_issues"] > 0:
                    issues.append(f"安全问题 {result['security_issues']} 处")
                if result["performance_issues"] > 0:
                    issues.append(f"性能问题 {result['performance_issues']} 处")
                if result["documentation_issues"] > 0:
                    issues.append(f"文档问题 {result['documentation_issues']} 处")
                
                if issues:
                    print(f"  ⚠️  发现问题: {', '.join(issues)}")
                else:
                    print(f"  ✅ 验证通过")
            
            results["total_files_checked"] += 1
        
        return results
    
    def calculate_health_score(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """计算系统健康分数"""
        total_files = results["total_files_checked"]
        valid_files = results["valid_files"]
        
        # 基础分数
        base_score = (valid_files / total_files) * 100 if total_files > 0 else 0
        
        # 硬编码优化分数
        hardcode_score = max(0, 100 - (results["total_hardcode_issues"] / total_files) * 10) if total_files > 0 else 100
        
        # 绕过模式修复分数
        bypass_score = max(0, 100 - (results["total_bypass_patterns"] / total_files) * 10) if total_files > 0 else 100
        
        # 安全分数
        security_score = max(0, 100 - (results["total_security_issues"] / total_files) * 20) if total_files > 0 else 100
        
        # 性能分数
        performance_score = max(0, 100 - (results["total_performance_issues"] / total_files) * 5) if total_files > 0 else 100
        
        # 文档分数
        documentation_score = max(0, 100 - (results["total_documentation_issues"] / total_files) * 2) if total_files > 0 else 100
        
        # 统一中心系统使用分数
        unified_center_score = (results["files_with_unified_centers"] / total_files) * 100 if total_files > 0 else 0
        
        # 智能配置使用分数
        smart_config_score = (results["files_with_smart_config"] / total_files) * 100 if total_files > 0 else 0
        
        # 综合健康分数
        overall_score = (
            base_score * 0.1 +
            hardcode_score * 0.15 +
            bypass_score * 0.15 +
            security_score * 0.2 +
            performance_score * 0.15 +
            documentation_score * 0.1 +
            unified_center_score * 0.1 +
            smart_config_score * 0.05
        )
        
        return {
            "overall_score": round(overall_score, 2),
            "base_score": round(base_score, 2),
            "hardcode_score": round(hardcode_score, 2),
            "bypass_score": round(bypass_score, 2),
            "security_score": round(security_score, 2),
            "performance_score": round(performance_score, 2),
            "documentation_score": round(documentation_score, 2),
            "unified_center_score": round(unified_center_score, 2),
            "smart_config_score": round(smart_config_score, 2)
        }
    
    def run_validation(self):
        """运行系统健康验证"""
        print("🚀 开始系统健康验证")
        print("=" * 60)
        
        # 获取需要验证的文件列表
        target_files = self._get_target_files()
        print(f"📋 发现 {len(target_files)} 个文件需要验证")
        
        # 批量验证
        results = self.batch_validate_system(target_files)
        
        # 计算健康分数
        health_scores = self.calculate_health_score(results)
        
        # 输出结果
        print("\n📊 系统健康验证结果:")
        print(f"  检查文件: {results['total_files_checked']}")
        print(f"  有效文件: {results['valid_files']}")
        print(f"  硬编码问题: {results['total_hardcode_issues']} 处")
        print(f"  绕过模式: {results['total_bypass_patterns']} 处")
        print(f"  安全问题: {results['total_security_issues']} 处")
        print(f"  性能问题: {results['total_performance_issues']} 处")
        print(f"  文档问题: {results['total_documentation_issues']} 处")
        print(f"  使用统一中心: {results['files_with_unified_centers']} 个文件")
        print(f"  使用智能配置: {results['files_with_smart_config']} 个文件")
        
        print("\n🎯 系统健康分数:")
        print(f"  综合健康分数: {health_scores['overall_score']}/100")
        print(f"  基础分数: {health_scores['base_score']}/100")
        print(f"  硬编码优化分数: {health_scores['hardcode_score']}/100")
        print(f"  绕过模式修复分数: {health_scores['bypass_score']}/100")
        print(f"  安全分数: {health_scores['security_score']}/100")
        print(f"  性能分数: {health_scores['performance_score']}/100")
        print(f"  文档分数: {health_scores['documentation_score']}/100")
        print(f"  统一中心使用分数: {health_scores['unified_center_score']}/100")
        print(f"  智能配置使用分数: {health_scores['smart_config_score']}/100")
        
        # 健康等级评估
        overall_score = health_scores['overall_score']
        if overall_score >= 95:
            health_level = "🏆 优秀"
        elif overall_score >= 90:
            health_level = "🥇 良好"
        elif overall_score >= 80:
            health_level = "🥈 中等"
        elif overall_score >= 70:
            health_level = "🥉 及格"
        else:
            health_level = "❌ 需要改进"
        
        print(f"\n🏥 系统健康等级: {health_level}")
        
        if results["errors"]:
            print(f"\n❌ 错误: {len(results['errors'])} 个")
            for error in results["errors"][:5]:  # 只显示前5个错误
                print(f"  - {error}")
        
        print("\n✅ 系统健康验证完成!")
        
        return results, health_scores
    
    def _get_target_files(self) -> List[str]:
        """获取需要验证的目标文件"""
        target_files = []
        
        # 搜索Python文件
        for root, dirs, files in os.walk("src"):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    target_files.append(file_path)
        
        return target_files

if __name__ == "__main__":
    validator = SystemHealthValidator()
    validator.run_validation()
