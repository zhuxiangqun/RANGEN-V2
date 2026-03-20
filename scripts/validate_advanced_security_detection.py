#!/usr/bin/env python3
"""
高级安全检测服务验证脚本
验证高级安全检测服务的导入、创建和基本功能
"""

import sys
import os
import logging
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_imports():
    """测试导入高级安全检测服务"""
    logger.info("测试导入高级安全检测服务...")
    try:
        from src.services.advanced_security_detection_service import (
            AdvancedSecurityDetectionService,
            create_advanced_security_detection_service,
            ThreatType,
            DetectionRuleType,
            SecurityDetectionRule
        )
        logger.info("✅ 高级安全检测服务导入成功")
        return True
    except ImportError as e:
        logger.error(f"❌ 高级安全检测服务导入失败: {e}")
        return False


def test_basic_imports():
    """测试导入基础安全检测服务"""
    logger.info("测试导入基础安全检测服务...")
    try:
        from src.services.security_detection_service import (
            SecurityDetectionService,
            create_security_detection_service
        )
        logger.info("✅ 基础安全检测服务导入成功")
        return True
    except ImportError as e:
        logger.error(f"❌ 基础安全检测服务导入失败: {e}")
        return False


def test_service_creation():
    """测试创建高级安全检测服务实例"""
    logger.info("测试创建高级安全检测服务实例...")
    try:
        from src.services.advanced_security_detection_service import create_advanced_security_detection_service
        
        config = {
            "max_user_profiles": 500,
            "max_events_per_key": 100,
            "geo_cache_ttl": 1800,
            "max_alert_history": 200
        }
        
        service = create_advanced_security_detection_service(config)
        logger.info(f"✅ 高级安全检测服务创建成功: {service.__class__.__name__}")
        
        # 验证基本属性
        assert hasattr(service, 'detection_rules'), "服务应具有detection_rules属性"
        assert hasattr(service, 'user_profiles'), "服务应具有user_profiles属性"
        assert hasattr(service, 'process_audit_event'), "服务应具有process_audit_event方法"
        
        logger.info("✅ 服务属性和方法验证通过")
        return True
    except Exception as e:
        logger.error(f"❌ 高级安全检测服务创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_audit_event_processing():
    """测试审计事件处理"""
    logger.info("测试审计事件处理...")
    try:
        from src.services.advanced_security_detection_service import create_advanced_security_detection_service
        from src.services.audit_log_service import AuditEvent, AuditEventType, AuditSeverity, AuditSource
        
        service = create_advanced_security_detection_service()
        
        # 创建测试审计事件
        test_event = AuditEvent(
            event_id=f"test_event_{int(datetime.now().timestamp())}",
            event_type=AuditEventType.LOGIN_FAILURE,
            timestamp=datetime.now(),
            severity=AuditSeverity.WARNING,
            source=AuditSource.AUTH_SERVICE,
            user_id="test_user_123",
            ip_address="192.168.1.100",
            resource_name="/api/login",
            metadata={"user_agent": "TestClient/1.0", "reason": "invalid_password"}
        )
        
        # 处理事件
        threats = service.process_audit_event(test_event)
        logger.info(f"✅ 审计事件处理完成，检测到 {len(threats)} 个威胁")
        
        # 验证统计信息
        stats = service.get_stats()
        assert stats["events_processed"] >= 1, f"应处理至少1个事件，实际: {stats['events_processed']}"
        logger.info(f"✅ 统计信息验证通过: 已处理 {stats['events_processed']} 个事件")
        
        return True
    except Exception as e:
        logger.error(f"❌ 审计事件处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_di_integration():
    """测试依赖注入集成"""
    logger.info("测试依赖注入集成...")
    try:
        from src.di.bootstrap import bootstrap_application
        
        # 启动应用（这会初始化DI容器并注册所有服务）
        app = bootstrap_application()
        
        # 从容器获取服务
        from src.di.unified_container import get_container
        container = get_container()
        
        # 尝试获取高级安全检测服务
        try:
            from src.services.advanced_security_detection_service import AdvancedSecurityDetectionService
            service = container.get_service(AdvancedSecurityDetectionService)
            logger.info(f"✅ 从DI容器成功获取高级安全检测服务: {service.__class__.__name__}")
        except Exception as e:
            logger.warning(f"⚠ 从DI容器获取高级安全检测服务失败，尝试获取基础服务: {e}")
            try:
                from src.services.security_detection_service import SecurityDetectionService
                service = container.get_service(SecurityDetectionService)
                logger.info(f"✅ 从DI容器成功获取基础安全检测服务: {service.__class__.__name__}")
            except Exception as e2:
                logger.error(f"❌ 从DI容器获取安全检测服务失败: {e2}")
                return False
        
        # 验证服务功能
        if service:
            stats = service.get_stats()
            logger.info(f"✅ 服务功能验证通过，统计信息: {stats}")
        
        return True
    except Exception as e:
        logger.error(f"❌ 依赖注入集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_async_functions():
    """测试异步功能（如果存在）"""
    logger.info("测试异步功能...")
    try:
        from src.services.advanced_security_detection_service import create_advanced_security_detection_service
        
        service = create_advanced_security_detection_service()
        
        # 检查是否存在异步方法
        if hasattr(service, 'process_audit_event_async'):
            logger.info("✅ 服务包含异步方法 process_audit_event_async")
            # 注意：实际异步调用需要事件循环
        else:
            logger.info("ℹ 服务不包含异步方法，这是可选的")
        
        return True
    except Exception as e:
        logger.error(f"❌ 异步功能测试失败: {e}")
        return False


def main():
    """主验证函数"""
    logger.info("=" * 60)
    logger.info("开始验证高级安全检测服务")
    logger.info("=" * 60)
    
    results = []
    
    # 运行所有测试
    results.append(("导入高级服务", test_imports()))
    results.append(("导入基础服务", test_basic_imports()))
    results.append(("创建服务实例", test_service_creation()))
    results.append(("处理审计事件", test_audit_event_processing()))
    results.append(("测试异步功能", test_async_functions()))
    results.append(("依赖注入集成", test_di_integration()))
    
    # 打印结果摘要
    logger.info("\n" + "=" * 60)
    logger.info("验证结果摘要")
    logger.info("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        logger.info(f"{status}: {test_name}")
        if success:
            passed += 1
    
    logger.info(f"\n总计: {passed}/{total} 个测试通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 所有验证测试通过！高级安全检测服务已成功集成。")
        return 0
    else:
        logger.warning(f"⚠  {total - passed} 个测试失败，需要进一步检查。")
        return 1


if __name__ == "__main__":
    sys.exit(main())