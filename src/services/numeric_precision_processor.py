"""
数值精确度处理模块
改进数值处理逻辑，保持原始数据的上下文信息，解决精度损失问题

主要功能：
1. 保持原始数值的精确度
2. 智能单位转换（米/英尺）
3. 上下文感知的数值格式化
4. 精度损失的检测和修复
"""

import logging
import re
import math
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal, getcontext, ROUND_HALF_UP
import json

logger = logging.getLogger(__name__)

# 设置高精度计算环境
getcontext().prec = 20  # 设置20位精度

class NumericUnit(Enum):
    """数值单位"""
    METERS = "meters"
    FEET = "feet"
    FLOORS = "floors"
    SQUARE_METERS = "square_meters"
    SQUARE_FEET = "square_feet"
    UNKNOWN = "unknown"

@dataclass
class PreciseNumber:
    """精确数值表示"""
    value: Decimal
    unit: NumericUnit
    original_string: Optional[str] = None
    confidence: float = 1.0
    source_context: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'value': str(self.value),
            'unit': self.unit.value,
            'original_string': self.original_string,
            'confidence': self.confidence,
            'source_context': self.source_context,
            'approximate_feet': float(self.to_feet()),
            'approximate_meters': float(self.to_meters())
        }
    
    def to_feet(self) -> Decimal:
        """转换为英尺"""
        if self.unit == NumericUnit.FEET:
            return self.value
        elif self.unit == NumericUnit.METERS:
            return self.value * Decimal('3.28084')
        elif self.unit == NumericUnit.FLOORS:
            # 假设每层3.3米
            return self.value * Decimal('3.3') * Decimal('3.28084')
        else:
            raise ValueError(f"无法将 {self.unit} 转换为英尺")
    
    def to_meters(self) -> Decimal:
        """转换为米"""
        if self.unit == NumericUnit.METERS:
            return self.value
        elif self.unit == NumericUnit.FEET:
            return self.value / Decimal('3.28084')
        elif self.unit == NumericUnit.FLOORS:
            return self.value * Decimal('3.3')
        else:
            raise ValueError(f"无法将 {self.unit} 转换为米")
    
    def format_with_precision(self, target_unit: NumericUnit, max_decimals: int = 2) -> str:
        """格式化为指定单位的字符串，保持精度"""
        if target_unit == NumericUnit.FEET:
            target_value = self.to_feet()
        elif target_unit == NumericUnit.METERS:
            target_value = self.to_meters()
        else:
            target_value = self.value
        
        # 使用四舍五入而不是截断
        quantized_value = target_value.quantize(
            Decimal(f'1e-{max_decimals}'), 
            rounding=ROUND_HALF_UP
        )
        
        # 移除尾随的零
        formatted = format(quantized_value, 'f').rstrip('0').rstrip('.')
        
        # 添加单位
        unit_symbol = {
            NumericUnit.METERS: 'm',
            NumericUnit.FEET: 'ft',
            NumericUnit.FLOORS: 'floors'
        }.get(target_unit, '')
        
        return f"{formatted} {unit_symbol}" if unit_symbol else formatted
    
    def is_approximate(self) -> bool:
        """判断是否为近似值"""
        return self.confidence < 0.95 or "approximately" in (self.original_string or "").lower()

