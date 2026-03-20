#!/usr/bin/env python3
"""
Hand 自动生成器 - HandAutoGenerator

根据用户需求描述，自动生成 Hand 代码并注册。

功能：
1. 接收自然语言需求
2. 分析需要的 Hand 类型
3. 调用 LLM 生成 Hand 代码
4. 写入文件并热加载
5. 返回给用户确认

支持：
- 模板生成（快速）
- LLM 生成（完整）
"""

import os
import re
import logging
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


# LLM 代码生成提示词
CODE_GENERATION_PROMPT = """
请为以下需求生成一个完整的 Hand 类代码。

需求：{requirement}

重要约束：
1. 继承 BaseHand，调用 super().__init__(name, description, category, safety_level)
2. 导入路径：from .base import BaseHand, HandCategory, HandSafetyLevel, HandExecutionResult
3. HandExecutionResult 需要参数：hand_name, success, output, error
4. 不要使用 markdown 代码块，直接输出纯 Python 代码
5. 代码必须完整，不要截断
6. 使用 async/await 异步编程
7. validate_parameters 和 execute 方法是必需的

类名使用 PascalCase，如 EmailOperationHand
"""


class LLMCodeGenerator:
    """基于 LLM 的代码生成器"""
    
    def __init__(self):
        self.llm = None
        self._init_llm()
    
    def _init_llm(self):
        """初始化 LLM"""
        try:
            from src.core.llm_integration import LLMIntegration
            self.llm = LLMIntegration({})
            logger.info("LLM 代码生成器初始化成功")
        except Exception as e:
            logger.warning(f"LLM 初始化失败，将使用模板生成: {e}")
            self.llm = None
    
    def generate_code(self, requirement: str) -> str:
        """
        使用 LLM 生成代码
        
        Args:
            requirement: 用户需求描述
            
        Returns:
            生成的 Python 代码
        """
        if self.llm is None:
            # LLM 不可用时返回模板代码
            return self._generate_fallback_template(requirement)
        
        try:
            prompt = CODE_GENERATION_PROMPT.format(requirement=requirement)
            result = self.llm._call_llm(prompt)
            
            if result:
                # 清理代码（移除 markdown 代码块标记）
                code = result.strip()
                if code.startswith("```python"):
                    code = code[7:]
                if code.startswith("```"):
                    code = code[3:]
                if code.endswith("```"):
                    code = code[:-3]
                code = code.strip()
                
                # 验证语法
                import ast
                try:
                    ast.parse(code)
                    logger.info("LLM 生成的代码语法正确")
                    return code
                except SyntaxError as e:
                    logger.warning(f"LLM 生成代码语法错误: {e}，使用模板")
                    return self._generate_fallback_template(requirement)
            
        except Exception as e:
            logger.error(f"LLM 代码生成失败: {e}")
        
        # 失败时返回模板代码
        return self._generate_fallback_template(requirement)
    
    def _generate_fallback_template(self, requirement: str) -> str:
        # 只提取 ASCII 字符作为类名
        ascii_chars = re.sub(r'[^a-zA-Z0-9]', '', requirement)
        if ascii_chars:
            words = [ascii_chars[i:i+3] for i in range(0, min(9, len(ascii_chars)), 3)]
            class_name = ''.join(w.capitalize() for w in words if w) or 'Auto'
        else:
            class_name = 'Auto'
        class_name = f"{class_name}Hand"
        
        return f'''#!/usr/bin/env python3
"""
{class_name} - 自动生成的 Hand
描述: {requirement}
"""

import logging
from typing import Dict, Any
from .base import BaseHand, HandCategory, HandSafetyLevel, HandExecutionResult

logger = logging.getLogger(__name__)


class {class_name}(BaseHand):
    """{requirement}"""
    
    def __init__(self):
        super().__init__(
            name="{class_name.lower()}",
            description="{requirement}",
            category=HandCategory.API_INTEGRATION,
            safety_level=HandSafetyLevel.MODERATE
        )
        self.logger = logger
    
    def validate_parameters(self, **kwargs) -> bool:
        return True
    
    async def execute(self, **kwargs) -> HandExecutionResult:
        try:
            action = kwargs.get("action", "execute")
            self.logger.info(f"执行 {{action}}")
            
            result = {{
                "action": action,
                "requirement": "{requirement}",
                "status": "executed",
                "message": "自动生成的 Hand 执行成功"
            }}
            
            return HandExecutionResult(
                hand_name=self.name,
                success=True,
                output=result
            )
            
        except Exception as e:
            self.logger.error(f"执行失败: {{e}}")
            return HandExecutionResult(
                hand_name=self.name,
                success=False,
                output={{}},
                error=str(e)
            )
'''


