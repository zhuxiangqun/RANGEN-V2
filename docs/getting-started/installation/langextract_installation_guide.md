# LangExtract 安装指南

## 一、依赖冲突问题

### 问题描述

安装 LangExtract 时可能遇到以下依赖冲突：

```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. 
This behaviour is the source of the following dependency conflicts.
google-auth-oauthlib 1.2.3 requires google-auth<2.42.0,>=2.15.0, but you have google-auth 2.45.0 which is incompatible
```

### 原因分析

- `google-auth-oauthlib 1.2.3` 要求 `google-auth<2.42.0,>=2.15.0`
- 当前环境安装了 `google-auth 2.45.0`，超出了兼容范围

## 二、解决方案

### 方案1：使用安装脚本（推荐，最简单）

```bash
bash scripts/install_langextract.sh
```

脚本会自动：
- 检测版本冲突
- 在安装 LangExtract 前固定 `google-auth` 版本
- 安装后再次检查并修复冲突
- 验证安装是否成功

### 方案2：手动安装（如果脚本无法解决）

```bash
# 步骤1：先固定 google-auth 版本（强制重新安装）
pip install "google-auth>=2.15.0,<2.42.0" --force-reinstall

# 步骤2：安装 LangExtract（可能会尝试升级 google-auth）
pip install langextract

# 步骤3：如果 google-auth 被升级，再次降级
pip show google-auth | grep "Version:"  # 检查版本
# 如果版本 >= 2.42.0，执行：
pip install "google-auth>=2.15.0,<2.42.0" --force-reinstall
```

### 方案2：升级 google-auth-oauthlib

```bash
# 升级 google-auth-oauthlib 到最新版本（如果支持更新的 google-auth）
pip install --upgrade google-auth-oauthlib

# 然后安装 LangExtract
pip install langextract
```

### 方案3：使用虚拟环境（最佳实践）

```bash
# 创建新的虚拟环境
python3 -m venv langextract_env

# 激活虚拟环境
source langextract_env/bin/activate  # macOS/Linux
# 或
langextract_env\Scripts\activate  # Windows

# 安装依赖（按顺序）
pip install "google-auth>=2.15.0,<2.42.0"
pip install google-auth-oauthlib
pip install langextract
```

### 方案4：使用 requirements 文件

```bash
# 使用项目提供的 requirements 文件
pip install -r requirements_langgraph.txt
```

## 三、验证安装

```bash
# 验证 LangExtract 是否安装成功
python -c "import langextract; print('✅ LangExtract 安装成功')"

# 检查版本
pip show langextract google-auth google-auth-oauthlib
```

## 四、配置 Google API Key

安装完成后，需要配置 Google API Key：

```bash
# 方法1：环境变量
export GOOGLE_API_KEY="your-api-key-here"

# 方法2：.env 文件
echo "GOOGLE_API_KEY=your-api-key-here" >> .env
```

## 五、常见问题

### Q1: 安装后仍然报错？

**A**: 检查是否有多个 Python 环境，确保在正确的环境中安装：

```bash
# 检查当前 Python 环境
which python
python --version

# 检查已安装的包
pip list | grep google-auth
```

### Q2: 如何获取 Google API Key？

**A**: 
1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用 Gemini API
4. 创建 API Key
5. 将 API Key 添加到环境变量或 `.env` 文件

### Q3: 是否必须使用 Google Gemini？

**A**: LangExtract 主要支持 Google Gemini 系列模型。如果需要使用其他模型，可能需要修改 LangExtract 的配置或使用其他提取库。

## 六、安装后测试

```python
# 测试脚本：test_langextract_installation.py

try:
    from langextract import LangExtract
    import os
    
    # 检查 API Key
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("⚠️ 警告: GOOGLE_API_KEY 未设置")
    else:
        print("✅ GOOGLE_API_KEY 已设置")
    
    # 尝试初始化（不实际调用 API）
    print("✅ LangExtract 模块导入成功")
    print("✅ 安装验证通过")
    
except ImportError as e:
    print(f"❌ LangExtract 导入失败: {e}")
    print("请检查安装是否正确")
except Exception as e:
    print(f"❌ 测试失败: {e}")
```

运行测试：

```bash
python test_langextract_installation.py
```

## 七、故障排除

### 问题1: pip 安装超时

```bash
# 使用国内镜像源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple langextract
```

### 问题2: 权限错误

```bash
# 使用 --user 标志
pip install --user langextract

# 或使用虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate
pip install langextract
```

### 问题3: 依赖冲突持续存在（LangExtract 安装时 google-auth 被自动升级）

**问题原因**：
- `google-cloud-storage`（LangExtract 的依赖）允许 `google-auth<3.0.0,>=2.26.1`
- 安装 LangExtract 时，pip 会自动升级 `google-auth` 到最新版本（如 2.45.0）
- 这导致与 `google-auth-oauthlib 1.2.3` 冲突（它需要 `google-auth<2.42.0`）

**快速修复**：

```bash
# 使用快速修复脚本（推荐）
bash scripts/fix_google_auth_version.sh
```

**手动修复**：

```bash
# 方法1：直接降级（最简单）
pip install "google-auth>=2.15.0,<2.42.0" --force-reinstall
```

```bash
# 方法2：使用约束文件安装
cat > constraints.txt << EOF
google-auth<2.42.0,>=2.15.0
EOF

pip install langextract -c constraints.txt
# 安装后再次检查并修复
pip install "google-auth>=2.15.0,<2.42.0" --force-reinstall
```

**验证修复**：

```bash
# 检查版本
pip show google-auth | grep "Version:"
# 应该显示版本 < 2.42.0

# 验证 LangExtract 仍然可用
python -c "import langextract; print('✅ LangExtract 可用')"
```

## 八、下一步

安装成功后，可以：

1. 查看 [LangExtract 集成方案](../architecture/langgraph_architectural_refactoring.md#十langextract-集成方案rag-增强版)
2. 开始实施集成（从阶段1开始）
3. 配置系统以使用 LangExtract

