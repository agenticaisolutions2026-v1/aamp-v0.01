from backend.agents.state import AgentState
from backend.agents.supervisor_agent import SupervisorAgent


state = AgentState()

state.user_query = "What is the current updates in the CRM system for our customers?"

supervisor = SupervisorAgent()

result = supervisor.execute(state)

print("User Query:", result.user_query)
print("Selected Agent:", result.selected_agent)
print("Status:", result.status)
print("Result:", result.result)
print("Error:", result.error)