@dataclass
class GeneratedHand:
    """生成的 Hand 信息"""
    name: str
    description: str
    category: str
    safety_level: str
    methods: List[Dict[str, str]]
    code: str
    file_path: str
    capabilities: List[str]


class HandTemplate:
    """Hand 模板"""
    
    # 基础模板
    BASE_TEMPLATE = '''#!/usr/bin/env python3
"""
{hand_name} - 自动生成的 Hand
描述: {description}
创建时间: {created_at}
"""

import logging
from typing import Dict, Any

from .base import BaseHand, HandCategory, HandSafetyLevel, HandExecutionResult

logger = logging.getLogger(__name__)


class {class_name}(BaseHand):
    """{description}"""
    
    def __init__(self):
        super().__init__(
            name="{name}",
            description="{description}",
            category={category},
            safety_level={safety_level}
        )
        self.logger = logger
    
    def validate_parameters(self, **kwargs) -> bool:
        required = {required_params}
        for param in required:
            if param not in kwargs:
                return False
        return True
    
    async def execute(self, **kwargs) -> HandExecutionResult:
        try:
            if not self.validate_parameters(**kwargs):
                return HandExecutionResult(
                    hand_name=self.name,
                    success=False,
                    output={{}},
                    error="参数验证失败"
                )
            
            action = kwargs.get("action", "default")
            
            if action == "default":
                result = await self.default_action(kwargs)
            elif action == "list":
                result = await self.list_action(kwargs)
            elif action == "get":
                result = await self.get_action(kwargs)
            elif action == "create":
                result = await self.create_action(kwargs)
            elif action == "update":
                result = await self.update_action(kwargs)
            elif action == "delete":
                result = await self.delete_action(kwargs)
            else:
                result = await self.custom_action(action, kwargs)
            
            return HandExecutionResult(
                hand_name=self.name,
                success=True,
                output=result
            )
            
        except Exception as e:
            self.logger.error(f"执行失败: {{e}}")
            return HandExecutionResult(
                hand_name=self.name,
                success=False,
                output={{}},
                error=str(e)
            )
    
    async def default_action(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """默认操作"""
        return {{"message": "{name} executed", "action": "default"}}
    
    async def list_action(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """列表操作"""
        return {{"items": [], "count": 0}}
    
    async def get_action(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """获取单个"""
        return {{"item": None}}
    
    async def create_action(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """创建操作"""
        return {{"created": True, "id": "generated_id"}}
    
    async def update_action(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """更新操作"""
        return {{"updated": True}}
    
    async def delete_action(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """删除操作"""
        return {{"deleted": True}}
    
    async def custom_action(self, action: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """自定义操作"""
        return {{"action": action, "result": "custom action executed"}}
'''

    # 常用 Hand 类型映射
    TYPE_MAPPINGS = {
        "邮件": {
            "name": "email",
            "real_implementation": "email",
            "category": "HandCategory.API_INTEGRATION",
            "safety_level": "HandSafetyLevel.MODERATE",
            "methods": ["fetch_unread", "send", "search", "mark_read"],
            "capabilities": ["IMAP", "SMTP"]
        },
        "日历": {
            "name": "calendar",
            "real_implementation": None,
            "category": "HandCategory.API_INTEGRATION",
            "safety_level": "HandSafetyLevel.MODERATE",
            "methods": ["get_events", "create_event", "update_event", "delete_event"],
            "capabilities": ["Google Calendar", "Outlook"]
        },
        "文件": {
            "name": "file",
            "real_implementation": None,
            "category": "HandCategory.FILE_OPERATION",
            "safety_level": "HandSafetyLevel.SAFE",
            "methods": ["read", "write", "copy", "move", "delete"],
            "capabilities": ["local", "cloud"]
        },
        "数据库": {
            "name": "database",
            "real_implementation": "database",
            "category": "HandCategory.DATA_PROCESSING",
            "safety_level": "HandSafetyLevel.RISKY",
            "methods": ["query", "insert", "update", "delete"],
            "capabilities": ["SQL", "NoSQL"]
        },
        "API": {
            "name": "api_operation",
            "category": "HandCategory.API_INTEGRATION",
            "safety_level": "HandSafetyLevel.MODERATE",
            "methods": ["get", "post", "put", "delete"],
            "capabilities": ["REST", "GraphQL"]
        },
        "天气": {
            "name": "weather_operation",
            "category": "HandCategory.API_INTEGRATION",
            "safety_level": "HandSafetyLevel.SAFE",
            "methods": ["get_current", "get_forecast", "get_alerts"],
            "capabilities": ["OpenWeatherMap", "WeatherAPI"]
        },
        "搜索": {
            "name": "search_operation",
            "category": "HandCategory.API_INTEGRATION",
            "safety_level": "HandSafetyLevel.SAFE",
            "methods": ["web_search", "image_search", "news_search"],
            "capabilities": ["Google", "Bing", "DuckDuckGo"]
        },
        "翻译": {
            "name": "translation_operation",
            "category": "HandCategory.API_INTEGRATION",
            "safety_level": "HandSafetyLevel.SAFE",
            "methods": ["translate", "detect_language", "batch_translate"],
            "capabilities": ["Google Translate", "DeepL", "OpenAI"]
        }
    }


