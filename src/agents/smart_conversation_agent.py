"""
Smart Conversation Agent - 智能对话Agent
"""
import os
import time
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import json

from src.interfaces.agent import IAgent, AgentConfig, AgentResult, ExecutionStatus
from src.services.logging_service import get_logger
from src.services.intent_understanding_service import (
    IntentType as SmartIntentType,
    IntentResult as SmartIntentResult,
    get_intent_understanding_service
)

logger = get_logger(__name__)

# API 配置
RANGEN_API_BASE = os.getenv("RANGEN_API_BASE", "http://localhost:8000")


# 保持向后兼容的意图类型映射
class IntentType(Enum):
    """意图类型（兼容旧代码）"""
    QUERY = "query"                    # 通用查询
    ACTION = "action"                 # 执行操作
    CREATION = "creation"             # 创建实体
    DIAGNOSIS = "diagnosis"           # 运维诊断
    CONFIRMATION = "confirmation"     # 确认
    FOLLOWUP = "followup"            # 后续操作
    HELP = "help"                    # 帮助


# 意图类型映射
_INTENT_MAP = {
    SmartIntentType.DIAGNOSIS: IntentType.DIAGNOSIS,
    SmartIntentType.CREATION: IntentType.CREATION,
    SmartIntentType.ACTION: IntentType.ACTION,
    SmartIntentType.CONFIRMATION: IntentType.CONFIRMATION,
    SmartIntentType.HELP: IntentType.HELP,
    SmartIntentType.FOLLOWUP: IntentType.FOLLOWUP,
    SmartIntentType.CLARIFICATION: IntentType.QUERY,
    SmartIntentType.GREETING: IntentType.QUERY,
    SmartIntentType.QUERY: IntentType.QUERY,
}


@dataclass
class ConversationContext:
    """对话上下文"""
    session_id: str
    user_id: Optional[str] = None
    history: List[Dict[str, str]] = field(default_factory=list)
    current_intent: Optional[IntentType] = None
    pending_action: Optional[Dict] = None
    created_entities: List[Dict] = field(default_factory=list)
    last_result: Optional[Dict] = None
    suggested_actions: List[str] = field(default_factory=list)


@dataclass
class IntentResult:
    """意图理解结果"""
    intent: IntentType
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)
    response_type: str = "text"  # text, action, confirmation, suggestion
    response_content: str = ""


