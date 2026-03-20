#!/usr/bin/env python3
"""
显示.env文件内容
"""

import os

def show_env_content():
    try:
        with open('.env', 'r') as f:
            content = f.read()
            print('📄 .env文件内容:')
            print('=' * 50)
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    if 'API_KEY' in line.upper():
                        # 隐藏API密钥
                        if '=' in line:
                            key, value = line.split('=', 1)
                            masked_value = value[:10] + '...' + value[-4:] if len(value) > 14 else value
                            print(f'{i:2d}: {key}={masked_value}')
                        else:
                            print(f'{i:2d}: {line}')
                    else:
                        print(f'{i:2d}: {line}')
                elif line.startswith('#'):
                    print(f'{i:2d}: {line}')
            print('=' * 50)

            # 检查DeepSeek配置
            deepseek_lines = [line for line in lines if 'DEEPSEEK' in line.upper() and '=' in line]
            print(f'\n📊 DeepSeek配置项数量: {len(deepseek_lines)}')

            # 检查环境变量是否已加载
            print('\n🔍 环境变量状态:')
            env_vars = ['DEEPSEEK_API_KEY', 'DEEPSEEK_BASE_URL', 'DEEPSEEK_MODEL']
            for var in env_vars:
                value = os.getenv(var, '')
                if value:
                    masked = value[:10] + '...' + value[-4:] if len(value) > 14 else value
                    print(f'✅ {var}: {masked} (已加载)')
                else:
                    print(f'❌ {var}: 未加载')

    except Exception as e:
        print(f'❌ 读取.env文件失败: {e}')

if __name__ == '__main__':
    show_env_content()
