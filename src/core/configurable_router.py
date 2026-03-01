"""
Configurable Router Implementation with System Status Awareness
"""
from typing import Dict, Any, Optional, List
from enum import Enum
from src.interfaces.router import IRouter, RouteTarget
from src.services.logging_service import get_logger
from src.services.performance_monitor import get_performance_monitor
from src.core.neural.factory import NeuralServiceFactory

logger = get_logger(__name__)

class SystemStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"

class ConfigurableRouter(IRouter):
    """
    A router that determines execution path based on:
    1. System Health (Circuit Breaking / Fallback)
    2. Explicit configuration (highest priority)
    3. Neural Intent Classification (DL-based)
    4. Default fallback
    """
    
    def __init__(self, default_route: RouteTarget = RouteTarget.REACT):
        self.default_route = default_route
        self._strategies: List[Dict] = []
        self.monitor = get_performance_monitor()
        
        # Neural Component
        self.intent_classifier = NeuralServiceFactory.get_intent_classifier()
        
        # Thresholds for auto-degradation
        self.latency_threshold = 10.0 # seconds
        self.error_rate_threshold = 0.20 # 20%
        
        logger.info(f"ConfigurableRouter initialized with default: {default_route.value}")

    def _check_system_health(self) -> SystemStatus:
        """Check system health metrics to determine status"""
        stats = self.monitor.get_stats()
        
        # Check alerts
        active_alerts = self.monitor.active_alerts
        has_critical = any(a.level == "critical" for a in active_alerts.values())
        has_warning = any(a.level == "warning" for a in active_alerts.values())
        
        if has_critical:
            return SystemStatus.CRITICAL
        elif has_warning:
            return SystemStatus.DEGRADED
            
        return SystemStatus.HEALTHY

    def add_strategy(self, name: str, condition: callable, target: RouteTarget):
        """Register a new routing strategy"""
        self._strategies.append({
            "name": name,
            "condition": condition,
            "target": target
        })
        logger.debug(f"Added routing strategy: {name} -> {target.value}")

    async def route(self, query: str, context: Optional[Dict] = None) -> RouteTarget:
        """
        Determine route based on query, context, and system health.
        """
        context = context or {}
        
        # 0. System Health Check (Circuit Breaker)
        health = self._check_system_health()
        if health == SystemStatus.CRITICAL:
            logger.warning("System is CRITICAL. Forcing fallback to DIRECT route.")
            return RouteTarget.DIRECT
        
        # 1. Check for explicit override in context
        if "force_route" in context:
            target_str = context["force_route"]
            try:
                target = RouteTarget(target_str)
                logger.info(f"Routing override active: {target.value}")
                return target
            except ValueError:
                logger.warning(f"Invalid force_route value: {target_str}")

        # 2. Evaluate registered strategies
        for strategy in self._strategies:
            try:
                if strategy["condition"](query, context):
                    logger.info(f"Strategy matched: {strategy['name']} -> {strategy['target'].value}")
                    return strategy["target"]
            except Exception as e:
                logger.error(f"Error evaluating strategy {strategy['name']}: {e}")

        # 3. Neural Intent Classification
        try:
            # Only use neural classification if system is healthy or just degraded
            # If critical, we already fell back to DIRECT above
            
            # Predict intent
            intents = await self.intent_classifier.classify(query)
            # Example output: {'research': 0.8, 'chat': 0.2}
            
            # Logic: If 'research' or 'calculation' or 'coding' is dominant -> ReAct
            # If 'chat' or 'qa' is dominant -> Direct (or specialized Chat Agent)
            
            # Find top intent
            top_intent = max(intents, key=intents.get)
            confidence = intents[top_intent]
            
            logger.info(f"Neural Intent: {top_intent} ({confidence:.2f})")
            
            if top_intent in ["research", "calculation", "coding"] and confidence > 0.6:
                return RouteTarget.REACT
            elif top_intent in ["chat", "qa"]:
                return RouteTarget.DIRECT
                
        except Exception as e:
            logger.error(f"Neural routing failed: {e}")
            # Fall through to default heuristics

        # 4. Simple Heuristics (Fallback if Neural fails or is unsure)
        # If query is very short/simple -> Direct
        if len(query.split()) < 5 and "?" not in query:
            return RouteTarget.DIRECT
            
        # If system is degraded, prefer simpler routes if query is not explicitly complex
        if health == SystemStatus.DEGRADED and "complex" not in context.get("tags", []):
             logger.warning("System is DEGRADED. Preferring simpler route.")
             return RouteTarget.DIRECT

        # 4. Fallback
        return self.default_route
