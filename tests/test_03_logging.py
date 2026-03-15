#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试日志服务 LoggingService"""

import sys
sys.path.insert(0, '.')

print('=== 测试日志服务 (LoggingService) ===')

try:
    from src.services.logging_service import get_logger, setup_logging
    
    # 测试设置日志
    print('1. 测试设置日志系统...')
    setup_logging()
    print('   日志系统已设置')
    
    # 测试获取日志记录器
    print('2. 测试获取日志记录器...')
    logger = get_logger('test_module')
    print(f'   Logger name: {logger.name}')
    print(f'   Logger level: {logger.level}')
    
    # 测试日志记录
    print('3. 测试日志记录...')
    logger.debug('Debug message')
    logger.info('Info message')
    logger.warning('Warning message')
    logger.error('Error message')
    print('   日志消息已发送')
    
    # 测试不同模块的日志记录器
    print('4. 测试多个模块日志记录器...')
    logger1 = get_logger('module_a')
    logger2 = get_logger('module_b')
    logger1.info('Module A log')
    logger2.info('Module B log')
    print('   多模块日志正常')
    
    print()
    print('=== LoggingService 测试通过 ✓ ===')
    sys.exit(0)
    
except Exception as e:
    print(f'✗ 测试失败: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
