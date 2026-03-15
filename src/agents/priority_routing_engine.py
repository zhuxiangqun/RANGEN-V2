"""
智能优先级路由引擎

实现"先skill后MCP，先本地后外部"的智能路由策略
"""
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import time


class SkillSource(str, Enum):
    """技能来源"""
    LOCAL = "local"            # 本地内置技能（最高优先级）
    LOCAL_MCP = "local_mcp"   # 本地MCP服务器技能
    EXTERNAL = "external"     # 外部导入技能
    EXTERNAL_MCP = "external_mcp"  # 外部MCP服务器技能（最低优先级）
    
    @property
    def priority_score(self) -> int:
        """获取来源优先级分数"""
        return {
            SkillSource.LOCAL: 100,
            SkillSource.LOCAL_MCP: 80,
            SkillSource.EXTERNAL: 60,
            SkillSource.EXTERNAL_MCP: 40
        }[self]


class ToolSource(str, Enum):
    """工具来源"""
    LOCAL = "local"            # 本地内置工具（最高优先级）
    LOCAL_MCP = "local_mcp"   # 本地MCP服务器工具
    EXTERNAL_MCP = "external_mcp"  # 外部MCP服务器工具（最低优先级）
    CUSTOM_API = "custom_api"  # 自定义API工具
    UNKNOWN = "unknown"
    
    @property
    def priority_score(self) -> int:
        """获取来源优先级分数"""
        return {
            ToolSource.LOCAL: 100,
            ToolSource.LOCAL_MCP: 80,
            ToolSource.CUSTOM_API: 70,
            ToolSource.EXTERNAL_MCP: 50,
            ToolSource.UNKNOWN: 30
        }[self]


@dataclass
class PrioritizedSkill:
    """优先级技能"""
    skill_id: str
    name: str
    description: str
    source: SkillSource
    priority: int  # 100-0，越高越优先
    semantic_score: float  # 语义匹配分数 0-1
    performance_score: float  # 性能分数（基于历史数据）
    total_score: float  # 综合分数
    
    @property
    def final_priority(self) -> float:
        """计算最终优先级"""
        # 权重分配：来源优先级40%，语义匹配30%，性能30%
        source_weight = self.source.priority_score / 100.0
        semantic_weight = self.semantic_score
        performance_weight = self.performance_score
        
        return (
            source_weight * 0.4 +
            semantic_weight * 0.3 +
            performance_weight * 0.3
        )


@dataclass
class PrioritizedTool:
    """优先级工具"""
    tool_id: str
    name: str
    description: str
    source: ToolSource
    priority: int  # 100-0，越高越优先
    semantic_score: float  # 语义匹配分数 0-1
    latency_score: float  # 延迟分数（本地=1.0，外部<1.0）
    reliability_score: float  # 可靠性分数 0-1
    total_score: float  # 综合分数
    
    @property
    def final_priority(self) -> float:
        """计算最终优先级"""
        # 权重分配：来源优先级40%，语义匹配25%，延迟20%，可靠性15%
        source_weight = self.source.priority_score / 100.0
        semantic_weight = self.semantic_score
        latency_weight = self.latency_score
        reliability_weight = self.reliability_score
        
        return (
            source_weight * 0.4 +
            semantic_weight * 0.25 +
            latency_weight * 0.2 +
            reliability_weight * 0.15
        )


