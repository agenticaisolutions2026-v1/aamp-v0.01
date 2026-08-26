import os
import logging
import requests
from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TavilySearchClient:
    """
    Handles API calls to Tavily.

    Responsibility:
        - Send search queries to Tavily
        - Return raw search results
        - No agent logic
        - No normalization
        - No deduplication
    """

    BASE_URL = "https://api.tavily.com/search"

    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")

        if not self.api_key:
            raise RuntimeError("TAVILY_API_KEY missing in .env")

    def search(
        self,
        query: str,
        max_results: int = 10
    ):
        try:
            logger.info(
                "Searching Tavily for query: %s",
                query
            )

            response = requests.post(
                self.BASE_URL,
                headers={
                    "Content-Type": "application/json"
                },
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": max_results
                },
                timeout=20
            )

            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(
                "Tavily request failed: %s",
                e
            )

            return {
                "error": str(e)
            }