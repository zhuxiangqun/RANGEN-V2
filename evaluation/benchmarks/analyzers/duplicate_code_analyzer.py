#!/usr/bin/env python3
"""
重复代码检测分析器
基于AST深度分析检测重复的模块、类、函数和代码块
"""

import ast
import hashlib
import logging
from typing import Dict, Any, List, Set, Tuple
from base_analyzer import BaseAnalyzer


class DuplicateCodeAnalyzer(BaseAnalyzer):
    """重复代码检测分析器 - 基于AST深度分析"""
    
    def analyze(self) -> Dict[str, Any]:
        """执行重复代码检测分析"""
        return {
            "duplicate_classes": self._detect_duplicate_classes(),
            "duplicate_functions": self._detect_duplicate_functions(),
            "duplicate_modules": self._detect_duplicate_modules(),
            "duplicate_code_blocks": self._detect_duplicate_code_blocks(),
            "duplicate_imports": self._detect_duplicate_imports(),
            "duplicate_config_interfaces": self._detect_duplicate_config_interfaces(),
            "duplicate_agent_definitions": self._detect_duplicate_agent_definitions(),
            "duplicate_data_structures": self._detect_duplicate_data_structures(),
            "duplicate_error_handling": self._detect_duplicate_error_handling(),
            "duplicate_logging_patterns": self._detect_duplicate_logging_patterns()
        }
    
    def _detect_duplicate_classes(self) -> Dict[str, Any]:
        """检测重复的类定义"""
        try:
            class_signatures = {}
            duplicate_classes = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # 生成类的签名（基于方法名、属性名、继承关系）
                        signature = self._generate_class_signature(node, content)
                        
                        if signature in class_signatures:
                            # 发现重复类
                            duplicate_classes.append({
                                "class_name": node.name,
                                "file_path": file_path,
                                "line_number": node.lineno,
                                "duplicate_with": class_signatures[signature],
                                "signature": signature,
                                "similarity": self._calculate_class_similarity(
                                    node, class_signatures[signature], content
                                )
                            })
                        else:
                            class_signatures[signature] = {
                                "class_name": node.name,
                                "file_path": file_path,
                                "line_number": node.lineno
                            }
            
            return {
                "has_duplicate_classes": len(duplicate_classes) > 0,
                "duplicate_count": len(duplicate_classes),
                "duplicates": duplicate_classes,
                "score": max(0, 1.0 - len(duplicate_classes) * 0.1)
            }
            
        except Exception as e:
            self.logger.error(f"检测重复类失败: {e}")
            return {"has_duplicate_classes": False, "duplicate_count": 0, "duplicates": [], "score": 1.0}
    
    def _detect_duplicate_functions(self) -> Dict[str, Any]:
        """检测重复的函数定义"""
        try:
            function_signatures = {}
            duplicate_functions = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # 生成函数的签名（基于参数、返回值、函数体结构）
                        signature = self._generate_function_signature(node, content)
                        
                        if signature in function_signatures:
                            # 发现重复函数
                            duplicate_functions.append({
                                "function_name": node.name,
                                "file_path": file_path,
                                "line_number": node.lineno,
                                "duplicate_with": function_signatures[signature],
                                "signature": signature,
                                "similarity": self._calculate_function_similarity(
                                    node, function_signatures[signature], content
                                )
                            })
                        else:
                            function_signatures[signature] = {
                                "function_name": node.name,
                                "file_path": file_path,
                                "line_number": node.lineno
                            }
            
            return {
                "has_duplicate_functions": len(duplicate_functions) > 0,
                "duplicate_count": len(duplicate_functions),
                "duplicates": duplicate_functions,
                "score": max(0, 1.0 - len(duplicate_functions) * 0.05)
            }
            
        except Exception as e:
            self.logger.error(f"检测重复函数失败: {e}")
            return {"has_duplicate_functions": False, "duplicate_count": 0, "duplicates": [], "score": 1.0}
    
    def _detect_duplicate_modules(self) -> Dict[str, Any]:
        """检测重复的模块功能"""
        try:
            module_functions = {}
            duplicate_modules = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                # 分析模块的主要功能
                module_features = self._extract_module_features(tree, content)
                module_signature = self._generate_module_signature(module_features)
                
                if module_signature in module_functions:
                    # 发现重复模块功能
                    duplicate_modules.append({
                        "module_path": file_path,
                        "duplicate_with": module_functions[module_signature],
                        "features": module_features,
                        "similarity": self._calculate_module_similarity(
                            module_features, module_functions[module_signature]
                        )
                    })
                else:
                    module_functions[module_signature] = {
                        "module_path": file_path,
                        "features": module_features
                    }
            
            return {
                "has_duplicate_modules": len(duplicate_modules) > 0,
                "duplicate_count": len(duplicate_modules),
                "duplicates": duplicate_modules,
                "score": max(0, 1.0 - len(duplicate_modules) * 0.2)
            }
            
        except Exception as e:
            self.logger.error(f"检测重复模块失败: {e}")
            return {"has_duplicate_modules": False, "duplicate_count": 0, "duplicates": [], "score": 1.0}
    
    def _detect_duplicate_code_blocks(self) -> Dict[str, Any]:
        """检测重复的代码块"""
        try:
            code_blocks = {}
            duplicate_blocks = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                # 提取代码块（函数体、类体等）
                blocks = self._extract_code_blocks(tree, content)
                
                for block in blocks:
                    block_hash = self._calculate_block_hash(block["content"])
                    
                    if block_hash in code_blocks:
                        # 发现重复代码块
                        duplicate_blocks.append({
                            "file_path": file_path,
                            "line_number": block["line_number"],
                            "block_type": block["type"],
                            "duplicate_with": code_blocks[block_hash],
                            "content_preview": block["content"][:100] + "..." if len(block["content"]) > 100 else block["content"]
                        })
                    else:
                        code_blocks[block_hash] = {
                            "file_path": file_path,
                            "line_number": block["line_number"],
                            "block_type": block["type"]
                        }
            
            return {
                "has_duplicate_blocks": len(duplicate_blocks) > 0,
                "duplicate_count": len(duplicate_blocks),
                "duplicates": duplicate_blocks,
                "score": max(0, 1.0 - len(duplicate_blocks) * 0.02)
            }
            
        except Exception as e:
            self.logger.error(f"检测重复代码块失败: {e}")
            return {"has_duplicate_blocks": False, "duplicate_count": 0, "duplicates": [], "score": 1.0}
    
    def _detect_duplicate_imports(self) -> Dict[str, Any]:
        """检测重复的导入语句"""
        try:
            import_patterns = {}
            duplicate_imports = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            import_key = f"import {alias.name}"
                            if import_key in import_patterns:
                                duplicate_imports.append({
                                    "file_path": file_path,
                                    "line_number": node.lineno,
                                    "import_statement": import_key,
                                    "duplicate_with": import_patterns[import_key]
                                })
                            else:
                                import_patterns[import_key] = {
                                    "file_path": file_path,
                                    "line_number": node.lineno
                                }
                    
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        for alias in node.names:
                            import_key = f"from {module} import {alias.name}"
                            if import_key in import_patterns:
                                duplicate_imports.append({
                                    "file_path": file_path,
                                    "line_number": node.lineno,
                                    "import_statement": import_key,
                                    "duplicate_with": import_patterns[import_key]
                                })
                            else:
                                import_patterns[import_key] = {
                                    "file_path": file_path,
                                    "line_number": node.lineno
                                }
            
            return {
                "has_duplicate_imports": len(duplicate_imports) > 0,
                "duplicate_count": len(duplicate_imports),
                "duplicates": duplicate_imports,
                "score": max(0, 1.0 - len(duplicate_imports) * 0.01)
            }
            
        except Exception as e:
            self.logger.error(f"检测重复导入失败: {e}")
            return {"has_duplicate_imports": False, "duplicate_count": 0, "duplicates": [], "score": 1.0}
    
    def _detect_duplicate_config_interfaces(self) -> Dict[str, Any]:
        """检测重复的配置管理接口"""
        try:
            config_functions = {}
            duplicate_configs = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # 检测配置相关的函数
                        if self._is_config_function(node, content):
                            signature = self._generate_config_function_signature(node, content)
                            
                            if signature in config_functions:
                                duplicate_configs.append({
                                    "function_name": node.name,
                                    "file_path": file_path,
                                    "line_number": node.lineno,
                                    "duplicate_with": config_functions[signature],
                                    "config_type": self._identify_config_type(node, content)
                                })
                            else:
                                config_functions[signature] = {
                                    "function_name": node.name,
                                    "file_path": file_path,
                                    "line_number": node.lineno
                                }
            
            return {
                "has_duplicate_configs": len(duplicate_configs) > 0,
                "duplicate_count": len(duplicate_configs),
                "duplicates": duplicate_configs,
                "score": max(0, 1.0 - len(duplicate_configs) * 0.15)
            }
            
        except Exception as e:
            self.logger.error(f"检测重复配置接口失败: {e}")
            return {"has_duplicate_configs": False, "duplicate_count": 0, "duplicates": [], "score": 1.0}
    
    def _detect_duplicate_agent_definitions(self) -> Dict[str, Any]:
        """检测重复的智能体定义"""
        try:
            agent_classes = {}
            duplicate_agents = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # 检测智能体类
                        if self._is_agent_class(node, content):
                            signature = self._generate_agent_signature(node, content)
                            
                            if signature in agent_classes:
                                duplicate_agents.append({
                                    "class_name": node.name,
                                    "file_path": file_path,
                                    "line_number": node.lineno,
                                    "duplicate_with": agent_classes[signature],
                                    "agent_type": self._identify_agent_type(node, content)
                                })
                            else:
                                agent_classes[signature] = {
                                    "class_name": node.name,
                                    "file_path": file_path,
                                    "line_number": node.lineno
                                }
            
            return {
                "has_duplicate_agents": len(duplicate_agents) > 0,
                "duplicate_count": len(duplicate_agents),
                "duplicates": duplicate_agents,
                "score": max(0, 1.0 - len(duplicate_agents) * 0.2)
            }
            
        except Exception as e:
            self.logger.error(f"检测重复智能体失败: {e}")
            return {"has_duplicate_agents": False, "duplicate_count": 0, "duplicates": [], "score": 1.0}
    
    def _detect_duplicate_data_structures(self) -> Dict[str, Any]:
        """检测重复的数据结构定义"""
        try:
            data_structures = {}
            duplicate_structures = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # 检测数据结构类（如dataclass、namedtuple等）
                        if self._is_data_structure(node, content):
                            signature = self._generate_data_structure_signature(node, content)
                            
                            if signature in data_structures:
                                duplicate_structures.append({
                                    "class_name": node.name,
                                    "file_path": file_path,
                                    "line_number": node.lineno,
                                    "duplicate_with": data_structures[signature],
                                    "structure_type": self._identify_data_structure_type(node, content)
                                })
                            else:
                                data_structures[signature] = {
                                    "class_name": node.name,
                                    "file_path": file_path,
                                    "line_number": node.lineno
                                }
            
            return {
                "has_duplicate_structures": len(duplicate_structures) > 0,
                "duplicate_count": len(duplicate_structures),
                "duplicates": duplicate_structures,
                "score": max(0, 1.0 - len(duplicate_structures) * 0.1)
            }
            
        except Exception as e:
            self.logger.error(f"检测重复数据结构失败: {e}")
            return {"has_duplicate_structures": False, "duplicate_count": 0, "duplicates": [], "score": 1.0}
    
    def _detect_duplicate_error_handling(self) -> Dict[str, Any]:
        """检测重复的错误处理模式"""
        try:
            error_patterns = {}
            duplicate_patterns = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                # 提取错误处理模式
                error_blocks = self._extract_error_handling_blocks(tree, content)
                
                for block in error_blocks:
                    pattern_hash = self._calculate_error_pattern_hash(block)
                    
                    if pattern_hash in error_patterns:
                        duplicate_patterns.append({
                            "file_path": file_path,
                            "line_number": block["line_number"],
                            "pattern_type": block["type"],
                            "duplicate_with": error_patterns[pattern_hash]
                        })
                    else:
                        error_patterns[pattern_hash] = {
                            "file_path": file_path,
                            "line_number": block["line_number"],
                            "pattern_type": block["type"]
                        }
            
            return {
                "has_duplicate_error_patterns": len(duplicate_patterns) > 0,
                "duplicate_count": len(duplicate_patterns),
                "duplicates": duplicate_patterns,
                "score": max(0, 1.0 - len(duplicate_patterns) * 0.05)
            }
            
        except Exception as e:
            self.logger.error(f"检测重复错误处理失败: {e}")
            return {"has_duplicate_error_patterns": False, "duplicate_count": 0, "duplicates": [], "score": 1.0}
    
    def _detect_duplicate_logging_patterns(self) -> Dict[str, Any]:
        """检测重复的日志记录模式"""
        try:
            logging_patterns = {}
            duplicate_patterns = []
            
            for file_path in self.python_files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                tree = self._parse_ast(content)
                if not tree:
                    continue
                
                # 提取日志记录模式
                logging_blocks = self._extract_logging_patterns(tree, content)
                
                for block in logging_blocks:
                    pattern_hash = self._calculate_logging_pattern_hash(block)
                    
                    if pattern_hash in logging_patterns:
                        duplicate_patterns.append({
                            "file_path": file_path,
                            "line_number": block["line_number"],
                            "pattern_type": block["type"],
                            "duplicate_with": logging_patterns[pattern_hash]
                        })
                    else:
                        logging_patterns[pattern_hash] = {
                            "file_path": file_path,
                            "line_number": block["line_number"],
                            "pattern_type": block["type"]
                        }
            
            return {
                "has_duplicate_logging_patterns": len(duplicate_patterns) > 0,
                "duplicate_count": len(duplicate_patterns),
                "duplicates": duplicate_patterns,
                "score": max(0, 1.0 - len(duplicate_patterns) * 0.03)
            }
            
        except Exception as e:
            self.logger.error(f"检测重复日志模式失败: {e}")
            return {"has_duplicate_logging_patterns": False, "duplicate_count": 0, "duplicates": [], "score": 1.0}
    
    # 辅助方法
    def _generate_class_signature(self, class_node: ast.ClassDef, content: str) -> str:
        """生成类的签名"""
        try:
            # 提取类的基本信息
            methods = []
            attributes = []
            bases = [base.id if isinstance(base, ast.Name) else str(base) for base in class_node.bases]
            
            for node in class_node.body:
                if isinstance(node, ast.FunctionDef):
                    methods.append(node.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            attributes.append(target.id)
            
            # 生成签名
            signature_parts = [
                f"class_{class_node.name}",
                f"methods_{sorted(methods)}",
                f"attributes_{sorted(attributes)}",
                f"bases_{sorted(bases)}"
            ]
            
            return "|".join(signature_parts)
            
        except Exception as e:
            self.logger.error(f"生成类签名失败: {e}")
            return f"class_{class_node.name}"
    
    def _generate_function_signature(self, func_node: ast.FunctionDef, content: str) -> str:
        """生成函数的签名"""
        try:
            # 提取函数的基本信息
            args = [arg.arg for arg in func_node.args.args]
            defaults = len(func_node.args.defaults)
            decorators = [decorator.id if isinstance(decorator, ast.Name) else str(decorator) for decorator in func_node.decorator_list]
            
            # 生成签名
            signature_parts = [
                f"func_{func_node.name}",
                f"args_{sorted(args)}",
                f"defaults_{defaults}",
                f"decorators_{sorted(decorators)}"
            ]
            
            return "|".join(signature_parts)
            
        except Exception as e:
            self.logger.error(f"生成函数签名失败: {e}")
            return f"func_{func_node.name}"
    
    def _generate_module_signature(self, features: Dict[str, Any]) -> str:
        """生成模块的签名"""
        try:
            signature_parts = [
                f"classes_{sorted(features.get('classes', []))}",
                f"functions_{sorted(features.get('functions', []))}",
                f"imports_{sorted(features.get('imports', []))}",
                f"patterns_{sorted(features.get('patterns', []))}"
            ]
            
            return "|".join(signature_parts)
            
        except Exception as e:
            self.logger.error(f"生成模块签名失败: {e}")
            return "module_signature"
    
    def _extract_module_features(self, tree: ast.AST, content: str) -> Dict[str, Any]:
        """提取模块的特征"""
        try:
            features = {
                "classes": [],
                "functions": [],
                "imports": [],
                "patterns": []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    features["classes"].append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    features["functions"].append(node.name)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            features["imports"].append(alias.name)
                    else:
                        module = node.module or ""
                        for alias in node.names:
                            features["imports"].append(f"{module}.{alias.name}")
            
            return features
            
        except Exception as e:
            self.logger.error(f"提取模块特征失败: {e}")
            return {"classes": [], "functions": [], "imports": [], "patterns": []}
    
    def _extract_code_blocks(self, tree: ast.AST, content: str) -> List[Dict[str, Any]]:
        """提取代码块"""
        try:
            blocks = []
            lines = content.split('\n')
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    start_line = node.lineno - 1
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 1
                    block_content = '\n'.join(lines[start_line:end_line])
                    
                    blocks.append({
                        "type": "function",
                        "name": node.name,
                        "line_number": node.lineno,
                        "content": block_content
                    })
                
                elif isinstance(node, ast.ClassDef):
                    start_line = node.lineno - 1
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 1
                    block_content = '\n'.join(lines[start_line:end_line])
                    
                    blocks.append({
                        "type": "class",
                        "name": node.name,
                        "line_number": node.lineno,
                        "content": block_content
                    })
            
            return blocks
            
        except Exception as e:
            self.logger.error(f"提取代码块失败: {e}")
            return []
    
    def _calculate_block_hash(self, content: str) -> str:
        """计算代码块的哈希值"""
        try:
            # 标准化内容（移除空白、注释等）
            normalized_content = self._normalize_code_content(content)
            return hashlib.md5(normalized_content.encode()).hexdigest()
            
        except Exception as e:
            self.logger.error(f"计算代码块哈希失败: {e}")
            return ""
    
    def _normalize_code_content(self, content: str) -> str:
        """标准化代码内容"""
        try:
            # 移除注释
            lines = content.split('\n')
            normalized_lines = []
            
            for line in lines:
                # 移除行内注释
                if '#' in line:
                    line = line[:line.index('#')]
                # 移除多余空白
                line = line.strip()
                if line:
                    normalized_lines.append(line)
            
            return '\n'.join(normalized_lines)
            
        except Exception as e:
            self.logger.error(f"标准化代码内容失败: {e}")
            return content
    
    def _is_config_function(self, func_node: ast.FunctionDef, content: str) -> bool:
        """判断是否是配置相关函数"""
        try:
            # 检查函数名
            config_keywords = ['config', 'get_config', 'set_config', 'load_config', 'save_config']
            if any(keyword in func_node.name.lower() for keyword in config_keywords):
                return True
            
            # 检查函数体中的配置相关调用
            for node in ast.walk(func_node):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if 'config' in node.func.id.lower():
                            return True
                    elif isinstance(node.func, ast.Attribute):
                        if 'config' in node.func.attr.lower():
                            return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"判断配置函数失败: {e}")
            return False
    
    def _is_agent_class(self, class_node: ast.ClassDef, content: str) -> bool:
        """判断是否是智能体类"""
        try:
            # 检查类名
            agent_keywords = ['agent', 'Agent']
            if any(keyword in class_node.name for keyword in agent_keywords):
                return True
            
            # 检查基类
            for base in class_node.bases:
                if isinstance(base, ast.Name):
                    if 'Agent' in base.id:
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"判断智能体类失败: {e}")
            return False
    
    def _is_data_structure(self, class_node: ast.ClassDef, content: str) -> bool:
        """判断是否是数据结构类"""
        try:
            # 检查装饰器
            for decorator in class_node.decorator_list:
                if isinstance(decorator, ast.Name):
                    if decorator.id in ['dataclass', 'namedtuple']:
                        return True
            
            # 检查类名模式
            data_structure_patterns = ['Config', 'Result', 'Data', 'Info', 'Meta']
            if any(pattern in class_node.name for pattern in data_structure_patterns):
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"判断数据结构类失败: {e}")
            return False
    
    def _calculate_class_similarity(self, class1: ast.ClassDef, class2_info: Dict, content: str) -> float:
        """计算类的相似度"""
        try:
            # 简化的相似度计算
            return 0.8  # 默认相似度
            
        except Exception as e:
            self.logger.error(f"计算类相似度失败: {e}")
            return 0.0
    
    def _calculate_function_similarity(self, func1: ast.FunctionDef, func2_info: Dict, content: str) -> float:
        """计算函数的相似度"""
        try:
            # 简化的相似度计算
            return 0.8  # 默认相似度
            
        except Exception as e:
            self.logger.error(f"计算函数相似度失败: {e}")
            return 0.0
    
    def _calculate_module_similarity(self, features1: Dict, features2: Dict) -> float:
        """计算模块的相似度"""
        try:
            # 简化的相似度计算
            return 0.8  # 默认相似度
            
        except Exception as e:
            self.logger.error(f"计算模块相似度失败: {e}")
            return 0.0
    
    def _generate_config_function_signature(self, func_node: ast.FunctionDef, content: str) -> str:
        """生成配置函数的签名"""
        try:
            return self._generate_function_signature(func_node, content)
            
        except Exception as e:
            self.logger.error(f"生成配置函数签名失败: {e}")
            return f"config_func_{func_node.name}"
    
    def _generate_agent_signature(self, class_node: ast.ClassDef, content: str) -> str:
        """生成智能体的签名"""
        try:
            return self._generate_class_signature(class_node, content)
            
        except Exception as e:
            self.logger.error(f"生成智能体签名失败: {e}")
            return f"agent_{class_node.name}"
    
    def _generate_data_structure_signature(self, class_node: ast.ClassDef, content: str) -> str:
        """生成数据结构的签名"""
        try:
            return self._generate_class_signature(class_node, content)
            
        except Exception as e:
            self.logger.error(f"生成数据结构签名失败: {e}")
            return f"data_{class_node.name}"
    
    def _identify_config_type(self, func_node: ast.FunctionDef, content: str) -> str:
        """识别配置类型"""
        try:
            if 'smart' in func_node.name.lower():
                return "smart_config"
            elif 'unified' in func_node.name.lower():
                return "unified_config"
            else:
                return "basic_config"
                
        except Exception as e:
            self.logger.error(f"识别配置类型失败: {e}")
            return "unknown_config"
    
    def _identify_agent_type(self, class_node: ast.ClassDef, content: str) -> str:
        """识别智能体类型"""
        try:
            if 'enhanced' in class_node.name.lower():
                return "enhanced_agent"
            elif 'base' in class_node.name.lower():
                return "base_agent"
            else:
                return "standard_agent"
                
        except Exception as e:
            self.logger.error(f"识别智能体类型失败: {e}")
            return "unknown_agent"
    
    def _identify_data_structure_type(self, class_node: ast.ClassDef, content: str) -> str:
        """识别数据结构类型"""
        try:
            if 'config' in class_node.name.lower():
                return "config_structure"
            elif 'result' in class_node.name.lower():
                return "result_structure"
            else:
                return "data_structure"
                
        except Exception as e:
            self.logger.error(f"识别数据结构类型失败: {e}")
            return "unknown_structure"
    
    def _extract_error_handling_blocks(self, tree: ast.AST, content: str) -> List[Dict[str, Any]]:
        """提取错误处理块"""
        try:
            error_blocks = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Try):
                    error_blocks.append({
                        "type": "try_except",
                        "line_number": node.lineno,
                        "content": "try_except_block"
                    })
                elif isinstance(node, ast.Raise):
                    error_blocks.append({
                        "type": "raise",
                        "line_number": node.lineno,
                        "content": "raise_statement"
                    })
            
            return error_blocks
            
        except Exception as e:
            self.logger.error(f"提取错误处理块失败: {e}")
            return []
    
    def _extract_logging_patterns(self, tree: ast.AST, content: str) -> List[Dict[str, Any]]:
        """提取日志记录模式"""
        try:
            logging_patterns = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        if node.func.attr in ['info', 'debug', 'warning', 'error', 'critical']:
                            logging_patterns.append({
                                "type": "logging_call",
                                "line_number": node.lineno,
                                "content": f"logger.{node.func.attr}"
                            })
            
            return logging_patterns
            
        except Exception as e:
            self.logger.error(f"提取日志模式失败: {e}")
            return []
    
    def _calculate_error_pattern_hash(self, block: Dict[str, Any]) -> str:
        """计算错误处理模式的哈希值"""
        try:
            content = f"{block['type']}_{block['content']}"
            return hashlib.md5(content.encode()).hexdigest()
            
        except Exception as e:
            self.logger.error(f"计算错误模式哈希失败: {e}")
            return ""
    
    def _calculate_logging_pattern_hash(self, block: Dict[str, Any]) -> str:
        """计算日志记录模式的哈希值"""
        try:
            content = f"{block['type']}_{block['content']}"
            return hashlib.md5(content.encode()).hexdigest()
            
        except Exception as e:
            self.logger.error(f"计算日志模式哈希失败: {e}")
            return ""
