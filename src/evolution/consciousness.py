#!/usr/bin/env python3
"""
后台意识循环
实现系统的持续学习、知识提取和背景思考能力
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum


class ConsciousnessState(Enum):
    """意识状态"""
    IDLE = "idle"          # 空闲
    THINKING = "thinking"  # 思考中
    LEARNING = "learning"  # 学习中
    ANALYZING = "analyzing"  # 分析中
    INTEGRATING = "integrating"  # 知识整合中


class LearningDomain(Enum):
    """学习领域"""
    JAPAN_MARKET = "japan_market"          # 日本市场知识
    BUSINESS_STRATEGY = "business_strategy"  # 商业策略
    TECHNICAL_PATTERNS = "technical_patterns"  # 技术模式
    USER_INTERACTION = "user_interaction"  # 用户交互
    SYSTEM_OPTIMIZATION = "system_optimization"  # 系统优化


@dataclass
class Thought:
    """思考记录"""
    thought_id: str
    topic: str
    content: str
    domain: LearningDomain
    insights: List[str] = field(default_factory=list)
    connections: List[str] = field(default_factory=list)  # 关联的其他思考
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_seconds: float = 0.0


@dataclass
class KnowledgePattern:
    """知识模式"""
    pattern_id: str
    name: str
    description: str
    domain: LearningDomain
    examples: List[str] = field(default_factory=list)
    success_rate: float = 0.0  # 0.0-1.0
    applications: List[str] = field(default_factory=list)
    learned_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_applied: Optional[str] = None
    application_count: int = 0


@dataclass
class Reflection:
    """反思记录"""
    reflection_id: str
    task_id: str
    task_description: str
    outcome: str  # success, partial_success, failure
    analysis: str
    lessons_learned: List[str]
    improvements_suggested: List[str]
    patterns_extracted: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class BackgroundConsciousness:
    """后台意识循环"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 意识状态
        self.state: ConsciousnessState = ConsciousnessState.IDLE
        self.current_thought: Optional[Thought] = None
        
        # 知识和记忆
        self.thoughts: List[Thought] = []
        self.patterns: Dict[str, KnowledgePattern] = {}
        self.reflections: List[Reflection] = []
        
        # 学习领域配置
        self.learning_domains = {
            LearningDomain.JAPAN_MARKET: {
                "priority": "high",
                "learning_sources": ["market_analysis", "customer_feedback", "industry_reports"],
                "update_frequency_hours": 24
            },
            LearningDomain.BUSINESS_STRATEGY: {
                "priority": "high",
                "learning_sources": ["entrepreneur_decisions", "project_outcomes", "business_metrics"],
                "update_frequency_hours": 48
            },
            LearningDomain.TECHNICAL_PATTERNS: {
                "priority": "medium",
                "learning_sources": ["code_changes", "performance_data", "bug_reports"],
                "update_frequency_hours": 72
            },
            LearningDomain.USER_INTERACTION: {
                "priority": "medium",
                "learning_sources": ["conversations", "feedback", "usage_patterns"],
                "update_frequency_hours": 24
            },
            LearningDomain.SYSTEM_OPTIMIZATION: {
                "priority": "low",
                "learning_sources": ["performance_metrics", "resource_usage", "evolution_results"],
                "update_frequency_hours": 168  # 每周
            }
        }
        
        # 思考循环配置
        self.thinking_interval_seconds = 300  # 5分钟
        self.deep_thinking_interval_hours = 6  # 深度思考间隔
        self.max_thoughts = 1000
        self.max_patterns = 200
        
        # 记忆文件路径
        self.memory_dir = Path(__file__).parent.parent.parent / "evolution_memory"
        self.memory_dir.mkdir(exist_ok=True)
        
        # 加载现有记忆
        self._load_memories()
        
        self.logger.info(f"后台意识初始化完成，已加载{len(self.thoughts)}个思考，{len(self.patterns)}个模式")
    
    def _load_memories(self):
        """加载记忆"""
        # 加载思考
        thoughts_file = self.memory_dir / "thoughts.json"
        if thoughts_file.exists():
            try:
                with open(thoughts_file, 'r', encoding='utf-8') as f:
                    thoughts_data = json.load(f)
                
                for thought_data in thoughts_data:
                    try:
                        thought = Thought(
                            thought_id=thought_data["thought_id"],
                            topic=thought_data["topic"],
                            content=thought_data["content"],
                            domain=LearningDomain(thought_data["domain"]),
                            insights=thought_data.get("insights", []),
                            connections=thought_data.get("connections", []),
                            timestamp=thought_data["timestamp"],
                            duration_seconds=thought_data.get("duration_seconds", 0.0)
                        )
                        self.thoughts.append(thought)
                    except Exception as e:
                        self.logger.warning(f"加载思考失败: {e}")
                
                self.logger.info(f"已加载{len(self.thoughts)}个思考")
            except Exception as e:
                self.logger.error(f"加载思考文件失败: {e}")
        
        # 加载知识模式
        patterns_file = self.memory_dir / "patterns.json"
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    patterns_data = json.load(f)
                
                for pattern_id, pattern_data in patterns_data.items():
                    try:
                        pattern = KnowledgePattern(
                            pattern_id=pattern_id,
                            name=pattern_data["name"],
                            description=pattern_data["description"],
                            domain=LearningDomain(pattern_data["domain"]),
                            examples=pattern_data.get("examples", []),
                            success_rate=pattern_data.get("success_rate", 0.0),
                            applications=pattern_data.get("applications", []),
                            learned_at=pattern_data.get("learned_at", datetime.now().isoformat()),
                            last_applied=pattern_data.get("last_applied"),
                            application_count=pattern_data.get("application_count", 0)
                        )
                        self.patterns[pattern_id] = pattern
                    except Exception as e:
                        self.logger.warning(f"加载模式失败: {e}")
                
                self.logger.info(f"已加载{len(self.patterns)}个知识模式")
            except Exception as e:
                self.logger.error(f"加载模式文件失败: {e}")
        
        # 加载反思
        reflections_file = self.memory_dir / "reflections.json"
        if reflections_file.exists():
            try:
                with open(reflections_file, 'r', encoding='utf-8') as f:
                    reflections_data = json.load(f)
                
                for reflection_data in reflections_data:
                    try:
                        reflection = Reflection(
                            reflection_id=reflection_data["reflection_id"],
                            task_id=reflection_data["task_id"],
                            task_description=reflection_data["task_description"],
                            outcome=reflection_data["outcome"],
                            analysis=reflection_data["analysis"],
                            lessons_learned=reflection_data["lessons_learned"],
                            improvements_suggested=reflection_data["improvements_suggested"],
                            patterns_extracted=reflection_data.get("patterns_extracted", []),
                            timestamp=reflection_data["timestamp"]
                        )
                        self.reflections.append(reflection)
                    except Exception as e:
                        self.logger.warning(f"加载反思失败: {e}")
                
                self.logger.info(f"已加载{len(self.reflections)}个反思")
            except Exception as e:
                self.logger.error(f"加载反思文件失败: {e}")
    
    def _save_memories(self):
        """保存记忆"""
        # 保存思考
        thoughts_file = self.memory_dir / "thoughts.json"
        thoughts_data = [
            {
                "thought_id": t.thought_id,
                "topic": t.topic,
                "content": t.content,
                "domain": t.domain.value,
                "insights": t.insights,
                "connections": t.connections,
                "timestamp": t.timestamp,
                "duration_seconds": t.duration_seconds
            }
            for t in self.thoughts[-self.max_thoughts:]  # 只保存最近的
        ]
        
        try:
            with open(thoughts_file, 'w', encoding='utf-8') as f:
                json.dump(thoughts_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存思考失败: {e}")
        
        # 保存知识模式
        patterns_file = self.memory_dir / "patterns.json"
        patterns_data = {}
        for pattern_id, pattern in list(self.patterns.items())[-self.max_patterns:]:  # 只保存最近的
            patterns_data[pattern_id] = {
                "name": pattern.name,
                "description": pattern.description,
                "domain": pattern.domain.value,
                "examples": pattern.examples,
                "success_rate": pattern.success_rate,
                "applications": pattern.applications,
                "learned_at": pattern.learned_at,
                "last_applied": pattern.last_applied,
                "application_count": pattern.application_count
            }
        
        try:
            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump(patterns_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存模式失败: {e}")
        
        # 保存反思
        reflections_file = self.memory_dir / "reflections.json"
        reflections_data = [
            {
                "reflection_id": r.reflection_id,
                "task_id": r.task_id,
                "task_description": r.task_description,
                "outcome": r.outcome,
                "analysis": r.analysis,
                "lessons_learned": r.lessons_learned,
                "improvements_suggested": r.improvements_suggested,
                "patterns_extracted": r.patterns_extracted,
                "timestamp": r.timestamp
            }
            for r in self.reflections[-100:]  # 只保存最近的100个
        ]
        
        try:
            with open(reflections_file, 'w', encoding='utf-8') as f:
                json.dump(reflections_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存反思失败: {e}")
        
        self.logger.debug(f"记忆已保存: {len(thoughts_data)}思考, {len(patterns_data)}模式, {len(reflections_data)}反思")
    
    async def start_consciousness_loop(self):
        """启动意识循环"""
        self.logger.info("🧠 启动后台意识循环")
        
        while True:
            try:
                await self.background_cycle()
                await asyncio.sleep(self.thinking_interval_seconds)
            except Exception as e:
                self.logger.error(f"意识循环错误: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟
    
    async def background_cycle(self):
        """执行一个后台意识周期"""
        previous_state = self.state
        self.state = ConsciousnessState.THINKING
        
        try:
            # 决定当前周期的活动
            activity = await self._select_consciousness_activity()
            
            if activity == "light_thinking":
                await self._light_thinking_cycle()
            elif activity == "deep_learning":
                await self._deep_learning_cycle()
            elif activity == "pattern_extraction":
                await self._pattern_extraction_cycle()
            elif activity == "knowledge_integration":
                await self._knowledge_integration_cycle()
            elif activity == "system_reflection":
                await self._system_reflection_cycle()
            else:
                await self._idle_thinking()
            
            # 定期保存记忆
            if len(self.thoughts) % 10 == 0:  # 每10个思考保存一次
                self._save_memories()
                
        except Exception as e:
            self.logger.error(f"意识周期执行失败: {e}")
            self.state = ConsciousnessState.IDLE
        finally:
            self.state = ConsciousnessState.IDLE
    
    async def _select_consciousness_activity(self) -> str:
        """选择意识活动"""
        # 基于时间、状态和优先级选择活动
        current_hour = datetime.now().hour
        
        # 深夜进行深度学习
        if 1 <= current_hour <= 4:
            return "deep_learning"
        
        # 清晨进行知识整合
        elif 5 <= current_hour <= 7:
            return "knowledge_integration"
        
        # 工作时间进行轻度思考
        elif 8 <= current_hour <= 18:
            # 检查是否有需要提取的模式
            if len(self.reflections) > 5 and len(self.reflections) % 3 == 0:
                return "pattern_extraction"
            else:
                return "light_thinking"
        
        # 晚上进行系统反思
        elif 19 <= current_hour <= 22:
            return "system_reflection"
        
        else:
            return "light_thinking"
    
    async def _light_thinking_cycle(self):
        """轻度思考周期"""
        self.logger.debug("💭 轻度思考周期开始")
        start_time = time.time()
        
        # 选择思考主题
        topics = [
            "日本市场的最新趋势",
            "创业者决策模式的优化",
            "系统性能的潜在改进点",
            "用户交互体验的优化",
            "技术债务的管理策略"
        ]
        
        selected_topic = topics[len(self.thoughts) % len(topics)]
        
        # 生成思考
        thought = await self._generate_thought(selected_topic, LearningDomain.SYSTEM_OPTIMIZATION)
        
        # 记录思考
        thought.duration_seconds = time.time() - start_time
        self.thoughts.append(thought)
        
        # 限制思考数量
        if len(self.thoughts) > self.max_thoughts:
            self.thoughts.pop(0)
        
        self.logger.debug(f"轻度思考完成: {thought.topic} (时长: {thought.duration_seconds:.1f}秒)")
    
    async def _deep_learning_cycle(self):
        """深度学习周期"""
        self.logger.debug("🎓 深度学习周期开始")
        self.state = ConsciousnessState.LEARNING
        start_time = time.time()
        
        # 选择学习领域（基于优先级）
        high_priority_domains = [
            domain for domain, config in self.learning_domains.items()
            if config["priority"] == "high"
        ]
        
        if high_priority_domains:
            selected_domain = high_priority_domains[len(self.thoughts) % len(high_priority_domains)]
            
            # 执行领域学习
            if selected_domain == LearningDomain.JAPAN_MARKET:
                await self._learn_japan_market()
            elif selected_domain == LearningDomain.BUSINESS_STRATEGY:
                await self._learn_business_strategy()
            elif selected_domain == LearningDomain.TECHNICAL_PATTERNS:
                await self._learn_technical_patterns()
        
        self.logger.debug(f"深度学习完成 (时长: {time.time() - start_time:.1f}秒)")
    
    async def _pattern_extraction_cycle(self):
        """模式提取周期"""
        self.logger.debug("🔍 模式提取周期开始")
        self.state = ConsciousnessState.ANALYZING
        start_time = time.time()
        
        # 分析最近的反思以提取模式
        recent_reflections = self.reflections[-10:] if len(self.reflections) >= 10 else self.reflections
        
        if recent_reflections:
            # 按结果分组
            successful_reflections = [r for r in recent_reflections if r.outcome == "success"]
            failed_reflections = [r for r in recent_reflections if r.outcome == "failure"]
            
            # 提取成功模式
            if successful_reflections:
                patterns = await self._extract_success_patterns(successful_reflections)
                for pattern in patterns:
                    if pattern.pattern_id not in self.patterns:
                        self.patterns[pattern.pattern_id] = pattern
                        self.logger.info(f"提取成功模式: {pattern.name}")
            
            # 提取失败教训
            if failed_reflections:
                lessons = await self._extract_failure_lessons(failed_reflections)
                for lesson in lessons:
                    # 将教训转化为思考
                    thought = Thought(
                        thought_id=f"lesson_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        topic="失败教训总结",
                        content=lesson,
                        domain=LearningDomain.SYSTEM_OPTIMIZATION,
                        insights=["从失败中学习", "避免重复错误"]
                    )
                    self.thoughts.append(thought)
        
        self.logger.debug(f"模式提取完成 (时长: {time.time() - start_time:.1f}秒)")
    
    async def _knowledge_integration_cycle(self):
        """知识整合周期"""
        self.logger.debug("🧩 知识整合周期开始")
        self.state = ConsciousnessState.INTEGRATING
        start_time = time.time()
        
        # 整合相关领域的知识
        integration_topics = [
            ("日本市场策略与技术实现", [LearningDomain.JAPAN_MARKET, LearningDomain.TECHNICAL_PATTERNS]),
            ("商业决策与用户反馈", [LearningDomain.BUSINESS_STRATEGY, LearningDomain.USER_INTERACTION]),
            ("系统优化与创业者价值", [LearningDomain.SYSTEM_OPTIMIZATION, LearningDomain.BUSINESS_STRATEGY])
        ]
        
        for topic, domains in integration_topics:
            integrated_knowledge = await self._integrate_knowledge_domains(topic, domains)
            if integrated_knowledge:
                thought = Thought(
                    thought_id=f"integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    topic=f"知识整合: {topic}",
                    content=integrated_knowledge,
                    domain=LearningDomain.SYSTEM_OPTIMIZATION,
                    insights=["跨领域知识整合", "系统性思维"]
                )
                self.thoughts.append(thought)
        
        self.logger.debug(f"知识整合完成 (时长: {time.time() - start_time:.1f}秒)")
    
    async def _system_reflection_cycle(self):
        """系统反思周期"""
        self.logger.debug("🤔 系统反思周期开始")
        start_time = time.time()
        
        # 反思近期系统表现
        reflection = await self._reflect_on_system_performance()
        if reflection:
            self.reflections.append(reflection)
            self.logger.info(f"系统反思完成: {reflection.task_description}")
        
        self.logger.debug(f"系统反思完成 (时长: {time.time() - start_time:.1f}秒)")
    
    async def _idle_thinking(self):
        """空闲思考"""
        self.logger.debug("😴 空闲思考")
        # 简单的随机思考或休息
        await asyncio.sleep(1)
    
    async def _generate_thought(self, topic: str, domain: LearningDomain) -> Thought:
        """生成思考"""
        thought_id = f"thought_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 模拟思考内容生成
        # 在实际系统中，这里会使用LLM生成更深入的内容
        
        thought_templates = {
            LearningDomain.JAPAN_MARKET: [
                f"关于{topic}的思考：日本市场具有独特的文化特征，需要深入了解本地用户的偏好和习惯。",
                f"分析{topic}：日本企业的决策流程通常较为谨慎，需要建立长期信任关系。",
                f"针对{topic}的见解：日本市场对品质和服务的要求极高，需要持续优化用户体验。"
            ],
            LearningDomain.BUSINESS_STRATEGY: [
                f"关于{topic}的思考：创业者决策需要考虑短期收益和长期价值的平衡。",
                f"分析{topic}：有效的商业策略需要基于数据驱动和快速迭代。",
                f"针对{topic}的见解：创业成功的关键在于持续学习和适应市场变化。"
            ],
            LearningDomain.TECHNICAL_PATTERNS: [
                f"关于{topic}的思考：代码质量直接影响系统可维护性和扩展性。",
                f"分析{topic}：良好的技术架构应该支持渐进式改进和模块化设计。",
                f"针对{topic}的见解：自动化测试和持续集成是确保系统稳定的关键。"
            ],
            LearningDomain.USER_INTERACTION: [
                f"关于{topic}的思考：用户体验的核心是减少认知负荷和提供明确的价值。",
                f"分析{topic}：有效的沟通需要理解用户的背景知识和期望。",
                f"针对{topic}的见解：用户反馈是优化系统的重要输入，需要系统性地收集和分析。"
            ],
            LearningDomain.SYSTEM_OPTIMIZATION: [
                f"关于{topic}的思考：系统优化应该基于性能数据和用户价值的平衡。",
                f"分析{topic}：自进化系统需要安全护栏和透明性机制。",
                f"针对{topic}的见解：持续的小步迭代比大规模重构更安全有效。"
            ]
        }
        
        template = thought_templates.get(domain, thought_templates[LearningDomain.SYSTEM_OPTIMIZATION])
        content = template[len(self.thoughts) % len(template)]
        
        # 生成洞察
        insights = [
            "需要进一步验证的假设",
            "可能的改进方向",
            "值得深入研究的领域"
        ]
        
        return Thought(
            thought_id=thought_id,
            topic=topic,
            content=content,
            domain=domain,
            insights=insights[:2],  # 取前2个洞察
            connections=[]
        )
    
    async def _learn_japan_market(self):
        """学习日本市场知识"""
        # 模拟日本市场学习
        # 在实际系统中，这里会分析市场数据、用户反馈等
        
        learning_topics = [
            "日本中小企业数字化转型趋势",
            "日本市场SaaS产品的定价策略",
            "日本企业的采购决策流程",
            "日本用户对AI工具的接受程度",
            "日本市场的竞争格局分析"
        ]
        
        topic = learning_topics[len(self.thoughts) % len(learning_topics)]
        
        thought = await self._generate_thought(topic, LearningDomain.JAPAN_MARKET)
        self.thoughts.append(thought)
        
        self.logger.info(f"日本市场学习: {topic}")
    
    async def _learn_business_strategy(self):
        """学习商业策略"""
        # 模拟商业策略学习
        # 在实际系统中，这里会分析创业者决策、项目结果等
        
        learning_topics = [
            "创业者风险评估模式",
            "资源分配优化策略",
            "市场进入时机选择",
            "客户获取成本优化",
            "商业模式迭代方法"
        ]
        
        topic = learning_topics[len(self.thoughts) % len(learning_topics)]
        
        thought = await self._generate_thought(topic, LearningDomain.BUSINESS_STRATEGY)
        self.thoughts.append(thought)
        
        self.logger.info(f"商业策略学习: {topic}")
    
    async def _learn_technical_patterns(self):
        """学习技术模式"""
        # 模拟技术模式学习
        # 在实际系统中，这里会分析代码变更、性能数据等
        
        learning_topics = [
            "高效的市场分析算法模式",
            "可扩展的系统架构设计",
            "错误处理和恢复机制",
            "性能优化技术模式",
            "代码重构的最佳实践"
        ]
        
        topic = learning_topics[len(self.thoughts) % len(learning_topics)]
        
        thought = await self._generate_thought(topic, LearningDomain.TECHNICAL_PATTERNS)
        self.thoughts.append(thought)
        
        self.logger.info(f"技术模式学习: {topic}")
    
    async def _extract_success_patterns(self, reflections: List[Reflection]) -> List[KnowledgePattern]:
        """从成功反思中提取模式"""
        patterns = []
        
        for reflection in reflections:
            # 分析反思内容，提取模式
            pattern_id = f"pattern_{reflection.task_id}_{datetime.now().strftime('%H%M%S')}"
            
            # 从反思中提取关键信息
            key_phrases = []
            for lesson in reflection.lessons_learned:
                if "成功" in lesson or "有效" in lesson or "良好" in lesson:
                    key_phrases.append(lesson)
            
            if key_phrases:
                pattern = KnowledgePattern(
                    pattern_id=pattern_id,
                    name=f"成功模式: {reflection.task_description[:30]}...",
                    description="从成功任务中提取的有效模式",
                    domain=LearningDomain.SYSTEM_OPTIMIZATION,
                    examples=key_phrases[:3],  # 取前3个例子
                    success_rate=0.8,  # 假设成功率为80%
                    applications=[reflection.task_description],
                    learned_at=datetime.now().isoformat(),
                    application_count=1
                )
                patterns.append(pattern)
        
        return patterns
    
    async def _extract_failure_lessons(self, reflections: List[Reflection]) -> List[str]:
        """从失败反思中提取教训"""
        lessons = []
        
        for reflection in reflections:
            # 分析失败原因
            failure_analysis = reflection.analysis
            improvements = reflection.improvements_suggested
            
            # 提取核心教训
            if "失败" in failure_analysis or "错误" in failure_analysis:
                core_lesson = f"失败任务 '{reflection.task_description}' 的教训: {failure_analysis}"
                if improvements:
                    core_lesson += f"。改进建议: {'; '.join(improvements[:2])}"
                lessons.append(core_lesson)
            
            # 从反思中提取具体教训
            for lesson in reflection.lessons_learned:
                if "避免" in lesson or "改进" in lesson or "注意" in lesson:
                    lessons.append(f"具体教训: {lesson}")
        
        # 去重并返回
        unique_lessons = []
        seen = set()
        for lesson in lessons:
            if lesson not in seen:
                seen.add(lesson)
                unique_lessons.append(lesson)
        
        return unique_lessons[:5]  # 返回最多5个关键教训
    
    async def _integrate_knowledge_domains(self, topic: str, domains: List[LearningDomain]) -> Optional[str]:
        """整合多个知识领域的知识"""
        if not domains:
            return None
        
        # 收集相关领域的思考
        relevant_thoughts = []
        for thought in self.thoughts[-50:]:  # 检查最近的50个思考
            if thought.domain in domains:
                relevant_thoughts.append(thought)
        
        if not relevant_thoughts:
            return None
        
        # 按领域分组
        domain_thoughts = {domain: [] for domain in domains}
        for thought in relevant_thoughts:
            if thought.domain in domain_thoughts:
                domain_thoughts[thought.domain].append(thought)
        
        # 生成整合知识
        integration_parts = []
        integration_parts.append(f"主题: {topic}")
        integration_parts.append("")
        
        for domain, thoughts in domain_thoughts.items():
            if thoughts:
                integration_parts.append(f"{domain.value} 相关思考:")
                for thought in thoughts[:3]:  # 每个领域最多3个思考
                    integration_parts.append(f"  - {thought.content[:100]}...")
                integration_parts.append("")
        
        # 添加跨领域洞察
        integration_parts.append("跨领域洞察:")
        if len(domains) >= 2:
            domain_names = [d.value for d in domains]
            integration_parts.append(f"  - {domain_names[0]} 和 {domain_names[1]} 的结合可以创造协同效应")
            integration_parts.append(f"  - 需要平衡不同领域的优先级和资源分配")
            integration_parts.append(f"  - 系统化思维有助于整合分散的知识")
        
        return "\n".join(integration_parts)
    
    async def _reflect_on_system_performance(self) -> Optional[Reflection]:
        """反思系统整体表现"""
        # 分析近期思考、模式和反思
        recent_thoughts = self.thoughts[-20:] if len(self.thoughts) >= 20 else self.thoughts
        recent_reflections = self.reflections[-10:] if len(self.reflections) >= 10 else self.reflections
        
        if not recent_thoughts and not recent_reflections:
            return None
        
        # 评估系统表现
        total_tasks = len(recent_reflections)
        successful_tasks = sum(1 for r in recent_reflections if r.outcome == "success")
        success_rate = successful_tasks / total_tasks if total_tasks > 0 else 0.0
        
        # 识别学习趋势
        learning_topics = set()
        for thought in recent_thoughts:
            learning_topics.add(thought.domain.value)
        
        # 生成反思
        reflection_id = f"system_reflection_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        outcome = "success" if success_rate >= 0.7 else "partial_success" if success_rate >= 0.4 else "failure"
        
        analysis_parts = []
        analysis_parts.append(f"系统性能分析 (基于最近{total_tasks}个任务):")
        analysis_parts.append(f"  - 任务成功率: {success_rate:.1%}")
        analysis_parts.append(f"  - 学习领域: {', '.join(sorted(learning_topics))}")
        analysis_parts.append(f"  - 知识模式数量: {len(self.patterns)}")
        analysis_parts.append(f"  - 思考数量: {len(self.thoughts)}")
        
        lessons = []
        if success_rate >= 0.8:
            lessons.append("系统表现良好，继续保持当前学习节奏")
        elif success_rate >= 0.6:
            lessons.append("系统表现尚可，建议优化学习策略")
        else:
            lessons.append("系统表现有待改进，需要调整学习方法")
        
        improvements = []
        if len(learning_topics) < 3:
            improvements.append("扩展学习领域，增加多样性")
        if len(self.patterns) < 10:
            improvements.append("加强模式提取，从成功案例中学习更多")
        if len(recent_thoughts) < 10:
            improvements.append("增加思考频率，深化知识理解")
        
        return Reflection(
            reflection_id=reflection_id,
            task_id="system_performance_review",
            task_description="系统整体性能反思",
            outcome=outcome,
            analysis="\n".join(analysis_parts),
            lessons_learned=lessons,
            improvements_suggested=improvements,
            patterns_extracted=["系统性能评估模式", "学习效率分析模式"]
        )