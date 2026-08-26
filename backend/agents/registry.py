from .base_agent import BaseAgent
from .state import AgentState
from .marketing_agent import MarketingAgent
from .analytics_agent import AnalyticsAgent
from .crm_agent import CRMAgent
from .lead_agent import LeadAgent
from .college_discovery_agent import CollegeDiscoveryAgent


class AgentRegistry:

    def __init__(self):
        self.agents = {
            "MarketingAgent": MarketingAgent(),
            "AnalyticsAgent": AnalyticsAgent(),
            "CRMAgent": CRMAgent(),
            "LeadAgent": LeadAgent(),
            "CollegeDiscoveryAgent": CollegeDiscoveryAgent()
        }

    def get_agent(self, agent_name):
        return self.agents.get(agent_name)
