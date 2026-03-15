# 异构系统数据自动发现与标准化 - 详细技术规格说明书

## 文档概述

### 1.1 文档目的
本文档提供异构系统数据自动发现与标准化引擎的详细技术规格，包括API接口定义、数据库设计、算法实现、部署架构和测试策略。本规格说明书面向技术架构师、开发工程师和运维人员。

### 1.2 适用范围
- 系统架构设计参考
- 开发实现指导
- 部署和运维指导
- 测试和质量保证

### 1.3 引用文档
- [HETEROGENEOUS_DATA_DISCOVERY_AND_STANDARDIZATION_DESIGN.md](file:///Users/apple/workdata/person/zy/RANGEN-main(syu-python)/HETEROGENEOUS_DATA_DISCOVERY_AND_STANDARDIZATION_DESIGN.md) - 总体设计方案
- [DATA_GOVERNANCE_CAPABILITY_ANALYSIS.md](file:///Users/apple/workdata/person/zy/RANGEN-main(syu-python)/DATA_GOVERNANCE_CAPABILITY_ANALYSIS.md) - 数据治理能力分析

---

## 第二章 API接口详细设计

### 2.1 API总体设计

#### 2.1.1 API架构原则
1. **RESTful设计**：遵循RESTful最佳实践
2. **版本控制**：通过URL路径进行版本控制 (/api/v1/)
3. **认证授权**：集成RANGEN统一安全中心
4. **文档化**：自动生成OpenAPI/Swagger文档
5. **错误处理**：统一错误响应格式

#### 2.1.2 API端点概览

| 模块 | 端点前缀 | 主要功能 |
|------|----------|----------|
| 数据源管理 | `/api/v1/data-sources` | 数据源增删改查、连接测试 |
| Schema发现 | `/api/v1/discovery` | Schema发现、数据采样 |
| 标准管理 | `/api/v1/standards` | 数据标准定义和管理 |
| 映射管理 | `/api/v1/mappings` | 映射规则生成和管理 |
| 质量评估 | `/api/v1/quality` | 数据质量评估和监控 |
| 报告生成 | `/api/v1/reports` | 分析报告生成和导出 |

### 2.2 数据源管理API

#### 2.2.1 创建数据源
```http
POST /api/v1/data-sources
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "ERP系统数据库",
  "type": "jdbc",
  "connection_config": {
    "driver": "oracle.jdbc.OracleDriver",
    "url": "jdbc:oracle:thin:@//localhost:1521/ERPDEV",
    "username": "readonly_user",
    "password": "encrypted_password",
    "properties": {
      "fetchSize": 1000,
      "queryTimeout": 30
    }
  },
  "security_level": "confidential",
  "description": "公司ERP系统生产数据库"
}
```

**响应示例**：
```json
{
  "id": "ds_abc123def456",
  "name": "ERP系统数据库",
  "type": "jdbc",
  "status": "connected",
  "connection_test_result": {
    "success": true,
    "latency_ms": 125,
    "version": "Oracle 19c"
  },
  "created_at": "2024-01-15T10:30:00Z",
  "created_by": "user123"
}
```

#### 2.2.2 数据源Schema发现
```http
POST /api/v1/data-sources/{data_source_id}/discover
Content-Type: application/json
Authorization: Bearer <token>

{
  "discovery_options": {
    "include_tables": ["CUSTOMER%", "ORDER%"],
    "exclude_tables": ["TEMP_%", "BACKUP_%"],
    "sample_size": 1000,
    "analyze_relationships": true,
    "infer_business_meaning": true
  },
  "priority": "high"
}
```

**异步响应**：
```json
{
  "job_id": "job_xyz789abc012",
  "status": "queued",
  "estimated_duration_seconds": 300,
  "progress_url": "/api/v1/jobs/job_xyz789abc012"
}
```

### 2.3 Schema发现API

#### 2.3.1 获取Schema发现结果
```http
GET /api/v1/discovery/{job_id}/results
Authorization: Bearer <token>
```

**响应示例**：
```json
{
  "job_id": "job_xyz789abc012",
  "status": "completed",
  "started_at": "2024-01-15T10:35:00Z",
  "completed_at": "2024-01-15T10:38:30Z",
  "results": {
    "tables_discovered": 128,
    "fields_analyzed": 2450,
    "data_sampled_mb": 125.5,
    "schema_details": {
      "tables": [
        {
          "id": "tbl_customer_001",
          "name": "CUSTOMER_MASTER",
          "estimated_row_count": 1250000,
          "fields": [
            {
              "name": "CUST_ID",
              "db_type": "NUMBER(10)",
              "inferred_type": "integer",
              "features": {
                "unique_values": 1250000,
                "null_percentage": 0.0,
                "min_value": 1000001,
                "max_value": 2250000,
                "is_primary_key": true,
                "is_foreign_key": false
              },
              "sample_values": [1000001, 1000002, 1000003],
              "business_meaning": {
                "confidence": 0.95,
                "meaning": "客户唯一标识",
                "standard_field_suggestion": "customer_id"
              }
            },
            {
              "name": "CUST_NAME",
              "db_type": "VARCHAR2(100)",
              "inferred_type": "string",
              "features": {
                "unique_values": 1248000,
                "null_percentage": 0.1,
                "min_length": 2,
                "max_length": 95,
                "pattern": "中文字符+英文可选"
              },
              "business_meaning": {
                "confidence": 0.98,
                "meaning": "客户名称",
                "standard_field_suggestion": "customer_name"
              }
            }
          ]
        }
      ]
    }
  }
}
```

### 2.4 数据标准管理API

#### 2.4.1 创建数据标准
```http
POST /api/v1/standards
Content-Type: application/json
Authorization: Bearer <token>

{
  "domain": "customer",
  "name": "客户主数据标准v1.0",
  "description": "客户主数据的企业级标准定义",
  "tables": [
    {
      "name": "customer",
      "description": "客户基本信息表",
      "fields": [
        {
          "name": "customer_id",
          "data_type": "bigint",
          "format": "CUST{10位数字}",
          "description": "客户唯一标识",
          "constraints": {
            "required": true,
            "unique": true,
            "min_value": 1000000000,
            "max_value": 9999999999
          },
          "validation_rules": [
            {
              "type": "regex",
              "pattern": "^CUST\\d{10}$",
              "error_message": "客户ID格式错误，应为CUST+10位数字"
            }
          ]
        },
        {
          "name": "customer_name",
          "data_type": "varchar",
          "max_length": 100,
          "description": "客户名称",
          "constraints": {
            "required": true,
            "min_length": 2,
            "max_length": 100
          }
        }
      ]
    }
  ]
}
```

### 2.5 映射规则生成API

#### 2.5.1 生成映射规则
```http
POST /api/v1/mappings/generate
Content-Type: application/json
Authorization: Bearer <token>

{
  "source_schema_id": "tbl_customer_001",
  "target_standard_id": "std_customer_v1",
  "mapping_strategy": "intelligent",
  "options": {
    "auto_resolve_conflicts": true,
    "generate_transformation_code": true,
    "target_platform": "spark_sql"
  }
}
```

**响应示例**：
```json
{
  "mapping_id": "map_123456789",
  "status": "generated",
  "source_schema": "CUSTOMER_MASTER",
  "target_standard": "customer",
  "field_mappings": [
    {
      "source_field": "CUST_ID",
      "target_field": "customer_id",
      "transformation": {
        "type": "direct_mapping",
        "function": "CAST(source.CUST_ID AS STRING)",
        "validation": {
          "required": true,
          "not_null": true,
          "format_check": "regex:^CUST\\d{10}$"
        }
      },
      "confidence": 0.98
    },
    {
      "source_field": "CUST_NAME",
      "target_field": "customer_name",
      "transformation": {
        "type": "direct_mapping",
        "function": "TRIM(source.CUST_NAME)",
        "validation": {
          "required": true,
          "max_length": 100
        }
      },
      "confidence": 0.95
    }
  ],
  "generated_code": {
    "spark_sql": "SELECT \n  CONCAT('CUST', LPAD(CAST(CUST_ID AS STRING), 10, '0')) AS customer_id,\n  TRIM(CUST_NAME) AS customer_name\nFROM erp.CUSTOMER_MASTER",
    "python_pandas": "import pandas as pd\ndef transform_customer(df):\n    df['customer_id'] = 'CUST' + df['CUST_ID'].astype(str).str.zfill(10)\n    df['customer_name'] = df['CUST_NAME'].str.strip()\n    return df"
  }
}
```

---

## 第三章 数据库详细设计

### 3.1 物理数据模型

#### 3.1.1 数据源管理表
```sql
-- 数据源表
CREATE TABLE data_sources (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('jdbc', 'api', 'file', 'cdc', 'cloud')),
    connection_config JSONB NOT NULL,
    security_level VARCHAR(20) NOT NULL DEFAULT 'internal' 
        CHECK (security_level IN ('public', 'internal', 'confidential', 'restricted')),
    status VARCHAR(20) NOT NULL DEFAULT 'disconnected'
        CHECK (status IN ('disconnected', 'connected', 'error', 'disabled')),
    last_connection_test TIMESTAMP,
    last_connection_result JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    
    -- 索引
    INDEX idx_data_sources_type (type),
    INDEX idx_data_sources_status (status),
    INDEX idx_data_sources_security (security_level)
);

-- 数据源连接审计表
CREATE TABLE data_source_audit_logs (
    id BIGSERIAL PRIMARY KEY,
    data_source_id VARCHAR(36) REFERENCES data_sources(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    user_id VARCHAR(255),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    
    INDEX idx_audit_data_source (data_source_id),
    INDEX idx_audit_timestamp (timestamp)
);
```

#### 3.1.2 Schema发现结果表
```sql
-- 表Schema表
CREATE TABLE table_schemas (
    id VARCHAR(36) PRIMARY KEY,
    data_source_id VARCHAR(36) REFERENCES data_sources(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    estimated_row_count BIGINT DEFAULT 0,
    storage_size_bytes BIGINT,
    primary_key_fields JSONB,
    foreign_key_relationships JSONB,
    fields JSONB NOT NULL,  -- 字段数组JSON
    sample_data JSONB,
    quality_metrics JSONB,
    discovered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_analyzed_at TIMESTAMP,
    metadata JSONB,
    
    -- 约束：同一数据源下表名唯一
    UNIQUE (data_source_id, name),
    
    -- 索引
    INDEX idx_table_schemas_source (data_source_id),
    INDEX idx_table_schemas_name (name)
);

-- 字段详细信息表（规范化存储）
CREATE TABLE field_details (
    id VARCHAR(36) PRIMARY KEY,
    table_schema_id VARCHAR(36) REFERENCES table_schemas(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    db_type VARCHAR(100),
    inferred_type VARCHAR(50),
    is_nullable BOOLEAN DEFAULT TRUE,
    is_primary_key BOOLEAN DEFAULT FALSE,
    is_foreign_key BOOLEAN DEFAULT FALSE,
    default_value TEXT,
    max_length INTEGER,
    precision INTEGER,
    scale INTEGER,
    unique_values_count INTEGER,
    null_percentage DECIMAL(5,2),
    min_value TEXT,
    max_value TEXT,
    pattern_analysis JSONB,
    statistical_features JSONB,
    sample_values JSONB,
    business_meaning JSONB,
    standard_field_suggestions JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    INDEX idx_field_details_table (table_schema_id),
    INDEX idx_field_details_name (name),
    INDEX idx_field_details_type (inferred_type)
);
```

#### 3.1.3 数据标准定义表
```sql
-- 数据标准表
CREATE TABLE data_standards (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'review', 'approved', 'deprecated')),
    definition JSONB NOT NULL,  -- 完整标准定义JSON
    governance_rules JSONB,
    compliance_requirements JSONB,
    created_by VARCHAR(255),
    approved_by VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    effective_date DATE,
    deprecated_date DATE,
    
    -- 约束：同一域下版本唯一
    UNIQUE (domain, version),
    
    -- 索引
    INDEX idx_standards_domain (domain),
    INDEX idx_standards_status (status)
);

-- 标准字段表
CREATE TABLE standard_fields (
    id VARCHAR(36) PRIMARY KEY,
    standard_id VARCHAR(36) REFERENCES data_standards(id) ON DELETE CASCADE,
    table_name VARCHAR(255) NOT NULL,
    field_name VARCHAR(255) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    format_pattern VARCHAR(255),
    is_required BOOLEAN DEFAULT FALSE,
    is_unique BOOLEAN DEFAULT FALSE,
    default_value TEXT,
    min_length INTEGER,
    max_length INTEGER,
    min_value TEXT,
    max_value TEXT,
    validation_rules JSONB,
    description TEXT,
    business_rules JSONB,
    examples JSONB,
    
    -- 约束：同一标准下表内字段名唯一
    UNIQUE (standard_id, table_name, field_name),
    
    -- 索引
    INDEX idx_standard_fields_standard (standard_id),
    INDEX idx_standard_fields_table (table_name)
);
```

#### 3.1.4 映射规则表
```sql
-- 映射规则表
CREATE TABLE mapping_rules (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    source_schema_id VARCHAR(36) REFERENCES table_schemas(id) ON DELETE CASCADE,
    target_standard_id VARCHAR(36) REFERENCES data_standards(id) ON DELETE CASCADE,
    mapping_type VARCHAR(50) NOT NULL DEFAULT 'field_mapping'
        CHECK (mapping_type IN ('field_mapping', 'table_mapping', 'complex_transformation')),
    overall_confidence DECIMAL(3,2) CHECK (overall_confidence >= 0 AND overall_confidence <= 1),
    status VARCHAR(20) NOT NULL DEFAULT 'generated'
        CHECK (status IN ('generated', 'reviewed', 'approved', 'implemented')),
    field_mappings JSONB NOT NULL,
    transformation_code JSONB,
    validation_rules JSONB,
    performance_metrics JSONB,
    created_by VARCHAR(255),
    reviewed_by VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    INDEX idx_mapping_rules_source (source_schema_id),
    INDEX idx_mapping_rules_target (target_standard_id),
    INDEX idx_mapping_rules_status (status)
);

-- 字段映射详情表
CREATE TABLE field_mappings (
    id VARCHAR(36) PRIMARY KEY,
    mapping_rule_id VARCHAR(36) REFERENCES mapping_rules(id) ON DELETE CASCADE,
    source_field_id VARCHAR(36) REFERENCES field_details(id) ON DELETE CASCADE,
    target_field_id VARCHAR(36) REFERENCES standard_fields(id) ON DELETE CASCADE,
    mapping_confidence DECIMAL(3,2) CHECK (mapping_confidence >= 0 AND mapping_confidence <= 1),
    transformation_logic JSONB NOT NULL,
    data_quality_rules JSONB,
    error_handling JSONB,
    test_cases JSONB,
    
    -- 约束：同一映射规则下源字段唯一
    UNIQUE (mapping_rule_id, source_field_id),
    
    -- 索引
    INDEX idx_field_mappings_mapping (mapping_rule_id),
    INDEX idx_field_mappings_source (source_field_id),
    INDEX idx_field_mappings_target (target_field_id)
);
```

### 3.2 数据库性能优化

#### 3.2.1 分区策略
```sql
-- 按时间分区示例
CREATE TABLE analysis_results_partitioned (
    -- 字段定义同analysis_results
) PARTITION BY RANGE (created_at);

-- 创建月度分区
CREATE TABLE analysis_results_2024_01 PARTITION OF analysis_results_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE analysis_results_2024_02 PARTITION OF analysis_results_partitioned
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

#### 3.2.2 索引优化
```sql
-- 复合索引
CREATE INDEX idx_field_details_analysis 
ON field_details(table_schema_id, inferred_type, null_percentage);

-- 部分索引
CREATE INDEX idx_active_data_sources 
ON data_sources(id) 
WHERE status = 'connected';

-- 表达式索引
CREATE INDEX idx_lower_table_name 
ON table_schemas(LOWER(name));
```

#### 3.2.3 物化视图
```sql
-- 数据质量概览物化视图
CREATE MATERIALIZED VIEW data_quality_overview AS
SELECT 
    ds.name as data_source_name,
    COUNT(DISTINCT ts.id) as table_count,
    COUNT(DISTINCT fd.id) as field_count,
    AVG(fd.null_percentage) as avg_null_percentage,
    SUM(CASE WHEN fd.is_primary_key THEN 1 ELSE 0 END) as primary_key_count,
    SUM(CASE WHEN fd.is_foreign_key THEN 1 ELSE 0 END) as foreign_key_count
FROM data_sources ds
JOIN table_schemas ts ON ds.id = ts.data_source_id
JOIN field_details fd ON ts.id = fd.table_schema_id
WHERE ds.status = 'connected'
GROUP BY ds.id, ds.name;

-- 定期刷新
REFRESH MATERIALIZED VIEW CONCURRENTLY data_quality_overview;
```

---

## 第四章 算法与AI模型详细设计

### 4.1 智能Schema发现算法

#### 4.1.1 数据类型推断算法
```python
class DataTypeInferenceEngine:
    """数据类型智能推断引擎"""
    
    def infer_data_type(self, field_name: str, sample_values: List[Any]) -> InferredType:
        """
        推断字段数据类型
        
        算法步骤：
        1. 模式匹配（正则表达式）
        2. 统计特征分析
        3. 机器学习分类
        4. 置信度计算
        """
        features = self._extract_features(field_name, sample_values)
        
        # 1. 规则匹配
        rule_based_type = self._rule_based_inference(field_name, sample_values)
        
        # 2. 统计推断
        stats_based_type = self._statistical_inference(features)
        
        # 3. ML模型推断
        ml_based_type = self._ml_inference(features)
        
        # 4. 综合决策
        final_type = self._ensemble_decision(
            rule_based_type, stats_based_type, ml_based_type
        )
        
        return InferredType(
            type=final_type.type,
            confidence=final_type.confidence,
            features=features,
            inference_path=final_type.inference_path
        )
    
    def _extract_features(self, field_name: str, sample_values: List[Any]) -> Dict[str, Any]:
        """提取特征用于推断"""
        return {
            "field_name_pattern": self._analyze_field_name_pattern(field_name),
            "value_length_stats": self._calculate_length_statistics(sample_values),
            "numeric_features": self._extract_numeric_features(sample_values),
            "pattern_features": self._extract_pattern_features(sample_values),
            "semantic_features": self._extract_semantic_features(field_name, sample_values)
        }
    
    def _rule_based_inference(self, field_name: str, sample_values: List[Any]) -> RuleBasedType:
        """基于规则的推断"""
        rules = [
            # 身份证号
            {
                "pattern": r"^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[1-2]\d|3[0-1])\d{3}[0-9Xx]$",
                "type": "id_card",
                "confidence": 0.95
            },
            # 手机号
            {
                "pattern": r"^1[3-9]\d{9}$",
                "type": "phone_number",
                "confidence": 0.98
            },
            # 邮箱
            {
                "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                "type": "email",
                "confidence": 0.90
            },
            # 日期
            {
                "pattern": r"^\d{4}-\d{2}-\d{2}$",
                "type": "date",
                "confidence": 0.85
            }
        ]
        
        # 应用规则匹配
        for rule in rules:
            if self._matches_pattern(sample_values, rule["pattern"], threshold=0.8):
                return RuleBasedType(
                    type=rule["type"],
                    confidence=rule["confidence"],
                    matched_rule=rule
                )
        
        return RuleBasedType(type="unknown", confidence=0.0)
    
    def _statistical_inference(self, features: Dict[str, Any]) -> StatisticalType:
        """基于统计的推断"""
        # 数值特征分析
        if features.get("is_numeric", False):
            numeric_stats = features["numeric_features"]
            
            # 判断是否为整数
            if numeric_stats.get("is_integer", False):
                # 根据值范围判断类型
                min_val = numeric_stats["min"]
                max_val = numeric_stats["max"]
                
                if min_val >= 0 and max_val <= 255:
                    return StatisticalType(type="tinyint", confidence=0.8)
                elif min_val >= -32768 and max_val <= 32767:
                    return StatisticalType(type="smallint", confidence=0.85)
                elif min_val >= 0 and max_val <= 4294967295:
                    return StatisticalType(type="unsigned_int", confidence=0.8)
                else:
                    return StatisticalType(type="bigint", confidence=0.75)
            else:
                # 浮点数
                decimal_places = numeric_stats.get("decimal_places", 0)
                if decimal_places <= 2:
                    return StatisticalType(type="decimal", confidence=0.7)
                else:
                    return StatisticalType(type="float", confidence=0.7)
        
        # 字符串特征分析
        elif features.get("is_string", False):
            length_stats = features["value_length_stats"]
            avg_length = length_stats.get("avg", 0)
            
            if avg_length <= 10:
                return StatisticalType(type="varchar(10)", confidence=0.7)
            elif avg_length <= 50:
                return StatisticalType(type="varchar(50)", confidence=0.7)
            elif avg_length <= 255:
                return StatisticalType(type="varchar(255)", confidence=0.7)
            else:
                return StatisticalType(type="text", confidence=0.8)
        
        return StatisticalType(type="unknown", confidence=0.0)
```

#### 4.1.2 业务含义推断算法
```python
class BusinessMeaningInference:
    """业务含义智能推断"""
    
    def __init__(self):
        self.knowledge_graph = self._load_knowledge_graph()
        self.domain_ontology = self._load_domain_ontology()
        self.pattern_library = self._load_pattern_library()
    
    def infer_business_meaning(self, field_info: FieldInfo) -> BusinessMeaning:
        """推断字段业务含义"""
        
        strategies = [
            self._infer_by_field_name,
            self._infer_by_data_pattern,
            self._infer_by_context,
            self._infer_by_knowledge_graph
        ]
        
        results = []
        for strategy in strategies:
            result = strategy(field_info)
            if result.confidence > 0.5:
                results.append(result)
        
        # 融合多个推断结果
        if results:
            fused_result = self._fuse_results(results)
            return fused_result
        
        return BusinessMeaning(
            meaning="未知",
            confidence=0.0,
            suggestions=[]
        )
    
    def _infer_by_field_name(self, field_info: FieldInfo) -> BusinessMeaning:
        """通过字段名推断"""
        field_name = field_info.name.lower()
        
        # 字段名模式匹配词典
        patterns = {
            # 客户相关
            r"(cust|customer).*id$": {"meaning": "客户ID", "confidence": 0.95},
            r"(cust|customer).*name$": {"meaning": "客户名称", "confidence": 0.90},
            r"(cust|customer).*phone$": {"meaning": "客户电话", "confidence": 0.85},
            r"(cust|customer).*email$": {"meaning": "客户邮箱", "confidence": 0.85},
            r"(cust|customer).*address$": {"meaning": "客户地址", "confidence": 0.80},
            
            # 产品相关
            r"(prod|product).*id$": {"meaning": "产品ID", "confidence": 0.95},
            r"(prod|product).*name$": {"meaning": "产品名称", "confidence": 0.90},
            r"(prod|product).*code$": {"meaning": "产品编码", "confidence": 0.85},
            r"(prod|product).*price$": {"meaning": "产品价格", "confidence": 0.80},
            
            # 订单相关
            r"(order).*id$": {"meaning": "订单ID", "confidence": 0.95},
            r"(order).*date$": {"meaning": "订单日期", "confidence": 0.90},
            r"(order).*amount$": {"meaning": "订单金额", "confidence": 0.85},
            r"(order).*status$": {"meaning": "订单状态", "confidence": 0.80},
            
            # 时间相关
            r".*date$": {"meaning": "日期", "confidence": 0.70},
            r".*time$": {"meaning": "时间", "confidence": 0.70},
            r".*datetime$": {"meaning": "日期时间", "confidence": 0.75},
            
            # 状态相关
            r".*status$": {"meaning": "状态", "confidence": 0.75},
            r".*flag$": {"meaning": "标志", "confidence": 0.70},
            r".*type$": {"meaning": "类型", "confidence": 0.75},
        }
        
        for pattern, info in patterns.items():
            if re.match(pattern, field_name):
                return BusinessMeaning(
                    meaning=info["meaning"],
                    confidence=info["confidence"],
                    suggestions=[f"建议字段名: {self._standardize_field_name(field_name)}"]
                )
        
        return BusinessMeaning(meaning="未知", confidence=0.0)
    
    def _infer_by_data_pattern(self, field_info: FieldInfo) -> BusinessMeaning:
        """通过数据模式推断"""
        sample_values = field_info.sample_values
        
        # 分析数据模式
        patterns = self._analyze_data_patterns(sample_values)
        
        # 模式匹配
        if patterns.get("is_id_card", False):
            return BusinessMeaning(
                meaning="身份证号",
                confidence=0.95,
                suggestions=["敏感信息，需要脱敏处理"]
            )
        elif patterns.get("is_phone", False):
            return BusinessMeaning(
                meaning="手机号码",
                confidence=0.90,
                suggestions=["个人敏感信息"]
            )
        elif patterns.get("is_email", False):
            return BusinessMeaning(
                meaning="电子邮箱",
                confidence=0.85,
                suggestions=["个人联系信息"]
            )
        elif patterns.get("is_amount", False):
            return BusinessMeaning(
                meaning="金额",
                confidence=0.80,
                suggestions=["财务数据，需精确计算"]
            )
        
        return BusinessMeaning(meaning="未知", confidence=0.0)
```

### 4.2 数据标准推荐算法

#### 4.2.1 标准字段推荐算法
```python
class StandardFieldRecommender:
    """标准字段推荐算法"""
    
    def __init__(self):
        self.industry_standards = self._load_industry_standards()
        self.best_practices = self._load_best_practices()
        self.similarity_model = self._load_similarity_model()
    
    def recommend_standard_field(self, source_field: FieldInfo) -> List[StandardFieldRecommendation]:
        """推荐标准字段"""
        
        recommendations = []
        
        # 1. 基于名称相似度推荐
        name_based = self._recommend_by_name_similarity(source_field)
        recommendations.extend(name_based)
        
        # 2. 基于数据类型匹配推荐
        type_based = self._recommend_by_data_type(source_field)
        recommendations.extend(type_based)
        
        # 3. 基于业务含义匹配推荐
        meaning_based = self._recommend_by_business_meaning(source_field)
        recommendations.extend(meaning_based)
        
        # 4. 基于上下文推荐
        context_based = self._recommend_by_context(source_field)
        recommendations.extend(context_based)
        
        # 排序和去重
        sorted_recs = self._rank_and_deduplicate(recommendations)
        
        return sorted_recs[:5]  # 返回前5个推荐
    
    def _recommend_by_name_similarity(self, source_field: FieldInfo) -> List[StandardFieldRecommendation]:
        """基于名称相似度推荐"""
        source_name = source_field.name.lower()
        
        recommendations = []
        for standard_field in self.industry_standards.get_fields():
            # 计算名称相似度
            similarity = self._calculate_name_similarity(source_name, standard_field.name)
            
            if similarity > 0.6:  # 相似度阈值
                recommendations.append(
                    StandardFieldRecommendation(
                        standard_field=standard_field,
                        confidence=similarity,
                        reason=f"名称相似度: {similarity:.2f}",
                        mapping_strategy="direct_mapping"
                    )
                )
        
        return recommendations
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """计算名称相似度"""
        # 多种相似度算法组合
        strategies = [
            self._jaccard_similarity,
            self._levenshtein_similarity,
            self._cosine_similarity,
            self._semantic_similarity
        ]
        
        similarities = []
        for strategy in strategies:
            try:
