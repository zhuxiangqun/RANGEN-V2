#!/usr/bin/env python3
"""
用户行为模拟器 - 模拟真实用户行为进行测试
"""

import random
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime, timedelta
import asyncio


class UserType(Enum):
    """用户类型"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ActionType(Enum):
    """行为类型"""
    QUERY = "query"
    NAVIGATION = "navigation"
    CONFIGURATION = "configuration"
    ERROR_RECOVERY = "error_recovery"
    FEEDBACK = "feedback"


@dataclass
class UserProfile:
    """用户画像"""
    user_id: str
    user_type: UserType
    experience_level: int  # 1-10
    preferred_features: List[str]
    usage_patterns: Dict[str, Any]
    error_tolerance: float  # 0-1
    patience_level: float  # 0-1


@dataclass
class UserAction:
    """用户行为"""
    action_id: str
    user_id: str
    action_type: ActionType
    timestamp: float
    duration: float
    success: bool
    data: Dict[str, Any]
    context: Dict[str, Any]


@dataclass
class SimulationSession:
    """模拟会话"""
    session_id: str
    user_profile: UserProfile
    start_time: float
    end_time: Optional[float]
    actions: List[UserAction]
    success_rate: float
    satisfaction_score: float


class UserBehaviorSimulator:
    """用户行为模拟器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.user_profiles: List[UserProfile] = []
        self.simulation_sessions: List[SimulationSession] = []
        self.behavior_patterns: Dict[str, Any] = {}
        self.error_scenarios: List[Dict[str, Any]] = []
        
        # 初始化行为模式
        self._initialize_behavior_patterns()
        self._initialize_error_scenarios()
        self._generate_user_profiles()
    
    def _initialize_behavior_patterns(self):
        """初始化行为模式"""
        self.behavior_patterns = {
            "query_patterns": {
                "beginner": {
                    "common_queries": [
                        "如何开始使用系统？",
                        "系统有什么功能？",
                        "如何配置基本设置？"
                    ],
                    "query_frequency": 0.8,
                    "complexity_range": (1, 3)
                },
                "intermediate": {
                    "common_queries": [
                        "如何优化系统性能？",
                        "如何自定义配置？",
                        "如何集成外部服务？"
                    ],
                    "query_frequency": 0.9,
                    "complexity_range": (2, 5)
                },
                "advanced": {
                    "common_queries": [
                        "如何实现高级功能？",
                        "如何进行系统调试？",
                        "如何扩展系统架构？"
                    ],
                    "query_frequency": 0.95,
                    "complexity_range": (4, 8)
                },
                "expert": {
                    "common_queries": [
                        "如何实现自定义算法？",
                        "如何进行性能调优？",
                        "如何实现高级集成？"
                    ],
                    "query_frequency": 1.0,
                    "complexity_range": (6, 10)
                }
            },
            "navigation_patterns": {
                "beginner": {
                    "preferred_paths": ["linear", "guided"],
                    "exploration_rate": 0.3,
                    "backtrack_frequency": 0.2
                },
                "intermediate": {
                    "preferred_paths": ["hierarchical", "categorized"],
                    "exploration_rate": 0.6,
                    "backtrack_frequency": 0.1
                },
                "advanced": {
                    "preferred_paths": ["direct", "shortcut"],
                    "exploration_rate": 0.8,
                    "backtrack_frequency": 0.05
                },
                "expert": {
                    "preferred_paths": ["direct", "custom"],
                    "exploration_rate": 0.9,
                    "backtrack_frequency": 0.02
                }
            },
            "error_handling": {
                "beginner": {
                    "error_tolerance": 0.3,
                    "retry_attempts": 3,
                    "help_seeking_rate": 0.8
                },
                "intermediate": {
                    "error_tolerance": 0.5,
                    "retry_attempts": 2,
                    "help_seeking_rate": 0.5
                },
                "advanced": {
                    "error_tolerance": 0.7,
                    "retry_attempts": 1,
                    "help_seeking_rate": 0.2
                },
                "expert": {
                    "error_tolerance": 0.9,
                    "retry_attempts": 1,
                    "help_seeking_rate": 0.1
                }
            }
        }
    
    def _initialize_error_scenarios(self):
        """初始化错误场景"""
        self.error_scenarios = [
            {
                "type": "network_error",
                "probability": 0.1,
                "description": "网络连接错误",
                "recovery_actions": ["retry", "check_connection", "contact_support"]
            },
            {
                "type": "validation_error",
                "probability": 0.15,
                "description": "输入验证错误",
                "recovery_actions": ["correct_input", "check_format", "read_documentation"]
            },
            {
                "type": "permission_error",
                "probability": 0.05,
                "description": "权限不足错误",
                "recovery_actions": ["check_permissions", "contact_admin", "use_alternative"]
            },
            {
                "type": "timeout_error",
                "probability": 0.08,
                "description": "操作超时错误",
                "recovery_actions": ["retry", "increase_timeout", "optimize_query"]
            },
            {
                "type": "resource_error",
                "probability": 0.12,
                "description": "资源不足错误",
                "recovery_actions": ["free_resources", "scale_up", "optimize_usage"]
            }
        ]
    
    def _generate_user_profiles(self):
        """生成用户画像"""
        user_types = [UserType.BEGINNER, UserType.INTERMEDIATE, UserType.ADVANCED, UserType.EXPERT]
        
        for i, user_type in enumerate(user_types):
            profile = UserProfile(
                user_id=f"user_{i+1}",
                user_type=user_type,
                experience_level=random.randint(1, 10),
                preferred_features=self._generate_preferred_features(user_type),
                usage_patterns=self._generate_usage_patterns(user_type),
                error_tolerance=random.uniform(0.3, 0.9),
                patience_level=random.uniform(0.4, 1.0)
            )
            self.user_profiles.append(profile)
    
    def _generate_preferred_features(self, user_type: UserType) -> List[str]:
        """生成偏好功能"""
        feature_sets = {
            UserType.BEGINNER: ["basic_query", "help_system", "guided_tutorial"],
            UserType.INTERMEDIATE: ["advanced_query", "customization", "integration"],
            UserType.ADVANCED: ["api_access", "debugging", "performance_tuning"],
            UserType.EXPERT: ["algorithm_customization", "system_extension", "advanced_integration"]
        }
        return feature_sets.get(user_type, [])
    
    def _generate_usage_patterns(self, user_type: UserType) -> Dict[str, Any]:
        """生成使用模式"""
        patterns = self.behavior_patterns["query_patterns"][user_type.value]
        return {
            "session_duration": random.uniform(5, 60),  # 分钟
            "query_frequency": patterns["query_frequency"],
            "complexity_preference": patterns["complexity_range"],
            "peak_usage_hours": random.sample(range(24), 3),
            "preferred_weekdays": random.sample(range(7), 5)
        }
    
    def simulate_user_session(self, user_profile: UserProfile, duration_minutes: int = 30) -> SimulationSession:
        """模拟用户会话"""
        session_id = f"session_{int(time.time() * 1000)}"
        start_time = time.time()
        
        session = SimulationSession(
            session_id=session_id,
            user_profile=user_profile,
            start_time=start_time,
            end_time=None,
            actions=[],
            success_rate=0.0,
            satisfaction_score=0.0
        )
        
        self.logger.info(f"开始模拟用户会话: {session_id}, 用户类型: {user_profile.user_type.value}")
        
        # 模拟用户行为
        end_time = start_time + (duration_minutes * 60)
        current_time = start_time
        
        while current_time < end_time:
            # 生成下一个行为
            action = self._generate_next_action(user_profile, current_time, session)
            if action:
                session.actions.append(action)
                current_time = action.timestamp + action.duration
            
            # 随机间隔
            interval = random.uniform(1, 10)  # 1-10秒间隔
            current_time += interval
        
        session.end_time = current_time
        session.success_rate = self._calculate_session_success_rate(session)
        session.satisfaction_score = self._calculate_satisfaction_score(session)
        
        self.simulation_sessions.append(session)
        self.logger.info(f"用户会话完成: {session_id}, 成功率: {session.success_rate:.2f}, 满意度: {session.satisfaction_score:.2f}")
        
        return session
    
    def _generate_next_action(self, user_profile: UserProfile, current_time: float, session: SimulationSession) -> Optional[UserAction]:
        """生成下一个用户行为"""
        # 根据用户类型和行为模式生成行为
        user_type = user_profile.user_type.value
        patterns = self.behavior_patterns["query_patterns"][user_type]
        
        # 决定行为类型
        action_type = self._select_action_type(user_profile, session)
        
        if action_type == ActionType.QUERY:
            return self._generate_query_action(user_profile, current_time, session)
        elif action_type == ActionType.NAVIGATION:
            return self._generate_navigation_action(user_profile, current_time, session)
        elif action_type == ActionType.CONFIGURATION:
            return self._generate_configuration_action(user_profile, current_time, session)
        elif action_type == ActionType.ERROR_RECOVERY:
            return self._generate_error_recovery_action(user_profile, current_time, session)
        elif action_type == ActionType.FEEDBACK:
            return self._generate_feedback_action(user_profile, current_time, session)
        
        return None
    
    def _select_action_type(self, user_profile: UserProfile, session: SimulationSession) -> ActionType:
        """选择行为类型"""
        # 基于用户类型和历史行为选择行为类型
        user_type = user_profile.user_type.value
        
        # 基础概率分布
        probabilities = {
            ActionType.QUERY: 0.6,
            ActionType.NAVIGATION: 0.2,
            ActionType.CONFIGURATION: 0.1,
            ActionType.ERROR_RECOVERY: 0.05,
            ActionType.FEEDBACK: 0.05
        }
        
        # 根据用户类型调整概率
        if user_type == "beginner":
            probabilities[ActionType.NAVIGATION] += 0.1
            probabilities[ActionType.ERROR_RECOVERY] += 0.05
        elif user_type == "expert":
            probabilities[ActionType.QUERY] += 0.1
            probabilities[ActionType.CONFIGURATION] += 0.05
        
        # 根据会话历史调整概率
        recent_actions = session.actions[-5:] if len(session.actions) >= 5 else session.actions
        if recent_actions:
            error_count = sum(1 for action in recent_actions if not action.success)
            if error_count > 2:
                probabilities[ActionType.ERROR_RECOVERY] += 0.2
        
        # 选择行为类型
        rand = random.random()
        cumulative = 0
        for action_type, prob in probabilities.items():
            cumulative += prob
            if rand <= cumulative:
                return action_type
        
        return ActionType.QUERY
    
    def _generate_query_action(self, user_profile: UserProfile, current_time: float, session: SimulationSession) -> UserAction:
        """生成查询行为"""
        user_type = user_profile.user_type.value
        patterns = self.behavior_patterns["query_patterns"][user_type]
        
        # 选择查询内容
        if random.random() < patterns["query_frequency"]:
            query = random.choice(patterns["common_queries"])
        else:
            query = self._generate_random_query(patterns["complexity_range"])
        
        # 计算行为持续时间
        complexity = self._calculate_query_complexity(query)
        duration = random.uniform(2, 10) + (complexity * 2)
        
        # 模拟成功/失败
        success = self._simulate_action_success(user_profile, complexity)
        
        return UserAction(
            action_id=f"action_{int(current_time * 1000)}",
            user_id=user_profile.user_id,
            action_type=ActionType.QUERY,
            timestamp=current_time,
            duration=duration,
            success=success,
            data={"query": query, "complexity": complexity},
            context={"session_id": session.session_id}
        )
    
    def _generate_navigation_action(self, user_profile: UserProfile, current_time: float, session: SimulationSession) -> UserAction:
        """生成导航行为"""
        user_type = user_profile.user_type.value
        nav_patterns = self.behavior_patterns["navigation_patterns"][user_type]
        
        # 选择导航路径
        path_type = random.choice(nav_patterns["preferred_paths"])
        
        # 计算行为持续时间
        duration = random.uniform(1, 5)
        
        # 模拟成功/失败
        success = random.random() > 0.1  # 导航成功率90%
        
        return UserAction(
            action_id=f"action_{int(current_time * 1000)}",
            user_id=user_profile.user_id,
            action_type=ActionType.NAVIGATION,
            timestamp=current_time,
            duration=duration,
            success=success,
            data={"path_type": path_type, "exploration": random.random() < nav_patterns["exploration_rate"]},
            context={"session_id": session.session_id}
        )
    
    def _generate_configuration_action(self, user_profile: UserProfile, current_time: float, session: SimulationSession) -> UserAction:
        """生成配置行为"""
        # 选择配置项
        config_items = ["theme", "language", "notifications", "privacy", "performance"]
        config_item = random.choice(config_items)
        
        # 计算行为持续时间
        duration = random.uniform(3, 15)
        
        # 模拟成功/失败
        success = random.random() > 0.05  # 配置成功率95%
        
        return UserAction(
            action_id=f"action_{int(current_time * 1000)}",
            user_id=user_profile.user_id,
            action_type=ActionType.CONFIGURATION,
            timestamp=current_time,
            duration=duration,
            success=success,
            data={"config_item": config_item, "value": f"value_{random.randint(1, 100)}"},
            context={"session_id": session.session_id}
        )
    
    def _generate_error_recovery_action(self, user_profile: UserProfile, current_time: float, session: SimulationSession) -> UserAction:
        """生成错误恢复行为"""
        # 选择错误场景
        error_scenario = random.choice(self.error_scenarios)
        
        # 选择恢复行为
        recovery_action = random.choice(error_scenario["recovery_actions"])
        
        # 计算行为持续时间
        duration = random.uniform(5, 30)
        
        # 模拟成功/失败
        success = random.random() < user_profile.error_tolerance
        
        return UserAction(
            action_id=f"action_{int(current_time * 1000)}",
            user_id=user_profile.user_id,
            action_type=ActionType.ERROR_RECOVERY,
            timestamp=current_time,
            duration=duration,
            success=success,
            data={"error_type": error_scenario["type"], "recovery_action": recovery_action},
            context={"session_id": session.session_id}
        )
    
    def _generate_feedback_action(self, user_profile: UserProfile, current_time: float, session: SimulationSession) -> UserAction:
        """生成反馈行为"""
        # 生成反馈内容
        feedback_types = ["positive", "negative", "suggestion", "bug_report"]
        feedback_type = random.choice(feedback_types)
        
        # 计算行为持续时间
        duration = random.uniform(2, 8)
        
        # 模拟成功/失败
        success = random.random() > 0.02  # 反馈成功率98%
        
        return UserAction(
            action_id=f"action_{int(current_time * 1000)}",
            user_id=user_profile.user_id,
            action_type=ActionType.FEEDBACK,
            timestamp=current_time,
            duration=duration,
            success=success,
            data={"feedback_type": feedback_type, "rating": random.randint(1, 5)},
            context={"session_id": session.session_id}
        )
    
    def _generate_random_query(self, complexity_range: Tuple[int, int]) -> str:
        """生成随机查询"""
        complexity = random.randint(complexity_range[0], complexity_range[1])
        
        query_templates = [
            "如何{action}{object}？",
            "系统是否支持{feature}？",
            "如何配置{setting}？",
            "如何优化{aspect}？",
            "如何实现{function}？"
        ]
        
        actions = ["使用", "配置", "优化", "实现", "集成"]
        objects = ["功能", "服务", "接口", "算法", "模块"]
        features = ["高级功能", "自定义配置", "API访问", "性能监控", "错误处理"]
        settings = ["基本设置", "高级设置", "安全设置", "性能设置", "集成设置"]
        aspects = ["性能", "安全性", "可维护性", "扩展性", "稳定性"]
        functions = ["自定义功能", "高级集成", "性能优化", "错误处理", "监控告警"]
        
        template = random.choice(query_templates)
        
        if "{action}" in template:
            template = template.replace("{action}", random.choice(actions))
        if "{object}" in template:
            template = template.replace("{object}", random.choice(objects))
        if "{feature}" in template:
            template = template.replace("{feature}", random.choice(features))
        if "{setting}" in template:
            template = template.replace("{setting}", random.choice(settings))
        if "{aspect}" in template:
            template = template.replace("{aspect}", random.choice(aspects))
        if "{function}" in template:
            template = template.replace("{function}", random.choice(functions))
        
        return template
    
    def _calculate_query_complexity(self, query: str) -> int:
        """计算查询复杂度"""
        complexity_keywords = [
            "如何", "是否", "配置", "优化", "实现", "集成",
            "高级", "自定义", "性能", "安全", "监控", "调试"
        ]
        
        complexity = 1
        for keyword in complexity_keywords:
            if keyword in query:
                complexity += 1
        
        return min(complexity, 10)
    
    def _simulate_action_success(self, user_profile: UserProfile, complexity: int) -> bool:
        """模拟行为成功"""
        # 基于用户经验和复杂度计算成功率
        experience_factor = user_profile.experience_level / 10
        complexity_factor = 1 - (complexity / 10)
        
        success_rate = (experience_factor + complexity_factor) / 2
        success_rate = max(success_rate, 0.1)  # 最低10%成功率
        
        return random.random() < success_rate
    
    def _calculate_session_success_rate(self, session: SimulationSession) -> float:
        """计算会话成功率"""
        if not session.actions:
            return 0.0
        
        successful_actions = sum(1 for action in session.actions if action.success)
        return successful_actions / len(session.actions)
    
    def _calculate_satisfaction_score(self, session: SimulationSession) -> float:
        """计算满意度分数"""
        if not session.actions:
            return 0.0
        
        # 基于成功率和用户耐心计算满意度
        success_rate = session.success_rate
        patience_factor = session.user_profile.patience_level
        
        # 考虑行为持续时间
        avg_duration = sum(action.duration for action in session.actions) / len(session.actions)
        duration_factor = max(0, 1 - (avg_duration / 60))  # 假设60秒为理想持续时间
        
        satisfaction = (success_rate * 0.6 + patience_factor * 0.2 + duration_factor * 0.2)
        return min(satisfaction, 1.0)
    
    def run_batch_simulation(self, num_sessions: int = 100) -> Dict[str, Any]:
        """运行批量模拟"""
        self.logger.info(f"开始批量模拟: {num_sessions} 个会话")
        
        results = {
            "total_sessions": num_sessions,
            "completed_sessions": 0,
            "failed_sessions": 0,
            "overall_success_rate": 0.0,
            "overall_satisfaction": 0.0,
            "user_type_stats": {},
            "error_analysis": {},
            "recommendations": []
        }
        
        for i in range(num_sessions):
            try:
                # 随机选择用户画像
                user_profile = random.choice(self.user_profiles)
                
                # 模拟会话
                session = self.simulate_user_session(user_profile, duration_minutes=random.randint(10, 60))
                
                results["completed_sessions"] += 1
                
                # 更新统计
                user_type = user_profile.user_type.value
                if user_type not in results["user_type_stats"]:
                    results["user_type_stats"][user_type] = {
                        "sessions": 0,
                        "success_rate": 0.0,
                        "satisfaction": 0.0
                    }
                
                stats = results["user_type_stats"][user_type]
                stats["sessions"] += 1
                stats["success_rate"] = (stats["success_rate"] * (stats["sessions"] - 1) + session.success_rate) / stats["sessions"]
                stats["satisfaction"] = (stats["satisfaction"] * (stats["sessions"] - 1) + session.satisfaction_score) / stats["sessions"]
                
            except Exception as e:
                self.logger.error(f"模拟会话失败: {e}")
                results["failed_sessions"] += 1
        
        # 计算总体统计
        if results["completed_sessions"] > 0:
            all_sessions = [s for s in self.simulation_sessions if s.end_time is not None]
            results["overall_success_rate"] = sum(s.success_rate for s in all_sessions) / len(all_sessions)
            results["overall_satisfaction"] = sum(s.satisfaction_score for s in all_sessions) / len(all_sessions)
        
        # 分析错误
        results["error_analysis"] = self._analyze_errors()
        
        # 生成建议
        results["recommendations"] = self._generate_recommendations(results)
        
        self.logger.info(f"批量模拟完成: 成功 {results['completed_sessions']}, 失败 {results['failed_sessions']}")
        
        return results
    
    def _analyze_errors(self) -> Dict[str, Any]:
        """分析错误"""
        error_analysis = {
            "total_errors": 0,
            "error_by_type": {},
            "error_by_user_type": {},
            "common_error_patterns": []
        }
        
        for session in self.simulation_sessions:
            for action in session.actions:
                if not action.success:
                    error_analysis["total_errors"] += 1
                    
                    # 按类型统计
                    action_type = action.action_type.value
                    error_analysis["error_by_type"][action_type] = error_analysis["error_by_type"].get(action_type, 0) + 1
                    
                    # 按用户类型统计
                    user_type = session.user_profile.user_type.value
                    if user_type not in error_analysis["error_by_user_type"]:
                        error_analysis["error_by_user_type"][user_type] = 0
                    error_analysis["error_by_user_type"][user_type] += 1
        
        return error_analysis
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        # 基于成功率生成建议
        if results["overall_success_rate"] < 0.8:
            recommendations.append("系统成功率较低，建议改进错误处理和用户引导")
        
        # 基于满意度生成建议
        if results["overall_satisfaction"] < 0.7:
            recommendations.append("用户满意度较低，建议优化用户体验和界面设计")
        
        # 基于用户类型统计生成建议
        for user_type, stats in results["user_type_stats"].items():
            if stats["success_rate"] < 0.7:
                recommendations.append(f"{user_type}用户成功率较低，建议提供针对性的帮助和指导")
        
        # 基于错误分析生成建议
        error_analysis = results["error_analysis"]
        if error_analysis["total_errors"] > 0:
            most_common_error = max(error_analysis["error_by_type"].items(), key=lambda x: x[1])
            recommendations.append(f"最常见的错误类型是{most_common_error[0]}，建议重点改进相关功能")
        
        return recommendations
    
    def export_simulation_data(self, file_path: str) -> bool:
        """导出模拟数据"""
        try:
            data = {
                "user_profiles": [profile.__dict__ for profile in self.user_profiles],
                "simulation_sessions": [session.__dict__ for session in self.simulation_sessions],
                "behavior_patterns": self.behavior_patterns,
                "error_scenarios": self.error_scenarios
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"模拟数据已导出到: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出模拟数据失败: {e}")
            return False


# 全局实例
user_behavior_simulator = UserBehaviorSimulator()
