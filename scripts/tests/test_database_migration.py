#!/usr/bin/env python3
"""
测试数据库迁移和新增列
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sqlite3
from src.services.database import DatabaseService

def test_database_columns():
    """测试数据库列是否存在"""
    print("测试数据库迁移和新增列...")
    
    # 创建数据库服务实例
    db_service = DatabaseService()
    
    # 初始化数据库（如果尚未初始化）
    db_service.initialize()
    
    # 获取连接
    conn = db_service.get_connection()
    cursor = conn.cursor()
    
    # 检查skills表列
    cursor.execute("PRAGMA table_info(skills)")
    skill_columns = [col[1] for col in cursor.fetchall()]
    
    print("Skills表列:", skill_columns)
    
    # 检查必要列是否存在
    required_skill_columns = ['source', 'priority']
    for col in required_skill_columns:
        if col in skill_columns:
            print(f"✓ Skills表包含列: {col}")
        else:
            print(f"✗ Skills表缺少列: {col}")
            return False
    
    # 检查tools表列
    cursor.execute("PRAGMA table_info(tools)")
    tool_columns = [col[1] for col in cursor.fetchall()]
    
    print("\nTools表列:", tool_columns)
    
    # 检查必要列是否存在
    required_tool_columns = ['source', 'priority']
    for col in required_tool_columns:
        if col in tool_columns:
            print(f"✓ Tools表包含列: {col}")
        else:
            print(f"✗ Tools表缺少列: {col}")
            return False
    
    # 测试插入数据
    print("\n测试插入带source和priority的数据...")
    
    # 测试插入工具
    test_tool_data = {
        'id': 'test_tool_1',
        'name': '测试工具',
        'description': '测试工具描述',
        'type': 'test',
        'source': 'local',
        'priority': 100,
        'status': 'active'
    }
    
    try:
        cursor.execute("""
            INSERT INTO tools (id, name, description, type, source, priority, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            test_tool_data['id'],
            test_tool_data['name'],
            test_tool_data['description'],
            test_tool_data['type'],
            test_tool_data['source'],
            test_tool_data['priority'],
            test_tool_data['status']
        ))
        conn.commit()
        print("✓ 成功插入工具数据")
    except Exception as e:
        print(f"✗ 插入工具数据失败: {e}")
        return False
    
    # 测试查询数据
    cursor.execute("SELECT source, priority FROM tools WHERE id = ?", ('test_tool_1',))
    result = cursor.fetchone()
    
    if result:
        source, priority = result
        print(f"✓ 查询到工具数据 - source: {source}, priority: {priority}")
        if source == 'local' and priority == 100:
            print("✓ 数据正确保存")
        else:
            print(f"✗ 数据不一致: source={source}, priority={priority}")
            return False
    else:
        print("✗ 未查询到工具数据")
        return False
    
    # 清理测试数据
    cursor.execute("DELETE FROM tools WHERE id = ?", ('test_tool_1',))
    conn.commit()
    print("✓ 清理测试数据")
    
    # 测试skills表插入（如果表中有数据）
    cursor.execute("SELECT COUNT(*) FROM skills")
    skill_count = cursor.fetchone()[0]
    print(f"\nSkills表现有记录数: {skill_count}")
    
    print("\n" + "=" * 60)
    print("数据库迁移测试通过！")
    print("=" * 60)
    
    return True

def test_api_models():
    """测试API模型"""
    print("\n测试API模型...")
    
    try:
        from src.api.tools import ToolResponse
        from src.api.models_skill import SkillResponse, SkillCreate
        
        print("✓ ToolResponse模型导入成功")
        print("✓ SkillResponse模型导入成功")
        print("✓ SkillCreate模型导入成功")
        
        # 检查模型字段
        tool_response_fields = ToolResponse.__fields__
        if 'source' in tool_response_fields and 'priority' in tool_response_fields:
            print("✓ ToolResponse模型包含source和priority字段")
        else:
            print("✗ ToolResponse模型缺少source或priority字段")
            return False
        
        skill_response_fields = SkillResponse.__fields__
        if 'source' in skill_response_fields and 'priority' in skill_response_fields:
            print("✓ SkillResponse模型包含source和priority字段")
        else:
            print("✗ SkillResponse模型缺少source或priority字段")
            return False
        
        skill_create_fields = SkillCreate.__fields__
        if 'source' in skill_create_fields and 'priority' in skill_create_fields:
            print("✓ SkillCreate模型包含source和priority字段")
        else:
            print("✗ SkillCreate模型缺少source或priority字段")
            return False
        
        print("\n" + "=" * 60)
        print("API模型测试通过！")
        print("=" * 60)
        
        return True
        
    except ImportError as e:
        print(f"✗ 导入API模型失败: {e}")
        return False
    except Exception as e:
        print(f"✗ API模型测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("开始测试数据库迁移和API模型")
    print("=" * 60)
    
    success = True
    
    try:
        if not test_database_columns():
            success = False
        
        if not test_api_models():
            success = False
        
        if success:
            print("\n" + "=" * 60)
            print("所有测试通过！系统已成功升级。")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("测试失败，请检查实现。")
            print("=" * 60)
            return 1
            
    except Exception as e:
        print(f"\n测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())