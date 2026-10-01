import re

from backend.agents.base_agent import BaseAgent
from backend.agents.state import AgentState
from backend.services.college_discovery_service import (
    CollegeDiscoveryService,
)


class CollegeDiscoveryAgent(BaseAgent):
    """
    Agent responsible for discovering colleges
    based on the user's request.

    The agent:
        - parses the user query
        - determines the requested count
        - delegates discovery to CollegeDiscoveryService
        - returns the discovered colleges
    """

    def __init__(self):
        self.service = CollegeDiscoveryService()

    def execute(
        self,
        state: AgentState,
    ) -> AgentState:

        try:
            state.status = "running"

            category, location = self._parse_query(
                state.user_query
            )

            count = self._determine_count(
                state.user_query
            )

            state.category = category
            state.location = location

            colleges = self.service.discover_colleges(
                state=location,
                category=category,
                target_count=count,
            )

            state.result = {
                "state": location,
                "category": category,
                "count": len(colleges),
                "colleges": colleges,
            }

            state.status = "success"

            return state

        except Exception as exc:

            state.error = str(exc)
            state.status = "failed"

            return state

    def _parse_query(
        self,
        query: str,
    ):
        """
        Parse category and state from the user query.

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

        category = match.group(1).strip()
        location = match.group(2).strip()

        return category, location

    def _determine_count(
        self,
        query: str,
    ) -> int:
        """
        Extract requested college count.

        If no number is specified,
        return 10 as the default.
        """

        match = re.search(
            r"\b(\d+)\b",
            query,
        )

        if match:
            return int(match.group(1))

        return 10

