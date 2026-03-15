#!/usr/bin/env python3
"""
RANGEN Lite 极简启动器
对齐pc-agent-loop的极简部署方式

使用方式:
    python rangen_lite.py              # 交互式配置并启动
    python rangen_lite.py --cli        # CLI模式
    python rangen_lite.py --web       # Web UI模式
    python rangen_lite.py --configure # 仅配置
"""
import os
import sys
import json
from pathlib import Path

APP_NAME = "RANGEN"
APP_DIR = Path.home() / ".rangen_lite"
CONFIG_FILE = APP_DIR / "config.json"

WELCOME_MESSAGE = """
===========================================
   RANGEN Lite - 极简启动器
   对标 pc-agent-loop 极简哲学
===========================================

功能:
  - 7原子工具 (code_run, file操作, web操作, ask_user)
  - SOP学习系统 (自动记忆任务流程)
  - 物理控制 (浏览器/键鼠/ADB)
  - 极简部署 (pip install + API key)

快速开始:
  1. 输入API Key
  2. 选择运行模式
  3. 开始使用!
"""


class LiteConfigurator:
    """轻量配置器"""
    
    def __init__(self):
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE) as f:
                    self.config = json.load(f)
            except:
                self.config = {}
    
    def save_config(self):
        """保存配置"""
        APP_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def configure(self, api_key: str = None, provider: str = "deepseek"):
        """配置系统"""
        if not api_key:
            api_key = input("请输入 DeepSeek API Key (sk-xxx): ").strip()
        
        if not api_key:
            print("错误: 需要API Key")
            return False
        
        self.config = {
            "provider": provider,
            "api_key": api_key,
            "initialized": True
        }
        self.save_config()
        self._generate_env(api_key)
        print("配置完成!")
        return True
    
    def _generate_env(self, api_key: str):
        """生成.env文件"""
        env_content = f"""# RANGEN Lite 配置
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY={api_key}
"""
        project_env = Path(__file__).parent / ".env.lite"
        with open(project_env, 'w') as f:
            f.write(env_content)
        print(f".env.lite 文件已生成")
    
    def check_dependencies(self):
        """检查依赖"""
        print("\n检查依赖...")
        required = ["streamlit", "fastapi", "langgraph"]
        missing = []
        
        for pkg in required:
            try:
                __import__(pkg)
                print(f"  OK: {pkg}")
            except ImportError:
                print(f"  MISSING: {pkg}")
                missing.append(pkg)
        
        if missing:
            print(f"缺少依赖: {', '.join(missing)}")
            install = input("是否安装? (y/n): ").strip().lower()
            if install == 'y':
                os.system(f"pip install {' '.join(missing)}")
        else:
            print("所有依赖已安装!")
        
        return len(missing) == 0
    
    def get_api_key(self) -> str:
        return self.config.get("api_key", "")
    
    def is_configured(self) -> bool:
        return self.config.get("initialized", False)


class LiteRunner:
    """轻量运行器"""
    
    def __init__(self, configurator: LiteConfigurator):
        self.configurator = configurator
    
    def run_web(self):
        """启动Web UI"""
        print("\n启动 Web UI...")
        ui_path = Path(__file__).parent / "src" / "ui" / "app.py"
        
        if ui_path.exists():
            os.system(f"streamlit run {ui_path}")
        else:
            print("UI文件不存在")
    
    def run_cli(self):
        """启动CLI模式"""
        print("\n启动 CLI 模式...")
        print("输入 'exit' 退出")
        
        api_key = self.configurator.get_api_key()
        if not api_key:
            print("请先配置API Key")
            return
        
        while True:
            try:
                query = input("\n> ").strip()
                
                if query == "exit":
                    break
                elif query == "help":
                    print("命令: sops, tools, exit")
                elif query == "sops":
                    print("SOP学习系统已集成")
                elif query == "tools":
                    print("7原子工具: code_run, file_read/write/patch, web_scan/execute_js, ask_user")
                elif query:
                    print(f"处理: {query[:50]}...")
            except KeyboardInterrupt:
                break
            except EOFError:
                break
        
        print("\n再见!")


def main():
    print(WELCOME_MESSAGE)
    
    configurator = LiteConfigurator()
    
    if not configurator.is_configured():
        print("\n首次使用，请先配置...")
        configurator.configure()
    
    configurator.check_dependencies()
    
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    if "--configure" in args:
        print("\n配置模式...")
        configurator.configure()
        return
    
    runner = LiteRunner(configurator)
    
    if "--cli" in args:
        runner.run_cli()
    elif "--web" in args:
        runner.run_web()
    else:
        print("\n请选择运行模式:")
        print("  1. Web UI (streamlit)")
        print("  2. CLI 模式")
        
        choice = input("\n请选择 (1/2): ").strip()
        
        if choice == "1":
            runner.run_web()
        elif choice == "2":
            runner.run_cli()


if __name__ == "__main__":
    main()
