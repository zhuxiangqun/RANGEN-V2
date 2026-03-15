# 代码规范指南

## 📖 概述

本指南定义了RANGEN系统的代码规范和最佳实践，旨在确保代码质量、可维护性和一致性。所有贡献者必须遵循这些规范。

## 🎯 核心原则

### 1. DRY (Don't Repeat Yourself)
- 避免重复代码，提取公共功能到函数或模块
- 使用抽象和接口减少代码重复

### 2. KISS (Keep It Simple, Stupid)
- 优先选择简单、清晰的实现
- 避免过度设计和不必要的复杂性

### 3. 单一职责原则
- 每个函数/类只负责一个功能
- 保持模块的专注性和内聚性

### 4. 组合优于继承
- 优先使用组合实现代码复用
- 谨慎使用继承，避免深度继承层次

## 📝 Python代码风格

### 命名约定

#### 变量和函数
- 使用`snake_case`（小写字母，单词间用下划线分隔）
- 使用描述性名称，避免缩写

```python
# 正确
agent_config = {}
process_request()
calculate_total_score()

# 错误
agentConfig = {}  # 驼峰命名法
procReq()         # 缩写
calc()           # 不明确
```

#### 类名
- 使用`PascalCase`（首字母大写，无下划线）

```python
# 正确
class BaseAgent:
    pass

class AgentConfigService:
    pass

# 错误
class base_agent:   # 应使用PascalCase
    pass

class Agent_config_service:  # 不应使用下划线
    pass
```

#### 常量
- 使用`UPPER_SNAKE_CASE`（全大写，单词间用下划线分隔）

```python
# 正确
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
API_BASE_URL = "https://api.example.com"

# 错误
maxRetries = 3      # 不是大写
DefaultTimeout = 30 # 不是蛇形命名
```

#### 私有成员
- 前缀使用下划线`_`
- 双下划线`__`前缀用于名称改写（谨慎使用）

```python
class AgentService:
    def __init__(self):
        self._internal_cache = {}  # 受保护的成员
        self.__secret_key = None   # 私有成员（名称改写）
    
    def _helper_method(self):      # 受保护的方法
        pass
    
    def __private_method(self):    # 私有方法
        pass
```

### 导入组织

#### 导入顺序
1. 标准库导入
2. 第三方库导入
3. 本地应用导入
4. 相对导入

```python
# 标准库导入
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# 第三方库导入
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from langgraph import StateGraph
from pydantic import BaseModel, Field

# 本地应用导入
from src.agents.base_agent import BaseAgent
from src.core.config import ConfigService
from src.services.error_handling import ErrorHandlingService

# 相对导入（在同一包内）
from .utils import helper_function
from ..models import AgentModel
```

#### 导入规范
- 每个导入单独一行（除了`from module import a, b, c`）
- 避免使用通配符导入（`from module import *`）
- 使用明确导入，避免循环导入

```python
# 正确
import os
import sys
from typing import Dict, List

from fastapi import FastAPI
from pydantic import BaseModel

# 可接受的
from typing import Dict, List, Optional, Union

# 避免
import os, sys  # 多个导入在同一行
from module import *  # 通配符导入
```

### 格式化规范

#### 行长度
- 最大行长度：120个字符（配置在`.pylintrc`中）
- 超过限制时适当换行

```python
# 正确：换行长行
result = some_function_with_long_name(
    argument1, argument2, argument3,
    keyword_argument1="value1",
    keyword_argument2="value2"
)

# 正确：使用括号隐式换行
long_string = (
    "这是一个非常长的字符串，"
    "需要使用括号进行换行处理，"
    "以保持代码的可读性。"
)

# 错误：超过120字符不换行
result = some_very_long_function_name_with_many_arguments(argument1, argument2, argument3, keyword_argument1="value1", keyword_argument2="value2")
```

#### 缩进
- 使用4个空格缩进（禁止使用制表符）
- 连续行使用额外缩进

```python
# 正确：4空格缩进
def process_request(request: Request) -> Response:
    try:
        result = some_function(
            argument1,
            argument2,
            argument3
        )
        return Response(data=result)
    except Exception as e:
        logger.error(f"处理请求失败: {e}")
        raise

# 错误：使用制表符或2空格缩进
def process_request(request):  # 制表符缩进
  try:                        # 2空格缩进
    result = some_function()
    return result
  except:
    raise
```

