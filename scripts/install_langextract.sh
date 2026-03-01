#!/bin/bash
# LangExtract 安装脚本
# 解决依赖冲突问题

set -e

echo "=========================================="
echo "LangExtract 安装脚本"
echo "=========================================="
echo ""

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3"
    exit 1
fi

echo "✅ Python 版本: $(python3 --version)"
echo ""

# 检查当前 google-auth 版本
echo "📦 检查当前依赖版本..."
GOOGLE_AUTH_VERSION=$(pip show google-auth 2>/dev/null | grep "Version:" | awk '{print $2}' || echo "未安装")
GOOGLE_AUTH_OAUTHLIB_VERSION=$(pip show google-auth-oauthlib 2>/dev/null | grep "Version:" | awk '{print $2}' || echo "未安装")

echo "   google-auth: $GOOGLE_AUTH_VERSION"
echo "   google-auth-oauthlib: $GOOGLE_AUTH_OAUTHLIB_VERSION"
echo ""

# 检查版本冲突
if [ "$GOOGLE_AUTH_VERSION" != "未安装" ]; then
    # 提取主版本号
    MAJOR_VERSION=$(echo $GOOGLE_AUTH_VERSION | cut -d. -f1)
    MINOR_VERSION=$(echo $GOOGLE_AUTH_VERSION | cut -d. -f2)
    
    # 检查是否 >= 2.42.0
    if [ "$MAJOR_VERSION" -gt 2 ] || ([ "$MAJOR_VERSION" -eq 2 ] && [ "$MINOR_VERSION" -ge 42 ]); then
        echo "⚠️  检测到版本冲突: google-auth $GOOGLE_AUTH_VERSION >= 2.42.0"
        echo "   google-auth-oauthlib 1.2.3 需要 google-auth<2.42.0"
        echo ""
        echo "🔧 解决方案："
        echo "   方案1: 降级 google-auth（推荐）"
        echo "   方案2: 升级 google-auth-oauthlib"
        echo ""
        read -p "选择方案 (1/2，默认1): " choice
        choice=${choice:-1}
        
        if [ "$choice" == "1" ]; then
            echo "📦 降级 google-auth 到兼容版本..."
            pip install "google-auth>=2.15.0,<2.42.0" --force-reinstall
            echo "✅ google-auth 已降级"
        elif [ "$choice" == "2" ]; then
            echo "📦 升级 google-auth-oauthlib..."
            pip install --upgrade google-auth-oauthlib
            echo "✅ google-auth-oauthlib 已升级"
        fi
        echo ""
    fi
fi

# 安装 LangExtract
echo "📦 安装 LangExtract..."
# 注意：google-cloud-storage 可能会尝试升级 google-auth
# 我们需要先固定 google-auth 版本，然后安装 LangExtract
echo "   先固定 google-auth 版本以避免冲突..."
pip install "google-auth>=2.15.0,<2.42.0" --force-reinstall --no-deps 2>/dev/null || pip install "google-auth>=2.15.0,<2.42.0" --force-reinstall

# 安装 LangExtract，但限制 google-auth 版本
echo "   安装 LangExtract（限制依赖版本）..."
pip install langextract --no-deps 2>/dev/null || pip install langextract

# 如果安装时 google-auth 被升级，再次降级
CURRENT_AUTH_VERSION=$(pip show google-auth 2>/dev/null | grep "Version:" | awk '{print $2}' || echo "")
if [ -n "$CURRENT_AUTH_VERSION" ]; then
    MAJOR=$(echo $CURRENT_AUTH_VERSION | cut -d. -f1)
    MINOR=$(echo $CURRENT_AUTH_VERSION | cut -d. -f2)
    if [ "$MAJOR" -gt 2 ] || ([ "$MAJOR" -eq 2 ] && [ "$MINOR" -ge 42 ]); then
        echo "   ⚠️  检测到 google-auth 被升级到 $CURRENT_AUTH_VERSION，正在降级..."
        pip install "google-auth>=2.15.0,<2.42.0" --force-reinstall
        echo "   ✅ google-auth 已降级到兼容版本"
    fi
fi

echo ""
echo "✅ LangExtract 安装完成！"
echo ""

# 最终检查版本冲突
echo "🔍 最终检查依赖版本..."
FINAL_AUTH_VERSION=$(pip show google-auth 2>/dev/null | grep "Version:" | awk '{print $2}' || echo "未安装")
FINAL_OAUTHLIB_VERSION=$(pip show google-auth-oauthlib 2>/dev/null | grep "Version:" | awk '{print $2}' || echo "未安装")

echo "   google-auth: $FINAL_AUTH_VERSION"
echo "   google-auth-oauthlib: $FINAL_OAUTHLIB_VERSION"

if [ "$FINAL_AUTH_VERSION" != "未安装" ]; then
    MAJOR=$(echo $FINAL_AUTH_VERSION | cut -d. -f1)
    MINOR=$(echo $FINAL_AUTH_VERSION | cut -d. -f2)
    if [ "$MAJOR" -gt 2 ] || ([ "$MAJOR" -eq 2 ] && [ "$MINOR" -ge 42 ]); then
        echo ""
        echo "⚠️  警告: 仍然存在版本冲突"
        echo "   google-auth $FINAL_AUTH_VERSION 与 google-auth-oauthlib $FINAL_OAUTHLIB_VERSION 不兼容"
        echo "   正在自动修复..."
        pip install "google-auth>=2.15.0,<2.42.0" --force-reinstall
        FIXED_VERSION=$(pip show google-auth 2>/dev/null | grep "Version:" | awk '{print $2}')
        echo "   ✅ 已修复: google-auth $FIXED_VERSION"
        echo ""
    else
        echo "   ✅ 版本兼容"
    fi
fi

# 验证安装
echo ""
echo "🔍 验证 LangExtract 安装..."
if python3 -c "import langextract" 2>/dev/null; then
    echo "✅ LangExtract 导入成功"
else
    echo "❌ LangExtract 导入失败"
    exit 1
fi

echo ""
echo "📝 下一步："
echo "   1. 设置 GOOGLE_API_KEY 环境变量"
echo "   2. 或在 .env 文件中添加: GOOGLE_API_KEY=your-api-key"
echo "   3. 查看安装指南: docs/installation/langextract_installation_guide.md"
echo ""
echo "💡 提示: 如果之后再次遇到版本冲突，可以运行:"
echo "   bash scripts/fix_google_auth_version.sh"
echo ""

