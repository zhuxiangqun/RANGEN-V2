"""
静态评估分析器

通过扫描代码来评估系统的架构、质量、数据能力等静态指标
"""

import ast
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple


class StaticArchitectureAnalyzer:
    """静态架构评估"""
    
    def __init__(self, source_path: str = None):
        self.source_path = source_path or "/Users/apple/workdata/person/zy/RANGEN-main(syu-python)/src"
    
    def analyze(self) -> Dict[str, Any]:
        """分析架构能力"""
        harness = self._analyze_harness()
        architecture = self._analyze_architecture()
        observability = self._analyze_observability()
        monitoring = self._analyze_monitoring()
        self_healing = self._analyze_self_healing()
        rollout = self._analyze_rollout()
        
        metrics = {
            "harness": harness,
            "architecture": architecture,
            "observability": observability,
            "monitoring": monitoring,
            "self_healing": self_healing,
            "rollout": rollout,
        }
        
        scores = [m["score"] for m in metrics.values()]
        overall = sum(scores) / len(scores) if scores else 0.0
        
        return {
            "overall_score": overall,
            "metrics": metrics,
            "passed_count": sum(1 for m in metrics.values() if m["score"] >= 0.7),
            "total_count": len(metrics),
        }
    
    def _get_py_files(self) -> List[Path]:
        py_files = list(Path(self.source_path).rglob("*.py"))
        return [f for f in py_files if "__pycache__" not in str(f) and ".venv" not in str(f)]
    
    def _analyze_harness(self) -> Dict[str, Any]:
        patterns = ["retry", "fallback", "circuit", "breaker", "timeout", "graceful"]
        found = self._find_patterns(patterns)
        score = min(1.0, len(found) / 5)
        return {"score": score, "found": found, "evidence": f"发现{len(found)}个容错机制"}
    
    def _analyze_architecture(self) -> Dict[str, Any]:
        patterns = ["abstract", "interface", "base", "factory", "builder", "strategy"]
        found = self._find_patterns(patterns)
        score = min(1.0, len(found) / 6)
        return {"score": score, "found": found, "evidence": f"发现{len(found)}个设计模式"}
    
    def _analyze_observability(self) -> Dict[str, Any]:
        patterns = ["log", "trace", "metric", "span", "event", "hook"]
        found = self._find_patterns(patterns)
        score = min(1.0, len(found) / 6)
        return {"score": score, "found": found, "evidence": f"发现{len(found)}个可观测性特性"}
    
    def _analyze_monitoring(self) -> Dict[str, Any]:
        patterns = ["alert", "notify", "dashboard", "status", "health", "check"]
        found = self._find_patterns(patterns)
        score = min(1.0, len(found) / 6)
        return {"score": score, "found": found, "evidence": f"发现{len(found)}个监控特性"}
    
    def _analyze_self_healing(self) -> Dict[str, Any]:
        patterns = ["restart", "recovery", "heal", "repair", "recover", "rollback"]
        found = self._find_patterns(patterns)
        score = min(1.0, len(found) / 6)
        return {"score": score, "found": found, "evidence": f"发现{len(found)}个自愈机制"}
    
    def _analyze_rollout(self) -> Dict[str, Any]:
        patterns = ["deploy", "release", "canary", "feature_flag", "ab_test", "gradual"]
        found = self._find_patterns(patterns)
        score = min(1.0, len(found) / 6)
        return {"score": score, "found": found, "evidence": f"发现{len(found)}个发布特性"}
    
    def _find_patterns(self, patterns: List[str]) -> List[str]:
        found = []
        for p in self._get_py_files():
            try:
                with open(p, encoding="utf-8") as f:
                    content = f.read().lower()
                for pattern in patterns:
                    if pattern.lower() in content and pattern not in found:
                        found.append(pattern)
            except:
                continue
        return found


