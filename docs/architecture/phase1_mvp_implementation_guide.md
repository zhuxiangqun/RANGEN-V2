# 第一阶段MVP实施指南

## 📋 概述

本文档提供第一阶段MVP（诊断仪表盘）的详细实施指南，确保在4周内交付一个可用的核心功能。

## 🎯 MVP核心功能

1. **定时诊断任务**：每小时运行一次诊断
2. **诊断数据库**：存储诊断报告和建议
3. **Web仪表盘**：展示系统健康度和问题
4. **基础告警**：严重问题自动通知

## 📅 4周实施计划

### 第1周：基础设施与数据收集

#### 任务1.1：搭建诊断数据库

**文件**：`src/core/diagnostic_database.py`

```python
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
import json

class DiagnosticDatabase:
    """诊断数据库（SQLite，生产环境可切换PostgreSQL）"""
    
    def __init__(self, db_path: str = "data/diagnostic/diagnostic.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 诊断报告表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS diagnostic_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_cycle INTEGER,
                diagnostic_type TEXT,
                system_state TEXT,
                findings TEXT,
                severity REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 建议表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recommendation_id TEXT UNIQUE,
                diagnostic_report_id INTEGER,
                recommendation_type TEXT,
                template_name TEXT,
                title TEXT,
                description TEXT,
                priority REAL,
                risk_level TEXT,
                expected_benefit TEXT,
                execution_plan TEXT,
                rollback_plan TEXT,
                validation_command TEXT,
                structured_data TEXT,
                status TEXT DEFAULT 'pending',
                approved_by TEXT,
                approved_at DATETIME,
                executed_at DATETIME,
                execution_result TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (diagnostic_report_id) REFERENCES diagnostic_reports(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_diagnostic_report(self, report: Dict[str, Any]) -> int:
        """保存诊断报告"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO diagnostic_reports 
            (report_cycle, diagnostic_type, system_state, findings, severity)
            VALUES (?, ?, ?, ?, ?)
        """, (
            report['report_cycle'],
            report['diagnostic_type'],
            json.dumps(report['system_state']),
            json.dumps(report['findings']),
            report['severity']
        ))
        
        report_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return report_id
    
    def save_recommendation(self, recommendation: Dict[str, Any]) -> str:
        """保存建议"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO recommendations
            (recommendation_id, diagnostic_report_id, recommendation_type, 
             template_name, title, description, priority, risk_level,
             expected_benefit, execution_plan, rollback_plan, validation_command,
             structured_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            recommendation['recommendation_id'],
            recommendation.get('diagnostic_report_id'),
            recommendation['type'],
            recommendation.get('template_name'),
            recommendation['title'],
            recommendation['description'],
            recommendation['priority'],
            recommendation['risk_level'],
            json.dumps(recommendation.get('expected_benefit', {})),
            json.dumps(recommendation.get('execution_plan', [])),
            json.dumps(recommendation.get('rollback_plan', [])),
            recommendation.get('validation_command'),
            json.dumps(recommendation.get('structured_data', {}))
        ))
        
        conn.commit()
        conn.close()
        return recommendation['recommendation_id']
    
    def get_pending_recommendations(self) -> List[Dict[str, Any]]:
        """获取待审批建议"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM recommendations 
            WHERE status = 'pending'
            ORDER BY priority DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_recent_diagnostic_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的诊断报告"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM diagnostic_reports
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
```

#### 任务1.2：在关键节点插入诊断埋点

**文件**：`src/core/diagnostic_data_collector.py`

