#!/usr/bin/env python3
"""
Hands能力包系统使用示例
"""

import asyncio
import logging
from pathlib import Path
import sys
import os

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.hands.registry import HandRegistry
from src.hands.executor import HandExecutor
from src.hands.file_hand import FileReadHand, FileWriteHand, DirectoryCreateHand, FileCopyHand
from src.hands.code_hand import CodeAnalysisHand, PythonTestHand, CodeGenerationHand
from src.hands.api_hand import APIRequestHand, DataProcessingHand


async def demonstrate_hand_registry():
    """演示Hand注册表"""
    print("📋 演示Hand注册表")
    print("=" * 60)
    
    # 创建注册表
    registry = HandRegistry()
    
    # 注册Hands
    print("注册Hands...")
    registry.register(FileReadHand())
    registry.register(FileWriteHand())
    registry.register(DirectoryCreateHand())
    registry.register(CodeAnalysisHand())
    registry.register(PythonTestHand())
    registry.register(APIRequestHand())
    registry.register(DataProcessingHand())
    
    # 显示统计信息
    stats = registry.stats()
    print(f"总Hands数量: {stats['total_hands']}")
    print("\n按类别统计:")
    for category, count in stats['by_category'].items():
        print(f"  {category}: {count}")
    
    print("\n按安全级别统计:")
    for safety_level, count in stats['by_safety_level'].items():
        print(f"  {safety_level}: {count}")
    
    print(f"\n所有Hands名称: {', '.join(stats['hand_names'])}")
    
    return registry


async def demonstrate_file_operations(executor: HandExecutor):
    """演示文件操作"""
    print("\n📁 演示文件操作")
    print("=" * 60)
    
    # 创建测试目录
    test_dir = Path("test_hand_demo")
    
    # 创建目录
    print("1. 创建目录...")
    result = await executor.execute_hand(
        "directory_create",
        path=str(test_dir)
    )
    print(f"   结果: {'成功' if result.success else '失败'} - {result.error or '目录创建成功'}")
    
    # 写入文件
    print("2. 写入文件...")
    test_file = test_dir / "test.txt"
    result = await executor.execute_hand(
        "file_write",
        path=str(test_file),
        content="Hello, Hands System!\nThis is a test file."
    )
    print(f"   结果: {'成功' if result.success else '失败'} - {result.error or '文件写入成功'}")
    
    # 读取文件
    print("3. 读取文件...")
    result = await executor.execute_hand(
        "file_read",
        path=str(test_file)
    )
    print(f"   结果: {'成功' if result.success else '失败'}")
    if result.success:
        print(f"   内容: {result.output[:50]}...")
    
    return test_dir


async def demonstrate_code_analysis(executor: HandExecutor, test_dir: Path):
    """演示代码分析"""
    print("\n🔍 演示代码分析")
    print("=" * 60)
    
    # 创建Python测试文件
    python_file = test_dir / "test_code.py"
    python_content = '''#!/usr/bin/env python3
"""
测试代码文件
"""

def calculate_sum(a: int, b: int) -> int:
    """计算两个数的和"""
    return a + b


class Calculator:
    """计算器类"""
    
    def multiply(self, x: float, y: float) -> float:
        """乘法运算"""
        return x * y
    
    def divide(self, x: float, y: float) -> float:
        """除法运算"""
        if y == 0:
            raise ValueError("除数不能为零")
        return x / y


if __name__ == "__main__":
    calc = Calculator()
    print(f"3 * 4 = {calc.multiply(3, 4)}")
    print(f"10 / 2 = {calc.divide(10, 2)}")
'''
    
    # 写入Python文件
    await executor.execute_hand(
        "file_write",
        path=str(python_file),
        content=python_content,
        overwrite=True
    )
    
    # 分析代码
    print("分析Python代码...")
    result = await executor.execute_hand(
        "code_analysis",
        path=str(python_file)
    )
    
    if result.success:
        analysis = result.output
        print(f"   文件信息: {analysis['file_info']}")
        print(f"   AST分析:")
        ast_data = analysis['ast_analysis']
        print(f"     - 函数数量: {len(ast_data['functions'])}")
        print(f"     - 类数量: {len(ast_data['classes'])}")
        print(f"  代码指标:")
        metrics = analysis['code_metrics']
        print(f"     - 代码行数: {metrics['lines_of_code']}")
        print(f"     - 注释行数: {metrics['comment_lines']}")
        print(f"     - 函数复杂度: {metrics['average_complexity']:.2f}")
    else:
        print(f"   分析失败: {result.error}")


