#!/usr/bin/env python3
"""
Intent Router - 意图路由

将意图识别结果路由到合适的 Hand 执行。

工作流程：
1. 接收用户查询
2. 使用 IntentUnderstandingService 识别意图
3. 根据意图选择合适的 Hand
4. 规划执行步骤
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

from .base import BaseHand
from .registry import HandRegistry

logger = logging.getLogger(__name__)


class IntentRouter:
    """
    意图路由 - 连接意图识别和 Hand 执行
    """
    
    def __init__(self, registry: Optional[HandRegistry] = None):
        self.logger = logger
        self.registry = registry or HandRegistry()
        self._intent_service = None
        self._task_planner = None
        
        # 意图到 Hand 类别的映射
        self._intent_hand_mapping = {
            # 邮件相关
            "邮件": ["email", "mail", "收件", "发件", "收邮件", "发邮件"],
            "收件": ["email"],
            "发件": ["email"],
            
            # 文件操作
            "文件": ["file", "read", "write", "copy"],
            "读取": ["file_read", "file"],
            "写入": ["file_write", "file"],
            
            # 搜索相关
            "搜索": ["search", "web", "google"],
            "查询": ["search", "query"],
            
            # 数据库
            "数据库": ["database", "db", "sql", "query"],
            "查询": ["database", "query", "search"],
            
            # 日历
            "日历": ["calendar", "schedule", "event"],
            "日程": ["calendar", "schedule"],
            
            # 天气
            "天气": ["weather", "forecast"],
            
            # 翻译
            "翻译": ["translation", "translate"],
            
            # 通知
            "通知": ["notification", "notify", "slack"],
            "Slack": ["slack"],
            
            # GitHub
            "GitHub": ["github", "repo", "issue", "pr"],
            
            # Notion
            "Notion": ["notion", "page", "database"],
            
            # 系统命令
            "系统": ["system", "command", "shell"],
            "命令": ["system", "shell"],
        }
    
    def _get_intent_service(self):
        """懒加载意图理解服务"""
        if self._intent_service is None:
            try:
                from src.services.intent_understanding_service import IntentUnderstandingService
                self._intent_service = IntentUnderstandingService()
                self.logger.info("意图理解服务初始化成功")
            except Exception as e:
                self.logger.warning(f"意图理解服务初始化失败: {e}")
                self._intent_service = None
        return self._intent_service
    
    def _get_task_planner(self):
        """懒加载任务规划器"""
        if self._task_planner is None:
            try:
                from .task_planner import TaskPlanner
                self._task_planner = TaskPlanner(self.registry)
                self.logger.info("任务规划器初始化成功")
            except Exception as e:
                self.logger.warning(f"任务规划器初始化失败: {e}")
                self._task_planner = None
        return self._task_planner
    
    def route(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        路由查询到合适的 Hand
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            路由结果，包含意图和推荐的 Hands
        """
        context = context or {}
        
        # 1. 尝试使用 LLM 进行意图识别
        intent_result = self._recognize_intent(query, context)
        
        # 2. 根据意图匹配 Hands
        recommended_hands = self._match_hands(intent_result, query)
        
        # 3. 生成执行计划
        execution_plan = self._plan_execution(intent_result, recommended_hands, query)
        
        return {
            "query": query,
            "intent": intent_result,
            "recommended_hands": recommended_hands,
            "execution_plan": execution_plan,
            "can_execute": len(recommended_hands) > 0
        }
    
    def _recognize_intent(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """识别意图"""
        service = self._get_intent_service()
        
        if service:
            try:
                import asyncio
                # IntentUnderstandingService.understand 是异步方法
                result = asyncio.run(service.understand(query, context))
                return {
                    "intent": result.intent.value if hasattr(result.intent, 'value') else str(result.intent),
                    "confidence": result.confidence,
                    "entities": result.entities,
                    "reasoning": result.reasoning,
                    "method": "llm"
                }
            except Exception as e:
                self.logger.warning(f"LLM意图识别失败: {e}")
        
        # 回退到关键词匹配
        return self._keyword_intent_recognition(query)
    
    def _keyword_intent_recognition(self, query: str) -> Dict[str, Any]:
        """基于关键词的意图识别"""
        query_lower = query.lower()
        
        # 检测关键词
        for intent_type, keywords in self._intent_hand_mapping.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return {
                        "intent": intent_type,
                        "confidence": 0.8,
                        "entities": {"keyword": keyword},
                        "reasoning": f"匹配关键词: {keyword}",
                        "method": "keyword"
                    }
        
        # 默认查询意图
        return {
            "intent": "query",
            "confidence": 0.5,
            "entities": {},
            "reasoning": "默认查询意图",
            "method": "default"
        }
    
    def _match_hands(self, intent_result: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """根据意图匹配 Hands"""
        matched_hands = []
        intent_type = intent_result.get("intent", "").lower()
        query_lower = query.lower()
        
        # 获取所有注册的 Hands
        all_hands = self.registry.get_all_hands()
        
        # 精确匹配
        for hand in all_hands:
            hand_name = hand.name.lower()
            hand_desc = hand.description.lower()
            
            # 跳过模板占位符（名称包含 "operation" 的）
            # 优先选择有完整实现的 Hand
            is_template = "_operation" in hand_name or hand_name.endswith("_hand")
            implementation_bonus = 0 if is_template else 5  # 真实实现加5分
            
            score = 0
            matched_keywords = []
            
            # 检查查询中的关键词
            for keyword in self._intent_hand_mapping.keys():
                keyword_lower = keyword.lower()
                
                # 查询直接匹配
                if keyword_lower in query_lower:
                    score += 5  # 查询匹配权重最高
                    matched_keywords.append(keyword)
                    
                    # 检查 Hand 名称或描述是否也匹配
                    if keyword_lower in hand_name or keyword_lower in hand_desc:
                        score += 3  # Hand 匹配额外加分
                elif keyword_lower in hand_name or keyword_lower in hand_desc:
                    score += 1
                    matched_keywords.append(keyword)
                
                # 意图匹配
                if keyword_lower in intent_type:
                    score += 2
            
            # 额外检查：邮件相关关键词
            email_keywords = ["邮件", "email", "mail", "收件", "发件", "收邮件", "发邮件"]
            if any(kw in query_lower for kw in email_keywords):
                if "email" in hand_name:
                    score += 20  # 邮件相关最高优先级
                    matched_keywords.append("邮件")
            
            # 文件相关关键词
            file_keywords = ["文件", "读取", "写入", "file", "read", "write"]
            if any(kw in query_lower for kw in file_keywords):
                if "file" in hand_name:
                    score += 5
            
            # 添加实现加分
            score += implementation_bonus
            
            if score > 0:
                matched_hands.append({
                    "hand": hand,
                    "hand_name": hand.name,
                    "score": score,
                    "is_template": is_template,
                    "matched_keywords": matched_keywords,
                    "category": hand.category.value,
                    "safety_level": hand.safety_level.value
                })
        
        # 按分数排序（真实实现优先）
        matched_hands.sort(key=lambda x: (x["score"], not x["is_template"]), reverse=True)
        
        return matched_hands[:5]  # 返回前5个匹配
    
    def _plan_execution(
        self, 
        intent_result: Dict[str, Any], 
        recommended_hands: List[Dict[str, Any]],
        query: str
    ) -> Dict[str, Any]:
        """生成执行计划"""
        planner = self._get_task_planner()
        
        if planner and recommended_hands:
            try:
                plan = planner.plan(query, recommended_hands)
                return plan
            except Exception as e:
                self.logger.warning(f"执行计划生成失败: {e}")
        
        # 简单计划
        return {
            "steps": [{"hand": h["hand_name"], "action": "execute"} for h in recommended_hands],
            "type": "simple",
            "parallel": False
        }
    
    def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        路由并执行查询
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            执行结果
        """
        # 1. 路由
        route_result = self.route(query, context)
        
        if not route_result["can_execute"]:
            return {
                "success": False,
                "error": "无法理解查询或没有匹配的 Hand",
                "query": query
            }
        
        # 2. 获取推荐的 Hand
        recommended_hands = route_result["recommended_hands"]
        primary_hand = recommended_hands[0]["hand"]
        
        # 3. 执行
        try:
            import asyncio
            
            # 从 intent 中提取参数
            params = self._extract_parameters(query, route_result["intent"])
            
            # 执行 Hand
            result = asyncio.run(primary_hand.execute(**params))
            
            return {
                "success": result.success,
                "hand": primary_hand.name,
                "result": result.output,
                "error": result.error,
                "intent": route_result["intent"],
                "alternative_hands": [h["hand_name"] for h in recommended_hands[1:]]
            }
            
        except Exception as e:
            self.logger.error(f"执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "hand": primary_hand.name,
                "query": query
            }
    
    def _extract_parameters(self, query: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """从查询中提取参数"""
        params = {}
        
        # 从意图实体中提取
        entities = intent.get("entities", {})
        for key, value in entities.items():
            if value:
                params[key] = value
        
        # 从查询中提取常见参数
        import re
        
        # 邮箱地址
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, query)
        if emails:
            params["email"] = emails[0]
        
        # 关键词
        query_lower = query.lower()
        
        if "搜索" in query or "查找" in query or "search" in query_lower:
            params["operation"] = "search"
            search_term = query.replace("搜索", "").replace("查找", "").strip()
            if search_term:
                params["query"] = search_term
        
        if "收" in query and ("邮件" in query or "mail" in query_lower):
            params["operation"] = "fetch_unread"
        
        if "发" in query and ("邮件" in query or "mail" in query_lower):
            params["operation"] = "send"
        
        return params


def create_intent_router() -> IntentRouter:
    """创建意图路由器的便捷函数"""
    return IntentRouter()