```python
import time
from datetime import datetime
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class DiagnosticDataCollector:
    """诊断数据收集器"""
    
    def __init__(self):
        self.execution_data = []
        self.node_execution_times = {}
        self.error_logs = []
    
    def collect_node_execution(
        self,
        node_name: str,
        start_time: float,
        end_time: float,
        success: bool,
        error: Optional[Exception] = None
    ):
        """收集节点执行数据"""
        execution_time = end_time - start_time
        
        data = {
            "node_name": node_name,
            "execution_time": execution_time,
            "start_time": start_time,
            "end_time": end_time,
            "success": success,
            "error": str(error) if error else None,
            "timestamp": datetime.now().isoformat()
        }
        
        self.execution_data.append(data)
        
        # 更新节点执行时间统计
        if node_name not in self.node_execution_times:
            self.node_execution_times[node_name] = []
        self.node_execution_times[node_name].append(execution_time)
        
        # 记录错误
        if not success and error:
            self.error_logs.append({
                "node_name": node_name,
                "error": str(error),
                "timestamp": datetime.now().isoformat()
            })
    
    def get_system_state(self) -> Dict[str, Any]:
        """获取系统状态（用于诊断）"""
        # 计算平均执行时间
        avg_execution_times = {
            node: sum(times) / len(times)
            for node, times in self.node_execution_times.items()
        }
        
        # 计算错误率
        total_executions = len(self.execution_data)
        failed_executions = sum(1 for d in self.execution_data if not d['success'])
        error_rate = failed_executions / total_executions if total_executions > 0 else 0
        
        return {
            "node_execution_times": avg_execution_times,
            "error_rate": error_rate,
            "total_executions": total_executions,
            "failed_executions": failed_executions,
            "recent_errors": self.error_logs[-10:],  # 最近10个错误
            "timestamp": datetime.now().isoformat()
        }
```

#### 任务1.3：集成到现有工作流

**修改**：`src/core/langgraph_unified_workflow.py`

```python
# 在 UnifiedResearchWorkflow.__init__ 中添加
from src.core.diagnostic_data_collector import DiagnosticDataCollector

class UnifiedResearchWorkflow:
    def __init__(self, ...):
        # ... 现有代码 ...
        
        # 新增：诊断数据收集器
        self.diagnostic_collector = DiagnosticDataCollector()
    
    # 在节点执行前后添加数据收集
    async def _execute_node_with_collection(self, node_name: str, node_func, state):
        """执行节点并收集数据"""
        start_time = time.time()
        success = False
        error = None
        
        try:
            result = await node_func(state)
            success = True
            return result
        except Exception as e:
            error = e
            raise
        finally:
            end_time = time.time()
            self.diagnostic_collector.collect_node_execution(
                node_name, start_time, end_time, success, error
            )
```

### 第2周：核心诊断逻辑

#### 任务2.1：实现基础诊断逻辑

**文件**：`src/core/system_diagnostic_module.py`

```python
from typing import Dict, List, Any
from datetime import datetime

class SystemDiagnosticModule:
    """系统诊断模块"""
    
    def __init__(self):
        # 诊断阈值配置
        self.thresholds = {
            "max_execution_time": 5.0,  # 最大执行时间（秒）
            "max_error_rate": 0.05,    # 最大错误率（5%）
            "max_node_execution_time": 3.0  # 单个节点最大执行时间
        }
    
    async def diagnose_system(
        self,
        system_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """诊断系统状态"""
        findings = []
        severity = 0.0
        
        # 1. 检查错误率
        error_rate = system_state.get("error_rate", 0)
        if error_rate > self.thresholds["max_error_rate"]:
            findings.append({
                "type": "high_error_rate",
                "severity": "high",
                "description": f"错误率过高: {error_rate:.2%}",
                "recommendation": "检查错误日志，分析错误原因"
            })
            severity += 0.5
        
        # 2. 检查节点执行时间
        node_execution_times = system_state.get("node_execution_times", {})
        slow_nodes = []
        for node_name, avg_time in node_execution_times.items():
            if avg_time > self.thresholds["max_node_execution_time"]:
                slow_nodes.append({
                    "node_name": node_name,
                    "avg_time": avg_time,
                    "threshold": self.thresholds["max_node_execution_time"]
                })
                findings.append({
                    "type": "slow_node",
                    "severity": "medium",
                    "node_name": node_name,
                    "description": f"节点 {node_name} 执行时间过长: {avg_time:.2f}秒",
                    "recommendation": f"优化节点 {node_name} 的性能"
                })
                severity += 0.3
        
        # 3. 检查最近错误
        recent_errors = system_state.get("recent_errors", [])
        if len(recent_errors) >= 5:
            # 分析错误模式
            error_patterns = self._analyze_error_patterns(recent_errors)
            findings.append({
                "type": "error_pattern",
                "severity": "high",
                "description": f"发现错误模式: {error_patterns}",
                "recommendation": "根据错误模式制定修复方案"
            })
            severity += 0.4
        
        return {
            "health_status": "healthy" if severity < 0.5 else "warning" if severity < 1.0 else "critical",
            "findings": findings,
            "severity": min(severity, 1.0),
            "timestamp": datetime.now().isoformat()
        }
    
    def _analyze_error_patterns(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析错误模式"""
        # 简单实现：统计错误类型
        error_types = {}
        for error in errors:
            error_type = error.get("error", "Unknown").split(":")[0]
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return error_types
```

