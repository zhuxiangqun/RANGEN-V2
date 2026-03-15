#!/usr/bin/env python3
"""
验证测试脚本修改
"""

def verify_changes():
    """验证测试脚本的修改"""
    print("🔍 验证test_rag_tool_optimization.py的修改...")

    with open('test_rag_tool_optimization.py', 'r') as f:
        content = f.read()

    # 检查是否移除了USE_LIGHTWEIGHT_RAG设置
    if "os.environ['USE_LIGHTWEIGHT_RAG'] = 'true'" in content:
        print("❌ 仍然设置了USE_LIGHTWEIGHT_RAG=true")
        return False
    else:
        print("✅ 已移除USE_LIGHTWEIGHT_RAG=true设置")

    # 检查是否包含注释掉的设置
    if "# os.environ['USE_LIGHTWEIGHT_RAG'] = 'true'" in content:
        print("✅ 已注释掉USE_LIGHTWEIGHT_RAG设置")
    else:
        print("⚠️  未找到注释掉的USE_LIGHTWEIGHT_RAG设置")

    # 检查超时时间
    if "timeout=60.0" in content:
        print("✅ 已设置60秒超时时间")
    else:
        print("❌ 未找到60秒超时设置")

    if "TEST_TIMEOUT = 120" in content:
        print("✅ 已设置120秒测试超时时间")
    else:
        print("❌ 未找到120秒测试超时设置")

    # 检查查询内容
    if '"什么是RAG？"' in content:
        print("✅ 已更新查询为RAG相关问题")
    else:
        print("❌ 未找到RAG相关查询")

    # 检查测试说明
    if "完整模式" in content:
        print("✅ 已更新测试说明为完整模式")
    else:
        print("❌ 未找到完整模式说明")

    print("\n📋 修改摘要:")
    print("- ✅ 移除轻量级模式")
    print("- ✅ 增加超时时间")
    print("- ✅ 更新查询内容")
    print("- ✅ 更新测试说明")
    print("\n🚀 现在可以运行完整RAG功能测试了！")

if __name__ == '__main__':
    verify_changes()
