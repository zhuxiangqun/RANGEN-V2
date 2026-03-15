"""
用户反馈收集系统

收集、存储和分析用户对技能的反馈，包括评分、评论、问题报告和改进建议。
与质量指标跟踪系统集成，提供反馈驱动的技能质量改进。
"""

import json
import sqlite3
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import statistics
import re
import os


class FeedbackType(Enum):
    """反馈类型"""
    RATING = "rating"  # 评分
    COMMENT = "comment"  # 评论
    ISSUE_REPORT = "issue_report"  # 问题报告
    FEATURE_REQUEST = "feature_request"  # 功能请求
    IMPROVEMENT_SUGGESTION = "improvement_suggestion"  # 改进建议
    USABILITY_FEEDBACK = "usability_feedback"  # 可用性反馈
    BUG_REPORT = "bug_report"  # 缺陷报告


class FeedbackSentiment(Enum):
    """反馈情感"""
    POSITIVE = "positive"  # 正面
    NEUTRAL = "neutral"  # 中性
    NEGATIVE = "negative"  # 负面


class FeedbackPriority(Enum):
    """反馈优先级"""
    LOW = "low"  # 低
    MEDIUM = "medium"  # 中
    HIGH = "high"  # 高
    CRITICAL = "critical"  # 关键


@dataclass
class FeedbackItem:
    """反馈项"""
    feedback_id: str
    skill_id: str
    feedback_type: FeedbackType
    content: str
    rating: Optional[float] = None  # 评分（0-10分）
    sentiment: Optional[FeedbackSentiment] = None
    priority: FeedbackPriority = FeedbackPriority.MEDIUM
    user_id: Optional[str] = None  # 匿名反馈时为空
    session_id: Optional[str] = None
    execution_context: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "feedback_id": self.feedback_id,
            "skill_id": self.skill_id,
            "feedback_type": self.feedback_type.value,
            "content": self.content,
            "rating": self.rating,
            "sentiment": self.sentiment.value if self.sentiment else None,
            "priority": self.priority.value,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "execution_context": self.execution_context,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeedbackItem':
        """从字典创建"""
        return cls(
            feedback_id=data["feedback_id"],
            skill_id=data["skill_id"],
            feedback_type=FeedbackType(data["feedback_type"]),
            content=data["content"],
            rating=data.get("rating"),
            sentiment=FeedbackSentiment(data["sentiment"]) if data.get("sentiment") else None,
            priority=FeedbackPriority(data.get("priority", "medium")),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            execution_context=data.get("execution_context"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"])
        )


@dataclass
class FeedbackAnalysis:
    """反馈分析结果"""
    skill_id: str
    total_feedback: int
    avg_rating: float
    rating_distribution: Dict[int, int]  # 评分分布（0-10分）
    feedback_by_type: Dict[str, int]
    sentiment_distribution: Dict[str, int]
    common_issues: List[Dict[str, Any]]  # 常见问题
    improvement_suggestions: List[Dict[str, Any]]  # 改进建议
    top_tags: List[Dict[str, Any]]  # 热门标签
    summary: str
    recommendations: List[str]
    analyzed_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "skill_id": self.skill_id,
            "total_feedback": self.total_feedback,
            "avg_rating": self.avg_rating,
            "rating_distribution": dict(self.rating_distribution),
            "feedback_by_type": dict(self.feedback_by_type),
            "sentiment_distribution": dict(self.sentiment_distribution),
            "common_issues": self.common_issues,
            "improvement_suggestions": self.improvement_suggestions,
            "top_tags": self.top_tags,
            "summary": self.summary,
            "recommendations": self.recommendations,
            "analyzed_at": self.analyzed_at.isoformat()
        }


