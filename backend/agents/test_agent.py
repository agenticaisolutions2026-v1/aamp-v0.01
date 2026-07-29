from backend.agents.state import AgentState
from backend.agents.supervised_agent import SupervisedAgent


def main():
    state = AgentState()
    state.user_query = "Hey I want to learn about AI agents."

    agent = SupervisedAgent()
    updated_state = agent.execute(state)

    print(updated_state.user_query)
    print(updated_state.current_agent)
    print(updated_state.status)


if __name__ == "__main__":
    main()