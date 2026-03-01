#!/bin/bash
# ChiefAgent迁移脚本

set -e  # 遇到错误立即退出

echo "🚀 开始迁移 ChiefAgent → AgentCoordinator"
echo "========================================="

# 创建必要的目录
mkdir -p logs backups analysis

# 步骤1：备份原文件
echo ""
echo "1. 备份原ChiefAgent相关文件..."
BACKUP_DIR="backups/chief_agent_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

find src -name "*.py" -type f -exec grep -l "ChiefAgent" {} \; | while read file; do
    cp "$file" "$BACKUP_DIR/$(basename $file).backup"
done

echo "   ✅ 备份完成，备份目录: $BACKUP_DIR"

# 步骤2：运行使用情况分析
echo ""
echo "2. 分析ChiefAgent使用情况..."
python scripts/analyze_agent_usage.py --agent ChiefAgent --output analysis/chief_usage.json

if [ $? -ne 0 ]; then
    echo "   ⚠️  分析失败，但继续执行..."
fi

# 步骤3：应用适配器模式（如果脚本存在）
if [ -f "scripts/apply_adapter.py" ]; then
    echo ""
    echo "3. 应用适配器模式..."
    python scripts/apply_adapter.py --source ChiefAgent --target AgentCoordinator --dry-run
    
    if [ $? -eq 0 ]; then
        echo "   ✅ 适配器应用成功"
        
        # 询问是否继续实际应用
        read -p "   是否继续实际应用适配器？(y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            python scripts/apply_adapter.py --source ChiefAgent --target AgentCoordinator
        fi
    else
        echo "   ⚠️  适配器应用失败，请检查错误"
    fi
else
    echo "   ⚠️  适配器脚本不存在，跳过此步骤"
fi

# 步骤4：运行兼容性测试（如果测试文件存在）
if [ -f "tests/test_chief_migration.py" ]; then
    echo ""
    echo "4. 运行兼容性测试..."
    python -m pytest tests/test_chief_migration.py -v
    
    if [ $? -eq 0 ]; then
        echo "   ✅ 测试通过"
    else
        echo "   ⚠️  测试失败，请检查测试结果"
        exit 1
    fi
else
    echo "   ⚠️  测试文件不存在，跳过此步骤"
fi

# 步骤5：启动逐步替换监控（如果脚本存在）
if [ -f "scripts/start_gradual_replacement.py" ]; then
    echo ""
    echo "5. 启动逐步替换监控..."
    echo "   初始替换比例: 1%"
    echo "   增加步长: 10%"
    echo "   检查间隔: 2分钟"
    
    python scripts/start_gradual_replacement.py \
        --source ChiefAgent \
        --target AgentCoordinator \
        --initial-rate 0.01 \
        --increase-step 0.1 \
        --check-interval 120 &
    
    REPLACEMENT_PID=$!
    echo "   ✅ 逐步替换监控已启动 (PID: $REPLACEMENT_PID)"
    echo "   📝 PID已保存到 logs/replacement_pid.txt"
    echo $REPLACEMENT_PID > logs/replacement_pid.txt
else
    echo "   ⚠️  逐步替换脚本不存在，跳过此步骤"
fi

echo ""
echo "✅ ChiefAgent迁移已启动"
echo ""
echo "📊 下一步操作："
echo "   1. 监控迁移进度: tail -f logs/migration_ChiefAgent.log"
echo "   2. 查看替换统计: python scripts/check_replacement_stats.py --agent ChiefAgent"
echo "   3. 停止替换监控: kill \$(cat logs/replacement_pid.txt)"
echo ""
echo "📖 详细文档: docs/migration_guide.md"

