"""
Configuration Service - Now integrated with unified error handling
"""
import os
import re
import yaml
from typing import Dict, Any, Optional
from src.services.logging_service import get_logger
from src.utils.error_handler import ErrorManager, ErrorCategory, ErrorLevel, error_boundary

logger = get_logger(__name__)

class ConfigService:
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigService, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _replace_env_var(self, match) -> str:
        """Replace environment variable in regex match"""
        var_name = match.group(1)
        default_value = match.group(2) if match.group(2) else ""
        result = os.getenv(var_name, default_value)
        return str(result) if result is not None else default_value

    def _substitute_env_vars(self, config_data: Any) -> Any:
        """Recursively substitute environment variables in config values"""
        if isinstance(config_data, dict):
            return {k: self._substitute_env_vars(v) for k, v in config_data.items()}
        elif isinstance(config_data, list):
            return [self._substitute_env_vars(item) for item in config_data]
        elif isinstance(config_data, str):
            # Handle ${VAR:default} format
            import re
            pattern = r'\$\{([^}:]+):?([^}]*)\}'
            
            def replace_var(match):
                var_name = match.group(1)
                default_value = match.group(2) if match.group(2) else ""
                result = os.getenv(var_name, default_value)
                return str(result) if result is not None else default_value
            
            return re.sub(pattern, replace_var, config_data)
        else:
            return config_data

    def _load_kms_config(self):
        """Load KMS configuration from external JSON file"""
        try:
            kms_config_path = self.get("kms.config_path", "knowledge_management_system/config/system_config.json")
            if os.path.exists(kms_config_path):
                with open(kms_config_path, 'r') as f:
                    kms_config = yaml.safe_load(f)
                    # Merge KMS config into main config
                    self._config.setdefault("kms", {}).update(kms_config)
                    logger.info(f"Loaded KMS config from {kms_config_path}")
            else:
                logger.warning(f"KMS config file not found at {kms_config_path}")
        except Exception as e:
            logger.error(f"Failed to load KMS config: {e}")

    @error_boundary(category=ErrorCategory.CONFIGURATION, level=ErrorLevel.HIGH)
    def _load_config(self):
        """Load configuration from YAML and Env vars"""
        # Load environment variables from .env file
        try:
            from dotenv import load_dotenv
            load_dotenv('.env')
        except ImportError:
            # Manual fallback if dotenv not available
            if os.path.exists('.env'):
                with open('.env', 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key] = value
        
        # 1. Load YAML
        config_path = os.getenv("RANGEN_CONFIG_PATH", "config/rangen_v2.yaml")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    raw_config = yaml.safe_load(f) or {}
                    self._config = self._substitute_env_vars(raw_config)
                logger.info(f"Loaded config from {config_path}")
            except Exception as e:
                error_manager = ErrorManager()
                error_manager.handle_error(
                    error=e,
                    category=ErrorCategory.CONFIGURATION,
                    level=ErrorLevel.HIGH,
                    context={
                        'config_path': config_path,
                        'operation': 'load_yaml_config'
                    },
                    function='_load_config'
                )
                # Use empty config as fallback
                self._config = {}
        else:
            logger.warning(f"Config file not found at {config_path}, using defaults")

        # 2. Additional direct environment overrides
        if os.getenv("LLM_PROVIDER"):
            self._config.setdefault("agents", {}).setdefault("reasoning_agent", {})["llm_provider"] = os.getenv("LLM_PROVIDER")
        
        # 3. Load KMS configuration if enabled
        if self.get("kms.enabled", True):
            self._load_kms_config()

    @error_boundary(category=ErrorCategory.CONFIGURATION, level=ErrorLevel.LOW)
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get config value by dot-notation path (e.g. 'agents.reasoning_agent.model')
        """
        keys = key_path.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            
            if value is None:
                return default
                
        return value

# Global accessor
def get_config() -> ConfigService:
    return ConfigService()
