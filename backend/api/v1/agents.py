from fastapi import APIRouter
from pydantic import BaseModel

from backend.agents.state import AgentState
from backend.agents.supervisor_agent import SupervisorAgent
from backend.agents.registry import AgentRegistry

from sqlalchemy import select
from backend.database.session import SessionLocal
from backend.models import AgentRun


router = APIRouter()

supervisor = SupervisorAgent()
agent_registry = AgentRegistry()


# ============================================================
# Request Model
# ============================================================

class AgentRequest(BaseModel):
    user_query: str


# ============================================================
# Get Registered Agents
# ============================================================

@router.get("/agents")
def get_agents():

    db = SessionLocal()

    try:
        agents = []

        for index, agent_name in enumerate(
            agent_registry.agents.keys(),
            start=1,
        ):

            latest_run = db.scalar(
                select(AgentRun)
                .where(
                    AgentRun.agent_name == agent_name
                )
                .order_by(
                    AgentRun.created_at.desc()
                )
            )

            if latest_run:

                if latest_run.status == "running":
                    status = "Running"

                elif latest_run.status == "completed":
                    status = "Completed"

                elif latest_run.status == "waiting":
                    status = "Waiting"

                else:
                    status = "Available"

                start_time = latest_run.started_at
                end_time = latest_run.completed_at

                duration = None

                if start_time:

                    end = end_time

                    if end is None and status == "Running":
                        from datetime import datetime, timezone
                        end = datetime.now(timezone.utc)

                    if end:
                        duration = round(
                            (
                                end - start_time
                            ).total_seconds()
                        )

            else:

                status = "Available"
                start_time = None
                end_time = None
                duration = None

            agents.append({
                "id": index,
                "name": agent_name,
                "status": status,
                "start_time": start_time,
                "end_time": end_time,
                "duration": (
                    f"{duration}s"
                    if duration is not None
                    else "—"
                ),
            })

        return agents

    finally:
        db.close()


# ============================================================
# Execute Agent Framework
# ============================================================

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
        "error": result.error,
    }