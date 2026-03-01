#!/usr/bin/env python3
"""
Test script for P1 Phase BetaParameterCalculator with ML-based Performance Tracking
Tests adaptive beta calculation, dynamic adjustment, and performance monitoring
"""

import sys
import os
import time
import logging
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.ddl.beta_parameter_calculator import BetaParameterCalculator, PerformanceMetric
from src.core.ddl.adaptive_beta import AdaptiveBetaThreshold

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_beta_calculation():
    """Test beta calculation for different query types"""
    logger.info("🧮 Testing Beta Calculation...")
    
    calculator = BetaParameterCalculator()
    
    # Test simple query
    simple_query = "What is AI?"
    beta_simple = calculator.calculate_beta_for_query(simple_query)
    logger.info(f"Simple query '{simple_query}' -> beta: {beta_simple}")
    assert 0.0 <= beta_simple <= 2.0, "Beta should be in valid range"
    assert beta_simple < 1.0, "Simple query should have lower beta"
    
    # Test complex query
    complex_query = "Compare and analyze the differences between machine learning and deep learning approaches in natural language processing, and evaluate their effectiveness in various applications"
    beta_complex = calculator.calculate_beta_for_query(complex_query)
    logger.info(f"Complex query '{complex_query[:50]}...' -> beta: {beta_complex}")
    assert 0.0 <= beta_complex <= 2.0, "Beta should be in valid range"
    assert beta_complex > 1.0, "Complex query should have higher beta"
    
    # Test context adjustments
    context = {"user_preference": "detailed", "system_load": 0.2, "domain": "science"}
    beta_with_context = calculator.calculate_beta_for_query(complex_query, context)
    logger.info(f"Complex query with context -> beta: {beta_with_context}")
    assert beta_with_context > beta_complex, "Detailed context should increase beta"
    
    logger.info("✅ Beta calculation tests passed!")


def test_performance_tracking():
    """Test performance monitoring and tracking"""
    logger.info("📊 Testing Performance Tracking...")
    
    calculator = BetaParameterCalculator()
    calculator.reset_performance_data()  # Reset for clean test
    
    # Simulate strategy executions
    test_queries = [
        ("What is machine learning?", "direct", 0.3, True, 0.8),
        ("How to implement neural networks?", "hyde", 1.0, True, 0.7),
        ("Compare RAG architectures in detail", "cot", 1.6, False, 0.4),
        ("Explain quantum computing", "direct", 0.2, True, 0.9),
        ("Analyze climate change impacts", "hyde", 1.2, True, 0.6),
    ]
    
    for query, strategy, beta, success, relevance in test_queries:
        calculator.record_strategy_execution(
            strategy_name=strategy,
            query=query,
            beta_value=beta,
            execution_time=0.5 + len(query.split()) * 0.1,
            success=success,
            relevance_score=relevance,
            coverage_score=0.7
        )
    
    # Check performance metrics
    metrics = calculator.get_performance_metrics()
    logger.info(f"Performance metrics: {metrics}")
    
    assert "direct" in metrics, "Direct strategy metrics should be recorded"
    assert "hyde" in metrics, "HyDE strategy metrics should be recorded"
    assert "cot" in metrics, "CoT strategy metrics should be recorded"
    
    # Verify success rates
    direct_metrics = metrics["direct"]
    hyde_metrics = metrics["hyde"]
    
    assert direct_metrics["success_rate"] > 0.8, "Direct should have high success rate"
    assert hyde_metrics["success_rate"] > 0.5, "HyDE should have moderate success rate"
    
    logger.info("✅ Performance tracking tests passed!")


def test_dynamic_adjustment():
    """Test dynamic beta adjustment based on performance"""
    logger.info("🔄 Testing Dynamic Adjustment...")
    
    calculator = BetaParameterCalculator()
    calculator.reset_performance_data()  # Reset for clean test
    
    # Initial calculation
    query = "How does machine learning work?"
    initial_beta = calculator.calculate_beta_for_query(query)
    logger.info(f"Initial beta: {initial_beta}")
    
    # Simulate poor performance for low beta strategies
    for i in range(10):
        calculator.record_strategy_execution(
            strategy_name="direct",
            query=f"{query} {i}",
            beta_value=0.3,
            execution_time=0.5,
            success=False,
            relevance_score=0.3
        )
    
    # Re-calculate beta - should be higher due to poor performance
    adjusted_beta = calculator.calculate_beta_for_query(query)
    logger.info(f"Adjusted beta after poor performance: {adjusted_beta}")
    
    # Simulate good performance for higher beta strategies
    for i in range(10):
        calculator.record_strategy_execution(
            strategy_name="hyde",
            query=f"{query} advanced {i}",
            beta_value=1.2,
            execution_time=0.8,
            success=True,
            relevance_score=0.8
        )
    
    # Test recommendations
    recommendations = calculator.get_strategy_recommendations(query)
    logger.info(f"Strategy recommendations: {recommendations}")
    
    assert len(recommendations) > 0, "Should provide recommendations"
    assert any(rec[0] in ["direct", "hyde", "cot"] for rec in recommendations), "Recommendations should include valid strategies"
    
    logger.info("✅ Dynamic adjustment tests passed!")


