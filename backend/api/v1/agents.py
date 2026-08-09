from fastapi import APIRouter
from pydantic import BaseModel      # Naresh - Newly added

from backend.agents.state import AgentState    # Naresh - Newly added
from backend.agents.supervisor_agent import SupervisorAgent  # Naresh - Newly added

router = APIRouter()
supervisor = SupervisorAgent()   # Naresh - Newly added

# Request model [# Naresh - Newly added- this 2 lines]
class AgentRequest(BaseModel):
    user_query: str


# Existing endpoint — keep for frontend
@router.get("/agents")
def get_agents():
    return [
        {
            "id": 1,
            "name": "Supervisor Agent",
            "status": "Running"
        },
        {
            "id": 2,
            "name": "Marketing Agent",
            "status": "Running"
        },
        {
            "id": 3,
            "name": "Analytics Agent",
            "status": "Idle"
        }
    ]

# New endpoint — execute Agent Framework [# Naresh - Newly added below all the code]
@router.post("/agents/execute")
def execute_agent(request: AgentRequest):

    state = AgentState()

    state.user_query = request.user_query

    result = supervisor.execute(state)

    return {
        "user_query": result.user_query,
        "selected_agent": result.selected_agent,
        "status": result.status,
        "result": result.result,
        "error": result.error
    }