class NumericPrecisionProcessor:
    """数值精确度处理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.unit_patterns = self._build_unit_patterns()
        self.precision_threshold = self.config.get('precision_threshold', 0.01)
        
    def _build_unit_patterns(self) -> Dict[str, Tuple[NumericUnit, float]]:
        """构建单位识别模式"""
        return {
            # 米制单位
            r'(\d+(?:\.\d+)?)\s*m\b': (NumericUnit.METERS, 1.0),
            r'(\d+(?:\.\d+)?)\s*meter[s]?\b': (NumericUnit.METERS, 1.0),
            r'(\d+(?:\.\d+)?)\s*metre[s]?\b': (NumericUnit.METERS, 1.0),
            
            # 英制单位
            r'(\d+(?:\.\d+)?)\s*ft\b': (NumericUnit.FEET, 1.0),
            r'(\d+(?:\.\d+)?)\s*feet\b': (NumericUnit.FEET, 1.0),
            r'(\d+(?:\.\d+)?)\s*foot\b': (NumericUnit.FEET, 1.0),
            r'(\d+(?:\.\d+)?)\s*\'\s*(?:\d+(?:\.\d+)?\s*")?': (NumericUnit.FEET, 1.0),  # 英尺英寸格式
            
            # 楼层
            r'(\d+(?:\.\d+)?)\s*floor[s]?\b': (NumericUnit.FLOORS, 1.0),
            r'(\d+(?:\.\d+)?)\s*story[ies]?\b': (NumericUnit.FLOORS, 1.0),
            r'(\d+(?:\.\d+)?)\s*storey[s]?\b': (NumericUnit.FLOORS, 1.0),
            
            # 面积单位
            r'(\d+(?:\.\d+)?)\s*m²\b': (NumericUnit.SQUARE_METERS, 1.0),
            r'(\d+(?:\.\d+)?)\s*sq\s*m\b': (NumericUnit.SQUARE_METERS, 1.0),
            r'(\d+(?:\.\d+)?)\s*ft²\b': (NumericUnit.SQUARE_FEET, 1.0),
            r'(\d+(?:\.\d+)?)\s*sq\s*ft\b': (NumericUnit.SQUARE_FEET, 1.0),
        }
    
    def extract_numbers(self, text: str, context: Optional[str] = None) -> List[PreciseNumber]:
        """从文本中提取数值，保持精确度"""
        numbers = []
        
        for pattern, (unit, multiplier) in self.unit_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                try:
                    # 提取数值部分
                    value_str = match.group(1)
                    value = Decimal(value_str) * Decimal(str(multiplier))
                    
                    # 检测精确度指示词
                    original_full_match = match.group(0)
                    confidence = self._calculate_confidence(original_full_match, value_str)
                    
                    # 创建精确数值对象
                    precise_num = PreciseNumber(
                        value=value,
                        unit=unit,
                        original_string=original_full_match,
                        confidence=confidence,
                        source_context=context
                    )
                    
                    numbers.append(precise_num)
                    
                except (ValueError, decimal.InvalidOperation) as e:
                    logger.warning(f"解析数值失败: {match.group(0)} - {e}")
                    continue
        
        return numbers
    
    def _calculate_confidence(self, full_match: str, value_str: str) -> float:
        """计算数值置信度"""
        confidence = 1.0
        
        # 检查近似词
        approximate_words = ['approximately', 'about', 'around', 'roughly', 'nearly', 'almost', 'over', 'under']
        full_lower = full_match.lower()
        
        for word in approximate_words:
            if word in full_lower:
                confidence -= 0.2
                break
        
        # 检查小数位数（更多小数位通常表示更高精度）
        decimal_places = len(value_str.split('.')[-1]) if '.' in value_str else 0
        if decimal_places == 0:
            confidence -= 0.1  # 整数可能是近似值
        elif decimal_places >= 3:
            confidence = min(confidence + 0.1, 1.0)  # 高精度
        
        # 检查范围表达式
        range_patterns = [r'\d+-\d+', r'between\s+\d+\s+and\s+\d+', r'\d+\s+to\s+\d+']
        for pattern in range_patterns:
            if re.search(pattern, full_lower):
                confidence -= 0.3
                break
        
        return max(confidence, 0.1)
    
    def convert_with_precision_loss_detection(
        self, 
        number: PreciseNumber, 
        target_unit: NumericUnit
    ) -> Tuple[PreciseNumber, Optional[str]]:
        """精确转换并检测精度损失"""
        try:
            if number.unit == target_unit:
                return number, None
            
            # 执行转换
            if target_unit == NumericUnit.FEET:
                converted_value = number.to_feet()
            elif target_unit == NumericUnit.METERS:
                converted_value = number.to_meters()
            else:
                return number, f"不支持转换到 {target_unit}"
            
            converted_number = PreciseNumber(
                value=converted_value,
                unit=target_unit,
                original_string=number.original_string,
                confidence=number.confidence,
                source_context=number.source_context
            )
            
            # 检测精度损失
            precision_loss = self._detect_precision_loss(number, converted_number)
            
            return converted_number, precision_loss
        
        except Exception as e:
            logger.error(f"数值转换失败: {e}")
            return number, f"转换错误: {str(e)}"
    
    def _detect_precision_loss(
        self, 
        original: PreciseNumber, 
        converted: PreciseNumber
    ) -> Optional[str]:
        """检测精度损失"""
        # 如果是米英尺之间的转换，检查是否为整数转换
        if {original.unit, converted.unit} == {NumericUnit.METERS, NumericUnit.FEET}:
            # 检查是否从精确小数变为整数
            if '.' in str(original.value) and '.' not in str(converted.value):
                return "可能存在精度损失：精确值被四舍五入为整数"
            
            # 检查反向转换的一致性
            if original.unit == NumericUnit.METERS:
                reverse_converted = converted.to_meters()
                diff = abs(reverse_converted - original.value)
                if diff > Decimal(str(self.precision_threshold)):
                    return f"转换精度损失超过阈值: {diff}"
        
        return None
    
    def format_building_height(
        self, 
        number: PreciseNumber, 
        preferred_unit: Optional[NumericUnit] = None
    ) -> Dict[str, str]:
        """格式化建筑高度，提供多种表示方式"""
        formats = {}
        
        # 原始格式
        formats['original'] = number.original_string or str(number.value)
        
        # 米制
        meters = number.to_meters()
        formats['meters_precise'] = f"{meters} m"
        formats['meters_rounded'] = self._round_to_sensible(meters, 'm')
        
        # 英制
        feet = number.to_feet()
        formats['feet_precise'] = f"{feet} ft"
        formats['feet_rounded'] = self._round_to_sensible(feet, 'ft')
        
        # 自然语言格式
        formats['natural_language'] = self._create_natural_language(number, preferred_unit)
        
        # 精度说明
        if number.is_approximate():
            formats['precision_note'] = "approximately"
        else:
            formats['precision_note'] = "exactly"
        
        return formats
    
    def _round_to_sensible(self, value: Decimal, unit: str) -> str:
        """智能舍入到合理的精度"""
        if unit == 'm':
            # 米：根据数值大小决定小数位数
            if value < 10:
                decimals = 2
            elif value < 100:
                decimals = 1
            else:
                decimals = 0
        elif unit == 'ft':
            # 英尺：通常不显示小数，除非数值很小
            if value < 50:
                decimals = 1
            else:
                decimals = 0
        else:
            decimals = 2
        
        quantized = value.quantize(
            Decimal(f'1e-{decimals}'), 
            rounding=ROUND_HALF_UP
        )
        formatted = format(quantized, 'f').rstrip('0').rstrip('.')
        
        return f"{formatted} {unit}"
    
    def _create_natural_language(
        self, 
        number: PreciseNumber, 
        preferred_unit: Optional[NumericUnit]
    ) -> str:
        """创建自然语言描述"""
        unit = preferred_unit or number.unit
        
        if unit == NumericUnit.FEET:
            value = number.to_feet()
            unit_name = "feet"
        elif unit == NumericUnit.METERS:
            value = number.to_meters()
            unit_name = "meters"
        else:
            value = number.value
            unit_name = number.unit.value.replace('_', ' ')
        
        # 添加近似词
        prefix = "approximately " if number.is_approximate() else ""
        
        # 格式化数值
        if '.' in str(value):
            formatted = self._round_to_sensible(value, unit_name[0])
        else:
            formatted = f"{int(value)} {unit_name}"
        
        return f"{prefix}{formatted}"
    
    def compare_numbers(self, num1: PreciseNumber, num2: PreciseNumber) -> Dict[str, Any]:
        """比较两个精确数值"""
        # 统一单位进行比较
        if num1.unit != num2.unit:
            num2_converted, error = self.convert_with_precision_loss_detection(num2, num1.unit)
            if error:
                return {'error': f"无法比较: {error}"}
            num2 = num2_converted
        
        diff = num1.value - num2.value
        relative_diff = abs(diff) / max(abs(num1.value), abs(num2.value)) if num1.value != 0 else 0
        
        return {
            'difference': float(diff),
            'relative_difference': float(relative_diff),
            'is_equal': abs(diff) < Decimal(str(self.precision_threshold)),
            'which_greater': 'first' if diff > 0 else 'second' if diff < 0 else 'equal',
            'confidence': min(num1.confidence, num2.confidence),
            'precision_warning': 'Significant precision loss possible' if relative_diff > 0.01 else None
        }
    
    def extract_building_dimensions(self, text: str) -> Dict[str, List[PreciseNumber]]:
        """提取建筑尺寸信息"""
        dimensions = {
            'height': [],
            'floors': [],
            'area': [],
            'other': []
        }
        
        numbers = self.extract_numbers(text)
        
        for number in numbers:
            if number.unit in [NumericUnit.METERS, NumericUnit.FEET]:
                # 根据上下文判断是否为高度
                context_lower = (number.source_context or '').lower()
                if any(word in context_lower for word in ['height', 'tall', 'high', 'story', 'floor']):
                    dimensions['height'].append(number)
                else:
                    dimensions['other'].append(number)
            elif number.unit == NumericUnit.FLOORS:
                dimensions['floors'].append(number)
            elif number.unit in [NumericUnit.SQUARE_METERS, NumericUnit.SQUARE_FEET]:
                dimensions['area'].append(number)
            else:
                dimensions['other'].append(number)
        
        return dimensions

# 全局处理器实例
_numeric_processor = None

def get_numeric_processor() -> NumericPrecisionProcessor:
    """获取数值处理器实例"""
    global _numeric_processor
    if _numeric_processor is None:
        _numeric_processor = NumericPrecisionProcessor()
    return _numeric_processor

def process_text_with_precision(text: str, context: Optional[str] = None) -> Dict[str, Any]:
    """处理文本中的数值，保持精确度"""
    processor = get_numeric_processor()
    numbers = processor.extract_numbers(text, context)
    
    result = {
        'numbers_found': len(numbers),
        'extracted_numbers': [num.to_dict() for num in numbers],
        'height_dimensions': [],
        'floor_counts': [],
        'areas': [],
        'precision_issues': []
    }
    
    for num in numbers:
        if num.unit in [NumericUnit.METERS, NumericUnit.FEET]:
            # 检查是否为高度信息
            if any(word in (context or '').lower() for word in ['height', 'tall', 'high']):
                formatted = processor.format_building_height(num)
                result['height_dimensions'].append(formatted)
        elif num.unit == NumericUnit.FLOORS:
            result['floor_counts'].append(num.to_dict())
        elif num.unit in [NumericUnit.SQUARE_METERS, NumericUnit.SQUARE_FEET]:
            result['areas'].append(num.to_dict())
    
    return result