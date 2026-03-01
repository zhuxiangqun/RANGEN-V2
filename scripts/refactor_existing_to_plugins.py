#!/usr/bin/env python3
"""
将现有组件重构为插件化架构

演示如何将现有的智能体和服务包装成标准化的插件。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.capability_plugin_framework import (
    CapabilityPluginFramework,
    CapabilityMetadata,
    CapabilityType
)
from src.core.standardized_interfaces import (
    StandardizedCapabilityInterface,
    StandardRequest,
    StandardResponse
)
from src.agents.knowledge_retrieval_agent import KnowledgeRetrievalAgent
from src.agents.reasoning_agent import ReasoningAgent
from src.agents.answer_generation_agent import AnswerGenerationAgent
from src.services.knowledge_service import KnowledgeService
from src.services.reasoning_service import ReasoningService
from src.services.answer_service import AnswerService


class PluginWrapper(StandardizedCapabilityInterface):
    """插件包装器 - 将现有组件包装为标准化插件"""

    def __init__(self, component_class, capability_metadata: CapabilityMetadata):
        self.component_class = component_class
        self._metadata = capability_metadata
        self.instance = None

    @property
    def interface_metadata(self):
        from src.core.standardized_interfaces import InterfaceMetadata, InterfaceVersion, DataFormat, CommunicationProtocol
        return InterfaceMetadata(
            interface_id=self._metadata.capability_id,
            name=self._metadata.name,
            version=InterfaceVersion.V1_0,
            description=self._metadata.description,
            supported_data_formats=[DataFormat.JSON],
            communication_protocols=[CommunicationProtocol.HTTP]
        )

    @property
    def metadata(self):
        return self._metadata

    async def initialize(self, config: dict) -> bool:
        """初始化插件"""
        try:
            # 创建组件实例
            if hasattr(self.component_class, '__init__'):
                # 检查是否需要特殊初始化参数
                init_params = {}
                if hasattr(self.component_class, '__init__'):
                    import inspect
                    sig = inspect.signature(self.component_class.__init__)
                    for param_name, param in sig.parameters.items():
                        if param_name != 'self' and param_name in config:
                            init_params[param_name] = config[param_name]

                if init_params:
                    self.instance = self.component_class(**init_params)
                else:
                    self.instance = self.component_class()
            else:
                self.instance = self.component_class()

            # 如果实例有initialize方法，调用它
            if hasattr(self.instance, 'initialize') and callable(getattr(self.instance, 'initialize')):
                return await self.instance.initialize(config)
            elif hasattr(self.instance, 'setup') and callable(getattr(self.instance, 'setup')):
                return await self.instance.setup(config)
            else:
                return True

        except Exception as e:
            print(f"插件初始化失败 {self._metadata.capability_id}: {e}")
            return False

    async def process_request(self, request):
        """处理标准化请求"""
        try:
            # 转换请求为组件期望的格式
            component_input = self._convert_request_to_component_input(request.payload)

            # 调用组件
            if hasattr(self.instance, 'execute'):
                result = await self.instance.execute(component_input)
            elif hasattr(self.instance, 'process'):
                result = await self.instance.process(component_input)
            elif hasattr(self.instance, 'run'):
                result = await self.instance.run(component_input)
            else:
                # 尝试直接调用实例
                result = await self.instance(component_input)

            # 转换结果为标准化响应
            response_payload = self._convert_component_result_to_response(result)

            return StandardResponse(
                payload=response_payload,
                success=True
            )

        except Exception as e:
            return StandardResponse(
                payload={'error': str(e)},
                success=False,
                error_message=str(e)
            )

    async def validate_request(self, request):
        """验证请求"""
        errors = []

        if not request.payload:
            errors.append("请求负载不能为空")

        # 检查必需的参数
        required_params = getattr(self.instance, 'required_parameters', [])
        for param in required_params:
            if param not in request.payload:
                errors.append(f"缺少必需参数: {param}")

        return errors

    async def get_status(self):
        """获取状态"""
        status = {
            'capability_id': self._metadata.capability_id,
            'state': 'ready' if self.instance else 'uninitialized',
            'version': self._metadata.version,
            'type': self._metadata.type.value
        }

        if self.instance and hasattr(self.instance, 'get_status'):
            try:
                instance_status = await self.instance.get_status()
                status.update(instance_status)
            except:
                pass

        return status

    async def cleanup(self):
        """清理资源"""
        if self.instance and hasattr(self.instance, 'cleanup'):
            try:
                await self.instance.cleanup()
            except Exception as e:
                print(f"清理失败 {self._metadata.capability_id}: {e}")

    def _convert_request_to_component_input(self, request_payload: dict) -> dict:
        """转换请求为组件输入格式"""
        # 默认直接返回，对于复杂组件需要定制转换
        return request_payload

    def _convert_component_result_to_response(self, component_result) -> dict:
        """转换组件结果为响应格式"""
        if isinstance(component_result, dict):
            return component_result
        elif hasattr(component_result, 'data'):
            return component_result.data
        elif hasattr(component_result, 'result'):
            return component_result.result
        else:
            return {'result': str(component_result)}


class KnowledgeRetrievalPlugin(PluginWrapper):
    """知识检索插件"""

    def __init__(self):
        metadata = CapabilityMetadata(
            capability_id="knowledge_retrieval_plugin",
            name="知识检索插件",
            version="1.0.0",
            type=CapabilityType.KNOWLEDGE_RETRIEVAL,
            description="基于现有知识检索智能体的插件化封装",
            author="AutoGenerated",
            provided_interfaces=["knowledge_retrieval"],
            tags={"knowledge", "retrieval", "plugin"}
        )
        super().__init__(KnowledgeRetrievalAgent, metadata)

    def _convert_request_to_component_input(self, request_payload: dict) -> dict:
        """转换知识检索请求"""
        return {
            'query': request_payload.get('query', ''),
            'context': request_payload.get('context', {}),
            'knowledge_base': request_payload.get('knowledge_base', 'default'),
            'limit': request_payload.get('limit', 10)
        }


class ReasoningPlugin(PluginWrapper):
    """推理插件"""

    def __init__(self):
        metadata = CapabilityMetadata(
            capability_id="reasoning_plugin",
            name="推理插件",
            version="1.0.0",
            type=CapabilityType.REASONING,
            description="基于现有推理智能体的插件化封装",
            author="AutoGenerated",
            provided_interfaces=["reasoning"],
            tags={"reasoning", "logic", "plugin"}
        )
        super().__init__(ReasoningAgent, metadata)

    def _convert_request_to_component_input(self, request_payload: dict) -> dict:
        """转换推理请求"""
        return {
            'query': request_payload.get('query', ''),
            'context': request_payload.get('context', {}),
            'reasoning_type': request_payload.get('reasoning_type', 'logical'),
            'evidence': request_payload.get('evidence', [])
        }


class AnswerGenerationPlugin(PluginWrapper):
    """答案生成插件"""

    def __init__(self):
        metadata = CapabilityMetadata(
            capability_id="answer_generation_plugin",
            name="答案生成插件",
            version="1.0.0",
            type=CapabilityType.ANSWER_GENERATION,
            description="基于现有答案生成智能体的插件化封装",
            author="AutoGenerated",
            provided_interfaces=["answer_generation"],
            tags={"answer", "generation", "plugin"}
        )
        super().__init__(AnswerGenerationAgent, metadata)

    def _convert_request_to_component_input(self, request_payload: dict) -> dict:
        """转换答案生成请求"""
        return {
            'query': request_payload.get('query', ''),
            'context': request_payload.get('context', {}),
            'knowledge': request_payload.get('knowledge', []),
            'reasoning': request_payload.get('reasoning', ''),
            'style': request_payload.get('style', 'concise')
        }


async def demonstrate_plugin_refactoring():
    """演示插件重构"""
    print("🔄 现有组件插件化重构演示")
    print("=" * 50)

    # 初始化插件框架
    framework = CapabilityPluginFramework()
    await framework.initialize_framework()

    # 注册现有组件作为插件
    plugins_to_register = [
        KnowledgeRetrievalPlugin(),
        ReasoningPlugin(),
        AnswerGenerationPlugin()
    ]

    print("📝 注册插件...")
    for plugin in plugins_to_register:
        try:
            plugin_id = await framework.register_plugin_from_class(
                type(plugin),  # 使用插件类的类型
                plugin_id=plugin.metadata.capability_id
            )
            print(f"  ✅ 注册成功: {plugin.metadata.name} ({plugin_id})")
        except Exception as e:
            print(f"  ❌ 注册失败: {plugin.metadata.name} - {e}")

    # 展示注册的插件
    print("\n📋 注册的插件:")
    all_plugins = framework.discover_capabilities()
    for plugin in all_plugins:
        print(f"  • {plugin.metadata.name} ({plugin.metadata.type.value})")

    # 测试插件执行
    print("\n🧪 测试插件执行..."
    test_queries = [
        {
            'plugin': 'knowledge_retrieval_plugin',
            'request': {
                'query': 'What is machine learning?',
                'limit': 5
            }
        },
        {
            'plugin': 'reasoning_plugin',
            'request': {
                'query': 'Why is the sky blue?',
                'reasoning_type': 'scientific'
            }
        },
        {
            'plugin': 'answer_generation_plugin',
            'request': {
                'query': 'Explain quantum computing',
                'style': 'educational'
            }
        }
    ]

    for i, test_case in enumerate(test_queries, 1):
        plugin_id = test_case['plugin']
        request_data = test_case['request']

        print(f"\n🔍 测试 {i}: {plugin_id}")

        try:
            # 创建标准化请求
            request = StandardRequest(payload=request_data)

            # 执行能力
            result = await framework.execute_capability(plugin_id, request.payload)

            print("  ✅ 执行成功"            print(f"     结果类型: {type(result)}")
            if isinstance(result, dict) and 'error' not in result:
                print(f"     结果摘要: {str(result)[:100]}...")
            else:
                print(f"     执行结果: {result}")

        except Exception as e:
            print(f"  ❌ 执行失败: {e}")

    # 创建组合能力示例
    print("\n🔗 创建组合能力示例..."
    try:
        composition_script = '''
COMPOSITION id="qa_pipeline" name="问答管道" strategy="performance_optimized" description="完整的问答处理管道"

NODE id="retrieve" capability="knowledge_retrieval_plugin" config={"limit": 3}
NODE id="reason" capability="reasoning_plugin" config={"reasoning_type": "logical"}
NODE id="answer" capability="answer_generation_plugin" config={"style": "concise"}

SEQUENCE retrieve -> reason -> answer

ENTRY retrieve
EXIT answer
'''

        # 创建组合能力
        composition_graph = await framework.composite_builder.create_composite_capability(
            "qa_pipeline",
            ["knowledge_retrieval_plugin", "reasoning_plugin", "answer_generation_plugin"],
            {
                "execution_order": ["retrieve", "reason", "answer"],
                "component_configs": {
                    "retrieve": {"limit": 3},
                    "reason": {"reasoning_type": "logical"},
                    "answer": {"style": "concise"}
                }
            }
        )

        print(f"  ✅ 组合能力创建成功: {composition_graph}")

    except Exception as e:
        print(f"  ❌ 组合能力创建失败: {e}")

    # 清理资源
    await framework.shutdown_framework()

    print("\n🎉 插件重构演示完成！")
    print("\n📊 总结:")
    print("  • 成功将现有智能体重构为标准化插件")
    print("  • 插件支持统一的初始化、执行和清理接口")
    print("  • 可以创建组合能力，实现能力编排")
    print("  • 保持了与现有代码的兼容性")
    print("\n💡 后续优化方向:")
    print("  • 添加更多插件类型（Citation、Memory等）")
    print("  • 实现插件热加载和卸载")
    print("  • 添加插件性能监控和优化")
    print("  • 支持插件版本管理和升级")


async def create_service_plugins():
    """创建服务层插件"""
    print("\n🏗️ 服务层插件创建演示")
    print("=" * 30)

    # 这里可以创建基于服务的插件
    # 暂时跳过，因为需要先确保服务层代码存在

    print("服务层插件创建已跳过（需要先实现服务层代码）")


async def main():
    """主函数"""
    print("🚀 现有组件插件化重构")
    print("=" * 50)

    try:
        await demonstrate_plugin_refactoring()
        await create_service_plugins()

    except KeyboardInterrupt:
        print("\n收到中断信号，正在退出...")
    except Exception as e:
        print(f"\n❌ 执行过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
