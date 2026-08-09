from .base_agent import BaseAgent


class LeadAgent(BaseAgent):

    def execute(self, state):
        state.selected_agent = "LeadAgent"
        state.result = '{"lead_score": 92, "priority": "high"}'
        return state