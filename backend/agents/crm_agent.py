from .base_agent import BaseAgent


class CRMAgent(BaseAgent):

    def execute(self, state):
        state.selected_agent = "CRMAgent"
        state.result = '{"customer": "Naresh-SSIET", "status": "Updated"}'
        state.status = "This is all are our customers updated list till now."
        state.error = None
        return state