import re
import logging

from backend.agents.base_agent import BaseAgent
from backend.agents.state import AgentState
from backend.agents.college_enrichment_agent import CollegeEnrichmentAgent
from backend.services.college_discovery_service import CollegeDiscoveryService


logger = logging.getLogger(__name__)


class CollegeDiscoveryAgent(BaseAgent):
    """
    Agent responsible for discovering colleges and then
    sending discovered colleges to the enrichment agent.

    Flow:

        User Query
            ↓
        CollegeDiscoveryService
            ↓
        Discovered Colleges
            ↓
        CollegeEnrichmentAgent
            ↓
        Enriched College Profiles

    The agent does NOT:
        - create SQL
        - connect directly to PostgreSQL
        - save directly to the database
    """

    def __init__(self):

        self.service = CollegeDiscoveryService()

        self.enrichment_agent = CollegeEnrichmentAgent()

    def execute(
        self,
        state: AgentState,
    ) -> AgentState:

        try:

            state.status = "running"

            # -------------------------------------------------
            # 1. Parse user query
            # -------------------------------------------------

            category, location = self._parse_query(
                state.user_query
            )

            state.category = category
            state.location = location

            logger.info(
                "College discovery request: %s in %s",
                category,
                location,
            )

            # -------------------------------------------------
            # 2. Determine how many colleges are required
            # -------------------------------------------------

            target_count = self._determine_count(
                state.user_query
            )

            logger.info(
                "Target college count: %s",
                target_count,
            )

            # -------------------------------------------------
            # 3. Discover colleges
            # -------------------------------------------------

            discovery_result = (
                self.service.discover_colleges(
                    state=location,
                    category=category,
                    target_count=target_count,
                )
            )

            colleges = discovery_result.get(
                "colleges",
                []
            )

            logger.info(
                "Discovered %s colleges",
                len(colleges),
            )

            # -------------------------------------------------
            # 4. Enrich each discovered college
            # -------------------------------------------------

            enriched_colleges = []

            for college in colleges:

                logger.info(
                    "Sending college for enrichment: %s",
                    college.get("name"),
                )

                enrichment_state = AgentState()

                enrichment_state.user_query = (
                    state.user_query
                )

                enrichment_state.result = college

                enrichment_result = (
                    self.enrichment_agent.execute(
                        enrichment_state
                    )
                )

                if enrichment_result.status == "failed":

                    logger.warning(
                        "Enrichment failed for %s: %s",
                        college.get("name"),
                        enrichment_result.error,
                    )

                    # Keep the original discovered college
                    # instead of losing it completely.
                    college["status"] = "partial"

                    college["error"] = (
                        enrichment_result.error
                    )

                    enriched_colleges.append(
                        college
                    )

                else:

                    enriched_colleges.append(
                        enrichment_result.result
                    )

            # -------------------------------------------------
            # 5. Return final structured result
            # -------------------------------------------------

            state.result = {
                "state": location,
                "category": category,
                "count": len(enriched_colleges),
                "colleges": enriched_colleges,
            }

            state.status = "success"

            return state

        except Exception as exc:

            logger.exception(
                "College discovery failed"
            )

            state.status = "failed"

            state.error = str(exc)

            return state

    # =========================================================
    # Query Parsing
    # =========================================================

    def _parse_query(
        self,
        query: str,
    ):
        """
        Parse category and state from a simple query.

        Example:

            engineering colleges in Andhra Pradesh

        Returns:

            category = engineering colleges
            location = Andhra Pradesh
        """

        query = query.strip()

        match = re.match(
            r"(.+?)\s+in\s+(.+)",
            query,
            re.IGNORECASE,
        )

        if not match:

            raise ValueError(
                "Query must follow the format: "
                "'<category> in <state>'"
            )

        category = (
            match.group(1)
            .strip()
        )

        location = (
            match.group(2)
            .strip()
        )

        return category, location

    # =========================================================
    # Count Extraction
    # =========================================================

    def _determine_count(
        self,
        query: str,
    ):
        """
        Extract requested college count.

        Examples:

            "find 5 engineering colleges in Andhra Pradesh"
                → 5

            "engineering colleges in Andhra Pradesh"
                → 5

        For the initial task testing, we use 5 colleges.
        """

        match = re.search(
            r"\b(\d+)\b",
            query,
        )

        if match:

            requested_count = int(
                match.group(1)
            )

            # Safety limit for initial testing.
            return min(
                requested_count,
                5,
            )

        return 5