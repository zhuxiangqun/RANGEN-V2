"""
Skills Dependency Resolver
=========================
Resolves skill dependencies and loads skills dynamically.
"""

from typing import Dict, List, Set, Optional
from collections import deque

from src.agents.skills import SkillRegistry, SkillScope, get_skill_registry
from src.services.logging_service import get_logger

logger = get_logger(__name__)


class SkillsDependencyResolver:
    """
    Resolves skill dependencies and provides ordered loading.
    
    Example:
        resolver = SkillsDependencyResolver()
        skills = resolver.resolve_skills(["answer-generation"])
        # Returns: [rag-retrieval, answer-generation] in correct order
    """
    
    def __init__(self, registry: Optional[SkillRegistry] = None):
        self.registry = registry or get_skill_registry()
    
    def get_dependencies(self, skill_name: str) -> List[str]:
        """Get direct dependencies for a skill."""
        skill = self.registry.get_skill(skill_name)
        if skill:
            return skill.metadata.dependencies or []
        return []
    
    def get_all_dependencies(self, skill_name: str) -> List[str]:
        """Get all dependencies (including transitive) for a skill."""
        visited: Set[str] = set()
        dependencies: List[str] = []
        
        def _collect(name: str):
            if name in visited:
                return
            visited.add(name)
            
            deps = self.get_dependencies(name)
            for dep in deps:
                _collect(dep)
                if dep not in dependencies:
                    dependencies.append(dep)
        
        _collect(skill_name)
        return dependencies
    
    def resolve_skills(self, skill_names: List[str], include_dependencies: bool = True) -> List[str]:
        """
        Resolve skills with their dependencies in correct load order.
        
        Args:
            skill_names: List of skill names to load
            include_dependencies: Whether to include dependencies
            
        Returns:
            Ordered list of skill names (dependencies first)
        """
        # Collect all skills including dependencies
        all_skills: Set[str] = set(skill_names)
        
        if include_dependencies:
            for name in skill_names:
                all_skills.update(self.get_all_dependencies(name))
        
        # Topological sort
        sorted_skills: List[str] = []
        visited: Set[str] = set()
        
        def _visit(name: str):
            if name in visited:
                return
            visited.add(name)
            
            # Visit dependencies first
            deps = self.get_dependencies(name)
            for dep in deps:
                if dep in all_skills:
                    _visit(dep)
            
            if name not in sorted_skills:
                sorted_skills.append(name)
        
        for name in all_skills:
            _visit(name)
        
        return sorted_skills
    
    def resolve_for_agent(self, agent_name: str) -> Dict[str, List[str]]:
        """Resolve skills and dependencies for an agent."""
        from src.agents.agent_skill_mapping import get_skills_for_agent
        
        skill_names = get_skills_for_agent(agent_name)
        resolved = self.resolve_skills(skill_names)
        
        return {
            "requested": skill_names,
            "resolved": resolved,
            "dependencies": [s for s in resolved if s not in skill_names]
        }
    
    def get_load_order(self, skills: List[str]) -> List[str]:
        """
        Get topological order for loading skills.
        
        Uses Kahn's algorithm for topological sorting.
        """
        # Build dependency graph
        graph: Dict[str, Set[str]] = {s: set() for s in skills}
        in_degree: Dict[str, int] = {s: 0 for s in skills}
        
        for skill in skills:
            deps = self.get_dependencies(skill)
            for dep in deps:
                if dep in skills:
                    graph[dep].add(skill)
                    in_degree[skill] += 1
        
        # Kahn's algorithm
        queue = deque([s for s in skills if in_degree[s] == 0])
        result: List[str] = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # If there's a cycle, add remaining skills
        remaining = [s for s in skills if s not in result]
        result.extend(remaining)
        
        return result
    
    def validate_dependencies(self, skill_names: List[str]) -> Dict[str, any]:
        """
        Validate skill dependencies for issues.
        
        Returns:
            Dict with 'valid', 'missing', 'cycles' keys
        """
        all_deps = set()
        for name in skill_names:
            all_deps.update(self.get_all_dependencies(name))
        
        # Check for missing skills
        missing = []
        for dep in all_deps:
            if not self.registry.get_skill(dep):
                missing.append(dep)
        
        # Check for cycles
        cycles = self._detect_cycles(skill_names)
        
        return {
            "valid": len(missing) == 0 and len(cycles) == 0,
            "missing": missing,
            "cycles": cycles,
            "total_skills": len(skill_names),
            "total_dependencies": len(all_deps)
        }
    
    def _detect_cycles(self, skill_names: List[str]) -> List[List[str]]:
        """Detect cycles in skill dependencies."""
        graph: Dict[str, List[str]] = {s: [] for s in skill_names}
        
        for skill in skill_names:
            deps = self.get_dependencies(skill)
            for dep in deps:
                if dep in skill_names:
                    graph[dep].append(skill)
        
        cycles: List[List[str]] = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        
        def _dfs(node: str, path: List[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if _dfs(neighbor, path.copy()):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:])
                    return True
            
            rec_stack.remove(node)
            return False
        
        for skill in skill_names:
            if skill not in visited:
                _dfs(skill, [])
        
        return cycles


# Global resolver instance
_resolver: Optional[SkillsDependencyResolver] = None


def get_skills_resolver() -> SkillsDependencyResolver:
    """Get global skills dependency resolver."""
    global _resolver
    if _resolver is None:
        _resolver = SkillsDependencyResolver()
    return _resolver


def resolve_agent_skills(agent_name: str) -> Dict[str, any]:
    """Convenience function to resolve skills for an agent."""
    resolver = get_skills_resolver()
    return resolver.resolve_for_agent(agent_name)


# Example usage
if __name__ == "__main__":
    resolver = get_skills_resolver()
    
    print("=" * 70)
    print("Skills Dependency Resolution")
    print("=" * 70)
    
    # Test with answer-generation
    skills = ["answer-generation"]
    resolved = resolver.resolve_skills(skills)
    print(f"\nResolve {skills}:")
    print(f"  Result: {resolved}")
    
    # Test with agent
    for agent in ["rag_agent", "reasoning_agent", "chief_agent"]:
        result = resolver.resolve_for_agent(agent)
        print(f"\n{agent}:")
        print(f"  Requested: {result['requested']}")
        print(f"  Resolved:  {result['resolved']}")
        print(f"  Dependencies: {result['dependencies']}")
    
    print("\n" + "=" * 70)
