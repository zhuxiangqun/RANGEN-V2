#!/bin/bash
# 修复 google-auth 版本冲突的快速脚本

set -e

echo "=========================================="
echo "修复 google-auth 版本冲突"
echo "=========================================="
echo ""

# 检查当前版本
CURRENT_VERSION=$(pip show google-auth 2>/dev/null | grep "Version:" | awk '{print $2}' || echo "未安装")
echo "当前 google-auth 版本: $CURRENT_VERSION"

if [ "$CURRENT_VERSION" != "未安装" ]; then
    MAJOR=$(echo $CURRENT_VERSION | cut -d. -f1)
    MINOR=$(echo $CURRENT_VERSION | cut -d. -f2)
    
    if [ "$MAJOR" -gt 2 ] || ([ "$MAJOR" -eq 2 ] && [ "$MINOR" -ge 42 ]); then
        echo "⚠️  检测到版本冲突: google-auth $CURRENT_VERSION >= 2.42.0"
        echo "   正在降级到兼容版本..."
        pip install "google-auth>=2.15.0,<2.42.0" --force-reinstall
        echo "✅ google-auth 已降级到兼容版本"
        
        # 验证
        NEW_VERSION=$(pip show google-auth 2>/dev/null | grep "Version:" | awk '{print $2}')
        echo "   新版本: $NEW_VERSION"
    else
        echo "✅ google-auth 版本兼容: $CURRENT_VERSION"
    fi
else
    echo "⚠️  google-auth 未安装"
fi

echo ""

