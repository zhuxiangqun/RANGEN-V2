#!/usr/bin/env python3
"""
Tests for Superpowers-style enforcement components

Tests:
1. HARD_GATE - Design-first gating
2. StrictTDDEnforcer - TDD enforcement
3. BlockingReviewer - Critical issue blocking
4. SubagentDispatcher - Precise context
5. Integration - Full enforcement chain
"""

import pytest
import os
import sys
import tempfile
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestHARDGate:
    """Tests for HARD_GATE component"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.state_file = tempfile.mktemp(suffix='.json')
        yield
        if os.path.exists(self.state_file):
            os.remove(self.state_file)
    
    def test_gate_initialization(self):
        from src.agents.hard_gate import HARD_GATE, GatePhase
        gate = HARD_GATE(state_file=self.state_file)
        assert gate is not None
    
    def test_start_design_phase(self):
        from src.agents.hard_gate import HARD_GATE
        gate = HARD_GATE(state_file=self.state_file)
        gate.reset()
        result = gate.start_design_phase("Test Design", "Description")
        assert result is not None
    
    def test_design_approval_flow(self):
        from src.agents.hard_gate import HARD_GATE
        gate = HARD_GATE(state_file=self.state_file)
        gate.reset()
        gate.start_design_phase("Test", "Test")
        approved = gate.approve_design("test_user")
        assert approved is True
    
    def test_implementation_phase_requires_approval(self):
        from src.agents.hard_gate import HARD_GATE
        gate = HARD_GATE(state_file=self.state_file)
        gate.reset()
        gate.start_design_phase("Test", "Test")
        gate.approve_design("test")
        gate.enter_implementation_phase()
        status = gate.get_status()
        assert status.get("phase") == "implementing"


class TestStrictTDDEnforcer:
    """Tests for StrictTDDEnforcer component"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.state_file = tempfile.mktemp(suffix='.json')
        yield
        if os.path.exists(self.state_file):
            os.remove(self.state_file)
    
    def test_enforcer_initialization(self):
        from src.agents.strict_tdd_enforcer import StrictTDDEnforcer
        enforcer = StrictTDDEnforcer(state_file=self.state_file)
        assert enforcer is not None
    
    def test_cannot_write_without_test(self):
        from src.agents.strict_tdd_enforcer import StrictTDDEnforcer
        enforcer = StrictTDDEnforcer(state_file=self.state_file)
        can_write, reason = enforcer.can_write_production("src/test.py")
        assert can_write is False
    
    def test_can_write_after_registering_test(self):
        from src.agents.strict_tdd_enforcer import StrictTDDEnforcer
        enforcer = StrictTDDEnforcer(state_file=self.state_file)
        enforcer.register_test("tests/test_foo.py", "src/foo.py")
        can_write, _ = enforcer.can_write_production("src/foo.py")
        assert can_write is True


class TestBlockingReviewer:
    """Tests for BlockingReviewer component"""
    
    def test_reviewer_initialization(self):
        from src.agents.blocking_reviewer import BlockingReviewer
        reviewer = BlockingReviewer()
        assert reviewer is not None
    
    def test_security_issues_block(self):
        from src.agents.blocking_reviewer import BlockingReviewer
        reviewer = BlockingReviewer()
        
        code = 'password = "hardcoded123"'
        result = reviewer.review(code, require_tests=False)
        
        assert result.status == "blocked"
        assert any(i.severity == "critical" for i in result.issues)
    
    def test_clean_code_passes(self):
        from src.agents.blocking_reviewer import BlockingReviewer
        reviewer = BlockingReviewer()
        
        code = '''
def add(a, b):
    return a + b
'''
        result = reviewer.review(code, require_tests=False)
        assert result.status in ["pass", "warning"]
    
    def test_missing_tests_blocks(self):
        from src.agents.blocking_reviewer import BlockingReviewer
        reviewer = BlockingReviewer()
        
        code = '''
class DataProcessor:
    def __init__(self):
        self.data = []
    
    def process(self, item):
        self.data.append(item)
'''
        result = reviewer.review(code)
        assert result.blocking_count >= 1


