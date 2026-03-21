"""
Unified Test Framework
======================

This module provides a unified test framework that connects:
1. Dimension definitions (from dimension_mapping.py)
2. Test execution (from discovery_helper.py)  
3. Coverage reporting

The framework maps each test dimension to its corresponding test function,
enabling comprehensive test coverage analysis.

Usage:
    from src.ui.test_framework import run_dimension_test, generate_coverage_report
    
    # Run test for a specific dimension
    result = run_dimension_test("agent", "reasoning", "test_agent_reasoning")
    
    # Generate coverage report
    report = generate_coverage_report()
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

try:
    from src.ui.dimension_mapping import (
        TOOL_CATEGORY_DIMENSIONS,
        AGENT_CAPABILITY_DIMENSIONS,
        SKILL_TRIGGER_DIMENSIONS,
        TEAM_TYPE_DIMENSIONS,
        WORKFLOW_TYPE_DIMENSIONS,
        SERVICE_TYPE_DIMENSIONS,
        SYSTEM_MODULE_DIMENSIONS,
    )
except ImportError:
    TOOL_CATEGORY_DIMENSIONS = {}
    AGENT_CAPABILITY_DIMENSIONS = {}
    SKILL_TRIGGER_DIMENSIONS = {}
    TEAM_TYPE_DIMENSIONS = {}
    WORKFLOW_TYPE_DIMENSIONS = {}
    SERVICE_TYPE_DIMENSIONS = {}
    SYSTEM_MODULE_DIMENSIONS = {}


class TestStatus(Enum):
    """Test execution status"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    NOT_IMPLEMENTED = "not_implemented"


@dataclass
class DimensionTest:
    """Represents a single dimension test"""
    dimension_name: str
    dimension_key: str
    weight: float
    test_function: Optional[str] = None
    test_cases: List[Dict[str, Any]] = field(default_factory=list)
    status: TestStatus = TestStatus.NOT_IMPLEMENTED
    last_result: Any = None
    error_message: Optional[str] = None


@dataclass
class EntityTestCoverage:
    """Test coverage for an entity type"""
    entity_type: str
    total_dimensions: int = 0
    tested_dimensions: int = 0
    passed_dimensions: int = 0
    failed_dimensions: int = 0
    not_tested_dimensions: int = 0
    coverage_percentage: float = 0.0
    dimensions: List[DimensionTest] = field(default_factory=list)


# ============================================================
# Test Mapping: Dimension -> Test Function
# ============================================================

DIMENSION_TEST_MAPPING: Dict[str, Dict[str, str]] = {
    # System Module Tests (maps dimension_key -> test function in discovery_helper)
    "system_module": {
        "llm": "test_llm",
        "tools": "test_tools", 
        "memory": "test_memory",
        "prompt": "test_prompt",
        "execution_loop": "test_execution_loop",
        "state_management": "test_state_management",
        "error_handling": "test_error_handling",
        "context_management": "test_context_management",
        "cache": "test_cache",
        "security": "test_security",
        "monitoring": "test_monitoring",
        "routing": "test_routing",
        "configuration": "test_configuration",
        "event_system": "test_event_system",
        "skill_registry": "test_skill_registry",
        "gateway": "test_gateway",
        "mcp_server": "test_mcp_server",
        "retrieval": "test_retrieval",
        "cost_control": "test_cost_control",
        "agent_coordinator": "test_agent_coordinator",
        "dependency_injection": "test_dependency_injection",
        "storage": "test_storage",
        "default": "test_system_module",  # Generic test for unknown modules
    },
    
    # Agent Tests
    "agent": {
        "reasoning": "test_agent",
        "planning": "test_agent",
        "conversation": "test_agent",
        "validation": "test_agent",
        "rag": "test_agent",
        "default": "test_agent",  # Generic test for unknown agents
    },
    
    # Tool Tests
    "tool": {
        "calculator": "test_tool",
        "search": "test_tool",
        "retrieval": "test_tool",
        "file": "test_tool",
        "browser": "test_tool",
        "api": "test_tool",
        "reasoning": "test_tool",
        "default": "test_tool",  # Generic test for unknown tools
    },
    
    # Skill Tests
    "skill": {
        "code": "test_skill",
        "document": "test_skill",
        "analysis": "test_skill",
        "writing": "test_skill",
        "default": "test_skill",  # Generic test for unknown skills
    },
    
    # Team Tests
    "team": {
        "testing": "test_team",
        "engineering": "test_team",
        "marketing": "test_team",
        "design": "test_team",
        "default": "test_team",  # Generic test for unknown teams
    },
    
    # Workflow Tests
    "workflow": {
        "execution_coordinator": "test_workflow",
        "audit": "test_workflow",
        "layered": "test_workflow",
        "default": "test_workflow",
    },
    
    # Service Tests
    "service": {
        "llm": "test_service",
        "model": "test_service",
        "cache": "test_service",
        "config": "test_service",
        "skill": "test_service",
        "metrics": "test_service",
        "default": "test_service",
    },
}


# ============================================================
# Coverage Analysis Functions
# ============================================================

