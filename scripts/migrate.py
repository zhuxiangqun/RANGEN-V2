"""
Migration Script for RANGEN v2
"""
import os
import yaml
import json
from typing import Dict, Any

def load_old_config(config_dir: str) -> Dict[str, Any]:
    """Load configuration from potential old sources"""
    old_config = {}
    
    # Try loading production_config.yaml
    prod_yaml = os.path.join(config_dir, "production_config.yaml")
    if os.path.exists(prod_yaml):
        print(f"Loading {prod_yaml}...")
        with open(prod_yaml, 'r') as f:
            old_config.update(yaml.safe_load(f) or {})

    # Try loading system_config.json
    sys_json = os.path.join(config_dir, "system_config.json")
    if os.path.exists(sys_json):
        print(f"Loading {sys_json}...")
        with open(sys_json, 'r') as f:
            old_config.update(json.load(f))
            
    return old_config

def transform_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """Transform old configuration to new RANGEN v2 schema"""
    
    # Default V2 Structure
    new_config = {
        "system": {
            "name": "rangen",
            "version": "2.0.0",
            "environment": old_config.get("environment", "production")
        },
        "routing": {
            "default_strategy": "react",
            "strategies": [
                {"name": "react", "enabled": True, "priority": 1},
                {"name": "cot", "enabled": True, "priority": 2},
                {"name": "direct", "enabled": True, "priority": 3}
            ]
        },
        "agents": {
            "reasoning_agent": {
                "model": old_config.get("model_name", "gpt-4"),
                "temperature": old_config.get("temperature", 0.7),
                "max_tokens": old_config.get("max_tokens", 2000),
                "max_iterations": 5
            },
            "retrieval_agent": {
                "top_k": old_config.get("top_k", 5),
                "similarity_threshold": old_config.get("similarity_threshold", 0.7),
                "use_rerank": True
            }
        },
        "knowledge_base": {
            "vector_store_path": old_config.get("vector_store_path", "./data/vector_store"),
            "embedding_model": old_config.get("embedding_model", "text-embedding-3-small")
        }
    }
    
    return new_config

def save_new_config(new_config: Dict[str, Any], output_path: str):
    """Save the new configuration file"""
    with open(output_path, 'w') as f:
        yaml.dump(new_config, f, default_flow_style=False, sort_keys=False)
    print(f"Successfully migrated configuration to: {output_path}")

def main():
    base_dir = os.getcwd()
    config_dir = os.path.join(base_dir, "config")
    output_path = os.path.join(config_dir, "rangen_v2.yaml")
    
    print("Starting RANGEN Configuration Migration...")
    
    try:
        old_config = load_old_config(config_dir)
        if not old_config:
            print("Warning: No existing configuration found. Generating default v2 config.")
        
        new_config = transform_config(old_config)
        save_new_config(new_config, output_path)
        
        print("\nMigration Complete!")
        print(f"Please review {output_path} and update any placeholder values.")
        
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    main()
