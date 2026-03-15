# 🔑 API密钥设置和验证指南

## 📋 当前问题

通过精确分析发现，RAGExpert的"成功率提升"是假象：
- **真实情况**：强制完整模式成功率仍为60%，API密钥无效
- **表面现象**：轻量级模式100%成功率仅为模拟结果
- **根本原因**：DEEPSEEK_API_KEY在沙箱环境中无法正确读取

## 🚀 解决方案

### 方法1：环境变量设置（推荐）

```bash
# 1. 设置环境变量
export DEEPSEEK_API_KEY="sk-your-actual-deepseek-key-here"
export USE_LIGHTWEIGHT_RAG="false"  # 强制使用完整模式

# 2. 验证设置
echo "API Key set:" $DEEPSEEK_API_KEY

# 3. 运行验证测试
python diagnostics/api_key_validation_test.py
```

### 方法2：使用设置脚本

```bash
# 编辑脚本设置真实密钥
nano diagnostics/test_with_env_vars.sh

# 修改这一行：
export DEEPSEEK_API_KEY="your-actual-key-here"

# 运行脚本
chmod +x diagnostics/test_with_env_vars.sh
./diagnostics/test_with_env_vars.sh
```

### 方法3：临时测试密钥

```bash
# 使用测试密钥进行验证（需要网络权限）
export DEEPSEEK_API_KEY="sk-test-key-for-validation"
export USE_LIGHTWEIGHT_RAG="false"
python diagnostics/api_key_validation_test.py
```

## 🔍 验证步骤

### 步骤1：检查密钥访问
```bash
python -c "
import os
from src.core.config_loader import get_deepseek_api_key
from src.utils.unified_centers import get_unified_config_center

print('环境变量:', '✅' if os.getenv('DEEPSEEK_API_KEY') else '❌')
print('智能加载器:', '✅' if get_deepseek_api_key() else '❌')

config_center = get_unified_config_center()
config_key = config_center.get_env_config('llm', 'DEEPSEEK_API_KEY', '')
print('配置中心:', '✅' if config_key else '❌')
"
```

### 步骤2：测试API调用
```bash
# 运行完整验证
python diagnostics/api_key_validation_test.py
```

### 步骤3：验证RAGExpert行为
```bash
# 测试前：强制完整模式
export USE_LIGHTWEIGHT_RAG="false"
python diagnostics/rag_success_rate_analysis.py

# 测试后：如果API密钥有效，应该看到真实LLM调用成功率提升
```

## 📊 预期结果

### ✅ API密钥有效时
```
🔑 密钥访问状态:
   环境变量: ✅
   配置中心: ✅
   智能加载器: ✅

🔗 API调用状态:
   调用成功: ✅
   响应时间: 1.23s

🏆 总体评估:
   ✅ API密钥完全可用！系统可以正常进行LLM调用
```

### ❌ API密钥无效时
```
🔑 密钥访问状态:
   环境变量: ❌
   配置中心: ❌
   智能加载器: ❌

🏆 总体评估:
   ❌ API密钥无法访问
```

## 💡 关键要点

1. **环境变量优先级最高**：直接`export`设置最可靠
2. **沙箱限制**：`.env`文件在沙箱中无法读取
3. **验证完整性**：需要同时验证密钥访问和API调用
4. **降级策略**：API无效时自动启用轻量级模式

## 🎯 后续行动

1. **立即执行**：设置有效的DEEPSEEK_API_KEY环境变量
2. **验证测试**：运行`api_key_validation_test.py`确认生效
3. **性能对比**：比较轻量级模式 vs 完整模式的真实性能
4. **文档更新**：根据测试结果更新系统状态文档