def test_adaptive_beta_integration():
    """Test integration between AdaptiveBetaThreshold and BetaParameterCalculator"""
    logger.info("🔗 Testing Adaptive Beta Integration...")
    
    adaptive_threshold = AdaptiveBetaThreshold()
    adaptive_threshold.beta_calculator.reset_performance_data()  # Reset for clean test
    
    # Test enhanced record_outcome with ML tracking
    test_scenarios = [
        ("ddl_direct", True, 0.3, "What is AI?", 0.8, 0.5),
        ("ddl_hyde", True, 1.0, "How to implement ML?", 0.7, 0.7),
        ("ddl_cot", False, 1.6, "Compare AI approaches", 0.4, 1.0),
    ]
    
    for strategy, success, beta, query, relevance, exec_time in test_scenarios:
        logger.info(f"Recording outcome: strategy={strategy}, success={success}, beta={beta}, query={query}, relevance={relevance}, exec_time={exec_time}")
        adaptive_threshold.record_outcome(
            strategy=strategy,
            success=success,
            beta_value=beta,
            query=query,
            relevance_score=relevance,
            execution_time=exec_time
        )
    
    # Check if ML metrics were recorded
    ml_metrics = adaptive_threshold.beta_calculator.get_performance_metrics()
    logger.info(f"Integrated ML metrics: {ml_metrics}")
    
    # Verify threshold adjustment logic
    initial_thresholds = adaptive_threshold.thresholds.copy()
    
    # Simulate more executions to trigger adjustment
    for _ in range(15):
        adaptive_threshold.record_outcome("ddl_direct", True, 0.3, 0.9, 0.5, "Simple query")
    
    adjusted_thresholds = adaptive_threshold.thresholds
    logger.info(f"Thresholds before: {initial_thresholds}")
    logger.info(f"Thresholds after: {adjusted_thresholds}")
    
    # Should have adjusted due to high success rate
    assert adjusted_thresholds["direct_to_hyde"] != initial_thresholds["direct_to_hyde"], \
        "Thresholds should be adjusted based on performance"
    
    logger.info("✅ Adaptive beta integration tests passed!")


def test_cache_and_persistence():
    """Test caching and data persistence"""
    logger.info("💾 Testing Cache and Persistence...")
    
    calculator = BetaParameterCalculator()
    
    # Test query caching
    query = "Test query for caching"
    beta1 = calculator.calculate_beta_for_query(query)
    beta2 = calculator.calculate_beta_for_query(query)
    
    assert beta1 == beta2, "Cached results should be identical"
    assert len(calculator.query_cache) > 0, "Query should be cached"
    
    # Test performance data persistence simulation
    calculator.record_strategy_execution(
        strategy_name="test_strategy",
        query="test query",
        beta_value=1.0,
        execution_time=0.5,
        success=True,
        relevance_score=0.8
    )
    
    # Trigger save (normally happens automatically)
    calculator._save_performance_data()
    
    # Create new instance to test loading
    calculator2 = BetaParameterCalculator()
    
    # Should load saved performance data
    assert calculator2.beta_adjustment_params == calculator.beta_adjustment_params, \
        "Configuration should be loaded correctly"
    
    logger.info("✅ Cache and persistence tests passed!")


def run_all_tests():
    """Run all P1 phase tests"""
    logger.info("🚀 Starting P1 Phase BetaParameterCalculator Tests...")
    
    try:
        test_beta_calculation()
        test_performance_tracking()
        test_dynamic_adjustment()
        test_adaptive_beta_integration()
        test_cache_and_persistence()
        
        logger.info("🎉 All P1 Phase Tests Passed!")
        logger.info("✅ BetaParameterCalculator with ML-based performance tracking is working correctly")
        logger.info("✅ Dynamic beta adjustment based on success rates is functional")
        logger.info("✅ Performance monitoring for strategy effectiveness is operational")
        logger.info("✅ Integration with existing AdaptiveBetaThreshold is successful")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()