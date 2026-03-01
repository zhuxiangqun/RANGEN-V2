#!/bin/bash
# RANGEN系统评测配置文件
# 复制此文件并根据需要修改参数

# ========================================
# 样本数量配置
# ========================================
export FRAMES_SAMPLE_COUNT=10         # FRAMES评测样本数 (0=全部样本, >0=指定数量)

# ========================================
# 大规模数据集配置
# ========================================
export FRAMES_BATCH_SIZE=1           # 批处理大小 (最小批次以避免内存压力)
export ULTRA_AGGRESSIVE_MODE=true    # 启用超激进模式
export FRAMES_LARGE_DATASET_MODE=true   # 是否启用大规模数据集模式

# ========================================
# 测试模式配置
# ========================================
export TEST_MODE=false               # 是否启用测试模式 (使用硬编码测试样本)
export USE_TEST_SAMPLES=false        # 是否使用测试样本 (由TEST_MODE自动设置)
export FRAMES_DATA_PATH="data/frames_dataset.json"  # FRAMES数据集文件路径

# ========================================
# 性能测试配置
# ========================================
export PERFORMANCE_TEST_ENABLED=false     # 禁用性能测试以减少内存压力
export MEMORY_MONITORING_ENABLED=true    # 启用内存监控
export CONCURRENCY_TEST_ENABLED=false    # 禁用并发测试以减少内存压力
export STRESS_TEST_ENABLED=false         # 禁用压力测试
export AGGRESSIVE_MEMORY_CLEANUP=true    # 启用激进内存清理
export MEMORY_CLEANUP_INTERVAL=1         # 每1个查询清理一次内存
export MEMORY_THRESHOLD=60               # 内存使用率阈值(%) - 降低到60%
export ULTRA_CLEANUP_INTERVAL=1          # 每1个查询执行超激进清理

# ========================================
# 超时配置
# ========================================
export EVALUATION_TIMEOUT=300            # 评测总超时时间(秒)
export QUERY_TIMEOUT=90                  # 单个查询超时时间(秒)

# ========================================
# 日志配置
# ========================================
export LOG_LEVEL=INFO                    # 日志级别: DEBUG, INFO, WARNING, ERROR
export LOG_RETENTION_DAYS=30             # 日志保留天数

# ========================================
# 输出配置
# ========================================
export OUTPUT_DIR="comprehensive_eval_results"  # 结果输出目录
export REPORT_FORMAT="markdown"          # 报告格式: markdown, json, html

# ========================================
# 使用说明
# ========================================
# 1. 复制此文件: cp config/evaluation_config.sh config/my_config.sh
# 2. 修改参数: vim config/my_config.sh
# 3. 加载配置: source config/my_config.sh
# 4. 运行评测: ./run_comprehensive_eval.sh

echo "✅ 评测配置已加载:"
echo "  - FRAMES样本数: $FRAMES_SAMPLE_COUNT"
echo "  - 性能测试: $PERFORMANCE_TEST_ENABLED"
echo "  - 内存监控: $MEMORY_MONITORING_ENABLED"
echo "  - 并发测试: $CONCURRENCY_TEST_ENABLED"
echo "  - 压力测试: $STRESS_TEST_ENABLED"