#### 任务2.2：创建诊断顾问框架

**文件**：`src/core/diagnostic_advisor.py`

```python
import asyncio
from datetime import datetime
from typing import Dict, Any
from src.core.system_diagnostic_module import SystemDiagnosticModule
from src.core.diagnostic_database import DiagnosticDatabase
from src.core.recommendation_engine import RecommendationEngine

class DiagnosticAdvisor:
    """诊断顾问引擎"""
    
    def __init__(self, diagnostic_db: DiagnosticDatabase):
        self.diagnostic_module = SystemDiagnosticModule()
        self.recommendation_engine = RecommendationEngine()
        self.diagnostic_db = diagnostic_db
        self.recommendation_cycle = 0
    
    async def diagnose_and_recommend(
        self,
        system_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行诊断和建议生成"""
        self.recommendation_cycle += 1
        
        # 1. 诊断系统
        diagnostic_result = await self.diagnostic_module.diagnose_system(system_state)
        
        # 2. 保存诊断报告
        report_id = self.diagnostic_db.save_diagnostic_report({
            "report_cycle": self.recommendation_cycle,
            "diagnostic_type": "system_health",
            "system_state": system_state,
            "findings": diagnostic_result["findings"],
            "severity": diagnostic_result["severity"]
        })
        
        # 3. 生成建议（如果有问题）
        recommendations = []
        if diagnostic_result["severity"] > 0.3:
            recommendations = await self.recommendation_engine.generate_recommendations(
                diagnostic_result, system_state
            )
            
            # 保存建议
            for rec in recommendations:
                rec["diagnostic_report_id"] = report_id
                self.diagnostic_db.save_recommendation(rec)
        
        return {
            "diagnostic_result": diagnostic_result,
            "recommendations": recommendations,
            "report_id": report_id
        }
```

#### 任务2.3：配置Celery定时任务

**文件**：`src/core/diagnostic_tasks.py`

```python
from celery import Celery
from src.core.diagnostic_advisor import DiagnosticAdvisor
from src.core.diagnostic_database import DiagnosticDatabase
from src.core.diagnostic_data_collector import DiagnosticDataCollector

app = Celery('diagnostic_tasks', broker='redis://localhost:6379/0')

@app.task
def run_diagnostic():
    """运行诊断任务（每小时执行）"""
    # 获取系统状态
    collector = DiagnosticDataCollector()
    system_state = collector.get_system_state()
    
    # 执行诊断
    db = DiagnosticDatabase()
    advisor = DiagnosticAdvisor(db)
    
    result = asyncio.run(advisor.diagnose_and_recommend(system_state))
    
    return result
```

**配置文件**：`celery_config.py`

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'run-diagnostic-every-hour': {
        'task': 'src.core.diagnostic_tasks.run_diagnostic',
        'schedule': crontab(minute=0),  # 每小时执行
    },
}
```

### 第3周：报告与展示

#### 任务3.1：构建Streamlit仪表盘

**文件**：`src/visualization/diagnostic_dashboard.py`

```python
import streamlit as st
import pandas as pd
import plotly.express as px
from src.core.diagnostic_database import DiagnosticDatabase
import json

st.set_page_config(page_title="系统诊断仪表盘", layout="wide")