class StaticDataCapabilityAnalyzer:
    """静态数据能力评估"""
    
    def __init__(self, source_path: str = None):
        self.source_path = source_path or "/Users/apple/workdata/person/zy/RANGEN-main(syu-python)/src"
    
    def analyze(self) -> Dict[str, Any]:
        data_source = self._analyze_data_source()
        knowledge_mgmt = self._analyze_knowledge_mgmt()
        vector_mgmt = self._analyze_vector_mgmt()
        data_lineage = self._analyze_data_lineage()
        
        metrics = {
            "data_source": data_source,
            "knowledge_mgmt": knowledge_mgmt,
            "vector_mgmt": vector_mgmt,
            "data_lineage": data_lineage,
        }
        
        scores = [m["score"] for m in metrics.values()]
        overall = sum(scores) / len(scores) if scores else 0.0
        
        return {
            "overall_score": overall,
            "metrics": metrics,
            "passed_count": sum(1 for m in metrics.values() if m["score"] >= 0.7),
            "total_count": len(metrics),
        }
    
    def _get_py_files(self) -> List[Path]:
        py_files = list(Path(self.source_path).rglob("*.py"))
        return [f for f in py_files if "__pycache__" not in str(f) and ".venv" not in str(f)]
    
    def _analyze_data_source(self) -> Dict[str, Any]:
        patterns = ["database", "db", "mysql", "postgres", "mongodb", "redis", "elasticsearch"]
        found = self._find_patterns(patterns)
        score = min(1.0, len(found) / 5)
        return {"score": score, "found": found, "evidence": f"支持{len(found)}种数据源"}
    
    def _analyze_knowledge_mgmt(self) -> Dict[str, Any]:
        patterns = ["knowledge", "kb", "knowledge_base", "ontology", "taxonomy"]
        found = self._find_patterns(patterns)
        score = min(1.0, len(found) / 5)
        return {"score": score, "found": found, "evidence": f"发现{len(found)}个知识管理特性"}
    
    def _analyze_vector_mgmt(self) -> Dict[str, Any]:
        patterns = ["vector", "embedding", "faiss", "pinecone", "chroma", "milvus"]
        found = self._find_patterns(patterns)
        score = min(1.0, len(found) / 5)
        return {"score": score, "found": found, "evidence": f"发现{len(found)}个向量管理特性"}
    
    def _analyze_data_lineage(self) -> Dict[str, Any]:
        patterns = ["lineage", "provenance", "血缘", "trace", "dependency"]
        found = self._find_patterns(patterns)
        score = min(1.0, len(found) / 5)
        return {"score": score, "found": found, "evidence": f"发现{len(found)}个血缘追踪特性"}
    
    def _find_patterns(self, patterns: List[str]) -> List[str]:
        found = []
        for p in self._get_py_files():
            try:
                with open(p, encoding="utf-8") as f:
                    content = f.read().lower()
                for pattern in patterns:
                    if pattern.lower() in content and pattern not in found:
                        found.append(pattern)
            except:
                continue
        return found


class StaticPlatformCapabilityAnalyzer:
    """静态平台能力评估"""
    
    def __init__(self, source_path: str = None):
        self.source_path = source_path or "/Users/apple/workdata/person/zy/RANGEN-main(syu-python)/src"
    
    def analyze(self) -> Dict[str, Any]:
        app_support = self._analyze_app_support()
        cost_control = self._analyze_cost_control()
        integration = self._analyze_integration()
        
        metrics = {
            "app_support": app_support,
            "cost_control": cost_control,
            "integration": integration,
        }
        
        scores = [m["score"] for m in metrics.values()]
        overall = sum(scores) / len(scores) if scores else 0.0
        
        return {
            "overall_score": overall,
            "metrics": metrics,
            "passed_count": sum(1 for m in metrics.values() if m["score"] >= 0.7),
            "total_count": len(metrics),
        }
    
    def _get_py_files(self) -> List[Path]:
        py_files = list(Path(self.source_path).rglob("*.py"))
        return [f for f in py_files if "__pycache__" not in str(f) and ".venv" not in str(f)]
    
    def _analyze_app_support(self) -> Dict[str, Any]:
        patterns = ["tenant", "namespace", "workspace", "project", "app"]
        found = self._find_patterns(patterns)
        score = min(1.0, len(found) / 5)
        return {"score": score, "found": found, "evidence": f"发现{len(found)}个应用支撑特性"}
    
    def _analyze_cost_control(self) -> Dict[str, Any]:
        patterns = ["cost", "budget", "quota", "limit", "rate", "token"]
        found = self._find_patterns(patterns)
        score = min(1.0, len(found) / 6)
        return {"score": score, "found": found, "evidence": f"发现{len(found)}个成本控制特性"}
    
    def _analyze_integration(self) -> Dict[str, Any]:
        patterns = ["api", "webhook", "callback", "event", "plugin", "extension"]
        found = self._find_patterns(patterns)
        score = min(1.0, len(found) / 6)
        return {"score": score, "found": found, "evidence": f"发现{len(found)}个集成特性"}
    
    def _find_patterns(self, patterns: List[str]) -> List[str]:
        found = []
        for p in self._get_py_files():
            try:
                with open(p, encoding="utf-8") as f:
                    content = f.read().lower()
                for pattern in patterns:
                    if pattern.lower() in content and pattern not in found:
                        found.append(pattern)
            except:
                continue
        return found


def run_static_evaluation(source_path: str = None) -> Dict[str, Any]:
    """运行所有静态评估"""
    source_path = source_path or "/Users/apple/workdata/person/zy/RANGEN-main(syu-python)/src"
    
    architecture = StaticArchitectureAnalyzer(source_path).analyze()
    data_capability = StaticDataCapabilityAnalyzer(source_path).analyze()
    platform_capability = StaticPlatformCapabilityAnalyzer(source_path).analyze()
    
    all_scores = [
        architecture["overall_score"],
        data_capability["overall_score"],
        platform_capability["overall_score"],
    ]
    overall = sum(all_scores) / len(all_scores)
    
    return {
        "overall_score": overall,
        "architecture": architecture,
        "data_capability": data_capability,
        "platform_capability": platform_capability,
    }
