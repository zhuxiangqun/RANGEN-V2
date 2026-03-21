#!/usr/bin/env python3
"""
AIDesignGenerator - AI 辅助设计生成器

基于需求自动生成详细设计方案，集成 HARD-GATE 流程:

流程:
1. 接收 DiscoveredRequirements (from RequirementDiscovery)
2. 调用 LLM 生成详细设计
3. 人类审查并批准
4. 提交到 HARD-GATE 进入实现

Usage:
    from src.agents.ai_design_generator import AIDesignGenerator
    
    generator = AIDesignGenerator()
    
    # 接收需求发现结果
    discovery = RequirementDiscoveryAgent()
    requirements = discovery.discover_requirements("实现用户认证模块")
    
    # AI 生成设计
    design = generator.generate_design(requirements)
    
    # 人类批准
    if generator.human_review(design):
        generator.proceed_to_implementation()
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class DesignSection(Enum):
    """设计文档章节"""
    OVERVIEW = "overview"           # 概览
    ARCHITECTURE = "architecture"   # 架构设计
    API_DESIGN = "api_design"       # API 设计
    DATA_MODEL = "data_model"       # 数据模型
    FILE_STRUCTURE = "file_structure"  # 文件结构
    IMPLEMENTATION = "implementation"  # 实现方案
    RISKS = "risks"               # 风险评估


@dataclass
class DesignComponent:
    """设计组件"""
    name: str
    description: str
    files: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    priority: str = "high"
    estimated_lines: int = 0


@dataclass
class GeneratedDesign:
    """AI 生成的完整设计"""
    title: str
    overview: str = ""
    architecture: str = ""
    api_endpoints: List[Dict] = field(default_factory=list)
    data_models: List[Dict] = field(default_factory=list)
    components: List[DesignComponent] = field(default_factory=list)
    file_structure: List[str] = field(default_factory=list)
    implementation_plan: List[Dict] = field(default_factory=list)
    risks: List[Dict] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    confidence: float = 0.0
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_hard_gate_format(self) -> Dict[str, Any]:
        """转换为 HARD-GATE 格式"""
        return {
            "title": self.title,
            "overview": self.overview,
            "components": [
                {
                    "name": c.name,
                    "description": c.description,
                    "files": c.files
                }
                for c in self.components
            ],
            "file_structure": self.file_structure,
            "api_endpoints": self.api_endpoints,
            "risks": self.risks
        }


class AIDesignGenerator:
    """
    AI 辅助设计生成器
    
    基于需求自动生成详细设计方案
    """
    
    DESIGN_PROMPT_TEMPLATE = """
你是资深架构师，基于以下需求生成详细设计方案。

## 需求
{requirements}

## 输出要求

请按以下格式输出设计:

### 1. 概览 (Overview)
简要描述系统要做什么

### 2. 架构设计 (Architecture)
- 系统架构
- 模块划分
- 技术选型及理由

### 3. API 设计 (API Design)
列出所有 API 端点，格式:
```
POST /api/users - 创建用户
  Body: {{"username": str, "email": str, "password": str}}
  Response: {{"id": str, "username": str, "created_at": str}}
```

### 4. 数据模型 (Data Model)
```
User:
  - id: str (UUID)
  - username: str (unique)
  - email: str (unique)
  - password_hash: str
  - created_at: datetime
```

### 5. 文件结构 (File Structure)
```
src/
  models/
    user.py      # 用户模型
  api/
    users.py     # 用户 API
  services/
    auth.py      # 认证服务
```

### 6. 实现步骤 (Implementation Plan)
按顺序列出实现步骤，每步控制在 50 行以内:
1. 创建数据模型 (src/models/user.py)
2. 实现 API 端点 (src/api/users.py)
3. 实现认证服务 (src/services/auth.py)

### 7. 风险评估 (Risks)
- 风险1: ... | 缓解: ...
- 风险2: ... | 缓解: ...

