#!/usr/bin/env python3
"""
统一错误处理系统测试脚本

验证错误处理系统的各项功能：
- 错误分类和记录
- 错误恢复策略
- 统计信息收集
- 装饰器使用
"""
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.error_handler import (
    ErrorManager, ErrorCategory, ErrorLevel, 
    error_boundary, handle_error, get_error_manager
)


def test_basic_error_handling():
    """测试基础错误处理功能"""
    print("🧪 测试基础错误处理...")
    
    manager = get_error_manager()
    
    # 测试不同类型的错误
    error1 = manager.handle_error(
        error="Test validation error",
        category=ErrorCategory.VALIDATION,
        level=ErrorLevel.LOW,
        context={"test_id": 1}
    )
    
    error2 = manager.handle_error(
        error=ConnectionError("Network connection failed"),
        category=ErrorCategory.NETWORK,
        level=ErrorLevel.HIGH,
        context={"url": "https://api.example.com"}
    )
    
    error3 = manager.handle_error(
        error=ValueError("Invalid parameter value"),
        category=ErrorCategory.VALIDATION,
        level=ErrorLevel.MEDIUM,
        function="test_function",
        line_number=42
    )
    
    print(f"✅ 创建了3个错误事件: {error1.error_id}, {error2.error_id}, {error3.error_id}")
    
    # 检查统计信息
    stats = manager.get_error_statistics()
    print(f"📊 错误统计: 总计 {stats['total_errors']} 个错误")
    print(f"   - 按分类: {dict(stats['errors_by_category'])}")
    print(f"   - 按级别: {dict(stats['errors_by_level'])}")
    
    return True


def test_error_decorator():
    """测试错误边界装饰器"""
    print("\n🧪 测试错误边界装饰器...")
    
    @error_boundary(
        category=ErrorCategory.BUSINESS,
        level=ErrorLevel.MEDIUM,
        context={"decorator_test": True}
    )
    def failing_function():
        raise RuntimeError("Intentional error for testing")
    
    try:
        failing_function()
        print("❌ 装饰器未能捕获异常")
        return False
    except RuntimeError:
        print("✅ 装饰器成功捕获并处理了异常")
        
        # 检查错误是否被记录
        manager = get_error_manager()
        recent_errors = manager.get_recent_errors(limit=5)
        business_errors = [e for e in recent_errors if e.category == ErrorCategory.BUSINESS]
        
        if business_errors:
            print(f"✅ 错误已正确记录: {business_errors[0].message}")
            return True
        else:
            print("❌ 错误未被正确记录")
            return False


def test_recovery_strategies():
    """测试错误恢复策略"""
    print("\n🧪 测试错误恢复策略...")
    
    manager = get_error_manager()
    call_count = 0
    
    def flaky_operation():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Temporary network failure")
        return "success_after_retries"
    
    # 创建网络错误
    error_event = manager.handle_error(
        error=ConnectionError("Temporary network failure"),
        category=ErrorCategory.NETWORK,
        level=ErrorLevel.MEDIUM,
        context={"operation": "flaky_operation"}
    )
    
    # 尝试恢复
    success, result = manager.try_recover(error_event, flaky_operation)
    
    if success and result == "success_after_retries":
        print(f"✅ 恢复策略成功，尝试了 {call_count} 次")
        return True
    else:
        print(f"❌ 恢复策略失败，尝试了 {call_count} 次")
        return False


def test_error_export():
    """测试错误报告导出"""
    print("\n🧪 测试错误报告导出...")
    
    manager = get_error_manager()
    
    try:
        report_path = manager.export_error_report()
        
        if Path(report_path).exists():
            print(f"✅ 错误报告已导出到: {report_path}")
            
            # 检查报告内容
            import json
            with open(report_path, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            if 'statistics' in report_data and 'recent_errors' in report_data:
                print("✅ 报告格式正确，包含统计信息和错误记录")
                return True
            else:
                print("❌ 报告格式不正确")
                return False
        else:
            print(f"❌ 报告文件未创建: {report_path}")
            return False
            
    except Exception as e:
        print(f"❌ 导出报告时出错: {e}")
        return False


def test_thread_safety():
    """测试线程安全性"""
    print("\n🧪 测试线程安全性...")
    
    import threading
    import time
    
    manager = get_error_manager()
    errors_created = []
    
    def create_errors(thread_id: int):
        for i in range(10):
            error = manager.handle_error(
                error=f"Thread {thread_id} error {i}",
                category=ErrorCategory.SYSTEM,
                level=ErrorLevel.LOW,
                context={"thread_id": thread_id, "error_index": i}
            )
            errors_created.append(error.error_id)
            time.sleep(0.01)  # 小延迟模拟并发
    
    # 创建多个线程同时创建错误
    threads = []
    for i in range(5):
        thread = threading.Thread(target=create_errors, args=(i,))
        threads.append(thread)
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    # 验证所有错误都被正确创建
    expected_count = 50  # 5 threads × 10 errors
    actual_count = len(errors_created)
    unique_count = len(set(errors_created))
    
    if actual_count == expected_count and unique_count == expected_count:
        print(f"✅ 线程安全测试通过，创建了 {actual_count} 个唯一错误")
        return True
    else:
        print(f"❌ 线程安全测试失败，预期 {expected_count} 个，实际 {actual_count} 个，唯一 {unique_count} 个")
        return False


def main():
    """主测试函数"""
    print("🚀 开始测试统一错误处理系统...\n")
    
    tests = [
        ("基础错误处理", test_basic_error_handling),
        ("错误边界装饰器", test_error_decorator),
        ("错误恢复策略", test_recovery_strategies),
        ("错误报告导出", test_error_export),
        ("线程安全性", test_thread_safety),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - 通过")
            else:
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            print(f"❌ {test_name} - 异常: {e}")
    
    print(f"\n📋 测试总结: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！统一错误处理系统工作正常。")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查实现。")
        return 1


if __name__ == "__main__":
    sys.exit(main())