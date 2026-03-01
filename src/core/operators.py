from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import ast
import re
import operator

@dataclass
class OperatorResult:
    success: bool
    data: Any
    confidence: float
    metadata: Dict[str, Any]

class BaseOperator(ABC):
    """推理算子基类"""
    
    def __init__(self, name: str):
        self.name = name
        
    @abstractmethod
    async def execute(self, inputs: Dict[str, Any], context: Any) -> OperatorResult:
        """执行算子逻辑"""
        pass

class ExtractionOperator(BaseOperator):
    """提取算子: 从文本中提取结构化信息"""
    def __init__(self):
        super().__init__("extraction")
        
    async def execute(self, inputs: Dict[str, Any], context: Any) -> OperatorResult:
        # 模拟提取逻辑
        text = inputs.get("text", "")
        schema = inputs.get("schema", {})
        
        # 实际应调用 LLM 进行提取
        return OperatorResult(
            success=True,
            data={"entities": ["Entity1", "Entity2"]},
            confidence=0.9,
            metadata={"source_len": len(text)}
        )

class ComparisonOperator(BaseOperator):
    """比对算子: 比较多源信息"""
    def __init__(self):
        super().__init__("comparison")
        
    async def execute(self, inputs: Dict[str, Any], context: Any) -> OperatorResult:
        source_a = inputs.get("source_a")
        source_b = inputs.get("source_b")
        
        # 实际应调用 LLM 进行比对
        return OperatorResult(
            success=True,
            data={"diff": "None", "common": "All"},
            confidence=0.85,
            metadata={}
        )

class SynthesisOperator(BaseOperator):
    """合成算子: 综合信息生成结论"""
    def __init__(self):
        super().__init__("synthesis")
        
    async def execute(self, inputs: Dict[str, Any], context: Any) -> OperatorResult:
        fragments = inputs.get("fragments", [])
        
        return OperatorResult(
            success=True,
            data="Synthesized conclusion based on fragments.",
            confidence=0.9,
            metadata={"fragment_count": len(fragments)}
        )

class ToolUseOperator(BaseOperator):
    """工具调用算子: 执行外部工具"""
    def __init__(self):
        super().__init__("tool_use")
        self._safe_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }
        
    def _safe_eval(self, expression: str) -> float:
        """安全地计算数学表达式"""
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
        
    async def execute(self, inputs: Dict[str, Any], context: Any) -> OperatorResult:
        tool_name = inputs.get("tool_name")
        tool_args = inputs.get("tool_args", {})
        
        # 模拟工具执行
        if tool_name == "calculator":
            expression = tool_args.get("expression", "0")
            try:
                result = self._safe_eval(expression)
                return OperatorResult(success=True, data=result, confidence=1.0, metadata={})
            except ValueError as e:
                return OperatorResult(success=False, data=None, confidence=0.0, metadata={"error": str(e)})
            
        return OperatorResult(success=False, data=None, confidence=0.0, metadata={"error": "Tool not found"})
