import requests


class TavilyCollegeWebsiteReader:
    """
    Reads the official college website page.

    Returns webpage text for the enrichment extractor.
    """

    def read(self, url: str):
        if not url:
            return ""

        try:
            response = requests.get(
                url,
                timeout=20,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 "
                        "(Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 "
                        "Chrome/151.0 Safari/537.36"
                    )
                }
            )

            response.raise_for_status()

            return response.text

        except requests.RequestException as exc:
            print(
                f"Failed to read website '{url}': {exc}"
            )
            return ""