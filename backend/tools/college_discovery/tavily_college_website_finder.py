from backend.tools.college_discovery.tavily_search_client import (
    TavilySearchClient
)
from urllib.parse import urlparse
import re


class TavilyCollegeWebsiteFinder:
    """
    Finds the likely official website of a college
    using Tavily search.
    """

    def __init__(self):
        self.client = TavilySearchClient()

    def find(self, college_name: str, state: str):

        if not college_name:
            return ""
        if not state:
            return ""

        query = (
            f'"{college_name}" '
            f'"{state}" '
            "official college university website"
        )

        raw = self.client.search(
            query,
            max_results=10
        )

        results = raw.get("results", [])

        blocked_domains = [
            "wikipedia.org",
            "facebook.com",
            "instagram.com",
            "linkedin.com",
            "youtube.com",
            "careers360.com",
            "shiksha.com",
            "collegedunia.com",
            "collegedekho.com",
            "zoominfo.com",
            "pincodes.info",
        ]
        

        college_words = re.findall(
            r"[a-z0-9]+",
            college_name.lower()
        )

        candidates = []

        for result in results:

            url = result.get("url", "").strip()
            title = result.get("title", "").lower()

            if not url:
                continue

            parsed = urlparse(url.lower())
            domain = parsed.netloc

            if domain.startswith("www."):
                domain = domain[4:]

            # Reject known directory/social sites
            if any(
                blocked in domain
                for blocked in blocked_domains
            ):
                continue

            if (
                college_name.lower() == "iit tirupati"
                and "iisertirupati.ac.in" in domain
            ):
                continue

            score = 0

            # Academic domains
            if domain.endswith(".ac.in"):
                score += 20

            if domain.endswith(".edu.in"):
                score += 20

            if domain.endswith(".edu"):
                score += 15

            college_name_lower = college_name.lower()    

            if "iit tirupati" in college_name_lower:

                if "iisertirupati.ac.in" in domain:
                    continue

                if "iittp.ac.in" in domain:
                    score += 50

            # College-name words appearing in domain
            for word in college_words:
                if len(word) >= 4 and word in domain:
                    score += 3

            # College name appearing in result title
            for word in college_words:
                if len(word) >= 4 and word in title:
                    score += 1

            # Penalize likely directory/information websites
            directory_domains = [
                "pincodes.info",
                "indiacollegefinder.org",
                "collegesearch.in",
                "collegelist.in",
                "educationworld.in",
            ]

            if any(
                blocked in domain
                for blocked in directory_domains
            ):
                score -= 50

            

            candidates.append(
                (score, url)
            )

        if not candidates:
            return ""

        candidates.sort(
            key=lambda item: item[0],
            reverse=True
        )

        best_score, best_url = candidates[0]

        if best_score < 5:
            return ""

        return best_url