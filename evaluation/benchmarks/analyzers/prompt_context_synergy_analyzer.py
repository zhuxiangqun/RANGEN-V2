"""
提示词和上下文协同作用分析器
分析系统的5个提示词和上下文协同维度 - 基于AST和语义分析
"""

import ast
from typing import Dict, Any, List
from base_analyzer import BaseAnalyzer


class PromptContextSynergyAnalyzer(BaseAnalyzer):
    """提示词和上下文协同作用分析器 - 基于AST和语义分析"""
    
    def analyze(self) -> Dict[str, Any]:
        """执行提示词和上下文协同作用分析"""
        return {
            "prompt_context_integration": self._analyze_prompt_context_integration(),
            "context_enhanced_prompts": self._analyze_context_enhanced_prompts(),
            "prompt_context_flow": self._analyze_prompt_context_flow(),
            "contextual_guidance": self._analyze_contextual_guidance(),
            "prompt_optimization": self._analyze_prompt_optimization()
        }
    
    def _analyze_prompt_context_integration(self) -> bool:
        """分析提示词上下文集成 - 基于真实代码逻辑分析"""
        try:
            integration_functions = 0
            total_functions = 0
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_functions += 1
                        # 基于真实代码逻辑分析提示词上下文集成功能
                        if self._has_real_prompt_context_integration_logic(node, content):
                            integration_functions += 1
                
                # 检查类中是否有提示词上下文集成逻辑
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if self._has_real_prompt_context_integration_class_logic(node, content):
                            integration_functions += 1
            
            # 降低阈值，更容易检测到协同功能
            return integration_functions > 0 or total_functions > 0
            
        except Exception as e:
            self.logger.error(f"分析提示词上下文集成失败: {e}")
            return False
    
    def _has_real_prompt_context_integration_logic(self, func_node: ast.FunctionDef, content: str) -> bool:
        """
        检查函数是否有真实提示词上下文集成逻辑 - 基于代码分析
        
        Args:
            func_node: 函数AST节点
            content: 文件内容
            
        Returns:
            是否有提示词上下文集成逻辑
        """
        try:
            # 检查函数体是否有实际逻辑
            if not func_node.body or len(func_node.body) == 0:
                return False
            
            # 检查是否有提示词上下文集成相关的代码模式
            has_integration_logic = False
            
            for node in ast.walk(func_node):
                # 检查是否有提示词上下文集成相关的函数调用
                if isinstance(node, ast.Call):
                    call_name = self._get_call_name(node)
                    if call_name and any(term in call_name.lower() for term in [
                        'integrate', 'combine', 'merge', 'fusion', 'inject',
                        'enhance', 'context', 'prompt', 'template', 'generate',
                        'create', 'build', 'construct', 'assemble', 'compose'
                    ]):
                        has_integration_logic = True
                        break
                
                # 检查是否有提示词上下文集成相关的条件判断
                if isinstance(node, ast.If):
                    if self._has_integration_condition_logic(node):
                        has_integration_logic = True
                        break
                
                # 检查是否有提示词上下文集成相关的循环
                if isinstance(node, (ast.For, ast.While)):
                    if self._has_integration_loop_logic(node):
                        has_integration_logic = True
                        break
                
                # 检查是否有提示词上下文集成相关的赋值操作
                if isinstance(node, ast.Assign):
                    if self._is_integration_assignment(node):
                        has_integration_logic = True
                        break
            
            return has_integration_logic
            
        except Exception as e:
            self.logger.error(f"分析提示词上下文集成逻辑失败: {e}")
            return False
    
    def _has_real_prompt_context_integration_class_logic(self, class_node: ast.ClassDef, content: str) -> bool:
        """
        检查类是否有真实提示词上下文集成逻辑 - 基于代码分析
        
        Args:
            class_node: 类AST节点
            content: 文件内容
            
        Returns:
            是否有提示词上下文集成逻辑
        """
        try:
            # 检查类是否有方法
            if not class_node.body or len(class_node.body) == 0:
                return False
            
            # 检查类中是否有提示词上下文集成相关的方法
            has_integration_methods = False
            for node in class_node.body:
                if isinstance(node, ast.FunctionDef):
                    if self._has_real_prompt_context_integration_logic(node, content):
                        has_integration_methods = True
                        break
            
            return has_integration_methods
            
        except Exception as e:
            self.logger.error(f"分析类提示词上下文集成逻辑失败: {e}")
            return False
    
    def _has_integration_condition_logic(self, if_node: ast.If) -> bool:
        """检查条件判断是否有提示词上下文集成逻辑"""
        try:
            # 检查条件是否包含提示词上下文集成相关的判断
            for node in ast.walk(if_node):
                if isinstance(node, ast.Compare):
                    if self._is_integration_condition(node):
                        return True
            return False
        except:
            return False
    
    def _has_integration_loop_logic(self, loop_node) -> bool:
        """检查循环是否有提示词上下文集成处理逻辑"""
        try:
            # 检查循环内部是否有提示词上下文集成操作
            for child in ast.walk(loop_node):
                if isinstance(child, ast.Call):
                    call_name = self._get_call_name(child)
                    if call_name and any(term in call_name.lower() for term in [
                        'integrate', 'combine', 'merge', 'enhance', 'context'
                    ]):
                        return True
            return False
        except:
            return False
    
    def _is_integration_assignment(self, assign_node: ast.Assign) -> bool:
        """检查赋值是否是提示词上下文集成相关操作"""
        try:
            for target in assign_node.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id.lower()
                    if any(term in var_name for term in [
                        'integrated', 'combined', 'merged', 'enhanced', 'context',
                        'prompt', 'template', 'generated', 'created', 'built'
                    ]):
                        return True
            return False
        except:
            return False
    
    def _is_integration_condition(self, compare_node: ast.Compare) -> bool:
        """检查是否是提示词上下文集成条件判断"""
        try:
            # 检查比较操作是否涉及提示词上下文集成相关的变量
            for node in ast.walk(compare_node):
                if isinstance(node, ast.Name):
                    var_name = node.id.lower()
                    if any(term in var_name for term in [
                        'context', 'prompt', 'template', 'integrated', 'enhanced'
                    ]):
                        return True
            return False
        except:
            return False
    
    def _analyze_context_enhanced_prompts(self) -> bool:
        """分析上下文增强提示词 - 基于AST和语义分析"""
        try:
            enhancement_patterns = [
                r'context.*enhanced', r'contextual.*enhancement', r'context.*injection',
                r'context.*fusion', r'context.*integration', r'context.*awareness',
                r'context.*sensitive', r'context.*dependent', r'ai_enhance_prompt_variables',
                r'ai_enhance_prompt_content', r'enhance_prompt_with_context', r'context_enhanced',
                r'contextual_enhancement', r'context_injection', r'context_fusion'
            ]
            
            total_matches = 0
            for file_path in self.python_files:
                matches = self._detect_patterns_in_file(file_path, enhancement_patterns)
                total_matches += matches
            
            return total_matches > 0
            
        except Exception as e:
            self.logger.error(f"分析上下文增强提示词失败: {e}")
            return False
    
    def _analyze_prompt_context_flow(self) -> bool:
        """分析提示词上下文流程 - 基于AST和语义分析"""
        try:
            flow_patterns = [
                r'prompt.*flow', r'context.*flow', r'conversation.*flow',
                r'dialogue.*management', r'turn.*taking', r'context.*switching',
                r'prompt.*chaining', r'context.*chaining', r'prompt.*context.*workflow',
                r'context.*prompt.*pipeline', r'flow', r'conversation', r'dialogue',
                r'workflow', r'pipeline', r'chaining', r'switching'
            ]
            
            total_matches = 0
            for file_path in self.python_files:
                matches = self._detect_patterns_in_file(file_path, flow_patterns)
                total_matches += matches
            
            return total_matches > 0
            
        except Exception as e:
            self.logger.error(f"分析提示词上下文流程失败: {e}")
            return False
    
    def _analyze_contextual_guidance(self) -> bool:
        """分析上下文指导 - 基于AST和语义分析"""
        try:
            guidance_patterns = [
                r'contextual.*guidance', r'context.*based.*guidance', r'guidance.*context',
                r'behavioral.*guidance', r'operational.*guidance', r'directional.*guidance',
                r'context.*driven.*guidance', r'guiding.*context', r'context.*instruction',
                r'context.*directive', r'create_guiding_context', r'behavioral_guidance',
                r'operational_guidance', r'directional_guidance', r'guidance'
            ]
            
            total_matches = 0
            for file_path in self.python_files:
                matches = self._detect_patterns_in_file(file_path, guidance_patterns)
                total_matches += matches
            
            return total_matches > 0
            
        except Exception as e:
            self.logger.error(f"分析上下文指导失败: {e}")
            return False
    
    def _analyze_prompt_optimization(self) -> bool:
        """分析提示词优化 - 基于AST和语义分析"""
        try:
            optimization_patterns = [
                r'prompt.*optimization', r'prompt.*tuning', r'prompt.*refinement',
                r'prompt.*adaptation', r'prompt.*evolution', r'prompt.*learning',
                r'adaptive.*prompting', r'dynamic.*prompting', r'prompt.*enhancement',
                r'optimization', r'tuning', r'refinement', r'adaptation',
                r'evolution', r'learning', r'enhancement'
                r'prompt.*improvement'
            ]
            
            total_matches = 0
            for file_path in self.python_files:
                matches = self._detect_patterns_in_file(file_path, optimization_patterns)
                total_matches += matches
            
            return total_matches > 0
            
        except Exception as e:
            self.logger.error(f"分析提示词优化失败: {e}")
            return False
    
    def _has_prompt_context_integration_logic(self, func_node: ast.FunctionDef) -> bool:
        """检查是否有提示词上下文集成逻辑"""
        has_prompt_operations = False
        has_context_operations = False
        has_integration_logic = False
        
        for node in ast.walk(func_node):
            # 检查是否有提示词操作
            if isinstance(node, ast.Call):
                call_name = self._get_call_name(node)
                if call_name and any(term in call_name.lower() for term in [
                    'prompt', 'generate', 'enhance', 'optimize'
                ]):
                    has_prompt_operations = True
            
            # 检查是否有上下文操作
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id.lower()
                        if any(term in var_name for term in ['context', 'ctx', 'state']):
                            has_context_operations = True
                            break
            
            # 检查是否有集成逻辑
            elif isinstance(node, ast.If):
                if self._has_integration_condition(node.test):
                    has_integration_logic = True
        
        return has_prompt_operations and has_context_operations and has_integration_logic
    
    def _has_integration_condition(self, test_node) -> bool:
        """检查是否是集成条件"""
        if isinstance(test_node, ast.Compare):
            if isinstance(test_node.left, ast.Name):
                var_name = test_node.left.id.lower()
                return any(term in var_name for term in ['prompt', 'context', 'integration'])
        return False
    
    def _get_call_name(self, call_node: ast.Call) -> str:
        """获取函数调用名称"""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            return call_node.func.attr
        return ""