async def demonstrate_api_integration(executor: HandExecutor):
    """演示API集成"""
    print("\n🌐 演示API集成")
    print("=" * 60)
    
    print("发送API请求...")
    result = await executor.execute_hand(
        "api_request",
        url="https://httpbin.org/json",
        method="GET"
    )
    
    if result.success:
        print(f"   API请求成功")
        response = result.output.get('response', {})
        if isinstance(response, dict) and 'slideshow' in response:
            print(f"   获取到JSON数据")
            print(f"   标题: {response['slideshow'].get('title', 'N/A')}")
            print(f"   作者: {response['slideshow'].get('author', 'N/A')}")
    else:
        print(f"   API请求失败: {result.error}")


async def demonstrate_data_processing(executor: HandExecutor):
    """演示数据处理"""
    print("\n📊 演示数据处理")
    print("=" * 60)
    
    # 测试数据
    sales_data = [
        {"product": "Laptop", "category": "Electronics", "price": 999.99, "quantity": 5},
        {"product": "Mouse", "category": "Electronics", "price": 29.99, "quantity": 20},
        {"product": "Notebook", "category": "Stationery", "price": 9.99, "quantity": 50},
        {"product": "Pen", "category": "Stationery", "price": 1.99, "quantity": 100},
        {"product": "Tablet", "category": "Electronics", "price": 499.99, "quantity": 8}
    ]
    
    # 数据聚合
    print("1. 按类别聚合销售额...")
    result = await executor.execute_hand(
        "data_processing",
        operation="aggregate",
        data=sales_data,
        aggregate_by="category",
        aggregation="sum"
    )
    
    if result.success:
        print(f"   聚合结果: {result.output}")
    else:
        print(f"   聚合失败: {result.error}")
    
    # 数据过滤
    print("2. 过滤高价商品...")
    result = await executor.execute_hand(
        "data_processing",
        operation="filter",
        data=sales_data,
        filter_criteria={
            "price": {"gt": 100}
        }
    )
    
    if result.success:
        filtered = result.output
        print(f"   高价商品数量: {len(filtered)}")
        for item in filtered:
            print(f"     - {item['product']}: ${item['price']}")
    else:
        print(f"   过滤失败: {result.error}")


async def demonstrate_code_generation(executor: HandExecutor, test_dir: Path):
    """演示代码生成"""
    print("\n💻 演示代码生成")
    print("=" * 60)
    
    # 生成Python类
    generated_file = test_dir / "generated_service.py"
    
    print("生成服务类...")
    result = await executor.execute_hand(
        "code_generation",
        path=str(generated_file),
        template="python_class",
        context={
            "class_name": "UserService",
            "description": "用户服务类",
            "init_params": ", user_repository",
            "init_body": "self.user_repository = user_repository"
        },
        overwrite=True
    )
    
    if result.success:
        print(f"   代码生成成功")
        print(f"   生成文件: {generated_file}")
        
        # 读取生成的文件
        read_result = await executor.execute_hand(
            "file_read",
            path=str(generated_file)
        )
        
        if read_result.success:
            content = read_result.output
            print(f"   内容预览:")
            for line in content.splitlines()[:15]:
                print(f"     {line}")
    else:
        print(f"   代码生成失败: {result.error}")


async def demonstrate_hand_sequence(executor: HandExecutor, test_dir: Path):
    """演示Hand序列执行"""
    print("\n⚙️ 演示Hand序列执行")
    print("=" * 60)
    
    sequence = [
        {
            "hand": "directory_create",
            "parameters": {
                "path": str(test_dir / "sequence_test")
            }
        },
        {
            "hand": "file_write",
            "parameters": {
                "path": str(test_dir / "sequence_test" / "step1.txt"),
                "content": "第一步创建的文件"
            }
        },
        {
            "hand": "file_write",
            "parameters": {
                "path": str(test_dir / "sequence_test" / "step2.txt"),
                "content": "第二步创建的文件",
                "mode": "a"
            }
        },
        {
            "hand": "file_copy",
            "parameters": {
                "source": str(test_dir / "sequence_test" / "step1.txt"),
                "destination": str(test_dir / "sequence_test" / "step1_copy.txt")
            }
        }
    ]
    
    print("执行Hand序列...")
    results = await executor.execute_sequence(sequence)
    
    print(f"序列执行完成，共 {len(results)} 步")
    for i, result in enumerate(results, 1):
        status = "✅ 成功" if result.success else "❌ 失败"
        print(f"  步骤 {i}: {status} - {result.hand_name}")
        if result.error:
            print(f"       错误: {result.error}")