#### 空格使用
- 运算符周围使用空格
- 逗号后使用空格
- 冒号后使用空格（在类型注解中）

```python
# 正确
x = 5 + 3
y = [1, 2, 3, 4]
def process(data: Dict[str, Any]) -> Optional[str]:
    pass

# 错误
x=5+3
y=[1,2,3,4]
def process(data:Dict[str,Any])->Optional[str]:
    pass
```

#### 空行使用
- 函数和类之间使用两个空行
- 类内方法之间使用一个空行
- 逻辑相关的代码块之间使用一个空行

```python
import os


class AgentService:
    """智能体服务类"""
    
    def __init__(self):
        self.config = {}
    
    def process_request(self, request):
        """处理请求"""
        # 验证输入
        self._validate_request(request)
        
        # 处理逻辑
        result = self._do_processing(request)
        
        return result
    
    def _validate_request(self, request):
        """验证请求"""
        pass
    
    def _do_processing(self, request):
        """执行处理"""
        pass


def helper_function():
    """辅助函数"""
    pass
```

### 类型注解

#### 基本类型注解
- 所有公共函数和类方法必须有完整的类型注解
- 使用`typing`模块提供的类型

```python
from typing import Dict, List, Any, Optional, Union, Tuple

def process_data(
    data: Dict[str, Any],
    options: Optional[Dict[str, Any]] = None
) -> Union[str, List[str]]:
    """处理数据函数
    
    Args:
        data: 输入数据字典
        options: 可选配置
        
    Returns:
        处理结果，可以是字符串或字符串列表
    """
    pass

class AgentConfig:
    """智能体配置类"""
    
    def __init__(self, name: str, timeout: int = 30):
        self.name: str = name
        self.timeout: int = timeout
        self.capabilities: List[str] = []
```

#### 复杂类型注解
```python
from typing import TypeVar, Generic, Callable, Iterator
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class ProcessingResult:
    """处理结果数据类"""
    success: bool
    data: Any
    error: Optional[str] = None

class Repository(Generic[T]):
    """泛型仓库类"""
    
    def get(self, id: str) -> Optional[T]:
        pass
    
    def save(self, item: T) -> bool:
        pass

def create_processor(
    config: Dict[str, Any]
) -> Callable[[str], ProcessingResult]:
    """创建处理器工厂函数"""
    def processor(input_text: str) -> ProcessingResult:
        # 处理逻辑
        pass
    
    return processor
```

### 文档字符串

#### 函数和类文档字符串
- 使用三重双引号`"""`包含文档字符串
- 第一行是简短描述
- 如果有更多内容，空一行后添加详细描述
- 包含参数、返回值和异常说明

```python
def calculate_score(
    input_data: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None
) -> float:
    """计算输入数据的得分
    
    根据输入数据和权重配置计算综合得分。如果未提供权重，
    则使用默认权重配置。
    
    Args:
        input_data: 输入数据字典，包含需要计算得分的字段
        weights: 可选权重配置，键为字段名，值为权重值
    
    Returns:
        计算得到的综合得分，范围在0到1之间
    
    Raises:
        ValueError: 当输入数据为空或权重配置无效时
        TypeError: 当输入数据类型不正确时
    
    Examples:
        >>> data = {"accuracy": 0.8, "speed": 0.9}
        >>> calculate_score(data)
        0.85
        >>> calculate_score(data, {"accuracy": 0.7, "speed": 0.3})
        0.83
    """
    if not input_data:
        raise ValueError("输入数据不能为空")
    
    # 计算逻辑
    pass
```

#### 类文档字符串
```python
class KnowledgeRetrievalAgent:
    """知识检索智能体
    
    负责从知识库中检索相关信息，支持多种检索策略和
    结果排序算法。可以配置为使用不同的向量数据库和
    嵌入模型。
    
    Attributes:
        config: 智能体配置
        vector_store: 向量数据库连接
        embedding_model: 嵌入模型名称
        max_results: 最大返回结果数
    
    Examples:
        >>> agent = KnowledgeRetrievalAgent()
        >>> results = agent.retrieve("什么是机器学习？")
        >>> len(results)
        10
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化知识检索智能体
        
        Args:
            config: 智能体配置字典
        """
        self.config = config
        self.vector_store = self._init_vector_store()
        self.embedding_model = config.get("embedding_model", "text-embedding-3-small")
        self.max_results = config.get("max_results", 10)
```

