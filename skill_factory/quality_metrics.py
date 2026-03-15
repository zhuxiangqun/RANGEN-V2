"""
质量指标跟踪系统

跟踪技能质量检查历史记录、AI验证得分趋势、性能指标和用户反馈
"""

import os
import json
import sqlite3
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import statistics

from .quality_checks.checker import QualityReport, CheckStatus
from .ai_validation import AIVerificationReport, ValidationStatus


class MetricType(Enum):
    """指标类型"""
    QUALITY_CHECK = "quality_check"
    AI_VALIDATION = "ai_validation"
    PERFORMANCE = "performance"
    USER_FEEDBACK = "user_feedback"


@dataclass
class QualityMetric:
    """质量指标数据点"""
    skill_id: str
    metric_type: MetricType
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "skill_id": self.skill_id,
            "metric_type": self.metric_type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QualityMetric':
        """从字典创建"""
        return cls(
            skill_id=data["skill_id"],
            metric_type=MetricType(data["metric_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            data=data["data"]
        )


class QualityMetricsTracker:
    """质量指标跟踪器
    
    跟踪技能的质量检查历史记录、AI验证得分趋势、性能指标和用户反馈
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """初始化跟踪器
        
        Args:
            storage_path: 存储路径，如果为None则使用默认路径
        """
        if storage_path is None:
            # 默认存储路径
            script_dir = os.path.dirname(os.path.abspath(__file__))
            storage_path = os.path.join(script_dir, "quality_metrics.db")
        
        self.storage_path = storage_path
        self._init_storage()
    
    def _init_storage(self):
        """初始化存储"""
        # 使用SQLite数据库存储指标
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        # 创建指标表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quality_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                data TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建技能摘要表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skill_summaries (
                skill_id TEXT PRIMARY KEY,
                first_seen DATETIME,
                last_updated DATETIME,
                total_checks INTEGER DEFAULT 0,
                passed_checks INTEGER DEFAULT 0,
                avg_ai_score REAL DEFAULT 0.0,
                total_feedback INTEGER DEFAULT 0,
                avg_rating REAL DEFAULT 0.0,
                performance_data TEXT,
                summary_json TEXT
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_skill_id ON quality_metrics(skill_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON quality_metrics(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metric_type ON quality_metrics(metric_type)')
        
        conn.commit()
        conn.close()
    
    def track_quality_check(self, skill_id: str, quality_report: QualityReport):
        """跟踪质量检查结果"""
        metric = QualityMetric(
            skill_id=skill_id,
            metric_type=MetricType.QUALITY_CHECK,
            timestamp=datetime.now(),
            data={
                "overall_status": quality_report.overall_status.value,
                "checks_count": len(quality_report.checks),
                "passed_checks": sum(1 for check in quality_report.checks if check.status == CheckStatus.PASSED),
                "failed_checks": sum(1 for check in quality_report.checks if check.status == CheckStatus.FAILED),
                "summary": quality_report.summary,
                "recommendations": quality_report.recommendations
            }
        )
        
        self._store_metric(metric)
        self._update_skill_summary(skill_id)
    
    def track_ai_validation(self, skill_id: str, ai_report: AIVerificationReport):
        """跟踪AI验证结果"""
        metric = QualityMetric(
            skill_id=skill_id,
            metric_type=MetricType.AI_VALIDATION,
            timestamp=datetime.now(),
            data={
                "overall_score": ai_report.overall_score,
                "validation_count": len(ai_report.validation_results),
                "passed_validations": sum(1 for result in ai_report.validation_results 
                                        if result.status in [ValidationStatus.PASSED, ValidationStatus.WARNING]),
                "summary": ai_report.summary,
                "recommendations": ai_report.recommendations,
                "category_scores": {
                    result.category.value: result.score
                    for result in ai_report.validation_results
                }
            }
        )
        
        self._store_metric(metric)
        self._update_skill_summary(skill_id)
    
    def track_performance(self, skill_id: str, performance_data: Dict[str, Any]):
        """跟踪性能指标"""
        metric = QualityMetric(
            skill_id=skill_id,
            metric_type=MetricType.PERFORMANCE,
            timestamp=datetime.now(),
            data={
                **performance_data,
                "tracked_at": datetime.now().isoformat()
            }
        )
        
        self._store_metric(metric)
        self._update_skill_summary(skill_id)
    
    def track_user_feedback(self, skill_id: str, rating: float, comment: Optional[str] = None):
        """跟踪用户反馈"""
        metric = QualityMetric(
            skill_id=skill_id,
            metric_type=MetricType.USER_FEEDBACK,
            timestamp=datetime.now(),
            data={
                "rating": rating,
                "comment": comment,
                "feedback_at": datetime.now().isoformat()
            }
        )
        
        self._store_metric(metric)
        self._update_skill_summary(skill_id)
    
    def _store_metric(self, metric: QualityMetric):
        """存储指标到数据库"""
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO quality_metrics (skill_id, metric_type, timestamp, data)
            VALUES (?, ?, ?, ?)
        ''', (
            metric.skill_id,
            metric.metric_type.value,
            metric.timestamp.isoformat(),
            json.dumps(metric.data, ensure_ascii=False)
        ))
        
        conn.commit()
        conn.close()
    
    def _update_skill_summary(self, skill_id: str):
        """更新技能摘要"""
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        # 获取现有摘要
        cursor.execute('SELECT * FROM skill_summaries WHERE skill_id = ?', (skill_id,))
        existing = cursor.fetchone()
        
        # 获取最新指标数据
        quality_metrics = self.get_metrics(skill_id, MetricType.QUALITY_CHECK)
        ai_metrics = self.get_metrics(skill_id, MetricType.AI_VALIDATION)
        feedback_metrics = self.get_metrics(skill_id, MetricType.USER_FEEDBACK)
        
        # 计算统计信息
        total_checks = len(quality_metrics)
        passed_checks = sum(1 for m in quality_metrics if m.data.get("overall_status") == "passed")
        
        ai_scores = [m.data.get("overall_score", 0) for m in ai_metrics]
        avg_ai_score = statistics.mean(ai_scores) if ai_scores else 0.0
        
        feedback_ratings = [m.data.get("rating", 0) for m in feedback_metrics if "rating" in m.data]
        avg_rating = statistics.mean(feedback_ratings) if feedback_ratings else 0.0
        
        # 性能数据
        performance_metrics = self.get_metrics(skill_id, MetricType.PERFORMANCE)
        performance_data = {}
        if performance_metrics:
            latest_performance = performance_metrics[-1].data
            performance_data = {
                "invocation_count": latest_performance.get("invocation_count", 0),
                "avg_execution_time": latest_performance.get("avg_execution_time", 0),
                "success_rate": latest_performance.get("success_rate", 0),
                "error_rate": latest_performance.get("error_rate", 0)
            }
        
        # 创建摘要JSON
        summary_json = json.dumps({
            "skill_id": skill_id,
            "quality_check_stats": {
                "total_checks": total_checks,
                "passed_checks": passed_checks,
                "pass_rate": passed_checks / total_checks if total_checks > 0 else 0
            },
            "ai_validation_stats": {
                "total_validations": len(ai_metrics),
                "avg_score": avg_ai_score,
                "score_trend": self._calculate_trend(ai_scores)
            },
            "user_feedback_stats": {
                "total_feedback": len(feedback_metrics),
                "avg_rating": avg_rating,
                "rating_trend": self._calculate_trend(feedback_ratings)
            },
            "performance_stats": performance_data,
            "last_updated": datetime.now().isoformat()
        }, ensure_ascii=False)
        
        if existing:
            # 更新现有摘要
            cursor.execute('''
                UPDATE skill_summaries 
                SET last_updated = ?, total_checks = ?, passed_checks = ?, 
                    avg_ai_score = ?, total_feedback = ?, avg_rating = ?, 
                    performance_data = ?, summary_json = ?
                WHERE skill_id = ?
            ''', (
                datetime.now().isoformat(),
                total_checks,
                passed_checks,
                avg_ai_score,
                len(feedback_metrics),
                avg_rating,
                json.dumps(performance_data, ensure_ascii=False),
                summary_json,
                skill_id
            ))
        else:
            # 插入新摘要
            cursor.execute('''
                INSERT INTO skill_summaries 
                (skill_id, first_seen, last_updated, total_checks, passed_checks, 
                 avg_ai_score, total_feedback, avg_rating, performance_data, summary_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                skill_id,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                total_checks,
                passed_checks,
                avg_ai_score,
                len(feedback_metrics),
                avg_rating,
                json.dumps(performance_data, ensure_ascii=False),
                summary_json
            ))
        
        conn.commit()
        conn.close()
    
    def _calculate_trend(self, values: List[float]) -> str:
        """计算趋势（上升、下降、稳定）"""
        if len(values) < 2:
            return "insufficient_data"
        
        # 计算简单线性趋势
        try:
            # 使用简单差值
            if values[-1] > values[0]:
                return "improving"
            elif values[-1] < values[0]:
                return "declining"
            else:
                return "stable"
        except:
            return "unknown"
    
    def get_metrics(self, skill_id: Optional[str] = None, 
                   metric_type: Optional[MetricType] = None,
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None) -> List[QualityMetric]:
        """获取指标数据"""
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        query = "SELECT skill_id, metric_type, timestamp, data FROM quality_metrics WHERE 1=1"
        params = []
        
        if skill_id:
            query += " AND skill_id = ?"
            params.append(skill_id)
        
        if metric_type:
            query += " AND metric_type = ?"
            params.append(metric_type.value)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        
        query += " ORDER BY timestamp ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        metrics = []
        for row in rows:
            skill_id, metric_type_str, timestamp_str, data_str = row
            try:
                data = json.loads(data_str)
                metric = QualityMetric(
                    skill_id=skill_id,
                    metric_type=MetricType(metric_type_str),
                    timestamp=datetime.fromisoformat(timestamp_str),
                    data=data
                )
                metrics.append(metric)
            except Exception as e:
                print(f"解析指标数据失败: {e}")
        
        return metrics
    
    def get_skill_summary(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """获取技能摘要"""
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT summary_json FROM skill_summaries WHERE skill_id = ?', (skill_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row[0])
        return None
    
    def get_all_skill_summaries(self) -> List[Dict[str, Any]]:
        """获取所有技能摘要"""
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT summary_json FROM skill_summaries ORDER BY skill_id')
        rows = cursor.fetchall()
        conn.close()
        
        summaries = []
        for row in rows:
            try:
                summaries.append(json.loads(row[0]))
            except:
                pass
        
        return summaries
    
    def get_skill_quality_trend(self, skill_id: str, days: int = 30) -> Dict[str, Any]:
        """获取技能质量趋势"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        metrics = self.get_metrics(skill_id, start_date=start_date, end_date=end_date)
        
        # 按天分组
        daily_data = {}
        for metric in metrics:
            date_str = metric.timestamp.date().isoformat()
            if date_str not in daily_data:
                daily_data[date_str] = {
                    "quality_checks": 0,
                    "passed_checks": 0,
                    "ai_scores": [],
                    "feedback_ratings": []
                }
            
            if metric.metric_type == MetricType.QUALITY_CHECK:
                daily_data[date_str]["quality_checks"] += 1
                if metric.data.get("overall_status") == "passed":
                    daily_data[date_str]["passed_checks"] += 1
            
            elif metric.metric_type == MetricType.AI_VALIDATION:
                daily_data[date_str]["ai_scores"].append(metric.data.get("overall_score", 0))
            
            elif metric.metric_type == MetricType.USER_FEEDBACK:
                if "rating" in metric.data:
                    daily_data[date_str]["feedback_ratings"].append(metric.data["rating"])
        
        # 计算每日统计
        trend_data = []
        for date_str, data in sorted(daily_data.items()):
            quality_pass_rate = 0
            if data["quality_checks"] > 0:
                quality_pass_rate = data["passed_checks"] / data["quality_checks"]
            
            avg_ai_score = 0
            if data["ai_scores"]:
                avg_ai_score = statistics.mean(data["ai_scores"])
            
            avg_rating = 0
            if data["feedback_ratings"]:
                avg_rating = statistics.mean(data["feedback_ratings"])
            
            trend_data.append({
                "date": date_str,
                "quality_pass_rate": quality_pass_rate,
                "avg_ai_score": avg_ai_score,
                "avg_rating": avg_rating,
                "total_checks": data["quality_checks"],
                "total_feedback": len(data["feedback_ratings"])
            })
        
        return {
            "skill_id": skill_id,
            "period_days": days,
            "trend_data": trend_data,
            "summary": self._calculate_trend_summary(trend_data)
        }
    
    def _calculate_trend_summary(self, trend_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算趋势摘要"""
        if len(trend_data) < 2:
            return {"status": "insufficient_data", "message": "数据不足"}
        
        latest = trend_data[-1]
        earliest = trend_data[0]
        
        quality_change = latest["quality_pass_rate"] - earliest["quality_pass_rate"]
        ai_score_change = latest["avg_ai_score"] - earliest["avg_ai_score"]
        rating_change = latest["avg_rating"] - earliest["avg_rating"]
        
        # 确定趋势状态
        status = "stable"
        if quality_change > 0.1 or ai_score_change > 5 or rating_change > 0.5:
            status = "improving"
        elif quality_change < -0.1 or ai_score_change < -5 or rating_change < -0.5:
            status = "declining"
        
        return {
            "status": status,
            "quality_change": quality_change,
            "ai_score_change": ai_score_change,
            "rating_change": rating_change,
            "message": self._generate_trend_message(status, quality_change, ai_score_change, rating_change)
        }
    
    def _generate_trend_message(self, status: str, quality_change: float, 
                               ai_score_change: float, rating_change: float) -> str:
        """生成趋势消息"""
        messages = []
        
        if status == "improving":
            messages.append("技能质量正在改善")
            if quality_change > 0:
                messages.append(f"质量检查通过率上升了 {quality_change:.1%}")
            if ai_score_change > 0:
                messages.append(f"AI验证得分上升了 {ai_score_change:.1f}分")
            if rating_change > 0:
                messages.append(f"用户评分上升了 {rating_change:.1f}分")
        
        elif status == "declining":
            messages.append("技能质量正在下降")
            if quality_change < 0:
                messages.append(f"质量检查通过率下降了 {abs(quality_change):.1%}")
            if ai_score_change < 0:
                messages.append(f"AI验证得分下降了 {abs(ai_score_change):.1f}分")
            if rating_change < 0:
                messages.append(f"用户评分下降了 {abs(rating_change):.1f}分")
        
        else:
            messages.append("技能质量保持稳定")
        
        return "；".join(messages)


# 全局跟踪器实例
_global_tracker = None

def get_quality_tracker() -> QualityMetricsTracker:
    """获取全局质量跟踪器"""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = QualityMetricsTracker()
    return _global_tracker