class TestSubagentDispatcher:
    """Tests for SubagentDispatcher component"""
    
    def test_dispatcher_initialization(self):
        from src.agents.subagent_dispatcher import SubagentDispatcher, SubagentType
        dispatcher = SubagentDispatcher()
        assert dispatcher is not None
    
    def test_dispatch_coder(self):
        from src.agents.subagent_dispatcher import SubagentDispatcher, SubagentType
        dispatcher = SubagentDispatcher()
        
        bundle = dispatcher.dispatch("Implement X", SubagentType.CODER)
        
        assert bundle.subagent_type == "coder"
        assert "Task" in bundle.prompt
        assert "Implement X" in bundle.prompt
    
    def test_dispatch_reviewer(self):
        from src.agents.subagent_dispatcher import SubagentDispatcher, SubagentType
        dispatcher = SubagentDispatcher()
        
        bundle = dispatcher.dispatch("Review X", SubagentType.REVIEWER)
        
        assert bundle.subagent_type == "reviewer"
        assert "Review" in bundle.prompt
    
    def test_context_construction(self):
        from src.agents.subagent_dispatcher import SubagentDispatcher
        dispatcher = SubagentDispatcher()
        
        context = dispatcher.construct_context(
            "Test task",
            ["src/agents/base_agent.py"]
        )
        
        assert isinstance(context, str)
        assert len(context) > 0


class TestIntegration:
    """Integration tests for full enforcement chain"""
    
    def test_hard_gate_tdd_chain(self):
        from src.agents.hard_gate import HARD_GATE
        from src.agents.strict_tdd_enforcer import StrictTDDEnforcer
        
        gate = HARD_GATE(state_file=tempfile.mktemp(suffix='.json'))
        enforcer = StrictTDDEnforcer(state_file=tempfile.mktemp(suffix='.json'))
        
        gate.reset()
        gate.start_design_phase("Integration Test", "Testing chain")
        gate.approve_design("test")
        gate.enter_implementation_phase()
        
        can_write_tdd, _ = enforcer.can_write_production("src/test.py")
        assert can_write_tdd is False
    
    def test_review_blocks_security_issues(self):
        from src.agents.blocking_reviewer import BlockingReviewer
        from src.agents.two_stage_reviewer import review_with_blocking
        
        code = '''
import pickle
password = "secret123"
'''
        result = review_with_blocking(code)
        
        assert result["can_merge"] is False
        assert len(result["blocking_issues"]) >= 1
    
    def test_requirement_discovery_hard_gate_integration(self):
        from src.agents.requirement_discovery import (
            RequirementDiscoveryAgent,
            check_hard_gate_for_requirements
        )
        
        can_proceed, reason = check_hard_gate_for_requirements()
        assert isinstance(can_proceed, bool)
        assert isinstance(reason, str)
        
        agent = RequirementDiscoveryAgent()
        result = agent.discover_requirements("Test system")
        assert result is not None
        assert len(result.requirements) > 0


class TestEdgeCases:
    """Edge case tests"""
    
    def test_empty_code_review(self):
        from src.agents.blocking_reviewer import BlockingReviewer
        reviewer = BlockingReviewer()
        
        result = reviewer.review("")
        assert result is not None
    
    def test_none_code_review(self):
        from src.agents.blocking_reviewer import BlockingReviewer
        reviewer = BlockingReviewer()
        
        result = reviewer.review("# comment only")
        assert result is not None
    
    def test_dispatcher_with_empty_files(self):
        from src.agents.subagent_dispatcher import SubagentDispatcher, SubagentType
        dispatcher = SubagentDispatcher()
        
        bundle = dispatcher.dispatch("Task", SubagentType.CODER, relevant_files=[])
        assert bundle.subagent_type == "coder"
        assert len(bundle.relevant_files) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
