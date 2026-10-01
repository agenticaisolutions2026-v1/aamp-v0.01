from .base_agent import BaseAgent
from .state import AgentState
from .marketing_agent import MarketingAgent
from .analytics_agent import AnalyticsAgent
from .crm_agent import CRMAgent
from .lead_agent import LeadAgent
from .college_discovery_agent import CollegeDiscoveryAgent
from .college_scoring_agent import CollegeScoringAgent
from .lead_qualification_agent import LeadQualificationAgent
from .human_review_agent import HumanReviewAgent
from .campaign_strategy_agent import CampaignStrategyAgent
from .personalization_agent import PersonalizationAgent
from .database_query_agent import DatabaseQueryAgent


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
            "PersonalizationAgent": PersonalizationAgent(),
            "HumanReviewAgent": HumanReviewAgent(),
            "DatabaseQueryAgent": DatabaseQueryAgent(),
        }

    def get_agent(self, agent_name):
        return self.agents.get(agent_name)
