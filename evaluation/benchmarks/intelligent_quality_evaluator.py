#!/usr/bin/env python3
"""
智能质量分析系统 - 修复版本
"""

import os
import sys
import ast
import re
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 添加分析器目录到路径
analyzers_path = os.path.join(os.path.dirname(__file__), 'analyzers')
sys.path.insert(0, analyzers_path)

from evaluation.benchmarks.analyzers.basic_quality_analyzer import BasicQualityAnalyzer
from evaluation.benchmarks.analyzers.ml_rl_synergy_analyzer import MLRLSynergyAnalyzer
from evaluation.benchmarks.analyzers.prompt_context_synergy_analyzer import PromptContextSynergyAnalyzer
from evaluation.benchmarks.analyzers.complex_reasoning_analyzer import ComplexReasoningAnalyzer
from evaluation.benchmarks.analyzers.query_processing_analyzer import QueryProcessingAnalyzer
from evaluation.benchmarks.analyzers.intelligence_dimensions_analyzer import IntelligenceDimensionsAnalyzer
from evaluation.benchmarks.analyzers.context_management_analyzer import ContextManagementAnalyzer
from evaluation.benchmarks.analyzers.system_monitoring_analyzer import SystemMonitoringAnalyzer
from evaluation.benchmarks.analyzers.config_management_analyzer import ConfigManagementAnalyzer
from evaluation.benchmarks.analyzers.scoring_evaluation_analyzer import ScoringEvaluationAnalyzer
from evaluation.benchmarks.analyzers.security_protection_analyzer import SecurityProtectionAnalyzer
from evaluation.benchmarks.analyzers.system_integration_analyzer import SystemIntegrationAnalyzer
from evaluation.benchmarks.analyzers.data_management_analyzer import DataManagementAnalyzer
from evaluation.benchmarks.analyzers.hardcoded_data_analyzer import HardcodedDataAnalyzer
from evaluation.benchmarks.analyzers.learning_capability_analyzer import LearningCapabilityAnalyzer
from evaluation.benchmarks.analyzers.business_logic_analyzer import BusinessLogicAnalyzer
from evaluation.benchmarks.analyzers.over_design_analyzer import OverDesignAnalyzer
from evaluation.benchmarks.analyzers.performance_analyzer import PerformanceAnalyzer
from evaluation.benchmarks.analyzers.architecture_analyzer import ArchitectureAnalyzer
from evaluation.benchmarks.analyzers.unimplemented_method_analyzer import UnimplementedMethodAnalyzer
from evaluation.benchmarks.analyzers.brain_decision_mechanism_analyzer import BrainDecisionMechanismAnalyzer
from evaluation.benchmarks.analyzers.duplicate_code_analyzer import DuplicateCodeAnalyzer
from evaluation.benchmarks.analyzers.enhanced_hardcoded_data_analyzer import EnhancedHardcodedDataAnalyzer
from evaluation.benchmarks.analyzers.improved_hardcoded_data_analyzer import ImprovedHardcodedDataAnalyzer
from evaluation.benchmarks.analyzers.architectural_hardcoding_analyzer import ArchitecturalHardcodingAnalyzer
from evaluation.benchmarks.analyzers.progressive_over_design_analyzer import ProgressiveOverDesignAnalyzer

# 暂时移除SourceCodeAnalyzer依赖


