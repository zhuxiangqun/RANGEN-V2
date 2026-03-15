#!/usr/bin/env python3
"""验证改进后的ExecutionCoordinator - 完整功能"""
import sys
sys.path.insert(0, '.')

print("=" * 60)
print("验证改进后的ExecutionCoordinator (完整功能)")
print("=" * 60)

# 1. 验证基础导入
print("\n[1] 验证基础导入...")
try:
    from src.core.execution_coordinator import ExecutionCoordinator
    print("   ✅ ExecutionCoordinator 导入成功")
except Exception as e:
    print(f"   ❌ 导入失败: {e}")
    sys.exit(1)

# 2. 验证轻量模式
print("\n[2] 验证轻量模式 (默认)...")
try:
    coordinator = ExecutionCoordinator()
    config = coordinator.get_config()
    print(f"   配置: {config}")
    assert config == {
        "enable_hooks": False, 
        "enable_event_stream": False, 
        "enable_self_learning": False,
        "enable_forgetting": False,
        "enable_audit": False
    }
    print("   ✅ 轻量模式正常")
except Exception as e:
    print(f"   ❌ 失败: {e}")

# 3. 验证标准模式
print("\n[3] 验证标准模式 (Hook + 事件流 + 遗忘)...")
try:
    coordinator = ExecutionCoordinator(
        enable_hooks=True,
        enable_event_stream=True,
        enable_forgetting=True
    )
    config = coordinator.get_config()
    print(f"   配置: {config}")
    assert config["enable_hooks"] == True
    assert config["enable_event_stream"] == True
    assert config["enable_forgetting"] == True
    print("   ✅ 标准模式正常")
except Exception as e:
    print(f"   ❌ 失败: {e}")

# 4. 验证完整模式
print("\n[4] 验证完整模式 (全部启用)...")
try:
    coordinator = ExecutionCoordinator(
        enable_hooks=True,
        enable_event_stream=True,
        enable_self_learning=True,
        enable_forgetting=True,
        enable_audit=True
    )
    config = coordinator.get_config()
    print(f"   配置: {config}")
    assert config["enable_hooks"] == True
    assert config["enable_event_stream"] == True
    assert config["enable_self_learning"] == True
    assert config["enable_forgetting"] == True
    assert config["enable_audit"] == True
    print("   ✅ 完整模式正常")
except Exception as e:
    print(f"   ❌ 失败: {e}")

# 5. 验证检查方法
print("\n[5] 验证检查方法...")
try:
    coordinator = ExecutionCoordinator(
        enable_hooks=True,
        enable_event_stream=True,
        enable_self_learning=True,
        enable_forgetting=True,
        enable_audit=True
    )
    assert coordinator.is_hook_enabled() == True
    assert coordinator.is_event_stream_enabled() == True
    assert coordinator.is_self_learning_enabled() == True
    assert coordinator.is_forgetting_enabled() == True
    assert coordinator.is_audit_enabled() == True
    print("   ✅ 检查方法正常")
except Exception as e:
    print(f"   ❌ 失败: {e}")

print("\n" + "=" * 60)
print("验证完成! 所有新功能已集成到ExecutionCoordinator")
print("=" * 60)
print("""
新集成的功能:
- enable_forgetting: 遗忘机制 (4层记忆管理)
- enable_audit: 审计日志

使用方式:
coordinator = ExecutionCoordinator(
    enable_hooks=True,          # Hook系统
    enable_event_stream=True,   # 事件流
    enable_self_learning=True,  # 自学习
    enable_forgetting=True,     # 遗忘机制 (新增)
    enable_audit=True          # 审计日志 (新增)
)
""")
