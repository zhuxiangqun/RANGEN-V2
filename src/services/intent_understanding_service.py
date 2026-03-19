"""
智能意图理解服务
=================

使用 LLM 进行语义级别的意图识别，比关键词匹配更智能。

核心能力：
1. 语义理解 - 理解用户真正想要什么
2. 上下文感知 - 结合对话历史理解
3. 实体提取 - 识别关键实体（Agent名、Skill名等）
4. 动态学习 - 从反馈中学习新模式（复用 SkillTriggerLearner）
5. 指代消解 - 理解"那个"、"它"等指代
"""

import os
import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import threading

from src.services.logging_service import get_logger

logger = get_logger(__name__)


class IntentType(Enum):
    """意图类型（扩展版）"""
    QUERY = "query"                    # 通用查询
    ACTION = "action"                 # 执行操作
    CREATION = "creation"             # 创建实体
    DIAGNOSIS = "diagnosis"           # 运维诊断/健康检查
    CONFIRMATION = "confirmation"     # 确认
    FOLLOWUP = "followup"            # 后续操作
    HELP = "help"                    # 帮助
    CLARIFICATION = "clarification"  # 澄清需求
    GREETING = "greeting"            # 问候


@dataclass
class IntentResult:
    """意图理解结果"""
    intent: IntentType
    confidence: float
    entities: Dict[str, Any]
    reasoning: str = ""  # LLM 的推理过程
    response_type: str = "text"  # text, action, confirmation, suggestion
    suggested_actions: List[str] = None
    
    def __post_init__(self):
        if self.suggested_actions is None:
            self.suggested_actions = []


# 意图理解的 system prompt
INTENT_SYSTEM_PROMPT = """你是一个专业的运维助手意图理解引擎。你的任务是根据用户输入，准确判断用户的真实意图。

## 可识别的意图类型：

1. **diagnosis** - 运维诊断/健康检查
   - 用户想检查系统状态、诊断问题
   - 关键词：检查、诊断、修复、查看状态、health、check、404、错误、问题、故障、离线、健康

2. **creation** - 创建实体
   - 用户想创建一个新的 Agent、Skill、Tool 等
   - 关键词：创建、新建、添加、做一个、帮我建

3. **action** - 执行操作
   - 用户想执行某个具体操作
   - 关键词：清理、重启、启动、停止、删除、stop、start

4. **query** - 通用查询
   - 用户在询问系统相关信息
   - 关键词：是什么、怎么用、如何、为什么

5. **confirmation** - 确认
   - 用户在确认或同意某个操作
   - 关键词：是、好、可以、确认、对、yes、ok

6. **clarification** - 澄清需求
   - 用户的需求不够明确，需要进一步澄清
   - 场景：信息不足、歧义、需要更多细节

7. **followup** - 后续操作
   - 用户想继续之前的操作或查看结果

8. **help** - 帮助
   - 用户请求帮助或指导

9. **greeting** - 问候
   - 用户在打招呼
   - 关键词：你好、hi、hello、嗨、您好

## 输出格式（必须严格遵循）：

```json
{
  "intent": "意图类型",
  "confidence": 0.0-1.0,
  "reasoning": "你的推理过程",
  "entities": {
    "target": "实体类型（agent/skill/tool/workflow等）",
    "name": "实体名称（如有）",
    "operation": "操作类型（如有）"
  },
  "response_type": "text/action/confirmation/suggestion",
  "suggested_actions": ["建议的操作1", "建议的操作2"]
}
```

## 重要原则：

1. **置信度**：只有当你非常确定时才给 0.9+ 的置信度
2. **实体提取**：尽量识别用户提到的具体实体
3. **上下文理解**：如果用户说"那个"、"它"，要结合上下文理解
4. **模糊处理**：如果无法确定意图，返回 clarification
"""