class SourceCodeAnalyzer:
    """源码分析器 - 基于静态分析的智能质量检测"""

    def __init__(self, source_path: str = "src"):
        self.source_path = source_path
        self.logger = logging.getLogger(__name__)
        self.python_files = self._collect_python_files()

    def _collect_python_files(self) -> List[str]:
        """收集核心系统的Python源码文件"""
        python_files = []
        try:
            # 分析src目录下的所有Python文件
            # 智能检测src目录位置：支持从根目录或evaluation目录运行
            src_dir = self.source_path
            if not os.path.exists(src_dir):
                src_dir = '../src'  # 如果在evaluation目录中运行
            if not os.path.exists(src_dir):
                src_dir = '../../src'  # 如果在evaluation/benchmarks目录中运行
            
            if os.path.exists(src_dir):
                for root, dirs, files in os.walk(src_dir):
                    # 排除测试和缓存目录
                    dirs[:] = [d for d in dirs if not d.startswith('__pycache__') and d != 'test']
                    for file in files:
                        if (file.endswith('.py') and not file.startswith('__') 
                            and not file.endswith('.backup') and 'backup' not in file.lower()):
                            python_files.append(os.path.join(root, file))
                self.logger.info(f"成功扫描到 {len(python_files)} 个Python文件")
            else:
                self.logger.error(f"未找到src目录: {src_dir}")
        except Exception as e:
            self.logger.error(f"收集核心系统Python文件失败: {e}")
        return python_files

    def analyze_advanced_issues(self) -> Dict[str, Any]:
        """分析高级问题"""
        self.logger.info("开始高级问题分析...")
        
        total_issues = 0
        issue_types = {}
        file_issues = {}
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                issues = self._detect_advanced_issues(file_path, content)
                if issues:
                    file_issues[file_path] = issues
                    total_issues += len(issues)
                    
                    for issue in issues:
                        issue_type = issue['type']
                        issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
                        
            except Exception as e:
                self.logger.error(f"分析文件失败 {file_path}: {e}")
        
        return {
            'total_issues': total_issues,
            'issue_types': issue_types,
            'file_issues': file_issues,
            'analysis_time': datetime.now().isoformat()
        }

    def _detect_advanced_issues(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """检测高级问题"""
        issues = []
        
        try:
            # 检测语法错误
            try:
                ast.parse(content)
            except SyntaxError as e:
                issues.append({
                    'type': 'syntax_error',
                    'line': e.lineno or 0,
                    'message': f"语法错误: {e.msg}",
                    'severity': 'high'
                })
            
            # 检测其他高级问题
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                # 检测潜在的性能问题
                if 'for ' in line and ' in ' in line and 'range(' in line:
                    if 'len(' in line:
                        issues.append({
                            'type': 'performance',
                            'line': i,
                            'message': "发现'value'模式错误",
                            'severity': 'medium'
                        })
                
                # 检测其他问题...
                
        except Exception as e:
            self.logger.error(f"检测高级问题失败 {file_path}: {e}")
        
        return issues


class IntelligentQualityAnalyzer:
    """智能质量分析器 - 修复版本"""
    
    def __init__(self, source_path: str = "src", use_progressive: bool = False, max_files: Optional[int] = None):
        self.source_path = source_path
        self.use_progressive = use_progressive
        self.max_files = max_files
        self.logger = logging.getLogger(__name__)
        
        # 收集Python文件
        self.python_files = self._collect_python_files()
        total_files = len(self.python_files)
        if self.max_files and total_files > self.max_files:
            import random
            random.seed(42)  # 固定随机种子以保证可重复性
            self.python_files = random.sample(self.python_files, self.max_files)
            self.logger.info(f"从 {total_files} 个文件中随机采样 {len(self.python_files)} 个文件进行评测")
        else:
            self.logger.info(f"成功扫描到 {len(self.python_files)} 个Python文件")
        
        # 初始化分析器 - 支持更多维度
        self.analyzers = {
            "basic_quality": BasicQualityAnalyzer(self.python_files),
            "ml_rl_synergy": MLRLSynergyAnalyzer(self.python_files),
            "prompt_context_synergy": PromptContextSynergyAnalyzer(self.python_files),
            "complex_reasoning": ComplexReasoningAnalyzer(self.python_files),
            "query_processing": QueryProcessingAnalyzer(self.python_files),
            "intelligence_dimensions": IntelligenceDimensionsAnalyzer(self.python_files),
            "context_management": ContextManagementAnalyzer(self.python_files),
            "system_monitoring": SystemMonitoringAnalyzer(self.python_files),
            "config_management": ConfigManagementAnalyzer(self.python_files),
            "scoring_evaluation": ScoringEvaluationAnalyzer(self.python_files),
            "security_protection": SecurityProtectionAnalyzer(self.python_files),
            "system_integration": SystemIntegrationAnalyzer(self.python_files),
            "data_management": DataManagementAnalyzer(self.python_files),
            "hardcoded_data": HardcodedDataAnalyzer(self.python_files),
            "learning_capability": LearningCapabilityAnalyzer(self.python_files),
            "business_logic": BusinessLogicAnalyzer(self.python_files),
            "over_design": OverDesignAnalyzer(self.python_files),
            "performance": PerformanceAnalyzer(self.python_files),
            "architecture": ArchitectureAnalyzer(self.python_files),
            "unimplemented_methods": UnimplementedMethodAnalyzer(self.python_files),
            "brain_decision_mechanism": BrainDecisionMechanismAnalyzer(self.python_files),
            "duplicate_code": DuplicateCodeAnalyzer(self.python_files),
            "enhanced_hardcoded_data": EnhancedHardcodedDataAnalyzer(self.python_files),
            "improved_hardcoded_data": ImprovedHardcodedDataAnalyzer(self.python_files),
            "architectural_hardcoding": ArchitecturalHardcodingAnalyzer(self.python_files),
            "progressive_over_design": ProgressiveOverDesignAnalyzer(self.python_files)
        }
        
        self.logger.info("评估系统初始化成功")
    
    def _collect_python_files(self) -> List[str]:
        """收集核心系统的Python源码文件"""
        python_files = []
        for root, dirs, files in os.walk(self.source_path):
            # 跳过__pycache__目录
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        return python_files
    
    def _generate_comprehensive_analysis_data(self):
        """生成综合分析数据（不打印到控制台）"""
        try:
            # 收集所有分析器的结果
            results = {}
            
            # 基础质量分析
            results['basic_quality'] = self.analyzers["basic_quality"].analyze()
            
            # ML和RL协同作用分析
            results['ml_rl_synergy'] = self.analyzers["ml_rl_synergy"].analyze()
            
            # 提示词和上下文协同作用分析
            results['prompt_context_synergy'] = self.analyzers["prompt_context_synergy"].analyze()
            
            # 复杂逻辑推理能力分析
            results['complex_reasoning'] = self.analyzers["complex_reasoning"].analyze()
            
            # 大脑决策机制分析
            try:
                brain_result = self.analyzers["brain_decision_mechanism"].analyze()
                results['brain_decision_mechanism'] = brain_result
            except Exception as e:
                print(f"大脑决策机制分析失败: {e}")
                results['brain_decision_mechanism'] = {"score": 0.0, "error": str(e)}
            
            # 查询处理流程分析
            results['query_processing'] = self.analyzers["query_processing"].analyze()
            
            # 智能程度维度分析
            results['intelligence_dimensions'] = self.analyzers["intelligence_dimensions"].analyze()
            
            # 上下文管理能力分析
            results['context_management'] = self.analyzers["context_management"].analyze()
            
            # 系统监控能力分析
            results['system_monitoring'] = self.analyzers["system_monitoring"].analyze()
            
            # 配置管理能力分析
            results['config_management'] = self.analyzers["config_management"].analyze()
            
            # 评分评估能力分析
            results['scoring_evaluation'] = self.analyzers["scoring_evaluation"].analyze()
            
            # 安全防护能力分析
            results['security_protection'] = self.analyzers["security_protection"].analyze()
            
            # 系统集成能力分析
            results['system_integration'] = self.analyzers["system_integration"].analyze()
            
            # 数据管理能力分析
            results['data_management'] = self.analyzers["data_management"].analyze()
            
            # 硬编码数据检测分析
            results['hardcoded_data'] = self.analyzers["hardcoded_data"].analyze()
            
            # 学习能力分析
            results['learning_capability'] = self.analyzers["learning_capability"].analyze()
            
            # 业务逻辑分析
            results['business_logic'] = self.analyzers["business_logic"].analyze()
            
            # 过度设计检测分析
            results['over_design'] = self.analyzers["over_design"].analyze()
            
            # 性能问题检测分析
            results['performance'] = self.analyzers["performance"].analyze()
            
            # 架构问题检测分析
            results['architecture'] = self.analyzers["architecture"].analyze()
            
            # 未实现方法检测分析
            results['unimplemented_methods'] = self.analyzers["unimplemented_methods"].analyze()
            
            # 重复代码检测分析
            results['duplicate_code'] = self.analyzers["duplicate_code"].analyze()
            
            # 增强硬编码数据检测分析
            results['enhanced_hardcoded_data'] = self.analyzers["enhanced_hardcoded_data"].analyze()
            
            # 改进硬编码数据检测分析
            results['improved_hardcoded_data'] = self.analyzers["improved_hardcoded_data"].analyze()
            
            # 架构硬编码检测分析
            results['architectural_hardcoding'] = self.analyzers["architectural_hardcoding"].analyze()
            
            # 渐进式过度设计检测分析
            results['progressive_over_design'] = self.analyzers["progressive_over_design"].analyze()
            
            return results
            
        except Exception as e:
            self.logger.error(f"生成分析数据失败: {e}")
            return {}
    
    def generate_and_display_report(self):
        """生成并显示详细的质量分析报告"""
        self.logger.info("开始生成详细质量分析报告...")

        # 保存Markdown报告到指定目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("comprehensive_eval_results", exist_ok=True)
        markdown_file = "comprehensive_eval_results/intelligent_quality_analysis_report.md"
        
        try:
            # 生成详细报告 - 使用模块化分析器（不打印到控制台）
            analysis_results = self._generate_comprehensive_analysis_data()
            
            # 添加高级问题检测
            source_analyzer = SourceCodeAnalyzer(self.source_path)
            advanced_issues = source_analyzer.analyze_advanced_issues()
            
            # 在报告中添加高级问题信息
            self._add_advanced_issues_to_report(advanced_issues)

            # 生成详细的Markdown报告
            report_content = self._generate_detailed_markdown_report(timestamp, analysis_results)
            
            with open(markdown_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            print(f"\n📊 详细质量分析报告已保存到: {markdown_file}")
            
        except Exception as e:
            self.logger.error(f"生成报告时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def _add_advanced_issues_to_report(self, advanced_issues: Dict[str, Any]):
        """将高级问题添加到报告中"""
        if advanced_issues['total_issues'] > 0:
            self.logger.warning(f"发现 {advanced_issues['total_issues']} 个高级问题")
    
    def _safe_sum_dict_values(self, data_dict: dict) -> float:
        """安全地计算字典中数值的总和"""
        if not data_dict:
            return 0.0
        try:
            # 只对数值类型求和
            numeric_values = [v for v in data_dict.values() if isinstance(v, (int, float))]
            return sum(numeric_values) / len(numeric_values) if numeric_values else 0.0
        except Exception:
            return 0.0

    def _generate_detailed_markdown_report(self, timestamp: str, analysis_results: Optional[dict] = None) -> str:
        """生成详细的Markdown报告"""
        try:
            # 使用传入的分析结果，避免重复运行分析器
            if analysis_results:
                basic_quality = analysis_results.get("basic_quality", {})
                ml_rl_synergy = analysis_results.get("ml_rl_synergy", {})
                prompt_context_synergy = analysis_results.get("prompt_context_synergy", {})
                complex_reasoning = analysis_results.get("complex_reasoning", {})
                query_processing = analysis_results.get("query_processing", {})
                intelligence_dimensions = analysis_results.get("intelligence_dimensions", {})
                context_management = analysis_results.get("context_management", {})
                system_monitoring = analysis_results.get("system_monitoring", {})
                config_management = analysis_results.get("config_management", {})
                scoring_evaluation = analysis_results.get("scoring_evaluation", {})
                security_protection = analysis_results.get("security_protection", {})
                system_integration = analysis_results.get("system_integration", {})
                data_management = analysis_results.get("data_management", {})
                hardcoded_data = analysis_results.get("hardcoded_data", {})
                learning_capability = analysis_results.get("learning_capability", {})
                business_logic = analysis_results.get("business_logic", {})
                over_design = analysis_results.get("over_design", {})
                performance = analysis_results.get("performance", {})
                architecture = analysis_results.get("architecture", {})
                unimplemented_methods = analysis_results.get("unimplemented_methods", {})
                brain_decision_mechanism = analysis_results.get("brain_decision_mechanism", {})
                
            else:
                # 如果没有传入分析结果，则使用默认值
                basic_quality = {}
                ml_rl_synergy = {}
                prompt_context_synergy = {}
                complex_reasoning = {}
                query_processing = {}
                intelligence_dimensions = {}
                context_management = {}
                system_monitoring = {}
                config_management = {}
                scoring_evaluation = {}
                security_protection = {}
                system_integration = {}
                data_management = {}
                hardcoded_data = {}
                learning_capability = {}
                business_logic = {}
                over_design = {}
                performance = {}
                architecture = {}
                unimplemented_methods = {}
                brain_decision_mechanism = {}
            
            # 安全获取数值的辅助函数
            def safe_get_float(data, key, default=0.0):
                if isinstance(data, dict):
                    value = data.get(key, default)
                    return float(value) if isinstance(value, (int, float)) else default
                return default
            
            # 生成报告内容
            report_content = f"""# 🧠 RANGEN核心系统智能质量分析报告

**生成时间**: {timestamp}  
**分析模式**: {'渐进式' if self.use_progressive else '快速'}  
**分析文件数**: {len(self.python_files)}

## 📊 基础质量分析

- **智能质量分数**: {safe_get_float(basic_quality, 'intelligence_quality', 0.0):.3f}
- **架构质量分数**: {safe_get_float(basic_quality, 'architecture_quality', 0.0):.3f}
- **安全质量分数**: {safe_get_float(basic_quality, 'security_quality', 0.0):.3f}
- **性能质量分数**: {safe_get_float(basic_quality, 'performance_quality', 0.0):.3f}
- **代码质量分数**: {safe_get_float(basic_quality, 'code_quality', 0.0):.3f}

## 🧠 大脑决策机制分析

- **大脑决策机制分数**: {safe_get_float(brain_decision_mechanism, 'score', 0.0):.3f}
- **nTc机制**: {safe_get_float(brain_decision_mechanism, 'nTc_mechanism', 0.0):.3f}
- **证据积累**: {safe_get_float(brain_decision_mechanism, 'evidence_accumulation', 0.0):.3f}
- **决策承诺**: {safe_get_float(brain_decision_mechanism, 'decision_commitment', 0.0):.3f}
- **几何化轨迹**: {safe_get_float(brain_decision_mechanism, 'geometric_trajectory', 0.0):.3f}
- **动态阈值**: {safe_get_float(brain_decision_mechanism, 'dynamic_threshold', 0.0):.3f}
- **承诺锁定**: {safe_get_float(brain_decision_mechanism, 'commitment_lock', 0.0):.3f}

## 🤖 ML和RL协同作用分析

- **ML-RL协同作用分数**: {safe_get_float(ml_rl_synergy, 'ml_rl_synergy_score', 0.0):.3f}

## 💬 提示词和上下文协同作用分析

- **提示词-上下文协同分数**: {self._safe_sum_dict_values(prompt_context_synergy):.3f}

## 🧠 复杂逻辑推理能力分析

- **复杂推理能力分数**: {self._safe_sum_dict_values(complex_reasoning):.3f}

## 🔍 查询处理流程分析

- **查询处理流程分数**: {self._safe_sum_dict_values(query_processing):.3f}

## 🎯 智能程度维度分析

- **智能维度综合分数**: {safe_get_float(intelligence_dimensions, 'intelligence_dimensions_score', 0.0):.3f}

## 📚 上下文管理能力分析

- **上下文管理分数**: {self._safe_sum_dict_values(context_management):.3f}

## 📊 系统监控能力分析

- **系统监控分数**: {self._safe_sum_dict_values(system_monitoring):.3f}

## ⚙️ 配置管理能力分析

- **配置管理分数**: {self._safe_sum_dict_values(config_management):.3f}

## 📈 评分评估能力分析

- **评分评估分数**: {self._safe_sum_dict_values(scoring_evaluation):.3f}

## 🔒 安全防护能力分析

- **安全防护分数**: {self._safe_sum_dict_values(security_protection):.3f}

## 🔗 系统集成能力分析

- **系统集成分数**: {self._safe_sum_dict_values(system_integration):.3f}

## 💾 数据管理能力分析

- **数据管理分数**: {self._safe_sum_dict_values(data_management):.3f}

## 🔍 硬编码数据检测分析

- **硬编码数据检测分数**: {self._safe_sum_dict_values(hardcoded_data):.3f}

## 🎓 学习能力分析

- **学习能力综合分数**: {safe_get_float(learning_capability, 'learning_capability_score', 0.0):.3f}

## 💼 业务逻辑分析

- **业务价值分数**: {safe_get_float(business_logic, 'business_value_score', 0.0):.3f}

## 🎨 过度设计检测分析

- **过度设计检测分数**: {safe_get_float(over_design, 'over_design_score', 0.0):.3f}

## ⚡ 性能问题检测分析

- **性能问题检测分数**: {safe_get_float(performance, 'performance_score', 0.0):.3f}

## 🏗️ 架构问题检测分析

- **架构问题检测分数**: {safe_get_float(architecture, 'architecture_score', 0.0):.3f}

## 📋 未实现方法检测分析

- **未实现方法检测分数**: {safe_get_float(unimplemented_methods, 'score', 0.0):.3f}
- **检测到的未实现方法数量**: {safe_get_float(unimplemented_methods, 'unimplemented_count', 0):.0f}

---

**报告生成完成** ✅
"""
            
            return report_content
            
        except Exception as e:
            self.logger.error(f"生成详细Markdown报告失败: {e}")
            # 返回基础报告
            basic_quality = self.analyzers["basic_quality"].analyze()
            return f"""# RANGEN核心系统智能质量分析报告

**生成时间**: {timestamp}  
**分析模式**: {'渐进式' if self.use_progressive else '快速'}  
**分析文件数**: {len(self.python_files)}

## 基础质量分析

- **智能质量分数**: {basic_quality.get('intelligence_quality', 0.0):.3f}
- **架构质量分数**: {basic_quality.get('architecture_quality', 0.0):.3f}
- **安全质量分数**: {basic_quality.get('security_quality', 0.0):.3f}
- **性能质量分数**: {basic_quality.get('performance_quality', 0.0):.3f}
- **代码质量分数**: {basic_quality.get('code_quality', 0.0):.3f}

---

**报告生成完成** ✅
"""


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='智能质量分析系统')
    parser.add_argument('--progressive', action='store_true', 
                       help='使用渐进式分析器（更详细但较慢）')
    parser.add_argument('--fast', action='store_true', 
                       help='使用快速分析器（默认）')
    
    args = parser.parse_args()
    
    # 确定分析模式
    use_progressive = args.progressive and not args.fast
    
    logging.basicConfig(level=logging.INFO)
    
    print("开始生成详细质量分析报告...")
    print(f"分析模式: {'渐进式' if use_progressive else '快速'}")

    analyzer = IntelligentQualityAnalyzer(use_progressive=use_progressive)

    # 生成并显示详细的质量分析报告
    analyzer.generate_and_display_report()


if __name__ == "__main__":
    main()
