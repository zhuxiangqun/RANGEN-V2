"""
Test Circuit Breaker Logic
"""

import time
import unittest
from unittest.mock import MagicMock
from src.core.utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState

class TestCircuitBreaker(unittest.TestCase):
    
    def test_state_transitions(self):
        # Setup: threshold=2, timeout=1s
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1, name="TestCB")
        
        # 1. Closed State
        self.assertEqual(cb.state, CircuitState.CLOSED)
        
        # Mock function that fails
        def fail_func():
            raise ValueError("Boom")
            
        # 2. Trigger Failures
        try: cb.call(fail_func)
        except ValueError: pass
        
        try: cb.call(fail_func)
        except ValueError: pass
        
        # Now it should be OPEN
        self.assertEqual(cb.state, CircuitState.OPEN)
        
        # 3. Verify Fast Failure
        with self.assertRaises(CircuitBreakerOpenError):
            cb.call(lambda: "Should not run")
            
        # 4. Wait for Recovery Timeout
        time.sleep(1.1)
        
        # Now calling it should transition to HALF_OPEN (inside call)
        # Mock function that succeeds
        def success_func():
            return "Success"
            
        result = cb.call(success_func)
        self.assertEqual(result, "Success")
        
        # 5. Should be CLOSED again
        self.assertEqual(cb.state, CircuitState.CLOSED)

if __name__ == "__main__":
    unittest.main()