### 8. 备选方案 (Alternatives)
考虑 2-3 个备选方案及优缺点

## 要求
- 设计要具体，包含文件名、函数签名
- 考虑安全性、性能、可维护性
- 实现步骤要原子化，便于 TDD
"""
    
    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        self.llm_config = llm_config or {}
        self._llm_client = None
        self._current_design: Optional[GeneratedDesign] = None
        logger.info("AIDesignGenerator 初始化")
    
    def _get_llm_client(self):
        """获取 LLM 客户端"""
        if self._llm_client is None:
            try:
                from src.orchestration.core_services.llm_integration import create_llm_integration
                self._llm_client = create_llm_integration(self.llm_config)
            except ImportError:
                logger.warning("LLM 集成不可用，使用模拟模式")
                return None
        return self._llm_client
    
    def generate_design(
        self,
        requirements: Any,
        context: Optional[str] = None
    ) -> GeneratedDesign:
        """
        基于需求生成设计
        
        Args:
            requirements: DiscoveredRequirements 对象或需求文本
            context: 额外上下文信息
            
        Returns:
            GeneratedDesign: 生成的完整设计
        """
        logger.info("开始生成 AI 设计...")
        
        # 提取需求文本
        requirements_text = self._extract_requirements_text(requirements)
        
        # 调用 LLM 生成设计
        design_text = self._call_llm_design(requirements_text, context)
        
        # 解析设计
        design = self._parse_design_response(design_text, requirements_text)
        
        self._current_design = design
        logger.info(f"设计生成完成: {design.title}")
        
        return design
    
    def _extract_requirements_text(self, requirements: Any) -> str:
        """从需求对象提取文本"""
        if isinstance(requirements, str):
            return requirements
        
        if hasattr(requirements, 'requirements'):
            lines = [f"- **{r.title}**: {r.description}" 
                    for r in requirements.requirements]
            return "\n".join(lines)
        
        return str(requirements)
    
    def _call_llm_design(
        self, 
        requirements: str, 
        context: Optional[str]
    ) -> str:
        """调用 LLM 生成设计"""
        client = self._get_llm_client()
        
        prompt = self.DESIGN_PROMPT_TEMPLATE.format(
            requirements=requirements
        )
        
        if context:
            prompt += f"\n\n## 额外上下文\n{context}"
        
        if client is None:
            return self._generate_mock_design(requirements)
        
        try:
            response = client.call_llm(
                prompt=prompt,
                max_tokens=4000
            )
            return response if response else self._generate_mock_design(requirements)
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            return self._generate_mock_design(requirements)
    
    def _generate_mock_design(self, requirements: str) -> str:
        """生成模拟设计 (当 LLM 不可用时)"""
        title = "Generated Design"
        
        return f"""
# {title}

## 1. 概览 (Overview)
基于需求实现完整功能模块。

## 2. 架构设计 (Architecture)
- 分层架构: API -> Service -> Model
- 单体应用，模块化设计

## 3. API 设计 (API Design)
```
POST /api/items - 创建
GET /api/items - 列表
GET /api/items/{{id}} - 详情
PUT /api/items/{{id}} - 更新
DELETE /api/items/{{id}} - 删除
```

## 4. 数据模型 (Data Model)
```
Item:
  - id: str (UUID)
  - name: str
  - created_at: datetime
  - updated_at: datetime
```

## 5. 文件结构 (File Structure)
```
src/
  models/
    item.py
  api/
    items.py
  services/
    item_service.py
```

## 6. 实现步骤 (Implementation Plan)
1. 创建模型 (src/models/item.py)
2. 创建 API (src/api/items.py)
3. 创建服务 (src/services/item_service.py)
4. 添加测试

## 7. 风险评估 (Risks)
- 风险: 缺少验证 | 缓解: 添加输入验证

