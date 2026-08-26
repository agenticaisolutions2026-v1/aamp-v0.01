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

        elif any(keyword in query for keyword in [
            "college",
            "colleges",
            "university",
            "universities",
            "engineering"
        ]):
            agent = self.registry.get_agent("CollegeDiscoveryAgent")

        else:
            agent = self.registry.get_agent("LeadAgent")

        state.selected_agent = agent.__class__.__name__

        return agent.execute(state)