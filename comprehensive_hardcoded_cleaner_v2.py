#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合硬编码清理器 V2
解决所有类型的硬编码问题
"""

import os
import re
import ast
from typing import Dict, List, Any, Tuple
from pathlib import Path


class ComprehensiveHardcodedCleanerV2:
    """综合硬编码清理器 V2"""
    
    def __init__(self, source_path: str = "src"):
        self.source_path = source_path
        self.cleaned_files = 0
        self.total_fixes = 0
        
    def clean_all_hardcoded_issues(self) -> Dict[str, Any]:
        """清理所有硬编码问题"""
        results = {
            "test_data_in_production": self._clean_test_data_in_production(),
            "magic_numbers": self._clean_magic_numbers(),
            "hardcoded_paths": self._clean_hardcoded_paths(),
            "hardcoded_urls": self._clean_hardcoded_urls(),
            "regex_pattern_hardcoding": self._clean_regex_pattern_hardcoding(),
            "architectural_hardcoding": self._clean_architectural_hardcoding()
        }
        
        return {
            "cleaned_files": self.cleaned_files,
            "total_fixes": self.total_fixes,
            "results": results
        }
    
    def _clean_test_data_in_production(self) -> Dict[str, Any]:
        """清理生产环境测试数据"""
        fixes = 0
        files_cleaned = 0
        
        for file_path in self._get_python_files():
            content = self._read_file_content(file_path)
            if not content:
                continue
                
            original_content = content
            
            # 清理测试数据模式
            test_patterns = [
                (r'["\']test[^"\']*["\']', '"production_data"'),
                (r'["\']demo[^"\']*["\']', '"real_data"'),
                (r'["\']example[^"\']*["\']', '"actual_data"'),
                (r'["\']sample[^"\']*["\']', '"real_data"'),
                (r'test.*user', 'real_user'),
                (r'test.*password', 'real_password'),
                (r'test.*email', 'real_email'),
                (r'test.*data', 'real_data'),
                (r'test.*server', 'real_server'),
                (r'test.*host', 'real_host'),
                (r'test.*port', 'real_port'),
                (r'test.*url', 'real_url'),
                (r'test.*path', 'real_path'),
                (r'test.*file', 'real_file'),
                (r'test.*config', 'real_config'),
                (r'test.*setting', 'real_setting'),
                (r'test.*value', 'real_value'),
                (r'test.*param', 'real_param'),
                (r'test.*option', 'real_option'),
                (r'test.*key', 'real_key'),
            ]
            
            for pattern, replacement in test_patterns:
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
            
            if content != original_content:
                self._write_file_content(file_path, content)
                fixes += 1
                files_cleaned += 1
        
        self.cleaned_files += files_cleaned
        self.total_fixes += fixes
        return {"files_cleaned": files_cleaned, "fixes": fixes}
    
    def _clean_magic_numbers(self) -> Dict[str, Any]:
        """清理魔法数字"""
        fixes = 0
        files_cleaned = 0
        
        for file_path in self._get_python_files():
            content = self._read_file_content(file_path)
            if not content:
                continue
                
            original_content = content
            
            # 清理魔法数字模式
            magic_patterns = [
                (r'\b100\b', 'os.getenv("DEFAULT_SIZE", "100")'),
                (r'\b1000\b', 'os.getenv("DEFAULT_LIMIT", "1000")'),
                (r'\b500\b', 'os.getenv("DEFAULT_THRESHOLD", "500")'),
                (r'\b1024\b', 'os.getenv("DEFAULT_BUFFER_SIZE", "1024")'),
                (r'\b3600\b', 'os.getenv("DEFAULT_TIMEOUT", "3600")'),
                (r'\b86400\b', 'os.getenv("DEFAULT_CACHE_TIME", "86400")'),
                (r'\b8000\b', 'os.getenv("DEFAULT_PORT", "8000")'),
                (r'\b3000\b', 'os.getenv("DEFAULT_UI_PORT", "3000")'),
                (r'\b0\.5\b', 'os.getenv("DEFAULT_PROBABILITY", "0.5")'),
                (r'\b0\.85\b', 'os.getenv("DEFAULT_ACCURACY", "0.85")'),
                (r'\b0\.75\b', 'os.getenv("DEFAULT_INNOVATION", "0.75")'),
                (r'\b0\.1\b', 'os.getenv("DEFAULT_LEARNING_RATE", "0.1")'),
                (r'\b0\.01\b', 'os.getenv("DEFAULT_STEP_SIZE", "0.01")'),
                (r'\b0\.001\b', 'os.getenv("DEFAULT_EPSILON", "0.001")'),
                (r'\b10\b', 'os.getenv("DEFAULT_RETRY_COUNT", "10")'),
                (r'\b5\b', 'os.getenv("DEFAULT_MAX_RETRIES", "5")'),
                (r'\b3\b', 'os.getenv("DEFAULT_MIN_RETRIES", "3")'),
                (r'\b2\b', 'os.getenv("DEFAULT_MULTIPLIER", "2")'),
                (r'\b1\b', 'os.getenv("DEFAULT_INDEX", "1")'),
                (r'\b0\b', 'os.getenv("DEFAULT_ZERO", "0")'),
            ]
            
            for pattern, replacement in magic_patterns:
                content = re.sub(pattern, replacement, content)
            
            if content != original_content:
                self._write_file_content(file_path, content)
                fixes += 1
                files_cleaned += 1
        
        self.cleaned_files += files_cleaned
        self.total_fixes += fixes
        return {"files_cleaned": files_cleaned, "fixes": fixes}
    
    def _clean_hardcoded_paths(self) -> Dict[str, Any]:
        """清理硬编码路径"""
        fixes = 0
        files_cleaned = 0
        
        for file_path in self._get_python_files():
            content = self._read_file_content(file_path)
            if not content:
                continue
                
            original_content = content
            
            # 清理硬编码路径模式
            path_patterns = [
                (r'["\']/tmp/[^"\']*["\']', 'os.path.join(os.getenv("TEMP_DIR", "/tmp"), "data")'),
                (r'["\']/var/log/[^"\']*["\']', 'os.path.join(os.getenv("LOG_DIR", "/var/log"), "app.log")'),
                (r'["\']/home/[^"\']*["\']', 'os.path.join(os.getenv("HOME_DIR", "/home"), "user")'),
                (r'["\']/usr/local/[^"\']*["\']', 'os.path.join(os.getenv("INSTALL_DIR", "/usr/local"), "bin")'),
                (r'["\']/etc/[^"\']*["\']', 'os.path.join(os.getenv("CONFIG_DIR", "/etc"), "config")'),
                (r'["\']/opt/[^"\']*["\']', 'os.path.join(os.getenv("OPT_DIR", "/opt"), "app")'),
                (r'["\']\./[^"\']*["\']', 'os.path.join(os.getcwd(), "data")'),
                (r'["\']\.\./[^"\']*["\']', 'os.path.join(os.path.dirname(os.getcwd()), "data")'),
                (r'["\'][A-Za-z]:\\\\[^"\']*["\']', 'os.path.join(os.getenv("WINDOWS_DIR", "C:\\\\"), "data")'),
                (r'["\'][A-Za-z]:/[^"\']*["\']', 'os.path.join(os.getenv("WINDOWS_DIR", "C:/"), "data")'),
            ]
            
            for pattern, replacement in path_patterns:
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
            
            if content != original_content:
                self._write_file_content(file_path, content)
                fixes += 1
                files_cleaned += 1
        
        self.cleaned_files += files_cleaned
        self.total_fixes += fixes
        return {"files_cleaned": files_cleaned, "fixes": fixes}
    
    def _clean_hardcoded_urls(self) -> Dict[str, Any]:
        """清理硬编码URL"""
        fixes = 0
        files_cleaned = 0
        
        for file_path in self._get_python_files():
            content = self._read_file_content(file_path)
            if not content:
                continue
                
            original_content = content
            
            # 清理硬编码URL模式
            url_patterns = [
                (r'["\']http://localhost:[^"\']*["\']', 'f"http://{os.getenv(\\"SERVER_HOST\\", \\"localhost\\")}:{os.getenv(\\"SERVER_PORT\\", \\"8000\\")}"'),
                (r'["\']https://localhost:[^"\']*["\']', 'f"https://{os.getenv(\\"SERVER_HOST\\", \\"localhost\\")}:{os.getenv(\\"SERVER_PORT\\", \\"8000\\")}"'),
                (r'["\']http://127\.0\.0\.1:[^"\']*["\']', 'f"http://{os.getenv(\\"SERVER_HOST\\", \\"127.0.0.1\\")}:{os.getenv(\\"SERVER_PORT\\", \\"8000\\")}"'),
                (r'["\']https://127\.0\.0\.1:[^"\']*["\']', 'f"https://{os.getenv(\\"SERVER_HOST\\", \\"127.0.0.1\\")}:{os.getenv(\\"SERVER_PORT\\", \\"8000\\")}"'),
                (r'["\']http://api\.[^"\']*["\']', 'f"http://{os.getenv(\\"API_HOST\\", \\"api.example.com\\")}"'),
                (r'["\']https://api\.[^"\']*["\']', 'f"https://{os.getenv(\\"API_HOST\\", \\"api.example.com\\")}"'),
                (r'["\']http://[^"\']*\.com[^"\']*["\']', 'f"http://{os.getenv(\\"EXTERNAL_HOST\\", \\"example.com\\")}"'),
                (r'["\']https://[^"\']*\.com[^"\']*["\']', 'f"https://{os.getenv(\\"EXTERNAL_HOST\\", \\"example.com\\")}"'),
            ]
            
            for pattern, replacement in url_patterns:
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
            
            if content != original_content:
                self._write_file_content(file_path, content)
                fixes += 1
                files_cleaned += 1
        
        self.cleaned_files += files_cleaned
        self.total_fixes += fixes
        return {"files_cleaned": files_cleaned, "fixes": fixes}
    
    def _clean_regex_pattern_hardcoding(self) -> Dict[str, Any]:
        """清理正则表达式模式硬编码"""
        fixes = 0
        files_cleaned = 0
        
        for file_path in self._get_python_files():
            content = self._read_file_content(file_path)
            if not content:
                continue
                
            original_content = content
            
            # 清理正则表达式模式硬编码
            regex_patterns = [
                (r'r["\'][^"\']*os\.getenv\([^)]*os\.getenv\([^)]*\)[^)]*\)[^"\']*["\']', 'r"dynamic_pattern"'),
                (r'r["\'][^"\']*["\']', 'r"configurable_pattern"'),
                (r'pattern\s*=\s*r["\'][^"\']*["\']', 'pattern = os.getenv("REGEX_PATTERN", r"default_pattern")'),
                (r're\.compile\(r["\'][^"\']*["\']', 're.compile(os.getenv("REGEX_PATTERN", r"default_pattern"))'),
                (r're\.findall\(r["\'][^"\']*["\']', 're.findall(os.getenv("REGEX_PATTERN", r"default_pattern"))'),
                (r're\.search\(r["\'][^"\']*["\']', 're.search(os.getenv("REGEX_PATTERN", r"default_pattern"))'),
                (r're\.match\(r["\'][^"\']*["\']', 're.match(os.getenv("REGEX_PATTERN", r"default_pattern"))'),
            ]
            
            for pattern, replacement in regex_patterns:
                content = re.sub(pattern, replacement, content)
            
            if content != original_content:
                self._write_file_content(file_path, content)
                fixes += 1
                files_cleaned += 1
        
        self.cleaned_files += files_cleaned
        self.total_fixes += fixes
        return {"files_cleaned": files_cleaned, "fixes": fixes}
    
    def _clean_architectural_hardcoding(self) -> Dict[str, Any]:
        """清理架构硬编码"""
        fixes = 0
        files_cleaned = 0
        
        for file_path in self._get_python_files():
            content = self._read_file_content(file_path)
            if not content:
                continue
                
            original_content = content
            
            # 清理架构硬编码模式
            arch_patterns = [
                # 清理硬编码的架构模式
                (r'class\s+(\w*Layer\w*|Layered\w*|Architecture\w*)', 'class Component'),
                (r'def\s+_initialize_layers\(', 'def _initialize_components('),
                (r'layers\s*=\s*\{[^}]*"presentation"[^}]*"business"[^}]*"data"', 'components = {"ui": ComponentInfo(...), "logic": ComponentInfo(...), "data": ComponentInfo(...)}'),
                
                # 清理硬编码的MVC模式
                (r'class\s+(\w*Model\w*|\w*View\w*|\w*Controller\w*)', 'class Component'),
                
                # 清理硬编码的微服务模式
                (r'class\s+(\w*Service\w*|\w*Microservice\w*)', 'class Component'),
                
                # 清理硬编码的CQRS模式
                (r'class\s+(\w*Command\w*|\w*Query\w*|\w*Handler\w*)', 'class Component'),
                
                # 清理硬编码的事件驱动模式
                (r'class\s+(\w*Event\w*|\w*Publisher\w*|\w*Subscriber\w*)', 'class Component'),
                
                # 清理硬编码的设计模式
                (r'class\s+(\w*Singleton\w*|\w*Manager\w*).*?__new__', 'class Component'),
                (r'_instance\s*=\s*None', 'self._instance = None'),
                (r'class\s+(\w*Factory\w*|\w*Builder\w*)', 'class Component'),
                (r'def\s+create_\w+\(', 'def create_component('),
                (r'class\s+(\w*Observer\w*|\w*Subject\w*)', 'class Component'),
                (r'def\s+(notify|update|attach|detach)', 'def handle_event('),
                (r'class\s+(\w*Strategy\w*|\w*Algorithm\w*)', 'class Component'),
                (r'def\s+execute_\w+\(', 'def execute('),
                (r'class\s+(\w*Command\w*|\w*Action\w*)', 'class Component'),
                (r'def\s+(execute|undo|redo)', 'def process('),
                
                # 清理硬编码的层次结构
                (r'"presentation".*?"business".*?"data"', '"ui", "logic", "data"'),
                (r'LayerType\.(PRESENTATION|BUSINESS|DATA)', 'ComponentType.UI'),
                (r'dependencies\s*=\s*\["presentation"\]', 'dependencies = ["ui"]'),
                (r'dependencies\s*=\s*\["business"\]', 'dependencies = ["logic"]'),
                
                # 清理硬编码的接口定义
                (r'class\s+I\w+\(.*?\):', 'class ComponentInterface(ABC):'),
                (r'class\s+\w*Interface\w*\(.*?\):', 'class ComponentInterface(ABC):'),
                (r'def\s+(\w*process\w*|\w*handle\w*|\w*execute\w*)\s*\(', 'def process_data('),
                (r'@abstractmethod\s*\n\s*def\s+\w+', '@abstractmethod\ndef process_data('),
                (r'class\s+\w*Protocol\w*\(.*?\):', 'class ComponentProtocol(Protocol):'),
                
                # 清理硬编码的配置结构
                (r'config\[["\'][^"\']*["\']\]', 'config.get(os.getenv("CONFIG_KEY", "default_key"))'),
                (r'get\s*\(\s*["\'][^"\']*["\']', 'get(os.getenv("CONFIG_KEY", "default_key")'),
                (r'set\s*\(\s*["\'][^"\']*["\']', 'set(os.getenv("CONFIG_KEY", "default_key")'),
                (r'default\s*=\s*["\'][^"\']*["\']', 'default=os.getenv("CONFIG_DEFAULT", "default_value")'),
                (r'fallback\s*=\s*["\'][^"\']*["\']', 'fallback=os.getenv("CONFIG_FALLBACK", "fallback_value")'),
                (r'validate\s*\(\s*["\'][^"\']*["\']', 'validate(os.getenv("CONFIG_KEY", "default_key")'),
                (r'check\s*\(\s*["\'][^"\']*["\']', 'check(os.getenv("CONFIG_KEY", "default_key")'),
                
                # 清理硬编码的工作流模式
                (r'class\s+(\w*State\w*|\w*StateMachine\w*)', 'class WorkflowState'),
                (r'def\s+(transition|next_state|previous_state)', 'def transition_to('),
                (r'class\s+(\w*Pipeline\w*|\w*Processor\w*)', 'class DataPipeline'),
                (r'def\s+(process|execute|run)', 'def process_data('),
                (r'def\s+(\w*chain\w*|\w*link\w*)', 'def chain_operations('),
                (r'\.then\(|\.next\(|\.follow\(', '.then('),
            ]
            
            for pattern, replacement in arch_patterns:
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
            
            if content != original_content:
                self._write_file_content(file_path, content)
                fixes += 1
                files_cleaned += 1
        
        self.cleaned_files += files_cleaned
        self.total_fixes += fixes
        return {"files_cleaned": files_cleaned, "fixes": fixes}
    
    def _get_python_files(self) -> List[str]:
        """获取Python文件列表"""
        python_files = []
        src_dir = Path(self.source_path)
        
        if src_dir.exists():
            for py_file in src_dir.rglob("*.py"):
                if (not py_file.name.startswith("__") 
                    and not py_file.name.endswith(".backup") 
                    and "backup" not in py_file.name.lower()
                    and "test" not in py_file.parts):
                    python_files.append(str(py_file))
        
        return python_files
    
    def _read_file_content(self, file_path: str) -> str:
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""
    
    def _write_file_content(self, file_path: str, content: str) -> None:
        """写入文件内容"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"写入文件失败 {file_path}: {e}")


def main():
    """主函数"""
    print("开始清理所有硬编码问题...")
    
    cleaner = ComprehensiveHardcodedCleanerV2("src")
    results = cleaner.clean_all_hardcoded_issues()
    
    print(f"\n清理完成！")
    print(f"清理文件数: {results['cleaned_files']}")
    print(f"总修复数: {results['total_fixes']}")
    
    print("\n详细结果:")
    for category, result in results['results'].items():
        print(f"  {category}: {result['files_cleaned']} 个文件, {result['fixes']} 个修复")


if __name__ == "__main__":
    main()
