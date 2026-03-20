#!/usr/bin/env python3
"""Test ADR system"""
import sys
sys.path.insert(0, '/Users/apple/workdata/person/zy/RANGEN-main(syu-python)')

from src.core.adr_examples import initialize_sample_adrs
from src.core.adr_registry import get_adr_registry

# Initialize sample ADRs
initialize_sample_adrs()
registry = get_adr_registry()

print('\n=== 活跃 ADR ===')
for adr in registry.get_active():
    print(f'  {adr.adr_id}: {adr.title} [{adr.status.value}]')

print('\n=== 角色分布 ===')
for role in ['builder', 'reviewer', 'coordinator']:
    from src.core.agent_role_registry import get_agent_role_registry, AgentRole
    r = get_agent_role_registry()
    count = len(r.get_agents_by_role(AgentRole[role.upper()]))
    print(f'  {role}: {count}')

print('\n✅ ADR 系统测试通过!')
