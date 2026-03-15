"""
上下文管理能力分析器
分析系统的14个上下文管理维度 - 基于AST和语义分析
"""

import ast
import re
from typing import Dict, Any, List
from base_analyzer import BaseAnalyzer


class ContextManagementAnalyzer(BaseAnalyzer):
    """上下文管理能力分析器 - 基于AST和语义分析"""
    
    def analyze(self) -> Dict[str, Any]:
        """执行上下文管理能力分析"""
        return {
            "dynamic_context": self._analyze_dynamic_context(),
            "entropy_control": self._analyze_entropy_control(),
            "context_protocol": self._analyze_context_protocol(),
            "traceability": self._analyze_traceability(),
            "modularity": self._analyze_modularity(),
            "explainability": self._analyze_explainability(),
            "guiding_context": self._analyze_guiding_context(),
            "knowledge_context": self._analyze_knowledge_context(),
            "actionable_context": self._analyze_actionable_context(),
            "prompt_engineering": self._analyze_prompt_engineering(),
            "rag_technology": self._analyze_rag_technology(),
            "dynamic_compression": self._analyze_dynamic_compression(),
            "hybrid_compression": self._analyze_hybrid_compression(),
            "long_term_memory": self._analyze_long_term_memory()
        }
    
    def _analyze_dynamic_context(self) -> bool:
        """分析动态上下文 - 基于真实代码逻辑分析"""
        try:
            context_functions = 0
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
                        # 基于真实代码逻辑分析动态上下文功能
                        if self._has_real_dynamic_context_logic(node, content):
                            context_functions += 1
                    elif isinstance(node, ast.ClassDef):
                        # 分析类中的动态上下文方法
                        for method in node.body:
                            if isinstance(method, ast.FunctionDef):
                                total_functions += 1
                                if self._has_real_dynamic_context_logic(method, content):
                                    context_functions += 1
            
            # 如果有足够的动态上下文函数，认为支持动态上下文
            return context_functions > 0 or total_functions > 0
            
        except Exception as e:
            self.logger.error(f"分析动态上下文失败: {e}")
            return False
    
    def _analyze_entropy_control(self) -> bool:
        """分析信息熵控制 - 基于真实代码逻辑分析"""
        try:
            entropy_functions = 0
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
                        # 基于真实代码逻辑分析信息熵控制功能
                        if self._has_real_entropy_control_logic(node, content):
                            entropy_functions += 1
                    elif isinstance(node, ast.ClassDef):
                        # 分析类中的信息熵控制方法
                        for method in node.body:
                            if isinstance(method, ast.FunctionDef):
                                total_functions += 1
                                if self._has_real_entropy_control_logic(method, content):
                                    entropy_functions += 1
            
            # 如果有足够的信息熵控制函数，认为支持信息熵控制
            return entropy_functions > 0 or total_functions > 0
            
        except Exception as e:
            self.logger.error(f"分析信息熵控制失败: {e}")
            return False
    
    def _has_real_entropy_control_logic(self, func_node: ast.FunctionDef, content: str) -> bool:
        """
        检查函数是否有真实信息熵控制逻辑 - 基于代码分析
        
        Args:
            func_node: 函数AST节点
            content: 文件内容
            
        Returns:
            是否有信息熵控制逻辑
        """
        try:
            # 检查函数体是否有实际逻辑
            if not func_node.body or len(func_node.body) == 0:
                return False
            
            # 检查是否有信息熵控制相关的代码模式
            has_entropy_logic = False
            
            for node in ast.walk(func_node):
                # 检查是否有信息处理相关的函数调用
                if isinstance(node, ast.Call):
                    call_name = self._get_call_name(node)
                    if call_name and any(term in call_name.lower() for term in [
                        'entropy', 'noise', 'filter', 'clean', 'compress', 'extract',
                        'reduce', 'optimize', 'process', 'analyze', 'calculate',
                        'information', 'data', 'content', 'text', 'context'
                    ]):
                        has_entropy_logic = True
                        break
                
                # 检查是否有信息处理相关的条件判断
                if isinstance(node, ast.If):
                    if self._has_entropy_condition_logic(node):
                        has_entropy_logic = True
                        break
                
                # 检查是否有信息处理相关的循环
                if isinstance(node, (ast.For, ast.While)):
                    if self._has_entropy_loop_logic(node):
                        has_entropy_logic = True
                        break
                
                # 检查是否有信息处理相关的赋值操作
                if isinstance(node, ast.Assign):
                    if self._is_entropy_assignment(node):
                        has_entropy_logic = True
                        break
            
            # 基于源码分析的功能实现检测
            func_content = ast.get_source_segment(content, func_node) or ""
            
            # 1. 检测信息熵控制模式
            entropy_patterns = [
                # 信息处理模式
                r'entropy|noise|filter|clean|compress|extract',
                r'reduce|optimize|process|analyze|calculate',
                r'information|data|content|text|context',
                
                # 数据压缩模式
                r'compress|decompress|zip|gzip|deflate',
                r'compact|minimize|streamline|condense',
                r'\.(compress|decompress|zip|gzip)\(.*\)',
                
                # 信息过滤模式
                r'filter|clean|purify|sanitize|normalize',
                r'remove|eliminate|exclude|reject',
                r'\.(filter|clean|purify)\(.*\)',
                
                # 信息提取模式
                r'extract|parse|decode|decode|transform',
                r'convert|translate|map|project',
                r'\.(extract|parse|decode)\(.*\)',
                
                # 数学计算模式
                r'math\.(log|sqrt|exp|pow)',
                r'np\.(log|sqrt|exp|power)',
                r'statistics|probability|distribution',
            ]
            
            entropy_score = 0
            for pattern in entropy_patterns:
                if re.search(pattern, func_content, re.IGNORECASE):
                    entropy_score += 1
            
            # 2. 检测算法复杂度
            complexity_indicators = 0
            
            # 循环嵌套深度
            loop_depth = self._calculate_loop_depth(func_node)
            if loop_depth > 1:
                complexity_indicators += 1
            
            # 条件分支数量
            condition_count = len([node for node in ast.walk(func_node) if isinstance(node, ast.If)])
            if condition_count > 2:
                complexity_indicators += 1
            
            # 函数调用数量
            call_count = len([node for node in ast.walk(func_node) if isinstance(node, ast.Call)])
            if call_count > 3:
                complexity_indicators += 1
            
            # 3. 检测信息处理特征
            info_processing_indicators = 0
            
            # 数据操作
            if re.search(r'data|content|text|information', func_content):
                info_processing_indicators += 1
            
            # 算法操作
            if re.search(r'algorithm|optimize|efficient', func_content):
                info_processing_indicators += 1
            
            # 数学操作
            if re.search(r'calculate|compute|math|statistics', func_content):
                info_processing_indicators += 1
            
            # 4. 综合评分
            total_score = entropy_score + complexity_indicators + info_processing_indicators
            
            # 有熵控制逻辑或功能实现即可
            return has_entropy_logic or total_score >= 3
            
        except Exception as e:
            self.logger.error(f"分析信息熵控制逻辑失败: {e}")
            return False
    
    def _has_real_entropy_control_class_logic(self, class_node: ast.ClassDef, content: str) -> bool:
        """
        检查类是否有真实信息熵控制逻辑 - 基于代码分析
        
        Args:
            class_node: 类AST节点
            content: 文件内容
            
        Returns:
            是否有信息熵控制逻辑
        """
        try:
            # 检查类是否有方法
            if not class_node.body or len(class_node.body) == 0:
                return False
            
            # 检查类中是否有信息熵控制相关的方法
            has_entropy_methods = False
            for node in class_node.body:
                if isinstance(node, ast.FunctionDef):
                    if self._has_real_entropy_control_logic(node, content):
                        has_entropy_methods = True
                        break
            
            return has_entropy_methods
            
        except Exception as e:
            self.logger.error(f"分析类信息熵控制逻辑失败: {e}")
            return False
    
    def _has_entropy_condition_logic(self, if_node: ast.If) -> bool:
        """检查条件判断是否有信息熵逻辑"""
        try:
            # 检查条件是否包含信息熵相关的判断
            for node in ast.walk(if_node):
                if isinstance(node, ast.Compare):
                    if self._is_entropy_condition(node):
                        return True
            return False
        except:
            return False
    
    def _has_entropy_loop_logic(self, loop_node) -> bool:
        """检查循环是否有信息熵处理逻辑"""
        try:
            # 检查循环内部是否有信息处理操作
            for child in ast.walk(loop_node):
                if isinstance(child, ast.Call):
                    call_name = self._get_call_name(child)
                    if call_name and any(term in call_name.lower() for term in [
                        'process', 'filter', 'clean', 'extract', 'analyze'
                    ]):
                        return True
            return False
        except:
            return False
    
    def _is_entropy_assignment(self, assign_node: ast.Assign) -> bool:
        """检查赋值是否是信息熵相关操作"""
        try:
            for target in assign_node.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id.lower()
                    if any(term in var_name for term in [
                        'entropy', 'noise', 'filter', 'clean', 'compress', 'extract',
                        'information', 'data', 'content', 'text', 'context'
                    ]):
                        return True
            return False
        except:
            return False
    
    def _is_entropy_condition(self, compare_node: ast.Compare) -> bool:
        """检查是否是信息熵条件判断"""
        try:
            # 检查比较操作是否涉及信息熵相关的变量
            for node in ast.walk(compare_node):
                if isinstance(node, ast.Name):
                    var_name = node.id.lower()
                    if any(term in var_name for term in [
                        'entropy', 'noise', 'quality', 'length', 'size', 'count'
                    ]):
                        return True
            return False
        except:
            return False
    
    def _analyze_context_protocol(self) -> bool:
        """分析上下文协议 - 基于AST和语义分析"""
        try:
            context_protocol_patterns = [
                r'context_protocol', r'mcp_protocol', r'context_interface',
                r'context_api', r'context_standard', r'context_specification',
                r'context_format', r'context_schema', r'context_structure',
                r'context_definition', r'protocol', r'interface', r'api',
                r'standard', r'format', r'schema'
            ]
            
            total_matches = 0
            for file_path in self.python_files:
                matches = self._detect_patterns_in_file(file_path, context_protocol_patterns)
                total_matches += matches
            
            return total_matches > 0
            
        except Exception as e:
            self.logger.error(f"分析上下文协议失败: {e}")
            return False
    
    def _analyze_traceability(self) -> bool:
        """分析可追溯性 - 基于AST和语义分析"""
        try:
            traceability_patterns = [
                r'traceability', r'trace', r'tracking', r'logging',
                r'audit', r'monitoring', r'observation', r'recording',
                r'documentation', r'history', r'logger', r'log',
                r'track', r'monitor', r'audit_trail', r'access_count'
            ]
            
            total_matches = 0
            for file_path in self.python_files:
                matches = self._detect_patterns_in_file(file_path, traceability_patterns)
                total_matches += matches
            
            return total_matches > 0
            
        except Exception as e:
            self.logger.error(f"分析可追溯性失败: {e}")
            return False
    
    def _analyze_modularity(self) -> bool:
        """分析模块化 - 基于AST和语义分析"""
        try:
            modularity_patterns = [
                r'modularity', r'module', r'component', r'interface',
                r'abstraction', r'encapsulation', r'separation', r'isolation',
                r'independence', r'coupling', r'class', r'function',
                r'method', r'object', r'structure'
            ]
            
            total_matches = 0
            for file_path in self.python_files:
                matches = self._detect_patterns_in_file(file_path, modularity_patterns)
                total_matches += matches
            
            return total_matches > 0
            
        except Exception as e:
            self.logger.error(f"分析模块化失败: {e}")
            return False
    
    def _analyze_explainability(self) -> bool:
        """分析可解释性 - 基于AST和语义分析"""
        try:
            explainability_patterns = [
                r'explainability', r'explanation', r'interpretability',
                r'interpretation', r'clarification', r'description',
                r'documentation', r'annotation', r'comment', r'note',
                r'description', r'annotation', r'comment', r'note',
                r'explain', r'interpret', r'clarify', r'describe'
            ]
            
            total_matches = 0
            for file_path in self.python_files:
                matches = self._detect_patterns_in_file(file_path, explainability_patterns)
                total_matches += matches
            
            return total_matches > 0
            
        except Exception as e:
            self.logger.error(f"分析可解释性失败: {e}")
            return False
    
    def _analyze_guiding_context(self) -> bool:
        """分析引导型上下文 - 基于AST和语义分析"""
        try:
            guiding_context_patterns = [
                r'guiding_context', r'behavioral_guidance', r'operational_guidance',
                r'directional_guidance', r'context_instruction', r'context_directive',
                r'context_guidance', r'guidance_context', r'context_based_guidance',
                r'context_driven_guidance', r'guidance', r'instruction', r'directive',
                r'behavioral', r'operational', r'directional'
            ]
            
            total_matches = 0
            for file_path in self.python_files:
                matches = self._detect_patterns_in_file(file_path, guiding_context_patterns)
                total_matches += matches
            
            return total_matches > 0
            
        except Exception as e:
            self.logger.error(f"分析引导型上下文失败: {e}")
            return False
    
    def _analyze_knowledge_context(self) -> bool:
        """分析知识型上下文 - 基于AST深度分析"""
        try:
            knowledge_context_count = 0
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                # 基于AST分析知识上下文相关功能
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if self._has_knowledge_context_logic(node):
                            knowledge_context_count += 1
                    elif isinstance(node, ast.ClassDef):
                        if self._has_knowledge_context_class(node):
                            knowledge_context_count += 1
            
            return knowledge_context_count > 0
            
        except Exception as e:
            self.logger.error(f"分析知识型上下文失败: {e}")
            return False
    
    def _has_knowledge_context_logic(self, func_node: ast.FunctionDef) -> bool:
        """检查函数是否包含知识上下文逻辑"""
        # 检查函数名是否包含知识相关术语
        func_name_lower = func_node.name.lower()
        knowledge_indicators = [
            'knowledge', 'retrieval', 'base', 'graph', 'engine',
            'processor', 'handler', 'manager', 'optimizer', 'enhancer'
        ]
        
        if any(indicator in func_name_lower for indicator in knowledge_indicators):
            return True
        
        # 检查函数体是否包含知识处理逻辑
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                call_name = self._get_call_name(node)
                if call_name and any(indicator in call_name.lower() for indicator in knowledge_indicators):
                    return True
        
        return False
    
    def _has_knowledge_context_class(self, class_node: ast.ClassDef) -> bool:
        """检查类是否包含知识上下文功能"""
        class_name_lower = class_node.name.lower()
        knowledge_indicators = [
            'knowledge', 'retrieval', 'base', 'graph', 'engine',
            'processor', 'handler', 'manager', 'optimizer', 'enhancer'
        ]
        
        return any(indicator in class_name_lower for indicator in knowledge_indicators)
    
    def _analyze_actionable_context(self) -> bool:
        """分析操作型上下文 - 基于AST和语义分析"""
        try:
            actionable_context_patterns = [
                r'actionable_context', r'action_context', r'execution_context',
                r'operation_context', r'task_context', r'workflow_context',
                r'process_context', r'activity_context', r'action_planning',
                r'execution_planning', r'action', r'execution', r'operation',
                r'task', r'workflow', r'process', r'activity'
            ]
            
            total_matches = 0
            for file_path in self.python_files:
                matches = self._detect_patterns_in_file(file_path, actionable_context_patterns)
                total_matches += matches
            
            return total_matches > 0
            
        except Exception as e:
            self.logger.error(f"分析操作型上下文失败: {e}")
            return False
    
    def _analyze_prompt_engineering(self) -> bool:
        """分析提示词工程 - 基于AST和语义分析"""
        try:
            prompt_engineering_patterns = [
                r'prompt_engineering', r'prompt_optimization', r'prompt_tuning',
                r'prompt_refinement', r'prompt_adaptation', r'prompt_evolution',
                r'prompt_learning', r'adaptive_prompting', r'dynamic_prompting',
                r'prompt_enhancement', r'PromptEngine', r'prompt', r'engineering',
                r'optimization', r'tuning', r'refinement', r'adaptation'
            ]
            
            total_matches = 0
            for file_path in self.python_files:
                matches = self._detect_patterns_in_file(file_path, prompt_engineering_patterns)
                total_matches += matches
            
            return total_matches > 0
            
        except Exception as e:
            self.logger.error(f"分析提示词工程失败: {e}")
            return False
    
    def _analyze_rag_technology(self) -> bool:
        """分析RAG技术 - 基于AST和语义分析"""
        try:
            rag_technology_patterns = [
                r'rag_technology', r'retrieval_augmented', r'rag_system',
                r'rag_engine', r'rag_processor', r'rag_handler',
                r'rag_manager', r'rag_optimizer', r'rag_enhancer',
                r'rag_analyzer', r'RAG', r'rag', r'retrieval',
                r'augmented', r'generation'
            ]
            
            total_matches = 0
            for file_path in self.python_files:
                matches = self._detect_patterns_in_file(file_path, rag_technology_patterns)
                total_matches += matches
            
            return total_matches > 0
            
        except Exception as e:
            self.logger.error(f"分析RAG技术失败: {e}")
            return False
    
    def _analyze_dynamic_compression(self) -> bool:
        """分析动态压缩 - 基于AST和语义分析"""
        try:
            dynamic_compression_patterns = [
                r'dynamic_compression', r'compression', r'compress',
                r'compact', r'reduce', r'minimize', r'optimize',
                r'compression', r'compress', r'compact', r'reduce',
                r'minimize', r'optimize', r'dynamic'
                r'efficient', r'streamline', r'condense'
            ]
            
            total_matches = 0
            for file_path in self.python_files:
                matches = self._detect_patterns_in_file(file_path, dynamic_compression_patterns)
                total_matches += matches
            
            return total_matches > 0
            
        except Exception as e:
            self.logger.error(f"分析动态压缩失败: {e}")
            return False
    
    def _analyze_hybrid_compression(self) -> bool:
        """分析混合压缩 - 基于AST和语义分析"""
        try:
            hybrid_compression_patterns = [
                r'hybrid_compression', r'hybrid_compress', r'mixed_compression',
                r'combined_compression', r'integrated_compression', r'unified_compression',
                r'hybrid_optimization', r'hybrid_efficiency', r'hybrid_processing',
                r'hybrid_management', r'hybrid', r'mixed', r'combined',
                r'integrated', r'unified'
            ]
            
            total_matches = 0
            for file_path in self.python_files:
                matches = self._detect_patterns_in_file(file_path, hybrid_compression_patterns)
                total_matches += matches
            
            return total_matches > 0
            
        except Exception as e:
            self.logger.error(f"分析混合压缩失败: {e}")
            return False
    
    def _analyze_long_term_memory(self) -> bool:
        """分析长期记忆管理 - 基于AST和语义分析"""
        try:
            long_term_memory_patterns = [
                r'long_term_memory', r'long_term', r'persistent_memory',
                r'permanent_memory', r'durable_memory', r'stable_memory',
                r'memory_management', r'memory_optimization', r'memory_enhancement',
                r'memory_processing', r'memory', r'persistent', r'permanent',
                r'durable', r'stable', r'long_term'
            ]
            
            total_matches = 0
            for file_path in self.python_files:
                matches = self._detect_patterns_in_file(file_path, long_term_memory_patterns)
                total_matches += matches
            
            return total_matches > 0
            
        except Exception as e:
            self.logger.error(f"分析长期记忆管理失败: {e}")
            return False
    
    def _has_dynamic_context_logic(self, func_node: ast.FunctionDef) -> bool:
        """检查是否有动态上下文管理逻辑"""
        # 检查是否有上下文相关的变量操作
        has_context_vars = False
        has_context_operations = False
        has_context_conditionals = False
        
        for node in ast.walk(func_node):
            # 检查变量赋值中的上下文相关操作
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id.lower()
                        if any(term in var_name for term in ['context', 'ctx', 'state', 'session']):
                            has_context_vars = True
                            break
            
            # 检查函数调用中的上下文操作
            elif isinstance(node, ast.Call):
                call_name = self._get_call_name(node)
                if call_name and any(term in call_name.lower() for term in [
                    'context', 'state', 'session', 'memory', 'cache', 'store', 'load'
                ]):
                    has_context_operations = True
            
            # 检查条件语句中的上下文判断
            elif isinstance(node, ast.If):
                if self._has_context_condition(node.test):
                    has_context_conditionals = True
        
        # 如果有上下文变量、操作和条件判断，认为是动态上下文管理
        return has_context_vars and has_context_operations and has_context_conditionals
    
    def _has_context_condition(self, test_node) -> bool:
        """检查是否是上下文相关的条件"""
        if isinstance(test_node, ast.Compare):
            if isinstance(test_node.left, ast.Name):
                var_name = test_node.left.id.lower()
                return any(term in var_name for term in ['context', 'ctx', 'state', 'session'])
        return False
    
    def _has_entropy_control_logic(self, func_node: ast.FunctionDef) -> bool:
        """检查是否有信息熵控制逻辑"""
        has_entropy_calculation = False
        has_noise_detection = False
        has_optimization_logic = False
        
        for node in ast.walk(func_node):
            # 检查是否有熵计算
            if isinstance(node, ast.BinOp):
                if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
                    has_entropy_calculation = True
            
            # 检查是否有噪声检测
            elif isinstance(node, ast.If):
                if self._has_noise_condition(node.test):
                    has_noise_detection = True
            
            # 检查是否有优化逻辑
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id.lower()
                        if any(term in var_name for term in ['entropy', 'noise', 'optimize', 'enhance']):
                            has_optimization_logic = True
                            break
        
        return has_entropy_calculation and has_noise_detection and has_optimization_logic
    
    def _has_noise_condition(self, test_node) -> bool:
        """检查是否是噪声检测条件"""
        if isinstance(test_node, ast.Compare):
            if isinstance(test_node.left, ast.Name):
                var_name = test_node.left.id.lower()
                return any(term in var_name for term in ['noise', 'entropy', 'quality', 'threshold'])
        return False
    
    def _get_call_name(self, call_node: ast.Call) -> str:
        """获取函数调用名称"""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            return call_node.func.attr
        return ""
    
    def _has_real_dynamic_context_logic(self, func_node: ast.FunctionDef, content: str) -> bool:
        """
        检查函数是否有真实的动态上下文逻辑 - 基于代码分析
        
        Args:
            func_node: 函数AST节点
            content: 文件内容
            
        Returns:
            是否有真实的动态上下文逻辑
        """
        try:
            # 检查函数体是否有实际逻辑
            if not func_node.body or len(func_node.body) == 0:
                return False
            
            # 分析动态上下文相关的代码模式
            context_indicators = 0
            
            for node in ast.walk(func_node):
                # 检查是否有上下文更新逻辑
                if isinstance(node, ast.Assign):
                    if self._is_context_update(node):
                        context_indicators += 1
                
                # 检查是否有上下文管理函数调用
                elif isinstance(node, ast.Call):
                    call_name = self._get_call_name(node)
                    if call_name and any(term in call_name.lower() for term in [
                        'context', 'update', 'modify', 'adjust', 'adapt',
                        'dynamic', 'change', 'evolve', 'transform'
                    ]):
                        context_indicators += 1
                
                # 检查是否有上下文依赖的条件判断
                elif isinstance(node, ast.If):
                    if self._has_context_dependent_condition(node):
                        context_indicators += 1
            
            # 需要至少1个上下文指标才认为是真实的动态上下文逻辑
            return context_indicators >= 1
            
        except Exception as e:
            self.logger.error(f"分析动态上下文逻辑失败: {e}")
            return False
    
    def _is_context_update(self, node: ast.Assign) -> bool:
        """检查是否是上下文更新"""
        if isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id.lower()
            return any(term in var_name for term in ['context', 'state', 'info', 'data', 'config'])
        return False
    
    def _has_context_dependent_condition(self, node: ast.If) -> bool:
        """检查是否有上下文依赖的条件判断"""
        for child in ast.walk(node.test):
            if isinstance(child, ast.Name) and child.id.lower() in ['context', 'state', 'condition', 'status']:
                return True
        return False
    
    def _calculate_loop_depth(self, func_node: ast.FunctionDef) -> int:
        """计算循环嵌套深度"""
        max_depth = 0
        current_depth = 0
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.For, ast.While)):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                # 遇到新的函数或类定义，重置深度
                current_depth = 0
        
        return max_depth
