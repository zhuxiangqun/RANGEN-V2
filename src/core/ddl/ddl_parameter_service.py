
import hashlib
from typing import Dict, Optional
from .ddl_types import DDLPhase, DDLParameters

class DDLParameterService:
    """
    DDL Parameter Service - Unified Management for Beta Parameter
    Single Source of Truth for DDL Logic.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            # Simple in-memory cache
            self._cache = {}
        
    async def get_parameters(self, query: str, phase: DDLPhase, context: Optional[Dict] = None) -> DDLParameters:
        """
        Get unified DDL parameters for a given query and phase.
        """
        beta = await self._calculate_beta(query, phase, context)
        
        # In the future, we can add confidence scores, derived parameters, etc.
        return DDLParameters(
            base_beta=beta,
            phase=phase,
            explanation=f"Calculated based on query complexity (length) and phase: {phase}"
        )

    async def _calculate_beta(self, query: str, phase: DDLPhase, context: Optional[Dict] = None) -> float:
        """
        Calculate Beta value.
        Current Implementation: Heuristic based on query length.
        Future Implementation: Model-based complexity analysis.
        """
        # Cache Check
        cache_key = f"{hashlib.md5(query.encode()).hexdigest()[:8]}_{phase}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Basic Heuristic Rule
        words = query.split()
        word_count = len(words)
        beta = 1.0  # Default center value
        
        # Adjust based on context hints if available
        context_hint = context.get('complexity', None) if context else None
        
        # 🚀 P3 优化: 使用 Phi-3 提供的 Beta 提示
        if context and 'ddl_beta_hint' in context:
            phi3_beta = context['ddl_beta_hint']
            # 将 Phi-3 的 Beta 与启发式 Beta 进行加权融合 (0.7 * Phi3 + 0.3 * Heuristic)
            # 这样既利用了 Phi-3 的智能，又保留了启发式规则作为兜底
            heuristic_beta = 1.0 # 临时占位，后续逻辑会计算
            # ... (保留后续逻辑以计算heuristic_beta) ...
            
        if phase == DDLPhase.RETRIEVAL:
            # Retrieval Phase:
            # Short/Simple -> Low Beta -> Direct Retrieval
            # Medium -> Medium Beta -> HyDE
            # Long/Complex -> High Beta -> CoT
            
            if context_hint == 'high':
                beta = 1.8
            elif context_hint == 'low':
                beta = 0.2
            else:
                # Length-based heuristic
                if word_count <= 5:
                    beta = 0.4  # Direct Retrieval (< 0.5)
                elif word_count <= 15:
                    beta = 1.0  # HyDE (0.5 - 1.4)
                else:
                    beta = 1.6  # CoT (> 1.4)
            
            # 🚀 P3: 融合 Phi-3 提示
            if context and 'ddl_beta_hint' in context:
                beta = 0.7 * context['ddl_beta_hint'] + 0.3 * beta
                
        elif phase == DDLPhase.REASONING:
            # Reasoning Phase
            if word_count <= 5:
                beta = 0.3
            elif word_count <= 15:
                beta = 0.9
            else:
                beta = 1.6
                
        else:  # MEMORY / CONTEXT
            beta = 1.0
        
        # Simple Cache
        self._cache[cache_key] = beta
        return beta

# Backward compatibility alias for P0 code
MinimalDDLService = DDLParameterService
