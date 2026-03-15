#!/usr/bin/env python3
"""
检查当前Python虚拟环境状态
"""

import sys
import os

def check_venv_status():
    print('🔍 Python虚拟环境状态检查')
    print('=' * 40)

    # 方法1: 检查sys.prefix和sys.base_prefix
    print('📍 方法1: sys.prefix 检查')
    print(f'   sys.prefix: {sys.prefix}')
    print(f'   sys.base_prefix: {sys.base_prefix}')

    is_venv = False
    if hasattr(sys, 'real_prefix'):
        is_venv = True
        print('   ✅ 检测到: sys.real_prefix 存在 (传统venv)')
    elif hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix:
        is_venv = True
        print('   ✅ 检测到: sys.base_prefix != sys.prefix (现代venv)')
    else:
        print('   ❌ 未检测到虚拟环境特征')

    print()

    # 方法2: 检查VIRTUAL_ENV环境变量
    print('📍 方法2: 环境变量检查')
    virtual_env = os.environ.get('VIRTUAL_ENV')
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')

    if virtual_env:
        print(f'   ✅ VIRTUAL_ENV: {virtual_env}')
        is_venv = True
    else:
        print('   ❌ VIRTUAL_ENV 环境变量不存在')

    if conda_env:
        print(f'   ✅ CONDA_DEFAULT_ENV: {conda_env}')
        is_venv = True
    else:
        print('   ℹ️  CONDA_DEFAULT_ENV 环境变量不存在')

    print()

    # 方法3: 检查当前目录
    print('📍 方法3: 目录结构检查')
    cwd = os.getcwd()
    print(f'   当前工作目录: {cwd}')

    venv_paths = ['.venv', 'venv', 'env']
    venv_found = False

    for venv_path in venv_paths:
        if os.path.exists(venv_path):
            print(f'   ✅ 发现虚拟环境目录: {venv_path}')
            venv_found = True
            # 检查是否激活
            if venv_path in sys.prefix:
                print(f'   ✅ 当前Python路径包含 {venv_path}')
                is_venv = True
        else:
            print(f'   ❌ 虚拟环境目录不存在: {venv_path}')

    print()

    # 最终结论
    print('🎯 最终结论')
    print('-' * 20)
    if is_venv:
        print('✅ 当前处于虚拟环境中')
        if virtual_env:
            print(f'   虚拟环境路径: {virtual_env}')
        elif '.venv' in sys.prefix or 'venv' in sys.prefix:
            print(f'   虚拟环境路径: (从sys.prefix推断)')
    else:
        print('❌ 当前未处于虚拟环境中')
        if venv_found:
            print('💡 提示: 发现虚拟环境目录，但未激活')
            print('   激活命令: source .venv/bin/activate')

    print()
    print('📋 Python路径信息')
    print(f'   Python可执行文件: {sys.executable}')
    print(f'   Python版本: {sys.version}')

if __name__ == "__main__":
    check_venv_status()