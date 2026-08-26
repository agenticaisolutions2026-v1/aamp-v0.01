from urllib.parse import urlparse

from backend.tools.college_discovery.tavily_college_website_finder import (
    TavilyCollegeWebsiteFinder
)
from backend.tools.college_discovery.tavily_college_website_reader import (
    TavilyCollegeWebsiteReader
)
from backend.tools.college_discovery.tavily_college_contact_page_finder import (
    TavilyCollegeContactPageFinder
)
from backend.tools.college_discovery.tavily_contact_search import (
    TavilyContactSearch
)
from backend.tools.college_discovery.tavily_college_contact_extractor import (
    TavilyCollegeContactExtractor
)


class TavilyCollegeWebEnricher:
    """
    Enriches a college using its official website.

    Collects:
        name
        website
        state
        city
        address
        phone
        email
        source_url
    """

    def __init__(self):
        self.website_finder = TavilyCollegeWebsiteFinder()
        self.website_reader = TavilyCollegeWebsiteReader()
        self.contact_page_finder = TavilyCollegeContactPageFinder()
        self.contact_search = TavilyContactSearch()
        self.contact_extractor = TavilyCollegeContactExtractor()

    def enrich(
        self,
        college_name: str,
        state: str = "",
        city: str = "",
        source_url: str = ""
    ):

        result = {
            "name": college_name,
            "website": "",
            "state": state,
            "city": city,
            "address": "",
            "phone": None,
            "email": None,
            "source_url": source_url,
        }

        # --------------------------------------------------
        # 1. Find official website
        # --------------------------------------------------

        website = self.website_finder.find(
            college_name,
            state
        )

        if not website:
            return result

        result["website"] = website

        # --------------------------------------------------
        # 2. Extract official domain
        # --------------------------------------------------

        domain = urlparse(website).netloc

        if domain.startswith("www."):
            domain = domain[4:]

        # --------------------------------------------------
        # 3. Read homepage
        # --------------------------------------------------

        homepage_html = self.website_reader.read(
            website
        )

        if not homepage_html:
            return result

        # --------------------------------------------------
        # 3. Find contact page from homepage
        # --------------------------------------------------

        contact_pages = self.contact_page_finder.find(
            homepage_html,
            website
        )

        contact_url = ""

        if contact_pages:
            contact_url = contact_pages[0]

        # --------------------------------------------------
        # 4. Tavily fallback if no contact page found
        # --------------------------------------------------

        if not contact_url:

            domain = urlparse(
                website
            ).netloc

            if domain.startswith("www."):
                domain = domain[4:]

            contact_url = self.contact_search.find(
                college_name,
                state,
                domain
            )

        # --------------------------------------------------
        # 5. Read contact page
        # --------------------------------------------------

        contact_html = ""

        if contact_url:
            contact_html = self.website_reader.read(
                contact_url
            )

        # --------------------------------------------------
        # Extract contact details
        # --------------------------------------------------

        details = {
            "address": "",
            "phone": None,
            "email": None,
        }

        if contact_html:

            details = self.contact_extractor.extract(
                contact_html
            )

        else:

            tavily_results = self.contact_search.search_details(
                college_name,
                state,
                domain
            )

    

            for search_result in tavily_results:

                title = search_result.get(
                    "title",
                    ""
                ).lower()

                url = search_result.get(
                    "url",
                    ""
                ).lower()

                content = search_result.get(
                    "content",
                    ""
                )

                if not content:
                    continue

                # Reject specialized contact pages
                if contact_url:

                    contact_url_lower = contact_url.lower()

                    bad_contact_paths = [
                        "/physics/",
                        "/chemistry/",
                        "/mathematics/",
                        "/department/",
                        "/departments/",
                        "/faculty/",
                        "/hostel/",
                        "/profile",
                    ]

                    if any(
                        path in contact_url_lower
                        for path in bad_contact_paths
                    ):
                        contact_url = ""

                    if contact_url:
                        contact_html = self.website_reader.read(
                            contact_url
                        )
                    else:
                        contact_html = ""


                # Skip obvious department/faculty pages
                department_keywords = [
                    "department of",
                    "physics",
                    "chemistry",
                    "mathematics",
                    "faculty",
                    "professor",
                    "laboratory",
                    "lab",
                    "/department/",
                    "/departments/",
                    "/faculty/",
                ]

                if any(
                    keyword in title
                    or keyword in url
                    for keyword in department_keywords
                ):
                    continue

                department_markers = [
                    "department of physics",
                    "department of chemistry",
                    "department of mathematics",
                    "department of mechanical",
                    "department of civil",
                    "department of computer science",
                    "department of electrical",
                    "department of electronics",
                ]

                if any(
                    marker in content.lower()
                    for marker in department_markers
                ):
                    continue

                extracted = self.contact_extractor.extract(
                    content
                )

                # --------------------------------------------
                # Reject department-specific email
                # --------------------------------------------

                email = extracted.get("email")

                department_email_prefixes = [
                    "ph_office",
                    "physics",
                    "chemistry",
                    "math",
                    "mathematics",
                    "cse",
                    "ece",
                    "eee",
                    "mech",
                    "civil",
                    "faculty",
                    "prof",
                ]

                if email:

                    email_prefix = email.split("@")[0].lower()

                    if any(
                        email_prefix.startswith(prefix)
                        for prefix in department_email_prefixes
                    ):
                        extracted["email"] = None

                if (
                    not details["address"]
                    and extracted.get("address")
                ):
                    details["address"] = extracted["address"]

                if (
                    not details["phone"]
                    and extracted.get("phone")
                ):
                    details["phone"] = extracted["phone"]

                if (
                    not details["email"]
                    and extracted.get("email")
                ):
                    details["email"] = extracted["email"]

                # Only stop when we have all important fields
                if (
                    details["address"]
                    and details["phone"]
                    and details["email"]
                ):
                    break

        # --------------------------------------------------
        # Update ORIGINAL college result
        # --------------------------------------------------

        result["address"] = details.get(
            "address",
            ""
        )

        result["phone"] = details.get(
            "phone"
        )

        result["email"] = details.get(
            "email"
        )

        return result