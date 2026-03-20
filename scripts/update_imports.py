#!/usr/bin/env python3
"""
更新导入路径脚本
"""

import os
import re
from pathlib import Path

def update_imports_in_file(file_path):
    """更新文件中的导入路径"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 更新架构优化器导入
        content = re.sub(
            r'from src\.core\.architecture_optimizer import',
            'from src.admin.architecture_optimizer import',
            content
        )
        
        # 更新变更日志管理器导入
        content = re.sub(
            r'from src\.core\.change_log_manager import',
            'from src.tools.change_log_manager import',
            content
        )
        
        # 更新模型迁移管理器导入
        content = re.sub(
            r'from src\.ml\.model_migration_manager import',
            'from src.admin.model_migration_manager import',
            content
        )
        
        # 更新用户行为模拟器导入
        content = re.sub(
            r'from src\.testing\.user_behavior_simulator import',
            'from tests.user_behavior_simulator import',
            content
        )
        
        # 更新身份管理器导入
        content = re.sub(
            r'from src\.data\.identity_manager import',
            'from src.data.identity_manager import',
            content
        )
        
        # 更新数据仓库连接器导入
        content = re.sub(
            r'from src\.data\.warehouse_connector import',
            'from src.data.warehouse_connector import',
            content
        )
        
        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 更新导入路径: {file_path}")
            return True
        else:
            print(f"⏭️  无需更新: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ 更新失败: {file_path} - {e}")
        return False

def main():
    """主函数"""
    print("🔄 开始更新导入路径...")
    
    # 查找所有Python文件
    python_files = []
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    updated_count = 0
    for file_path in python_files:
        if update_imports_in_file(file_path):
            updated_count += 1
    
    print(f"\n🎉 导入路径更新完成！")
    print(f"📊 处理文件数: {len(python_files)}")
    print(f"✅ 更新文件数: {updated_count}")

if __name__ == "__main__":
    main()
