from .registry import AgentRegistry


class SupervisorAgent:

    def __init__(self):
        self.registry = AgentRegistry()

    def execute(self, state):

        query = state.user_query.lower()

        if "marketing" in query:
            agent = self.registry.get_agent("MarketingAgent")

        elif "analytics" in query:
            agent = self.registry.get_agent("AnalyticsAgent")

        elif "crm" in query:
            agent = self.registry.get_agent("CRMAgent")

        else:
            agent = self.registry.get_agent("LeadAgent")

        return agent.execute(state)