class PriorityRoutingEngine:
    """智能优先级路由引擎
    
    实现"先skill后MCP，先本地后外部"的智能路由策略
    """
    
    def __init__(self, skill_registry, tool_registry):
        """初始化路由引擎
        
        Args:
            skill_registry: 技能注册表实例
            tool_registry: 工具注册表实例
        """
        self.skill_registry = skill_registry
        self.tool_registry = tool_registry
        
        # 性能追踪数据
        self.skill_performance: Dict[str, Dict[str, Any]] = {}
        self.tool_performance: Dict[str, Dict[str, Any]] = {}
        
        # 路由决策历史记录
        self.routing_decisions: List[Dict[str, Any]] = []
        self.max_routing_decisions_history = 1000  # 最大历史记录数
        
        # 路由统计
        self.routing_stats = {
            "total_queries": 0,
            "skill_routing_count": 0,
            "tool_routing_count": 0,
            "local_resource_count": 0,
            "external_resource_count": 0,
            "fallback_count": 0,
            "avg_decision_time": 0.0,
            "success_rate": 0.0
        }
        
        # 默认延迟和可靠性分数（基于来源）
        self.default_latency_scores = {
            ToolSource.LOCAL: 1.0,
            ToolSource.LOCAL_MCP: 0.9,
            ToolSource.CUSTOM_API: 0.8,
            ToolSource.EXTERNAL_MCP: 0.7,
            ToolSource.UNKNOWN: 0.5
        }
        
        self.default_reliability_scores = {
            ToolSource.LOCAL: 1.0,
            ToolSource.LOCAL_MCP: 0.9,
            ToolSource.CUSTOM_API: 0.8,
            ToolSource.EXTERNAL_MCP: 0.7,
            ToolSource.UNKNOWN: 0.5
        }
        
        # 监控日志
        self.monitoring_enabled = True
        self.decision_time_window = 300  # 5分钟时间窗口
        
        # 网络状况监控
        self.network_monitoring_enabled = True
        self.server_latency_data: Dict[str, Dict[str, Any]] = {}
        self.last_network_check: Dict[str, float] = {}
        self.network_check_interval = 60  # 网络检查间隔（秒）
        self.max_allowed_latency = 5.0  # 最大允许延迟（秒）
        
        # 动态优先级调整配置
        self.dynamic_priority_adjustment = True
        self.latency_weight = 0.3  # 延迟对优先级的影响权重
        self.reliability_weight = 0.2  # 可靠性对优先级的影响权重
        self.base_source_weight = 0.5  # 基础来源权重
    
    def discover_skills_with_priority(self, query: str, limit: int = 5) -> List[PrioritizedSkill]:
        """按优先级发现技能
        
        实现"先skill后MCP，先本地后外部"策略
        
        Args:
            query: 查询文本
            limit: 返回数量限制
            
        Returns:
            按优先级排序的技能列表
        """
        # 1. 使用技能注册表发现相关技能
        raw_skills = self.skill_registry.discover(query, limit=limit * 3)
        
        prioritized_skills = []
        
        for skill_result in raw_skills:
            skill = skill_result["skill"]
            semantic_score = min(1.0, skill_result["score"] / 10.0)  # 归一化到0-1
            
            # 确定技能来源
            source = self._determine_skill_source(skill)
            
            # 获取性能分数
            performance_score = self._get_skill_performance(skill.skill_id)
            
            # 获取优先级（从数据库或默认）
            priority = self._get_skill_priority(skill, source)
            
            prioritized_skill = PrioritizedSkill(
                skill_id=skill.skill_id,
                name=skill.name,
                description=skill.description,
                source=source,
                priority=priority,
                semantic_score=semantic_score,
                performance_score=performance_score,
                total_score=0.0  # 稍后计算
            )
            
            # 计算总分数
            prioritized_skill.total_score = prioritized_skill.final_priority
            
            prioritized_skills.append(prioritized_skill)
        
        # 2. 按优先级排序
        prioritized_skills.sort(key=lambda x: x.total_score, reverse=True)
        
        # 3. 返回前limit个
        return prioritized_skills[:limit]
    
    def select_tools_with_priority(self, query: str, top_k: int = 3) -> List[PrioritizedTool]:
        """按优先级选择工具
        
        实现"先本地后外部"策略
        
        Args:
            query: 查询文本
            top_k: 返回数量
            
        Returns:
            按优先级排序的工具列表
        """
        # 获取所有工具
        all_tools = self.tool_registry.get_all_tools()
        
        prioritized_tools = []
        
        for tool in all_tools:
            # 计算语义匹配分数
            semantic_score = self._calculate_tool_semantic_score(query, tool)
            
            # 确定工具来源
            source = self._determine_tool_source(tool)
            
            # 获取延迟和可靠性分数
            latency_score = self._get_tool_latency_score(tool, source)
            reliability_score = self._get_tool_reliability_score(tool, source)
            
            # 获取优先级
            priority = self._get_tool_priority(tool, source)
            
            prioritized_tool = PrioritizedTool(
                tool_id=tool.get("id", ""),
                name=tool.get("name", ""),
                description=tool.get("description", ""),
                source=source,
                priority=priority,
                semantic_score=semantic_score,
                latency_score=latency_score,
                reliability_score=reliability_score,
                total_score=0.0
            )
            
            # 计算总分数（考虑动态网络调整）
            base_score = prioritized_tool.final_priority
            
            # 提取服务器名称（如果是MCP工具）
            server_name = None
            if prioritized_tool.source in [ToolSource.LOCAL_MCP, ToolSource.EXTERNAL_MCP]:
                server_name = self._extract_server_name_from_tool_id(prioritized_tool.tool_id)
            
            # 应用动态网络调整
            if self.dynamic_priority_adjustment and server_name:
                adjusted_score = self.adjust_priority_based_on_network(
                    base_score * 100,  # 转换为100分制
                    prioritized_tool.source,
                    server_name
                ) / 100.0  # 转换回0-1分制
                prioritized_tool.total_score = adjusted_score
            else:
                prioritized_tool.total_score = base_score
            
            prioritized_tools.append(prioritized_tool)
        
        # 按优先级排序
        prioritized_tools.sort(key=lambda x: x.total_score, reverse=True)
        
        # 返回前top_k个
        return prioritized_tools[:top_k]
    
    def route_request(self, query: str) -> Dict[str, Any]:
        """智能路由请求
        
        完整实现"先skill后MCP，先本地后外部"策略
        
        Args:
            query: 用户请求
            
        Returns:
            路由结果，包含推荐的技能和工具
        """
        start_time = time.time()
        
        result = {
            "query": query,
            "recommended_skills": [],
            "recommended_tools": [],
            "strategy": "先skill后MCP，先本地后外部"
        }
        
        # 1. 优先发现技能
        skills = self.discover_skills_with_priority(query, limit=3)
        result["recommended_skills"] = [
            {
                "skill_id": skill.skill_id,
                "name": skill.name,
                "source": skill.source.value,
                "priority_score": skill.total_score,
                "description": skill.description
            }
            for skill in skills
        ]
        
        decision_data = {
            "query": query,
            "decision_time": time.time() - start_time,
            "context": {}
        }
        
        # 2. 如果找到技能，优先使用技能
        if skills:
            result["recommended_action"] = "use_skill"
            result["primary_recommendation"] = {
                "type": "skill",
                "id": skills[0].skill_id,
                "name": skills[0].name,
                "reason": f"找到匹配技能，优先级: {skills[0].total_score:.2f}"
            }
            
            # 记录技能路由决策
            decision_data.update({
                "decision_type": "skill_routing",
                "selected_resource": skills[0].skill_id,
                "selected_resource_type": "skill",
                "selected_resource_source": skills[0].source.value,
                "priority_score": skills[0].total_score,
                "semantic_score": skills[0].semantic_score,
                "alternative_options": len(skills) - 1
            })
        else:
            # 3. 如果没有找到技能，选择工具
            tools = self.select_tools_with_priority(query, top_k=3)
            result["recommended_tools"] = [
                {
                    "tool_id": tool.tool_id,
                    "name": tool.name,
                    "source": tool.source.value,
                    "priority_score": tool.total_score,
                    "description": tool.description
                }
                for tool in tools
            ]
            
            if tools:
                result["recommended_action"] = "use_tool"
                result["primary_recommendation"] = {
                    "type": "tool",
                    "id": tools[0].tool_id,
                    "name": tools[0].name,
                    "reason": f"找到匹配工具，优先级: {tools[0].total_score:.2f}"
                }
                
                # 记录工具路由决策
                decision_data.update({
                    "decision_type": "tool_routing",
                    "selected_resource": tools[0].tool_id,
                    "selected_resource_type": "tool",
                    "selected_resource_source": tools[0].source.value,
                    "priority_score": tools[0].total_score,
                    "semantic_score": tools[0].semantic_score,
                    "alternative_options": len(tools) - 1
                })
            else:
                result["recommended_action"] = "no_match"
                result["primary_recommendation"] = {
                    "type": "none",
                    "reason": "未找到匹配的技能或工具"
                }
                
                # 记录回退决策
                decision_data.update({
                    "decision_type": "fallback",
                    "selected_resource": None,
                    "selected_resource_type": "none",
                    "selected_resource_source": "none",
                    "priority_score": 0.0,
                    "semantic_score": 0.0,
                    "alternative_options": 0
                })
        
        # 更新决策时间
        decision_data["decision_time"] = time.time() - start_time
        
        # 记录路由决策
        if self.monitoring_enabled:
            self.record_routing_decision(decision_data)
        
        return result
    
    def _determine_skill_source(self, skill) -> SkillSource:
        """确定技能来源"""
        # 检查source字段
        if hasattr(skill, 'source') and skill.source:
            try:
                return SkillSource(skill.source)
            except ValueError:
                pass
        
        # 根据skill_id推断
        skill_id = skill.skill_id.lower()
        
        if skill_id.startswith("mcp_"):
            # 检查是否是本地MCP
            if "_local_" in skill_id or skill_id.endswith("_local"):
                return SkillSource.LOCAL_MCP
            else:
                return SkillSource.EXTERNAL_MCP
        elif skill_id.startswith("builtin_") or skill_id.startswith("core_"):
            return SkillSource.LOCAL
        else:
            # 默认为外部技能
            return SkillSource.EXTERNAL
    
    def _determine_tool_source(self, tool: Dict[str, Any]) -> ToolSource:
        """确定工具来源"""
        # 检查source字段
        source = tool.get("source")
        if source:
            try:
                return ToolSource(source)
            except ValueError:
                pass
        
        # 根据tool_id推断
        tool_id = tool.get("id", "").lower()
        tool_type = tool.get("type", "").lower()
        
        if tool_id.startswith("mcp_"):
            # 检查server_type或source字段
            if "local" in tool_id or tool.get("server_type") == "local":
                return ToolSource.LOCAL_MCP
            else:
                return ToolSource.EXTERNAL_MCP
        elif tool_type == "builtin" or tool_id.startswith("builtin_"):
            return ToolSource.LOCAL
        elif tool_type == "custom_api":
            return ToolSource.CUSTOM_API
        else:
            return ToolSource.UNKNOWN
    
    def _calculate_tool_semantic_score(self, query: str, tool: Dict[str, Any]) -> float:
        """计算工具语义匹配分数"""
        query_lower = query.lower()
        description = tool.get("description", "").lower()
        name = tool.get("name", "").lower()
        
        score = 0.0
        
        # 检查描述中的关键词
        query_words = set(query_lower.split())
        desc_words = set(description.split())
        
        if query_words and desc_words:
            overlap = len(query_words.intersection(desc_words))
            score += overlap * 0.2
        
        # 检查名称匹配
        if any(word in name for word in query_words):
            score += 0.3
        
        # 限制在0-1之间
        return min(1.0, score)
    
    def _get_skill_performance(self, skill_id: str) -> float:
        """获取技能性能分数"""
        if skill_id in self.skill_performance:
            perf = self.skill_performance[skill_id]
            success_rate = perf.get("success_rate", 0.8)
            avg_time = perf.get("avg_execution_time", 1.0)
            
            # 计算性能分数：成功率权重70%，执行时间权重30%
            time_score = max(0.0, 1.0 - min(avg_time / 10.0, 1.0))  # 时间越短分数越高
            return success_rate * 0.7 + time_score * 0.3
        
        # 默认性能分数
        return 0.8
    
    def _get_tool_latency_score(self, tool: Dict[str, Any], source: ToolSource) -> float:
        """获取工具延迟分数"""
        # 首先检查是否有历史延迟数据
        tool_id = tool.get("id")
        if tool_id in self.tool_performance:
            perf = self.tool_performance[tool_id]
            avg_latency = perf.get("avg_latency", 1.0)
            # 延迟越短分数越高
            historical_score = max(0.1, 1.0 - min(avg_latency / 5.0, 0.9))
        else:
            historical_score = self.default_latency_scores.get(source, 0.5)
        
        # 如果启用了动态优先级调整，结合实时网络状况
        if self.dynamic_priority_adjustment and source in [ToolSource.LOCAL_MCP, ToolSource.EXTERNAL_MCP]:
            # 尝试从工具ID提取服务器名称
            server_name = self._extract_server_name_from_tool_id(tool_id)
            if server_name:
                dynamic_score = self.get_dynamic_latency_score(source, server_name)
                # 结合历史分数和动态分数（历史权重0.3，动态权重0.7）
                return historical_score * 0.3 + dynamic_score * 0.7
        
        return historical_score
    
    def _extract_server_name_from_tool_id(self, tool_id: str) -> Optional[str]:
        """从工具ID中提取服务器名称
        
        工具ID格式示例: mcp_{server_name}_{tool_name}
        """
        if not tool_id:
            return None
        
        parts = tool_id.split('_')
        if len(parts) >= 2 and parts[0] == 'mcp':
            return parts[1]
        
        return None
    
    def _get_tool_reliability_score(self, tool: Dict[str, Any], source: ToolSource) -> float:
        """获取工具可靠性分数"""
        # 首先检查是否有历史可靠性数据
        tool_id = tool.get("id")
        if tool_id in self.tool_performance:
            perf = self.tool_performance[tool_id]
            success_rate = perf.get("success_rate", 0.8)
            historical_score = success_rate
        else:
            historical_score = self.default_reliability_scores.get(source, 0.5)
        
        # 如果启用了动态优先级调整，结合实时网络状况
        if self.dynamic_priority_adjustment and source in [ToolSource.LOCAL_MCP, ToolSource.EXTERNAL_MCP]:
            # 尝试从工具ID提取服务器名称
            server_name = self._extract_server_name_from_tool_id(tool_id)
            if server_name:
                dynamic_score = self.get_dynamic_reliability_score(source, server_name)
                # 结合历史分数和动态分数（历史权重0.4，动态权重0.6）
                return historical_score * 0.4 + dynamic_score * 0.6
        
        return historical_score
    
    def _get_skill_priority(self, skill, source: SkillSource) -> int:
        """获取技能优先级"""
        # 首先检查skill是否有priority字段
        if hasattr(skill, 'priority') and skill.priority is not None:
            return skill.priority
        
        # 使用基于来源的默认优先级
        return source.priority_score
    
    def _get_tool_priority(self, tool: Dict[str, Any], source: ToolSource) -> int:
        """获取工具优先级"""
        # 首先检查tool是否有priority字段
        priority = tool.get("priority")
        if priority is not None:
            return priority
        
        # 使用基于来源的默认优先级
        return source.priority_score
    
    def record_routing_decision(self, decision_data: Dict[str, Any]):
        """记录路由决策
        
        Args:
            decision_data: 路由决策数据，包含以下字段：
                - query: 查询文本
                - decision_type: 决策类型 (skill_routing, tool_routing, fallback)
                - selected_resource: 选中的资源ID
                - selected_resource_type: 资源类型 (skill, tool)
                - selected_resource_source: 资源来源 (local, local_mcp, external_mcp, etc.)
                - priority_score: 优先级分数
                - semantic_score: 语义匹配分数
                - decision_time: 决策耗时(秒)
                - timestamp: 时间戳(默认为当前时间)
                - context: 上下文信息
        """
        if not self.monitoring_enabled:
            return
        
        # 添加时间戳
        import time
        decision_data["timestamp"] = decision_data.get("timestamp", time.time())
        
        # 添加到历史记录
        self.routing_decisions.append(decision_data)
        
        # 限制历史记录大小
        if len(self.routing_decisions) > self.max_routing_decisions_history:
            self.routing_decisions = self.routing_decisions[-self.max_routing_decisions_history:]
        
        # 更新统计信息
        self._update_routing_stats(decision_data)
        
        # 记录日志
        self._log_routing_decision(decision_data)
    
    def _update_routing_stats(self, decision_data: Dict[str, Any]):
        """更新路由统计信息"""
        self.routing_stats["total_queries"] += 1
        
        decision_type = decision_data.get("decision_type", "")
        if decision_type == "skill_routing":
            self.routing_stats["skill_routing_count"] += 1
        elif decision_type == "tool_routing":
            self.routing_stats["tool_routing_count"] += 1
        elif decision_type == "fallback":
            self.routing_stats["fallback_count"] += 1
        
        # 统计本地/外部资源使用
        resource_source = decision_data.get("selected_resource_source", "")
        if resource_source in ["local", "local_mcp"]:
            self.routing_stats["local_resource_count"] += 1
        elif resource_source in ["external", "external_mcp"]:
            self.routing_stats["external_resource_count"] += 1
        
        # 更新平均决策时间
        decision_time = decision_data.get("decision_time", 0.0)
        current_avg = self.routing_stats["avg_decision_time"]
        total_decisions = self.routing_stats["total_queries"]
        
        # 移动平均
        if total_decisions == 1:
            self.routing_stats["avg_decision_time"] = decision_time
        else:
            alpha = 0.1  # 平滑因子
            self.routing_stats["avg_decision_time"] = (1 - alpha) * current_avg + alpha * decision_time
    
    def _log_routing_decision(self, decision_data: Dict[str, Any]):
        """记录路由决策日志"""
        import logging
        
        logger = logging.getLogger(__name__)
        
        query = decision_data.get("query", "")[:50]  # 截断长查询
        decision_type = decision_data.get("decision_type", "unknown")
        resource_id = decision_data.get("selected_resource", "unknown")
        resource_source = decision_data.get("selected_resource_source", "unknown")
        priority_score = decision_data.get("priority_score", 0.0)
        decision_time = decision_data.get("decision_time", 0.0)
        
        log_message = (
            f"路由决策: 查询='{query}'，类型={decision_type}，"
            f"资源={resource_id}({resource_source})，"
            f"优先级={priority_score:.2f}，耗时={decision_time:.3f}s"
        )
        
        if decision_type == "fallback":
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def get_routing_statistics(self) -> Dict[str, Any]:
        """获取路由统计信息"""
        stats = self.routing_stats.copy()
        
        # 计算成功率（基于最近的决策）
        if stats["total_queries"] > 0:
            # 这里可以添加更复杂的成功率计算逻辑
            stats["success_rate"] = 0.85  # 默认值，可根据实际数据调整
        
        # 添加性能指标
        stats["local_resource_ratio"] = (
            stats["local_resource_count"] / max(1, stats["total_queries"])
        )
        stats["skill_routing_ratio"] = (
            stats["skill_routing_count"] / max(1, stats["total_queries"])
        )
        
        return stats
    
    def get_recent_decisions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取最近的路由决策"""
        return self.routing_decisions[-limit:] if self.routing_decisions else []
    
    def check_network_health(self, server_name: str, server_url: Optional[str] = None) -> Dict[str, Any]:
        """检查服务器网络健康状况
        
        Args:
            server_name: 服务器名称
            server_url: 服务器URL（可选，如果为None则从已注册数据中获取）
            
        Returns:
            网络健康状态，包含延迟、可用性等信息
        """
        if not self.network_monitoring_enabled:
            return {"status": "monitoring_disabled", "latency": 1.0, "available": True}
        
        import requests
        import socket
        from urllib.parse import urlparse
        
        try:
            # 检查是否需要执行网络检查（避免过于频繁）
            current_time = time.time()
            last_check = self.last_network_check.get(server_name, 0)
            
            if current_time - last_check < self.network_check_interval:
                # 使用缓存的延迟数据
                cached_data = self.server_latency_data.get(server_name)
                if cached_data:
                    return cached_data
            
            # 如果没有提供URL，尝试从工具注册表获取
            if server_url is None:
                server_url = self._get_server_url_from_registry(server_name)
            
            if not server_url:
                return {"status": "no_url", "latency": self.max_allowed_latency, "available": False}
            
            # 测量延迟
            start_time = time.time()
            
            # 根据URL类型执行不同的检查
            parsed_url = urlparse(server_url)
            
            if parsed_url.scheme.startswith('http'):
                # HTTP/HTTPS 服务器
                try:
                    response = requests.get(f"{parsed_url.scheme}://{parsed_url.netloc}/", timeout=2)
                    latency = time.time() - start_time
                    available = response.status_code < 500
                except requests.exceptions.RequestException as e:
                    latency = self.max_allowed_latency
                    available = False
            else:
                # 其他类型（如stdio），使用socket连接检查
                try:
                    host = parsed_url.hostname or 'localhost'
                    port = parsed_url.port or 8080
                    
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    sock.connect((host, port))
                    sock.close()
                    latency = time.time() - start_time
                    available = True
                except (socket.timeout, ConnectionRefusedError, OSError) as e:
                    latency = self.max_allowed_latency
                    available = False
            
            # 保存结果
            health_data = {
                "status": "healthy" if available else "unhealthy",
                "latency": latency,
                "available": available,
                "last_check": current_time,
                "server_name": server_name,
                "server_url": server_url
            }
            
            self.server_latency_data[server_name] = health_data
            self.last_network_check[server_name] = current_time
            
            # 记录日志
            if not available:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"服务器 {server_name} 网络不可用，延迟: {latency:.3f}s")
            
            return health_data
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"检查服务器 {server_name} 网络健康状态失败: {e}")
            
            return {
                "status": "error",
                "latency": self.max_allowed_latency,
                "available": False,
                "error": str(e),
                "last_check": time.time()
            }
    
    def _get_server_url_from_registry(self, server_name: str) -> Optional[str]:
        """从工具注册表获取服务器URL"""
        # 这里需要实现从工具注册表获取服务器URL的逻辑
        # 由于具体实现取决于工具注册表的结构，这里提供一个示例
        try:
            # 假设工具注册表有get_server_info方法
            if hasattr(self.tool_registry, 'get_server_info'):
                server_info = self.tool_registry.get_server_info(server_name)
                if server_info and 'url' in server_info:
                    return server_info['url']
            
            # 或者从工具ID中提取
            # 工具ID格式可能是: mcp_{server_name}_{tool_name}
            # 可以尝试查找以mcp_{server_name}_开头的工具
            all_tools = self.tool_registry.get_all_tools()
            for tool in all_tools:
                tool_id = tool.get('id', '')
                if tool_id.startswith(f"mcp_{server_name}_"):
                    # 返回一个默认URL或从工具配置中获取
                    return f"http://{server_name}.local:8000"
            
            return None
        except Exception:
            return None
    
    def get_dynamic_latency_score(self, source: ToolSource, server_name: Optional[str] = None) -> float:
        """获取动态延迟分数（基于实时网络状况）"""
        if not self.dynamic_priority_adjustment:
            # 使用默认延迟分数
            return self.default_latency_scores.get(source, 0.5)
        
        # 对于本地资源，返回最高分数
        if source == ToolSource.LOCAL:
            return 1.0
        
        # 对于MCP资源，检查服务器网络状况
        if source in [ToolSource.LOCAL_MCP, ToolSource.EXTERNAL_MCP] and server_name:
            health_data = self.check_network_health(server_name)
            latency = health_data.get("latency", self.max_allowed_latency)
            available = health_data.get("available", False)
            
            if not available:
                # 服务器不可用，降低分数
                return 0.2
            
            # 根据延迟计算分数（延迟越低分数越高）
            # 归一化延迟：1.0 - min(latency / max_allowed_latency, 1.0)
            normalized_latency = min(latency / self.max_allowed_latency, 1.0)
            latency_score = 1.0 - normalized_latency
            
            # 确保分数在合理范围内
            return max(0.1, min(1.0, latency_score * 0.9 + 0.1))  # 在0.1-1.0之间
        
        # 默认情况
        return self.default_latency_scores.get(source, 0.5)
    
    def get_dynamic_reliability_score(self, source: ToolSource, server_name: Optional[str] = None) -> float:
        """获取动态可靠性分数（基于实时网络状况）"""
        if not self.dynamic_priority_adjustment:
            # 使用默认可靠性分数
            return self.default_reliability_scores.get(source, 0.5)
        
        # 对于本地资源，返回最高分数
        if source == ToolSource.LOCAL:
            return 1.0
        
        # 对于MCP资源，检查服务器网络状况
        if source in [ToolSource.LOCAL_MCP, ToolSource.EXTERNAL_MCP] and server_name:
            health_data = self.check_network_health(server_name)
            available = health_data.get("available", False)
            
            if not available:
                # 服务器不可用，降低可靠性分数
                return 0.3
            
            # 根据历史成功率和网络状况计算可靠性
            # 这里可以结合历史性能和网络状况
            base_score = self.default_reliability_scores.get(source, 0.5)
            
            # 如果服务器可用，提高分数；否则降低分数
            if available:
                return min(1.0, base_score * 1.2)
            else:
                return max(0.1, base_score * 0.5)
        
        # 默认情况
        return self.default_reliability_scores.get(source, 0.5)
    
    def adjust_priority_based_on_network(self, base_priority: float, source: ToolSource, 
                                        server_name: Optional[str] = None) -> float:
        """基于网络状况调整优先级"""
        if not self.dynamic_priority_adjustment:
            return base_priority
        
        # 获取动态分数
        latency_score = self.get_dynamic_latency_score(source, server_name)
        reliability_score = self.get_dynamic_reliability_score(source, server_name)
        
        # 计算调整后的优先级
        # 基础权重来自来源类型，动态权重来自网络状况
        adjusted_priority = (
            base_priority * self.base_source_weight +
            latency_score * 100 * self.latency_weight +  # 转换为100分制
            reliability_score * 100 * self.reliability_weight
        ) / (self.base_source_weight + self.latency_weight + self.reliability_weight)
        
        # 限制在合理范围内
        return max(10.0, min(100.0, adjusted_priority))
    
    def record_skill_performance(self, skill_id: str, success: bool, execution_time: float):
        """记录技能性能数据"""
        if skill_id not in self.skill_performance:
            self.skill_performance[skill_id] = {
                "total_calls": 0,
                "success_count": 0,
                "total_time": 0.0,
                "success_rate": 0.8,
                "avg_execution_time": 1.0
            }
        
        perf = self.skill_performance[skill_id]
        perf["total_calls"] += 1
        perf["total_time"] += execution_time
        
        if success:
            perf["success_count"] += 1
        
        # 更新平均值
        perf["success_rate"] = perf["success_count"] / max(1, perf["total_calls"])
        perf["avg_execution_time"] = perf["total_time"] / max(1, perf["total_calls"])
    
    def record_tool_performance(self, tool_id: str, success: bool, latency: float):
        """记录工具性能数据"""
        if tool_id not in self.tool_performance:
            self.tool_performance[tool_id] = {
                "total_calls": 0,
                "success_count": 0,
                "total_latency": 0.0,
                "success_rate": 0.8,
                "avg_latency": 1.0
            }
        
        perf = self.tool_performance[tool_id]
        perf["total_calls"] += 1
        perf["total_latency"] += latency
        
        if success:
            perf["success_count"] += 1
        
        # 更新平均值
        perf["success_rate"] = perf["success_count"] / max(1, perf["total_calls"])
        perf["avg_latency"] = perf["total_latency"] / max(1, perf["total_calls"])


# 单例实例
_priority_routing_engine: Optional[PriorityRoutingEngine] = None


def get_priority_routing_engine(skill_registry=None, tool_registry=None) -> PriorityRoutingEngine:
    """获取优先级路由引擎单例"""
    global _priority_routing_engine
    if _priority_routing_engine is None:
        if skill_registry is None or tool_registry is None:
            raise ValueError("首次调用需要提供skill_registry和tool_registry")
        _priority_routing_engine = PriorityRoutingEngine(skill_registry, tool_registry)
    return _priority_routing_engine