#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心系统使用情况分析
分析系统是否在核心系统之外使用其他能力
"""

import os
import re
import json
import logging
from typing import Dict, List, Any, Set
from pathlib import Path

logger = logging.getLogger(__name__)

class CoreSystemUsageAnalyzer:
    """核心系统使用情况分析器"""
    
    def __init__(self):
        self.analysis_results = {
            "core_system_usage": {},
            "external_capabilities": {},
            "bypass_patterns": {},
            "hardcode_issues": {},
            "recommendations": []
        }
    
    def analyze_core_system_usage(self) -> Dict[str, Any]:
        """分析核心系统使用情况"""
        print("🔍 开始分析核心系统使用情况...")
        print("=" * 60)
        
        # 分析统一中心系统使用情况
        self._analyze_unified_centers()
        
        # 分析外部能力使用情况
        self._analyze_external_capabilities()
        
        # 分析绕过模式
        self._analyze_bypass_patterns()
        
        # 分析硬编码问题
        self._analyze_hardcode_issues()
        
        # 生成建议
        self._generate_recommendations()
        
        return self.analysis_results
    
    def _analyze_unified_centers(self):
        """分析统一中心系统使用情况"""
        print("\n📊 分析统一中心系统使用情况...")
        
        # 统一中心系统列表
        unified_centers = [
            "unified_intelligent_center",
            "unified_data_center", 
            "unified_security_center",
            "unified_monitoring_center",
            "unified_cache_center",
            "unified_scheduler_center",
            "unified_integration_center",
            "unified_identity_center",
            "unified_logging_center",
            "unified_answer_center",
            "unified_learning_center",
            "unified_smart_config"
        ]
        
        center_usage = {}
        for center in unified_centers:
            usage_count = self._count_center_usage(center)
            center_usage[center] = {
                "usage_count": usage_count,
                "status": "active" if usage_count > 0 else "inactive"
            }
        
        self.analysis_results["core_system_usage"] = center_usage
        
        # 输出统计
        active_centers = sum(1 for center in center_usage.values() if center["status"] == "active")
        total_centers = len(unified_centers)
        
        print(f"  ✅ 活跃中心: {active_centers}/{total_centers}")
        print(f"  📈 使用率: {active_centers/total_centers*100:.1f}%")
        
        for center, info in center_usage.items():
            status_icon = "✅" if info["status"] == "active" else "❌"
            print(f"    {status_icon} {center}: {info['usage_count']} 次使用")
    
    def _count_center_usage(self, center_name: str) -> int:
        """统计中心使用次数"""
        usage_count = 0
        
        # 搜索导入语句
        import_patterns = [
            f"from.*{center_name}.*import",
            f"import.*{center_name}",
            f"get_{center_name}",
            f"create_{center_name}"
        ]
        
        for pattern in import_patterns:
            try:
                # 使用grep搜索
                import subprocess
                result = subprocess.run(
                    ["grep", "-r", "-l", pattern, "src/"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    files = result.stdout.strip().split('\n')
                    usage_count += len(files)
            except:
                pass
        
        return usage_count
    
    def _analyze_external_capabilities(self):
        """分析外部能力使用情况"""
        print("\n🌐 分析外部能力使用情况...")
        
        external_capabilities = {
            "direct_api_calls": self._find_direct_api_calls(),
            "external_services": self._find_external_services(),
            "hardcoded_urls": self._find_hardcoded_urls(),
            "external_dependencies": self._find_external_dependencies()
        }
        
        self.analysis_results["external_capabilities"] = external_capabilities
        
        # 输出统计
        total_external = sum(len(capabilities) for capabilities in external_capabilities.values())
        print(f"  🔍 发现外部能力使用: {total_external} 处")
        
        for category, capabilities in external_capabilities.items():
            if capabilities:
                print(f"    📋 {category}: {len(capabilities)} 处")
                for capability in capabilities[:3]:  # 只显示前3个
                    print(f"      - {capability}")
    
    def _find_direct_api_calls(self) -> List[str]:
        """查找直接API调用"""
        api_patterns = [
            r"requests\.(get|post|put|delete)",
            r"aiohttp\.(get|post|put|delete)",
            r"urllib\.request",
            r"httpx\.(get|post|put|delete)",
            r"fetch\(",
            r"axios\."
        ]
        
        found_calls = []
        for pattern in api_patterns:
            try:
                import subprocess
                result = subprocess.run(
                    ["grep", "-r", "-n", pattern, "src/"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    found_calls.extend(lines)
            except:
                pass
        
        return found_calls
    
    def _find_external_services(self) -> List[str]:
        """查找外部服务调用"""
        service_patterns = [
            r"openai\.",
            r"anthropic\.",
            r"deepseek\.",
            r"jina\.",
            r"faiss\.",
            r"huggingface\.",
            r"transformers\."
        ]
        
        found_services = []
        for pattern in service_patterns:
            try:
                import subprocess
                result = subprocess.run(
                    ["grep", "-r", "-n", pattern, "src/"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    found_services.extend(lines)
            except:
                pass
        
        return found_services
    
    def _find_hardcoded_urls(self) -> List[str]:
        """查找硬编码URL"""
        url_patterns = [
            r"https?://[^\s\"']+",
            r"api\.[a-zA-Z0-9.-]+",
            r"localhost:\d+",
            r"127\.0\.0\.1:\d+"
        ]
        
        found_urls = []
        for pattern in url_patterns:
            try:
                import subprocess
                result = subprocess.run(
                    ["grep", "-r", "-n", pattern, "src/"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    found_urls.extend(lines)
            except:
                pass
        
        return found_urls
    
    def _find_external_dependencies(self) -> List[str]:
        """查找外部依赖"""
        dependency_patterns = [
            r"import\s+[a-zA-Z_][a-zA-Z0-9_]*",
            r"from\s+[a-zA-Z_][a-zA-Z0-9_]*\s+import"
        ]
        
        found_dependencies = []
        for pattern in dependency_patterns:
            try:
                import subprocess
                result = subprocess.run(
                    ["grep", "-r", "-n", pattern, "src/"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    # 过滤掉内部模块
                    external_lines = [
                        line for line in lines 
                        if not any(center in line for center in [
                            "src.", "unified_", "enhanced_", "intelligent_"
                        ])
                    ]
                    found_dependencies.extend(external_lines)
            except:
                pass
        
        return found_dependencies
    
    def _analyze_bypass_patterns(self):
        """分析绕过统一中心系统的模式"""
        print("\n🚫 分析绕过模式...")
        
        bypass_patterns = {
            "direct_function_calls": self._find_direct_function_calls(),
            "hardcoded_configs": self._find_hardcoded_configs(),
            "bypass_validation": self._find_bypass_validation(),
            "direct_imports": self._find_direct_imports()
        }
        
        self.analysis_results["bypass_patterns"] = bypass_patterns
        
        # 输出统计
        total_bypasses = sum(len(patterns) for patterns in bypass_patterns.values())
        print(f"  ⚠️ 发现绕过模式: {total_bypasses} 处")
        
        for category, patterns in bypass_patterns.items():
            if patterns:
                print(f"    📋 {category}: {len(patterns)} 处")
                for pattern in patterns[:3]:  # 只显示前3个
                    print(f"      - {pattern}")
    
    def _find_direct_function_calls(self) -> List[str]:
        """查找直接函数调用"""
        direct_call_patterns = [
            r"def\s+\w+\(.*\):",
            r"class\s+\w+:",
            r"\.\w+\(.*\)"
        ]
        
        found_calls = []
        for pattern in direct_call_patterns:
            try:
                import subprocess
                result = subprocess.run(
                    ["grep", "-r", "-n", pattern, "src/"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    found_calls.extend(lines)
            except:
                pass
        
        return found_calls
    
    def _find_hardcoded_configs(self) -> List[str]:
        """查找硬编码配置"""
        config_patterns = [
            r"=\s*\d+",
            r"=\s*['\"][^'\"]+['\"]",
            r"timeout\s*=",
            r"max_\w+\s*=",
            r"threshold\s*="
        ]
        
        found_configs = []
        for pattern in config_patterns:
            try:
                import subprocess
                result = subprocess.run(
                    ["grep", "-r", "-n", pattern, "src/"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    found_configs.extend(lines)
            except:
                pass
        
        return found_configs
    
    def _find_bypass_validation(self) -> List[str]:
        """查找绕过验证的模式"""
        bypass_patterns = [
            r"#\s*TODO.*bypass",
            r"#\s*FIXME.*bypass",
            r"#\s*HACK.*bypass",
            r"#\s*绕过",
            r"#\s*跳过"
        ]
        
        found_bypasses = []
        for pattern in bypass_patterns:
            try:
                import subprocess
                result = subprocess.run(
                    ["grep", "-r", "-n", pattern, "src/"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    found_bypasses.extend(lines)
            except:
                pass
        
        return found_bypasses
    
    def _find_direct_imports(self) -> List[str]:
        """查找直接导入"""
        import_patterns = [
            r"from\s+src\.",
            r"import\s+src\.",
            r"from\s+\.\w+",
            r"import\s+\.\w+"
        ]
        
        found_imports = []
        for pattern in import_patterns:
            try:
                import subprocess
                result = subprocess.run(
                    ["grep", "-r", "-n", pattern, "src/"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    found_imports.extend(lines)
            except:
                pass
        
        return found_imports
    
    def _analyze_hardcode_issues(self):
        """分析硬编码问题"""
        print("\n🔧 分析硬编码问题...")
        
        hardcode_issues = {
            "hardcoded_values": self._find_hardcoded_values(),
            "hardcoded_strings": self._find_hardcoded_strings(),
            "hardcoded_numbers": self._find_hardcoded_numbers(),
            "hardcoded_urls": self._find_hardcoded_urls()
        }
        
        self.analysis_results["hardcode_issues"] = hardcode_issues
        
        # 输出统计
        total_hardcodes = sum(len(issues) for issues in hardcode_issues.values())
        print(f"  🔧 发现硬编码问题: {total_hardcodes} 处")
        
        for category, issues in hardcode_issues.items():
            if issues:
                print(f"    📋 {category}: {len(issues)} 处")
                for issue in issues[:3]:  # 只显示前3个
                    print(f"      - {issue}")
    
    def _find_hardcoded_values(self) -> List[str]:
        """查找硬编码值"""
        value_patterns = [
            r"=\s*\d+",
            r"=\s*['\"][^'\"]+['\"]",
            r"=\s*True",
            r"=\s*False",
            r"=\s*None"
        ]
        
        found_values = []
        for pattern in value_patterns:
            try:
                import subprocess
                result = subprocess.run(
                    ["grep", "-r", "-n", pattern, "src/"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    found_values.extend(lines)
            except:
                pass
        
        return found_values
    
    def _find_hardcoded_strings(self) -> List[str]:
        """查找硬编码字符串"""
        string_patterns = [
            r"['\"][^'\"]{10,}['\"]",
            r"['\"][^'\"]*[a-zA-Z]{3,}[^'\"]*['\"]"
        ]
        
        found_strings = []
        for pattern in string_patterns:
            try:
                import subprocess
                result = subprocess.run(
                    ["grep", "-r", "-n", pattern, "src/"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    found_strings.extend(lines)
            except:
                pass
        
        return found_strings
    
    def _find_hardcoded_numbers(self) -> List[str]:
        """查找硬编码数字"""
        number_patterns = [
            r"=\s*\d+",
            r"timeout\s*=\s*\d+",
            r"max_\w+\s*=\s*\d+",
            r"threshold\s*=\s*\d+"
        ]
        
        found_numbers = []
        for pattern in number_patterns:
            try:
                import subprocess
                result = subprocess.run(
                    ["grep", "-r", "-n", pattern, "src/"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    found_numbers.extend(lines)
            except:
                pass
        
        return found_numbers
    
    def _generate_recommendations(self):
        """生成改进建议"""
        print("\n💡 生成改进建议...")
        
        recommendations = []
        
        # 基于分析结果生成建议
        if self.analysis_results["external_capabilities"]["direct_api_calls"]:
            recommendations.append({
                "category": "外部API调用",
                "issue": "发现直接API调用",
                "recommendation": "建议通过统一中心系统管理所有外部API调用",
                "priority": "high"
            })
        
        if self.analysis_results["bypass_patterns"]["hardcoded_configs"]:
            recommendations.append({
                "category": "硬编码配置",
                "issue": "发现硬编码配置值",
                "recommendation": "建议使用智能配置系统管理所有配置",
                "priority": "medium"
            })
        
        if self.analysis_results["hardcode_issues"]["hardcoded_values"]:
            recommendations.append({
                "category": "硬编码值",
                "issue": "发现硬编码值",
                "recommendation": "建议使用动态配置和智能参数管理",
                "priority": "medium"
            })
        
        # 添加通用建议
        recommendations.extend([
            {
                "category": "架构优化",
                "issue": "统一中心系统使用率",
                "recommendation": "提高统一中心系统的使用率，减少直接调用",
                "priority": "high"
            },
            {
                "category": "代码质量",
                "issue": "代码一致性",
                "recommendation": "确保所有功能都通过统一中心系统访问",
                "priority": "medium"
            }
        ])
        
        self.analysis_results["recommendations"] = recommendations
        
        # 输出建议
        print(f"  💡 生成建议: {len(recommendations)} 条")
        for i, rec in enumerate(recommendations, 1):
            priority_icon = "🔴" if rec["priority"] == "high" else "🟡" if rec["priority"] == "medium" else "🟢"
            print(f"    {i}. {priority_icon} {rec['category']}: {rec['recommendation']}")
    
    def print_summary(self):
        """打印分析摘要"""
        print("\n📊 核心系统使用情况分析摘要")
        print("=" * 60)
        
        # 统一中心系统使用情况
        core_usage = self.analysis_results["core_system_usage"]
        active_centers = sum(1 for center in core_usage.values() if center["status"] == "active")
        total_centers = len(core_usage)
        
        print(f"🏗️ 统一中心系统:")
        print(f"  - 活跃中心: {active_centers}/{total_centers} ({active_centers/total_centers*100:.1f}%)")
        print(f"  - 使用率: {'优秀' if active_centers/total_centers > 0.8 else '良好' if active_centers/total_centers > 0.6 else '需要改进'}")
        
        # 外部能力使用情况
        external_caps = self.analysis_results["external_capabilities"]
        total_external = sum(len(capabilities) for capabilities in external_caps.values())
        
        print(f"\n🌐 外部能力使用:")
        print(f"  - 外部调用: {total_external} 处")
        print(f"  - 风险等级: {'高' if total_external > 50 else '中' if total_external > 20 else '低'}")
        
        # 绕过模式
        bypass_patterns = self.analysis_results["bypass_patterns"]
        total_bypasses = sum(len(patterns) for patterns in bypass_patterns.values())
        
        print(f"\n🚫 绕过模式:")
        print(f"  - 绕过次数: {total_bypasses} 处")
        print(f"  - 合规性: {'需要改进' if total_bypasses > 30 else '良好' if total_bypasses > 10 else '优秀'}")
        
        # 硬编码问题
        hardcode_issues = self.analysis_results["hardcode_issues"]
        total_hardcodes = sum(len(issues) for issues in hardcode_issues.values())
        
        print(f"\n🔧 硬编码问题:")
        print(f"  - 硬编码数量: {total_hardcodes} 处")
        print(f"  - 动态化程度: {'需要改进' if total_hardcodes > 100 else '良好' if total_hardcodes > 50 else '优秀'}")
        
        # 总体评估
        print(f"\n🎯 总体评估:")
        if active_centers/total_centers > 0.8 and total_external < 20 and total_bypasses < 10 and total_hardcodes < 50:
            print("  ✅ 优秀 - 系统高度统一，外部依赖较少")
        elif active_centers/total_centers > 0.6 and total_external < 50 and total_bypasses < 30 and total_hardcodes < 100:
            print("  ✅ 良好 - 系统基本统一，需要进一步优化")
        else:
            print("  ⚠️ 需要改进 - 系统统一性不足，需要重构")

if __name__ == "__main__":
    analyzer = CoreSystemUsageAnalyzer()
    results = analyzer.analyze_core_system_usage()
    analyzer.print_summary()
    
    # 保存结果
    with open('core_system_usage_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 分析结果已保存到: core_system_usage_analysis.json")
