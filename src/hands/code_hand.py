#!/usr/bin/env python3
"""
代码操作Hands
"""

import ast
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess
import sys

from .base import BaseHand, HandCategory, HandSafetyLevel, HandExecutionResult


class CodeAnalysisHand(BaseHand):
    """代码分析Hand"""
    
    def __init__(self):
        super().__init__(
            name="code_analysis",
            description="分析代码文件",
            category=HandCategory.CODE_MODIFICATION,
            safety_level=HandSafetyLevel.SAFE
        )
    
    def validate_parameters(self, **kwargs) -> bool:
        """验证参数"""
        required = ["path"]
        return all(key in kwargs for key in required)
    
    async def execute(self, **kwargs) -> HandExecutionResult:
        """执行代码分析"""
        try:
            file_path = Path(kwargs["path"])
            
            if not file_path.exists():
                return HandExecutionResult(
                    hand_name=self.name,
                    success=False,
                    output=None,
                    error=f"文件不存在: {file_path}"
                )
            
            if not file_path.is_file():
                return HandExecutionResult(
                    hand_name=self.name,
                    success=False,
                    output=None,
                    error=f"不是文件: {file_path}"
                )
            
            # 读取文件内容
            content = file_path.read_text(encoding="utf-8")
            
            # 分析结果
            analysis = {
                "file_info": {
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                    "extension": file_path.suffix,
                    "lines": len(content.splitlines())
                },
                "ast_analysis": await self._analyze_ast(content),
                "code_metrics": await self._calculate_metrics(content),
                "potential_issues": await self._find_issues(content)
            }
            
            return HandExecutionResult(
                hand_name=self.name,
                success=True,
                output=analysis,
                validation_results={
                    "analysis_complete": True,
                    "file_type": file_path.suffix
                }
            )
            
        except Exception as e:
            return HandExecutionResult(
                hand_name=self.name,
                success=False,
                output=None,
                error=f"代码分析失败: {e}"
            )
    
    async def _analyze_ast(self, content: str) -> Dict[str, Any]:
        """分析AST"""
        try:
            tree = ast.parse(content)
            
            functions = []
            classes = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        "name": node.name,
                        "args": len(node.args.args),
                        "has_docstring": ast.get_docstring(node) is not None,
                        "decorators": [d.id for d in node.decorator_list if hasattr(d, 'id')]
                    })
                elif isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "methods": len([n for n in node.body if isinstance(n, ast.FunctionDef)]),
                        "has_docstring": ast.get_docstring(node) is not None,
                        "bases": [base.id for base in node.bases if hasattr(base, 'id')]
                    })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({"type": "import", "module": alias.name})
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append({
                            "type": "from_import",
                            "module": module,
                            "name": alias.name
                        })
            
            return {
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "ast_valid": True
            }
            
        except SyntaxError as e:
            return {
                "functions": [],
                "classes": [],
                "imports": [],
                "ast_valid": False,
                "syntax_error": str(e)
            }
    
    async def _calculate_metrics(self, content: str) -> Dict[str, Any]:
        """计算代码指标"""
        lines = content.splitlines()
        
        # 基础统计
        total_lines = len(lines)
        code_lines = sum(1 for line in lines if line.strip() and not line.strip().startswith("#"))
        comment_lines = sum(1 for line in lines if line.strip().startswith("#"))
        blank_lines = sum(1 for line in lines if not line.strip())
        
        # 复杂度估计
        complexity = 0
        complexity += content.count("if ")
        complexity += content.count("for ")
        complexity += content.count("while ")
        complexity += content.count("try:")
        complexity += content.count("except ")
        
        return {
            "lines": {
                "total": total_lines,
                "code": code_lines,
                "comments": comment_lines,
                "blank": blank_lines
            },
            "complexity": {
                "score": complexity,
                "description": self._describe_complexity(complexity)
            },
            "readability": {
                "average_line_length": sum(len(line) for line in lines) / total_lines if total_lines > 0 else 0
            }
        }
    
    def _describe_complexity(self, complexity: int) -> str:
        """描述复杂度"""
        if complexity < 5:
            return "简单"
        elif complexity < 15:
            return "中等"
        elif complexity < 30:
            return "复杂"
        else:
            return "非常复杂"
    
    async def _find_issues(self, content: str) -> List[Dict[str, Any]]:
        """查找潜在问题"""
        issues = []
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            # 检查硬编码字符串
            if 'API_KEY' in line and 'os.getenv' not in line:
                issues.append({
                    "line": i,
                    "type": "security",
                    "severity": "high",
                    "description": "检测到硬编码的API密钥",
                    "suggestion": "使用环境变量或配置中心"
                })
            
            # 检查宽泛的异常捕获
            if 'except:' in line or 'except Exception:' in line:
                issues.append({
                    "line": i,
                    "type": "code_quality",
                    "severity": "medium",
                    "description": "宽泛的异常捕获",
                    "suggestion": "使用具体的异常类型"
                })
            
            # 检查过长的行
            if len(line) > 120:
                issues.append({
                    "line": i,
                    "type": "style",
                    "severity": "low",
                    "description": f"行过长 ({len(line)} 字符)",
                    "suggestion": "考虑拆分为多行"
                })
        
        return issues


