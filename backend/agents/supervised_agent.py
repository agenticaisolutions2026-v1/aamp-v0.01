from backend.agents.base_agent import BaseAgent


class SupervisedAgent(BaseAgent):

    def execute(self, state):
        print("Supervised agent started")
        state.current_agent = "SupervisedAgent"
        state.status = "Completed"
        return state