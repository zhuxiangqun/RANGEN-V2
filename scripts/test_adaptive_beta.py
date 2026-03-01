#!/usr/bin/env python3
"""
Test script for AdaptiveBetaThreshold
"""

import sys
import os
import logging
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.ddl.adaptive_beta import AdaptiveBetaThreshold

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_adaptive_beta():
    logger.info("🚀 Starting AdaptiveBetaThreshold Test...")
    
    # 1. Initialize
    adaptive = AdaptiveBetaThreshold()
    # Reset for test
    adaptive.thresholds = {"direct_to_hyde": 0.5, "hyde_to_cot": 1.4}
    adaptive.stats = {
        "direct": {"success": 0, "total": 0},
        "hyde": {"success": 0, "total": 0},
        "cot": {"success": 0, "total": 0}
    }
    
    logger.info(f"Initial Thresholds: {adaptive.thresholds}")
    
    # 2. Simulate High Success for Direct Strategy
    logger.info("Simulating 10 successful Direct queries...")
    for _ in range(10):
        adaptive.record_outcome("ddl_direct", success=True)
        
    logger.info(f"Stats after Direct success: {adaptive.stats['direct']}")
    logger.info(f"New Thresholds: {adaptive.thresholds}")
    
    # Expect direct_to_hyde to increase (e.g., 0.5 -> 0.55) to allow more direct queries
    assert adaptive.thresholds["direct_to_hyde"] > 0.5, "Direct threshold should increase on high success"
    
    # 3. Simulate Low Success for HyDE Strategy
    logger.info("Simulating 10 failed HyDE queries...")
    # Reset stats to clear previous adjustment counter effect
    # (In real usage, it accumulates, but for test clarity we just add more)
    for _ in range(10):
        adaptive.record_outcome("ddl_hyde", success=False)
        
    logger.info(f"Stats after HyDE failure: {adaptive.stats['hyde']}")
    logger.info(f"New Thresholds: {adaptive.thresholds}")
    
    # Expect hyde_to_cot to decrease (e.g., 1.4 -> 1.35) to switch to CoT earlier
    assert adaptive.thresholds["hyde_to_cot"] < 1.4, "HyDE threshold should decrease on low success"
    
    logger.info("🎉 All Tests Passed!")

if __name__ == "__main__":
    test_adaptive_beta()
