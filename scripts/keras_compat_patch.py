
# Keras 3.0 兼容性补丁 - 强制优先导入版本
import os
import sys
import importlib
import types
from typing import Any

print("🔧 正在应用Keras兼容性补丁...")

# 设置环境变量 - 在任何导入之前
os.environ['KERAS_BACKEND'] = 'tensorflow'
os.environ['TF_KERAS'] = '1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # 提高到3以减少警告
os.environ['TF_DISABLE_MLIR'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

print("✅ Keras环境变量已设置")

# 创建真正的模块对象作为keras兼容性存根
def create_keras_stub():
    """创建真正的模块对象作为keras兼容性存根"""
    keras_stub = types.ModuleType('keras')

    # 动态设置属性 - Pyright类型检查忽略
    setattr(keras_stub, '__version__', '2.15.0')  # 伪装成Keras 2.x版本
    setattr(keras_stub, 'backend', None)
    setattr(keras_stub, 'layers', None)
    setattr(keras_stub, 'models', None)
    setattr(keras_stub, 'utils', None)
    setattr(keras_stub, 'optimizers', None)
    setattr(keras_stub, 'callbacks', None)
    setattr(keras_stub, 'preprocessing', None)

    # 添加__getattr__方法来处理动态属性访问
    def __getattr__(name):
        # 返回一个占位符对象，避免AttributeError
        return lambda *args, **kwargs: None

    setattr(keras_stub, '__getattr__', __getattr__)

    return keras_stub

# 在sys.modules中预先插入keras，阻止真正的keras导入
if 'keras' not in sys.modules:
    sys.modules['keras'] = create_keras_stub()
    print("✅ 已预插入Keras兼容性存根")

# 创建tf_keras占位符（如果不存在）
if 'tf_keras' not in sys.modules:
    sys.modules['tf_keras'] = create_keras_stub()
    print("✅ 已预插入tf_keras兼容性存根")

# 不干预torch - 让torch正常导入
# torch的兼容性问题通过环境变量和keras存根间接解决

print("🎉 Keras兼容性补丁应用完成 - 所有keras导入将被重定向")
