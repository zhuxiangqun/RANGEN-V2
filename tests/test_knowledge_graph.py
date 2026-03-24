"""
Knowledge Graph Service Tests
Based on actual code: src/services/knowledge_graph_service.py
"""
import pytest
from src.services.knowledge_graph_service import (
    KnowledgeGraphService, EntityType, RelationType,
    Entity, Relation, AssociationDiscoveryResult
)


class TestKnowledgeGraphService:
    @pytest.fixture
    def kg_service(self):
        return KnowledgeGraphService()
    
    def test_can_be_instantiated(self, kg_service):
        assert kg_service is not None
    
    def test_has_create_entity_method(self, kg_service):
        assert hasattr(kg_service, 'create_entity')


class TestKnowledgeGraphEnums:
    def test_entity_type_enum(self):
        assert EntityType.CONCEPT == "concept"
        assert EntityType.TOOL == "tool"
        assert EntityType.SKILL == "skill"
    
    def test_relation_type_enum(self):
        assert RelationType.USES == "uses"
        assert RelationType.DEPENDS_ON == "depends_on"


class TestEntity:
    def test_can_create_entity(self):
        entity = Entity(
            id="entity_1",
            name="Test Entity",
            entity_type=EntityType.CONCEPT,
            properties={"key": "value"}
        )
        assert entity.name == "Test Entity"
        assert entity.entity_type == EntityType.CONCEPT


class TestRelation:
    def test_can_create_relation(self):
        relation = Relation(
            id="rel_1",
            source_id="entity_1",
            target_id="entity_2",
            relation_type=RelationType.USES,
            weight=0.8
        )
        assert relation.weight == 0.8
        assert relation.relation_type == RelationType.USES
