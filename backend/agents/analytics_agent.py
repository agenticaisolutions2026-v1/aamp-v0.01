from .base_agent import BaseAgent


class AnalyticsAgent(BaseAgent):

    def execute(self, state):
        state.selected_agent = "AnalyticsAgent"
        state.result = '{"clicks": 250, "conversion": "18%"}'
        return state