#### LangGraph节点文档字符串
```python
def knowledge_retrieval_node(state: AgentState) -> AgentState:
    """知识检索节点 - 从知识库检索相关信息
    
    根据当前查询和上下文，从向量知识库中检索最相关的
    文档片段。支持混合检索策略（语义+关键词）和结果
    重排序。
    
    Node ID: knowledge_retrieval
    Input State Keys: query, context
    Output State Keys: retrieved_documents, retrieval_metadata
    """
    query = state.get("query", "")
    context = state.get("context", {})
    
    # 检索逻辑
    retrieved_docs = knowledge_base.retrieve(query, context)
    
    return {
        **state,
        "retrieved_documents": retrieved_docs,
        "retrieval_metadata": {
            "count": len(retrieved_docs),
            "timestamp": datetime.now().isoformat()
        }
    }
```

## 🔧 代码质量工具

### Pylint配置
项目使用`.pylintrc`配置文件，主要规则包括：

```ini
# 基本配置
max-line-length=120
indent-string='    '

# 命名约定
method-naming-style=snake_case
function-naming-style=snake_case
variable-naming-style=snake_case
class-naming-style=PascalCase
const-naming-style=UPPER_SNAKE_CASE

# 导入检查
known-standard-library=os,sys,re,json,datetime,typing,pathlib
known-third-party=fastapi,uvicorn,pydantic,langgraph,numpy,pandas
wildcard-imports=deny

# 禁用过于严格的警告
disable=W0613,R0902,R0903
```

### 代码检查命令
```bash
# 运行代码检查
pylint src/

# 检查特定模块
pylint src/agents/

# 生成HTML报告
pylint src/ --output-format=html > pylint_report.html

# 使用配置文件
pylint --rcfile=.pylintrc src/
```

### 代码格式化工具

#### Black格式化
```bash
# 格式化所有Python文件
black src/

# 检查格式化（不修改）
black --check src/

# 格式化单个文件
black src/agents/base_agent.py

# 指定行长度
black --line-length=120 src/
```

#### isort导入排序
```bash
# 排序所有导入
isort src/

# 检查导入排序（不修改）
isort --check-only src/

# 使用Black配置文件
isort --profile=black src/
```

### 类型检查

#### MyPy类型检查
```bash
# 运行类型检查
mypy src/

# 忽略缺失导入
mypy --ignore-missing-imports src/

# 严格模式
mypy --strict src/

# 生成HTML报告
mypy --html-report mypy_report src/
```

#### Pyright类型检查（可选）
```bash
# 如果安装了pyright
pyright src/
```

## 🏗️ 架构模式

### 智能体开发模式

#### BaseAgent接口
所有智能体必须继承自`BaseAgent`抽象基类：

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseAgent(ABC):
    """智能体基类
    
    所有智能体的共同接口，定义了智能体的基本行为和生命周期。
    """
    
    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """初始化智能体
        
        Args:
            config: 智能体配置
        """
        self.config = config
        self.name = config.get("name", self.__class__.__name__)
        self.capabilities = config.get("capabilities", [])
    
    @abstractmethod
    async def process(self, input_data: Any, context: Optional[Dict] = None) -> Any:
        """处理输入数据
        
        Args:
            input_data: 输入数据
            context: 可选上下文信息
            
        Returns:
            处理结果
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置
        
        Returns:
            配置是否有效
        """
        pass
    
    def get_capabilities(self) -> List[str]:
        """获取智能体能力列表
        
        Returns:
            能力列表
        """
        return self.capabilities
```

#### AgentBuilder模式
使用构建器模式创建智能体实例：

```python
class AgentBuilder:
    """智能体构建器"""
    
    def __init__(self):
        self._agent_type = None
        self._config = {}
        self._capabilities = []
    
    def set_type(self, agent_type: str) -> 'AgentBuilder':
        self._agent_type = agent_type
        return self
    
    def set_config(self, config: Dict[str, Any]) -> 'AgentBuilder':
        self._config = config
        return self
    
    def add_capability(self, capability: str) -> 'AgentBuilder':
        self._capabilities.append(capability)
        return self
    
    def build(self) -> BaseAgent:
        if not self._agent_type:
            raise ValueError("智能体类型未设置")
        
        config = {**self._config, "capabilities": self._capabilities}
        
        # 根据类型创建智能体
        if self._agent_type == "knowledge_retrieval":
            from src.agents.knowledge_retrieval_agent import KnowledgeRetrievalAgent
            return KnowledgeRetrievalAgent(config)
        elif self._agent_type == "research":
            from src.agents.research_agent import ResearchAgent
            return ResearchAgent(config)
        else:
            raise ValueError(f"未知的智能体类型: {self._agent_type}")