def get_dimension_for_entity(entity_type: str, dimension_key: str) -> Optional[Dict[str, Any]]:
    """Get dimension definition for a specific entity type and dimension key"""
    dimension_maps = {
        "system_module": SYSTEM_MODULE_DIMENSIONS,
        "agent": AGENT_CAPABILITY_DIMENSIONS,
        "tool": TOOL_CATEGORY_DIMENSIONS,
        "skill": SKILL_TRIGGER_DIMENSIONS,
        "team": TEAM_TYPE_DIMENSIONS,
        "workflow": WORKFLOW_TYPE_DIMENSIONS,
        "service": SERVICE_TYPE_DIMENSIONS,
    }
    
    dim_map = dimension_maps.get(entity_type, {})
    return dim_map.get(dimension_key, {}).get("dimensions", {})


def get_all_dimensions_for_entity(entity_type: str) -> Dict[str, Dict[str, Any]]:
    """Get all dimension definitions for an entity type"""
    dimension_maps = {
        "system_module": SYSTEM_MODULE_DIMENSIONS,
        "agent": AGENT_CAPABILITY_DIMENSIONS,
        "tool": TOOL_CATEGORY_DIMENSIONS,
        "skill": SKILL_TRIGGER_DIMENSIONS,
        "team": TEAM_TYPE_DIMENSIONS,
        "workflow": WORKFLOW_TYPE_DIMENSIONS,
        "service": SERVICE_TYPE_DIMENSIONS,
    }
    
    return dimension_maps.get(entity_type, {})


def analyze_coverage(entity_type: str) -> EntityTestCoverage:
    """Analyze test coverage for a specific entity type"""
    dimensions = get_all_dimensions_for_entity(entity_type)
    test_mapping = DIMENSION_TEST_MAPPING.get(entity_type, {})
    
    coverage = EntityTestCoverage(
        entity_type=entity_type,
        total_dimensions=len(dimensions)
    )
    
    for dim_key, dim_def in dimensions.items():
        dim_test = DimensionTest(
            dimension_name=dim_def.get("name", dim_key),
            dimension_key=dim_key,
            weight=dim_def.get("weight", 0.0),
            test_function=test_mapping.get(dim_key),
            test_cases=dim_def.get("test_cases", [])
        )
        
        # Check if test exists
        if dim_test.test_function:
            coverage.tested_dimensions += 1
            dim_test.status = TestStatus.SKIPPED  # Has test but not run
        else:
            coverage.not_tested_dimensions += 1
            dim_test.status = TestStatus.NOT_IMPLEMENTED
            
        coverage.dimensions.append(dim_test)
    
    if coverage.total_dimensions > 0:
        coverage.coverage_percentage = (coverage.tested_dimensions / coverage.total_dimensions) * 100
    
    return coverage


def generate_coverage_report() -> Dict[str, EntityTestCoverage]:
    """Generate comprehensive test coverage report for all entity types"""
    report = {}
    
    for entity_type in DIMENSION_TEST_MAPPING.keys():
        coverage = analyze_coverage(entity_type)
        report[entity_type] = coverage
    
    return report


def print_coverage_report():
    """Print human-readable coverage report"""
    report = generate_coverage_report()
    
    print("=" * 80)
    print("TEST COVERAGE REPORT")
    print("=" * 80)
    
    for entity_type, coverage in report.items():
        print(f"\n{entity_type.upper()}")
        print("-" * 40)
        print(f"  Total Dimensions: {coverage.total_dimensions}")
        print(f"  Has Test Function: {coverage.tested_dimensions}")
        print(f"  Coverage: {coverage.coverage_percentage:.1f}%")
        
        if coverage.dimensions:
            print("  Dimensions:")
            for dim in coverage.dimensions:
                status_icon = "✅" if dim.test_function else "❌"
                print(f"    {status_icon} {dim.dimension_key}: {dim.dimension_name}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_dims = sum(c.total_dimensions for c in report.values())
    total_tested = sum(c.tested_dimensions for c in report.values())
    overall_coverage = (total_tested / total_dims * 100) if total_dims > 0 else 0
    
    print(f"Total Dimensions: {total_dims}")
    print(f"Dimensions with Tests: {total_tested}")
    print(f"Overall Coverage: {overall_coverage:.1f}%")


def get_missing_tests(entity_type: str) -> List[str]:
    """Get list of dimensions that don't have test functions"""
    coverage = analyze_coverage(entity_type)
    missing = []
    
    for dim in coverage.dimensions:
        if not dim.test_function:
            missing.append(dim.dimension_key)
    
    return missing


def export_coverage_report(output_path: str = "test_coverage_report.json"):
    """Export coverage report to JSON file"""
    report = generate_coverage_report()
    
    # Convert to serializable format
    serializable_report = {}
    for entity_type, coverage in report.items():
        serializable_report[entity_type] = {
            "total_dimensions": coverage.total_dimensions,
            "tested_dimensions": coverage.tested_dimensions,
            "coverage_percentage": coverage.coverage_percentage,
            "dimensions": [
                {
                    "dimension_key": d.dimension_key,
                    "dimension_name": d.dimension_name,
                    "weight": d.weight,
                    "test_function": d.test_function,
                    "status": d.status.value,
                }
                for d in coverage.dimensions
            ]
        }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(serializable_report, f, indent=2, ensure_ascii=False)
    
    return output_path


if __name__ == "__main__":
    print_coverage_report()
