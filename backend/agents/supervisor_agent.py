from datetime import datetime, timezone

from backend.models.agent_run import AgentRun
from backend.models.workflow_run import WorkflowRun


from .registry import AgentRegistry
from backend.agents.workflow_orchestrator import WorkflowOrchestrator
from backend.database.session import SessionLocal


class SupervisorAgent:
    def __init__(self):
        self.registry = AgentRegistry()
        self.orchestrator = WorkflowOrchestrator()

    def execute(self, state):
        print(">>> NEW SUPERVISOR EXECUTE")
        db = SessionLocal()

        workflow_run = WorkflowRun(
            user_query=state.user_query,
            status="running",
            started_at=datetime.now(timezone.utc),
        )

        db.add(workflow_run)
        db.commit()
        db.refresh(workflow_run)

        try:
            query = state.user_query.lower()

            if "marketing" in query:
                agent = self.registry.get_agent("MarketingAgent")

            elif "analytics" in query:
                agent = self.registry.get_agent("AnalyticsAgent")

            elif "crm" in query:
                agent = self.registry.get_agent("CRMAgent")

            elif any(keyword in query for keyword in [
                "find colleges",
                "find college",
                "find universities",
                "find university",
                "discover colleges",
                "discover college",
                "discover universities",
                "discover university",
                "search colleges",
                "search college",
                "search universities",
                "search university",
                "engineering colleges in",
                "colleges in",
                "universities in",
            ]):
                agent = self.registry.get_agent("CollegeDiscoveryAgent")

            elif any(keyword in query for keyword in [
                "lead score",
                "leadscore",
                "priority",
                "department",
                "cse",
                "ece",
                "ai/ml",
                "ai ml",
                "generative ai",
                "agentic ai",
                "whatsapp",
                "linkedin",
                "website",
                "contact",
                "updated",
                "information",
                "details",
            ]):
                agent = self.registry.get_agent("DatabaseQueryAgent")

            else:
                agent = self.registry.get_agent("LeadAgent")

            agent_name = agent.__class__.__name__

            agent_run = AgentRun(
                workflow_id=workflow_run.id,
                agent_name=agent_name,
                status="running",
                started_at=datetime.now(timezone.utc),
            )

            db.add(agent_run)
            db.commit()
            db.refresh(agent_run)

            state.selected_agent = agent_name

            result = agent.execute(state)
            if agent_name == "CollegeDiscoveryAgent" and result.status != "failed":
                    discovery_result = result.result or {}
                    colleges = discovery_result.get("colleges", [])

                    result = self.orchestrator.process_colleges(
                        result,
                        colleges,
                    )

            agent_run.status = "completed"
            agent_run.completed_at = datetime.now(timezone.utc)
            agent_run.result = str(state.result) if state.result else None

            workflow_run.status = "completed"
            workflow_run.completed_at = datetime.now(timezone.utc)
            workflow_run.result = str(state.result) if state.result else None

            db.commit()

            return result

        except Exception as exc:
            if "agent_run" in locals():
                agent_run.status = "failed"
                agent_run.completed_at = datetime.now(timezone.utc)
                agent_run.error = str(exc)

            workflow_run.status = "failed"
            workflow_run.completed_at = datetime.now(timezone.utc)
            workflow_run.error = str(exc)

            db.commit()

            state.status = "failed"
            state.error = str(exc)

            return state

        finally:
            db.close()