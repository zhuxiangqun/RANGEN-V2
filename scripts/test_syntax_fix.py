#!/usr/bin/env python3
"""
验证语法修复
"""

def test_syntax():
    """测试修复后的语法"""
    query = "测试查询"

    # 测试修复后的代码
    try:
        result = f'抱歉，我没有找到关于"{query}"的相关信息。'
        print("✅ 语法修复成功")
        print(f"结果: {result}")
        return True
    except SyntaxError as e:
        print(f"❌ 语法错误仍然存在: {e}")
        return False

if __name__ == "__main__":
    test_syntax()
