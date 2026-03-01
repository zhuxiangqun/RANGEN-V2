"""
Beta Parameter Calculator with ML-based Performance Tracking
P1 Phase Implementation - Dynamic Beta Calculation with Performance Monitoring

Based on RAG_OPTIMIZATION_PLAN.md Section 4.5
"""

import json
import os
import logging
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metrics for strategy evaluation"""
    strategy_name: str
    query: str
    beta_value: float
    execution_time: float
    success: bool
    relevance_score: float
    coverage_score: float
    timestamp: float
    phase: str = "retrieval"


@dataclass
class StrategyPerformance:
    """Aggregated performance data for a strategy"""
    total_executions: int
    successful_executions: int
    avg_relevance: float
    avg_coverage: float
    avg_execution_time: float
    success_rate: float
    last_updated: float


class BetaParameterCalculator:
    """
    DDL β参数计算器 - P1 Phase Implementation
    
    Features:
    - ML-based performance tracking
    - Dynamic beta adjustment based on success rates
    - Strategy effectiveness monitoring
    - Real-time performance metrics collection
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self.config_path = "data/learning/beta_calculator_config.json"
        self.metrics_path = "data/learning/performance_metrics.json"
        
        # Performance tracking
        self.performance_history: deque = deque(maxlen=1000)  # Last 1000 executions
        self.strategy_performance: Dict[str, StrategyPerformance] = {}
        
        # Beta adjustment parameters
        self.beta_adjustment_params = {
            "min_beta": 0.1,
            "max_beta": 2.0,
            "learning_rate": 0.1,
            "performance_window": 20,  # Last 20 executions for adjustment
            "success_rate_threshold": 0.6,
            "relevance_threshold": 0.7
        }
        
        # Strategy mapping based on beta values
        self.beta_strategy_map = {
            "direct": (0.0, 0.5),      # β < 0.5: Direct retrieval
            "hyde": (0.5, 1.4),        # 0.5 ≤ β < 1.4: HyDE
            "cot": (1.4, 2.1)          # β ≥ 1.4: Chain-of-Thought
        }
        
        # Query complexity cache
        self.query_cache: Dict[str, float] = {}
        self.cache_max_size = 1000
        
        self._load_config()
        
    def calculate_beta_for_query(self, query: str, context: Optional[Dict] = None) -> float:
        """
        计算当前查询的β参数（0-2范围）
        影响因素：查询复杂度、历史表现、系统负载
        """
        # 1. 基础β：查询复杂度分析
        base_beta = self._calculate_query_complexity_beta(query)
        
        # 2. 历史表现调整
        adjusted_beta = self._adjust_beta_by_performance(base_beta, query)
        
        # 3. Context-aware adjustments
        if context:
            adjusted_beta = self._apply_context_adjustments(adjusted_beta, context)
        
        # 4. Safety constraints
        final_beta = max(self.beta_adjustment_params["min_beta"], 
                        min(self.beta_adjustment_params["max_beta"], adjusted_beta))
        
        logger.debug(f"Beta calculation: query='{query[:50]}...', base={base_beta:.2f}, final={final_beta:.2f}")
        return round(final_beta, 2)
    
    def _calculate_query_complexity_beta(self, query: str) -> float:
        """Calculate beta based on query complexity"""
        # Check cache first
        cache_key = hashlib.md5(query.encode()).hexdigest()[:8]
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]
        
        # Complexity factors
        word_count = len(query.split())
        char_count = len(query)
        question_words = sum(1 for word in query.lower().split() 
                           if word in ['what', 'how', 'why', 'when', 'where', 'who', 'which'])
        complex_terms = sum(1 for term in query.lower().split() 
                          if any(keyword in term for keyword in ['compare', 'analyze', 'evaluate', 'explain', 'difference']))
        
        # Calculate complexity score (0-2 range)
        complexity_score = 0.0
        
        # Word count factor (0-0.5)
        if word_count <= 5:
            complexity_score += 0.2
        elif word_count <= 15:
            complexity_score += 0.4
        else:
            complexity_score += 0.5
        
        # Question words factor (0-0.5)
        if question_words == 0:
            complexity_score += 0.1
        elif question_words <= 2:
            complexity_score += 0.3
        else:
            complexity_score += 0.5
        
        # Complex terms factor (0-0.5)
        if complex_terms == 0:
            complexity_score += 0.1
        elif complex_terms <= 2:
            complexity_score += 0.3
        else:
            complexity_score += 0.5
        
        # Length factor (0-0.5)
        if char_count <= 50:
            complexity_score += 0.1
        elif char_count <= 150:
            complexity_score += 0.3
        else:
            complexity_score += 0.5
        
        # Cache management
        if len(self.query_cache) >= self.cache_max_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self.query_cache))
            del self.query_cache[oldest_key]
        
        self.query_cache[cache_key] = complexity_score
        return complexity_score
    
    def _adjust_beta_by_performance(self, base_beta: float, query: str) -> float:
        """Adjust beta based on historical performance"""
        # Find similar queries from history
        similar_metrics = self._find_similar_query_metrics(query)
        
        if not similar_metrics:
            return base_beta
        
        # Calculate average success rate for similar queries
        success_rates = [m.success for m in similar_metrics if m.success is not None]
        if not success_rates:
            return base_beta
        
        avg_success = sum(success_rates) / len(success_rates)
        
        # Adjust beta based on performance
        if avg_success < self.beta_adjustment_params["success_rate_threshold"]:
            # Poor performance: increase beta to use more advanced strategies
            adjustment = self.beta_adjustment_params["learning_rate"] * (1.0 - avg_success)
            adjusted_beta = base_beta + adjustment
            logger.debug(f"Performance adjustment: +{adjustment:.2f} due to low success rate {avg_success:.2f}")
        else:
            # Good performance: slightly decrease beta to optimize efficiency
            adjustment = self.beta_adjustment_params["learning_rate"] * 0.5 * (avg_success - 0.6)
            adjusted_beta = base_beta - adjustment
            logger.debug(f"Performance adjustment: -{adjustment:.2f} due to good success rate {avg_success:.2f}")
        
        return adjusted_beta
    
    def _apply_context_adjustments(self, beta: float, context: Dict) -> float:
        """Apply context-aware beta adjustments"""
        adjusted_beta = beta
        
        # User preference hints
        if 'user_preference' in context:
            pref = context['user_preference'].lower()
            if pref == 'detailed':
                adjusted_beta += 0.3
            elif pref == 'quick':
                adjusted_beta -= 0.2
        
        # System load considerations
        if 'system_load' in context:
            load = context['system_load']
            if load > 0.8:  # High load: prefer simpler strategies
                adjusted_beta -= 0.2
            elif load < 0.3:  # Low load: can afford complex strategies
                adjusted_beta += 0.1
        
        # Domain-specific adjustments
        if 'domain' in context:
            domain = context['domain'].lower()
            if domain in ['science', 'research', 'academic']:
                adjusted_beta += 0.2  # Complex domains need more reasoning
            elif domain in ['fact', 'simple', 'basic']:
                adjusted_beta -= 0.2  # Simple domains can use direct retrieval
        
        return adjusted_beta
    
    def _find_similar_query_metrics(self, query: str, max_results: int = 10) -> List[PerformanceMetric]:
        """Find performance metrics for similar queries"""
        current_words = set(query.lower().split())
        similarities = []
        
        for metric in self.performance_history:
            metric_words = set(metric.query.lower().split())
            
            # Calculate Jaccard similarity
            intersection = len(current_words.intersection(metric_words))
            union = len(current_words.union(metric_words))
            
            if union > 0:
                similarity = intersection / union
                if similarity > 0.2:  # Minimum similarity threshold
                    similarities.append((similarity, metric))
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x[0], reverse=True)
        return [metric for _, metric in similarities[:max_results]]
    
    def record_strategy_execution(self, 
                                strategy_name: str,
                                query: str,
                                beta_value: float,
                                execution_time: float,
                                success: bool,
                                relevance_score: float = 0.0,
                                coverage_score: float = 0.0,
                                phase: str = "retrieval"):
        """Record strategy execution for performance tracking"""
        metric = PerformanceMetric(
            strategy_name=strategy_name,
            query=query,
            beta_value=beta_value,
            execution_time=execution_time,
            success=success,
            relevance_score=relevance_score,
            coverage_score=coverage_score,
            timestamp=time.time(),
            phase=phase
        )
        
        # Add to history
        self.performance_history.append(metric)
        
        # Update strategy performance
        self._update_strategy_performance(strategy_name, metric)
        
        # Periodic cleanup and save
        if len(self.performance_history) % 20 == 0:
            self._save_performance_data()
        
        logger.debug(f"Recorded execution: {strategy_name}, success={success}, beta={beta_value:.2f}")
    
    def _update_strategy_performance(self, strategy_name: str, metric: PerformanceMetric):
        """Update aggregated performance data for a strategy"""
        if strategy_name not in self.strategy_performance:
            self.strategy_performance[strategy_name] = StrategyPerformance(
                total_executions=0,
                successful_executions=0,
                avg_relevance=0.0,
                avg_coverage=0.0,
                avg_execution_time=0.0,
                success_rate=0.0,
                last_updated=time.time()
            )
        
        perf = self.strategy_performance[strategy_name]
        
        # Ensure avg_relevance is a float (handle any type issues)
        if not isinstance(perf.avg_relevance, (int, float)):
            perf.avg_relevance = 0.0
        if not isinstance(perf.avg_coverage, (int, float)):
            perf.avg_coverage = 0.0
        if not isinstance(perf.avg_execution_time, (int, float)):
            perf.avg_execution_time = 0.0
        
        # Update running averages
        perf.total_executions += 1
        if metric.success:
            perf.successful_executions += 1
        
        # Calculate new averages using exponential moving average
        alpha = 0.1  # Exponential moving average factor
        perf.avg_relevance = float((1 - alpha) * float(perf.avg_relevance) + alpha * float(metric.relevance_score))
        perf.avg_coverage = float((1 - alpha) * float(perf.avg_coverage) + alpha * float(metric.coverage_score))
        perf.avg_execution_time = float((1 - alpha) * float(perf.avg_execution_time) + alpha * float(metric.execution_time))
        perf.success_rate = float(perf.successful_executions) / float(perf.total_executions)
        perf.last_updated = time.time()
        
        logger.debug(f"Updated {strategy_name} performance: success_rate={perf.success_rate:.2f}")
    
    def get_strategy_recommendations(self, query: str) -> List[Tuple[str, float]]:
        """Get strategy recommendations with confidence scores"""
        base_beta = self._calculate_query_complexity_beta(query)
        recommendations = []
        
        for strategy_name, (min_beta, max_beta) in self.beta_strategy_map.items():
            if min_beta <= base_beta < max_beta:
                confidence = 1.0 - abs(base_beta - (min_beta + max_beta) / 2) / (max_beta - min_beta)
                
                # Adjust confidence based on historical performance
                if strategy_name in self.strategy_performance:
                    perf = self.strategy_performance[strategy_name]
                    confidence *= perf.success_rate
                
                recommendations.append((strategy_name, confidence))
        
        # Sort by confidence
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations
    
    def get_performance_metrics(self, strategy_name: Optional[str] = None) -> Dict[str, Any]:
        """Get current performance metrics"""
        if strategy_name and strategy_name in self.strategy_performance:
            return asdict(self.strategy_performance[strategy_name])
        
        return {name: asdict(perf) for name, perf in self.strategy_performance.items()}
    
    def _load_config(self):
        """Load configuration and performance data"""
        # Load configuration
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.beta_adjustment_params.update(config.get("adjustment_params", {}))
                    self.beta_strategy_map.update(config.get("strategy_mapping", {}))
            except Exception as e:
                logger.warning(f"Failed to load beta calculator config: {e}")
        
        # Load performance data
        if os.path.exists(self.metrics_path):
            try:
                with open(self.metrics_path, 'r') as f:
                    data = json.load(f)
                    # Reconstruct strategy performance
                    for name, perf_data in data.get("strategy_performance", {}).items():
                        self.strategy_performance[name] = StrategyPerformance(**perf_data)
            except Exception as e:
                logger.warning(f"Failed to load performance metrics: {e}")
    
    def _save_performance_data(self):
        """Save performance data to file"""
        try:
            os.makedirs(os.path.dirname(self.metrics_path), exist_ok=True)
            data = {
                "strategy_performance": {name: asdict(perf) for name, perf in self.strategy_performance.items()},
                "last_updated": time.time()
            }
            with open(self.metrics_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save performance metrics: {e}")
    
    def reset_performance_data(self):
        """Reset all performance tracking data"""
        self.performance_history.clear()
        self.strategy_performance.clear()
        self.query_cache.clear()
        logger.info("Performance data reset")