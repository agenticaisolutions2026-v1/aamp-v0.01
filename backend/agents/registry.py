from .analytics_agent import AnalyticsAgent
from .base_agent import BaseAgent
from .campaign_strategy_agent import CampaignStrategyAgent
from .college_discovery_agent import CollegeDiscoveryAgent
from .college_scoring_agent import CollegeScoringAgent
from .crm_agent import CRMAgent
from .lead_agent import LeadAgent
from .lead_qualification_agent import LeadQualificationAgent
from .marketing_agent import MarketingAgent
from .outreach_orchestrator_agent import OutreachOrchestratorAgent


class AgentRegistry:

    def __init__(self):

        self.agents = {
            "MarketingAgent": MarketingAgent(),
            "AnalyticsAgent": AnalyticsAgent(),
            "CRMAgent": CRMAgent(),
            "LeadAgent": LeadAgent(),
            "CollegeDiscoveryAgent": CollegeDiscoveryAgent(),
            "CollegeScoringAgent": CollegeScoringAgent(),
            "LeadQualificationAgent": LeadQualificationAgent(),
            "CampaignStrategyAgent": CampaignStrategyAgent(),
            "OutreachOrchestratorAgent": OutreachOrchestratorAgent(),
        }

    def get_agent(
        self,
        agent_name: str,
    ) -> BaseAgent:

        return self.agents.get(
            agent_name
        )