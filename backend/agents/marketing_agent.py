from .base_agent import BaseAgent


class MarketingAgent(BaseAgent):

    def execute(self, state):
        state.selected_agent = "MarketingAgent"
        state.result = "Here we are providing free coaching for final year students!"
        state.status = "successfully created the marketing campaign for final year students."
        state.error = None
        return state