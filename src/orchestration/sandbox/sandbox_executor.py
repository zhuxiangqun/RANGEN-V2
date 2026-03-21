#!/usr/bin/env python3
"""
沙盒执行器 - Skill-Creator 自测试核心组件

功能:
- 在隔离环境中执行新创建的技能
- 捕获执行结果和错误
- 支持超时控制
- 提供错误诊断和修复建议
"""

import os
import sys
import time
import uuid
import traceback
import subprocess
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from .test_result import TestResult, TestStatus


@dataclass
class SandboxConfig:
    """沙盒配置"""
    timeout_seconds: int = 30
    max_retries: int = 3
    memory_limit_mb: int = 512
    cpu_limit_percent: int = 50
    network_enabled: bool = False
    filesystem_readonly: bool = True
    workspace_dir: str = "./sandbox_workspace"


class SandboxExecutor:
    """
    沙盒执行器
    
    在隔离环境中执行技能代码，捕获错误并提供诊断信息。
    """
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self._setup_workspace()
    
    def _setup_workspace(self):
        """设置工作目录"""
        self.workspace = Path(self.config.workspace_dir)
        self.workspace.mkdir(parents=True, exist_ok=True)
    
    def execute_skill(
        self, 
        skill_code: str,
        skill_name: str,
        test_input: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> TestResult:
        """
        在沙盒中执行技能
        
        Args:
            skill_code: 技能代码 (Python)
            skill_name: 技能名称
            test_input: 测试输入参数
            context: 上下文信息
            
        Returns:
            TestResult: 测试结果
        """
        test_id = f"test_{uuid.uuid4().hex[:12]}"
        start_time = time.time()
        
        test_file = self._create_test_file(skill_code, skill_name, test_input)
        
        try:
            result = self._run_test_process(test_file, skill_name)
            self._cleanup_test_file(test_file)
            return result
            
        except TimeoutError:
            self._cleanup_test_file(test_file)
            return TestResult(
                test_id=test_id,
                skill_name=skill_name,
                status=TestStatus.TIMEOUT,
                execution_time=time.time() - start_time,
                error="Execution timeout",
                suggestions=["Increase timeout or optimize skill code"]
            )
        except Exception as e:
            self._cleanup_test_file(test_file)
            return TestResult(
                test_id=test_id,
                skill_name=skill_name,
                status=TestStatus.ERROR,
                execution_time=time.time() - start_time,
                error=str(e),
                error_trace=traceback.format_exc(),
                suggestions=self._generate_error_suggestions(e)
            )
    
    def _create_test_file(
        self, 
        skill_code: str, 
        skill_name: str,
        test_input: Optional[Dict[str, Any]]
    ) -> Path:
        """创建临时测试文件"""
        test_id = uuid.uuid4().hex[:8]
        test_file = self.workspace / f"test_{skill_name}_{test_id}.py"
        
        test_script = self._build_test_script(skill_code, skill_name, test_input)
        test_file.write_text(test_script, encoding='utf-8')
        
        return test_file
    
    def _build_test_script(
        self, 
        skill_code: str, 
        skill_name: str,
        test_input: Optional[Dict[str, Any]]
    ) -> str:
        """构建测试脚本"""
        import base64
        input_json = self._serialize_input(test_input)
        has_input = "True" if test_input else "False"
        
        # Base64 编码代码避免引号问题
        encoded = base64.b64encode(skill_code.encode()).decode()
        
        return f'''
import sys
import json
import traceback
import base64

try:
    # Decode and execute skill code
    code = base64.b64decode("{encoded}").decode()
    exec(code)
    
    # Find function
    skill_func = locals().get("{skill_name}") or globals().get("{skill_name}")
    if skill_func is None:
        skill_func = locals().get("main") or globals().get("main")
    if skill_func is None:
        skill_func = locals().get("execute") or globals().get("execute")
    
    if skill_func is None:
        raise ValueError("Could not find function")
    
    # Execute
    test_input = {input_json}
    if {has_input} and test_input:
        result = skill_func(**test_input)
    else:
        result = skill_func()
    
    print("__RESULT__:" + json.dumps({{
        "status": "success",
        "output": str(result) if result is not None else None
    }}))
    
except Exception as e:
    print("__ERROR__:" + json.dumps({{
        "status": "error",
        "error": str(e),
        "trace": traceback.format_exc()
    }}))
'''
    
    def _serialize_input(self, test_input: Optional[Dict[str, Any]]) -> str:
        """序列化测试输入"""
        if test_input is None:
            return "{}"
        return json.dumps(test_input, ensure_ascii=False)
    
    def _run_test_process(self, test_file: Path, skill_name: str) -> TestResult:
        """运行测试进程"""
        start_time = time.time()
        test_id = f"test_{uuid.uuid4().hex[:12]}"
        
        try:
            process = subprocess.Popen(
                [sys.executable, str(test_file.absolute())],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                stdout, stderr = process.communicate(timeout=self.config.timeout_seconds)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                raise TimeoutError(f"Test exceeded {self.config.timeout_seconds}s timeout")
            
            execution_time = time.time() - start_time
            
            return self._parse_test_output(
                test_id=test_id,
                skill_name=skill_name,
                stdout=stdout,
                stderr=stderr,
                execution_time=execution_time
            )
            
        except subprocess.TimeoutExpired:
            return TestResult(
                test_id=test_id,
                skill_name=skill_name,
                status=TestStatus.TIMEOUT,
                execution_time=self.config.timeout_seconds,
                error="Process timeout",
                suggestions=["Optimize skill code or increase timeout"]
            )
    
    def _parse_test_output(
        self,
        test_id: str,
        skill_name: str,
        stdout: str,
        stderr: str,
        execution_time: float
    ) -> TestResult:
        """解析测试输出"""
        if "__RESULT__" in stdout:
            try:
                result_line = [l for l in stdout.split('\n') if l.startswith('__RESULT__:')][0]
                result_data = json.loads(result_line.replace('__RESULT__:', '').strip())
                
                return TestResult(
                    test_id=test_id,
                    skill_name=skill_name,
                    status=TestStatus.PASSED,
                    execution_time=execution_time,
                    output=result_data.get("output"),
                    suggestions=[]
                )
            except (json.JSONDecodeError, IndexError) as e:
                return TestResult(
                    test_id=test_id,
                    skill_name=skill_name,
                    status=TestStatus.ERROR,
                    execution_time=execution_time,
                    error=f"Failed to parse result: {e}",
                    error_trace=stdout + "\n" + stderr
                )
        
        if "__ERROR__" in stdout:
            try:
                error_line = [l for l in stdout.split('\n') if l.startswith('__ERROR__:')][0]
                error_data = json.loads(error_line.replace('__ERROR__:', '').strip())
                
                return TestResult(
                    test_id=test_id,
                    skill_name=skill_name,
                    status=TestStatus.FAILED,
                    execution_time=execution_time,
                    error=error_data.get("error"),
                    error_trace=error_data.get("trace"),
                    output=error_data.get("logs"),
                    suggestions=self._generate_error_suggestions(
                        Exception(error_data.get("error", "Unknown error"))
                    )
                )
            except (json.JSONDecodeError, IndexError):
                return TestResult(
                    test_id=test_id,
                    skill_name=skill_name,
                    status=TestStatus.FAILED,
                    execution_time=execution_time,
                    error="Unknown error",
                    error_trace=stdout + "\n" + stderr,
                    suggestions=["Check skill syntax and imports"]
                )
        
        return TestResult(
            test_id=test_id,
            skill_name=skill_name,
            status=TestStatus.FAILED,
            execution_time=execution_time,
            error="Test produced no result",
            error_trace=stdout + "\n" + stderr,
            suggestions=["Ensure skill has a callable function"]
        )
    
    def _generate_error_suggestions(self, error: Exception) -> List[str]:
        """根据错误类型生成修复建议"""
        error_msg = str(error).lower()
        suggestions = []
        
        if "importerror" in error_msg or "modulenotfound" in error_msg:
            suggestions.append("Add missing import statement")
            suggestions.append("Check if required packages are installed")
        elif "syntaxerror" in error_msg:
            suggestions.append("Fix Python syntax errors")
            suggestions.append("Check indentation and brackets")
        elif "attributeerror" in error_msg:
            suggestions.append("Check object attributes exist")
            suggestions.append("Verify method names are correct")
        elif "typeerror" in error_msg or "argument" in error_msg:
            suggestions.append("Check function parameter types")
            suggestions.append("Verify required arguments are provided")
        elif "timeout" in error_msg:
            suggestions.append("Optimize skill code for faster execution")
            suggestions.append("Consider async/await patterns")
        else:
            suggestions.append("Review error trace for specific issue")
            suggestions.append("Simplify skill logic")
        
        return suggestions
    
    def _cleanup_test_file(self, test_file: Path):
        """清理测试文件"""
        try:
            if test_file.exists():
                test_file.unlink()
        except Exception:
            pass


_sandbox_executor = None

def get_sandbox_executor() -> SandboxExecutor:
    """获取沙盒执行器实例"""
    global _sandbox_executor
    if _sandbox_executor is None:
        _sandbox_executor = SandboxExecutor()
    return _sandbox_executor