class IntentUnderstandingService:
    """
    智能意图理解服务
    
    使用 LLM 进行语义级别的意图识别，比关键词匹配更智能。
    """
    
    def __init__(self):
        self._llm = None
        self._cache: Dict[str, IntentResult] = {}
        self._cache_max_size = 100
        self._lock = threading.RLock()
        
        # 动态学习器 - 复用 SkillTriggerLearner
        self._learner = None
        
        # 用户学习的模式 - 从反馈中学习
        self._learned_patterns: Dict[str, List[Dict]] = defaultdict(list)
        
        # 指代词列表
        self._coreference_pronouns = [
            "那个", "这个", "它", "他", "她",
            "那", "这", "这些", "那些", "这个"
        ]
        
        # 回退到关键词匹配的意图模式
        self._keyword_patterns = {
            IntentType.DIAGNOSIS: [
                "诊断", "检查", "修复", "health", "check", "404", 
                "错误", "问题", "故障", "离线", "评估", "performance",
                "分数", "原因", "分析", "状态", "服务"
            ],
            IntentType.CREATION: [
                "创建", "新建", "添加", "做一个", "帮我建", 
                "添加一个", "新增"
            ],
            IntentType.ACTION: [
                "清理", "清除", "重启", "stop", "start", "删除",
                "停止", "启动", "关闭", "打开"
            ],
            IntentType.CONFIRMATION: [
                "是", "好", "可以", "确认", "对", "yes", "ok", "y", "执行", "do it"
            ],
            IntentType.HELP: [
                "帮助", "help", "怎么用", "如何使用"
            ],
            IntentType.GREETING: [
                "你好", "hi", "hello", "嗨", "您好", "hi there"
            ],
            IntentType.FOLLOWUP: [
                "继续", "然后呢", "接下来", "继续执行", "go on"
            ]
        }
    
    def _get_learner(self):
        """获取学习器 - 懒加载 SkillTriggerLearner"""
        if self._learner is None:
            try:
                from src.core.self_learning.skill_trigger_learner import SkillTriggerLearner
                self._learner = SkillTriggerLearner()
                
                # 注册所有意图类型作为"技能"
                for intent in IntentType:
                    self._learner.register_skill(
                        skill_name=intent.value,
                        trigger_keywords=[]
                    )
                logger.info("IntentUnderstandingService: SkillTriggerLearner initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize SkillTriggerLearner: {e}")
                self._learner = None
        return self._learner
    
    def _load_env(self):
        """加载环境变量"""
        try:
            from dotenv import load_dotenv
            load_dotenv(override=False)
        except ImportError:
            pass
    
    def _get_llm(self):
        """懒加载 LLM"""
        if self._llm is None:
            try:
                self._load_env()  # 确保环境变量已加载
                
                from src.core.llm_integration import LLMIntegration
                
                api_key = os.getenv("DEEPSEEK_API_KEY", "")
                logger.info(f"IntentUnderstandingService: API Key found: {api_key[:10] if api_key else 'None'}...")
                
                config = {
                    "llm_provider": os.getenv("LLM_PROVIDER", "deepseek"),
                    "api_key": api_key,
                    "model": "deepseek-chat",
                    "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
                }
                self._llm = LLMIntegration(config)
                logger.info("IntentUnderstandingService: LLM initialized")
            except Exception as e:
                logger.warning(f"IntentUnderstandingService: Failed to initialize LLM: {e}")
                self._llm = None
        return self._llm
    
    def _parse_llm_response(self, response: str) -> Optional[IntentResult]:
        """解析 LLM 返回的结果"""
        try:
            # 提取 JSON 部分
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            
            data = json.loads(json_str.strip())
            
            # 映射意图字符串到 IntentType
            intent_str = data.get("intent", "query").lower()
            intent_map = {
                "query": IntentType.QUERY,
                "action": IntentType.ACTION,
                "creation": IntentType.CREATION,
                "diagnosis": IntentType.DIAGNOSIS,
                "confirmation": IntentType.CONFIRMATION,
                "followup": IntentType.FOLLOWUP,
                "help": IntentType.HELP,
                "clarification": IntentType.CLARIFICATION,
                "greeting": IntentType.GREETING
            }
            
            intent = intent_map.get(intent_str, IntentType.QUERY)
            
            return IntentResult(
                intent=intent,
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", ""),
                entities=data.get("entities", {}),
                response_type=data.get("response_type", "text"),
                suggested_actions=data.get("suggested_actions", [])
            )
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            return None
        except Exception as e:
            logger.warning(f"Failed to parse intent result: {e}")
            return None
    
    def _keyword_fallback(self, query: str, context: Dict[str, Any] = None) -> IntentResult:
        """关键词回退策略"""
        query_lower = query.lower()
        
        # 检查确认意图（如果有 pending_action）
        if context and context.get("pending_action"):
            for kw in self._keyword_patterns[IntentType.CONFIRMATION]:
                # 跳过可能导致误判的词
                if kw == "是" and ("是否" in query_lower or "是不是" in query_lower):
                    continue
                if kw in query_lower:
                    return IntentResult(
                        intent=IntentType.CONFIRMATION,
                        confidence=0.95,
                        entities={},
                        reasoning="用户确认了 pending_action"
                    )
        
        # 匹配关键词模式
        for intent_type, keywords in self._keyword_patterns.items():
            for kw in keywords:
                # 跳过可能导致误判的词
                if kw == "是" and ("是否" in query_lower or "是不是" in query_lower):
                    continue
                if kw in query_lower:
                    return IntentResult(
                        intent=intent_type,
                        confidence=0.7,
                        entities={},
                        reasoning=f"关键词匹配: {kw}"
                    )
        
        # 默认返回通用查询
        return IntentResult(
            intent=IntentType.QUERY,
            confidence=0.5,
            entities={"query": query},
            reasoning="无法匹配任何关键词，返回默认查询"
        )
    
    async def understand(
        self, 
        query: str, 
        context: Dict[str, Any] = None
    ) -> IntentResult:
        """
        理解用户意图
        
        Args:
            query: 用户输入
            context: 对话上下文（可选）
            
        Returns:
            IntentResult: 结构化的意图理解结果
        """
        # 缓存检查
        cache_key = f"{query}:{context.get('session_id', '') if context else ''}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 清理缓存
        if len(self._cache) > self._cache_max_size:
            self._cache = {}
        
        # 调用 LLM
        llm = self._get_llm()
        
        if llm is None:
            logger.warning("LLM unavailable, using keyword fallback")
            result = self._keyword_fallback(query, context)
            self._cache[cache_key] = result
            return result
        
        try:
            # 构建 prompt
            history_context = ""
            if context and context.get("history"):
                recent = context["history"][-3:]  # 最近3轮对话
                for msg in recent:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")[:200]
                    history_context += f"\n{role}: {content}"
            
            user_prompt = f"""用户输入: {query}

对话上下文（最近3轮）:
{history_context if history_context else "(无)"}

请分析用户意图："""
            
            # 调用 LLM
            response = llm._call_llm(
                prompt=user_prompt,
                system_prompt=INTENT_SYSTEM_PROMPT,
                temperature=0.1  # 低温度保证稳定性
            )
            
            if response:
                result = self._parse_llm_response(response)
                if result:
                    self._cache[cache_key] = result
                    return result
            
            # LLM 返回无效，回退到关键词
            logger.warning("LLM returned invalid response, using keyword fallback")
            result = self._keyword_fallback(query, context)
            self._cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"Intent understanding failed: {e}")
            result = self._keyword_fallback(query, context)
            self._cache[cache_key] = result
            return result
    
    def _has_coreference(self, query: str) -> bool:
        """检查查询是否包含指代词"""
        query_lower = query.lower()
        return any(pronoun in query_lower for pronoun in self._coreference_pronouns)
    
    async def resolve_coreference(
        self, 
        query: str, 
        history: List[Dict[str, str]]
    ) -> str:
        """
        使用 LLM 解析指代词，将"那个"、"它"等替换为具体内容
        
        Args:
            query: 用户输入（可能包含指代词）
            history: 对话历史
            
        Returns:
            替换后的查询
        """
        if not self._has_coreference(query):
            return query
        
        llm = self._get_llm()
        if llm is None:
            return query
        
        try:
            # 构建历史上下文
            history_text = ""
            for i, msg in enumerate(history[-5:]):
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_text += f"{i+1}. {role}: {content[:300]}\n"
            
            resolve_prompt = f"""用户输入包含指代词，请将其解析为具体内容。

指代词示例：那个、它、这个、这些、那、这

历史对话：
{history_text if history_text else "(无)"}

用户当前输入：{query}

请输出解析后的完整查询（只输出解析后的句子，不要其他内容）："""
            
            response = llm._call_llm(
                prompt=resolve_prompt,
                system_prompt="你是一个指代消解专家，负责将包含指代词的句子转换为完整清晰的句子。",
                temperature=0.1
            )
            
            if response:
                resolved = response.strip()
                logger.debug(f"Coreference resolved: '{query}' -> '{resolved}'")
                return resolved
            
        except Exception as e:
            logger.warning(f"Coreference resolution failed: {e}")
        
        return query
    
    def get_expanded_context(
        self, 
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """
        获取扩展后的上下文，用于传给 LLM 进行意图识别
        
        Args:
            query: 用户查询
            context: 当前上下文
            
        Returns:
            格式化的上下文字符串
        """
        parts = []
        
        # 添加完整历史（不只是最近3轮）
        history = context.get("history", [])
        if history:
            parts.append("对话历史：")
            for i, msg in enumerate(history[-10:]):  # 最近10轮
                role = msg.get("role", "user")
                content = msg.get("content", "")[:300]
                parts.append(f"  [{i+1}] {role}: {content}")
        
        # 添加待确认操作
        pending = context.get("pending_action")
        if pending:
            parts.append(f"\n待确认操作: {pending}")
        
        # 添加会话信息
        session_id = context.get("session_id")
        if session_id:
            parts.append(f"\n会话ID: {session_id}")
        
        return "\n".join(parts) if parts else "(无上下文)"
    
    def learn_from_feedback(
        self,
        query: str,
        correct_intent: str,
        session_id: str = None
    ):
        """
        从用户反馈中学习正确的意图模式
        
        Args:
            query: 用户查询
            correct_intent: 用户纠正后的正确意图
            session_id: 会话ID
        """
        with self._lock:
            # 记录学习模式
            pattern_key = correct_intent.lower()
            pattern = {
                "query": query,
                "intent": correct_intent,
                "keywords": self._extract_keywords(query),
                "timestamp": __import__("time").time()
            }
            self._learned_patterns[pattern_key].append(pattern)
            
            # 限制每个意图的学习样本数
            max_samples = 100
            if len(self._learned_patterns[pattern_key]) > max_samples:
                self._learned_patterns[pattern_key] = self._learned_patterns[pattern_key][-max_samples:]
            
            # 使用 SkillTriggerLearner 记录
            learner = self._get_learner()
            if learner:
                try:
                    from src.core.self_learning.skill_trigger_learner import TriggerCondition
                    condition = TriggerCondition(
                        keywords=self._extract_keywords(query),
                        query_patterns=[query]
                    )
                    learner.record_trigger(
                        skill_name=correct_intent,
                        trigger_condition=condition,
                        query=query,
                        context={"session_id": session_id},
                        success=True,
                        quality_score=1.0
                    )
                    logger.info(f"Learned new pattern: '{query}' -> {correct_intent}")
                except Exception as e:
                    logger.warning(f"Failed to record to SkillTriggerLearner: {e}")
    
    def _extract_keywords(self, query: str) -> List[str]:
        """从查询中提取关键词"""
        import re
        # 简单分词
        words = re.findall(r'[\w]+', query.lower())
        # 过滤停用词
        stopwords = {"的", "了", "在", "是", "我", "你", "他", "她", "它", "这", "那", "什么", "怎么", "如何", "吗", "呢"}
        return [w for w in words if len(w) > 1 and w not in stopwords]
    
    def predict_from_learning(
        self, 
        query: str
    ) -> Tuple[Optional[IntentType], float]:
        """
        基于学习的历史预测意图
        
        Args:
            query: 用户查询
            
        Returns:
            (预测的意图, 置信度)
        """
        query_lower = query.lower()
        keywords = set(self._extract_keywords(query))
        
        best_intent = None
        best_score = 0.0
        
        for intent_str, patterns in self._learned_patterns.items():
            score = 0.0
            for pattern in patterns[-10:]:  # 只看最近的模式
                pattern_keywords = set(pattern.get("keywords", []))
                if keywords & pattern_keywords:  # 有交集
                    overlap = len(keywords & pattern_keywords) / len(keywords | pattern_keywords)
                    score = max(score, overlap)
            
            if score > best_score and score > 0.3:
                best_score = score
                best_intent = IntentType(intent_str) if intent_str in [i.value for i in IntentType] else None
        
        return best_intent, best_score
    
    def record_outcome(
        self,
        query: str,
        predicted_intent: IntentType,
        actual_intent: IntentType,
        session_id: str = None
    ):
        """
        记录意图预测的结果，用于后续学习
        
        Args:
            query: 用户查询
            predicted_intent: 预测的意图
            actual_intent: 实际的意图（如果用户纠正则为纠正后的，否则同预测）
        """
        success = predicted_intent == actual_intent
        learner = self._get_learner()
        
        if learner:
            try:
                from src.core.self_learning.skill_trigger_learner import TriggerCondition
                condition = TriggerCondition(
                    keywords=self._extract_keywords(query),
                    query_patterns=[query]
                )
                learner.record_trigger(
                    skill_name=actual_intent.value,
                    trigger_condition=condition,
                    query=query,
                    context={"session_id": session_id},
                    success=success,
                    quality_score=1.0 if success else 0.0
                )
            except Exception as e:
                logger.warning(f"Failed to record outcome: {e}")
    
    def clear_cache(self):
        """清理缓存"""
        self._cache = {}
        logger.info("Intent cache cleared")


# 单例
_intent_service: Optional[IntentUnderstandingService] = None

def get_intent_understanding_service() -> IntentUnderstandingService:
    """获取意图理解服务单例"""
    global _intent_service
    if _intent_service is None:
        _intent_service = IntentUnderstandingService()
    return _intent_service
