#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全面测试 RANGEN 系统 - 746个文件抽样测试"""

import sys
import os
from pathlib import Path

sys.path.insert(0, '.')

print('=' * 70)
print('RANGEN V2 全面功能测试 (746 Python 文件)')
print('=' * 70)

results = {}
all_passed = True

def test_import(module_path, name=None):
    """测试模块导入"""
    global all_passed
    try:
        parts = module_path.split('.')
        m = __import__(module_path, fromlist=[parts[-1]])
        return True, None
    except Exception as e:
        all_passed = False
        return False, str(e)[:50]

# 按模块分组测试关键文件
test_groups = {
    # Core 模块 (220 files) - 测试关键文件
    'core (220 files)': [
        'src.core.intelligent_orchestrator',
        'src.core.langgraph_unified_workflow',
        'src.core.reasoning_state',
        'src.core.service_registry',
        'src.core.cache_system',
        'src.core.execution_coordinator',
        'src.core.dynamic_config_system',
        'src.core.adaptive_optimizer',
    ],
    
    # Utils 模块 (154 files)
    'utils (154 files)': [
        'src.utils.unified_centers',
        'src.utils.unified_complexity_model_service',
        'src.utils.llm_factory',
    ],
    
    # Agents 模块 (78 files)
    'agents (78 files)': [
        'src.agents.base_agent',
        'src.agents.chief_agent',
        'src.agents.reasoning_agent',
        'src.agents.agent_builder',
        'src.agents.agent_factory',
        'src.agents.tools.tool_registry',
        'src.agents.tools.retrieval_tool',
    ],
    
    # Services 模块 (61 files)
    'services (61 files)': [
        'src.services.config_service',
        'src.services.logging_service',
        'src.services.knowledge_retrieval_service',
        'src.services.reasoning_service',
        'src.services.faiss_service',
        'src.services.model_service',
    ],
    
    # Gateway 模块 (27 files)
    'gateway (27 files)': [
        'src.gateway.gateway',
        'src.gateway.server',
        'src.gateway.agents.agent_runtime',
    ],
    
    # API 模块 (24 files)
    'api (24 files)': [
        'src.api.models',
        'src.api.routes',
    ],
    
    # AI 模块 (21 files)
    'ai (21 files)': [
        'src.ai.engines.llm_engine',
    ],
    
    # Adapters 模块 (18 files)
    'adapters (18 files)': [
        'src.adapters.model_adapter',
    ],
    
    # 其他重要模块
    'layers (8 files)': [
        'src.layers.business_layer',
    ],
    'interfaces (8 files)': [
        'src.interfaces.agent',
        'src.interfaces.tool',
    ],
    'visualization (11 files)': [
        'src.visualization.servers.trace_server',
    ],
    'monitoring (4 files)': [
        'src.monitoring.performance_monitor',
    ],
    'observability (3 files)': [
        'src.observability.opentelemetry_integration',
    ],
}

total_tests = 0
total_passed = 0

for group_name, tests in test_groups.items():
    print(f'\n[{group_name}]')
    print('-' * 70)
    for module_path in tests:
        name = module_path.split('.')[-1]
        ok, err = test_import(module_path, name)
        total_tests += 1
        if ok:
            total_passed += 1
            print(f'  ✓ {name}')
        else:
            print(f'  ✗ {name}: {err}')

# 汇总
print('\n' + '=' * 70)
print('测试结果汇总')
print('=' * 70)
print(f'总计测试: {total_tests}')
print(f'通过: {total_passed} ({total_passed/total_tests*100:.1f}%)')
print(f'失败: {total_tests - total_passed} ({(total_tests-total_passed)/total_tests*100:.1f}%)')

if not all_passed:
    print('\n⚠ 存在失败模块，请检查依赖或代码问题')
    sys.exit(1)
else:
    print('\n✓ 所有关键模块测试通过!')
    sys.exit(0)