# 使用示例
agent = (AgentBuilder()
         .set_type("knowledge_retrieval")
         .set_config({"timeout": 30, "max_results": 10})
         .add_capability("semantic_search")
         .add_capability("keyword_search")
         .build())
```

### 错误处理模式

#### 统一错误处理服务
```python
class ErrorHandlingService:
    """统一错误处理服务"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def handle_error(
        self,
        error: Exception,
        context: str = "",
        level: str = "ERROR"
    ) -> Dict[str, Any]:
        """处理错误
        
        Args:
            error: 异常对象
            context: 错误上下文描述
            level: 日志级别
            
        Returns:
            错误响应字典
        """
        error_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # 记录错误
        log_message = f"{context}: {error}" if context else str(error)
        getattr(self.logger, level.lower())(log_message, extra={
            "error_id": error_id,
            "timestamp": timestamp,
            "error_type": error.__class__.__name__
        })
        
        # 返回标准化错误响应
        return {
            "success": False,
            "error": {
                "id": error_id,
                "message": str(error),
                "type": error.__class__.__name__,
                "timestamp": timestamp,
                "context": context
            }
        }

# 使用示例
class AgentService:
    def __init__(self):
        self.error_handler = ErrorHandlingService()
    
    def process_request(self, request: Request) -> Response:
        try:
            result = self._do_work(request)
            return Response(success=True, data=result)
        except ValueError as e:
            error_response = self.error_handler.handle_error(
                e, context="AgentService.process_request: 验证错误"
            )
            return Response(**error_response)
        except Exception as e:
            error_response = self.error_handler.handle_error(
                e, context="AgentService.process_request: 未知错误"
            )
            return Response(**error_response)
```

### 配置管理

#### 环境变量配置
```python
import os
from typing import Optional

class ConfigService:
    """配置服务"""
    
    @staticmethod
    def get_env_var(key: str, default: Optional[str] = None) -> str:
        """获取环境变量
        
        Args:
            key: 环境变量键
            default: 默认值
            
        Returns:
            环境变量值
            
        Raises:
            ValueError: 环境变量未设置且无默认值
        """
        value = os.getenv(key, default)
        if value is None:
            raise ValueError(f"环境变量 {key} 未设置且无默认值")
        return value
    
    @staticmethod
    def get_llm_provider() -> str:
        """获取LLM提供商"""
        return ConfigService.get_env_var("LLM_PROVIDER", "mock")
    
    @staticmethod
    def get_api_key(provider: str) -> Optional[str]:
        """获取API密钥"""
        if provider == "deepseek":
            return ConfigService.get_env_var("DEEPSEEK_API_KEY", None)
        elif provider == "stepflash":
            return ConfigService.get_env_var("STEPSFLASH_API_KEY", None)
        return None
```

#### 配置文件管理
```python
import yaml
from pathlib import Path

class YamlConfig:
    """YAML配置文件管理"""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def validate(self) -> bool:
        """验证配置"""
        required_keys = ["agents", "services", "database"]
        for key in required_keys:
            if key not in self._config:
                return False
        return True
```

## 📊 日志记录规范

### 结构化日志记录
```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志记录"""
        handler = logging.StreamHandler()
        formatter = StructuredFormatter()
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def info(self, message: str, **extra):
        """记录信息日志"""
        self.logger.info(message, extra=extra)
    
    def error(self, message: str, **extra):
        """记录错误日志"""
        self.logger.error(message, extra=extra)
    
    def debug(self, message: str, **extra):
        """记录调试日志"""
        self.logger.debug(message, extra=extra)

class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加额外字段
        if hasattr(record, 'extra') and record.extra:
            log_data.update(record.extra)
        
        return json.dumps(log_data, ensure_ascii=False)

# 使用示例
logger = StructuredLogger(__name__)

