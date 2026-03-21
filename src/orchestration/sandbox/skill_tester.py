#!/usr/bin/env python3
"""
技能测试器 - 带 Self-Correction 的自动测试

功能:
- 执行技能测试
- 失败时自动分析错误并修复
- 提供修复建议
"""

import re
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime

from .sandbox_executor import SandboxExecutor, SandboxConfig, get_sandbox_executor
from .test_result import TestResult, TestStatus


@dataclass
class SkillTestConfig:
    """技能测试配置"""
    max_retries: int = 3
    timeout_seconds: int = 30
    auto_fix: bool = True
    fix_llm_callable: Optional[Callable[[str, str], str]] = None


class SkillTester:
    """
    技能测试器
    
    支持 Self-Correction: 测试失败时自动分析错误并尝试修复
    """
    
    def __init__(self, config: Optional[SkillTestConfig] = None):
        self.config = config or SkillTestConfig()
        self.sandbox = get_sandbox_executor()
    
    async def test_and_fix(
        self,
        skill_code: str,
        skill_name: str,
        test_input: Optional[Dict[str, Any]] = None,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        测试并自动修复技能
        
        Args:
            skill_code: 技能代码
            skill_name: 技能名称
            test_input: 测试输入
            description: 技能描述（用于 LLM 修复）
            
        Returns:
            {
                "success": bool,
                "final_code": str,
                "test_result": TestResult,
                "attempts": int,
                "fix_history": List[Dict]
            }
        """
        current_code = skill_code
        fix_history = []
        attempts = 0
        max_attempts = self.config.max_retries
        
        while attempts < max_attempts:
            attempts += 1
            
            # 执行测试
            result = self.sandbox.execute_skill(
                skill_code=current_code,
                skill_name=skill_name,
                test_input=test_input
            )
            
            if result.is_success():
                return {
                    "success": True,
                    "final_code": current_code,
                    "test_result": result,
                    "attempts": attempts,
                    "fix_history": fix_history
                }
            
            # 记录失败
            fix_record = {
                "attempt": attempts,
                "error": result.error,
                "suggestions": result.suggestions
            }
            fix_history.append(fix_record)
            
            # 如果配置了自动修复且有 LLM 调用器
            if self.config.auto_fix and self.config.fix_llm_callable:
                fixed_code = await self._try_fix(
                    current_code=current_code,
                    error=result.error,
                    error_trace=result.error_trace or "",
                    description=description,
                    suggestions=result.suggestions
                )
                
                if fixed_code and fixed_code != current_code:
                    fix_record["fixed"] = True
                    fix_record["original_error"] = result.error
                    current_code = fixed_code
                    continue
            
            # 达到最大尝试次数
            if attempts >= max_attempts:
                break
        
        return {
            "success": False,
            "final_code": current_code,
            "test_result": result,
            "attempts": attempts,
            "fix_history": fix_history
        }
    
    async def _try_fix(
        self,
        current_code: str,
        error: str,
        error_trace: str,
        description: str,
        suggestions: List[str]
    ) -> Optional[str]:
        """
        尝试使用 LLM 修复代码
        
        Args:
            current_code: 当前代码
            error: 错误信息
            error_trace: 错误堆栈
            description: 技能描述
            suggestions: 建议列表
            
        Returns:
            修复后的代码，如果失败返回 None
        """
        if not self.config.fix_llm_callable:
            return None
        
        try:
            # 构建修复提示词
            fix_prompt = self._build_fix_prompt(
                current_code, error, error_trace, description, suggestions
            )
            
            # 调用 LLM 修复
            fixed_code = await self.config.fix_llm_callable(fix_prompt, error)
            
            # 验证修复后的代码语法
            if self._validate_syntax(fixed_code):
                return fixed_code
            
            return None
            
        except Exception as e:
            print(f"LLM fix failed: {e}")
            return None
    
    def _build_fix_prompt(
        self,
        current_code: str,
        error: str,
        error_trace: str,
        description: str,
        suggestions: List[str]
    ) -> str:
        """构建修复提示词"""
        suggestions_text = "\n".join([f"- {s}" for s in suggestions])
        
        return f"""你是一个 Python 技能修复专家。

## 技能描述
{description}

## 当前代码
```python
{current_code}
```

## 错误信息
{error}

## 错误堆栈
{error_trace}

## 已有建议
{suggestions_text}

## 任务
修复上述错误，返回修复后的完整 Python 代码。
只返回代码，不要解释。
"""
    
    def _validate_syntax(self, code: str) -> bool:
        """验证代码语法"""
        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError:
            return False
    
    def test_simple(
        self,
        skill_code: str,
        skill_name: str,
        test_input: Optional[Dict[str, Any]] = None
    ) -> TestResult:
        """
        简单测试（无自动修复）
        
        Args:
            skill_code: 技能代码
            skill_name: 技能名称
            test_input: 测试输入
            
        Returns:
            TestResult
        """
        return self.sandbox.execute_skill(
            skill_code=skill_code,
            skill_name=skill_name,
            test_input=test_input
        )


@dataclass
class TestReport:
    """测试报告"""
    skill_name: str
    passed: bool
    total_attempts: int
    final_result: TestResult
    fix_history: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_name": self.skill_name,
            "passed": self.passed,
            "total_attempts": self.total_attempts,
            "final_result": self.final_result.to_dict(),
            "fix_history": self.fix_history,
            "timestamp": self.timestamp.isoformat()
        }
