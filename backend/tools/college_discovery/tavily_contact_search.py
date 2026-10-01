import re
from backend.tools.college_discovery.tavily_search_client import (
    TavilySearchClient
)


class TavilyContactSearch:
    """
    Finds official contact pages and contact information
    from the official college domain using Tavily.
    """

    def __init__(self):
        self.client = TavilySearchClient()

    def find(
        self,
        college_name: str,
        state: str,
        official_domain: str
    ):
        """
        Find a likely official contact page.
        """

        if not college_name or not official_domain:
            return ""

        query = (
            f'"{college_name}" '
            f'"{state}" '
            f'site:{official_domain} '
            '"contact us" '
            '"main office" '
            'address phone email'
        )

        raw = self.client.search(
            query,
            max_results=10
        )

        results = raw.get("results", [])

        contact_keywords = [
            "contact",
            "contact-us",
            "contact us",
            "reach",
            "reach-us",
            "get-in-touch",
            "get in touch",
        ]

        preferred_paths = [
            "/contact",
            "/contact-us",
            "/contactus",
            "/reach-us",
        ]

        excluded_paths = [
            "/hostel/",
            "/hostels/",
            "/blog/",
            "/blogs/",
            "/news/",
            "/events/",
            "/admission/",
            "/admissions/",
            "/placement/",
            "/placements/",
            "/department/",
            "/departments/",
            "/faculty/",
            "/physics/",
            "/chemistry/",
            "/mathematics/",
            "/cse/",
            "/ece/",
            "/eee/",
        ]

        # --------------------------------------------------
        # 1. Prefer general contact pages
        # --------------------------------------------------

        for result in results:

            url = result.get("url", "").strip()

            if not url:
                continue

            url_lower = url.lower()

            # Skip specialized pages
            if any(
                path in url_lower
                for path in excluded_paths
            ):
                continue

            # Prefer standard contact URLs
            if any(
                path in url_lower
                for path in preferred_paths
            ):
                return url

        # --------------------------------------------------
        # 2. Look for contact keywords in title / URL
        # --------------------------------------------------

        for result in results:

            url = result.get("url", "").strip()
            title = result.get("title", "").lower()

            if not url:
                continue

            url_lower = url.lower()

            # Skip specialized pages
            if any(
                path in url_lower
                for path in excluded_paths
            ):
                continue

            if any(
                keyword in title
                or keyword in url_lower
                for keyword in contact_keywords
            ):
                return url

        # --------------------------------------------------
        # 3. Fallback to any result from official domain
        # --------------------------------------------------

        for result in results:

            url = result.get("url", "").strip()

            if not url:
                continue

            url_lower = url.lower()

            if any(
                path in url_lower
                for path in excluded_paths
            ):
                continue

            if official_domain.lower() in url_lower:
                return url

        return ""

    def search_details(
        self,
        college_name: str,
        state: str,
        official_domain: str
    ):
        """
        Search Tavily for contact details directly.

        Used when the official contact page cannot be
        found or cannot be read.
        """

        if not college_name or not official_domain:
            return []

        query = (
            f'"{college_name}" '
            f'"{state}" '
            f'site:{official_domain} '
            '"contact us" '
            '"main office" '
            'address phone email'
        )

        raw = self.client.search(
            query,
            max_results=10
        )

        return raw.get("results", [])

    # ====================================================
    # NEW EXTENSION METHODS (FOR ROLE & MISSING EMAIL RECOVERY)
    # ====================================================

    def search_role_contact(
        self,
        college_name: str,
        role: str,
        official_domain: str
    ):
        """
        Targeted multi-tier search to find role-specific contacts
        (e.g., Placement Officer / TPO) and extract missing emails.
        """
        if not college_name or not role:
            return []

        # Tier 1: Target specific role on domain with email indicator '@'
        query_1 = (
            f'"{college_name}" "{role}" '
            f'site:{official_domain} "@"'
        )
        raw_1 = self.client.search(query_1, max_results=5)
        results_1 = raw_1.get("results", [])

        if results_1:
            return results_1

        # Tier 2: Search for Placement / TPO page specifically
        query_2 = (
            f'"{college_name}" "placement" OR "TPO" '
            f'site:{official_domain} email contact'
        )
        raw_2 = self.client.search(query_2, max_results=5)
        return raw_2.get("results", [])

    @staticmethod
    def extract_email_from_text(text: str, target_domain: str = "") -> str:
        """
        Extracts email addresses from unstructured snippet text using regex.
        Optionally prioritizes emails ending with the college domain.
        """
        if not text:
            return ""

        # Match standard email pattern
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        matches = re.findall(email_pattern, text)

        # Filter out common false positives from images/files
        valid_emails = [
            e.strip().lower() for e in matches
            if not e.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg'))
        ]

        if not valid_emails:
            return ""

        # Prioritize college domain email if specified
        if target_domain:
            domain_clean = target_domain.lower().replace("www.", "")
            for email in valid_emails:
                if domain_clean in email:
                    return email

        return valid_emails[0]