## 8. 备选方案 (Alternatives)
- 方案2: 使用现成框架 | 缺点: 灵活性降低
"""
    
    def _parse_design_response(
        self, 
        design_text: str,
        requirements: str
    ) -> GeneratedDesign:
        """解析 LLM 返回的设计"""
        design = GeneratedDesign(
            title="AI Generated Design"
        )
        
        lines = design_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # 检测章节
            if line.startswith('# ') or line.startswith('## ') or line.startswith('### '):
                section_name = line.lstrip('# ').strip().lower()
                if '概览' in section_name or 'overview' in section_name:
                    current_section = DesignSection.OVERVIEW
                elif '架构' in section_name or 'architecture' in section_name:
                    current_section = DesignSection.ARCHITECTURE
                elif 'api' in section_name:
                    current_section = DesignSection.API_DESIGN
                elif '数据' in section_name or 'model' in section_name:
                    current_section = DesignSection.DATA_MODEL
                elif '文件' in section_name or 'file' in section_name:
                    current_section = DesignSection.FILE_STRUCTURE
                elif '实现' in section_name or 'plan' in section_name:
                    current_section = DesignSection.IMPLEMENTATION
                elif '风险' in section_name or 'risk' in section_name:
                    current_section = DesignSection.RISKS
                continue
            
            if not line or line.startswith('```'):
                continue
            
            # 解析内容
            if current_section == DesignSection.OVERVIEW:
                design.overview += line + "\n"
            elif current_section == DesignSection.ARCHITECTURE:
                design.architecture += line + "\n"
            elif current_section == DesignSection.API_DESIGN:
                if '/' in line and any(m in line for m in ['POST', 'GET', 'PUT', 'DELETE']):
                    design.api_endpoints.append({"endpoint": line})
            elif current_section == DesignSection.FILE_STRUCTURE:
                if '/' in line and not line.startswith('#'):
                    design.file_structure.append(line.strip())
            elif current_section == DesignSection.RISKS:
                if '-' in line or '风险' in line:
                    design.risks.append({"description": line})
        
        # 提取文件名作为组件
        for f in design.file_structure[:5]:
            if f.endswith('.py'):
                design.components.append(DesignComponent(
                    name=f.split('/')[-1].replace('.py', ''),
                    description=f"模块: {f}",
                    files=[f]
                ))
        
        design.confidence = 0.8
        
        return design
    
    def human_review(self, design: GeneratedDesign) -> bool:
        """
        人类审查设计
        
        Args:
            design: 生成的设计
            
        Returns:
            bool: 是否批准
        """
        print("\n" + "=" * 60)
        print("🤖 AI 生成的设计方案")
        print("=" * 60)
        
        print(f"\n📋 标题: {design.title}")
        print(f"\n📝 概览:\n{design.overview[:200]}...")
        
        if design.api_endpoints:
            print(f"\n🔗 API 端点 ({len(design.api_endpoints)}):")
            for ep in design.api_endpoints[:5]:
                print(f"   {ep.get('endpoint', '')}")
        
        print(f"\n📁 文件结构 ({len(design.file_structure)}):")
        for f in design.file_structure[:10]:
            print(f"   {f}")
        
        if design.components:
            print(f"\n🧩 组件 ({len(design.components)}):")
            for c in design.components[:5]:
                print(f"   - {c.name}: {c.description[:50]}...")
        
        if design.risks:
            print(f"\n⚠️  风险 ({len(design.risks)}):")
            for r in design.risks[:3]:
                print(f"   - {r.get('description', '')[:60]}...")
        
        print("\n" + "=" * 60)
        
        response = input("✅ 批准此设计? (y/n/q=quit): ").strip().lower()
        
        if response == 'q':
            raise KeyboardInterrupt("用户取消")
        
        approved = response in ['y', 'yes', '是', '']
        
        if approved:
            logger.info("设计已批准")
        else:
            logger.info("设计被拒绝")
        
        return approved
    
    def submit_to_hard_gate(
        self, 
        design: GeneratedDesign,
        approved_by: str = "ai_review"
    ) -> bool:
        """
        提交设计到 HARD-GATE
        
        Args:
            design: 生成的设计
            approved_by: 批准人
            
        Returns:
            bool: 是否成功提交
        """
        try:
            from src.agents.hard_gate import HARD_GATE, GatePhase
            
            gate = HARD_GATE()
            
            # 检查当前阶段
            if gate._state.phase != GatePhase.IDLE:
                logger.warning(f"HARD-GATE 当前阶段: {gate._state.phase.value}")
            
            # 开始设计阶段
            gate.start_design_phase(
                title=design.title,
                description=design.overview[:200]
            )
            
            # 添加设计组件
            for component in design.components:
                gate.add_design_component(
                    component=component.name,
                    files=component.files
                )
            
            # 添加问题
            for risk in design.risks[:3]:
                gate.add_design_question(
                    question=f"风险: {risk.get('description', '')[:100]}",
                    answer="已评估，可接受"
                )
            
            # 批准设计
            gate.approve_design(approved_by)
            
            # 进入实现阶段
            gate.enter_implementation_phase()
            
            logger.info("设计已提交到 HARD-GATE 并进入实现阶段")
            return True
            
        except ImportError:
            logger.error("HARD_GATE 不可用")
            return False
        except Exception as e:
            logger.error(f"提交 HARD-GATE 失败: {e}")
            return False
    
    def auto_approve_and_proceed(self, design: GeneratedDesign) -> bool:
        """
        自动批准并进入实现 (跳过人工审查)
        
        用于自动化流程
        """
        return self.submit_to_hard_gate(design, approved_by="ai_auto_approved")
    
    def get_current_design(self) -> Optional[GeneratedDesign]:
        """获取当前设计"""
        return self._current_design
    
    def modify_requirements(
        self,
        design: GeneratedDesign,
        new_requirements: str
    ) -> GeneratedDesign:
        """
        修改需求并重新生成设计
        
        保留已批准的部分，只更新变化的需求
        
        Args:
            design: 现有设计
            new_requirements: 新需求
            
        Returns:
            GeneratedDesign: 更新后的设计
        """
        logger.info("基于现有设计修改需求...")
        
        requirements_text = f"## 新需求\n{new_requirements}\n\n## 现有设计摘要\n- 标题: {design.title}\n- 文件: {len(design.file_structure)} 个"
        
        design_text = self._call_llm_design(requirements_text, None)
        new_design = self._parse_design_response(design_text, new_requirements)
        
        # 保留原设计的标题
        new_design.title = design.title
        
        self._current_design = new_design
        
        return new_design
    
    def add_requirements(
        self,
        design: GeneratedDesign,
        additional_requirements: str
    ) -> GeneratedDesign:
        """
        添加新需求到现有设计
        
        Args:
            design: 现有设计
            additional_requirements: 额外需求
            
        Returns:
            GeneratedDesign: 更新后的设计
        """
        logger.info("添加新需求到现有设计...")
        
        existing = "\n".join(design.file_structure[:10])
        requirements_text = f"## 现有设计\n{existing}\n\n## 新增需求\n{additional_requirements}"
        
        design_text = self._call_llm_design(requirements_text, None)
        new_design = self._parse_design_response(design_text, additional_requirements)
        
        # 合并文件列表
        new_design.title = design.title
        new_design.file_structure = list(set(
            design.file_structure + new_design.file_structure
        ))
        
        self._current_design = new_design
        
        return new_design


def handle_agent_without_design(agent_name: str) -> Dict[str, Any]:
    """
    处理没有设计的 Agent
    
    Args:
        agent_name: Agent 名称
        
    Returns:
        {
            "action": "skip|create_design|analyze",
            "design": Optional[GeneratedDesign],
            "message": str
        }
    """
    try:
        from src.agents.hard_gate import HARD_GATE, GatePhase
        
        gate = HARD_GATE()
        
        # 检查 HARD-GATE 状态
        if gate._state.phase == GatePhase.IDLE:
            return {
                "action": "create_design",
                "design": None,
                "message": f"Agent '{agent_name}' 没有设计，需要先创建设计"
            }
        
        # 如果正在实现，检查设计是否包含此 Agent
        design = gate.present_design()
        if design and agent_name.lower() in design.lower():
            return {
                "action": "skip",
                "design": None,
                "message": f"Agent '{agent_name}' 已在当前设计中"
            }
        
        return {
            "action": "analyze",
            "design": None,
            "message": f"Agent '{agent_name}' 需要分析是否需要设计变更"
        }
        
    except Exception as e:
        logger.warning(f"检查 Agent 设计状态失败: {e}")
        return {
            "action": "skip",
            "design": None,
            "message": f"HARD-GATE 不可用，跳过检查: {e}"
        }


def retroactively_create_design(agent_name: str, agent_code: str) -> GeneratedDesign:
    """
    回溯创建设计
    
    分析现有 Agent 代码，反向生成设计文档
    
    Args:
        agent_name: Agent 名称
        agent_code: Agent 代码
        
    Returns:
        GeneratedDesign: 推断的设计
    """
    generator = AIDesignGenerator()
    
    prompt = f"""
