#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/apple/workdata/person/zy/RANGEN-main(syu-python)')

from src.core.reasoning.learning_manager import LearningManager

lm = LearningManager(learning_enabled=True)
print("=== Before recording ===")
print("ml_parameters:", lm.learning_data.get("ml_parameters", {}))
print()

param_category = "ml_parameters"
param_name = "learning_rate"
query_type = "factual"

print("=== Checking condition flow ===")
print(f"{param_name} in {param_category}?", param_name in lm.learning_data.get(param_category, {}))

if param_name in lm.learning_data.get(param_category, {}):
    print(f"query_type {query_type} in learning_rate?", query_type in lm.learning_data[param_category][param_name])

print("\n=== Now record a result ===")
lm.record_parameter_result(param_category, param_name, query_type, 0.02, True, {"accuracy": 0.9})

print("After recording:")
print("ml_parameters:", lm.learning_data.get("ml_parameters", {}))
