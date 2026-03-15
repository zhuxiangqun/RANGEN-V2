-- AI中台管理平台 v1.0 数据库表结构
-- 创建时间: 2026-03-02

-- Agents表 - 存储AI智能体配置
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'agent',
    description TEXT,
    config_path TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reference_count INTEGER DEFAULT 0
);

-- Skills表 - 存储技能组合
CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    tools TEXT,
    config_path TEXT,
    source TEXT,
    priority INTEGER DEFAULT 100,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extension_reason TEXT,
    reference_count INTEGER DEFAULT 0
);

-- Tools表 - 存储工具定义
CREATE TABLE IF NOT EXISTS tools (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    type TEXT,
    source TEXT,
    priority INTEGER DEFAULT 100,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent-Skill关联表
CREATE TABLE IF NOT EXISTS agent_skills (
    agent_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (agent_id, skill_id),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

-- Agent-Tool关联表
CREATE TABLE IF NOT EXISTS agent_tools (
    agent_id TEXT NOT NULL,
    tool_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (agent_id, tool_id),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    FOREIGN KEY (tool_id) REFERENCES tools(id) ON DELETE CASCADE
);

-- Skill-Tool关联表
CREATE TABLE IF NOT EXISTS skill_tools (
    skill_id TEXT NOT NULL,
    tool_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (skill_id, tool_id),
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE,
    FOREIGN KEY (tool_id) REFERENCES tools(id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_skills_status ON skills(status);
CREATE INDEX IF NOT EXISTS idx_tools_status ON tools(status);
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(type);

-- =============================================================================
-- AI中台模型管理 v2.0 - 模型市场、微调、训练
-- =============================================================================

-- 模型供应商表
CREATE TABLE IF NOT EXISTS model_providers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT,
    website TEXT,
    api_type TEXT NOT NULL DEFAULT 'openai_compatible',
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 模型表
CREATE TABLE IF NOT EXISTS models (
    id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL,
    name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    model_type TEXT NOT NULL,
    description TEXT,
    strengths TEXT,
    context_length INTEGER DEFAULT 4096,
    supports_function_calling BOOLEAN DEFAULT 0,
    supports_vision BOOLEAN DEFAULT 0,
    input_price REAL DEFAULT 0,
    output_price REAL DEFAULT 0,
    is_local BOOLEAN DEFAULT 0,
    ollama_model_name TEXT,
    status TEXT DEFAULT 'active',
    is_default BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (provider_id) REFERENCES model_providers(id) ON DELETE CASCADE
);

-- 微调任务表
CREATE TABLE IF NOT EXISTS fine_tune_tasks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    base_model_id TEXT NOT NULL,
    description TEXT,
    data_source_type TEXT NOT NULL,
    data_source_path TEXT,
    data_source_url TEXT,
    data_format TEXT NOT NULL,
    epochs INTEGER DEFAULT 3,
    learning_rate REAL DEFAULT 0.0001,
    batch_size INTEGER DEFAULT 4,
    status TEXT DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    output_model_name TEXT,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (base_model_id) REFERENCES models(id) ON DELETE SET NULL
);

-- 训练任务表
CREATE TABLE IF NOT EXISTS training_tasks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    base_model_id TEXT,
    description TEXT,
    model_type TEXT NOT NULL,
    training_data_type TEXT NOT NULL,
    data_source_path TEXT,
    data_source_url TEXT,
    data_format TEXT NOT NULL,
    epochs INTEGER DEFAULT 10,
    learning_rate REAL DEFAULT 0.00001,
    batch_size INTEGER DEFAULT 8,
    vocabulary_size INTEGER,
    seq_length INTEGER DEFAULT 512,
    status TEXT DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    current_epoch INTEGER DEFAULT 0,
    current_loss REAL,
    output_model_name TEXT,
    error_message TEXT,
    config_json TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (base_model_id) REFERENCES models(id) ON DELETE SET NULL
);

-- 模型使用记录表
CREATE TABLE IF NOT EXISTS model_usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    duration_ms INTEGER DEFAULT 0,
    status TEXT DEFAULT 'success',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
);

-- 训练指标记录表
CREATE TABLE IF NOT EXISTS training_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    task_type TEXT NOT NULL,
    epoch INTEGER,
    step INTEGER,
    loss REAL,
    accuracy REAL,
    learning_rate REAL,
    batch_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_models_provider ON models(provider_id);
CREATE INDEX IF NOT EXISTS idx_models_type ON models(model_type);
CREATE INDEX IF NOT EXISTS idx_models_status ON models(status);
CREATE INDEX IF NOT EXISTS idx_fine_tune_status ON fine_tune_tasks(status);
CREATE INDEX IF NOT EXISTS idx_training_status ON training_tasks(status);
CREATE INDEX IF NOT EXISTS idx_model_usage_model ON model_usage_logs(model_id);
CREATE INDEX IF NOT EXISTS idx_model_usage_created ON model_usage_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_training_metrics_task ON training_metrics(task_id);

-- 插入默认模型供应商
INSERT OR IGNORE INTO model_providers (id, name, display_name, description, api_type, status) VALUES
    ('deepseek', 'deepseek', 'DeepSeek', '中国领先的AI模型提供商，推理能力强', 'openai_compatible', 'active'),
    ('openai', 'openai', 'OpenAI', '美国AI研究实验室，GPT系列（外部LLM只使用DeepSeek，此供应商已停用）', 'openai', 'inactive'),
    ('anthropic', 'anthropic', 'Anthropic', '美国AI安全公司，Claude系列（外部LLM只使用DeepSeek，此供应商已停用）', 'anthropic', 'inactive'),
    ('ollama', 'ollama', 'Ollama', '本地开源大模型运行平台', 'ollama', 'active'),
    ('huggingface', 'huggingface', 'HuggingFace', 'AI模型社区，支持微调训练', 'huggingface', 'active');

-- 插入默认模型
INSERT OR IGNORE INTO models (id, provider_id, name, display_name, model_type, description, strengths, context_length, is_default, status) VALUES
    ('deepseek-reasoner', 'deepseek', 'deepseek-reasoner', 'DeepSeek Reasoner', 'llm', '最新深度推理模型，数学和逻辑能力强', '["推理能力强", "数学逻辑", "代码生成"]', 64000, 1, 'active'),
    ('deepseek-chat', 'deepseek', 'deepseek-chat', 'DeepSeek Chat', 'llm', '通用对话模型，性价比高', '["对话流畅", "中文优化", "低成本"]', 64000, 0, 'active'),
    ('gpt-4o', 'openai', 'gpt-4o', 'GPT-4o', 'llm', 'OpenAI最新旗舰模型，GPT-4优化版（外部LLM只使用DeepSeek，此模型已停用）', '["综合能力强", "多模态", "最新技术"]', 128000, 0, 'inactive'),
    ('gpt-4o-mini', 'openai', 'gpt-4o-mini', 'GPT-4o Mini', 'llm', '小型快速模型，成本低（外部LLM只使用DeepSeek，此模型已停用）', '["快速响应", "低成本", "高性价比"]', 128000, 0, 'inactive'),
    ('claude-3-5-sonnet', 'anthropic', 'claude-3-5-sonnet', 'Claude 3.5 Sonnet', 'llm', 'Anthropic最新模型，代码和分析能力强（外部LLM只使用DeepSeek，此模型已停用）', '["代码能力", "分析推理", "长文本"]', 200000, 0, 'inactive'),
    ('claude-3-haiku', 'anthropic', 'claude-3-haiku', 'Claude 3 Haiku', 'llm', '快速响应模型（外部LLM只使用DeepSeek，此模型已停用）', '["快速响应", "低成本", "低延迟"]', 200000, 0, 'inactive'),
    ('llama3-70b', 'ollama', 'llama3:70b', 'Llama 3 70B', 'llm', 'Meta开源大模型', '["开源免费", "本地运行", "可定制"]', 8192, 0, 'active'),
    ('qwen2.5-72b', 'ollama', 'qwen2.5:72b', 'Qwen 2.5 72B', 'llm', '阿里开源中文大模型', '["中文优化", "开源免费", "本地运行"]', 32768, 0, 'active'),
    ('phi3-medium', 'ollama', 'phi3:medium', 'Phi-3 Medium', 'llm', 'Microsoft轻量级模型', '["轻量高效", "本地运行", "低资源"]', 4096, 0, 'active'),
    ('text-embedding-3-small', 'openai', 'text-embedding-3-small', 'OpenAI Embedding', 'embedding', 'OpenAI最新向量化模型（外部LLM只使用DeepSeek，此模型已停用）', '["高精度", "1536维"]', 8192, 0, 'inactive'),
    ('all-mpnet-base-v2', 'ollama', 'all-mpnet-base-v2', 'MPNet Base V2', 'embedding', '本地向量化模型，HuggingFace出品', '["本地免费", "768维", "高精度"]', 384, 0, 'active');