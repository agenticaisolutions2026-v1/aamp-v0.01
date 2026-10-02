import re


class Normalizer:
    """
    Converts raw Tavily search results into a consistent
    college structure.

    Responsibilities:
        - Read Tavily results
        - Remove list/ranking/blog pages
        - Remove non-college organizations
        - Keep individual college/university results
        - Extract basic location and phone information
    """

    def normalize(self, raw_results):
        colleges = []

        # Tavily returns results under "results"
        results = raw_results.get("results", [])

        for item in results:

            title = (
                item.get("title") or ""
            ).strip()

            link = (
                item.get("url") or ""
            ).strip()

            snippet = (
                item.get("content") or ""
            ).strip()

            if not title or not link:
                continue

            # Remove list/ranking/blog pages
            if self.is_list_page(
                title,
                link,
                snippet,
            ):
                continue

            # Remove known non-college organizations
            if self.is_non_college(
                title,
                snippet,
                link,
            ):
                continue

            # Make sure this looks like an institution
            if not self.looks_like_college(
                title,
                snippet,
                link,
            ):
                continue

            college = {
                "name": title,
                "website": link,
                "state": self.extract_state(item),
                "city": self.extract_city(item),
                "address": "",
                "phone": self.extract_phone(item),
                "source_url": link,
            }

            colleges.append(college)

        return colleges

    # =========================================================
    # LIST / BLOG / RANKING DETECTION
    # =========================================================

    def is_list_page(
        self,
        title,
        link,
        snippet,
    ):
        text = (
            f"{title} {link} {snippet}"
        ).lower()

        patterns = [
            "list of colleges",
            "top 10",
            "top 20",
            "top 25",
            "top 50",
            "top engineering colleges",
            "best engineering colleges",
            "best b.tech colleges",
            "best btech colleges",
            "engineering colleges in",
            "colleges in andhra pradesh",
            "ranking",
            "rankings",
            "ranked colleges",
            "/blog/",
            "/blogs/",
            "/article/",
            "/articles/",
            "/news/",
            "blog:",
            "blog -",
            "top 10 b.tech",
            "top 10 btech",
            "specializations to study",
            "how to choose",
            "category:",
            "category/",
            "colleges/",
            "/college-list",
            "college-list",
            "college directory",
            "university directory",
        ]

        return any(
            pattern in text
            for pattern in patterns
        )

    # =========================================================
    # NON-COLLEGE DETECTION
    # =========================================================

    def is_non_college(
        self,
        title,
        snippet,
        link,
    ):
        text = (
            f"{title} {snippet} {link}"
        ).lower()

        excluded_patterns = [
            "state council of higher education",
            "higher education council",
            "government department",
            "education department",
            "department of higher education",
            "university grants commission",
            "ugc",
            "aicte",
            "apsche",
            "collegedunia",
            "careers360",
            "shiksha.com",
            "getmyuni",
            "collegeseek",
        ]

        return any(
            pattern in text
            for pattern in excluded_patterns
        )

    # =========================================================
    # COLLEGE / UNIVERSITY DETECTION
    # =========================================================

    def looks_like_college(
        self,
        title,
        snippet,
        link,
    ):
        text = (
            f"{title} {snippet} {link}"
        ).lower()

        institution_patterns = [
            "college",
            "university",
            "institute",
            "school of engineering",
            "engineering institute",
            "national institute",
            "technical university",
            "institute of technology",
        ]

        return any(
            pattern in text
            for pattern in institution_patterns
        )

    # =========================================================
    # STATE EXTRACTION
    # =========================================================

    def extract_state(self, item):
        title = item.get("title", "") or ""
        content = item.get("content", "") or ""
        url = item.get("url", "") or ""

        title_lower = title.lower()
        content_lower = content.lower()
        url_lower = url.lower()

        # Strong evidence from title
        if "telangana" in title_lower:
            return "Telangana"

        if "andhra pradesh" in title_lower:
            return "Andhra Pradesh"

        # URL evidence
        if "telangana" in url_lower:
            return "Telangana"

        if "andhra" in url_lower:
            return "Andhra Pradesh"

        # Content evidence
        if "telangana" in content_lower:
            return "Telangana"

        if "andhra pradesh" in content_lower:
            return "Andhra Pradesh"

        return ""

    # =========================================================
    # CITY EXTRACTION
    # =========================================================

    def extract_city(self, item):
        text = " ".join(
            [
                item.get("title", "") or "",
                item.get("content", "") or "",
            ]
        )

        cities = [
            "Visakhapatnam",
            "Vijayawada",
            "Guntur",
            "Tirupati",
            "Nellore",
            "Kurnool",
            "Rajahmundry",
            "Kakinada",
            "Anantapur",
            "Anakapalle",
            "Kadapa",
            "Eluru",
            "Ongole",
            "Srikakulam",
            "Vizianagaram",
            "Machilipatnam",
            "Chittoor",
            "Amaravati",
            "Tenali",
            "Bhimavaram",
            "Proddatur",
            "Tadepalligudem",
            "Nandyal",
            "Markapur",
            "Gudivada",
            "Madanapalle",
            "Kadiri",
        ]

        for city in cities:
            if re.search(
                rf"\b{re.escape(city)}\b",
                text,
                re.IGNORECASE,
            ):
                return city

        match = re.search(
            r"located\s+in\s+([A-Za-z\s]+)",
            text,
            re.IGNORECASE,
        )

        if match:
            return (
                match.group(1)
                .strip()
                .split(".")[0]
            )

        return ""

    # =========================================================
    # PHONE EXTRACTION
    # =========================================================

    def extract_phone(self, item):
        text = " ".join(
            [
                item.get("title", "") or "",
                item.get("content", "") or "",
            ]
        )

        match = re.search(
            r"(?:\+91[\s-]?)?[6-9]\d{9}",
            text,
        )

        if match:
            return match.group(0)

        return None