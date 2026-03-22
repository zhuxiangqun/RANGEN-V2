#!/usr/bin/env python3
"""
检查当前环境变量和配置文件状态
"""

import os
import sys

def check_env_status():
    print('🔍 检查当前API配置状态')
    print('=' * 50)

    # 检查关键环境变量
    env_vars = ['DEEPSEEK_API_KEY', 'DEEPSEEK_BASE_URL', 'DEEPSEEK_MODEL']
    api_configured = False

    for var in env_vars:
        value = os.getenv(var, '')
        if value:
            masked = value[:10] + '...' + value[-4:] if len(value) > 14 else value
            print(f'✅ {var}: {masked} (长度: {len(value)})')
            if var == 'DEEPSEEK_API_KEY' and len(value) > 10:
                api_configured = True
        else:
            print(f'❌ {var}: 未设置')

    # 检查是否有.env文件
    env_files = ['.env', '.env.local', '.env.development', '.env.production']
    found_env_file = False

    print('\\n🔧 检查环境配置文件:')
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f'📄 发现环境文件: {env_file}')
            found_env_file = True
            try:
                with open(env_file, 'r') as f:
                    content = f.read()
                    lines = [line.strip() for line in content.split('\\n') if line.strip() and not line.strip().startswith('#')]
                    deepseek_lines = [line for line in lines if 'DEEPSEEK' in line.upper()]
                    if deepseek_lines:
                        print(f'   📋 包含 {len(deepseek_lines)} 个DeepSeek配置项')
                        for line in deepseek_lines[:3]:  # 只显示前3个
                            print(f'      • {line}')
                        if len(deepseek_lines) > 3:
                            print(f'      ... 还有 {len(deepseek_lines) - 3} 个配置项')
                    else:
                        print(f'   ⚠️  不包含DeepSeek配置项')
            except Exception as e:
                print(f'   ❌ 读取失败: {e}')
        else:
            print(f'❌ {env_file}: 不存在')

    print('\\n📋 状态总结:')
    if api_configured:
        print('✅ API配置就绪，可以开始Agent迁移测试')
    elif found_env_file:
        print('⚠️ 发现.env文件但环境变量未加载')
        print('   💡 请运行: source .env 或手动设置环境变量')
    else:
        print('❌ 未发现API配置')
        print('   💡 请创建.env文件并配置DeepSeek API密钥')

    print('=' * 50)

if __name__ == '__main__':
    check_env_status()
