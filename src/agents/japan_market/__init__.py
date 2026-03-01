#!/usr/bin/env python3
"""
日本市场进入Agent系统
入口模块
"""

from .base import JapanMarketAgent, JapanAgentConfig, JapanAgentFactory
from .market_researcher import JapanMarketResearcher
from .solution_planner import JapanSolutionPlanner
from .rnd_manager import JapanRNDManager
from .customer_manager import JapanCustomerManager
from .legal_advisor import JapanLegalAdvisor, create_japan_legal_advisor
from .financial_expert import JapanFinancialExpert, create_japan_financial_expert
from .hr_specialist import JapanHRSpecialist, create_japan_hr_specialist
from .project_coordinator import JapanMarketEntryProject, ProjectConfig, start_japan_market_entry

__all__ = [
    # Base
    "JapanMarketAgent",
    "JapanAgentConfig",
    "JapanAgentFactory",
    
    # Core Market Agents
    "JapanMarketResearcher",
    "JapanSolutionPlanner",
    "JapanRNDManager",
    "JapanCustomerManager",
    
    # Specialist Agents
    "JapanLegalAdvisor",
    "create_japan_legal_advisor",
    "JapanFinancialExpert",
    "create_japan_financial_expert",
    "JapanHRSpecialist",
    "create_japan_hr_specialist",
    
    # Project
    "JapanMarketEntryProject",
    "ProjectConfig",
    "start_japan_market_entry"
]