class PythonTestHand(BaseHand):
    """Python测试Hand"""
    
    def __init__(self):
        super().__init__(
            name="python_test",
            description="运行Python测试",
            category=HandCategory.TEST_EXECUTION,
            safety_level=HandSafetyLevel.SAFE
        )
    
    def validate_parameters(self, **kwargs) -> bool:
        """验证参数"""
        return True  # 所有参数都是可选的
    
    async def execute(self, **kwargs) -> HandExecutionResult:
        """执行Python测试"""
        try:
            test_path = kwargs.get("path", "tests/")
            pattern = kwargs.get("pattern", "")
            verbose = kwargs.get("verbose", False)
            
            # 构建pytest命令
            cmd = [sys.executable, "-m", "pytest"]
            
            if test_path:
                cmd.append(test_path)
            
            if pattern:
                cmd.extend(["-k", pattern])
            
            if verbose:
                cmd.append("-v")
            
            # 添加其他选项
            if kwargs.get("coverage", False):
                cmd.extend(["--cov=src", "--cov-report=term-missing"])
            
            # 运行测试
            self.logger.info(f"运行测试命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=kwargs.get("timeout", 300)  # 默认5分钟超时
            )
            
            # 解析结果
            test_output = {
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd)
            }
            
            # 提取测试统计信息
            stats = self._extract_test_stats(result.stdout)
            
            success = result.returncode == 0
            
            return HandExecutionResult(
                hand_name=self.name,
                success=success,
                output={
                    "stats": stats,
                    "raw_output": test_output
                },
                error=None if success else "测试运行失败",
                validation_results={
                    "tests_run": True,
                    "exit_code": result.returncode
                }
            )
            
        except subprocess.TimeoutExpired:
            return HandExecutionResult(
                hand_name=self.name,
                success=False,
                output=None,
                error="测试执行超时"
            )
        except Exception as e:
            return HandExecutionResult(
                hand_name=self.name,
                success=False,
                output=None,
                error=f"测试执行失败: {e}"
            )
    
    def _extract_test_stats(self, stdout: str) -> Dict[str, Any]:
        """从pytest输出中提取统计信息"""
        stats = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "total": 0
        }
        
        # 简单模式匹配
        lines = stdout.splitlines()
        for line in lines:
            if "passed" in line and "failed" in line and "skipped" in line:
                # 解析类似 "5 passed, 1 failed, 2 skipped" 的字符串
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.isdigit():
                        if i > 0 and parts[i-1] in ["passed", "failed", "skipped", "errors"]:
                            stats[parts[i-1]] = int(part)
                
                # 计算总数
                stats["total"] = sum(stats.values())
                break
        
        return stats


