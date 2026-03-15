#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能解耦系统 - 降低模块耦合度的智能解决方案

本模块提供智能解耦功能，包括：
- 模块依赖分析
- 智能解耦策略
- 接口抽象化
- 依赖注入管理

作者: RANGEN开发团队
版本: 1.0.0
更新时间: 2024
"""

import logging
import ast
import os
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import importlib.util

from src.utils.unified_centers import get_unified_center

logger = logging.getLogger(__name__)

@dataclass
class ModuleDependency:
    """模块依赖信息"""
    module_name: str
    imported_modules: Set[str]
    exported_functions: Set[str]
    exported_classes: Set[str]
    coupling_score: float
    dependencies: List[str] = field(default_factory=list)

@dataclass
class DecouplingStrategy:
    """解耦策略"""
    strategy_type: str
    target_modules: List[str]
    description: str
    implementation: str
    priority: int = 1

class IntelligentDecouplingSystem:
    """智能解耦系统"""
    
    def __init__(self):
        """初始化智能解耦系统"""
        self.context = {"query_type": "decoupling_system"}
        self.module_dependencies: Dict[str, ModuleDependency] = {}
        self.decoupling_strategies: List[DecouplingStrategy] = []
        
        # 初始化智能组件
        self._initialize_intelligent_components()
        
        logger.info("智能解耦系统初始化完成")

    def _initialize_intelligent_components(self):
        """初始化智能组件"""
        try:
            # 使用统一中心系统获取智能分析器
            self.dependency_analyzer = get_unified_center('dependency_analyzer')
            if not self.dependency_analyzer:
                self.dependency_analyzer = self._create_basic_dependency_analyzer()
            
            # 初始化解耦策略生成器
            self.strategy_generator = get_unified_center('strategy_generator')
            if not self.strategy_generator:
                self.strategy_generator = self._create_basic_strategy_generator()
                
        except Exception as e:
            logger.error(f"智能组件初始化失败: {e}")
            self.dependency_analyzer = self._create_basic_dependency_analyzer()
            self.strategy_generator = self._create_basic_strategy_generator()

    def _create_basic_dependency_analyzer(self):
        """创建基础依赖分析器"""
        class BasicDependencyAnalyzer:
            def analyze_module_dependencies(self, file_path: str) -> ModuleDependency:
                """分析模块依赖"""
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    tree = ast.parse(content)
                    
                    imported_modules = set()
                    exported_functions = set()
                    exported_classes = set()
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imported_modules.add(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                imported_modules.add(node.module)
                        elif isinstance(node, ast.FunctionDef):
                            exported_functions.add(node.name)
                        elif isinstance(node, ast.ClassDef):
                            exported_classes.add(node.name)
                    
                    # 计算耦合度分数
                    coupling_score = self._calculate_coupling_score(
                        len(imported_modules), 
                        len(exported_functions), 
                        len(exported_classes)
                    )
                    
                    return ModuleDependency(
                        module_name=os.path.basename(file_path),
                        imported_modules=imported_modules,
                        exported_functions=exported_functions,
                        exported_classes=exported_classes,
                        coupling_score=coupling_score
                    )
                    
                except Exception as e:
                    logger.error(f"依赖分析失败: {e}")
                    return ModuleDependency(
                        module_name=os.path.basename(file_path),
                        imported_modules=set(),
                        exported_functions=set(),
                        exported_classes=set(),
                        coupling_score=1.0
                    )
            
            def _calculate_coupling_score(self, import_count: int, function_count: int, class_count: int) -> float:
                """计算耦合度分数"""
                # 基于导入数量和导出数量的比例计算耦合度
                total_exports = function_count + class_count
                if total_exports == 0:
                    return 1.0
                
                # 耦合度 = 导入数量 / 导出数量，值越高耦合度越高
                coupling_ratio = import_count / total_exports
                return min(1.0, coupling_ratio)
        
        return BasicDependencyAnalyzer()

    def _create_basic_strategy_generator(self):
        """创建基础策略生成器"""
        class BasicStrategyGenerator:
            def generate_decoupling_strategies(self, module_deps: Dict[str, ModuleDependency]) -> List[DecouplingStrategy]:
                """生成解耦策略"""
                strategies = []
                
                # 识别高耦合模块
                high_coupling_modules = [
                    name for name, dep in module_deps.items() 
                    if dep.coupling_score > 0.7
                ]
                
                if high_coupling_modules:
                    strategies.append(DecouplingStrategy(
                        strategy_type="interface_abstraction",
                        target_modules=high_coupling_modules,
                        description="为高耦合模块创建接口抽象",
                        implementation="创建抽象基类和接口定义",
                        priority=1
                    ))
                
                # 识别循环依赖
                circular_deps = self._detect_circular_dependencies(module_deps)
                if circular_deps:
                    strategies.append(DecouplingStrategy(
                        strategy_type="circular_dependency_break",
                        target_modules=circular_deps,
                        description="打破循环依赖",
                        implementation="引入中间层或事件系统",
                        priority=2
                    ))
                
                # 识别过度依赖
                over_dependent_modules = [
                    name for name, dep in module_deps.items() 
                    if len(dep.imported_modules) > 10
                ]
                if over_dependent_modules:
                    strategies.append(DecouplingStrategy(
                        strategy_type="dependency_injection",
                        target_modules=over_dependent_modules,
                        description="使用依赖注入减少直接依赖",
                        implementation="实现依赖注入容器",
                        priority=3
                    ))
                
                return strategies
            
            def _detect_circular_dependencies(self, module_deps: Dict[str, ModuleDependency]) -> List[str]:
                """检测循环依赖"""
                # 简化的循环依赖检测
                circular_modules = []
                for name, dep in module_deps.items():
                    # 检查是否存在相互依赖
                    for imported in dep.imported_modules:
                        if imported in module_deps:
                            imported_dep = module_deps[imported]
                            if name in imported_dep.imported_modules:
                                circular_modules.extend([name, imported])
                
                return list(set(circular_modules))
        
        return BasicStrategyGenerator()

    def analyze_project_dependencies(self, project_path: str) -> Dict[str, ModuleDependency]:
        """分析项目依赖"""
        try:
            logger.info(f"开始分析项目依赖: {project_path}")
            
            module_deps = {}
            
            # 遍历项目目录
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    if file.endswith('.py') and not file.startswith('__'):
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, project_path)
                        
                        # 分析模块依赖
                        dep = self.dependency_analyzer.analyze_module_dependencies(file_path)
                        dep.module_name = relative_path
                        module_deps[relative_path] = dep
            
            self.module_dependencies = module_deps
            
            # 生成解耦策略
            self.decoupling_strategies = self.strategy_generator.generate_decoupling_strategies(module_deps)
            
            logger.info(f"项目依赖分析完成，发现 {len(module_deps)} 个模块")
            return module_deps
            
        except Exception as e:
            logger.error(f"项目依赖分析失败: {e}")
            return {}

    def get_high_coupling_modules(self, threshold: float = 0.7) -> List[Tuple[str, float]]:
        """获取高耦合模块"""
        try:
            high_coupling = [
                (name, dep.coupling_score) 
                for name, dep in self.module_dependencies.items() 
                if dep.coupling_score > threshold
            ]
            return sorted(high_coupling, key=lambda x: x[1], reverse=True)
        except Exception as e:
            logger.error(f"获取高耦合模块失败: {e}")
            return []

    def generate_decoupling_recommendations(self) -> List[Dict[str, Any]]:
        """生成解耦建议"""
        try:
            recommendations = []
            
            for strategy in self.decoupling_strategies:
                recommendation = {
                    'strategy_type': strategy.strategy_type,
                    'target_modules': strategy.target_modules,
                    'description': strategy.description,
                    'implementation': strategy.implementation,
                    'priority': strategy.priority,
                    'estimated_effort': self._estimate_effort(strategy),
                    'expected_benefit': self._estimate_benefit(strategy)
                }
                recommendations.append(recommendation)
            
            # 按优先级排序
            recommendations.sort(key=lambda x: x['priority'])
            return recommendations
            
        except Exception as e:
            logger.error(f"生成解耦建议失败: {e}")
            return []

    def _estimate_effort(self, strategy: DecouplingStrategy) -> str:
        """估算实施工作量"""
        effort_map = {
            "interface_abstraction": "中等",
            "circular_dependency_break": "高",
            "dependency_injection": "高",
            "module_split": "中等",
            "event_system": "高"
        }
        return effort_map.get(strategy.strategy_type, "未知")

    def _estimate_benefit(self, strategy: DecouplingStrategy) -> str:
        """估算预期收益"""
        benefit_map = {
            "interface_abstraction": "高",
            "circular_dependency_break": "高",
            "dependency_injection": "中",
            "module_split": "中",
            "event_system": "高"
        }
        return benefit_map.get(strategy.strategy_type, "未知")

    def create_interface_abstraction(self, module_name: str) -> str:
        """创建接口抽象"""
        try:
            if module_name not in self.module_dependencies:
                return ""
            
            dep = self.module_dependencies[module_name]
            
            # 生成接口定义
            interface_code = f"""