class SmartConversationAgent(IAgent):
    """
    智能对话Agent
    
    工作流程：
    1. 理解意图 - 分析用户输入，理解真正意图
    2. 匹配能力 - 检查现有Agent/Skill/Tool
    3. 执行 - 调用相应能力执行
    4. 反馈 - 返回结果并提供建议
    5. 记忆 - 保存对话上下文
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                name="smart_conversation_agent",
                description="智能对话Agent，支持自然语言交互、任务执行和能力创建",
                version="1.0.0"
            )
        super().__init__(config)
        
        self._conversation_sessions: Dict[str, ConversationContext] = {}
        self._session_timeout = 3600
        
        self._executors = {
            "production_workflow": self._execute_production_workflow,
            "ops_diagnosis": self._execute_ops_diagnosis,
            "unified_tool_executor": self._execute_tool,
            "unified_creator": self._execute_creation,
        }
        
        logger.info("SmartConversationAgent initialized")
    
    async def execute(self, inputs: Dict[str, Any], context: Optional[Dict] = None) -> AgentResult:
        start_time = time.time()
        
        try:
            query = inputs.get("query", "")
            session_id = inputs.get("session_id") or str(uuid.uuid4())
            
            ctx = self._get_or_create_session(session_id)
            
            user_context = context or {}
            
            result = await self.converse(query, ctx, user_context)
            
            self._update_history(ctx, "user", query)
            self._update_history(ctx, "assistant", result.get("response", ""))
            
            return AgentResult(
                agent_name=self.config.name,
                status=ExecutionStatus.COMPLETED,
                output=result,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"SmartConversationAgent execution failed: {e}")
            return AgentResult(
                agent_name=self.config.name,
                status=ExecutionStatus.FAILED,
                output=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    def _get_or_create_session(self, session_id: str) -> ConversationContext:
        if session_id not in self._conversation_sessions:
            self._conversation_sessions[session_id] = ConversationContext(
                session_id=session_id
            )
        return self._conversation_sessions[session_id]
    
    def _update_history(self, ctx: ConversationContext, role: str, content: str):
        ctx.history.append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })
    
    async def converse(
        self,
        query: str,
        ctx: ConversationContext,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        主对话逻辑
        """
        query_lower = query.lower().strip()
        
        if query_lower in ["help", "帮助", "h", "?"]:
            return await self._handle_help(ctx)
        
        if query_lower in ["clear", "清除", "重置"]:
            ctx.history = []
            return {"response": "对话历史已清除。有什么可以帮您的？", "type": "text"}
        
        intent = await self._understand_intent(query, ctx)
        
        if intent.response_type == "confirmation":
            return await self._handle_confirmation(query, ctx, intent)
        
        if intent.intent == IntentType.CONFIRMATION:
            return await self._handle_pending_action(ctx, query_lower)
        
        if intent.intent == IntentType.CREATION:
            return await self._handle_creation(query, ctx, intent)
        
        if intent.intent == IntentType.DIAGNOSIS:
            return await self._execute_ops_diagnosis(query, ctx)
        
        if intent.intent == IntentType.ACTION:
            return await self._handle_action(query, ctx, intent)
        
        return await self._handle_general_query(query, ctx, intent)
    
    async def _understand_intent(self, query: str, ctx: ConversationContext) -> IntentResult:
        """理解用户意图 - 使用智能 LLM 理解"""
        # 1. 指代消解 - 将"那个"、"它"等替换为具体内容
        if ctx.history:
            try:
                intent_service = get_intent_understanding_service()
                resolved_query = await intent_service.resolve_coreference(query, ctx.history)
                if resolved_query != query:
                    logger.info(f"Coreference resolved: '{query}' -> '{resolved_query}'")
                    query = resolved_query
            except Exception as e:
                logger.debug(f"Coreference resolution skipped: {e}")
        
        try:
            intent_service = get_intent_understanding_service()
            context_dict = {
                "session_id": ctx.session_id,
                "history": ctx.history,
                "pending_action": ctx.pending_action
            }
            smart_result = await intent_service.understand(query, context_dict)
            
            # 映射到兼容的 IntentResult
            mapped_intent = _INTENT_MAP.get(
                smart_result.intent if hasattr(smart_result.intent, 'value') else smart_result.intent,
                IntentType.QUERY
            )
            
            return IntentResult(
                intent=mapped_intent,
                confidence=smart_result.confidence,
                entities=smart_result.entities,
                response_type=smart_result.response_type
            )
        except Exception as e:
            logger.warning(f"Smart intent understanding failed, using keyword fallback: {e}")
        
        # 回退到关键词匹配
        query_lower = query.lower()
        
        if ctx.pending_action:
            confirmation_keywords = ["是", "好", "可以", "确认", "对", "yes", "ok", "y", "执行", "do it"]
            if any(k in query_lower for k in confirmation_keywords):
                return IntentResult(
                    intent=IntentType.CONFIRMATION,
                    confidence=0.95,
                    response_type="action"
                )
        
        if any(k in query_lower for k in ["创建", "新建", "添加", "做一个", "帮我建"]):
            return IntentResult(
                intent=IntentType.CREATION,
                confidence=0.9,
                entities={"type": self._infer_entity_type(query_lower)}
            )
        
        if any(k in query_lower for k in ["诊断", "检查", "修复", "health", "check", "404", "错误", "问题", "故障", "离线"]):
            return IntentResult(
                intent=IntentType.DIAGNOSIS,
                confidence=0.85,
                entities={"query": query}
            )
        
        if any(k in query_lower for k in ["清理", "清除", "重启", "stop", "start"]):
            return IntentResult(
                intent=IntentType.ACTION,
                confidence=0.8,
                entities={"action": query}
            )
        
        if any(k in query_lower for k in ["评估", "evaluation", "performance", "分数", "50分", "原因", "分析"]):
            return IntentResult(
                intent=IntentType.DIAGNOSIS,
                confidence=0.9,
                entities={"query": query, "type": "evaluation"}
            )
        
        return IntentResult(
            intent=IntentType.QUERY,
            confidence=0.7,
            entities={"query": query}
        )
    
    def _infer_entity_type(self, query: str) -> str:
        if "agent" in query or "智能体" in query:
            return "agent"
        if "skill" in query or "技能" in query:
            return "skill"
        if "tool" in query or "工具" in query:
            return "tool"
        if "workflow" in query or "流程" in query:
            return "workflow"
        if "team" in query or "团队" in query:
            return "team"
        return "agent"
    
    async def _handle_confirmation(
        self,
        query: str,
        ctx: ConversationContext,
        intent: IntentResult
    ) -> Dict[str, Any]:
        """处理确认"""
        if ctx.pending_action:
            action = ctx.pending_action
            ctx.pending_action = None
            
            action_type = action.get("type")
            
            if action_type == "create":
                return await self._execute_creation(
                    action.get("entity_type"),
                    action.get("description"),
                    ctx
                )
            
            if action_type == "ops_fix":
                return await self._execute_ops_diagnosis(
                    action.get("query"),
                    ctx
                )
            
            return {"response": "已确认，正在执行...", "type": "text"}
        
        return {"response": "好的，继续。", "type": "text"}
    
    async def _handle_pending_action(
        self,
        ctx: ConversationContext,
        query_lower: str
    ) -> Dict[str, Any]:
        """处理待确认的操作"""
        if not ctx.pending_action:
            return {"response": "没有待确认的操作。", "type": "text"}
        
        confirmation_keywords = ["是", "好", "可以", "确认", "对", "yes", "ok", "y", "执行"]
        if any(k in query_lower for k in confirmation_keywords):
            action = ctx.pending_action
            ctx.pending_action = None
            
            action_type = action.get("type")
            
            if action_type == "create":
                return await self._execute_creation(
                    action.get("entity_type", "agent"),
                    action.get("description", ""),
                    ctx
                )
            
            if action_type == "ops_fix":
                return await self._execute_ops_diagnosis(
                    action.get("query", ""),
                    ctx
                )
            
            return {"response": "已确认，正在执行...", "type": "text"}
        
        if "取消" in query_lower or "不要" in query_lower or "算了" in query_lower:
            ctx.pending_action = None
            return {"response": "已取消。还有其他需要帮忙的吗？", "type": "text"}
        
        return {"response": "请确认是否执行该操作（是/取消）", "type": "confirmation"}
    
    async def _handle_creation(
        self,
        query: str,
        ctx: ConversationContext,
        intent: IntentResult
    ) -> Dict[str, Any]:
        """处理创建请求"""
        entity_type = intent.entities.get("type", "agent")
        
        ctx.pending_action = {
            "type": "create",
            "entity_type": entity_type,
            "description": query
        }
        
        return {
            "response": f"好的，我将为您的需求创建一个 {entity_type}。是否确认创建？",
            "type": "confirmation",
            "suggested_actions": [
                f"是，创建{entity_type}",
                "取消"
            ]
        }
    
    async def _execute_creation(
        self,
        entity_type: str,
        description: str,
        ctx: ConversationContext
    ) -> Dict[str, Any]:
        """执行创建"""
        try:
            from src.services.unified_creator import get_unified_creator
            
            creator = get_unified_creator()
            result = await creator.create_from_natural_language(
                description=description,
                entity_type=entity_type
            )
            
            if result.success:
                entity_name = result.entity_name or "新实体"
                ctx.created_entities.append({
                    "type": entity_type,
                    "name": entity_name
                })
                
                return {
                    "response": f"✅ 创建成功！已创建 {entity_type}: {entity_name}\n\n现在您可以使用它了。有什么其他需要吗？",
                    "type": "text",
                    "entity": {
                        "type": entity_type,
                        "name": entity_name
                    }
                }
            else:
                return {
                    "response": f"❌ 创建失败: {result.error}\n\n请尝试更详细地描述您的需求。",
                    "type": "text"
                }
                
        except Exception as e:
            logger.error(f"Creation failed: {e}")
            return {
                "response": f"❌ 创建过程中出错: {str(e)}",
                "type": "text"
            }
    
    async def _execute_ops_diagnosis(
        self,
        query: str,
        ctx: ConversationContext
    ) -> Dict[str, Any]:
        """执行运维诊断或评估分析"""
        query_lower = query.lower()
        
        if any(k in query_lower for k in ["评估", "evaluation", "performance", "分数", "50分", "原因"]):
            return await self._handle_evaluation_query(query)
        
        try:
            from src.agents.ops_diagnosis_agent import get_ops_diagnosis_agent
            
            ops = get_ops_diagnosis_agent()
            result = await ops.execute(
                inputs={"query": query},
                context={"auto_fix": True}
            )
            
            if result.status == ExecutionStatus.COMPLETED:
                output = result.output or {}
                findings = output.get("findings", [])
                steps = output.get("steps", [])
                
                response_parts = []
                for finding in findings:
                    status = finding.get("status", "")
                    component = finding.get("component", "")
                    message = finding.get("message", "")
                    diagnosis = finding.get("diagnosis", "")
                    
                    if status == "healthy":
                        response_parts.append(f"✅ {component}: {message}")
                    elif status == "error" or status == "offline":
                        response_parts.append(f"❌ {component}: {message}")
                        if diagnosis:
                            response_parts.append(f"   原因: {diagnosis}")
                    else:
                        response_parts.append(f"⚠️ {component}: {message}")
                
                if steps:
                    response_parts.append("\n**执行结果:**")
                    for step in steps:
                        if isinstance(step, str):
                            response_parts.append(f"  {step}")
                
                response_parts.append("\n还有其他需要帮忙的吗？")
                
                return {
                    "response": "\n".join(response_parts),
                    "type": "text",
                    "findings": findings
                }
            else:
                return {
                    "response": f"❌ 诊断执行失败: {result.error}",
                    "type": "text"
                }
                
        except Exception as e:
            logger.error(f"Ops diagnosis failed: {e}")
            return {
                "response": f"❌ 诊断过程出错: {str(e)}",
                "type": "text"
            }
    
    async def _handle_evaluation_query(self, query: str) -> Dict[str, Any]:
        """处理评估相关的查询"""
        try:
            import requests
            
            api_key = os.getenv("RANGEN_API_KEY", "")
            headers = {"Authorization": f"Bearer {api_key}"}
            
            response_parts = []
            response_parts.append("📊 **系统评估分析**\n")
            
            try:
                resp = requests.get(
                    f"{RANGEN_API_BASE}/api/v1/evaluation/report",
                    headers=headers,
                    timeout=10
                )
                if resp.status_code == 200:
                    data = resp.json()
                    response_parts.append("获取到评估报告:")
                    response_parts.append(f"```json\n{json.dumps(data, indent=2, ensure_ascii=False)}\n```")
                else:
                    response_parts.append(f"评估报告接口返回: {resp.status_code}")
            except Exception as e:
                response_parts.append(f"无法获取评估报告: {str(e)}")
            
            try:
                resp = requests.get(
                    f"{RANGEN_API_BASE}/health",
                    headers=headers,
                    timeout=5
                )
                if resp.status_code == 200:
                    health = resp.json()
                    response_parts.append("\n**系统健康状态:**")
                    response_parts.append(f"- 状态: {health.get('status', 'unknown')}")
                    response_parts.append(f"- 版本: {health.get('version', 'unknown')}")
                else:
                    response_parts.append("\n⚠️ 系统健康检查返回异常")
            except Exception as e:
                response_parts.append(f"\n⚠️ 无法获取健康状态: {str(e)}")
            
            response_parts.append("\n\n**性能提升建议:**")
            response_parts.append("1. 检查系统日志，分析错误原因")
            response_parts.append("2. 运行监控工具查看各组件状态")
            response_parts.append("3. 使用'帮我诊断'命令进行全面检查")
            
            return {
                "response": "\n".join(response_parts),
                "type": "text"
            }
            
        except Exception as e:
            logger.error(f"Evaluation query failed: {e}")
            return {
                "response": f"❌ 分析评估时出错: {str(e)}",
                "type": "text"
            }
    
    async def _handle_action(
        self,
        query: str,
        ctx: ConversationContext,
        intent: IntentResult
    ) -> Dict[str, Any]:
        """处理操作请求"""
        return await self._execute_ops_diagnosis(query, ctx)
    
    async def _handle_general_query(
        self,
        query: str,
        ctx: ConversationContext,
        intent: IntentResult
    ) -> Dict[str, Any]:
        """处理通用查询"""
        query_lower = query.lower()
        
        # 问候语
        greetings = ["你好", "hi", "hello", "嗨", "您好"]
        if any(g in query_lower for g in greetings):
            return {
                "response": "👋 你好！我是 RANGEN 智能助手。\n\n我可以帮您：\n- 🔍 运维诊断和修复\n- 🔧 创建 Agent、Skill、Tool\n- 💬 回答系统相关问题\n\n请告诉我您需要什么帮助？",
                "type": "text"
            }
        
        # 信息查询类问题 - "告诉我"、"是否"、"有没有"等
        query_keywords = ["告诉我", "是否", "有没有", "什么", "哪些", "如何", "怎么", "为什么"]
        if any(k in query_lower for k in query_keywords):
            return await self._answer_query(query, ctx)
        
        # 运维诊断类问题 - "检查"、"修复"、"状态"等
        ops_keywords = ["检查", "诊断", "修复", "状态", "health", "check", "重启", "清理"]
        if any(k in query_lower for k in ops_keywords):
            return await self._execute_ops_diagnosis(query, ctx)
        
        # 默认返回帮助提示
        return {
            "response": "🤔 我是 RANGEN 智能助手，专注于运维相关任务。\n\n我可以帮您：\n- 🔍 **运维诊断**：\"检查根路径\"、\"MCP服务状态\"\n- 🔧 **创建能力**：\"创建一个Agent\"、\"添加Skill\"\n- 💬 **信息查询**：\"告诉我系统有哪些功能\"\n\n请告诉我您需要什么帮助？",
            "type": "text"
        }
    
    async def _answer_query(
        self,
        query: str,
        ctx: ConversationContext
    ) -> Dict[str, Any]:
        """回答信息查询类问题 - 使用能力发现服务"""
        import re
        
        # URL 检测 - 优先处理
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, query)
        if urls:
            return await self._handle_url_query(urls[0], query, ctx)
        
        # 使用能力发现服务
        try:
            from src.services.capability_discovery_service import get_capability_discovery_service
            
            discovery = get_capability_discovery_service()
            
            # 发现匹配的能力
            plan = discovery.discover(query, {"history": ctx.history})
            
            logger.info(f"Discovered capabilities: {[c.capability.name for c in plan.matched_capabilities]}")
            
            # 直接执行能力（使用第一个匹配的）
            if plan.matched_capabilities:
                first_cap = plan.matched_capabilities[0]
                cap_name = first_cap.capability.name
                
                # 根据能力类型选择执行方式
                if cap_name == "ProductionWorkflow":
                    return await self._execute_production_workflow(query, ctx)
                elif cap_name == "OpsDiagnosisAgent":
                    return await self._execute_ops_diagnosis(query, ctx)
                elif cap_name == "WebCrawler":
                    # 如果没有 URL 但匹配到 WebCrawler，可能是内容分析需求
                    return await self._execute_production_workflow(query, ctx)
                
                # 默认使用 ProductionWorkflow
                return await self._execute_production_workflow(query, ctx)
            
        except Exception as e:
            logger.error(f"Capability discovery failed: {e}")
        
        # 回退到 ProductionWorkflow
        return await self._execute_production_workflow(query, ctx)
    
    async def _handle_url_query(
        self,
        url: str,
        query: str,
        ctx: ConversationContext
    ) -> Dict[str, Any]:
        """处理包含URL的查询"""
        try:
            from src.kms.web_crawler import WebCrawler
            
            crawler = WebCrawler(timeout=30)
            result = await crawler.crawl(url)
            
            if result.success:
                # 获取页面内容
                content = result.content[:8000]  # 限制内容长度
                title = result.title or url
                
                # 使用 LLM 总结内容
                return await self._summarize_content(url, title, content, query)
            else:
                return {
                    "response": f"❌ 无法访问该URL: {result.error}\n\n请检查链接是否正确，或尝试提供文章的主要内容。",
                    "type": "text"
                }
                
        except Exception as e:
            logger.error(f"URL handling failed: {e}")
            return {
                "response": f"❌ 处理URL时出错: {str(e)}",
                "type": "text"
            }
    
    async def _summarize_content(
        self,
        url: str,
        title: str,
        content: str,
        query: str
    ) -> Dict[str, Any]:
        """使用ProductionWorkflow总结网页内容"""
        try:
            # 构建包含内容的查询
            enhanced_query = f"""请分析以下网页内容并回答用户问题。

**网页标题**: {title}
**网页URL**: {url}
**用户问题**: {query}

**网页内容**:
{content}

请用简洁明了的方式回答用户的问题。如果内容不足以回答问题，请说明。"""
            
            # 使用 ProductionWorkflow 处理
            return await self._execute_production_workflow(enhanced_query, {"url": url, "title": title})
            
        except Exception as e:
            logger.error(f"Content summarization failed: {e}")
            return {
                "response": f"内容已获取，但总结失败。请访问以下链接查看原文:\n{url}",
                "type": "text"
            }
    
    def _get_production_workflow(self):
        try:
            from src.core.production_workflow import ProductionWorkflow
            return ProductionWorkflow()
        except:
            return None
    
    async def _execute_production_workflow(
        self,
        query: str,
        ctx: ConversationContext
    ) -> Dict[str, Any]:
        """执行ProductionWorkflow"""
        try:
            from src.core.production_workflow import ProductionWorkflow
            
            workflow = ProductionWorkflow()
            result = await workflow.execute(query=query, context={})
            
            answer = result.get("answer", result.get("final_answer", ""))
            
            return {
                "response": answer or "处理完成",
                "type": "text",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Production workflow failed: {e}")
            return {
                "response": f"处理请求时出错: {str(e)}",
                "type": "text"
            }
    
    async def _execute_tool(
        self,
        query: str,
        ctx: ConversationContext
    ) -> Dict[str, Any]:
        """执行工具"""
        try:
            from src.core.unified_tool_executor import get_unified_tool_executor
            
            executor = get_unified_tool_executor()
            if executor:
                result = await executor.execute(query=query)
                if result.success:
                    return {
                        "response": f"✅ 工具执行成功\n{result.output}",
                        "type": "text"
                    }
                else:
                    return {
                        "response": f"工具执行失败: {result.error}",
                        "type": "text"
                    }
            
            return await self._execute_production_workflow(query, ctx)
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return await self._execute_production_workflow(query, ctx)
    
    async def _handle_help(self, ctx: ConversationContext) -> Dict[str, Any]:
        """处理帮助请求"""
        help_text = """
🤖 **智能助手使用指南**

我可以帮助您完成以下任务：

**1. 运维诊断**
   - "检查根路径是否正常"
   - "MCP服务离线了，帮我重启"
   - "系统健康检查"

**2. 创建能力**
   - "帮我创建一个指标监控Agent"
   - "添加一个新的数据分析Skill"
   - "做一个API调用工具"

**3. 通用问答**
   - 直接输入您的问题

**4. 清除历史**
   - 输入 "clear" 或 "清除" 可以清除对话历史

请告诉我您需要什么帮助？
"""
        return {"response": help_text, "type": "text"}
    
    def get_session_context(self, session_id: str) -> Optional[ConversationContext]:
        return self._conversation_sessions.get(session_id)
    
    def clear_session(self, session_id: str):
        if session_id in self._conversation_sessions:
            del self._conversation_sessions[session_id]


_smart_conversation_agent: Optional[SmartConversationAgent] = None

def get_smart_conversation_agent() -> SmartConversationAgent:
    global _smart_conversation_agent
    if _smart_conversation_agent is None:
        _smart_conversation_agent = SmartConversationAgent()
    return _smart_conversation_agent
