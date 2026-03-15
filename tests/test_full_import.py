#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全面测试 RANGEN 系统所有模块"""

import sys
sys.path.insert(0, '.')

print('=' * 60)
print('RANGEN V2 全面功能测试')
print('=' * 60)

results = []

def test_module(name, import_path):
    """测试模块导入"""
    try:
        module = __import__(import_path)
        print(f'✓ {name:30s} - OK')
        return True, None
    except Exception as e:
        error_msg = str(e)[:60]
        print(f'✗ {name:30s} - {error_msg}')
        return False, error_msg

# 按模块分类测试
modules = {
    # 核心模块
    'agents': 'src.agents',
    'core': 'src.core', 
    'services': 'src.services',
    'interfaces': 'src.interfaces',
    'gateway': 'src.gateway',
    'layers': 'src.layers',
    'api': 'src.api',
    'ui': 'src.ui',
    'bootstrap': 'src.bootstrap',
    'memory': 'src.memory',
    
    # 扩展模块
    'adapters': 'src.adapters',
    'admin': 'src.admin',
    'ai': 'src.ai',
    'config': 'src.config',
    'di': 'src.di',
    'domain': 'src.domain',
    'evolution': 'src.evolution',
    'hands': 'src.hands',
    'hook': 'src.hook',
    'integration': 'src.integration',
    'kms': 'src.kms',
    'knowledge': 'src.knowledge',
    'middleware': 'src.middleware',
    'monitoring': 'src.monitoring',
    'observability': 'src.observability',
    'strategies': 'src.strategies',
    'templates': 'src.templates',
    'tools': 'src.tools',
    'utils': 'src.utils',
    'visualization': 'src.visualization',
}

print('\n[1] 测试主要模块导入')
print('-' * 60)

for name, path in modules.items():
    ok, err = test_module(name, path)
    results.append((name, ok, err))

print('\n[2] 测试关键子模块')
print('-' * 60)

# 关键子模块
submodules = [
    ('agents.base_agent', 'src.agents.base_agent'),
    ('agents.reasoning_agent', 'src.agents.reasoning_agent'),
    ('agents.chief_agent', 'src.agents.chief_agent'),
    ('agents.agent_builder', 'src.agents.agent_builder'),
    ('core.intelligent_orchestrator', 'src.core.intelligent_orchestrator'),
    ('core.reasoning_state', 'src.core.reasoning_state'),
    ('services.config_service', 'src.services.config_service'),
    ('services.logging_service', 'src.services.logging_service'),
    ('services.knowledge_retrieval_service', 'src.services.knowledge_retrieval_service'),
    ('gateway.gateway', 'src.gateway.gateway'),
    ('layers.business_layer', 'src.layers.business_layer'),
    ('utils.unified_centers', 'src.utils.unified_centers'),
]

for name, path in submodules:
    ok, err = test_module(name, path)
    results.append((name, ok, err))

print('\n[3] 测试第三方依赖')
print('-' * 60)

deps = [
    ('langgraph', 'langgraph'),
    ('fastapi', 'fastapi'),
    ('streamlit', 'streamlit'),
    ('pydantic', 'pydantic'),
    ('langchain', 'langchain'),
    ('numpy', 'numpy'),
    ('torch', 'torch'),
]

for name, path in deps:
    ok, err = test_module(name, path)
    results.append((name, ok, err))

# 汇总
print('\n' + '=' * 60)
print('测试结果汇总')
print('=' * 60)

passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)
total = len(results)

print(f'总计: {total}')
print(f'通过: {passed} ({passed/total*100:.1f}%)')
print(f'失败: {failed} ({failed/total*100:.1f}%)')

if failed > 0:
    print('\n失败模块:')
    for name, ok, err in results:
        if not ok:
            print(f'  - {name}: {err}')

print('\n' + '=' * 60)
sys.exit(0 if failed == 0 else 1)
