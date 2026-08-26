import logging

from backend.agents.base_agent import BaseAgent
from backend.agents.state import AgentState
from backend.services.college_enrichment_service import (
    CollegeEnrichmentService,
)


logger = logging.getLogger(__name__)


class CollegeEnrichmentAgent(BaseAgent):
    """
    Enrich a discovered college using its official website.

    The agent:
        - receives a college through AgentState.result
        - calls CollegeEnrichmentService
        - returns the structured profile in AgentState.result

    The agent does NOT:
        - create SQL
        - connect to PostgreSQL
        - save directly to the database
    """

    def __init__(
        self,
        enrichment_service=None,
    ):
        self.enrichment_service = (
            enrichment_service
            or CollegeEnrichmentService()
        )

    def execute(
        self,
        state: AgentState,
    ) -> AgentState:

        try:
            state.status = "running"

            college = state.result

            if not isinstance(
                college,
                dict,
            ):
                raise ValueError(
                    "AgentState.result must contain "
                    "a college dictionary"
                )

            logger.info(
                "Enriching college: %s",
                college.get("name"),
            )

            enriched = (
                self.enrichment_service.enrich_college(
                    college
                )
            )

            state.result = enriched

            state.status = enriched.get(
                "status",
                "partial",
            )

            return state

        except Exception as exc:

            logger.exception(
                "College enrichment failed"
            )

            state.status = "failed"
            state.error = str(exc)

            return state