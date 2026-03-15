#!/bin/bash

# 分块评测脚本 - 避免段错误
# 每次处理10个样本，块间休息30秒

echo "🛡️ 启动分块评测模式"
echo "每次处理10个样本，块间休息30秒"

# 获取数据集大小
TOTAL_SAMPLES=$(python3 -c "
import json
with open('data/frames_dataset.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    if isinstance(data, list):
        print(len(data))
    elif isinstance(data, dict) and 'samples' in data:
        print(len(data['samples']))
    else:
        print(824)
")

echo "📊 数据集总样本数: $TOTAL_SAMPLES"

# 计算分块
CHUNK_SIZE=10
TOTAL_CHUNKS=$(( (TOTAL_SAMPLES + CHUNK_SIZE - 1) / CHUNK_SIZE ))

echo "📦 将分 $TOTAL_CHUNKS 个块进行评测"

# 创建结果目录
mkdir -p results

# 成功和失败计数
SUCCESSFUL_CHUNKS=0
FAILED_CHUNKS=0

# 处理每个块
for ((i=0; i<TOTAL_CHUNKS; i++)); do
    START_IDX=$((i * CHUNK_SIZE))
    END_IDX=$((START_IDX + CHUNK_SIZE))
    if [ $END_IDX -gt $TOTAL_SAMPLES ]; then
        END_IDX=$TOTAL_SAMPLES
    fi
    
    CHUNK_ID=$((i + 1))
    
    echo "🚀 开始处理第 $CHUNK_ID/$TOTAL_CHUNKS 块: 样本 $START_IDX-$END_IDX"
    
    # 运行评测
    if python3 scripts/simple_chunk_evaluator.py $START_IDX $END_IDX $CHUNK_ID; then
        echo "✅ 第 $CHUNK_ID 块完成"
        SUCCESSFUL_CHUNKS=$((SUCCESSFUL_CHUNKS + 1))
    else
        echo "❌ 第 $CHUNK_ID 块失败"
        FAILED_CHUNKS=$((FAILED_CHUNKS + 1))
    fi
    
    # 块间休息
    if [ $i -lt $((TOTAL_CHUNKS - 1)) ]; then
        echo "😴 块间休息 5 秒，让系统恢复..."
        sleep 5
    fi
done

# 汇总结果
echo "📊 评测结果汇总:"
echo "  ✅ 成功块数: $SUCCESSFUL_CHUNKS/$TOTAL_CHUNKS"
echo "  ❌ 失败块数: $FAILED_CHUNKS/$TOTAL_CHUNKS"
echo "  📈 成功率: $(( SUCCESSFUL_CHUNKS * 100 / TOTAL_CHUNKS ))%"

# 合并结果
if [ $SUCCESSFUL_CHUNKS -gt 0 ]; then
    echo "🔄 合并结果文件..."
    python3 -c "
import json
import glob
import os

# 查找所有结果文件
result_files = glob.glob('results/chunk_*_results.json')

if not result_files:
    print('⚠️ 没有找到结果文件')
    exit(1)

# 合并结果
all_results = []
for file in sorted(result_files):
    with open(file, 'r', encoding='utf-8') as f:
        results = json.load(f)
        all_results.extend(results)

# 保存合并结果
with open('results/merged_evaluation_results.json', 'w', encoding='utf-8') as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False)

print(f'📄 合并结果已保存到: results/merged_evaluation_results.json')
print(f'📊 总评测样本数: {len(all_results)}')
"
    
    echo "🎉 分块评测完成！"
else
    echo "❌ 所有块都失败了"
fi
