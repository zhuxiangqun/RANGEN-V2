#!/bin/bash
# 修复模型缓存脚本 - 清理损坏的embedding模型缓存

echo "🔧 开始修复模型缓存..."

MODEL_NAME="${LOCAL_EMBEDDING_MODEL:-all-mpnet-base-v2}"
CACHE_DIR="$HOME/.cache/huggingface/hub"
MODEL_CACHE_PATH="$CACHE_DIR/models--sentence-transformers--${MODEL_NAME//\//--}"

echo "📋 模型名称: $MODEL_NAME"
echo "📁 缓存路径: $MODEL_CACHE_PATH"

if [ -d "$MODEL_CACHE_PATH" ]; then
    echo "⚠️  发现模型缓存，准备清理..."
    echo "   路径: $MODEL_CACHE_PATH"
    
    # 询问用户确认
    read -p "是否清理此缓存？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$MODEL_CACHE_PATH"
        echo "✅ 已清理模型缓存: $MODEL_CACHE_PATH"
        echo "💡 下次运行时，系统会自动重新下载模型"
    else
        echo "❌ 取消清理"
    fi
else
    echo "ℹ️  未找到模型缓存，无需清理"
fi

echo ""
echo "📝 其他可用的模型缓存："
ls -d "$CACHE_DIR"/models--sentence-transformers--* 2>/dev/null | head -5 || echo "   无"

echo ""
echo "✅ 修复脚本执行完成"