async def demonstrate_integration_with_evolution():
    """演示与自进化系统的集成"""
    print("\n🔄 演示与自进化系统的集成")
    print("=" * 60)
    
    try:
        # 导入进化系统组件
        from src.evolution.engine import SelfEvolutionEngine  # type: ignore[attr-defined]
        from src.evolution.constitution import ConstitutionChecker  # type: ignore[attr-defined]
        from src.hands.base import HandRegistry, HandExecutor  # type: ignore[attr-defined, misc]
        
        print("初始化自进化系统...")
        
        # 创建Hands系统
        registry = HandRegistry()
        executor = HandExecutor(registry)
        
        # 创建进化引擎
        evolution_engine = SelfEvolutionEngine(
            repo_path=Path.cwd(),
            hand_executor=executor,
            constitution_checker=ConstitutionChecker(),
            enable_background_consciousness=True
        )
        
        print("自进化系统集成成功!")
        print("系统组件:")
        print("  - Hand注册表: 已初始化")
        print("  - Hand执行器: 已初始化")
        print("  - 自进化引擎: 已初始化")
        print("  - 宪法检查器: 已集成")
        
        # 演示Hands如何被进化系统使用
        print("\nHands在自进化中的作用:")
        print("  1. 文件操作: 读取/写入配置文件、代码文件")
        print("  2. 代码修改: 自动优化、重构代码")
        print("  3. API集成: 调用外部服务、获取数据")
        print("  4. 测试执行: 运行测试验证修改")
        print("  5. 数据验证: 确保进化符合规范")
        
        return evolution_engine
        
    except ImportError as e:
        print(f"集成失败: {e}")
        print("请确保自进化系统模块已正确安装")
        return None


async def cleanup(test_dir: Path):
    """清理测试文件"""
    print("\n🧹 清理测试文件")
    print("=" * 60)
    
    if test_dir.exists():
        import shutil
        try:
            shutil.rmtree(test_dir)
            print(f"已删除测试目录: {test_dir}")
        except Exception as e:
            print(f"清理失败: {e}")
    else:
        print("测试目录不存在")


async def main():
    """主函数"""
    print("🚀 Hands能力包系统演示")
    print("=" * 60)
    
    test_dir = None
    evolution_engine = None
    
    try:
        # 演示Hand注册表
        registry = await demonstrate_hand_registry()
        
        # 创建执行器
        executor = HandExecutor(registry)
        
        # 演示文件操作
        test_dir = await demonstrate_file_operations(executor)
        
        # 演示代码分析
        await demonstrate_code_analysis(executor, test_dir)
        
        # 演示API集成
        await demonstrate_api_integration(executor)
        
        # 演示数据处理
        await demonstrate_data_processing(executor)
        
        # 演示代码生成
        await demonstrate_code_generation(executor, test_dir)
        
        # 演示Hand序列执行
        await demonstrate_hand_sequence(executor, test_dir)
        
        # 演示与自进化系统的集成
        evolution_engine = await demonstrate_integration_with_evolution()
        
        # 显示执行统计
        print("\n📈 执行统计")
        print("=" * 60)
        
        stats = executor.get_statistics()
        print(f"总执行次数: {stats['total_executions']}")
        print(f"成功次数: {stats['successful_executions']}")
        print(f"成功率: {stats['success_rate']:.1%}")
        print(f"平均执行时间: {stats['average_execution_time']:.2f}s")
        
        if stats['by_category']:
            print("\n按类别统计:")
            for category, cat_stats in stats['by_category'].items():
                success_rate = cat_stats['success'] / cat_stats['total'] if cat_stats['total'] > 0 else 0
                print(f"  {category}: {cat_stats['total']} 次 ({success_rate:.1%} 成功率)")
        
        print("\n最近执行记录:")
        for i, execution in enumerate(stats['recent_executions'][-5:], 1):
            status = "✅" if execution['success'] else "❌"
            print(f"  {i}. {status} {execution['hand']} ({execution['time']:.2f}s)")
        
        print("\n🎉 演示完成!")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理
        if test_dir:
            await cleanup(test_dir)
        
        print("\n🔚 演示结束")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.WARNING,  # 减少日志输出，专注于演示
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # 运行演示
    asyncio.run(main())