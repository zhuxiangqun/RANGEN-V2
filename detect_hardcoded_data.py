#!/usr/bin/env python3
"""
硬编码数据检测脚本
检测魔法数字、硬编码路径、硬编码URL、硬编码凭据等
"""

import os
import re
import subprocess
from typing import List, Dict, Any

def detect_hardcoded_data() -> Dict[str, Any]:
    """检测硬编码数据"""
    results = {
        'magic_numbers': [],
        'hardcoded_paths': [],
        'hardcoded_urls': [],
        'hardcoded_credentials': [],
        'simulated_data': []
    }
    
    # 搜索魔法数字
    print("🔍 检测魔法数字...")
    result = subprocess.run(['grep', '-r', '-n', '--include=*.py', '-E', r'\b(0|1|2|3|4|5|6|7|8|9)+\b', 'src/'], capture_output=True, text=True)
    if result.stdout:
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if any(pattern in line for pattern in ['timeout', 'port', 'size', 'limit', 'max', 'min', 'count', 'retry', 'delay', 'threshold']):
                results['magic_numbers'].append(line)
    
    # 搜索硬编码路径
    print("🔍 检测硬编码路径...")
    result = subprocess.run(['grep', '-r', '-n', '--include=*.py', '-E', r'[\"\'][/\\\\][^\"\']*[\"\']', 'src/'], capture_output=True, text=True)
    if result.stdout:
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if any(pattern in line for pattern in ['/path/', '/tmp/', '/var/', '/usr/', 'C:\\\\', 'D:\\\\', '/home/', '/opt/']):
                results['hardcoded_paths'].append(line)
    
    # 搜索硬编码URL
    print("🔍 检测硬编码URL...")
    result = subprocess.run(['grep', '-r', '-n', '--include=*.py', '-E', r'https?://[^\"\']*', 'src/'], capture_output=True, text=True)
    if result.stdout:
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if 'http' in line:
                results['hardcoded_urls'].append(line)
    
    # 搜索硬编码凭据
    print("🔍 检测硬编码凭据...")
    result = subprocess.run(['grep', '-r', '-n', '--include=*.py', '-E', r'[\"\'][a-zA-Z0-9]{8,}[\"\']', 'src/'], capture_output=True, text=True)
    if result.stdout:
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if any(pattern in line for pattern in ['password', 'secret', 'key', 'token', 'api_key', 'credential']):
                results['hardcoded_credentials'].append(line)
    
    # 搜索模拟数据
    print("🔍 检测模拟数据...")
    result = subprocess.run(['grep', '-r', '-n', '--include=*.py', '-i', 'simulated\|test_data\|mock\|fake\|dummy', 'src/'], capture_output=True, text=True)
    if result.stdout:
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if any(pattern in line.lower() for pattern in ['simulated', 'test_data', 'mock', 'fake', 'dummy']):
                results['simulated_data'].append(line)
    
    return results

def main():
    """主函数"""
    print("🚀 开始检测硬编码数据...")
    results = detect_hardcoded_data()
    
    print(f"\n📊 检测结果:")
    print(f"魔法数字: {len(results['magic_numbers'])}个")
    print(f"硬编码路径: {len(results['hardcoded_paths'])}个")
    print(f"硬编码URL: {len(results['hardcoded_urls'])}个")
    print(f"硬编码凭据: {len(results['hardcoded_credentials'])}个")
    print(f"模拟数据: {len(results['simulated_data'])}个")
    
    print(f"\n🔍 详细结果:")
    
    if results['magic_numbers']:
        print(f"\n魔法数字示例:")
        for i, line in enumerate(results['magic_numbers'][:5]):
            print(f"{i+1}. {line}")
    
    if results['hardcoded_paths']:
        print(f"\n硬编码路径示例:")
        for i, line in enumerate(results['hardcoded_paths'][:5]):
            print(f"{i+1}. {line}")
    
    if results['hardcoded_urls']:
        print(f"\n硬编码URL示例:")
        for i, line in enumerate(results['hardcoded_urls'][:5]):
            print(f"{i+1}. {line}")
    
    if results['hardcoded_credentials']:
        print(f"\n硬编码凭据示例:")
        for i, line in enumerate(results['hardcoded_credentials'][:5]):
            print(f"{i+1}. {line}")
    
    if results['simulated_data']:
        print(f"\n模拟数据示例:")
        for i, line in enumerate(results['simulated_data'][:5]):
            print(f"{i+1}. {line}")
    
    # 保存结果到文件
    with open('hardcoded_data_report.txt', 'w', encoding='utf-8') as f:
        f.write("硬编码数据检测报告\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"魔法数字: {len(results['magic_numbers'])}个\n")
        f.write(f"硬编码路径: {len(results['hardcoded_paths'])}个\n")
        f.write(f"硬编码URL: {len(results['hardcoded_urls'])}个\n")
        f.write(f"硬编码凭据: {len(results['hardcoded_credentials'])}个\n")
        f.write(f"模拟数据: {len(results['simulated_data'])}个\n\n")
        
        for category, items in results.items():
            if items:
                f.write(f"\n{category.upper()}:\n")
                f.write("-" * 30 + "\n")
                for item in items:
                    f.write(f"{item}\n")
    
    print(f"\n✅ 检测完成！结果已保存到 hardcoded_data_report.txt")

if __name__ == "__main__":
    main()
