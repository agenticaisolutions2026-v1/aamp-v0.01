import logging

from backend.tools.college_discovery.tavily_search_client import (
    TavilySearchClient,
)
from backend.tools.college_discovery.normalizer import Normalizer
from backend.tools.college_discovery.deduplicator import Deduplicator
from backend.tools.college_discovery.aggregator import Aggregator


logger = logging.getLogger(__name__)


class CollegeDiscoveryService:
    """
    Service responsible for discovering engineering colleges.

    Flow:

        Multiple Tavily Searches
                ↓
        Normalizer
                ↓
        Deduplicator
                ↓
        Select up to 5 colleges
                ↓
        Aggregator
    """

    def __init__(self):

        self.search_client = TavilySearchClient()
        self.normalizer = Normalizer()
        self.deduplicator = Deduplicator()
        self.aggregator = Aggregator()

    def discover_colleges(
        self,
        state: str,
        category: str,
        target_count: int = 5,
    ):
        """
        Discover colleges using multiple Tavily searches.

        The initial task is limited to 5 colleges.

        Multiple queries are used because a single Tavily
        search may return list pages, government websites,
        or other non-college results.
        """

        # -------------------------------------------------
        # Safety limit
        # -------------------------------------------------

        target_count = min(
            target_count,
            5,
        )

        # -------------------------------------------------
        # Build multiple search queries
        # -------------------------------------------------

        search_queries = [
            f"{category} in {state} official college website",

            f"engineering colleges {state} official websites",

            f"B.Tech colleges {state} official website",

            f"engineering institute {state} official website",

            f"engineering college Visakhapatnam {state} official",

            f"engineering college Vijayawada {state} official",

            f"engineering college Guntur {state} official",

            f"engineering college Tirupati {state} official",

            f"engineering college Kakinada {state} official",

            f"engineering college Kurnool {state} official",

            f"engineering college Nellore {state} official",
        ]

        all_colleges = []

        # -------------------------------------------------
        # Search each query
        # -------------------------------------------------

        for search_query in search_queries:

            # Stop once enough colleges are found.
            if len(all_colleges) >= target_count:
                break

            logger.info(
                "Searching Tavily: %s",
                search_query,
            )

            try:

                raw_results = (
                    self.search_client.search(
                        query=search_query,
                        max_results=10,
                    )
                )

                # -------------------------------------------------
                # Handle Tavily error
                # -------------------------------------------------

                if raw_results.get("error"):

                    logger.warning(
                        "Tavily search failed: %s",
                        raw_results.get("error"),
                    )

                    continue

                # -------------------------------------------------
                # Normalize results
                # -------------------------------------------------

                normalized = (
                    self.normalizer.normalize(
                        raw_results
                    )
                )

                logger.info(
                    "Query produced %s normalized colleges",
                    len(normalized),
                )

                # -------------------------------------------------
                # Add results
                # -------------------------------------------------

                all_colleges.extend(
                    normalized
                )

                # -------------------------------------------------
                # Deduplicate
                # -------------------------------------------------

                all_colleges = (
                    self.deduplicator.deduplicate(
                        all_colleges
                    )
                )

                logger.info(
                    "Discovery progress: %s/%s colleges",
                    len(all_colleges),
                    target_count,
                )

            except Exception as exc:

                logger.exception(
                    "College discovery query failed: %s",
                    exc,
                )

                continue

        # -------------------------------------------------
        # Final deduplication
        # -------------------------------------------------

        deduped = (
            self.deduplicator.deduplicate(
                all_colleges
            )
        )

        # -------------------------------------------------
        # Select only requested number
        # -------------------------------------------------

        selected = deduped[
            :target_count
        ]

        logger.info(
            "Final college discovery result: %s/%s",
            len(selected),
            target_count,
        )

        # -------------------------------------------------
        # Return structured result
        # -------------------------------------------------

        return self.aggregator.aggregate(
            selected,
            state=state,
            category=category,
        )