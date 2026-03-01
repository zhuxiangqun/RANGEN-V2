"""
RANGEN Unified Configuration System
Single entry point for all configuration with environment presets support.
"""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from enum import Enum


class Environment(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class LLMProvider(Enum):
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    MOCK = "mock"
    ANTHROPIC = "anthropic"


@dataclass
class SystemConfig:
    name: str = "RANGEN V2"
    version: str = "2.0.0"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"


@dataclass
class LLMConfig:
    provider: str = "deepseek"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    reasoning_model: str = "deepseek-reasoner"
    validation_model: str = "deepseek-chat"
    citation_model: str = "deepseek-chat"
    fallback_model: str = "deepseek-chat"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-3.5-turbo"


@dataclass
class KnowledgeBaseConfig:
    vector_store_path: str = "./data/vector_store"
    embedding_model: str = "all-mpnet-base-v2"
    local_embedding_model: str = "all-MiniLM-L6-v2"
    cache_dir: str = "~/.cache/huggingface/hub"
    use_local_models: bool = True
    auto_download: bool = True


@dataclass
class KMSConfig:
    enabled: bool = True
    config_path: str = "knowledge_management_system/config/system_config.json"
    host: str = "localhost"
    port: int = 8001
    timeout: int = 30
    retry_attempts: int = 3
    vector_rerank: bool = True
    small_to_big_retrieval: bool = True
    knowledge_graph: bool = True
    multi_modal: bool = False
    default_top_k: int = 15
    similarity_threshold: float = 0.6
    max_content_length: int = 2000000


@dataclass
class NeuralModelsConfig:
    primary_embedding: str = "all-mpnet-base-v2"
    secondary_embedding: str = "all-MiniLM-L6-v2"
    model_cache_dir: str = "~/.cache/huggingface/hub"
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    cross_encoder_enabled: bool = True


@dataclass
class AgentConfig:
    reasoning_enabled: bool = True
    reasoning_llm_provider: str = "deepseek"
    reasoning_model: str = "deepseek-reasoner"
    reasoning_timeout: int = 60
    reasoning_max_tokens: int = 8192
    validation_enabled: bool = True
    validation_llm_provider: str = "deepseek"
    validation_model: str = "deepseek-chat"
    validation_timeout: int = 30
    citation_enabled: bool = True
    citation_llm_provider: str = "deepseek"
    citation_model: str = "deepseek-chat"
    citation_timeout: int = 15
    workspace_enabled: bool = False
    workspace_root: str = "./workspace"


@dataclass
class PerformanceConfig:
    max_concurrent_tasks: int = 10
    task_timeout: int = 300
    memory_limit: str = "2048MB"
    deduplication_window: int = 60
    long_term_cache_window: int = 300


@dataclass
class RetrievalConfig:
    max_query_length: int = 1000
    top_k_results: int = 5
    enable_reranking: bool = True
    rerank_top_k: int = 10
    enable_context_expansion: bool = True
    context_expansion_threshold: float = 1.3


@dataclass
class SecurityConfig:
    input_validation_enabled: bool = True
    max_query_length: int = 10000
    rate_limiting_enabled: bool = True
    requests_per_minute: int = 60


@dataclass
class MonitoringConfig:
    enabled: bool = True
    metrics_interval: int = 30
    health_check_enabled: bool = True
    performance_tracking: bool = True


@dataclass
class IntegrationsConfig:
    langgraph_enabled: bool = True
    langgraph_fallback_on_error: bool = True
    opentelemetry_enabled: bool = False
    opentelemetry_service_name: str = "rangen-v2"
    opentelemetry_endpoint: str = "http://localhost:4317"


class UnifiedConfig:
    """Unified Configuration System - Single entry point for all config."""
    
    def __init__(self, config_dir: str = "config"):
        self._config_dir = Path(config_dir)
        self._environment = Environment.DEVELOPMENT
        self._raw_config: Dict[str, Any] = {}
        
        self.system = SystemConfig()
        self.llm = LLMConfig()
        self.knowledge_base = KnowledgeBaseConfig()
        self.kms = KMSConfig()
        self.neural_models = NeuralModelsConfig()
        self.agents = AgentConfig()
        self.performance = PerformanceConfig()
        self.retrieval = RetrievalConfig()
        self.security = SecurityConfig()
        self.monitoring = MonitoringConfig()
        self.integrations = IntegrationsConfig()
    
    @property
    def environment(self) -> str:
        return self._environment.value
    
    @property
    def is_production(self) -> bool:
        return self._environment == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        return self._environment == Environment.DEVELOPMENT
    
    @property
    def is_testing(self) -> bool:
        return self._environment == Environment.TESTING
    
    def load(self, environment: Optional[str] = None, config_path: Optional[str] = None) -> "UnifiedConfig":
        if environment:
            self._environment = Environment(environment)
        
        self._load_env_file()
        
        if config_path is None:
            preset_path = self._config_dir / "environments" / f"{self._environment.value}.yaml"
            if preset_path.exists():
                config_path = str(preset_path)
            else:
                config_path = str(self._config_dir / "rangen_v2.yaml")
        
        if os.path.exists(config_path):
            self._load_yaml(config_path)
        
        self._apply_env_overrides()
        self._apply_to_models()
        
        return self
    
    def _load_env_file(self):
        for env_path in [".env", ".env.local"]:
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
    
    def _load_yaml(self, path: str):
        import re
        with open(path, 'r') as f:
            raw = yaml.safe_load(f) or {}
        self._raw_config = self._substitute_env_vars(raw)
    
    def _substitute_env_vars(self, data: Any) -> Any:
        import re
        if isinstance(data, dict):
            return {k: self._substitute_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._substitute_env_vars(item) for item in data]
        elif isinstance(data, str):
            pattern = r'\$\{([^}:]+):?([^}]*)\}'
            def replace_var(match):
                var_name = match.group(1)
                default_value = match.group(2) if match.group(2) else ""
                result = os.getenv(var_name, default_value)
                return str(result) if result is not None else default_value
            return re.sub(pattern, replace_var, data)
        return data
    
    def _apply_env_overrides(self):
        env_mappings = {
            "ENVIRONMENT": ("system", "environment"),
            "DEBUG": ("system", "debug", lambda v: v.lower() == "true"),
            "LOG_LEVEL": ("system", "log_level"),
            "LLM_PROVIDER": ("llm", "provider"),
            "DEEPSEEK_API_KEY": ("llm", "deepseek_api_key"),
            "OPENAI_API_KEY": ("llm", "openai_api_key"),
            "VECTOR_STORE_PATH": ("knowledge_base", "vector_store_path"),
            "EMBEDDING_MODEL": ("knowledge_base", "embedding_model"),
            "KMS_ENABLED": ("kms", "enabled", lambda v: v.lower() == "true"),
            "MAX_CONCURRENT_TASKS": ("performance", "max_concurrent_tasks", int),
            "TASK_TIMEOUT": ("performance", "task_timeout", int),
            "TOP_K_RESULTS": ("retrieval", "top_k_results", int),
            "ENABLE_RERANKING": ("retrieval", "enable_reranking", lambda v: v.lower() == "true"),
            "RATE_LIMITING": ("security", "rate_limiting_enabled", lambda v: v.lower() == "true"),
            "REQUESTS_PER_MINUTE": ("security", "requests_per_minute", int),
        }
        
        for env_var, mapping in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    section, attr = mapping[0], mapping[1]
                    converter = mapping[2] if len(mapping) > 2 else str
                    converted = converter(value)
                    setattr(getattr(self, section), attr, converted)
                except Exception:
                    pass
    
    def _apply_to_models(self):
        raw = self._raw_config
        
        if "system" in raw:
            for k, v in raw["system"].items():
                if hasattr(self.system, k):
                    setattr(self.system, k, v)
        
        if "llm" in raw:
            llm_data = raw["llm"]
            if "provider" in llm_data:
                setattr(self.llm, "provider", llm_data["provider"])
            for provider in ["deepseek", "openai"]:
                if provider in llm_data:
                    for k, v in llm_data[provider].items():
                        attr_name = f"{provider}_{k}"
                        if hasattr(self.llm, attr_name):
                            setattr(self.llm, attr_name, v)
        
        for section_name in ["knowledge_base", "performance", "retrieval", "monitoring"]:
            if section_name in raw:
                section = getattr(self, section_name)
                for k, v in raw[section_name].items():
                    if hasattr(section, k):
                        setattr(section, k, v)
        
        if "kms" in raw:
            for k, v in raw["kms"].items():
                if k != "service" and k != "features" and k != "performance":
                    if hasattr(self.kms, k):
                        setattr(self.kms, k, v)
        
        if "neural_models" in raw:
            nm_data = raw["neural_models"]
            if "embedding" in nm_data:
                emb = nm_data["embedding"]
                if "primary_model" in emb:
                    setattr(self.neural_models, "primary_embedding", emb["primary_model"])
                if "secondary_model" in emb:
                    setattr(self.neural_models, "secondary_embedding", emb["secondary_model"])
            if "cross_encoder" in nm_data:
                ce = nm_data["cross_encoder"]
                if "model_name" in ce:
                    setattr(self.neural_models, "cross_encoder_model", ce["model_name"])
                if "enabled" in ce:
                    setattr(self.neural_models, "cross_encoder_enabled", ce["enabled"])
        
        if "agents" in raw:
            for agent_type in ["reasoning_agent", "validation_agent", "citation_agent"]:
                if agent_type in raw["agents"]:
                    agent_data = raw["agents"][agent_type]
                    prefix = agent_type.replace("_agent", "")
                    for k, v in agent_data.items():
                        attr_name = f"{prefix}_{k}"
                        if hasattr(self.agents, attr_name):
                            setattr(self.agents, attr_name, v)
        
        if "security" in raw:
            sec_data = raw["security"]
            for key in ["input_validation", "rate_limiting"]:
                if key in sec_data:
                    for k, v in sec_data[key].items():
                        attr_name = f"{key.replace('_', '_')}_{k}"
                        if key == "input_validation":
                            attr_name = f"input_validation_{k}" if k != "enabled" else f"input_validation_enabled"
                        elif key == "rate_limiting":
                            attr_name = f"rate_limiting_{k}" if k != "enabled" else f"rate_limiting_enabled"
                        if hasattr(self.security, attr_name):
                            setattr(self.security, attr_name, v)
        
        if "integrations" in raw:
            int_data = raw["integrations"]
            for key in ["langgraph", "opentelemetry"]:
                if key in int_data:
                    for k, v in int_data[key].items():
                        attr_name = f"{key}_{k}"
                        if hasattr(self.integrations, attr_name):
                            setattr(self.integrations, attr_name, v)
    
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        obj = self
        for k in keys:
            if hasattr(obj, k):
                obj = getattr(obj, k)
            else:
                return default
        return obj
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "system": asdict(self.system),
            "llm": asdict(self.llm),
            "knowledge_base": asdict(self.knowledge_base),
            "kms": asdict(self.kms),
            "neural_models": asdict(self.neural_models),
            "agents": asdict(self.agents),
            "performance": asdict(self.performance),
            "retrieval": asdict(self.retrieval),
            "security": asdict(self.security),
            "monitoring": asdict(self.monitoring),
            "integrations": asdict(self.integrations),
        }


def get_unified_config(environment: Optional[str] = None, config_dir: str = "config") -> UnifiedConfig:
    config = UnifiedConfig(config_dir)
    config.load(environment=environment)
    return config


_config_instance: Optional[UnifiedConfig] = None


def get_config() -> UnifiedConfig:
    global _config_instance
    if _config_instance is None:
        _config_instance = get_unified_config()
    return _config_instance