def process_request(request_id: str, agent_type: str):
    logger.info("开始处理请求", 
                request_id=request_id,
                agent_type=agent_type,
                timestamp=datetime.now().isoformat())
    
    try:
        # 处理逻辑
        result = do_work()
        logger.info("请求处理完成",
                    request_id=request_id,
                    result="success",
                    duration="1.2s")
        return result
    except Exception as e:
        logger.error("请求处理失败",
                     request_id=request_id,
                     error=str(e),
                     error_type=e.__class__.__name__)
        raise
```

## 🔒 安全规范

### 输入验证
```python
from typing import Any
import re

class InputValidator:
    """输入验证器"""
    
    @staticmethod
    def validate_string(value: Any, max_length: int = 1000) -> str:
        """验证字符串输入"""
        if not isinstance(value, str):
            raise TypeError(f"期望字符串，得到 {type(value).__name__}")
        
        if not value.strip():
            raise ValueError("字符串不能为空")
        
        if len(value) > max_length:
            raise ValueError(f"字符串长度不能超过 {max_length} 个字符")
        
        # 清理潜在危险字符
        cleaned = re.sub(r'[<>"\']', '', value)
        return cleaned.strip()
    
    @staticmethod
    def validate_dict(value: Any, required_keys: List[str] = None) -> Dict:
        """验证字典输入"""
        if not isinstance(value, dict):
            raise TypeError(f"期望字典，得到 {type(value).__name__}")
        
        if required_keys:
            missing_keys = [key for key in required_keys if key not in value]
            if missing_keys:
                raise ValueError(f"缺少必需键: {missing_keys}")
        
        return value
    
    @staticmethod
    def sanitize_sql_input(value: str) -> str:
        """清理SQL输入"""
        # 移除SQL注入风险字符
        dangerous_patterns = [
            r"'.*--",    # SQL注释
            r"'.*;",     # 语句结束
            r"'.*union", # UNION注入
            r"'.*select",# SELECT注入
            r"'.*drop",  # DROP注入
            r"'.*insert",# INSERT注入
            r"'.*update",# UPDATE注入
            r"'.*delete",# DELETE注入
        ]
        
        for pattern in dangerous_patterns:
            value = re.sub(pattern, '', value, flags=re.IGNORECASE)
        
        return value
```

### 安全函数使用
```python
# 禁止使用的函数
# eval()     - 可能执行任意代码
# exec()     - 可能执行任意代码
# compile()  - 可能编译任意代码
# pickle.loads() - 可能反序列化恶意对象

# 安全替代方案

# 使用ast.literal_eval代替eval
import ast

# 安全：只评估字面量表达式
safe_result = ast.literal_eval("[1, 2, 3]")

# 危险：可能执行任意代码
dangerous_result = eval("__import__('os').system('rm -rf /')")  # 禁止！

# 使用json.loads代替pickle
import json

# 安全：只解析JSON数据
safe_data = json.loads('{"key": "value"}')

# 危险：可能反序列化恶意对象
dangerous_data = pickle.loads(malicious_pickle_data)  # 禁止！
```

### 敏感数据处理
```python
import hashlib
import hmac
import secrets

class SecurityUtils:
    """安全工具类"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """哈希密码"""
        salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return f"{salt}:{hashed.hex()}"
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """验证密码"""
        try:
            salt, stored_hash = hashed_password.split(':')
            new_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            )
            return hmac.compare_digest(new_hash.hex(), stored_hash)
        except (ValueError, AttributeError):
            return False
    
    @staticmethod
    def generate_api_key() -> str:
        """生成API密钥"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def sanitize_log_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """清理日志数据，移除敏感信息"""
        sensitive_keys = ['password', 'api_key', 'token', 'secret', 'key']
        sanitized = data.copy()
        
        for key in sensitive_keys:
            if key in sanitized:
                sanitized[key] = '***REDACTED***'
        
        return sanitized
```

## 📋 预提交检查

### 预提交钩子配置
创建`.pre-commit-config.yaml`文件：

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black
        args: [--line-length=120]
        language_version: python3.9
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]
        language_version: python3.9
  
  - repo: https://github.com/pycqa/pylint
    rev: v3.0.1
    hooks:
      - id: pylint
        args:
          - --rcfile=.pylintrc
          - --fail-under=8.0
        language_version: python3.9
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.6.1
    hooks:
      - id: mypy
        args: [--ignore-missing-imports, --follow-imports=silent]
        language_version: python3.9
  
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
  
  - repo: local
    hooks:
      - id: check-node-docstrings
        name: 检查LangGraph节点文档字符串
        entry: python scripts/check_node_docstrings.py
        language: system
        pass_filenames: false
        always_run: true
      
      - id: run-unit-tests
        name: 运行单元测试
        entry: pytest tests/ -m unit
        language: system
        pass_filenames: false
        always_run: false
        stages: [push]
```

### 安装和使用
```bash
# 安装pre-commit
pip install pre-commit

# 安装预提交钩子
pre-commit install

# 运行所有钩子
pre-commit run --all-files

# 运行特定钩子
pre-commit run black --all-files
pre-commit run pylint --all-files

# 手动触发提交前检查
git commit -m "提交消息"  # 会自动运行预提交钩子
```

## 🧪 测试规范

### 测试代码规范
测试代码也需要遵循相同的代码规范：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识检索智能体测试
"""

