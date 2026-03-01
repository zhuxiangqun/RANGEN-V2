#!/usr/bin/env python3
"""
Phi-3 环境设置与模型下载脚本
"""

import os
import sys
import subprocess
from pathlib import Path

# 配置
MODEL_REPO = "microsoft/Phi-3-mini-4k-instruct-gguf"
MODEL_FILE = "Phi-3-mini-4k-instruct-q4.gguf"
TARGET_DIR = Path(__file__).parent.parent / "models"

def check_dependencies():
    """检查必要依赖"""
    print("🔍 检查依赖...")
    missing = []
    
    try:
        import llama_cpp
        print("✅ llama-cpp-python 已安装")
    except ImportError:
        missing.append("llama-cpp-python")
        
    try:
        import huggingface_hub
        print("✅ huggingface-hub 已安装")
    except ImportError:
        missing.append("huggingface-hub")
        
    if missing:
        print(f"❌ 缺少依赖: {', '.join(missing)}")
        print("💡 正在尝试自动安装...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
            print("✅ 依赖安装成功！")
        except subprocess.CalledProcessError:
            print("❌ 自动安装失败，请手动运行:")
            print(f"pip install {' '.join(missing)}")
            sys.exit(1)

def download_model():
    """下载 Phi-3 模型"""
    TARGET_DIR.mkdir(exist_ok=True)
    target_path = TARGET_DIR / MODEL_FILE
    
    if target_path.exists():
        print(f"✅ 模型已存在: {target_path}")
        return

    print(f"⬇️ 开始下载 {MODEL_FILE}...")
    print(f"   源: {MODEL_REPO}")
    print(f"   目标: {TARGET_DIR}")
    
    try:
        from huggingface_hub import hf_hub_download
        
        hf_hub_download(
            repo_id=MODEL_REPO,
            filename=MODEL_FILE,
            local_dir=str(TARGET_DIR),
            local_dir_use_symlinks=False
        )
        print("✅ 模型下载完成！")
        
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        sys.exit(1)

def verify_installation():
    """验证模型能否加载"""
    print("🔄 验证模型加载...")
    try:
        sys.path.append(str(Path(__file__).parent.parent))
        from src.services.local_llm_service import LocalLLMService
        
        service = LocalLLMService()
        if service.llm:
            print("🎉 验证成功！Phi-3 已准备就绪。")
            
            # 简单测试
            print("🧪 执行测试查询...")
            result = service.analyze_query_complexity("What is 1+1?")
            print(f"   测试结果: {result}")
        else:
            print("❌ 验证失败: 模型无法加载")
            
    except Exception as e:
        print(f"❌ 验证出错: {e}")

if __name__ == "__main__":
    print("🚀 开始 Phi-3 环境设置 (Phase 3.1)")
    check_dependencies()
    download_model()
    verify_installation()
