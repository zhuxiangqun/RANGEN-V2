import json
import re
import logging
from typing import Any, Optional, Union, Dict, List

logger = logging.getLogger(__name__)

class RobustJsonExtractor:
    """
    基于 DDL (Defensive Depth Layering) 原则的鲁棒 JSON 提取器。
    
    架构设计：
    - Layer 1: 输入防御 (Input Defense) - 快速过滤
    - Layer 2: 精确格式 (Precise Format) - 标准解析
    - Layer 3: 结构感知 (Structure Aware) - 栈算法提取
    - Layer 4: 启发式恢复 (Heuristic Recovery) - 常见错误修复
    - Layer 5: AI 修复 (AI Repair) - [预留接口]
    - Layer 6: 优雅降级 (Graceful Degradation) - 失败处理
    """

    @classmethod
    def extract(cls, text: str) -> Optional[Union[Dict[str, Any], List[Any]]]:
        """执行多层防御提取流程"""
        
        # === Layer 1: Input Defense ===
        # 快速过滤无效输入，避免浪费资源
        text = cls._layer1_input_defense(text)
        if text is None:
            return None
            
        # === Layer 2.5: Thinking Process Cleanup (针对 DeepSeek R1) ===
        # 显式移除 <think> 标签，这比依赖栈算法更可靠
        # 增强：支持多种标签格式，以及未闭合的情况
        text_clean = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text_clean = re.sub(r'<thinking>.*?</thinking>', '', text_clean, flags=re.DOTALL | re.IGNORECASE)
        
        # 激进清理：如果开头不是 { 或 [，尝试找到第一个 { 或 [ 并截断前面的内容
        # 这处理了 "Here is the JSON:\n```json\n..." 或 "Thinking...\n..." 的情况
        if text_clean and not text_clean.strip().startswith(('{', '[')):
            match = re.search(r'([\{\[])', text_clean)
            if match:
                text_clean = text_clean[match.start():]
        
        text_clean = text_clean.strip()
        
        # === Layer 2: Precise Format ===
        # 尝试标准解析 (最快，成本最低)
        # 优先使用清理后的文本，如果失败则尝试原始文本
        result = cls._layer2_precise_format(text_clean)
        if result is not None:
            logger.debug("Layer 2: Precise format match (cleaned text)")
            return result
            
        if text_clean != text:
             result = cls._layer2_precise_format(text)
             if result is not None:
                 logger.debug("Layer 2: Precise format match (original text)")
                 return result
            
        # === Layer 3: Structure Aware ===
        # 核心层：使用栈算法从噪声中提取 JSON
        # 优先使用清理后的文本
        result = cls._layer3_structure_aware(text_clean)
        if result is not None:
            logger.debug("Layer 3: Structure aware extraction success")
            return result
            
        # === Layer 4: Heuristic Recovery ===
        # 尝试修复常见的小错误
        result = cls._layer4_heuristic_recovery(text_clean)
        if result is not None:
            logger.warning("Layer 4: Heuristic recovery used")
            return result
            
        # === Layer 6: Graceful Degradation ===
        logger.warning("Layer 6: All extraction layers failed")
        return None

    @staticmethod
    def _layer1_input_defense(text: str) -> Optional[str]:
        """Layer 1: 输入验证与清理"""
        if not text or not isinstance(text, str):
            return None
        
        # 基础清理
        text = text.strip()
        
        # 快速特征检查
        if '{' not in text and '[' not in text:
            return None
            
        # 长度防御 (防止恶意长文本导致栈溢出)
        if len(text) > 100000:
            logger.warning("Input text too long, truncating to 100k chars")
            text = text[:100000]
            
        return text

    @staticmethod
    def _layer2_precise_format(text: str) -> Optional[Any]:
        """Layer 2: 精确格式匹配 (直接解析 & Markdown)"""
        # 1. 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
            
        # 2. 尝试 Markdown 代码块
        patterns = [
            r'```(?:json)?\s*(\{.*?\})\s*```',  # ```json {...} ```
            r'```(?:json)?\s*(\[.*?\])\s*```'   # ```json [...] ```
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        return None

    @staticmethod
    def _layer3_structure_aware(text: str) -> Optional[Any]:
        """Layer 3: 结构感知提取 (基于栈算法)"""
        # 复用之前的栈算法，这对于从 Thinking Process 中提取 JSON 至关重要
        return RobustJsonExtractor._extract_outermost_structure(text)

    @staticmethod
    def _layer4_heuristic_recovery(text: str) -> Optional[Any]:
        """Layer 4: 启发式恢复 (修复常见格式错误)"""
        # 1. 尝试使用栈算法提取的内容进行修复，而不是修复整个文本
        # 这样可以避免误伤正文中的 Python 代码示例
        candidate = RobustJsonExtractor._extract_outermost_structure(text)
        if not candidate and '{' in text:
             # 如果栈算法失败（可能是因为括号不匹配），尝试正则贪婪匹配作为候选
             try:
                 start = text.find('{')
                 end = text.rfind('}')
                 if start != -1 and end != -1:
                     candidate_str = text[start:end+1]
                 else:
                     candidate_str = text
             except:
                 candidate_str = text
        elif isinstance(candidate, (dict, list)):
             # 如果已经是有效对象，无需修复
             return candidate
        else:
             # candidate 可能是 None，使用原始文本
             candidate_str = text

        # 定义常见错误修复规则
        replacements = [
            # Python Boolean -> JSON Boolean
            (r'\bTrue\b', 'true'),
            (r'\bFalse\b', 'false'),
            (r'\bNone\b', 'null'),
            # 数学等式中的等号转义 (针对 "a=1" 这种情况，如果它不在字符串中)
            # 这是一个非常激进的修复，可能会误伤。我们尝试将其限制在特定上下文中。
            # 更好的方法可能是先转义所有反斜杠
            (r'\\', r'\\\\'),
        ]
        
        fixed_text = candidate_str
        for pattern, repl in replacements:
            fixed_text = re.sub(pattern, repl, fixed_text)
            
        try:
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            pass
            
        # 尝试更激进的单引号修复 (仅当上述修复无效时)
        # 注意：这可能会破坏包含单引号的字符串内容，风险较高
        try:
            # 简单的单引号转双引号，假设 key 和 value 都是单引号包裹
            # 这是一个非常粗糙的近似，仅用于挽救严重错误的 JSON
            potential_json = candidate_str.replace("'", '"')
            return json.loads(potential_json)
        except json.JSONDecodeError:
            pass
            
        return None

    @staticmethod
    def _extract_outermost_structure(text: str) -> Optional[Any]:
        """
        使用栈算法寻找最外层的完整 JSON 结构 ({...} 或 [...])。
        这种方法可以忽略 JSON 前后的噪声文本。
        """
        stack = []
        start_index = -1
        
        # 扫描寻找第一个开括号
        for i, char in enumerate(text):
            if char == '{' or char == '[':
                stack.append(char)
                start_index = i
                break
        
        if start_index == -1:
            return None
            
        # 从第一个开括号开始扫描
        current_in_string = False
        escape_next = False
        
        for i in range(start_index + 1, len(text)):
            char = text[i]
            
            # 处理字符串内部字符 (忽略字符串内的括号)
            if current_in_string:
                if escape_next:
                    escape_next = False
                elif char == '\\':
                    escape_next = True
                elif char == '"':
                    current_in_string = False
                continue
            
            if char == '"':
                current_in_string = True
                continue
                
            # 处理括号嵌套
            if char == '{' or char == '[':
                stack.append(char)
            elif char == '}' or char == ']':
                if not stack:
                    # 栈空了但遇到了闭括号，说明结构不匹配
                    return None
                
                last_open = stack.pop()
                # 检查括号是否匹配
                if (char == '}' and last_open != '{') or (char == ']' and last_open != '['):
                    return None
                
                # 如果栈空了，说明找到了最外层的闭括号
                if not stack:
                    candidate = text[start_index : i+1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        # 即使括号匹配，内容可能仍是非法 JSON (交给 Layer 4 修复)
                        return None
                        
        # 🚀 宽松模式：如果循环结束时栈不为空（即括号未闭合），尝试自动补全
        if stack:
            logger.warning(f"Layer 3: JSON incomplete, attempting to close brackets. Open brackets: {len(stack)}")
            # 构建补全字符串
            completion = ""
            while stack:
                bracket = stack.pop()
                if bracket == '{':
                    completion += '}'
                elif bracket == '[':
                    completion += ']'
            
            # 尝试补全并解析
            # 注意：我们只取从 start_index 开始到最后的文本
            candidate = text[start_index:] + completion
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                return None
                        
        return None
