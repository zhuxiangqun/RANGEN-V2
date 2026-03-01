#!/bin/bash

# PostgreSQL 多数据库初始化脚本
# 在 Docker 容器启动时自动创建多个数据库

set -e
set -u

function create_database() {
    local database="$1"
    echo "创建数据库: $database"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
        CREATE DATABASE $database;
        GRANT ALL PRIVILEGES ON DATABASE $database TO $POSTGRES_USER;
        COMMENT ON DATABASE $database IS 'RANGEN V2 - $database database';
EOSQL
}

function create_user() {
    local username="$1"
    local password="$2"
    echo "创建用户: $username"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
        CREATE USER $username WITH PASSWORD '$password';
        ALTER USER $username WITH SUPERUSER;
EOSQL
}

echo "========================"
echo "RANGEN V2 数据库初始化"
echo "========================"
echo "POSTGRES_USER: $POSTGRES_USER"
echo "POSTGRES_DB: $POSTGRES_DB"
echo "POSTGRES_MULTIPLE_DATABASES: ${POSTGRES_MULTIPLE_DATABASES:-未设置}"
echo ""

# 等待 PostgreSQL 启动
echo "等待 PostgreSQL 启动..."
while ! pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
    sleep 1
done
echo "PostgreSQL 已启动"
echo ""

# 创建默认数据库（如果不存在）
if [ -n "$POSTGRES_DB" ]; then
    echo "创建主数据库: $POSTGRES_DB"
    createdb -U "$POSTGRES_USER" "$POSTGRES_DB" || echo "数据库 $POSTGRES_DB 已存在或创建失败"
    echo ""
fi

# 创建多个数据库（如果指定）
if [ -n "${POSTGRES_MULTIPLE_DATABASES:-}" ]; then
    echo "创建多个数据库..."
    IFS=',' read -ra databases <<< "$POSTGRES_MULTIPLE_DATABASES"
    for database in "${databases[@]}"; do
        database=$(echo "$database" | xargs)  # 去除空格
        if [ -n "$database" ]; then
            create_database "$database"
        fi
    done
    echo ""
fi

# 创建额外的数据库（硬编码的默认值）
echo "创建默认数据库..."
DEFAULT_DATABASES=(
    "rangen_dev"
    "rangen_test"
    "rangen_kms"
    "rangen_rpa"
    "rangen_monitoring"
)

for database in "${DEFAULT_DATABASES[@]}"; do
    echo "检查数据库: $database"
    if psql -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw "$database"; then
        echo "数据库 $database 已存在，跳过"
    else
        create_database "$database"
    fi
done
echo ""

# 创建扩展
echo "创建数据库扩展..."
for database in "rangen_dev" "rangen_kms" "rangen_rpa"; do
    if psql -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw "$database"; then
        echo "在数据库 $database 中创建扩展..."
        psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$database" <<-EOSQL
            CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
            CREATE EXTENSION IF NOT EXISTS "pg_trgm";
            CREATE EXTENSION IF NOT EXISTS "btree_gin";
            CREATE EXTENSION IF NOT EXISTS "pgcrypto";
EOSQL
    fi
done
echo ""

# 设置数据库权限
echo "设置数据库权限..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    ALTER USER $POSTGRES_USER WITH SUPERUSER;
    GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;
    
    -- 为所有数据库设置权限
    DO \$\$
    DECLARE
        dbname text;
    BEGIN
        FOR dbname IN SELECT datname FROM pg_database 
        WHERE datistemplate = false AND datname LIKE 'rangen_%'
        LOOP
            EXECUTE 'GRANT ALL PRIVILEGES ON DATABASE ' || quote_ident(dbname) || ' TO ' || quote_ident('$POSTGRES_USER');
        END LOOP;
    END
    \$\$;
EOSQL

# 创建监控表（在监控数据库中）
if psql -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw "rangen_monitoring"; then
    echo "创建监控表..."
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "rangen_monitoring" <<-EOSQL
        CREATE TABLE IF NOT EXISTS system_metrics (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            service_name VARCHAR(100),
            metric_name VARCHAR(100),
            metric_value DOUBLE PRECISION,
            tags JSONB
        );
        
        CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp);
        CREATE INDEX IF NOT EXISTS idx_system_metrics_service ON system_metrics(service_name);
        CREATE INDEX IF NOT EXISTS idx_system_metrics_name ON system_metrics(metric_name);
        
        CREATE TABLE IF NOT EXISTS request_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            request_id VARCHAR(100),
            endpoint VARCHAR(255),
            method VARCHAR(10),
            status_code INTEGER,
            duration_ms DOUBLE PRECISION,
            user_agent TEXT,
            client_ip VARCHAR(45)
        );
        
        CREATE INDEX IF NOT EXISTS idx_request_logs_timestamp ON request_logs(timestamp);
        CREATE INDEX IF NOT EXISTS idx_request_logs_endpoint ON request_logs(endpoint);
        CREATE INDEX IF NOT EXISTS idx_request_logs_status ON request_logs(status_code);
        
        COMMENT ON TABLE system_metrics IS '系统监控指标表';
        COMMENT ON TABLE request_logs IS 'API请求日志表';
EOSQL
fi

echo "=========================="
echo "数据库初始化完成"
echo "========================