db = DiagnosticDatabase()

# 侧边栏
st.sidebar.title("系统诊断")
st.sidebar.button("刷新数据")

# 主界面
st.title("系统诊断仪表盘")

# 1. 系统健康度概览
st.header("系统健康度")
recent_reports = db.get_recent_diagnostic_reports(limit=24)  # 最近24小时

if recent_reports:
    df = pd.DataFrame(recent_reports)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['severity'] = df['severity'].astype(float)
    
    # 健康度曲线
    fig = px.line(df, x='timestamp', y='severity', 
                  title='系统健康度趋势',
                  labels={'severity': '严重程度', 'timestamp': '时间'})
    st.plotly_chart(fig, use_container_width=True)
    
    # 最新健康状态
    latest_report = recent_reports[0]
    health_status = json.loads(latest_report['findings'])
    st.metric("当前状态", latest_report.get('health_status', 'unknown'))
    st.metric("严重程度", f"{latest_report['severity']:.2f}")

# 2. 最新问题列表
st.header("最新问题")
findings = json.loads(latest_report['findings']) if recent_reports else []
for finding in findings[:10]:
    with st.expander(f"{finding.get('type', 'Unknown')} - {finding.get('severity', 'unknown')}"):
        st.write(finding.get('description', ''))
        st.write(f"建议: {finding.get('recommendation', '')}")

# 3. 待审批建议
st.header("待审批建议")
pending_recs = db.get_pending_recommendations()
for rec in pending_recs:
    with st.expander(f"{rec['title']} - 优先级: {rec['priority']:.2f}"):
        st.write(f"描述: {rec['description']}")
        st.write(f"风险等级: {rec['risk_level']}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"批准 {rec['recommendation_id']}"):
                # 更新状态
                st.success("已批准")
        with col2:
            if st.button(f"拒绝 {rec['recommendation_id']}"):
                st.warning("已拒绝")
```

#### 任务3.2：配置告警

**文件**：`src/core/alert_manager.py`

```python
import smtplib
from email.mime.text import MIMEText
from typing import Dict, Any

class AlertManager:
    """告警管理器"""
    
    def __init__(self, smtp_config: Dict[str, Any]):
        self.smtp_config = smtp_config
    
    def send_alert(self, diagnostic_result: Dict[str, Any]):
        """发送告警"""
        if diagnostic_result["severity"] > 0.7:  # 严重问题
            self._send_email(diagnostic_result)
    
    def _send_email(self, diagnostic_result: Dict[str, Any]):
        """发送邮件告警"""
        msg = MIMEText(f"系统诊断发现严重问题:\n{diagnostic_result}")
        msg['Subject'] = '系统诊断告警'
        msg['From'] = self.smtp_config['from']
        msg['To'] = self.smtp_config['to']
        
        server = smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port'])
        server.send_message(msg)
        server.quit()
```

### 第4周：集成与优化

#### 任务4.1：集成到现有系统

修改 `src/unified_research_system.py`：

```python
# 在 UnifiedResearchSystem 中添加
from src.core.diagnostic_advisor import DiagnosticAdvisor
from src.core.diagnostic_database import DiagnosticDatabase

class UnifiedResearchSystem:
    async def initialize(self):
        # ... 现有代码 ...
        
        # 新增：初始化诊断顾问
        if os.getenv("ENABLE_DIAGNOSTIC_ADVISOR", "false").lower() == "true":
            self.diagnostic_db = DiagnosticDatabase()
            self.diagnostic_advisor = DiagnosticAdvisor(self.diagnostic_db)
            logger.info("✅ 诊断顾问已初始化")
```

## 📝 验收标准

- ✅ 能够每小时自动运行诊断
- ✅ 能够识别并报告系统问题
- ✅ 能够生成基础优化建议
- ✅ 仪表盘能够正常展示诊断结果
- ✅ 严重问题能够及时告警

## 🔗 相关文档

- [AI系统诊断与进化顾问设计方案](./ai_self_evolution_system_design.md)
- [建议模板设计](./ai_self_evolution_system_design.md#建议模板设计)

