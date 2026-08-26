from backend.tools.college_discovery.search_client import SearchClient
from backend.tools.college_discovery.normalizer import Normalizer
from backend.tools.college_discovery.deduplicator import Deduplicator
from backend.tools.college_discovery.aggregator import Aggregator
import logging

logger = logging.getLogger(__name__)


class CollegeDiscoveryService:
    """
    Service responsible for orchestrating college discovery.

    Flow:
        SearchClient → Normalizer → Deduplicator → Aggregator
    """

    def __init__(self):
        self.search_client = SearchClient()
        self.normalizer = Normalizer()
        self.deduplicator = Deduplicator()
        self.aggregator = Aggregator()

        
    def discover_colleges(
        self,
        state: str,
        category: str,
        target_count: int = 10
    ):
        """
        Discover colleges using paginated SerpAPI results.

        Keeps searching additional Google result pages until:
            - target_count unique colleges are found, or
            - no more useful results are available.
        """

        query = f"{category} in {state}"

        all_colleges = []
        start = 0

        # Safety limit so discovery doesn't search forever.
        max_pages = 5

        for _ in range(max_pages):

            # Search current Google page
            raw_results = self.search_client.search(
                query,
                start=start
            )

            if raw_results.get("error"):
                break

            # Normalize current page
            normalized = self.normalizer.normalize(
                raw_results
            )

            # Add current results
            all_colleges.extend(
                normalized
            )

            # Deduplicate everything collected so far
            deduped = self.deduplicator.deduplicate(
                all_colleges
            )

            logger.info(
                "Discovery progress: %s/%s colleges",
                len(deduped),
                target_count
            )

            # Target reached
            if len(deduped) >= target_count:
                break

            # Move to next Google page
            start += 10

        # Final deduplication
        deduped = self.deduplicator.deduplicate(
            all_colleges
        )

        selected = deduped[:target_count]

        return self.aggregator.aggregate(
            selected,
            state=state,
            category=category
        )