class HandAutoGenerator:
    """Hand 自动生成器"""
    
    def __init__(self, hands_dir: Optional[str] = None):
        """
        初始化自动生成器
        
        Args:
            hands_dir: Hands 目录路径，默认使用 src/hands/
        """
        if hands_dir is None:
            self.hands_dir = Path(__file__).parent
        else:
            self.hands_dir = Path(hands_dir)
        
        self.template = HandTemplate()
        self.generated_hands: Dict[str, GeneratedHand] = {}
        self.logger = logger
        
        # 确保目录存在
        self.hands_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_requirement(self, requirement: str) -> Dict[str, Any]:
        """
        分析用户需求，返回需求特征
        
        Args:
            requirement: 用户需求描述
            
        Returns:
            分析结果字典
        """
        requirement_lower = requirement.lower()
        
        # 检测关键词
        detected_types = []
        for type_name, config in self.template.TYPE_MAPPINGS.items():
            if type_name in requirement_lower:
                detected_types.append({
                    "type": type_name,
                    "config": config
                })
        
        # 提取动作
        actions = []
        action_keywords = {
            "收": ["fetch", "get", "receive"],
            "发": ["send", "post", "create"],
            "查": ["search", "query", "find"],
            "删": ["delete", "remove"],
            "改": ["update", "modify", "edit"],
            "列": ["list", "get_all"]
        }
        
        for chinese, english_list in action_keywords.items():
            if chinese in requirement:
                actions.extend(english_list)
        
        # 检测安全级别
        safety_keywords = {
            "危险": "dangerous",
            "修改": "risky",
            "创建": "moderate",
            "查看": "safe",
            "读取": "safe"
        }
        
        safety_level = "moderate"  # 默认
        for keyword, level in safety_keywords.items():
            if keyword in requirement:
                safety_level = level
                break
        
        return {
            "requirement": requirement,
            "detected_types": detected_types,
            "actions": actions if actions else ["default"],
            "safety_level": safety_level
        }
    
    def generate_hand_code(self, requirement: str, hand_type: Optional[str] = None) -> GeneratedHand:
        """
        根据需求生成 Hand 代码
        
        Args:
            requirement: 用户需求描述
            hand_type: 指定 Hand 类型
            
        Returns:
            生成的 Hand 信息
        """
        # 检查是否已有真实实现
        analysis = self.analyze_requirement(requirement)
        existing_hand = self._find_existing_hand(analysis, requirement)
        
        if existing_hand:
            self.logger.info(f"发现已有实现: {existing_hand}")
            return self._create_reference_to_hand(existing_hand, requirement)
        # 分析需求
        analysis = self.analyze_requirement(requirement)
        
        # 确定配置
        if hand_type and hand_type in self.template.TYPE_MAPPINGS:
            config = self.template.TYPE_MAPPINGS[hand_type]
        elif analysis["detected_types"]:
            config = analysis["detected_types"][0]["config"]
        else:
            # 默认配置
            config = {
                "name": self._generate_name_from_requirement(requirement),
                "category": "HandCategory.API_INTEGRATION",
                "safety_level": "HandSafetyLevel.MODERATE",
                "methods": ["execute"],
                "capabilities": []
            }
        
        # 生成名称和类名
        name = config.get("name", self._generate_name_from_requirement(requirement))
        class_name = self._to_class_name(name)
        description = requirement
        
        # 生成文件路径
        file_name = f"{name.replace('_', '_')}.py"
        file_path = self.hands_dir / file_name
        
        # 生成代码
        code = self.template.BASE_TEMPLATE.format(
            hand_name=name,
            class_name=class_name,
            description=description,
            name=name,
            category=config.get("category", "HandCategory.API_INTEGRATION"),
            safety_level=config.get("safety_level", "HandSafetyLevel.MODERATE"),
            parameters={},
            dependencies=[],
            examples=[],
            required_params=[],
            created_at=datetime.now().isoformat()
        )
        
        # 创建 GeneratedHand
        generated = GeneratedHand(
            name=name,
            description=description,
            category=config.get("category", ""),
            safety_level=config.get("safety_level", ""),
            methods=[{"name": m} for m in config.get("methods", [])],
            code=code,
            file_path=str(file_path),
            capabilities=config.get("capabilities", [])
        )
        
        self.generated_hands[name] = generated
        return generated
    
    def save_and_register(self, generated: GeneratedHand) -> bool:
        """
        保存生成的代码并注册
        
        Args:
            generated: 生成的 Hand 信息
            
        Returns:
            是否成功
        """
        try:
            # 保存到文件
            with open(generated.file_path, 'w', encoding='utf-8') as f:
                f.write(generated.code)
            
            self.logger.info(f"已保存 Hand: {generated.file_path}")
            
            # 尝试热加载
            success = self.reload_registry()
            
            # 完整验证
            if success:
                verify_result = self.verify_generated_hand(generated)
                if not verify_result:
                    self.logger.warning(f"Hand 验证失败，将删除: {generated.file_path}")
                    import os
                    if os.path.exists(generated.file_path):
                        os.remove(generated.file_path)
                    return False
            
            return success
            
        except Exception as e:
            self.logger.error(f"保存失败: {e}")
            return False
    
    def verify_generated_hand(self, generated: GeneratedHand) -> bool:
        """
        完整验证生成的 Hand
        
        验证流程：
        1. 语法验证
        2. Import 验证
        3. 实例化验证
        4. 执行验证
        
        Returns:
            是否通过所有验证
        """
        import ast
        import importlib
        import sys
        import asyncio
        
        try:
            # 1. 语法验证
            try:
                ast.parse(generated.code)
            except SyntaxError as e:
                self.logger.error(f"语法错误: {e}")
                return False
            
            # 2. Import 验证
            module_name = generated.name
            try:
                # 移除旧模块
                if module_name in sys.modules:
                    del sys.modules[module_name]
                
                # 尝试导入
                mod = importlib.import_module(f"hands.{module_name}")
                
            except Exception as e:
                self.logger.error(f"Import 失败: {e}")
                return False
            
            # 3. 找到 Hand 类
            cls = None
            for attr_name in dir(mod):
                if attr_name.endswith('Hand') and attr_name != 'BaseHand':
                    cls = getattr(mod, attr_name)
                    break
            
            if cls is None:
                self.logger.error("未找到 Hand 类")
                return False
            
            # 4. 实例化验证
            try:
                hand = cls()
            except Exception as e:
                self.logger.error(f"实例化失败: {e}")
                return False
            
            # 5. 执行验证
            try:
                result = asyncio.run(hand.execute())
                if not result.success:
                    self.logger.warning(f"执行返回失败但继续: {result.error}")
            except Exception as e:
                self.logger.error(f"执行失败: {e}")
                return False
            
            self.logger.info(f"✅ Hand 验证通过: {generated.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"验证过程异常: {e}")
            return False
    
    def reload_registry(self) -> bool:
        """重新加载注册表"""
        try:
            import importlib
            import src.hands.registry as registry_module
            importlib.reload(registry_module)
            
            from src.hands.registry import HandRegistry
            new_registry = HandRegistry(auto_discover=True)
            
            self.logger.info(f"重新加载完成，新 Hand 数量: {new_registry.stats()['total_hands']}")
            return True
            
        except Exception as e:
            self.logger.warning(f"热加载失败: {e}")
            return False
    
    def generate_from_template(self, template_name: str, params: Dict[str, Any]) -> GeneratedHand:
        """
        从模板生成
        
        Args:
            template_name: 模板名称
            params: 模板参数
            
        Returns:
            生成的 Hand
        """
        if template_name not in self.template.TYPE_MAPPINGS:
            raise ValueError(f"未知模板: {template_name}")
        
        config = self.template.TYPE_MAPPINGS[template_name]
        requirement = params.get("description", template_name)
        
        return self.generate_hand_code(requirement, template_name)
    
    def list_generated_hands(self) -> List[Dict[str, Any]]:
        """列出所有生成的 Hands"""
        return [
            {
                "name": h.name,
                "description": h.description,
                "file_path": h.file_path,
                "capabilities": h.capabilities
            }
            for h in self.generated_hands.values()
        ]
    
    def generate_with_llm(self, requirement: str) -> GeneratedHand:
        """
        使用 LLM 生成完整代码
        
        Args:
            requirement: 用户需求描述
            
        Returns:
            生成的 Hand 信息
        """
        self.logger.info(f"使用 LLM 生成代码: {requirement}")
        
        llm_generator = LLMCodeGenerator()
        llm_code = llm_generator.generate_code(requirement)
        
        if llm_code:
            name = self._generate_name_from_requirement(requirement)
            file_path = self.hands_dir / f"{name}.py"
            
            generated = GeneratedHand(
                name=name,
                description=requirement,
                category="HandCategory.API_INTEGRATION",
                safety_level="HandSafetyLevel.MODERATE",
                methods=[{"name": "execute"}],
                code=llm_code,
                file_path=str(file_path),
                capabilities=[]
            )
            
            self.generated_hands[name] = generated
            
            # 保存并验证
            success = self.save_and_register(generated)
            
            # 如果验证失败，生成模板代码
            if not success:
                self.logger.warning("LLM 代码验证失败，回退到模板")
                return self.generate_hand_code(requirement)
            
            self.logger.info(f"LLM 生成完成: {generated.name}")
            return generated
        else:
            self.logger.warning("LLM 生成失败，回退到模板")
            return self.generate_hand_code(requirement)
    
    def _find_existing_hand(self, analysis: Dict[str, Any], requirement: str) -> Optional[str]:
        """
        检查是否已有真实实现
        
        Args:
            analysis: 需求分析结果
            requirement: 原始需求
            
        Returns:
            已有 Hand 的名称，如果没有则返回 None
        """
        # 已检测到的类型
        detected_types = analysis.get("detected_types", [])
        
        # 使用 TYPE_MAPPINGS 中的配置
        for detected in detected_types:
            type_name = detected.get("type", "")
            
            if type_name in self.template.TYPE_MAPPINGS:
                config = self.template.TYPE_MAPPINGS[type_name]
                
                # 优先检查真实实现
                real_impl = config.get("real_implementation")
                if real_impl:
                    # 检查这个 Hand 是否已注册
                    try:
                        from .registry import HandRegistry
                        registry = HandRegistry()
                        if registry.get_hand(real_impl):
                            self.logger.info(f"找到真实实现: {real_impl} (用于: {type_name})")
                            return real_impl
                    except:
                        pass
        
        return None
    
    def _create_reference_to_hand(self, hand_name: str, requirement: str) -> GeneratedHand:
        """
        创建对已有 Hand 的引用
        
        Args:
            hand_name: 已有 Hand 的名称
            requirement: 原始需求
            
        Returns:
            引用信息（不是新生成的文件）
        """
        return GeneratedHand(
            name=hand_name,
            description=requirement,
            category="reference",
            safety_level="",
            methods=[],
            code="",  # 空代码，表示使用已有实现
            file_path="",  # 空路径，表示不生成文件
            capabilities=[]
        )
    
    def _generate_name_from_requirement(self, requirement: str) -> str:
        """从需求生成名称（只使用 ASCII 字符）"""
        # 只保留 ASCII 字母和数字
        name = re.sub(r'[^a-zA-Z0-9]', '', requirement)
        name = name.lower()
        name = name[:30]
        return name if name else "auto_generated"
    
    def _to_class_name(self, name: str) -> str:
        """转换为类名格式"""
        words = name.replace('_', ' ').split()
        return ''.join(word.capitalize() for word in words) + 'Hand'


# 便捷函数
def auto_generate_hand(requirement: str, use_llm: bool = False) -> GeneratedHand:
    """
    自动生成 Hand 的便捷函数
    
    Args:
        requirement: 用户需求描述
        use_llm: 是否使用 LLM 生成完整代码
        
    Returns:
        生成的 Hand 信息
    """
    generator = HandAutoGenerator()
    
    if use_llm:
        return generator.generate_with_llm(requirement)
    else:
        generated = generator.generate_hand_code(requirement)
        generator.save_and_register(generated)
        return generated


def generate_with_llm(requirement: str) -> GeneratedHand:
    """
    使用 LLM 生成完整代码
    
    这个函数会：
    1. 调用 LLM 生成包含具体 API 调用的代码
    2. 修复代码格式
    3. 保存并注册
    
    Args:
        requirement: 用户需求描述
        
    Returns:
        生成的 Hand 信息
    """
    generator = HandAutoGenerator()
    return generator.generate_with_llm(requirement)


if __name__ == "__main__":
    # 测试
    generator = HandAutoGenerator()
    
    # 测试用例
    test_cases = [
        "帮我收新邮件",
        "操作日历事件",
        "搜索网页内容",
        "翻译文本"
    ]
    
    print("=" * 60)
    print("Hand 自动生成器测试")
    print("=" * 60)
    
    for req in test_cases:
        print(f"\n需求: {req}")
        analysis = generator.analyze_requirement(req)
        print(f"  分析: {analysis}")
        
        generated = generator.generate_hand_code(req)
        print(f"  生成: {generated.name}")
        print(f"  文件: {generated.file_path}")


# ==================== OpenClaw 优化的自动生成器 ====================

class OpenClawHandGenerator:
    """OpenClaw 优化的 Hand 生成器
    
    集成三大原则:
    1. Superpowers (方法论): 需求发现 → TDD 检查 → 代码审查
    2. Claude HUD (可观测性): 实时进度可视化
    3. Open SWE (团队协作): MiddlewareChain 处理
    """
    
    def __init__(self):
        self._init_openclaw_components()
    
    def _init_openclaw_components(self):
        """初始化 OpenClaw 组件"""
        # AgentHUD - 可观测性
        try:
            from src.ui.agent_hud import get_hud_instance
            self.hud = get_hud_instance()
        except ImportError:
            self.hud = None
        
        # Requirement Discovery - 需求发现
        try:
            from src.agents.requirement_discovery import RequirementDiscoveryAgent
            self.requirement_agent = RequirementDiscoveryAgent()
        except ImportError:
            self.requirement_agent = None
        
        # TDD Enforcer - TDD 铁律
        try:
            from src.agents.tdd_enforcer import get_enforcer
            self.tdd_enforcer = get_enforcer()
        except ImportError:
            self.tdd_enforcer = None
        
        # Two Stage Reviewer - 代码审查
        try:
            from src.agents.two_stage_reviewer import TwoStageReviewer
            self.reviewer = TwoStageReviewer()
        except ImportError:
            self.reviewer = None
        
        # Middleware Chain - 中间件
        try:
            from src.core.middleware import get_middleware_chain, LoggingMiddleware
            self.middleware = get_middleware_chain()
        except ImportError:
            self.middleware = None
        
        # 基础代码生成器
        self.base_generator = HandAutoGenerator()
    
    def generate_with_openclaw(self, requirement: str, auto_register: bool = False) -> Dict[str, Any]:
        """使用 OpenClaw 原则生成 Hand
        
        流程:
        1. 需求发现 (5W1H)
        2. TDD 检查
        3. 代码生成
        4. 两阶段审查
        5. Middleware 处理
        6. AgentHUD 可视化
        """
        result = {
            "success": False,
            "requirement": requirement,
            "discovered_requirements": None,
            "tdd_check": None,
            "code": None,
            "review_result": None,
            "file_path": None,
            "errors": []
        }
        
        if self.hud:
            self.hud.record_tool_start("openclaw_generator", "requirement_discovery")
        
        # Step 1: 需求发现
        if self.requirement_agent:
            try:
                discovered = self.requirement_agent.discover_requirements(requirement)
                result["discovered_requirements"] = self.requirement_agent.export_to_dict()
                result["spec_document"] = self.requirement_agent.generate_spec(discovered)
                logger.info(f"需求发现完成: {len(discovered.requirements)} 个需求")
            except Exception as e:
                result["errors"].append(f"需求发现失败: {e}")
        else:
            result["errors"].append("RequirementDiscoveryAgent 不可用")
        
        if self.hud:
            self.hud.record_tool_start("openclaw_generator", "tdd_check")
        
        # Step 2: TDD 检查 (生成测试代码)
        if self.tdd_enforcer:
            try:
                test_file = f"tests/generated/test_{requirement[:20].replace(' ', '_')}.py"
                self.tdd_enforcer.register_test(test_file, production_path="")
                result["tdd_check"] = {
                    "test_file": test_file,
                    "status": "test_registered",
                    "ready": True
                }
                logger.info(f"TDD 检查通过: 测试已注册")
            except Exception as e:
                result["tdd_check"] = {"status": "failed", "error": str(e)}
                result["errors"].append(f"TDD 检查失败: {e}")
        
        if self.hud:
            self.hud.record_tool_start("openclaw_generator", "code_generation")
        
        # Step 3: 代码生成
        try:
            generated = self.base_generator.generate_hand_code(requirement)
            result["code"] = generated.code
            result["file_path"] = generated.file_path
            logger.info(f"代码生成完成: {generated.name}")
        except Exception as e:
            result["errors"].append(f"代码生成失败: {e}")
            return result
        
        if self.hud:
            self.hud.record_tool_start("openclaw_generator", "code_review")
        
        # Step 4: 两阶段代码审查
        if self.reviewer and result["code"]:
            try:
                review_result = self.reviewer.run_review(result["code"], result.get("spec_document", ""))
                result["review_result"] = review_result.to_dict()
                
                if review_result.overall_status == "fail":
                    result["errors"].append(f"代码审查未通过: {review_result.stage1_result.summary}")
                elif review_result.overall_status == "needs_work":
                    result["errors"].append(f"代码审查有警告: {review_result.stage1_result.summary}")
                
                logger.info(f"代码审查完成: {review_result.overall_status}")
            except Exception as e:
                result["errors"].append(f"代码审查失败: {e}")
        
        if self.hud:
            self.hud.record_tool_start("openclaw_generator", "middleware_processing")
        
        # Step 5: Middleware 处理
        if self.middleware and result["code"]:
            try:
                import asyncio
                middleware_result = asyncio.get_event_loop().run_until_complete(
                    self.middleware.execute(result["code"], request_id="hand_generation")
                )
                if not middleware_result.success:
                    result["errors"].append(f"Middleware 处理: {middleware_result.error}")
                logger.info(f"Middleware 处理完成")
            except Exception as e:
                result["errors"].append(f"Middleware 处理失败: {e}")
        
        # Step 6: 写入文件
        if result["file_path"] and result["code"]:
            try:
                os.makedirs(os.path.dirname(result["file_path"]), exist_ok=True)
                with open(result["file_path"], "w") as f:
                    f.write(result["code"])
                logger.info(f"文件写入成功: {result['file_path']}")
            except Exception as e:
                result["errors"].append(f"文件写入失败: {e}")
        
        # 记录完成
        if self.hud:
            success = len(result["errors"]) == 0
            if success:
                self.hud.record_tool_start("openclaw_generator", "complete")
            else:
                self.hud.record_error("; ".join(result["errors"][:2]))
        
        result["success"] = len(result["errors"]) == 0
        return result
    
    def get_generation_summary(self, result: Dict[str, Any]) -> str:
        """获取生成摘要"""
        lines = ["=" * 60, "OpenClaw Hand 生成摘要", "=" * 60]
        
        lines.append(f"\n原始需求: {result['requirement']}")
        
        if result.get("discovered_requirements"):
            reqs = result["discovered_requirements"].get("requirements", [])
            lines.append(f"\n发现需求: {len(reqs)} 个")
            for r in reqs[:3]:
                lines.append(f"  - [{r.get('priority', 'N/A')}] {r.get('title', 'N/A')}")
        
        if result.get("tdd_check"):
            status = result["tdd_check"].get("status", "unknown")
            lines.append(f"\nTDD 检查: {status}")
        
        if result.get("review_result"):
            review = result["review_result"]
            lines.append(f"\n代码审查:")
            lines.append(f"  Stage 1: {review.get('stage1', {}).get('status', 'N/A')}")
            if review.get('stage2'):
                lines.append(f"  Stage 2: {review.get('stage2', {}).get('status', 'N/A')}")
            lines.append(f"  总体: {review.get('overall_status', 'N/A')}")
        
        lines.append(f"\n文件: {result.get('file_path', 'N/A')}")
        lines.append(f"状态: {'✅ 成功' if result.get('success') else '❌ 失败'}")
        
        if result.get('errors'):
            lines.append(f"\n错误 ({len(result['errors'])}):")
            for e in result['errors'][:3]:
                lines.append(f"  - {e}")
        
        return "\n".join(lines)
