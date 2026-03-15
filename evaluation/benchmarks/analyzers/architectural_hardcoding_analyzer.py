#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
架构硬编码检测器
专门检测架构层面的硬编码问题，包括硬编码的架构模式、设计模式、层次结构等
"""

import ast
import re
import os
from typing import Dict, Any, List, Set, Union


class ArchitecturalHardcodingAnalyzer:
    """架构硬编码检测器"""
    
    def __init__(self, python_files: List[str]):
        self.python_files = python_files
        self.logger = self._get_logger()
    
    def _get_logger(self):
        """获取日志记录器"""
        import logging
        return logging.getLogger("ArchitecturalHardcodingAnalyzer")
    
    def analyze(self) -> Dict[str, Any]:
        """执行架构硬编码检测分析"""
        return {
            "hardcoded_architecture_patterns": self._detect_hardcoded_architecture_patterns(),
            "hardcoded_design_patterns": self._detect_hardcoded_design_patterns(),
            "hardcoded_layer_structure": self._detect_hardcoded_layer_structure(),
            "hardcoded_dependency_injection": self._detect_hardcoded_dependency_injection(),
            "hardcoded_interface_definitions": self._detect_hardcoded_interface_definitions(),
            "hardcoded_configuration_structure": self._detect_hardcoded_configuration_structure(),
            "hardcoded_service_registration": self._detect_hardcoded_service_registration(),
            "hardcoded_workflow_patterns": self._detect_hardcoded_workflow_patterns(),
            "hardcoded_error_handling_patterns": self._detect_hardcoded_error_handling_patterns(),
            "hardcoded_logging_patterns": self._detect_hardcoded_logging_patterns()
        }
    
    def _detect_hardcoded_architecture_patterns(self) -> Dict[str, Any]:
        """检测硬编码的架构模式"""
        try:
            issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测硬编码的架构模式
                architecture_patterns = [
                    # 硬编码的分层架构
                    (r'class\s+(\w*Layer\w*|Layered\w*|Architecture\w*)', 'hardcoded_layer_class'),
                    (r'def\s+_initialize_layers\(', 'hardcoded_layer_initialization'),
                    (r'layers\s*=\s*\{[^}]*"presentation"[^}]*"business"[^}]*"data"', 'hardcoded_three_layer_structure'),
                    
                    # 硬编码的MVC模式
                    (r'class\s+(\w*Model\w*|\w*View\w*|\w*Controller\w*)', 'hardcoded_mvc_pattern'),
                    
                    # 硬编码的微服务模式
                    (r'class\s+(\w*Service\w*|\w*Microservice\w*)', 'hardcoded_microservice_pattern'),
                    
                    # 硬编码的CQRS模式
                    (r'class\s+(\w*Command\w*|\w*Query\w*|\w*Handler\w*)', 'hardcoded_cqrs_pattern'),
                    
                    # 硬编码的事件驱动模式
                    (r'class\s+(\w*Event\w*|\w*Publisher\w*|\w*Subscriber\w*)', 'hardcoded_event_driven_pattern'),
                ]
                
                for pattern, issue_type in architecture_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': issue_type,
                            'content': match.group(0),
                            'severity': 'high'
                        })
            
            return {
                'has_hardcoded_architecture_patterns': len(issues) > 0,
                'hardcoded_architecture_pattern_count': len(issues),
                'issues': issues[:10],
                'score': max(0, 1.0 - len(issues) * 0.1)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码架构模式失败: {e}")
            return {'has_hardcoded_architecture_patterns': False, 'hardcoded_architecture_pattern_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_hardcoded_design_patterns(self) -> Dict[str, Any]:
        """检测硬编码的设计模式"""
        try:
            issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测硬编码的设计模式
                design_patterns = [
                    # 硬编码的单例模式
                    (r'class\s+(\w*Singleton\w*|\w*Manager\w*).*?__new__', 'hardcoded_singleton_pattern'),
                    (r'_instance\s*=\s*None', 'hardcoded_singleton_instance'),
                    
                    # 硬编码的工厂模式
                    (r'class\s+(\w*Factory\w*|\w*Builder\w*)', 'hardcoded_factory_pattern'),
                    (r'def\s+create_\w+\(', 'hardcoded_factory_method'),
                    
                    # 硬编码的观察者模式
                    (r'class\s+(\w*Observer\w*|\w*Subject\w*)', 'hardcoded_observer_pattern'),
                    (r'def\s+(notify|update|attach|detach)', 'hardcoded_observer_methods'),
                    
                    # 硬编码的策略模式
                    (r'class\s+(\w*Strategy\w*|\w*Algorithm\w*)', 'hardcoded_strategy_pattern'),
                    (r'def\s+execute_\w+\(', 'hardcoded_strategy_execution'),
                    
                    # 硬编码的命令模式
                    (r'class\s+(\w*Command\w*|\w*Action\w*)', 'hardcoded_command_pattern'),
                    (r'def\s+(execute|undo|redo)', 'hardcoded_command_methods'),
                ]
                
                for pattern, issue_type in design_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': issue_type,
                            'content': match.group(0),
                            'severity': 'medium'
                        })
            
            return {
                'has_hardcoded_design_patterns': len(issues) > 0,
                'hardcoded_design_pattern_count': len(issues),
                'issues': issues[:10],
                'score': max(0, 1.0 - len(issues) * 0.05)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码设计模式失败: {e}")
            return {'has_hardcoded_design_patterns': False, 'hardcoded_design_pattern_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_hardcoded_layer_structure(self) -> Dict[str, Any]:
        """检测硬编码的层次结构"""
        try:
            issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测硬编码的层次结构
                layer_patterns = [
                    # 硬编码的三层架构
                    (r'"presentation".*?"business".*?"data"', 'hardcoded_three_layer_structure'),
                    (r'LayerType\.(PRESENTATION|BUSINESS|DATA)', 'hardcoded_layer_types'),
                    
                    # 硬编码的层次依赖
                    (r'dependencies\s*=\s*\["presentation"\]', 'hardcoded_layer_dependencies'),
                    (r'dependencies\s*=\s*\["business"\]', 'hardcoded_layer_dependencies'),
                    
                    # 硬编码的层次初始化
                    (r'def\s+_initialize_layers\(', 'hardcoded_layer_initialization'),
                    (r'layers\s*=\s*\{[^}]*"presentation"[^}]*"business"[^}]*"data"[^}]*\}', 'hardcoded_layer_definition'),
                ]
                
                for pattern, issue_type in layer_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': issue_type,
                            'content': match.group(0)[:100] + '...' if len(match.group(0)) > 100 else match.group(0),
                            'severity': 'high'
                        })
            
            return {
                'has_hardcoded_layer_structure': len(issues) > 0,
                'hardcoded_layer_structure_count': len(issues),
                'issues': issues[:10],
                'score': max(0, 1.0 - len(issues) * 0.1)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码层次结构失败: {e}")
            return {'has_hardcoded_layer_structure': False, 'hardcoded_layer_structure_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_hardcoded_dependency_injection(self) -> Dict[str, Any]:
        """检测硬编码的依赖注入"""
        try:
            issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测硬编码的依赖注入
                di_patterns = [
                    # 硬编码的服务注册
                    (r'register_service\s*\(\s*["\'][^"\']*["\']', 'hardcoded_service_registration'),
                    (r'services\s*=\s*\{[^}]*["\'][^"\']*["\'][^}]*\}', 'hardcoded_service_container'),
                    
                    # 硬编码的依赖解析
                    (r'get_service\s*\(\s*["\'][^"\']*["\']', 'hardcoded_service_resolution'),
                    (r'resolve\s*\(\s*["\'][^"\']*["\']', 'hardcoded_dependency_resolution'),
                    
                    # 硬编码的生命周期管理
                    (r'singleton\s*\(\s*["\'][^"\']*["\']', 'hardcoded_singleton_lifecycle'),
                    (r'transient\s*\(\s*["\'][^"\']*["\']', 'hardcoded_transient_lifecycle'),
                    (r'scoped\s*\(\s*["\'][^"\']*["\']', 'hardcoded_scoped_lifecycle'),
                ]
                
                for pattern, issue_type in di_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': issue_type,
                            'content': match.group(0),
                            'severity': 'medium'
                        })
            
            return {
                'has_hardcoded_dependency_injection': len(issues) > 0,
                'hardcoded_dependency_injection_count': len(issues),
                'issues': issues[:10],
                'score': max(0, 1.0 - len(issues) * 0.05)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码依赖注入失败: {e}")
            return {'has_hardcoded_dependency_injection': False, 'hardcoded_dependency_injection_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_hardcoded_interface_definitions(self) -> Dict[str, Any]:
        """检测硬编码的接口定义"""
        try:
            issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测硬编码的接口定义
                interface_patterns = [
                    # 硬编码的接口名称
                    (r'class\s+I\w+\(.*?\):', 'hardcoded_interface_naming'),
                    (r'class\s+\w*Interface\w*\(.*?\):', 'hardcoded_interface_class'),
                    
                    # 硬编码的接口方法
                    (r'def\s+(\w*process\w*|\w*handle\w*|\w*execute\w*)\s*\(', 'hardcoded_interface_methods'),
                    
                    # 硬编码的抽象方法
                    (r'@abstractmethod\s*\n\s*def\s+\w+', 'hardcoded_abstract_methods'),
                    
                    # 硬编码的协议定义
                    (r'class\s+\w*Protocol\w*\(.*?\):', 'hardcoded_protocol_definition'),
                ]
                
                for pattern, issue_type in interface_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': issue_type,
                            'content': match.group(0),
                            'severity': 'medium'
                        })
            
            return {
                'has_hardcoded_interface_definitions': len(issues) > 0,
                'hardcoded_interface_definition_count': len(issues),
                'issues': issues[:10],
                'score': max(0, 1.0 - len(issues) * 0.05)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码接口定义失败: {e}")
            return {'has_hardcoded_interface_definitions': False, 'hardcoded_interface_definition_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_hardcoded_configuration_structure(self) -> Dict[str, Any]:
        """检测硬编码的配置结构"""
        try:
            issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测硬编码的配置结构
                config_patterns = [
                    # 硬编码的配置键
                    (r'config\[["\'][^"\']*["\']\]', 'hardcoded_config_keys'),
                    (r'get\s*\(\s*["\'][^"\']*["\']', 'hardcoded_config_get'),
                    (r'set\s*\(\s*["\'][^"\']*["\']', 'hardcoded_config_set'),
                    
                    # 硬编码的配置默认值
                    (r'default\s*=\s*["\'][^"\']*["\']', 'hardcoded_config_defaults'),
                    (r'fallback\s*=\s*["\'][^"\']*["\']', 'hardcoded_config_fallbacks'),
                    
                    # 硬编码的配置验证
                    (r'validate\s*\(\s*["\'][^"\']*["\']', 'hardcoded_config_validation'),
                    (r'check\s*\(\s*["\'][^"\']*["\']', 'hardcoded_config_checks'),
                ]
                
                for pattern, issue_type in config_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': issue_type,
                            'content': match.group(0),
                            'severity': 'medium'
                        })
            
            return {
                'has_hardcoded_configuration_structure': len(issues) > 0,
                'hardcoded_configuration_structure_count': len(issues),
                'issues': issues[:10],
                'score': max(0, 1.0 - len(issues) * 0.05)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码配置结构失败: {e}")
            return {'has_hardcoded_configuration_structure': False, 'hardcoded_configuration_structure_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_hardcoded_service_registration(self) -> Dict[str, Any]:
        """检测硬编码的服务注册"""
        try:
            issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测硬编码的服务注册
                service_patterns = [
                    # 硬编码的服务名称
                    (r'register\s*\(\s*["\'][^"\']*["\']', 'hardcoded_service_name'),
                    (r'bind\s*\(\s*["\'][^"\']*["\']', 'hardcoded_service_binding'),
                    
                    # 硬编码的服务类型
                    (r'as_singleton\s*\(\s*["\'][^"\']*["\']', 'hardcoded_singleton_service'),
                    (r'as_transient\s*\(\s*["\'][^"\']*["\']', 'hardcoded_transient_service'),
                    (r'as_scoped\s*\(\s*["\'][^"\']*["\']', 'hardcoded_scoped_service'),
                    
                    # 硬编码的服务工厂
                    (r'factory\s*\(\s*["\'][^"\']*["\']', 'hardcoded_service_factory'),
                ]
                
                for pattern, issue_type in service_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': issue_type,
                            'content': match.group(0),
                            'severity': 'medium'
                        })
            
            return {
                'has_hardcoded_service_registration': len(issues) > 0,
                'hardcoded_service_registration_count': len(issues),
                'issues': issues[:10],
                'score': max(0, 1.0 - len(issues) * 0.05)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码服务注册失败: {e}")
            return {'has_hardcoded_service_registration': False, 'hardcoded_service_registration_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_hardcoded_workflow_patterns(self) -> Dict[str, Any]:
        """检测硬编码的工作流模式"""
        try:
            issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测硬编码的工作流模式
                workflow_patterns = [
                    # 硬编码的状态机
                    (r'class\s+(\w*State\w*|\w*StateMachine\w*)', 'hardcoded_state_machine'),
                    (r'def\s+(transition|next_state|previous_state)', 'hardcoded_state_transitions'),
                    
                    # 硬编码的管道模式
                    (r'class\s+(\w*Pipeline\w*|\w*Processor\w*)', 'hardcoded_pipeline_pattern'),
                    (r'def\s+(process|execute|run)', 'hardcoded_pipeline_execution'),
                    
                    # 硬编码的链式调用
                    (r'def\s+(\w*chain\w*|\w*link\w*)', 'hardcoded_chain_pattern'),
                    (r'\.then\(|\.next\(|\.follow\(', 'hardcoded_chain_methods'),
                ]
                
                for pattern, issue_type in workflow_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': issue_type,
                            'content': match.group(0),
                            'severity': 'medium'
                        })
            
            return {
                'has_hardcoded_workflow_patterns': len(issues) > 0,
                'hardcoded_workflow_pattern_count': len(issues),
                'issues': issues[:10],
                'score': max(0, 1.0 - len(issues) * 0.05)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码工作流模式失败: {e}")
            return {'has_hardcoded_workflow_patterns': False, 'hardcoded_workflow_pattern_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_hardcoded_error_handling_patterns(self) -> Dict[str, Any]:
        """检测硬编码的错误处理模式"""
        try:
            issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测硬编码的错误处理模式
                error_patterns = [
                    # 硬编码的异常类型
                    (r'raise\s+(\w*Error\w*|\w*Exception\w*)\s*\(', 'hardcoded_exception_types'),
                    (r'except\s+(\w*Error\w*|\w*Exception\w*):', 'hardcoded_exception_handling'),
                    
                    # 硬编码的错误消息
                    (r'raise\s+\w+\s*\(\s*["\'][^"\']*["\']', 'hardcoded_error_messages'),
                    (r'logger\.error\s*\(\s*["\'][^"\']*["\']', 'hardcoded_error_logging'),
                    
                    # 硬编码的错误代码
                    (r'error_code\s*=\s*["\']\d+["\']', 'hardcoded_error_codes'),
                    (r'status_code\s*=\s*\d+', 'hardcoded_status_codes'),
                ]
                
                for pattern, issue_type in error_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': issue_type,
                            'content': match.group(0),
                            'severity': 'low'
                        })
            
            return {
                'has_hardcoded_error_handling_patterns': len(issues) > 0,
                'hardcoded_error_handling_pattern_count': len(issues),
                'issues': issues[:10],
                'score': max(0, 1.0 - len(issues) * 0.02)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码错误处理模式失败: {e}")
            return {'has_hardcoded_error_handling_patterns': False, 'hardcoded_error_handling_pattern_count': 0, 'issues': [], 'score': 1.0}
    
    def _detect_hardcoded_logging_patterns(self) -> Dict[str, Any]:
        """检测硬编码的日志模式"""
        try:
            issues = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测硬编码的日志模式
                logging_patterns = [
                    # 硬编码的日志级别
                    (r'logger\.(debug|info|warning|error|critical)\s*\(', 'hardcoded_log_levels'),
                    
                    # 硬编码的日志消息
                    (r'logger\.\w+\s*\(\s*["\'][^"\']*["\']', 'hardcoded_log_messages'),
                    
                    # 硬编码的日志格式
                    (r'logging\.basicConfig\s*\([^)]*format\s*=\s*["\'][^"\']*["\']', 'hardcoded_log_format'),
                    
                    # 硬编码的日志处理器
                    (r'FileHandler\s*\(\s*["\'][^"\']*["\']', 'hardcoded_log_handlers'),
                ]
                
                for pattern, issue_type in logging_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append({
                            'file': file_path,
                            'line': line_num,
                            'type': issue_type,
                            'content': match.group(0),
                            'severity': 'low'
                        })
            
            return {
                'has_hardcoded_logging_patterns': len(issues) > 0,
                'hardcoded_logging_pattern_count': len(issues),
                'issues': issues[:10],
                'score': max(0, 1.0 - len(issues) * 0.02)
            }
            
        except Exception as e:
            self.logger.error(f"检测硬编码日志模式失败: {e}")
            return {'has_hardcoded_logging_patterns': False, 'hardcoded_logging_pattern_count': 0, 'issues': [], 'score': 1.0}
    
    def _read_file_content(self, file_path: str) -> str:
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""


def create_architectural_hardcoding_analyzer(python_files: List[str]) -> ArchitecturalHardcodingAnalyzer:
    """创建架构硬编码检测器"""
    return ArchitecturalHardcodingAnalyzer(python_files)