class CodeFormatHand(BaseHand):
    """代码格式化Hand"""
    
    def __init__(self):
        super().__init__(
            name="code_format",
            description="格式化代码文件",
            category=HandCategory.CODE_MODIFICATION,
            safety_level=HandSafetyLevel.MODERATE
        )
    
    def validate_parameters(self, **kwargs) -> bool:
        """验证参数"""
        required = ["path"]
        return all(key in kwargs for key in required)
    
    async def execute(self, **kwargs) -> HandExecutionResult:
        """执行代码格式化"""
        try:
            file_path = Path(kwargs["path"])
            
            if not file_path.exists():
                return HandExecutionResult(
                    hand_name=self.name,
                    success=False,
                    output=None,
                    error=f"文件不存在: {file_path}"
                )
            
            # 备份原文件
            backup_path = None
            if kwargs.get("backup", True):
                backup_path = file_path.with_suffix(file_path.suffix + ".bak")
                import shutil
                shutil.copy2(file_path, backup_path)
            
            # 读取原内容
            original_content = file_path.read_text(encoding="utf-8")
            
            # 应用格式化
            formatter = kwargs.get("formatter", "black")  # black, autopep8, yapf
            formatted_content = await self._format_code(original_content, formatter, kwargs)
            
            # 写入格式化后的内容
            file_path.write_text(formatted_content, encoding="utf-8")
            
            return HandExecutionResult(
                hand_name=self.name,
                success=True,
                output={
                    "path": str(file_path),
                    "formatter": formatter,
                    "backup_created": backup_path is not None,
                    "backup_path": str(backup_path) if backup_path else None,
                    "changes_made": original_content != formatted_content
                },
                validation_results={
                    "formatted_successfully": True,
                    "file_exists": file_path.exists()
                }
            )
            
        except Exception as e:
            return HandExecutionResult(
                hand_name=self.name,
                success=False,
                output=None,
                error=f"代码格式化失败: {e}"
            )
    
    async def _format_code(self, content: str, formatter: str, options: Dict[str, Any]) -> str:
        """格式化代码"""
        if formatter == "black":
            # 使用black格式化
            try:
                import black
                mode = black.Mode(
                    line_length=options.get("line_length", 88),
                    string_normalization=options.get("string_normalization", True)
                )
                return black.format_str(content, mode=mode)
            except ImportError:
                self.logger.warning("black未安装，使用简单格式化")
                return self._simple_format(content)
        
        elif formatter == "autopep8":
            # 使用autopep8格式化
            try:
                import autopep8
                return autopep8.fix_code(content, options=options)
            except ImportError:
                self.logger.warning("autopep8未安装，使用简单格式化")
                return self._simple_format(content)
        
        else:
            # 简单格式化
            return self._simple_format(content)
    
    def _simple_format(self, content: str) -> str:
        """简单格式化代码"""
        lines = content.splitlines()
        formatted_lines = []
        
        for line in lines:
            # 去除行尾空白
            stripped = line.rstrip()
            # 保留必要的缩进
            formatted_lines.append(stripped)
        
        # 确保文件以换行符结尾
        result = "\n".join(formatted_lines)
        if not result.endswith("\n"):
            result += "\n"
        
        return result


