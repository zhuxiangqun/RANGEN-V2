#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
外部API统一管理器 - 统一管理所有外部API调用
"""

import os
import re
import json
import logging
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class ExternalAPIUnifier:
    """外部API统一管理器"""
    
    def __init__(self):
        self.api_endpoints = {
            "jina_api": {
                "base_url": "https://api.jina.ai/v1",
                "timeout": 30,
                "max_retries": 3,
                "rate_limit": 100  # requests per minute
            },
            "deepseek_api": {
                "base_url": "https://api.deepseek.com/v1",
                "timeout": 60,
                "max_retries": 3,
                "rate_limit": 50
            },
            "openai_api": {
                "base_url": "https://api.openai.com/v1",
                "timeout": 60,
                "max_retries": 3,
                "rate_limit": 50
            },
            "huggingface_api": {
                "base_url": "https://api-inference.huggingface.co",
                "timeout": 120,
                "max_retries": 2,
                "rate_limit": 20
            }
        }
        
        self.request_history = []
        self.rate_limits = {}
        
    async def make_secure_request(self, service: str, endpoint: str, 
                                method: str = "GET", data: Optional[Dict[str, Any]] = None,
                                headers: Optional[Dict[str, str]] = None,
                                timeout: Optional[int] = None) -> Dict[str, Any]:
        """统一的外部API请求方法"""
        try:
            # 获取服务配置
            if service not in self.api_endpoints:
                raise ValueError(f"未知的服务: {service}")
            
            config = self.api_endpoints[service]
            base_url = config["base_url"]
            request_timeout = timeout or config["timeout"]
            
            # 构建完整URL
            if endpoint.startswith("http"):
                url = endpoint
            else:
                url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            
            # 检查速率限制
            if not self._check_rate_limit(service):
                raise Exception(f"服务 {service} 达到速率限制")
            
            # 准备请求头
            request_headers = headers or {}
            if "Authorization" not in request_headers:
                request_headers["Authorization"] = self._get_auth_header(service)
            
            # 记录请求
            self._record_request(service, url, method)
            
            # 执行请求
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=request_timeout)) as session:
                if method.upper() == "GET":
                    async with session.get(url, headers=request_headers) as response:
                        return await self._handle_response(response, service)
                elif method.upper() == "POST":
                    async with session.post(url, headers=request_headers, json=data) as response:
                        return await self._handle_response(response, service)
                elif method.upper() == "PUT":
                    async with session.put(url, headers=request_headers, json=data) as response:
                        return await self._handle_response(response, service)
                elif method.upper() == "DELETE":
                    async with session.delete(url, headers=request_headers) as response:
                        return await self._handle_response(response, service)
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")
                    
        except Exception as e:
            logger.error(f"API请求失败 {service}: {e}")
            return {
                "success": False,
                "error": str(e),
                "service": service,
                "endpoint": endpoint
            }
    
    def _check_rate_limit(self, service: str) -> bool:
        """检查速率限制"""
        if service not in self.rate_limits:
            self.rate_limits[service] = []
        
        import time
        current_time = time.time()
        
        # 清理过期的请求记录
        self.rate_limits[service] = [
            req_time for req_time in self.rate_limits[service]
            if current_time - req_time < 60  # 保留最近1分钟的请求
        ]
        
        # 检查是否超过速率限制
        max_requests = self.api_endpoints[service]["rate_limit"]
        if len(self.rate_limits[service]) >= max_requests:
            return False
        
        # 记录当前请求
        self.rate_limits[service].append(current_time)
        return True
    
    def _get_auth_header(self, service: str) -> str:
        """获取认证头"""
        # 从环境变量获取API密钥
        env_key = f"{service.upper()}_API_KEY"
        api_key = os.getenv(env_key)
        
        if not api_key:
            logger.warning(f"未找到 {service} API密钥: {env_key}")
            return "Bearer dummy_key"  # 使用虚拟密钥避免错误
        
        return f"Bearer {api_key}"
    
    def _record_request(self, service: str, url: str, method: str):
        """记录请求历史"""
        self.request_history.append({
            "service": service,
            "url": url,
            "method": method,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # 保持历史记录在合理范围内
        if len(self.request_history) > 1000:
            self.request_history = self.request_history[-500:]
    
    async def _handle_response(self, response: aiohttp.ClientResponse, service: str) -> Dict[str, Any]:
        """处理API响应"""
        try:
            if response.status == 200:
                data = await response.json()
                return {
                    "success": True,
                    "data": data,
                    "status_code": response.status,
                    "service": service
                }
            else:
                error_text = await response.text()
                return {
                    "success": False,
                    "error": f"HTTP {response.status}: {error_text}",
                    "status_code": response.status,
                    "service": service
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"响应解析失败: {e}",
                "status_code": response.status,
                "service": service
            }
    
    def get_request_stats(self) -> Dict[str, Any]:
        """获取请求统计信息"""
        stats = {
            "total_requests": len(self.request_history),
            "service_stats": {},
            "rate_limits": self.rate_limits
        }
        
        # 按服务统计
        for request in self.request_history:
            service = request["service"]
            if service not in stats["service_stats"]:
                stats["service_stats"][service] = 0
            stats["service_stats"][service] += 1
        
        return stats
    
    def update_service_config(self, service: str, config: Dict[str, Any]):
        """更新服务配置"""
        if service in self.api_endpoints:
            self.api_endpoints[service].update(config)
            logger.info(f"更新服务配置: {service}")
        else:
            self.api_endpoints[service] = config
            logger.info(f"添加新服务配置: {service}")

class ExternalAPIRefactorer:
    """外部API重构器 - 将直接API调用重构为统一调用"""
    
    def __init__(self):
        self.refactor_patterns = {
            "requests_calls": [
                (r"requests\.get\(['\"]([^'\"]+)['\"]", "jina_api", "GET"),
                (r"requests\.post\(['\"]([^'\"]+)['\"]", "jina_api", "POST"),
                (r"requests\.put\(['\"]([^'\"]+)['\"]", "jina_api", "PUT"),
                (r"requests\.delete\(['\"]([^'\"]+)['\"]", "jina_api", "DELETE")
            ],
            "aiohttp_calls": [
                (r"aiohttp\.get\(['\"]([^'\"]+)['\"]", "jina_api", "GET"),
                (r"aiohttp\.post\(['\"]([^'\"]+)['\"]", "jina_api", "POST"),
                (r"aiohttp\.put\(['\"]([^'\"]+)['\"]", "jina_api", "PUT"),
                (r"aiohttp\.delete\(['\"]([^'\"]+)['\"]", "jina_api", "DELETE")
            ],
            "urllib_calls": [
                (r"urllib\.request\.urlopen\(['\"]([^'\"]+)['\"]", "jina_api", "GET"),
                (r"urllib\.request\.Request\(['\"]([^'\"]+)['\"]", "jina_api", "GET")
            ]
        }
    
    def refactor_file(self, file_path: str) -> Dict[str, Any]:
        """重构单个文件的外部API调用"""
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}", "refactored": False}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            refactor_count = 0
            
            # 应用重构模式
            for category, patterns in self.refactor_patterns.items():
                for pattern, service, method in patterns:
                    content, count = self._apply_refactor_pattern(
                        content, pattern, service, method
                    )
                    refactor_count += count
            
            # 添加统一API管理器导入
            content = self._add_unified_api_imports(content)
            
            # 如果文件有变化，保存文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return {"refactored": True, "refactor_count": refactor_count}
            else:
                return {"refactored": False, "refactor_count": 0}
                
        except Exception as e:
            return {"error": str(e), "refactored": False}
    
    def _apply_refactor_pattern(self, content: str, pattern: str, 
                              service: str, method: str) -> Tuple[str, int]:
        """应用重构模式"""
        refactor_count = 0
        
        # 查找匹配的模式
        matches = list(re.finditer(pattern, content))
        
        for match in reversed(matches):  # 从后往前替换
            url = match.group(1)
            
            # 生成统一API调用
            replacement = self._generate_unified_api_call(url, service, method)
            
            # 替换原始调用
            content = content[:match.start()] + replacement + content[match.end():]
            refactor_count += 1
        
        return content, refactor_count
    
    def _generate_unified_api_call(self, url: str, service: str, method: str) -> str:
        """生成统一API调用代码"""
        # 提取端点路径
        if url.startswith("http"):
            endpoint = url.split("/", 3)[-1] if "/" in url.split("//", 1)[-1] else ""
        else:
            endpoint = url
        
        return f"""await api_unifier.make_secure_request(
    service="{service}",
    endpoint="{endpoint}",
    method="{method}"
)"""
    
    def _add_unified_api_imports(self, content: str) -> str:
        """添加统一API管理器导入"""
        # 检查是否已有导入
        if 'ExternalAPIUnifier' in content and 'from external_api_unifier import' not in content:
            # 在文件开头添加导入
            lines = content.split('\n')
            import_line = 'from external_api_unifier import ExternalAPIUnifier'
            
            # 找到合适的位置插入导入
            insert_index = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    insert_index = i + 1
                elif line.strip() == '':
                    continue
                else:
                    break
            
            lines.insert(insert_index, import_line)
            lines.insert(insert_index + 1, 'api_unifier = ExternalAPIUnifier()')
            content = '\n'.join(lines)
        
        return content
    
    def batch_refactor(self, target_files: List[str]) -> Dict[str, Any]:
        """批量重构外部API调用"""
        print("🔄 开始批量重构外部API调用...")
        print("=" * 50)
        
        results = {
            "files_processed": 0,
            "files_refactored": 0,
            "total_refactors": 0,
            "errors": []
        }
        
        for file_path in target_files:
            print(f"📝 处理文件: {file_path}")
            
            result = self.refactor_file(file_path)
            
            if "error" in result:
                results["errors"].append(f"{file_path}: {result['error']}")
                print(f"  ❌ 错误: {result['error']}")
            elif result["refactored"]:
                results["files_refactored"] += 1
                results["total_refactors"] += result["refactor_count"]
                print(f"  ✅ 重构完成: {result['refactor_count']} 处API调用")
            else:
                print(f"  ⚪ 无需重构")
            
            results["files_processed"] += 1
        
        return results

def main():
    """主函数"""
    print("🚀 外部API统一管理")
    print("=" * 60)
    
    # 查找需要重构的文件
    target_files = []
    for root, dirs, files in os.walk("src"):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 检查是否包含直接API调用
                    if any(pattern in content for pattern in [
                        'requests.', 'aiohttp.', 'urllib.request'
                    ]):
                        target_files.append(file_path)
                except:
                    pass
    
    print(f"📋 发现 {len(target_files)} 个文件需要重构")
    
    # 执行重构
    refactorer = ExternalAPIRefactorer()
    results = refactorer.batch_refactor(target_files)
    
    # 输出结果
    print("\n📊 外部API重构结果:")
    print(f"  处理文件: {results['files_processed']}")
    print(f"  重构文件: {results['files_refactored']}")
    print(f"  重构API调用: {results['total_refactors']} 处")
    
    if results["errors"]:
        print(f"\n❌ 错误: {len(results['errors'])} 个")
        for error in results["errors"][:5]:
            print(f"  - {error}")
    
    print("\n✅ 外部API重构完成!")

if __name__ == "__main__":
    main()
