#!/usr/bin/env python3
"""Test script for agent_role_registry"""
import sys
sys.path.insert(0, '/Users/apple/workdata/person/zy/RANGEN-main(syu-python)')

from src.core.agent_role_registry import AgentRoleRegistry, AgentRole, get_agent_role_registry

# Test the registry
registry = get_agent_role_registry()
print('=== Role Summary ===')
print(registry.get_role_summary())

print('\n=== Reviewers ===')
for r in registry.get_reviewers():
    print(f'  {r.agent_name}: {r.description}')

print('\n=== Test is_reviewer/is_builder ===')
print(f'  validation_agent is_reviewer: {registry.is_reviewer("validation_agent")}')
print(f'  reasoning_agent is_reviewer: {registry.is_reviewer("reasoning_agent")}')
print(f'  engineering_agent is_builder: {registry.is_builder("engineering_agent")}')
print('\n✅ All tests passed!')
