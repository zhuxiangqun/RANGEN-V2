#!/bin/bash
# 检查测试输出的便捷脚本

echo "=========================================="
echo "🔍 测试输出检查工具"
echo "=========================================="
echo ""

# 检查 pytest 是否安装
if ! python3 -m pytest --version > /dev/null 2>&1; then
    echo "❌ pytest 未安装"
    echo "   请运行: bash scripts/install_pytest.sh"
    exit 1
fi

echo "✅ pytest 已安装"
echo ""

# 显示可用的测试
echo "📋 可用的测试:"
echo "   1. test_state_consistency (最快，约30秒)"
echo "   2. test_simple_query_path (简单查询，约1-2分钟)"
echo "   3. test_complex_query_path (复杂查询，约2-5分钟)"
echo "   4. test_multiple_queries (多查询，约5-15分钟)"
echo "   5. test_concurrent_queries (并发查询，约2-5分钟)"
echo "   6. test_error_recovery (错误恢复，约30秒)"
echo "   7. test_checkpoint_recovery (检查点恢复，约1-2分钟)"
echo "   8. 所有测试 (约10-25分钟)"
echo ""

# 运行最简单的测试
echo "🚀 运行最简单的测试 (test_state_consistency) 来检查输出..."
echo ""

python3 -m pytest tests/test_langgraph_integration.py::TestLangGraphIntegration::test_state_consistency -v -s --tb=short

exit_code=$?

echo ""
echo "=========================================="
if [ $exit_code -eq 0 ]; then
    echo "✅ 测试通过"
else
    echo "❌ 测试失败 (退出代码: $exit_code)"
fi
echo "=========================================="

exit $exit_code

