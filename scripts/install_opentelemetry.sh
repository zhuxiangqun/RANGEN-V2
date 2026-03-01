#!/bin/bash
# OpenTelemetry 安装脚本
# 用于安装 OpenTelemetry 监控功能

echo "=========================================="
echo "安装 OpenTelemetry 监控支持"
echo "=========================================="

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3 命令"
    exit 1
fi

echo "📦 正在安装 OpenTelemetry 核心包..."
python3 -m pip install opentelemetry-api>=1.20.0 opentelemetry-sdk>=1.20.0

if [ $? -eq 0 ]; then
    echo "✅ OpenTelemetry 核心包安装成功"
else
    echo "❌ OpenTelemetry 核心包安装失败"
    exit 1
fi

# 询问是否安装导出器
echo ""
echo "是否安装 OpenTelemetry 导出器？"
echo "1) 仅控制台导出器（默认，已包含在 SDK 中）"
echo "2) Jaeger 导出器（用于分布式追踪）"
echo "3) Zipkin 导出器（用于分布式追踪）"
echo "4) OTLP 导出器（通用协议）"
echo "5) 全部安装"
echo "6) 跳过（仅使用控制台导出器）"
read -p "请选择 (1-6，默认 6): " choice

case $choice in
    2)
        echo "📦 正在安装 Jaeger 导出器..."
        python3 -m pip install opentelemetry-exporter-jaeger-thrift
        ;;
    3)
        echo "📦 正在安装 Zipkin 导出器..."
        python3 -m pip install opentelemetry-exporter-zipkin-json
        ;;
    4)
        echo "📦 正在安装 OTLP 导出器..."
        python3 -m pip install opentelemetry-exporter-otlp-proto-grpc
        ;;
    5)
        echo "📦 正在安装所有导出器..."
        python3 -m pip install opentelemetry-exporter-jaeger-thrift opentelemetry-exporter-zipkin-json opentelemetry-exporter-otlp-proto-grpc
        ;;
    *)
        echo "ℹ️ 跳过导出器安装（将使用控制台导出器）"
        ;;
esac

echo ""
echo "=========================================="
echo "✅ OpenTelemetry 安装完成"
echo "=========================================="
echo ""
echo "📝 使用说明："
echo "1. OpenTelemetry 默认已启用（无需设置环境变量）"
echo "2. 如需禁用，设置环境变量: export ENABLE_OPENTELEMETRY=false"
echo "3. 如需使用其他导出器，设置环境变量:"
echo "   export OPENTELEMETRY_EXPORTER=jaeger  # 或 zipkin, otlp"
echo "   export OPENTELEMETRY_ENDPOINT=http://localhost:14268/api/traces"
echo ""
echo "🎉 监控功能现在已可用！"

