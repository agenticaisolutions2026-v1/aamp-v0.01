import re

from backend.agents.base_agent import BaseAgent
from backend.agents.state import AgentState
from backend.agents.college_enrichment_agent import CollegeEnrichmentAgent
from backend.services.college_discovery_service import CollegeDiscoveryService
from backend.services.college_demo_service import CollegeDemoService


class CollegeDiscoveryAgent(BaseAgent):
    """
    Agent responsible for discovering colleges based on
    the user's request.
    """

    def __init__(self):
        self.service = CollegeDiscoveryService()
        self.enrichment_agent = CollegeEnrichmentAgent()
        self.demo_service = CollegeDemoService()

    def execute(self, state):

        try:
            category, location = self._parse_query(
                state.user_query
            )

            state.category = category
            state.location = location

            # Today's demo:
            # Use the 5 already-enriched college profiles.
            colleges = (
                self.demo_service
                .get_enriched_colleges()
            )

            state.result = {
                "state": location,
                "category": category,
                "count": len(colleges),
                "colleges": colleges,
            }

            state.status = "success"

            return state

        except Exception as e:

            state.error = str(e)
            state.status = "failed"

            return state

            # enriched_colleges = []

            #for college in colleges:

                #enrichment_state = AgentState()

                #enrichment_state.user_query = (state.user_query)
                   
                #enrichment_state.result = college

                #enrichment_result = (
                    #self.enrichment_agent.execute(
                        #enrichment_state
                   # )
                #)

                # enriched_colleges.append(
                    #enrichment_result.result
                #)



    def _parse_query(self, query):
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
            re.IGNORECASE
        )

        if not match:
            raise ValueError(
                "Query must follow the format: '<category> in <state>'"
            )

        category = match.group(1).strip()
        location = match.group(2).strip()

        return category, location

    def _determine_count(self, query):
        """
        Extract requested college count from the user query.

        If no number is specified, use 10 as the default target.
        """

        match = re.search(r"\b(\d+)\b", query)

        if match:
            return int(match.group(1))

        return 5

