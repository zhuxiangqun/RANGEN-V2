#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试核心模块导入"""

import sys
sys.path.insert(0, '.')

print('=== 测试核心模块导入 ===')
modules = [
    ('agents', 'src.agents'),
    ('core', 'src.core'),
    ('services', 'src.services'),
    ('interfaces', 'src.interfaces'),
    ('gateway', 'src.gateway'),
    ('layers', 'src.layers'),
    ('api', 'src.api'),
    ('ui', 'src.ui'),
    ('bootstrap', 'src.bootstrap'),
    ('memory', 'src.memory'),
]

results = []
for name, path in modules:
    try:
        __import__(path)
        print(f'✓ {name} ({path})')
        results.append((name, True, None))
    except Exception as e:
        print(f'✗ {name} ({path}): {e}')
        results.append((name, False, str(e)))

print()
print('=== 汇总 ===')
passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)
print(f'通过: {passed}/{len(modules)}')
print(f'失败: {failed}/{len(modules)}')

if failed > 0:
    print()
    print('失败模块:')
    for name, ok, err in results:
        if not ok:
            print(f'  - {name}: {err}')

sys.exit(0 if failed == 0 else 1)