import unittest
import asyncio
from unittest.mock import Mock, patch
from tests.test_framework import AsyncTestCase

class TestKnowledgeRetrievalAgent(AsyncTestCase):
    """知识检索智能体测试类"""
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.agent_config = {
            "name": "TestKnowledgeAgent",
            "timeout": 30,
            "max_results": 10
        }
    
    async def test_agent_initialization(self):
        """测试智能体初始化"""
        agent = KnowledgeRetrievalAgent(self.agent_config)
        self.assertEqual(agent.name, "TestKnowledgeAgent")
        self.assertEqual(agent.timeout, 30)
    
    async def test_retrieval_functionality(self):
        """测试检索功能"""
        agent = KnowledgeRetrievalAgent(self.agent_config)
        
        with patch.object(agent, '_search_vector_store') as mock_search:
            mock_search.return_value = [{"id": "1", "content": "测试内容"}]
            
            results = await agent.retrieve("测试查询")
            
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["id"], "1")
    
    async def test_error_handling(self):
        """测试错误处理"""
        agent = KnowledgeRetrievalAgent(self.agent_config)
        
        with patch.object(agent, '_search_vector_store') as mock_search:
            mock_search.side_effect = Exception("搜索失败")
            
            with self.assertRaises(Exception) as context:
                await agent.retrieve("测试查询")
            
            self.assertEqual(str(context.exception), "搜索失败")
```

## 🔄 代码审查清单

### 提交前自查清单
- [ ] 代码通过所有测试（`pytest`）
- [ ] 代码通过Pylint检查（`pylint src/`）
- [ ] 代码已格式化（`black src/`和`isort src/`）
- [ ] 类型注解完整（`mypy src/`）
- [ ] 文档字符串完整且准确
- [ ] 无硬编码的敏感信息
- [ ] 错误处理恰当
- [ ] 日志记录恰当
- [ ] 性能考虑周全
- [ ] 安全考虑周全

### 代码审查要点
1. **代码结构**
   - 是否遵循单一职责原则？
   - 函数和类是否大小合适？
   - 是否有重复代码？

2. **代码质量**
   - 命名是否清晰？
   - 类型注解是否完整？
   - 错误处理是否恰当？
   - 日志记录是否恰当？

3. **性能和安全**
   - 是否有性能问题？
   - 是否有安全漏洞？
   - 是否处理了边界情况？

4. **测试和文档**
   - 是否有足够的测试覆盖？
   - 测试是否有效？
   - 文档是否完整准确？

## 📚 学习资源

### 官方文档
- [Python官方风格指南 (PEP 8)](https://www.python.org/dev/peps/pep-0008/)
- [Python类型注解 (PEP 484)](https://www.python.org/dev/peps/pep-0484/)
- [Python文档字符串 (PEP 257)](https://www.python.org/dev/peps/pep-0257/)

### 工具文档
- [Black代码格式化器](https://black.readthedocs.io/)
- [Pylint代码检查器](https://pylint.readthedocs.io/)
- [MyPy类型检查器](https://mypy.readthedocs.io/)
- [isort导入排序器](https://pycqa.github.io/isort/)

### 项目资源
- [RANGEN测试指南](../testing/unit-testing.md)
- [RANGEN开发环境指南](development-environment.md)
- [RANGEN架构设计](../architecture/README.md)

---

*最后更新：2026-03-07*  
*文档版本：1.0.0*  
*维护团队：RANGEN开发工作组*