class FeedbackCollector:
    """用户反馈收集器
    
    收集、存储和分析用户反馈，提供反馈驱动的技能质量改进。
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """初始化反馈收集器
        
        Args:
            storage_path: 存储路径，如果为None则使用默认路径
        """
        if storage_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            storage_path = os.path.join(script_dir, "feedback_data.db")
        
        self.storage_path = storage_path
        self._init_storage()
    
    def _init_storage(self):
        """初始化存储"""
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        # 创建反馈表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feedback_id TEXT UNIQUE NOT NULL,
                skill_id TEXT NOT NULL,
                feedback_type TEXT NOT NULL,
                content TEXT NOT NULL,
                rating REAL,
                sentiment TEXT,
                priority TEXT NOT NULL DEFAULT 'medium',
                user_id TEXT,
                session_id TEXT,
                execution_context TEXT,
                tags TEXT,
                metadata TEXT,
                created_at DATETIME NOT NULL,
                indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建技能反馈摘要表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skill_feedback_summaries (
                skill_id TEXT PRIMARY KEY,
                total_feedback INTEGER DEFAULT 0,
                avg_rating REAL DEFAULT 0.0,
                rating_distribution TEXT,
                feedback_by_type TEXT,
                sentiment_distribution TEXT,
                last_feedback_at DATETIME,
                last_analysis_at DATETIME,
                summary_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建反馈分析表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id TEXT NOT NULL,
                analysis_type TEXT NOT NULL,
                analysis_data TEXT NOT NULL,
                summary TEXT,
                recommendations TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建常见问题表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS common_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id TEXT NOT NULL,
                issue_type TEXT NOT NULL,
                issue_text TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                first_seen DATETIME,
                last_seen DATETIME,
                status TEXT DEFAULT 'open',
                priority TEXT DEFAULT 'medium',
                tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建改进建议表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS improvement_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id TEXT NOT NULL,
                suggestion_type TEXT NOT NULL,
                suggestion_text TEXT NOT NULL,
                votes INTEGER DEFAULT 1,
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'medium',
                tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_skill ON feedback_items(skill_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback_items(feedback_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_rating ON feedback_items(rating)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_time ON feedback_items(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_issues_skill ON common_issues(skill_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_suggestions_skill ON improvement_suggestions(skill_id)')
        
        conn.commit()
        conn.close()
    
    def _generate_feedback_id(self, skill_id: str, content: str, user_id: Optional[str] = None) -> str:
        """生成反馈ID"""
        # 使用技能ID、内容、用户ID和时间戳生成哈希ID
        base_str = f"{skill_id}:{content}:{user_id or 'anonymous'}:{datetime.now().timestamp()}"
        return hashlib.md5(base_str.encode('utf-8')).hexdigest()[:16]
    
    def submit_feedback(
        self,
        skill_id: str,
        feedback_type: FeedbackType,
        content: str,
        rating: Optional[float] = None,
        sentiment: Optional[FeedbackSentiment] = None,
        priority: FeedbackPriority = FeedbackPriority.MEDIUM,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        execution_context: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """提交反馈
        
        Args:
            skill_id: 技能ID
            feedback_type: 反馈类型
            content: 反馈内容
            rating: 评分（0-10分）
            sentiment: 情感
            priority: 优先级
            user_id: 用户ID
            session_id: 会话ID
            execution_context: 执行上下文
            tags: 标签
            metadata: 元数据
            
        Returns:
            str: 反馈ID
        """
        # 验证评分范围
        if rating is not None:
            rating = max(0.0, min(10.0, rating))
        
        # 生成反馈ID
        feedback_id = self._generate_feedback_id(skill_id, content, user_id)
        
        # 如果未提供情感，自动分析情感
        if sentiment is None:
            sentiment = self._analyze_sentiment(content)
        
        # 如果未提供优先级，根据反馈类型和内容确定
        if priority == FeedbackPriority.MEDIUM:
            priority = self._determine_priority(feedback_type, content, rating, sentiment)
        
        # 创建反馈项
        feedback = FeedbackItem(
            feedback_id=feedback_id,
            skill_id=skill_id,
            feedback_type=feedback_type,
            content=content,
            rating=rating,
            sentiment=sentiment,
            priority=priority,
            user_id=user_id,
            session_id=session_id,
            execution_context=execution_context,
            tags=tags or [],
            metadata=metadata or {},
            created_at=datetime.now()
        )
        
        # 存储反馈
        self._store_feedback(feedback)
        
        # 更新技能反馈摘要
        self._update_skill_summary(skill_id)
        
        # 如果是问题报告或改进建议，提取并存储
        if feedback_type in [FeedbackType.ISSUE_REPORT, FeedbackType.BUG_REPORT]:
            self._extract_and_store_issue(skill_id, content, feedback)
        
        if feedback_type == FeedbackType.IMPROVEMENT_SUGGESTION:
            self._extract_and_store_suggestion(skill_id, content, feedback)
        
        return feedback_id
    
    def _analyze_sentiment(self, content: str) -> FeedbackSentiment:
        """分析情感
        
        简单的情感分析：基于关键词判断正面/负面/中性
        """
        positive_keywords = [
            "好", "很好", "优秀", "完美", "满意", "喜欢", "推荐",
            "excellent", "good", "great", "awesome", "perfect", "love", "recommend"
        ]
        
        negative_keywords = [
            "差", "很差", "糟糕", "问题", "错误", "失败", "不满意",
            "bad", "poor", "terrible", "awful", "error", "fail", "disappointed"
        ]
        
        content_lower = content.lower()
        
        positive_count = sum(1 for keyword in positive_keywords if keyword in content_lower)
        negative_count = sum(1 for keyword in negative_keywords if keyword in content_lower)
        
        if positive_count > negative_count:
            return FeedbackSentiment.POSITIVE
        elif negative_count > positive_count:
            return FeedbackSentiment.NEGATIVE
        else:
            return FeedbackSentiment.NEUTRAL
    
    def _determine_priority(
        self,
        feedback_type: FeedbackType,
        content: str,
        rating: Optional[float],
        sentiment: FeedbackSentiment
    ) -> FeedbackPriority:
        """确定优先级"""
        # 缺陷报告通常优先级较高
        if feedback_type == FeedbackType.BUG_REPORT:
            return FeedbackPriority.HIGH
        
        # 负面情感且评分低的反馈优先级较高
        if sentiment == FeedbackSentiment.NEGATIVE and rating is not None and rating < 3:
            return FeedbackPriority.HIGH
        
        # 问题报告优先级中等
        if feedback_type == FeedbackType.ISSUE_REPORT:
            return FeedbackPriority.MEDIUM
        
        # 功能请求和改进建议优先级较低
        if feedback_type in [FeedbackType.FEATURE_REQUEST, FeedbackType.IMPROVEMENT_SUGGESTION]:
            return FeedbackPriority.LOW
        
        return FeedbackPriority.MEDIUM
    
    def _store_feedback(self, feedback: FeedbackItem):
        """存储反馈"""
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO feedback_items 
            (feedback_id, skill_id, feedback_type, content, rating, sentiment, 
             priority, user_id, session_id, execution_context, tags, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            feedback.feedback_id,
            feedback.skill_id,
            feedback.feedback_type.value,
            feedback.content,
            feedback.rating,
            feedback.sentiment.value if feedback.sentiment else None,
            feedback.priority.value,
            feedback.user_id,
            feedback.session_id,
            json.dumps(feedback.execution_context, ensure_ascii=False) if feedback.execution_context else None,
            json.dumps(feedback.tags, ensure_ascii=False) if feedback.tags else None,
            json.dumps(feedback.metadata, ensure_ascii=False),
            feedback.created_at.isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def _update_skill_summary(self, skill_id: str):
        """更新技能反馈摘要"""
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        # 获取技能的所有反馈
        cursor.execute('''
            SELECT feedback_type, rating, sentiment, created_at 
            FROM feedback_items 
            WHERE skill_id = ? 
            ORDER BY created_at DESC
        ''', (skill_id,))
        
        feedback_rows = cursor.fetchall()
        
        if not feedback_rows:
            return
        
        # 计算统计信息
        total_feedback = len(feedback_rows)
        
        # 评分统计
        ratings = [row[1] for row in feedback_rows if row[1] is not None]
        avg_rating = statistics.mean(ratings) if ratings else 0.0
        
        # 评分分布（0-10分，1分为单位）
        rating_distribution = defaultdict(int)
        for rating in ratings:
            bucket = int(rating)  # 整数分桶
            rating_distribution[bucket] += 1
        
        # 反馈类型分布
        feedback_by_type = defaultdict(int)
        for row in feedback_rows:
            feedback_by_type[row[0]] += 1
        
        # 情感分布
        sentiment_distribution = defaultdict(int)
        for row in feedback_rows:
            sentiment = row[2]
            if sentiment:
                sentiment_distribution[sentiment] += 1
        
        # 最新反馈时间
        last_feedback_at = feedback_rows[0][3] if feedback_rows else datetime.now().isoformat()
        
        # 创建摘要JSON
        summary_json = json.dumps({
            "skill_id": skill_id,
            "total_feedback": total_feedback,
            "avg_rating": avg_rating,
            "rating_distribution": dict(rating_distribution),
            "feedback_by_type": dict(feedback_by_type),
            "sentiment_distribution": dict(sentiment_distribution),
            "last_feedback_at": last_feedback_at,
            "updated_at": datetime.now().isoformat()
        }, ensure_ascii=False)
        
        # 检查是否已有摘要
        cursor.execute('SELECT * FROM skill_feedback_summaries WHERE skill_id = ?', (skill_id,))
        existing = cursor.fetchone()
        
        if existing:
            # 更新现有摘要
            cursor.execute('''
                UPDATE skill_feedback_summaries 
                SET total_feedback = ?, avg_rating = ?, rating_distribution = ?,
                    feedback_by_type = ?, sentiment_distribution = ?, 
                    last_feedback_at = ?, updated_at = ?, summary_json = ?
                WHERE skill_id = ?
            ''', (
                total_feedback,
                avg_rating,
                json.dumps(dict(rating_distribution), ensure_ascii=False),
                json.dumps(dict(feedback_by_type), ensure_ascii=False),
                json.dumps(dict(sentiment_distribution), ensure_ascii=False),
                last_feedback_at,
                datetime.now().isoformat(),
                summary_json,
                skill_id
            ))
        else:
            # 插入新摘要
            cursor.execute('''
                INSERT INTO skill_feedback_summaries 
                (skill_id, total_feedback, avg_rating, rating_distribution,
                 feedback_by_type, sentiment_distribution, last_feedback_at,
                 last_analysis_at, summary_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                skill_id,
                total_feedback,
                avg_rating,
                json.dumps(dict(rating_distribution), ensure_ascii=False),
                json.dumps(dict(feedback_by_type), ensure_ascii=False),
                json.dumps(dict(sentiment_distribution), ensure_ascii=False),
                last_feedback_at,
                datetime.now().isoformat(),
                summary_json,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
    
    def _extract_and_store_issue(self, skill_id: str, content: str, feedback: FeedbackItem):
        """提取并存储问题"""
        # 简单的问题提取：基于关键词提取问题类型
        issue_types = {
            "error": ["错误", "失败", "异常", "崩溃", "bug", "error", "failure", "exception"],
            "performance": ["慢", "卡顿", "延迟", "超时", "slow", "lag", "delay", "timeout"],
            "usability": ["难用", "复杂", "不直观", "confusing", "complex", "hard to use"],
            "feature": ["缺少", "需要", "希望有", "missing", "need", "want", "should have"]
        }
        
        content_lower = content.lower()
        detected_types = []
        
        for issue_type, keywords in issue_types.items():
            if any(keyword in content_lower for keyword in keywords):
                detected_types.append(issue_type)
        
        if not detected_types:
            detected_types = ["other"]
        
        # 存储问题
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        for issue_type in detected_types:
            # 检查是否已存在相似问题
            cursor.execute('''
                SELECT id, frequency FROM common_issues 
                WHERE skill_id = ? AND issue_type = ? 
                ORDER BY last_seen DESC LIMIT 1
            ''', (skill_id, issue_type))
            
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有问题频率
                issue_id, frequency = existing
                cursor.execute('''
                    UPDATE common_issues 
                    SET frequency = ?, last_seen = ?
                    WHERE id = ?
                ''', (frequency + 1, datetime.now().isoformat(), issue_id))
            else:
                # 插入新问题
                cursor.execute('''
                    INSERT INTO common_issues 
                    (skill_id, issue_type, issue_text, frequency, first_seen, last_seen, 
                     status, priority, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    skill_id,
                    issue_type,
                    content[:200],  # 截取前200个字符
                    1,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    "open",
                    feedback.priority.value,
                    json.dumps(feedback.tags, ensure_ascii=False) if feedback.tags else None
                ))
        
        conn.commit()
        conn.close()
    
    def _extract_and_store_suggestion(self, skill_id: str, content: str, feedback: FeedbackItem):
        """提取并存储改进建议"""
        # 简单的建议提取：基于关键词提取建议类型
        suggestion_types = {
            "feature": ["增加", "添加", "支持", "集成", "add", "support", "integrate"],
            "improvement": ["改进", "优化", "增强", "完善", "improve", "optimize", "enhance"],
            "usability": ["简化", "易用", "直观", "simplify", "user friendly", "intuitive"],
            "performance": ["加速", "优化性能", "减少延迟", "speed up", "performance", "reduce latency"]
        }
        
        content_lower = content.lower()
        detected_types = []
        
        for suggestion_type, keywords in suggestion_types.items():
            if any(keyword in content_lower for keyword in keywords):
                detected_types.append(suggestion_type)
        
        if not detected_types:
            detected_types = ["general"]
        
        # 存储建议
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        for suggestion_type in detected_types:
            # 检查是否已存在相似建议
            cursor.execute('''
                SELECT id, votes FROM improvement_suggestions 
                WHERE skill_id = ? AND suggestion_type = ? 
                ORDER BY created_at DESC LIMIT 1
            ''', (skill_id, suggestion_type))
            
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有建议投票数
                suggestion_id, votes = existing
                cursor.execute('''
                    UPDATE improvement_suggestions 
                    SET votes = ?, updated_at = ?
                    WHERE id = ?
                ''', (votes + 1, datetime.now().isoformat(), suggestion_id))
            else:
                # 插入新建议
                cursor.execute('''
                    INSERT INTO improvement_suggestions 
                    (skill_id, suggestion_type, suggestion_text, votes, 
                     status, priority, tags, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    skill_id,
                    suggestion_type,
                    content[:200],  # 截取前200个字符
                    1,
                    "pending",
                    feedback.priority.value,
                    json.dumps(feedback.tags, ensure_ascii=False) if feedback.tags else None,
                    datetime.now().isoformat()
                ))
        
        conn.commit()
        conn.close()
    
    def analyze_feedback(self, skill_id: str) -> FeedbackAnalysis:
        """分析技能反馈
        
        Args:
            skill_id: 技能ID
            
        Returns:
            FeedbackAnalysis: 反馈分析结果
        """
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        # 获取技能的所有反馈
        cursor.execute('''
            SELECT feedback_type, content, rating, sentiment, priority, tags, created_at 
            FROM feedback_items 
            WHERE skill_id = ? 
            ORDER BY created_at DESC
        ''', (skill_id,))
        
        feedback_rows = cursor.fetchall()
        
        if not feedback_rows:
            return self._create_empty_analysis(skill_id)
        
        # 计算统计信息
        total_feedback = len(feedback_rows)
        
        # 评分统计
        ratings = [row[2] for row in feedback_rows if row[2] is not None]
        avg_rating = statistics.mean(ratings) if ratings else 0.0
        
        # 评分分布（0-10分，1分为单位）
        rating_distribution = defaultdict(int)
        for rating in ratings:
            bucket = int(rating)  # 整数分桶
            rating_distribution[bucket] += 1
        
        # 反馈类型分布
        feedback_by_type = defaultdict(int)
        for row in feedback_rows:
            feedback_by_type[row[0]] += 1
        
        # 情感分布
        sentiment_distribution = defaultdict(int)
        for row in feedback_rows:
            sentiment = row[3]
            if sentiment:
                sentiment_distribution[sentiment] += 1
        
        # 提取常见问题
        common_issues = self._extract_common_issues(skill_id)
        
        # 提取改进建议
        improvement_suggestions = self._extract_improvement_suggestions(skill_id)
        
        # 提取热门标签
        top_tags = self._extract_top_tags(feedback_rows)
        
        # 生成总结
        summary = self._generate_analysis_summary(
            total_feedback, avg_rating, sentiment_distribution, 
            common_issues, improvement_suggestions
        )
        
        # 生成建议
        recommendations = self._generate_recommendations(
            avg_rating, sentiment_distribution, common_issues, improvement_suggestions
        )
        
        # 创建分析结果
        analysis = FeedbackAnalysis(
            skill_id=skill_id,
            total_feedback=total_feedback,
            avg_rating=avg_rating,
            rating_distribution=dict(rating_distribution),
            feedback_by_type=dict(feedback_by_type),
            sentiment_distribution=dict(sentiment_distribution),
            common_issues=common_issues,
            improvement_suggestions=improvement_suggestions,
            top_tags=top_tags,
            summary=summary,
            recommendations=recommendations,
            analyzed_at=datetime.now()
        )
        
        # 存储分析结果
        self._store_analysis(analysis)
        
        # 更新技能分析时间
        cursor.execute('''
            UPDATE skill_feedback_summaries 
            SET last_analysis_at = ?
            WHERE skill_id = ?
        ''', (datetime.now().isoformat(), skill_id))
        
        conn.commit()
        conn.close()
        
        return analysis
    
    def _create_empty_analysis(self, skill_id: str) -> FeedbackAnalysis:
        """创建空分析结果"""
        return FeedbackAnalysis(
            skill_id=skill_id,
            total_feedback=0,
            avg_rating=0.0,
            rating_distribution={},
            feedback_by_type={},
            sentiment_distribution={},
            common_issues=[],
            improvement_suggestions=[],
            top_tags=[],
            summary="暂无用户反馈",
            recommendations=["收集更多用户反馈以进行分析"],
            analyzed_at=datetime.now()
        )
    
    def _extract_common_issues(self, skill_id: str) -> List[Dict[str, Any]]:
        """提取常见问题"""
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT issue_type, issue_text, frequency, status, priority, first_seen, last_seen
            FROM common_issues 
            WHERE skill_id = ? 
            ORDER BY frequency DESC, last_seen DESC 
            LIMIT 10
        ''', (skill_id,))
        
        issues = []
        for row in cursor.fetchall():
            issues.append({
                "issue_type": row[0],
                "issue_text": row[1],
                "frequency": row[2],
                "status": row[3],
                "priority": row[4],
                "first_seen": row[5],
                "last_seen": row[6]
            })
        
        conn.close()
        return issues
    
    def _extract_improvement_suggestions(self, skill_id: str) -> List[Dict[str, Any]]:
        """提取改进建议"""
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT suggestion_type, suggestion_text, votes, status, priority, created_at
            FROM improvement_suggestions 
            WHERE skill_id = ? 
            ORDER BY votes DESC, created_at DESC 
            LIMIT 10
        ''', (skill_id,))
        
        suggestions = []
        for row in cursor.fetchall():
            suggestions.append({
                "suggestion_type": row[0],
                "suggestion_text": row[1],
                "votes": row[2],
                "status": row[3],
                "priority": row[4],
                "created_at": row[5]
            })
        
        conn.close()
        return suggestions
    
    def _extract_top_tags(self, feedback_rows: List[Tuple]) -> List[Dict[str, Any]]:
        """提取热门标签"""
        tag_counts = defaultdict(int)
        
        for row in feedback_rows:
            tags_json = row[5]  # 第6列是tags
            if tags_json:
                try:
                    tags = json.loads(tags_json)
                    for tag in tags:
                        tag_counts[tag] += 1
                except:
                    pass
        
        # 按频率排序
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        
        # 转换为字典列表
        top_tags = []
        for tag, count in sorted_tags[:10]:
            top_tags.append({
                "tag": tag,
                "count": count,
                "percentage": count / len(feedback_rows) * 100 if feedback_rows else 0
            })
        
        return top_tags
    
    def _generate_analysis_summary(
        self,
        total_feedback: int,
        avg_rating: float,
        sentiment_distribution: Dict[str, int],
        common_issues: List[Dict[str, Any]],
        improvement_suggestions: List[Dict[str, Any]]
    ) -> str:
        """生成分析总结"""
        if total_feedback == 0:
            return "暂无用户反馈"
        
        summary_parts = []
        
        # 总体反馈情况
        summary_parts.append(f"共收集到 {total_feedback} 条用户反馈")
        
        # 评分情况
        if avg_rating > 0:
            if avg_rating >= 8:
                rating_desc = "优秀"
            elif avg_rating >= 6:
                rating_desc = "良好"
            elif avg_rating >= 4:
                rating_desc = "一般"
            else:
                rating_desc = "较差"
            summary_parts.append(f"平均评分 {avg_rating:.1f}/10.0 ({rating_desc})")
        
        # 情感分布
        total_sentiment = sum(sentiment_distribution.values())
        if total_sentiment > 0:
            positive_rate = sentiment_distribution.get("positive", 0) / total_sentiment * 100
            negative_rate = sentiment_distribution.get("negative", 0) / total_sentiment * 100
            
            if positive_rate > 60:
                sentiment_desc = "非常积极"
            elif positive_rate > 40:
                sentiment_desc = "比较积极"
            elif negative_rate > 40:
                sentiment_desc = "比较消极"
            elif negative_rate > 20:
                sentiment_desc = "有所不满"
            else:
                sentiment_desc = "基本中性"
            
            summary_parts.append(f"用户情感 {sentiment_desc} (正面{positive_rate:.0f}%/负面{negative_rate:.0f}%)")
        
        # 问题情况
        if common_issues:
            open_issues = [issue for issue in common_issues if issue.get("status") == "open"]
            if open_issues:
                high_priority_issues = [issue for issue in open_issues if issue.get("priority") in ["high", "critical"]]
                if high_priority_issues:
                    summary_parts.append(f"存在 {len(high_priority_issues)} 个高优先级待解决问题")
        
        # 建议情况
        if improvement_suggestions:
            pending_suggestions = [suggestion for suggestion in improvement_suggestions if suggestion.get("status") == "pending"]
            if pending_suggestions:
                summary_parts.append(f"有 {len(pending_suggestions)} 个待处理改进建议")
        
        # 返回连接后的摘要
        if not summary_parts:
            return "暂无分析结果"
        
        return "。".join(summary_parts) + "。"
