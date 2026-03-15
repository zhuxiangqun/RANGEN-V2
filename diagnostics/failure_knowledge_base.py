#!/usr/bin/env python3
"""
失败案例知识库 - 收集、分类和分析系统失败模式

用于建立结构化的失败案例数据库，为后续的机器学习优化（如LearningOptimizer）准备高质量数据。

执行方式:
cd /Users/syu/workdata/person/zy/RANGEN-main\(syu-python\)
source .venv/bin/activate
python diagnostics/failure_knowledge_base.py
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@dataclass
class FailureCase:
    """失败案例数据结构"""
    id: str
    timestamp: str
    query: str
    context: Dict[str, Any]  # session历史、用户信息等
    agent_chain: List[Dict]  # 完整的Agent调用链
    error_type: str
    error_details: str
    trace_mermaid: Optional[str] = None
    suggested_fix: Optional[str] = None
    severity: str = "medium"  # high/medium/low
    reproducible: bool = False
    tags: List[str] = None
    similar_cases: List[str] = None  # 相似案例ID

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.similar_cases is None:
            self.similar_cases = []

class FailureKnowledgeBase:
    """失败案例知识库"""

    def __init__(self, storage_path: str = "diagnostics/failure_kb.json"):
        self.storage_path = storage_path
        self.cases: List[FailureCase] = []
        self.load_existing_cases()

    def add_failure_case(self, query: str, context: Dict, error: Exception,
                        full_trace: Optional[Dict] = None, screenshots: Optional[List] = None):
        """记录一个完整的失败案例"""

        case = FailureCase(
            id=self._generate_case_id(query, error),
            timestamp=datetime.now().isoformat(),
            query=query,
            context=context,
            agent_chain=full_trace.get("agent_chain", []) if full_trace else [],
            error_type=self._classify_error(error, context),
            error_details=str(error),
            trace_mermaid=full_trace.get("mermaid") if full_trace else None,
            suggested_fix=self._suggest_fix(error, context),
            severity=self._assess_severity(error, context),
            tags=self._generate_tags(error, context)
        )

        # 检查相似案例
        case.similar_cases = self.find_similar_cases(case)

        self.cases.append(case)
        self.save_cases()

        print(f"📝 已记录失败案例: {case.id} ({case.error_type}) - {case.severity}严重程度")

    def _classify_error(self, error: Exception, context: Dict) -> str:
        """智能分类失败类型"""
        error_str = str(error).lower()
        context_str = str(context).lower()

        # 精确匹配规则
        if 'timeout' in error_str:
            return 'timeout_error'
        elif 'api' in error_str and 'error' in error_str:
            return 'api_error'
        elif 'routing' in context_str or 'coordinator' in context_str:
            return 'routing_error'
        elif 'data' in error_str and 'error' in error_str:
            return 'data_error'
        elif 'logic' in error_str or 'assertion' in error_str:
            return 'logic_error'

        # 基于Agent链分析
        if context.get('agent_chain'):
            failed_agent = self._find_failed_agent(context['agent_chain'])
            if failed_agent:
                return f"{failed_agent}_failure"

        return 'unknown_error'

    def _suggest_fix(self, error: Exception, context: Dict) -> str:
        """根据错误类型提供修复建议"""
        error_type = self._classify_error(error, context)

        suggestions = {
            'timeout_error': '增加超时时间或实现异步处理',
            'api_error': '检查API密钥、网络连接或实现重试机制',
            'routing_error': '修复AgentCoordinator的路由逻辑',
            'data_error': '增加数据验证和错误处理',
            'logic_error': '检查业务逻辑和边界条件处理'
        }

        return suggestions.get(error_type, '需要人工分析')

    def _assess_severity(self, error: Exception, context: Dict) -> str:
        """评估失败严重程度"""
        # 基于错误类型和上下文评估
        error_type = self._classify_error(error, context)

        if error_type in ['api_error', 'routing_error']:
            return 'high'  # 系统级问题
        elif error_type in ['timeout_error', 'data_error']:
            return 'medium'  # 功能级问题
        else:
            return 'low'  # 一般问题

    def _generate_tags(self, error: Exception, context: Dict) -> List[str]:
        """生成标签用于分类和搜索"""
        tags = []
        error_str = str(error).lower()

        # 错误特征标签
        if 'timeout' in error_str:
            tags.append('timeout')
        if 'api' in error_str:
            tags.append('api_error')
        if 'data' in error_str:
            tags.append('data_quality')

        # 上下文标签
        if context.get('user_type') == 'premium':
            tags.append('premium_user')
        if len(context.get('session_history', [])) > 10:
            tags.append('long_session')

        # Agent相关标签
        if context.get('agent_chain'):
            for step in context['agent_chain']:
                tags.append(f"agent_{step.get('agent', 'unknown')}")

        return list(set(tags))  # 去重

    def find_similar_cases(self, new_case: FailureCase, threshold: float = 0.8) -> List[str]:
        """查找相似历史案例"""
        similar_ids = []

        for existing_case in self.cases[-100:]:  # 只检查最近100个案例
            similarity = self._calculate_similarity(new_case, existing_case)
            if similarity >= threshold:
                similar_ids.append(existing_case.id)

        return similar_ids

    def _calculate_similarity(self, case1: FailureCase, case2: FailureCase) -> float:
        """计算两个案例的相似度"""
        # 基于错误类型、查询关键词、Agent链的相似度计算
        type_sim = 1.0 if case1.error_type == case2.error_type else 0.0

        # 查询文本相似度（简单关键词匹配）
        query1_words = set(case1.query.lower().split())
        query2_words = set(case2.query.lower().split())
        query_sim = len(query1_words & query2_words) / len(query1_words | query2_words) if (query1_words | query2_words) else 0.0

        # Agent链相似度
        chain_sim = self._calculate_chain_similarity(case1.agent_chain, case2.agent_chain)

        return (type_sim * 0.4 + query_sim * 0.4 + chain_sim * 0.2)

    def _calculate_chain_similarity(self, chain1: List[Dict], chain2: List[Dict]) -> float:
        """计算Agent链的相似度"""
        if not chain1 or not chain2:
            return 0.0

        agents1 = [step.get('agent') for step in chain1]
        agents2 = [step.get('agent') for step in chain2]

        # 计算共同Agent的比例
        common_agents = set(agents1) & set(agents2)
        total_unique = set(agents1) | set(agents2)

        return len(common_agents) / len(total_unique) if total_unique else 0.0

    def _find_failed_agent(self, agent_chain: List[Dict]) -> Optional[str]:
        """从Agent链中找到失败的Agent"""
        for step in agent_chain:
            if not step.get('success', True):
                return step.get('agent')
        return None

    def _generate_case_id(self, query: str, error: Exception) -> str:
        """生成案例唯一ID"""
        content = f"{query}_{str(error)}_{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def load_existing_cases(self):
        """加载现有案例"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.cases = [FailureCase(**case) for case in data]
        except FileNotFoundError:
            self.cases = []

    def save_cases(self):
        """保存案例到文件"""
        data = [asdict(case) for case in self.cases]
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    async def analyze_patterns(self) -> Dict[str, Any]:
        """分析失败模式和趋势"""
        if not self.cases:
            return {"error": "没有失败案例数据"}

        # 统计错误类型分布
        error_types = {}
        for case in self.cases:
            error_types[case.error_type] = error_types.get(case.error_type, 0) + 1

        # 统计严重程度分布
        severities = {}
        for case in self.cases:
            severities[case.severity] = severities.get(case.severity, 0) + 1

        # 统计热门标签
        all_tags = []
        for case in self.cases:
            all_tags.extend(case.tags)

        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return {
            "total_cases": len(self.cases),
            "error_type_distribution": error_types,
            "severity_distribution": severities,
            "top_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "temporal_trend": self._analyze_temporal_trend()
        }

    def _analyze_temporal_trend(self) -> Dict[str, int]:
        """分析时间趋势（每日失败数）"""
        daily_counts = {}
        for case in self.cases:
            date = case.timestamp[:10]  # YYYY-MM-DD
            daily_counts[date] = daily_counts.get(date, 0) + 1
        return daily_counts

    def export_report(self) -> str:
        """导出分析报告"""
        analysis = asyncio.run(self.analyze_patterns())

        report = "# 失败案例分析报告\n\n"
        report += f"## 概述\n"
        report += f"- 总案例数：{analysis['total_cases']}\n"
        report += f"- 分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        report += f"## 错误类型分布\n"
        for error_type, count in analysis['error_type_distribution'].items():
            percentage = (count / analysis['total_cases']) * 100
            report += f"- {error_type}: {count}次 ({percentage:.1f}%)\n"
        report += "\n"

        report += f"## 严重程度分布\n"
        for severity, count in analysis['severity_distribution'].items():
            percentage = (count / analysis['total_cases']) * 100
            report += f"- {severity}: {count}次 ({percentage:.1f}%)\n"
        report += "\n"

        report += f"## Top 10 标签\n"
        for tag, count in analysis['top_tags']:
            report += f"- {tag}: {count}次\n"
        report += "\n"

        return report

