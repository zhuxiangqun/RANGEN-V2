#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移优先级计算脚本

基于Agent使用情况数据，计算迁移优先级分数。
"""

import json
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime


class MigrationMetrics:
    """迁移优先级计算器"""
    
    # Agent映射关系（原有Agent -> 目标Agent）
    AGENT_MAPPING = {
        "ChiefAgent": "AgentCoordinator",
        "RAGAgent": "RAGExpert",
        "KnowledgeRetrievalAgent": "RAGExpert",
        "ReActAgent": "ReasoningExpert",
        "LearningSystem": "LearningOptimizer",
        "StrategicChiefAgent": "AgentCoordinator",
        "PromptEngineeringAgent": "ToolOrchestrator",
        "ContextEngineeringAgent": "MemoryManager",
        "AnswerGenerationAgent": "RAGExpert",
        "OptimizedKnowledgeRetrievalAgent": "RAGExpert",
        "EnhancedAnalysisAgent": "ReasoningExpert",
        "FactVerificationAgent": "QualityController",
        "CitationAgent": "QualityController",
        "IntelligentCoordinatorAgent": "AgentCoordinator",
        "IntelligentStrategyAgent": "AgentCoordinator",
        "MemoryAgent": "MemoryManager",
    }
    
    # 业务关键性Agent列表
    BUSINESS_CRITICAL_AGENTS = [
        "ChiefAgent",
        "RAGAgent",
        "KnowledgeRetrievalAgent",
        "ReasoningAgent",
        "ReActAgent",
    ]
    
    # 迁移难度估算（基于依赖复杂度）
    MIGRATION_DIFFICULTY = {
        "ChiefAgent": 25,  # 高难度，多依赖
        "RAGAgent": 20,    # 中高难度
        "KnowledgeRetrievalAgent": 15,
        "ReActAgent": 15,
        "ReasoningAgent": 15,
        "LearningSystem": 12,
        "MemoryAgent": 10,
        "CitationAgent": 8,
        "AnswerGenerationAgent": 10,
        "PromptEngineeringAgent": 10,
        "ContextEngineeringAgent": 10,
        "EnhancedAnalysisAgent": 12,
        "StrategicChiefAgent": 20,
        "OptimizedKnowledgeRetrievalAgent": 12,
    }
    
    def __init__(self, usage_data_file: str = "agent_usage_analysis.json"):
        """初始化"""
        self.usage_data = self._load_usage_data(usage_data_file)
        self.migration_priorities = []
    
    def _load_usage_data(self, filepath: str) -> Dict[str, Any]:
        """加载使用情况数据"""
        if not Path(filepath).exists():
            print(f"⚠️  使用情况数据文件不存在: {filepath}")
            print("   请先运行: python scripts/analyze_agent_usage.py")
            return {
                "imports": {},
                "instantiations": {},
                "method_calls": {},
            }
        
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def calculate_priority_score(self, agent_name: str) -> Dict[str, Any]:
        """计算Agent迁移优先级分数"""
        # 1. 使用频率权重（40%）
        import_count = self.usage_data.get("imports", {}).get(agent_name, 0)
        instantiation_count = self.usage_data.get("instantiations", {}).get(agent_name, 0)
        method_call_count = self.usage_data.get("method_calls", {}).get(agent_name, 0)
        
        total_usage = import_count + instantiation_count + method_call_count
        max_usage = max([
            sum(self.usage_data.get("imports", {}).values()),
            sum(self.usage_data.get("instantiations", {}).values()),
        ]) or 1
        
        frequency_score = (total_usage / max_usage) * 40  # 归一化到0-40
        
        # 2. 业务关键性权重（30%）
        business_critical = agent_name in self.BUSINESS_CRITICAL_AGENTS
        business_score = 30 if business_critical else 10
        
        # 3. 迁移难度权重（30%）
        difficulty = self.MIGRATION_DIFFICULTY.get(agent_name, 15)
        difficulty_score = (30 - difficulty)  # 难度越低，分数越高
        
        total_score = frequency_score + business_score + difficulty_score
        
        # 确定优先级
        priority = self._determine_priority(total_score)
        
        # 获取目标Agent
        target_agent = self.AGENT_MAPPING.get(agent_name, "未知")
        
        return {
            "agent": agent_name,
            "target_agent": target_agent,
            "total_score": round(total_score, 2),
            "frequency_score": round(frequency_score, 2),
            "business_score": business_score,
            "difficulty_score": round(difficulty_score, 2),
            "migration_priority": priority,
            "usage_count": {
                "imports": import_count,
                "instantiations": instantiation_count,
                "method_calls": method_call_count,
                "total": total_usage,
            },
            "locations": self.usage_data.get("agent_locations", {}).get(agent_name, []),
        }
    
    def _determine_priority(self, score: float) -> str:
        """确定优先级"""
        if score >= 60:
            return "P0-立即迁移"
        elif score >= 40:
            return "P1-本周迁移"
        elif score >= 20:
            return "P2-本月迁移"
        else:
            return "P3-可延迟"
    
    def calculate_all_priorities(self) -> List[Dict[str, Any]]:
        """计算所有Agent的优先级"""
        priorities = []
        
        # 获取所有原有Agent
        all_agents = set(self.AGENT_MAPPING.keys())
        
        # 添加使用情况数据中的Agent
        usage_agents = set(self.usage_data.get("imports", {}).keys())
        all_agents.update(usage_agents)
        
        for agent_name in sorted(all_agents):
            if agent_name in self.AGENT_MAPPING:
                priority_data = self.calculate_priority_score(agent_name)
                priorities.append(priority_data)
        
        # 按优先级排序
        priority_order = {
            "P0-立即迁移": 0,
            "P1-本周迁移": 1,
            "P2-本月迁移": 2,
            "P3-可延迟": 3,
        }
        
        priorities.sort(
            key=lambda x: (
                priority_order.get(x["migration_priority"], 99),
                -x["total_score"]
            )
        )
        
        return priorities
    
    def generate_report(self, output_file: str = "migration_priority.json"):
        """生成优先级报告"""
        priorities = self.calculate_all_priorities()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_agents": len(priorities),
            "priorities": priorities,
            "summary": {
                "P0": len([p for p in priorities if p["migration_priority"] == "P0-立即迁移"]),
                "P1": len([p for p in priorities if p["migration_priority"] == "P1-本周迁移"]),
                "P2": len([p for p in priorities if p["migration_priority"] == "P2-本月迁移"]),
                "P3": len([p for p in priorities if p["migration_priority"] == "P3-可延迟"]),
            }
        }
        
        # 保存JSON报告
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 优先级报告已保存: {output_file}")
        
        # 打印优先级摘要
        print("\n📈 迁移优先级摘要:")
        print(f"  P0-立即迁移: {report['summary']['P0']} 个Agent")
        print(f"  P1-本周迁移: {report['summary']['P1']} 个Agent")
        print(f"  P2-本月迁移: {report['summary']['P2']} 个Agent")
        print(f"  P3-可延迟:   {report['summary']['P3']} 个Agent")
        
        # 打印Top 5优先级Agent
        print("\n🔥 Top 5 迁移优先级Agent:")
        for idx, priority in enumerate(priorities[:5], 1):
            print(f"  {idx}. {priority['agent']:40s} → {priority['target_agent']:30s} [{priority['migration_priority']}] (分数: {priority['total_score']:.1f})")
        
        return report


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="计算迁移优先级")
    parser.add_argument(
        "--usage-data",
        type=str,
        default="agent_usage_analysis.json",
        help="使用情况数据文件（默认: agent_usage_analysis.json）"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="migration_priority.json",
        help="输出文件路径（默认: migration_priority.json）"
    )
    
    args = parser.parse_args()
    
    metrics = MigrationMetrics(usage_data_file=args.usage_data)
    report = metrics.generate_report(output_file=args.output)
    
    print(f"\n✅ 优先级计算完成！")
    print(f"   - 总Agent数: {report['total_agents']}")


if __name__ == "__main__":
    main()

