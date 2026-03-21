#!/bin/bash
# Skill Factory 质量检查脚本
# 6项确定性检查，缺一不可

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查函数
check_file_exists() {
    local file_path=$1
    local file_name=$2
    
    if [ ! -f "$file_path" ]; then
        log_error "$file_name 文件不存在: $file_path"
        return 1
    else
        log_success "$file_name 文件存在"
        return 0
    fi
}

check_yaml_format() {
    local file_path=$1
    local file_name=$2
    
    if python3 -c "import yaml; yaml.safe_load(open('$file_path'))" 2>/dev/null; then
        log_success "$file_name 格式正确"
        return 0
    else
        log_error "$file_name 格式不正确或解析失败"
        return 1
    fi
}

check_required_fields() {
    local file_path=$1
    local file_name=$2
    local fields_str=$3
    
    IFS=',' read -ra fields <<< "$fields_str"
    local missing_fields=()
    
    for field in "${fields[@]}"; do
        if ! grep -q "$field" "$file_path" 2>/dev/null; then
            missing_fields+=("$field")
        fi
    done
    
    if [ ${#missing_fields[@]} -eq 0 ]; then
        log_success "$file_name 所有必填字段都存在"
        return 0
    else
        log_error "$file_name 缺少以下必填字段: ${missing_fields[*]}"
        return 1
    fi
}

check_skill_md_structure() {
    local file_path=$1
    
    # 检查是否包含必要的章节
    local required_sections=("## 技能描述" "## 触发条件" "## 使用示例" "## 工具列表")
    local missing_sections=()
    
    for section in "${required_sections[@]}"; do
        if ! grep -q "$section" "$file_path" 2>/dev/null; then
            missing_sections+=("$section")
        fi
    done
    
    if [ ${#missing_sections[@]} -eq 0 ]; then
        log_success "SKILL.md 结构完整"
        return 0
    else
        log_warning "SKILL.md 缺少以下章节: ${missing_sections[*]}"
        # 这里只是警告，不是错误
        return 0
    fi
}

check_triggers_non_empty() {
    local file_path=$1
    
    if grep -q "triggers:" "$file_path" 2>/dev/null; then
        # 提取triggers字段内容
        local triggers_content=$(grep -A5 "triggers:" "$file_path" | tail -n+2 | head -5 | grep -v "^--$" | grep -v "^\s*$")
        if [ -n "$triggers_content" ]; then
            log_success "triggers 字段非空"
            return 0
        else
            log_error "triggers 字段为空或格式不正确"
            return 1
        fi
    else
        log_error "skill.yaml 缺少 triggers 字段"
        return 1
    fi
}

check_tools_non_empty() {
    local file_path=$1
    
    if grep -q "tools:" "$file_path" 2>/dev/null; then
        # 提取tools字段内容
        local tools_content=$(grep -A10 "tools:" "$file_path" | tail -n+2 | head -10 | grep -v "^--$" | grep -v "^\s*$")
        if [ -n "$tools_content" ]; then
            log_success "tools 字段非空"
            return 0
        else
            log_warning "tools 字段为空（某些原型可能不需要工具）"
            # 这里只是警告，不是错误
            return 0
        fi
    else
        log_warning "skill.yaml 缺少 tools 字段（某些原型可能不需要工具）"
        return 0
    fi
}

check_prototype_field() {
    local file_path=$1
    
    if grep -q "prototype_type:" "$file_path" 2>/dev/null; then
        # 检查原型类型是否有效
        local prototype_value=$(grep "prototype_type:" "$file_path" | cut -d':' -f2 | tr -d ' ' | tr -d '"' | tr -d "'")
        local valid_prototypes=("workflow" "expert" "coordinator" "quality_gate" "mcp_integration")
        
        if [[ " ${valid_prototypes[@]} " =~ " ${prototype_value} " ]]; then
            log_success "prototype_type 字段有效: $prototype_value"
            return 0
        else
            log_error "无效的 prototype_type: $prototype_value，有效值: ${valid_prototypes[*]}"
            return 1
        fi
    else
        log_warning "skill.yaml 缺少 prototype_type 字段（将在分类阶段自动添加）"
        return 0
    fi
}

# 主检查函数
main_check() {
    local skill_dir=$1
    
    log_info "开始检查技能目录: $skill_dir"
    log_info "========================================"
    
    local check_passed=true
    
    # 1. 检查 SKILL.md 文件存在性
    if ! check_file_exists "$skill_dir/SKILL.md" "SKILL.md"; then
        check_passed=false
    fi
    
    # 2. 检查 skill.yaml 文件存在性
    if ! check_file_exists "$skill_dir/skill.yaml" "skill.yaml"; then
        check_passed=false
    fi
    
    # 3. 检查 skill.yaml 格式
    if [ -f "$skill_dir/skill.yaml" ]; then
        if ! check_yaml_format "$skill_dir/skill.yaml" "skill.yaml"; then
            check_passed=false
        fi
    fi
    
    # 4. 检查 skill.yaml 必填字段
    if [ -f "$skill_dir/skill.yaml" ]; then
        # 必填字段：name, description, version, triggers
        if ! check_required_fields "$skill_dir/skill.yaml" "skill.yaml" "name:,description:,version:,triggers:"; then
            check_passed=false
        fi
    fi
    
    # 5. 检查 SKILL.md 基本结构
    if [ -f "$skill_dir/SKILL.md" ]; then
        check_skill_md_structure "$skill_dir/SKILL.md"
    fi
    
    # 6. 检查 triggers 字段非空
    if [ -f "$skill_dir/skill.yaml" ]; then
        if ! check_triggers_non_empty "$skill_dir/skill.yaml"; then
            check_passed=false
        fi
    fi
    
    # 7. 检查 tools 字段（警告级别）
    if [ -f "$skill_dir/skill.yaml" ]; then
        check_tools_non_empty "$skill_dir/skill.yaml"
    fi
    
    # 8. 检查 prototype_type 字段
    if [ -f "$skill_dir/skill.yaml" ]; then
        check_prototype_field "$skill_dir/skill.yaml"
    fi
    
    log_info "========================================"
    
    if [ "$check_passed" = true ]; then
        log_success "✅ 所有关键检查通过！技能质量合格。"
        return 0
    else
        log_error "❌ 质量检查未通过，请修复上述问题。"
        return 1
    fi
}

# 脚本使用方法
print_usage() {
    echo "使用方法: $0 <技能目录路径>"
    echo ""
    echo "示例:"
    echo "  $0 src/agents/skills/bundled/answer-generation"
    echo "  $0 ./my_new_skill"
    echo ""
    echo "检查项目:"
    echo "  1. SKILL.md 文件存在性"
    echo "  2. skill.yaml 文件存在性"
    echo "  3. skill.yaml 格式正确性"
    echo "  4. skill.yaml 必填字段完整性"
    echo "  5. SKILL.md 基本结构"
    echo "  6. triggers 字段非空"
    echo "  7. tools 字段检查（警告）"
    echo "  8. prototype_type 字段检查"
}

# 主程序
if [ $# -ne 1 ]; then
    echo "错误: 需要提供技能目录路径"
    print_usage
    exit 1
fi

SKILL_DIR=$1

if [ ! -d "$SKILL_DIR" ]; then
    log_error "目录不存在: $SKILL_DIR"
    exit 1
fi

# 执行检查
main_check "$SKILL_DIR"
exit_code=$?

if [ $exit_code -eq 0 ]; then
    log_success "🎉 技能质量检查完成，可以进入下一阶段！"
else
    log_error "🔧 请修复问题后重新运行检查。"
fi

exit $exit_code