# 全局失败知识库实例
failure_kb = FailureKnowledgeBase()

async def demo_failure_collection():
    """演示失败案例收集"""
    print("🔍 失败案例知识库演示\n")

    # 模拟一些失败案例
    sample_failures = [
        {
            "query": "What is machine learning?",
            "context": {"session_history": ["previous query"], "user_type": "premium"},
            "error": TimeoutError("API request timed out"),
            "trace": {"agent_chain": [{"agent": "RAGExpert", "success": False}]}
        },
        {
            "query": "Explain neural networks",
            "context": {"session_history": [], "user_type": "regular"},
            "error": ValueError("Invalid data format"),
            "trace": {"agent_chain": [{"agent": "ReasoningExpert", "success": False}]}
        },
        {
            "query": "How does AI work?",
            "context": {"agent_chain": [{"agent": "AgentCoordinator", "success": False}]},
            "error": RuntimeError("Routing logic error"),
            "trace": {"agent_chain": [{"agent": "AgentCoordinator", "success": False}]}
        }
    ]

    # 添加案例到知识库
    for failure in sample_failures:
        failure_kb.add_failure_case(
            query=failure["query"],
            context=failure["context"],
            error=failure["error"],
            full_trace=failure["trace"]
        )

    # 分析模式
    print("\n📊 失败模式分析:")
    analysis = await failure_kb.analyze_patterns()
    print(f"总案例数: {analysis['total_cases']}")
    print(f"错误类型分布: {analysis['error_type_distribution']}")
    print(f"严重程度分布: {analysis['severity_distribution']}")
    print(f"Top标签: {analysis['top_tags']}")

    # 导出报告
    report = failure_kb.export_report()
    with open("diagnostics/failure_analysis_report.md", "w", encoding="utf-8") as f:
        f.write(report)

    print("\n✅ 分析报告已保存到: diagnostics/failure_analysis_report.md")

if __name__ == "__main__":
    asyncio.run(demo_failure_collection())
