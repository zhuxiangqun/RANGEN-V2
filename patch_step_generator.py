import os
import re

file_path = 'src/core/reasoning/step_generator.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 定位 _parse_llm_response 函数
start_marker = 'def _parse_llm_response(self, response: str, query: str) -> List[Dict[str, Any]]:'
end_marker = 'llm_steps = None'

start_idx = content.find(start_marker)
if start_idx == -1:
    print("❌ Could not find function definition")
    exit(1)

# 找到该函数内的 llm_steps = None (这是我们要替换的结束点)
# 我们从 start_idx 开始找，找到第一个匹配的 end_marker
# 注意：我们要找的是函数内部的那个点，根据之前的 Read 输出，它在 try 块的末尾附近
# 为了更精确，我们可以找到函数定义的下一行，直到 llm_steps = None 之前的内容都替换掉

# 新的函数体 (不包含 def 行，从 docstring 开始)
new_body = """        \"\"\"解析LLM响应 - 🚀 P0改进：增强容错性\"\"\"
        try:
            self.logger.debug(f"🔍 [解析响应] 开始解析LLM响应，响应长度: {len(response)}字符")
            
            # 🚀 改进1：使用 RobustJsonExtractor 进行提取
            from src.core.utils.robust_json import RobustJsonExtractor
            parsed = RobustJsonExtractor.extract(response)
            
            if parsed:
                self.logger.debug("✅ [解析响应] RobustJsonExtractor 成功提取 JSON")
            else:
                self.logger.warning(f"⚠️ [解析响应] RobustJsonExtractor 未能提取 JSON")
                # 回退到旧的启发式逻辑（尝试从文本中提取步骤）
                response_clean = response.strip()
                
                # 🚀 检测：LLM是否直接返回了答案（而不是推理步骤）
                is_direct_answer = (
                    len(response_clean) < 100 and  # 短文本
                    not ('{' in response_clean or '[' in response_clean) and  # 不包含JSON结构
                    not ('step' in response_clean.lower() or '步骤' in response_clean) and  # 不包含步骤描述
                    not ('reasoning' in response_clean.lower() or '推理' in response_clean)  # 不包含推理过程
                )
                
                if is_direct_answer:
                    # ... (保留原有的直接答案检测逻辑)
                    print(f"❌ [解析响应] LLM直接返回了答案（'{response_clean[:50]}'），而不是JSON格式的推理步骤")
                    self.logger.error(f"❌ [解析响应] LLM直接返回了答案（'{response_clean[:50]}'），而不是JSON格式的推理步骤")
                    
                    # 🚀 检查是否有reasoning_content（思考过程）
                    if (hasattr(self, 'llm_integration') and 
                        self.llm_integration is not None and 
                        hasattr(self.llm_integration, '_last_reasoning_content')):
                        reasoning_content = self.llm_integration._last_reasoning_content
                        if reasoning_content:
                            self.logger.info(f"🔍 [解析响应] 检测到思考过程内容，长度: {len(reasoning_content)}字符")
                            # 尝试从思考过程中提取推理步骤
                            try:
                                reasoning_steps_from_thinking = self._extract_reasoning_steps_from_thinking(reasoning_content, query)
                                if reasoning_steps_from_thinking:
                                    self.logger.info(f"✅ [解析响应] 从思考过程中提取推理步骤成功: {len(reasoning_steps_from_thinking)} 步")
                                    return reasoning_steps_from_thinking
                            except Exception as extract_error:
                                self.logger.warning(f"❌ [解析响应] 从思考过程中提取推理步骤失败: {extract_error}")
                    return []
                
                # 尝试从非JSON响应中提取推理步骤
                if response and len(response.strip()) > 0:
                    self.logger.info(f"🔍 [解析响应] 尝试从非JSON响应中提取推理步骤")
                    extracted_steps = self._extract_steps_from_answer_response(response, query)
                    if extracted_steps:
                        self.logger.info(f"✅ [解析响应] 从非JSON响应中提取到 {len(extracted_steps)} 个步骤")
                        return extracted_steps
                return []
            
            # 🚀 改进3：支持多种响应格式
            """

# 查找要替换的范围
# 我们要替换的是从 docstring 开始，一直到 `llm_steps = None` 之前
# 原文中有 `"""解析LLM响应 - 🚀 P0改进：增强容错性"""`
docstring_start = content.find('"""解析LLM响应', start_idx)
if docstring_start == -1:
    print("❌ Could not find docstring")
    exit(1)

# 找到 llm_steps = None 的位置
# 我们需要找到该函数内的那个位置。
# 我们可以利用缩进，或者利用上下文。
# 原文中 `llm_steps = None` 前面是 `# 🚀 改进3：支持多种响应格式`
target_end_marker = '            # 🚀 改进3：支持多种响应格式'
end_idx = content.find(target_end_marker, docstring_start)

if end_idx == -1:
    print("❌ Could not find end marker")
    exit(1)

# 执行替换
new_content = content[:docstring_start] + new_body + content[end_idx:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Successfully patched step_generator.py")