class CodeModificationHand(BaseHand):
    """代码修改Hand"""
    
    def __init__(self):
        super().__init__(
            name="code_modification",
            description="修改代码文件",
            category=HandCategory.CODE_MODIFICATION,
            safety_level=HandSafetyLevel.RISKY
        )
    
    def validate_parameters(self, **kwargs) -> bool:
        """验证参数"""
        required = ["path", "modifications"]
        return all(key in kwargs for key in required)
    
    async def execute(self, **kwargs) -> HandExecutionResult:
        """执行代码修改"""
        try:
            file_path = Path(kwargs["path"])
            modifications = kwargs["modifications"]
            
            if not file_path.exists():
                return HandExecutionResult(
                    hand_name=self.name,
                    success=False,
                    output=None,
                    error=f"文件不存在: {file_path}"
                )
            
            # 读取原内容
            original_content = file_path.read_text(encoding="utf-8")
            lines = original_content.splitlines()
            
            # 备份原文件
            backup_path = None
            if kwargs.get("backup", True):
                backup_path = file_path.with_suffix(file_path.suffix + ".bak")
                import shutil
                shutil.copy2(file_path, backup_path)
            
            # 应用修改
            modified_content = await self._apply_modifications(lines, modifications)
            
            # 写入修改后的内容
            file_path.write_text(modified_content, encoding="utf-8")
            
            # 验证修改
            validation = await self._validate_modifications(original_content, modified_content, modifications)
            
            return HandExecutionResult(
                hand_name=self.name,
                success=True,
                output={
                    "path": str(file_path),
                    "modifications_applied": len(modifications),
                    "backup_created": backup_path is not None,
                    "backup_path": str(backup_path) if backup_path else None,
                    "validation": validation
                },
                validation_results={
                    "modified_successfully": True,
                    "validation_passed": validation.get("passed", False)
                }
            )
            
        except Exception as e:
            return HandExecutionResult(
                hand_name=self.name,
                success=False,
                output=None,
                error=f"代码修改失败: {e}"
            )
    
    async def _apply_modifications(self, original_lines: List[str], modifications: List[Dict[str, Any]]) -> str:
        """应用修改到代码行"""
        lines = original_lines.copy()
        
        # 按行号排序修改（从后往前应用，避免行号变化影响）
        modifications_sorted = sorted(modifications, key=lambda x: x.get("line", 0), reverse=True)
        
        for mod in modifications_sorted:
            mod_type = mod.get("type")
            line_num = mod.get("line", 0) - 1  # 转换为0-based索引
            
            if line_num < 0 or line_num >= len(lines):
                continue  # 跳过无效行号
            
            if mod_type == "replace":
                new_content = mod.get("content", "")
                lines[line_num] = new_content
            
            elif mod_type == "insert":
                new_content = mod.get("content", "")
                lines.insert(line_num, new_content)
            
            elif mod_type == "delete":
                lines.pop(line_num)
            
            elif mod_type == "replace_range":
                start_line = mod.get("start_line", line_num) - 1
                end_line = mod.get("end_line", line_num) - 1
                new_content = mod.get("content", "")
                
                # 替换行范围
                if start_line <= end_line and start_line >= 0 and end_line < len(lines):
                    # 删除旧行，插入新内容
                    del lines[start_line:end_line+1]
                    # 新内容可能是多行
                    new_lines = new_content.splitlines()
                    for i, new_line in enumerate(new_lines):
                        lines.insert(start_line + i, new_line)
        
        return "\n".join(lines)
    
    async def _validate_modifications(self, original: str, modified: str, modifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """验证修改"""
        # 基本验证
        original_lines = original.splitlines()
        modified_lines = modified.splitlines()
        
        validation = {
            "passed": True,
            "checks": [],
            "warnings": []
        }
        
        # 检查行数变化
        line_change = len(modified_lines) - len(original_lines)
        if line_change != 0:
            validation["checks"].append({
                "type": "line_count",
                "status": "info",
                "message": f"行数变化: {line_change}"
            })
        
        # 检查语法
        try:
            ast.parse(modified)
            validation["checks"].append({
                "type": "syntax",
                "status": "passed",
                "message": "语法检查通过"
            })
        except SyntaxError as e:
            validation["passed"] = False
            validation["checks"].append({
                "type": "syntax",
                "status": "failed",
                "message": f"语法错误: {e}"
            })
        
        # 检查是否应用了所有修改
        applied_count = 0
        for mod in modifications:
            mod_type = mod.get("type")
            if mod_type in ["replace", "insert", "delete", "replace_range"]:
                applied_count += 1
        
        validation["checks"].append({
            "type": "modifications_applied",
            "status": "passed",
            "message": f"应用了 {applied_count}/{len(modifications)} 个修改"
        })
        
        return validation


class CodeGenerationHand(BaseHand):
    """代码生成Hand"""
    
    def __init__(self):
        super().__init__(
            name="code_generation",
            description="生成代码文件",
            category=HandCategory.CODE_MODIFICATION,
            safety_level=HandSafetyLevel.MODERATE
        )
    
    def validate_parameters(self, **kwargs) -> bool:
        """验证参数"""
        required = ["path", "template"]
        return all(key in kwargs for key in required)
    
    async def execute(self, **kwargs) -> HandExecutionResult:
        """执行代码生成"""
        try:
            file_path = Path(kwargs["path"])
            template = kwargs["template"]
            context = kwargs.get("context", {})
            
            # 检查文件是否已存在
            if file_path.exists() and not kwargs.get("overwrite", False):
                return HandExecutionResult(
                    hand_name=self.name,
                    success=False,
                    output=None,
                    error=f"文件已存在: {file_path} (使用 overwrite=True 覆盖)"
                )
            
            # 生成代码
            generated_code = await self._generate_code(template, context)
            
            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            file_path.write_text(generated_code, encoding="utf-8")
            
            return HandExecutionResult(
                hand_name=self.name,
                success=True,
                output={
                    "path": str(file_path),
                    "template": template,
                    "generated_lines": len(generated_code.splitlines()),
                    "file_created": file_path.exists()
                },
                validation_results={
                    "generated_successfully": True,
                    "file_exists": file_path.exists()
                }
            )
            
        except Exception as e:
            return HandExecutionResult(
                hand_name=self.name,
                success=False,
                output=None,
                error=f"代码生成失败: {e}"
            )
    
    async def _generate_code(self, template: str, context: Dict[str, Any]) -> str:
        """根据模板生成代码"""
        # 内置模板
        templates = {
            "python_class": '''#!/usr/bin/env python3
"""
{description}
"""

from typing import Dict, List, Any, Optional


class {class_name}:
    """{description}"""
    
    def __init__(self{init_params}):
        """初始化"""
        {init_body}
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{class_name}()"
    
    # TODO: 添加具体方法''',
            
            "python_function": '''#!/usr/bin/env python3
"""
{description}
"""

def {function_name}({params}) -> {return_type}:
    """{description}
    
    Args:
        {param_docs}
    
    Returns:
        {return_docs}
    """
    # TODO: 实现功能
    {function_body}''',
            
            "test_file": '''#!/usr/bin/env python3
"""
测试文件
"""

import pytest
from pathlib import Path
import sys

# 添加源文件路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from {module} import {class_name}


class Test{class_name}:
    """测试 {class_name}"""
    
    def setup_method(self):
        """测试设置"""
        self.instance = {class_name}()
    
    def test_initialization(self):
        """测试初始化"""
        assert self.instance is not None
    
    def test_string_representation(self):
        """测试字符串表示"""
        assert str(self.instance) == "{class_name}()"
    
    # TODO: 添加更多测试'''
        }
        
        # 获取模板
        if template in templates:
            template_content = templates[template]
        else:
            # 假设template是文件路径
            template_path = Path(template)
            if template_path.exists():
                template_content = template_path.read_text(encoding="utf-8")
            else:
                # 使用template作为直接内容
                template_content = template
        
        # 应用上下文变量
        generated = template_content
        for key, value in context.items():
            placeholder = "{" + key + "}"
            generated = generated.replace(placeholder, str(value))
        
        return generated


# 测试函数
async def test_code_hands():
    """测试代码Hands"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    from pathlib import Path
    
    print("🧪 测试代码Hands")
    print("=" * 60)
    
    # 创建测试目录
    test_dir = Path("test_code_hands")
    test_dir.mkdir(exist_ok=True)
    
    try:
        # 测试CodeAnalysisHand
        print("\n📊 测试CodeAnalysisHand...")
        analysis_hand = CodeAnalysisHand()
        
        # 创建测试文件
        test_file = test_dir / "test_analysis.py"
        test_content = '''#!/usr/bin/env python3
"""
测试文件
"""

def example_function(param1, param2):
    """示例函数"""
    if param1 > param2:
        return param1
    else:
        return param2


class ExampleClass:
    """示例类"""
    
    def method(self):
        """示例方法"""
        pass
'''
        test_file.write_text(test_content, encoding="utf-8")
        
        result = await analysis_hand.execute(path=str(test_file))
        print(f"分析结果: {'成功' if result.success else '失败'}")
        if result.success:
            analysis = result.output
            print(f"  文件信息: {analysis['file_info']}")
            print(f"  函数数量: {len(analysis['ast_analysis']['functions'])}")
            print(f"  代码指标: {analysis['code_metrics']}")
        
        # 测试PythonTestHand
        print("\n🧪 测试PythonTestHand...")
        test_hand = PythonTestHand()
        
        # 创建简单测试
        test_test_file = test_dir / "test_simple.py"
        test_test_content = '''def test_example():
    """示例测试"""
    assert 1 + 1 == 2
'''
        test_test_file.write_text(test_test_content, encoding="utf-8")
        
        result = await test_hand.execute(path=str(test_test_file))
        print(f"测试结果: {'成功' if result.success else '失败'}")
        if result.success:
            print(f"  测试统计: {result.output['stats']}")
        
        # 测试CodeGenerationHand
        print("\n💻 测试CodeGenerationHand...")
        gen_hand = CodeGenerationHand()
        
        gen_file = test_dir / "generated_class.py"
        result = await gen_hand.execute(
            path=str(gen_file),
            template="python_class",
            context={
                "class_name": "GeneratedClass",
                "description": "生成的测试类",
                "init_params": ", name: str",
                "init_body": "self.name = name"
            },
            overwrite=True
        )
        
        print(f"代码生成: {'成功' if result.success else '失败'}")
        if result.success:
            print(f"  生成文件: {gen_file}")
            if gen_file.exists():
                content = gen_file.read_text(encoding="utf-8")
                print(f"  内容预览:\n{content[:200]}...")
        
        print("\n✅ 代码Hands测试完成")
        
    finally:
        # 清理测试目录
        if test_dir.exists():
            import shutil
            shutil.rmtree(test_dir)


if __name__ == "__main__":
    asyncio.run(test_code_hands())