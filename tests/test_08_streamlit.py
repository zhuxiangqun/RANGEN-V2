#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 Streamlit Web UI"""

import sys
sys.path.insert(0, '.')

print('=== 测试 Streamlit Web UI ===')

try:
    # 测试导入 Streamlit
    print('1. 测试导入 Streamlit...')
    import streamlit as st
    print(f'   ✓ Streamlit 版本: {st.__version__}')
    
    # 测试导入 UI 应用
    print('2. 测试导入 UI 应用模块...')
    from src.ui import app as ui_app
    print('   ✓ UI 应用模块导入成功')
    
    # 检查 UI 目录结构
    print('3. 检查 UI 目录...')
    import os
    ui_files = []
    for root, dirs, files in os.walk('src/ui'):
        for f in files:
            if f.endswith('.py'):
                ui_files.append(os.path.join(root, f))
    print(f'   UI 文件数量: {len(ui_files)}')
    print(f'   文件列表: {[os.path.basename(f) for f in ui_files]}')
    
    print()
    print('=== Streamlit Web UI 测试通过 ✓ ===')
    sys.exit(0)
    
except Exception as e:
    print(f'✗ 测试失败: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
