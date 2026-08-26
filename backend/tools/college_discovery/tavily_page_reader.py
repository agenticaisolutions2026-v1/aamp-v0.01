import logging

import requests
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class TavilyPageReader:
    """
    Fetches a webpage and converts its HTML into clean text.

    Responsibility:
        - Fetch webpage
        - Remove non-visible HTML content
        - Return clean page text

    Does not:
        - Search Tavily
        - Extract colleges
        - Normalize colleges
        - Deduplicate colleges
    """

    def read(self, url: str) -> str:
        try:
            logger.info("Reading source page: %s", url)

            response = requests.get(
                url,
                timeout=20
            )

            response.raise_for_status()

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            # Remove non-visible content
            for tag in soup([
                "script",
                "style",
                "noscript"
            ]):
                tag.decompose()

            text = soup.get_text(
                separator="\n",
                strip=True
            )

            return text

        except requests.exceptions.RequestException as e:
            logger.error(
                "Failed to read source page '%s': %s",
                url,
                e
            )

            return ""