# 为 {module_name} 生成的接口抽象
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class {module_name.title().replace('.', '').replace('_', '')}Interface(ABC):
    \"\"\"{module_name} 接口抽象\"\"\"
    
"""
            
            # 为导出的函数生成抽象方法
            for func_name in dep.exported_functions:
                interface_code += f"""
    @abstractmethod
    def {func_name}(self, *args, **kwargs) -> Any:
        \"\"\"{func_name} 抽象方法\"\"\"
        pass
"""
            
            # 为导出的类生成抽象基类
            for class_name in dep.exported_classes:
                interface_code += f"""
class {class_name}Interface(ABC):
    \"\"\"{class_name} 接口抽象\"\"\"
    
    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass
"""
            
            return interface_code
            
        except Exception as e:
            logger.error(f"创建接口抽象失败: {e}")
            return ""

    def get_dependency_statistics(self) -> Dict[str, Any]:
        """获取依赖统计信息"""
        try:
            if not self.module_dependencies:
                return {}
            
            total_modules = len(self.module_dependencies)
            avg_coupling = sum(dep.coupling_score for dep in self.module_dependencies.values()) / total_modules
            high_coupling_count = len(self.get_high_coupling_modules())
            
            return {
                'total_modules': total_modules,
                'average_coupling': avg_coupling,
                'high_coupling_modules': high_coupling_count,
                'decoupling_strategies': len(self.decoupling_strategies),
                'analysis_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取依赖统计失败: {e}")
            return {}

# 全局实例
_decoupling_system_instance = None

def get_intelligent_decoupling_system() -> IntelligentDecouplingSystem:
    """获取智能解耦系统实例"""
    global _decoupling_system_instance
    if _decoupling_system_instance is None:
        _decoupling_system_instance = IntelligentDecouplingSystem()
    return _decoupling_system_instance

def analyze_project_dependencies(project_path: str) -> Dict[str, ModuleDependency]:
    """便捷函数: 分析项目依赖"""
    system = get_intelligent_decoupling_system()
    return system.analyze_project_dependencies(project_path)

if __name__ == "__main__":
    # 测试智能解耦系统
    print("测试智能解耦系统...")
    
    system = IntelligentDecouplingSystem()
    
    # 分析当前项目
    deps = system.analyze_project_dependencies("src")
    print(f"分析完成，发现 {len(deps)} 个模块")
    
    # 获取高耦合模块
    high_coupling = system.get_high_coupling_modules()
    print(f"高耦合模块: {len(high_coupling)} 个")
    for module, score in high_coupling[:5]:
        print(f"  {module}: {score:.3f}")
    
    # 生成解耦建议
    recommendations = system.generate_decoupling_recommendations()
    print(f"解耦建议: {len(recommendations)} 条")
    for rec in recommendations:
        print(f"  {rec['strategy_type']}: {rec['description']}")
    
    # 显示统计信息
    stats = system.get_dependency_statistics()
    print(f"依赖统计: {stats}")
    
    print("智能解耦系统测试完成！")
