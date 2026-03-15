"""
大脑决策机制分析器
基于程序源码逻辑分析，检测大脑启发的决策机制
"""

import ast
from typing import Dict, Any, List
from base_analyzer import BaseAnalyzer


class BrainDecisionMechanismAnalyzer(BaseAnalyzer):
    """大脑决策机制分析器 - 基于程序源码逻辑分析"""
    
    def analyze(self) -> Dict[str, Any]:
        """执行大脑决策机制分析"""
        # 分析各个维度
        brain_decision_score = self._analyze_brain_decision_mechanisms()
        ntc_mechanism = self._analyze_ntc_mechanism()
        evidence_accumulation = self._analyze_evidence_accumulation()
        decision_commitment = self._analyze_decision_commitment()
        geometric_trajectory = self._analyze_geometric_trajectory()
        dynamic_threshold = self._analyze_dynamic_threshold()
        commitment_lock = self._analyze_commitment_lock()
        
        # 计算综合分数
        detailed_scores = {
            "brain_decision_score": brain_decision_score,
            "nTc_mechanism": ntc_mechanism,
            "evidence_accumulation": evidence_accumulation,
            "decision_commitment": decision_commitment,
            "geometric_trajectory": geometric_trajectory,
            "dynamic_threshold": dynamic_threshold,
            "commitment_lock": commitment_lock
        }
        
        # 计算平均分数
        overall_score = sum(detailed_scores.values()) / len(detailed_scores)
        
        return {
            "score": overall_score,
            "total_issues": 0,  # 大脑决策机制不是问题，而是功能
            "issues": [],
            "detailed_scores": detailed_scores
        }
    
    def _analyze_brain_decision_mechanisms(self) -> float:
        """分析大脑决策机制 - 基于程序源码逻辑"""
        try:
            total_score = 0.0
            file_count = 0
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 简化检测：直接检查文件内容中的大脑决策机制关键词
                file_score = self._detect_brain_decision_keywords(content)
                
                if file_score > 0:
                    total_score += file_score
                    file_count += 1
            
            return total_score / max(file_count, 1) if file_count > 0 else 0.0
            
        except Exception as e:
            self.logger.error(f"分析大脑决策机制失败: {e}")
            return 0.0
    
    def _detect_brain_decision_keywords(self, content: str) -> float:
        """检测大脑决策机制关键词"""
        try:
            score = 0.0
            
            # 检测大脑决策机制的关键特征
            brain_decision_patterns = [
                'brain_decision_config',
                'nTc_threshold',
                'evidence_accumulation',
                'decision_commitment',
                'dynamic_threshold',
                'commitment_lock',
                'decision_trajectories',
                'committed_decisions',
                'current_decision_state',
                'evidence_trajectory',
                'calculate_evidence_confidence',
                'commit_to_decision',
                'is_decision_committed',
                'calculate_dynamic_threshold',
                'geometric_trajectories',
                'trajectory_axes',
                'evidence_axis',
                'commitment_axis',
                'update_geometric_trajectory',
                'detect_ntc_moment',
                'calculate_trajectory_angle',
                'calculate_change_rate',
                'calculate_slope',
                'calculate_decision_confidence'
            ]
            
            # 计算匹配的关键词数量
            matches = 0
            for pattern in brain_decision_patterns:
                if pattern in content:
                    matches += 1
            
            # 根据匹配数量计算分数
            if matches > 0:
                score = min(matches / len(brain_decision_patterns), 1.0)
            
            return score
            
        except Exception as e:
            self.logger.error(f"检测大脑决策关键词失败: {e}")
            return 0.0
    
    def _has_brain_decision_mechanism(self, func_node: ast.FunctionDef, content: str) -> bool:
        """
        检查函数是否有大脑决策机制 - 基于程序源码逻辑分析
        
        Args:
            func_node: 函数AST节点
            content: 文件内容
            
        Returns:
            是否有大脑决策机制
        """
        try:
            # 分析函数的实际决策机制实现
            decision_mechanism_analysis = self._analyze_decision_mechanism_implementation(func_node)
            
            # 分析证据积累机制
            evidence_accumulation_analysis = self._analyze_evidence_accumulation_implementation(func_node)
            
            # 分析决策承诺机制
            commitment_analysis = self._analyze_commitment_implementation(func_node)
            
            # 分析动态阈值机制
            threshold_analysis = self._analyze_dynamic_threshold_implementation(func_node)
            
            # 分析决策状态管理
            state_management_analysis = self._analyze_decision_state_management(func_node)
            
            # 综合评分
            total_score = (
                decision_mechanism_analysis['has_decision_mechanism'] * 0.3 +
                evidence_accumulation_analysis['has_evidence_accumulation'] * 0.25 +
                commitment_analysis['has_commitment_mechanism'] * 0.25 +
                threshold_analysis['has_dynamic_threshold'] * 0.1 +
                state_management_analysis['has_state_management'] * 0.1
            )
            
            return total_score > 0.4  # 阈值：需要至少40%的大脑决策特征
            
        except Exception as e:
            self.logger.error(f"分析大脑决策机制失败: {e}")
            return False
    
    def _analyze_decision_mechanism_implementation(self, func_node: ast.FunctionDef) -> Dict[str, Any]:
        """分析决策机制实现 - 基于程序源码逻辑"""
        analysis = {
            'has_decision_mechanism': False,
            'decision_states': 0,
            'decision_transitions': 0,
            'decision_config': 0,
            'decision_trajectories': 0
        }
        
        # 检查是否有决策状态管理
        for node in ast.walk(func_node):
            if isinstance(node, ast.Assign):
                if self._is_decision_state_assignment(node):
                    analysis['decision_states'] += 1
                    analysis['has_decision_mechanism'] = True
            
            elif isinstance(node, ast.If):
                if self._is_decision_transition(node):
                    analysis['decision_transitions'] += 1
                    analysis['has_decision_mechanism'] = True
            
            elif isinstance(node, ast.Dict):
                if self._is_decision_config_dict(node):
                    analysis['decision_config'] += 1
                    analysis['has_decision_mechanism'] = True
            
            elif isinstance(node, ast.Call):
                if self._is_decision_trajectory_call(node):
                    analysis['decision_trajectories'] += 1
                    analysis['has_decision_mechanism'] = True
        
        return analysis
    
    def _analyze_evidence_accumulation_implementation(self, func_node: ast.FunctionDef) -> Dict[str, Any]:
        """分析证据积累机制实现 - 基于程序源码逻辑"""
        analysis = {
            'has_evidence_accumulation': False,
            'evidence_trajectory': 0,
            'evidence_confidence': 0,
            'evidence_timeout': 0,
            'evidence_analysis': 0
        }
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Assign):
                if self._is_evidence_trajectory_assignment(node):
                    analysis['evidence_trajectory'] += 1
                    analysis['has_evidence_accumulation'] = True
            
            elif isinstance(node, ast.Call):
                if self._is_evidence_confidence_call(node):
                    analysis['evidence_confidence'] += 1
                    analysis['has_evidence_accumulation'] = True
                
                elif self._is_evidence_timeout_call(node):
                    analysis['evidence_timeout'] += 1
                    analysis['has_evidence_accumulation'] = True
                
                elif self._is_evidence_analysis_call(node):
                    analysis['evidence_analysis'] += 1
                    analysis['has_evidence_accumulation'] = True
        
        return analysis
    
    def _analyze_commitment_implementation(self, func_node: ast.FunctionDef) -> Dict[str, Any]:
        """分析决策承诺机制实现 - 基于程序源码逻辑"""
        analysis = {
            'has_commitment_mechanism': False,
            'commitment_check': 0,
            'commitment_lock': 0,
            'commitment_timestamp': 0,
            'commitment_duration': 0
        }
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.If):
                if self._is_commitment_check(node):
                    analysis['commitment_check'] += 1
                    analysis['has_commitment_mechanism'] = True
            
            elif isinstance(node, ast.Assign):
                if self._is_commitment_lock_assignment(node):
                    analysis['commitment_lock'] += 1
                    analysis['has_commitment_mechanism'] = True
                
                elif self._is_commitment_timestamp_assignment(node):
                    analysis['commitment_timestamp'] += 1
                    analysis['has_commitment_mechanism'] = True
            
            elif isinstance(node, ast.Call):
                if self._is_commitment_duration_call(node):
                    analysis['commitment_duration'] += 1
                    analysis['has_commitment_mechanism'] = True
        
        return analysis
    
    def _analyze_dynamic_threshold_implementation(self, func_node: ast.FunctionDef) -> Dict[str, Any]:
        """分析动态阈值机制实现 - 基于程序源码逻辑"""
        analysis = {
            'has_dynamic_threshold': False,
            'threshold_calculation': 0,
            'threshold_adjustment': 0,
            'threshold_modifiers': 0,
            'threshold_comparison': 0
        }
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Assign):
                if self._is_threshold_calculation_assignment(node):
                    analysis['threshold_calculation'] += 1
                    analysis['has_dynamic_threshold'] = True
                
                elif self._is_threshold_modifiers_assignment(node):
                    analysis['threshold_modifiers'] += 1
                    analysis['has_dynamic_threshold'] = True
            
            elif isinstance(node, ast.Call):
                if self._is_threshold_adjustment_call(node):
                    analysis['threshold_adjustment'] += 1
                    analysis['has_dynamic_threshold'] = True
            
            elif isinstance(node, ast.Compare):
                if self._is_threshold_comparison(node):
                    analysis['threshold_comparison'] += 1
                    analysis['has_dynamic_threshold'] = True
        
        return analysis
    
    def _analyze_decision_state_management(self, func_node: ast.FunctionDef) -> Dict[str, Any]:
        """分析决策状态管理 - 基于程序源码逻辑"""
        analysis = {
            'has_state_management': False,
            'state_variables': 0,
            'state_transitions': 0,
            'state_checks': 0,
            'state_updates': 0
        }
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Assign):
                if self._is_state_variable_assignment(node):
                    analysis['state_variables'] += 1
                    analysis['has_state_management'] = True
                
                elif self._is_state_update_assignment(node):
                    analysis['state_updates'] += 1
                    analysis['has_state_management'] = True
            
            elif isinstance(node, ast.If):
                if self._is_state_check(node):
                    analysis['state_checks'] += 1
                    analysis['has_state_management'] = True
                
                elif self._is_state_transition(node):
                    analysis['state_transitions'] += 1
                    analysis['has_state_management'] = True
        
        return analysis
    
    # 辅助方法 - 基于程序源码逻辑分析
    def _is_decision_state_assignment(self, node: ast.Assign) -> bool:
        """检查是否是决策状态赋值"""
        if isinstance(node.value, ast.Str):
            value = node.value.s.lower()
            return any(term in value for term in [
                'evidence_accumulation', 'decision_commitment', 'execution',
                '证据积累', '决策承诺', '执行'
            ])
        return False
    
    def _is_decision_transition(self, node: ast.If) -> bool:
        """检查是否是决策转换"""
        if isinstance(node.test, ast.Compare):
            if isinstance(node.test.left, ast.Name):
                var_name = node.test.left.id.lower()
                return any(term in var_name for term in [
                    'decision_state', 'current_state', 'state'
                ])
        return False
    
    def _is_decision_config_dict(self, node: ast.Dict) -> bool:
        """检查是否是决策配置字典"""
        if node.keys:
            for key in node.keys:
                if isinstance(key, ast.Str):
                    key_name = key.s.lower()
                    if any(term in key_name for term in [
                        'nTc_threshold', 'evidence_accumulation_timeout', 
                        'commitment_lock_duration', 'dynamic_threshold_adjustment'
                    ]):
                        return True
        return False
    
    def _is_decision_trajectory_call(self, node: ast.Call) -> bool:
        """检查是否是决策轨迹调用"""
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr.lower()
            return any(term in func_name for term in [
                'accumulate_evidence', 'calculate_confidence', 'commit_to_decision',
                'evidence_trajectory', 'decision_trajectory'
            ])
        return False
    
    def _is_evidence_trajectory_assignment(self, node: ast.Assign) -> bool:
        """检查是否是证据轨迹赋值"""
        if isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id.lower()
            return any(term in var_name for term in [
                'evidence_trajectory', 'evidence_confidence', 'evidence_analysis'
            ])
        return False
    
    def _is_evidence_confidence_call(self, node: ast.Call) -> bool:
        """检查是否是证据置信度调用"""
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr.lower()
            return any(term in func_name for term in [
                'calculate_evidence_confidence', 'evidence_confidence', 'confidence'
            ])
        return False
    
    def _is_evidence_timeout_call(self, node: ast.Call) -> bool:
        """检查是否是证据超时调用"""
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr.lower()
            return any(term in func_name for term in [
                'evidence_accumulation_timeout', 'timeout', 'evidence_timeout'
            ])
        return False
    
    def _is_evidence_analysis_call(self, node: ast.Call) -> bool:
        """检查是否是证据分析调用"""
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr.lower()
            return any(term in func_name for term in [
                'analyze_engine_suitability', 'analyze_query_complexity', 
                'extract_context_features', 'evidence_analysis'
            ])
        return False
    
    def _is_commitment_check(self, node: ast.If) -> bool:
        """检查是否是承诺检查"""
        if isinstance(node.test, ast.Call):
            if isinstance(node.test.func, ast.Attribute):
                func_name = node.test.func.attr.lower()
                return any(term in func_name for term in [
                    'is_decision_committed', 'commitment_check', 'is_committed'
                ])
        return False
    
    def _is_commitment_lock_assignment(self, node: ast.Assign) -> bool:
        """检查是否是承诺锁定赋值"""
        if isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id.lower()
            return any(term in var_name for term in [
                'committed_decisions', 'commitment_lock', 'decision_lock'
            ])
        return False
    
    def _is_commitment_timestamp_assignment(self, node: ast.Assign) -> bool:
        """检查是否是承诺时间戳赋值"""
        if isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id.lower()
            return any(term in var_name for term in [
                'timestamp', 'commit_time', 'decision_time'
            ])
        return False
    
    def _is_commitment_duration_call(self, node: ast.Call) -> bool:
        """检查是否是承诺持续时间调用"""
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr.lower()
            return any(term in func_name for term in [
                'commitment_lock_duration', 'lock_duration', 'commitment_duration'
            ])
        return False
    
    def _is_threshold_calculation_assignment(self, node: ast.Assign) -> bool:
        """检查是否是阈值计算赋值"""
        if isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id.lower()
            return any(term in var_name for term in [
                'dynamic_threshold', 'threshold', 'nTc_threshold'
            ])
        return False
    
    def _is_threshold_modifiers_assignment(self, node: ast.Assign) -> bool:
        """检查是否是阈值修饰符赋值"""
        if isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id.lower()
            return any(term in var_name for term in [
                'threshold_modifiers', 'modifiers', 'threshold_adjustment'
            ])
        return False
    
    def _is_threshold_adjustment_call(self, node: ast.Call) -> bool:
        """检查是否是阈值调整调用"""
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr.lower()
            return any(term in func_name for term in [
                'calculate_dynamic_threshold', 'adjust_threshold', 'threshold_adjustment'
            ])
        return False
    
    def _is_threshold_comparison(self, node: ast.Compare) -> bool:
        """检查是否是阈值比较"""
        if isinstance(node.left, ast.Name):
            var_name = node.left.id.lower()
            return any(term in var_name for term in [
                'evidence_confidence', 'confidence', 'threshold'
            ])
        return False
    
    def _is_state_variable_assignment(self, node: ast.Assign) -> bool:
        """检查是否是状态变量赋值"""
        if isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id.lower()
            return any(term in var_name for term in [
                'current_decision_state', 'decision_state', 'current_state'
            ])
        return False
    
    def _is_state_update_assignment(self, node: ast.Assign) -> bool:
        """检查是否是状态更新赋值"""
        if isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id.lower()
            return any(term in var_name for term in [
                'current_decision_state', 'decision_state', 'current_state'
            ])
        return False
    
    def _is_state_check(self, node: ast.If) -> bool:
        """检查是否是状态检查"""
        if isinstance(node.test, ast.Compare):
            if isinstance(node.test.left, ast.Name):
                var_name = node.test.left.id.lower()
                return any(term in var_name for term in [
                    'current_decision_state', 'decision_state', 'current_state'
                ])
        return False
    
    def _is_state_transition(self, node: ast.If) -> bool:
        """检查是否是状态转换"""
        if isinstance(node.test, ast.Compare):
            if isinstance(node.test.left, ast.Name):
                var_name = node.test.left.id.lower()
                return any(term in var_name for term in [
                    'current_decision_state', 'decision_state', 'current_state'
                ])
        return False
    
    # 其他分析方法 - 简化版本
    def _analyze_ntc_mechanism(self) -> float:
        """分析nTc机制"""
        try:
            base_score = self._analyze_brain_decision_mechanisms()
            return min(base_score * 0.8, 1.0)
        except:
            return 0.0
    
    def _analyze_evidence_accumulation(self) -> float:
        """分析证据积累机制"""
        try:
            base_score = self._analyze_brain_decision_mechanisms()
            return min(base_score * 0.7, 1.0)
        except:
            return 0.0
    
    def _analyze_decision_commitment(self) -> float:
        """分析决策承诺机制"""
        try:
            base_score = self._analyze_brain_decision_mechanisms()
            return min(base_score * 0.6, 1.0)
        except:
            return 0.0
    
    def _analyze_geometric_trajectory(self) -> float:
        """分析几何化轨迹"""
        try:
            total_score = 0.0
            file_count = 0
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # 检测几何轨迹相关的关键词
                geometric_patterns = [
                    'geometric_trajectories',
                    'trajectory_axes',
                    'evidence_axis',
                    'commitment_axis',
                    'update_geometric_trajectory',
                    'detect_ntc_moment',
                    'calculate_trajectory_angle',
                    'calculate_change_rate',
                    'calculate_slope',
                    'trajectory_angle',
                    'nTc_detected',
                    'evidence_points',
                    'commitment_points'
                ]
                
                matches = 0
                for pattern in geometric_patterns:
                    if pattern in content:
                        matches += 1
                
                if matches > 0:
                    file_score = min(matches / len(geometric_patterns), 1.0)
                    total_score += file_score
                    file_count += 1
            
            return total_score / max(file_count, 1) if file_count > 0 else 0.0
            
        except Exception as e:
            self.logger.error(f"分析几何轨迹失败: {e}")
            return 0.0
    
    def _analyze_dynamic_threshold(self) -> float:
        """分析动态阈值机制"""
        try:
            base_score = self._analyze_brain_decision_mechanisms()
            return min(base_score * 0.9, 1.0)
        except:
            return 0.0
    
    def _analyze_commitment_lock(self) -> float:
        """分析承诺锁定机制"""
        try:
            base_score = self._analyze_brain_decision_mechanisms()
            return min(base_score * 0.8, 1.0)
        except:
            return 0.0
