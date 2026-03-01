#!/usr/bin/env python3
"""
计算器工具示例
演示如何创建新的工具
"""

import time
import logging
import re
import ast
import operator
from typing import Dict, Any, Optional

from .base_tool import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class CalculatorTool(BaseTool):
    """计算器工具 - 示例实现"""
    
    def __init__(self):
        """初始化计算器工具"""
        super().__init__(
            tool_name="calculator",
            description="计算器工具：执行数学计算"
        )
        # 定义安全的运算符
        self._safe_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }
    
    async def call(self, expression: Optional[str] = None, operation: Optional[str] = None, 
                   a: Optional[float] = None, b: Optional[float] = None, **kwargs) -> ToolResult:
        """
        调用计算器工具
        
        Args:
            expression: 数学表达式（如 "2 + 3"）
            operation: 运算类型（如 "add", "subtract", "multiply", "divide"）
            a: 第一个操作数
            b: 第二个操作数
            **kwargs: 其他参数
            
        Returns:
            ToolResult: 工具执行结果
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"🔢 计算器工具调用")
            
            result = None
            
            # 方式1: 使用表达式
            if expression:
                result = self._safe_evaluate_expression(expression)
            
            # 方式2: 使用操作和操作数
            elif operation and a is not None and b is not None:
                result = self._perform_operation(operation, a, b)
            
            else:
                raise ValueError("必须提供expression或(operation, a, b)")
            
            execution_time = time.time() - start_time
            self.logger.info(f"✅ 计算器工具执行成功: {result}")
            self._record_call(True)
            
            return ToolResult(
                success=True,
                data={
                    "result": result,
                    "expression": expression or f"{operation}({a}, {b})"
                },
                metadata={
                    "execution_time": execution_time
                },
                execution_time=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"❌ 计算器工具执行失败: {e}", exc_info=True)
            self._record_call(False)
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _safe_evaluate_expression(self, expression: str) -> float:
        """安全地计算数学表达式，使用AST解析避免eval安全漏洞"""
        # 验证表达式只包含安全字符
        if not re.match(r'^[\d+\-*/().\s]+$', expression):
            raise ValueError(f"不安全的表达式: {expression}")
        
        try:
            # 解析表达式为AST
            node = ast.parse(expression, mode='eval')
            
            # 递归求值
            def _eval_node(node):
                if isinstance(node, ast.Num):  # Python < 3.8
                    return node.n
                elif isinstance(node, ast.Constant):  # Python >= 3.8
                    if isinstance(node.value, (int, float)):
                        return node.value
                    else:
                        raise ValueError(f"不支持的常量类型: {type(node.value)}")
                elif isinstance(node, ast.BinOp):
                    left = _eval_node(node.left)
                    right = _eval_node(node.right)
                    op_type = type(node.op)
                    if op_type in self._safe_operators:
                        return self._safe_operators[op_type](left, right)
                    else:
                        raise ValueError(f"不支持的运算符: {op_type}")
                elif isinstance(node, ast.UnaryOp):
                    operand = _eval_node(node.operand)
                    op_type = type(node.op)
                    if op_type in self._safe_operators:
                        return self._safe_operators[op_type](operand)
                    else:
                        raise ValueError(f"不支持的一元运算符: {op_type}")
                else:
                    raise ValueError(f"不支持的语法节点: {type(node)}")
            
            result = _eval_node(node.body)
            return float(result)
            
        except (SyntaxError, ValueError, ZeroDivisionError) as e:
            raise ValueError(f"表达式计算失败: {e}")
    
    def _perform_operation(self, operation: str, a: float, b: float) -> float:
        """执行运算"""
        operations = {
            "add": lambda x, y: x + y,
            "subtract": lambda x, y: x - y,
            "multiply": lambda x, y: x * y,
            "divide": lambda x, y: x / y if y != 0 else float('inf'),
            "power": lambda x, y: x ** y,
        }
        
        if operation not in operations:
            raise ValueError(f"不支持的操作: {operation}")
        
        return operations[operation](a, b)
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """获取工具参数模式"""
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "数学表达式（如 '2 + 3'）"
                },
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide", "power"],
                    "description": "运算类型"
                },
                "a": {
                    "type": "number",
                    "description": "第一个操作数"
                },
                "b": {
                    "type": "number",
                    "description": "第二个操作数"
                }
            },
            "required": []
        }