分析以下 Agent 代码，推断其设计:

## Agent 名称
{agent_name}

## 代码
```
{agent_code[:3000]}
```

请推断:
1. 功能描述
2. 主要类/函数
3. 依赖关系
4. 文件结构
"""
    
    design_text = generator._call_llm_design(prompt, None)
    design = generator._parse_design_response(design_text, f"Agent: {agent_name}")
    design.title = f"[Legacy] {agent_name}"
    
    return design


# ============================================================================
# 便捷函数
# ============================================================================

def generate_design_for_requirements(
    requirements_text: str,
    auto_approve: bool = False
) -> GeneratedDesign:
    """
    一键生成设计并提交到 HARD-GATE
    
    Usage:
        design = generate_design_for_requirements("实现用户认证")
        if auto_approve:
            # 直接进入实现
            pass
        else:
            # 人工审查
            generator = AIDesignGenerator()
            if generator.human_review(design):
                generator.submit_to_hard_gate(design)
    """
    generator = AIDesignGenerator()
    design = generator.generate_design(requirements_text)
    
    if auto_approve:
        generator.auto_approve_and_proceed(design)
    else:
        if generator.human_review(design):
            generator.submit_to_hard_gate(design)
    
    return design


# ============================================================================
# Demo / Tests
# ============================================================================

if __name__ == "__main__":
    print("=== AIDesignGenerator Demo ===\n")
    
    generator = AIDesignGenerator()
    
    requirements = """
## 需求清单

1. **REQ-001: 用户注册**
   - 用户可以注册新账户
   - 需要邮箱和密码
   - 密码需要加密存储

2. **REQ-002: 用户登录**
   - 用户可以使用邮箱密码登录
   - 登录成功后返回 Token
   - Token 有效期 24 小时

3. **REQ-003: 用户信息管理**
   - 查看个人信息
   - 修改密码
   - 删除账户
"""
    
    print("1. 生成设计...")
    design = generator.generate_design(requirements)
    
    print(f"\n✅ 设计生成完成!")
    print(f"   标题: {design.title}")
    print(f"   文件数: {len(design.file_structure)}")
    print(f"   组件数: {len(design.components)}")
    print(f"   API数: {len(design.api_endpoints)}")
    
    print("\n2. 文件结构:")
    for f in design.file_structure[:8]:
        print(f"   {f}")
    
    print("\n3. 组件:")
    for c in design.components:
        print(f"   - {c.name}: {c.description}")
    
    print("\n=== Demo Complete ===")
