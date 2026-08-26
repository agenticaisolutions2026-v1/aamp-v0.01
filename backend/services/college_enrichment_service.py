import logging
import re
from typing import Any

from backend.tools.college_discovery.website_enricher import (
    WebsiteEnricher,
)


logger = logging.getLogger(__name__)


class CollegeEnrichmentService:
    """
    Converts official college website research into
    a structured college enrichment profile.

    Responsibilities:
        - Call WebsiteEnricher
        - Extract institutional information
        - Extract academic information
        - Extract opportunity information
        - Extract public contact information
        - Track source URLs
        - Report missing fields

    Does NOT:
        - create SQL
        - connect to PostgreSQL
        - write to database
    """

    DEPARTMENT_PATTERNS = {
        "Computer Science and Engineering": [
            "computer science and engineering",
            "computer science & engineering",
            "computer science engineering",
            "department of computer science",
            "department of cse",
        ],
        "Artificial Intelligence and Machine Learning": [
            "artificial intelligence and machine learning",
            "artificial intelligence & machine learning",
            "artificial intelligence and ml",
            "ai and ml",
            "ai & ml",
            "ai/ml",
        ],
        "Artificial Intelligence": [
            "department of artificial intelligence",
            "artificial intelligence department",
            "department of ai",
        ],
        "Data Science": [
            "department of data science",
            "data science department",
            "data science and analytics",
        ],
        "Information Technology": [
            "department of information technology",
            "information technology department",
            "department of it",
        ],
        "Electronics and Communication Engineering": [
            "electronics and communication engineering",
            "electronics & communication engineering",
            "electronics and communications engineering",
            "department of electronics and communication",
            "department of ece",
        ],
        "Electrical and Electronics Engineering": [
            "electrical and electronics engineering",
            "electrical & electronics engineering",
            "department of electrical and electronics",
            "department of eee",
        ],
        "Mechanical Engineering": [
            "department of mechanical engineering",
            "mechanical engineering department",
        ],
        "Civil Engineering": [
            "department of civil engineering",
            "civil engineering department",
        ],
        "Chemical Engineering": [
            "department of chemical engineering",
            "chemical engineering department",
        ],
        "Biotechnology": [
            "department of biotechnology",
            "biotechnology department",
        ],
    }

    PROGRAM_PATTERNS = [
        "b.tech",
        "btech",
        "b.tech.",
        "m.tech",
        "mtech",
        "m.tech.",
        "b.e.",
        "b.e",
        "m.e.",
        "m.e",
        "b.sc",
        "b.sc.",
        "m.sc",
        "m.sc.",
        "bca",
        "mca",
        "mba",
        "ph.d",
        "phd",
    ]

    EMAIL_PATTERN = re.compile(
        r"[A-Za-z0-9._%+-]+@"
        r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    )

    PHONE_PATTERNS = [
        re.compile(
            r"\+91[\s.-]?[6-9]\d{4}[\s.-]?\d{5}"
        ),
        re.compile(
            r"\b[6-9]\d{9}\b"
        ),
        re.compile(
            r"\+91[\s.-]?\d{2,5}"
            r"[\s.-]?\d{5,8}"
        ),
    ]

    ADDRESS_KEYWORDS = [
        "address",
        "campus",
        "gandhi nagar",
        "road,",
        "road ",
        "nagar,",
        "district",
        "andhra pradesh",
        "telangana",
        "karnataka",
        "tamil nadu",
        "odisha",
    ]


    def _normalize_program(
        self,
        program: str,
    ) -> str:
        """
        Normalize common academic program abbreviations.
        """

        value = (
            str(program or "")
            .strip()
            .upper()
        )

        value = value.replace(
            " ",
            "",
        ).rstrip(".")

        normalized = {
            "B.TECH": "B.Tech",
            "BTECH": "B.Tech",

            "M.TECH": "M.Tech",
            "MTECH": "M.Tech",

            "B.E.": "B.E",
            "B.E": "B.E",
            "BE": "B.E",

            "M.E.": "M.E",
            "M.E": "M.E",
            "ME": "M.E",

            "B.SC": "B.Sc",
            "BSC": "B.Sc",

            "M.SC": "M.Sc",
            "MSC": "M.Sc",

            "BCA": "BCA",
            "MCA": "MCA",

            "MBA": "MBA",

            "PH.D": "Ph.D",
            "PHD": "Ph.D",
        }

        return normalized.get(
            value,
            program.strip(),
        )

    def __init__(
        self,
        website_enricher: WebsiteEnricher | None = None,
    ):
        self.website_enricher = (
            website_enricher
            or WebsiteEnricher()
        )

    # ---------------------------------------------------------
    # Generic helpers
    # ---------------------------------------------------------

    @staticmethod
    def _unique(
        values: list[str],
    ) -> list[str]:

        result = []
        seen = set()

        for value in values:

            value = str(
                value or ""
            ).strip()

            if not value:
                continue

            key = value.lower()

            if key not in seen:
                seen.add(key)
                result.append(value)

        return result

    @staticmethod
    def _field(
        value: Any,
        source: str | None,
    ) -> dict[str, Any]:

        return {
            "value": value,
            "source": source,
        }

    @staticmethod
    def _page_text(
        page: dict[str, Any],
    ) -> str:

        return (
            f"{page.get('title', '')} "
            f"{page.get('content', '')}"
        )

    def _all_pages(
        self,
        pages: dict[str, list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:

        result = []
        seen = set()

        for category_pages in pages.values():

            for page in category_pages:

                url = str(
                    page.get("url") or ""
                ).strip()

                if not url:
                    continue

                if url not in seen:
                    seen.add(url)
                    result.append(page)

        return result

    # ---------------------------------------------------------
    # Email
    # ---------------------------------------------------------

    def _find_email(
        self,
        pages: list[dict[str, Any]],
    ) -> dict[str, Any]:

        # Prefer contact / placement pages because
        # they are more likely to contain institutional
        # contact addresses.
        for page in pages:

            content = (
                page.get("content")
                or ""
            )

            matches = self.EMAIL_PATTERN.findall(
                content
            )

            if matches:

                return self._field(
                    matches[0],
                    page.get("url"),
                )

        return self._field(
            None,
            None,
        )

    # ---------------------------------------------------------
    # Phone
    # ---------------------------------------------------------

    def _find_phone(
        self,
        pages: list[dict[str, Any]],
    ) -> dict[str, Any]:

        for page in pages:

            content = (
                page.get("content")
                or ""
            )

            for pattern in self.PHONE_PATTERNS:

                match = pattern.search(
                    content
                )

                if match:

                    phone = (
                        match.group(0)
                        .strip()
                    )

                    return self._field(
                        phone,
                        page.get("url"),
                    )

        return self._field(
            None,
            None,
        )

    # ---------------------------------------------------------
    # Address
    # ---------------------------------------------------------

    def _find_address(
        self,
        pages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Extract an institutional address conservatively.

        An address is accepted only when:
        - it appears after an explicit address/location label
        - it contains the expected college location when available
        - it looks like a physical address
        - unrelated text such as email/social-media content
            is rejected
        """

        address_labels = [
            "address:",
            "address -",
            "address :",
            "college address:",
            "campus address:",
            "location:",
            "located at:",
        ]

        # The enrichment input gives us the expected location.
        expected_city = (
            str(
                getattr(
                    self,
                    "_current_city",
                    "",
                )
                or ""
            )
            .strip()
            .lower()
        )

        expected_state = (
            str(
                getattr(
                    self,
                    "_current_state",
                    "",
                )
                or ""
            )
            .strip()
            .lower()
        )

        for page in pages:

            content = (
                page.get("content")
                or ""
            )

            lines = [
                line.strip()
                for line in content.splitlines()
                if line.strip()
            ]

            for index, line in enumerate(lines):

                lower = line.lower()

                matched_label = next(
                    (
                        label
                        for label in address_labels
                        if label in lower
                    ),
                    None,
                )

                if not matched_label:
                    continue

                candidates = []

                # Address after label on same line
                remainder = line[
                    lower.find(matched_label)
                    + len(matched_label):
                ].strip(
                    " :-\t"
                )

                if remainder:
                    candidates.append(
                        remainder
                    )

                # Address on next line
                if index + 1 < len(lines):
                    candidates.append(
                        lines[index + 1]
                    )

                for candidate in candidates:

                    candidate_lower = (
                        candidate.lower()
                    )

                    # Reject obvious non-address content.
                    if "email" in candidate_lower:
                        continue

                    if "@" in candidate:
                        continue

                    if "social media" in candidate_lower:
                        continue

                    if "admission enquiry" in candidate_lower:
                        continue

                    if "thank you" in candidate_lower:
                        continue

                    if len(candidate) < 15:
                        continue

                    # If we know the expected city/state,
                    # require at least one to appear.
                    if expected_city or expected_state:

                        location_match = (
                            expected_city
                            and expected_city
                            in candidate_lower
                        ) or (
                            expected_state
                            and expected_state
                            in candidate_lower
                        )

                        if not location_match:
                            continue

                    # A physical address normally contains
                    # some combination of numbers, locality,
                    # road, district, PIN etc.
                    has_number = bool(
                        re.search(
                            r"\d",
                            candidate,
                        )
                    )

                    has_address_term = any(
                        term in candidate_lower
                        for term in [
                            "road",
                            "street",
                            "nagar",
                            "avenue",
                            "campus",
                            "district",
                            "village",
                            "town",
                            "city",
                            "pin",
                            "pincode",
                            "andhra pradesh",
                            "telangana",
                            "karnataka",
                            "tamil nadu",
                            "odisha",
                        ]
                    )

                    if (
                        has_number
                        and has_address_term
                    ):
                        return self._field(
                            candidate,
                            page.get("url"),
                        )

        return self._field(
            None,
            None,
        )

    # ---------------------------------------------------------
    # Departments
    # ---------------------------------------------------------

    def _extract_departments(
        self,
        pages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        departments = []

        for page in pages:

            text = self._page_text(
                page
            ).lower()

            for (
                department,
                patterns,
            ) in self.DEPARTMENT_PATTERNS.items():

                if any(
                    pattern.lower() in text
                    for pattern in patterns
                ):

                    departments.append(
                        self._field(
                            department,
                            page.get("url"),
                        )
                    )

        # Deduplicate by department name.
        result = []
        seen = set()

        for item in departments:

            key = item["value"].lower()

            if key not in seen:
                seen.add(key)
                result.append(item)

        return result

    # ---------------------------------------------------------
    # Programs
    # ---------------------------------------------------------

    def _extract_programs(
        self,
        pages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        programs = []

        for page in pages:

            text = (
                page.get("content")
                or ""
            ).lower()

            for pattern in self.PROGRAM_PATTERNS:

                if pattern in text:

                    programs.append(
                        self._field(
                            pattern.upper(),
                            page.get("url"),
                        )
                    )

        result = []
        seen = set()

        for item in programs:

            normalized = self._normalize_program(
                item["value"]
            )

            key = normalized.lower()

            if key not in seen:

                seen.add(key)

                result.append(
                    self._field(
                        normalized,
                        item["source"],
                    )
                )

        return result

    # ---------------------------------------------------------
    # Keyword evidence
    # ---------------------------------------------------------

    def _find_keyword_evidence(
        self,
        pages: list[dict[str, Any]],
        keywords: list[str],
    ) -> dict[str, Any]:

        for page in pages:

            text = self._page_text(
                page
            ).lower()

            for keyword in keywords:

                if keyword.lower() in text:

                    return self._field(
                        True,
                        page.get("url"),
                    )

        return self._field(
            False,
            None,
        )

    # ---------------------------------------------------------
    # Main enrichment
    # ---------------------------------------------------------

    def enrich_college(
        self,
        college: dict[str, Any],
    ) -> dict[str, Any]:

        name = college.get("name")
        website = college.get("website")

        self._current_city = (
            college.get("city")
            or ""
        )

        self._current_state = (
            college.get("state")
            or ""
        )

        if not website:

            return {
                "name": self._field(
                    name,
                    None,
                ),
                "website": self._field(
                    None,
                    None,
                ),
                "status": "failed",
                "missing_fields": [
                    "website",
                ],
                "sources": [],
                "errors": [
                    "Official website unavailable"
                ],
            }

        logger.info(
            "Enriching college: %s",
            name,
        )

        research = (
            self.website_enricher.find_relevant_pages(
                college_name=name,
                website=website,
            )
        )

        if research.get(
            "status"
        ) == "failed":

            return {
                "name": self._field(
                    name,
                    None,
                ),
                "website": self._field(
                    website,
                    website,
                ),
                "status": "failed",
                "missing_fields": [
                    "website_research",
                ],
                "sources": [],
                "errors": research.get(
                    "errors",
                    [],
                ),
            }

        pages = research.get(
            "pages",
            {},
        )

        all_pages = self._all_pages(
            pages
        )

        department_pages = pages.get(
            "departments",
            [],
        )

        program_pages = pages.get(
            "programs",
            [],
        )

        academic_pages = (
            department_pages
            + program_pages
        )

        placement_pages = pages.get(
            "placement",
            [],
        )

        contact_pages = pages.get(
            "contact",
            [],
        )

        innovation_pages = pages.get(
            "innovation",
            [],
        )

        entrepreneurship_pages = pages.get(
            "entrepreneurship",
            [],
        )

        club_event_pages = pages.get(
            "clubs_events",
            [],
        )

        # -----------------------------------------------------
        # Extract information
        # -----------------------------------------------------

        departments = (
            self._extract_departments(
                academic_pages
                or all_pages
            )
        )

        programs = (
            self._extract_programs(
                academic_pages
                or all_pages
            )
        )

        # For contacts, prefer contact pages,
        # then placement pages, then other official pages.
        contact_priority_pages = (
            contact_pages
            + placement_pages
            + all_pages
        )

        official_email = self._find_email(
            contact_priority_pages
        )

        official_phone = self._find_phone(
            contact_priority_pages
        )

        # Address must come ONLY from official
        # Tavily-returned website content.
        address = self._find_address(
            contact_priority_pages
        )

        # -----------------------------------------------------
        # AI evidence
        # -----------------------------------------------------

        ai_ml_related = (
            self._find_keyword_evidence(
                all_pages,
                [
                    "artificial intelligence",
                    "machine learning",
                    "ai and ml",
                    "ai & ml",
                    "artificial intelligence and "
                    "machine learning",
                ],
            )
        )

        generative_ai_related = (
            self._find_keyword_evidence(
                all_pages,
                [
                    "generative ai",
                    "generative artificial intelligence",
                    "genai",
                    "large language model",
                    "large language models",
                ],
            )
        )

        agentic_ai_related = (
            self._find_keyword_evidence(
                all_pages,
                [
                    "agentic ai",
                    "agentic artificial intelligence",
                    "ai agents",
                    "artificial intelligence agents",
                ],
            )
        )

        # -----------------------------------------------------
        # Page fields
        # -----------------------------------------------------

        placement_page = (
            self._field(
                placement_pages[0].get(
                    "url"
                ),
                placement_pages[0].get(
                    "url"
                ),
            )
            if placement_pages
            else self._field(
                None,
                None,
            )
        )

        contact_page = (
            self._field(
                contact_pages[0].get(
                    "url"
                ),
                contact_pages[0].get(
                    "url"
                ),
            )
            if contact_pages
            else self._field(
                None,
                None,
            )
        )

        # -----------------------------------------------------
        # Missing fields
        # -----------------------------------------------------

        missing_fields = []

        if not departments:
            missing_fields.append(
                "departments"
            )

        if not programs:
            missing_fields.append(
                "programs"
            )

        if placement_page["value"] is None:
            missing_fields.append(
                "placement_page"
            )

        if contact_page["value"] is None:
            missing_fields.append(
                "contact_page"
            )

        if official_email["value"] is None:
            missing_fields.append(
                "official_email"
            )

        if official_phone["value"] is None:
            missing_fields.append(
                "official_phone"
            )

        if address["value"] is None:
            missing_fields.append(
                "address"
            )

        if not innovation_pages:
            missing_fields.append(
                "innovation_information"
            )

        if not entrepreneurship_pages:
            missing_fields.append(
                "entrepreneurship_information"
            )

        if not club_event_pages:
            missing_fields.append(
                "clubs_events"
            )

        status = (
            "complete"
            if not missing_fields
            else "partial"
        )

        # -----------------------------------------------------
        # Sources
        # -----------------------------------------------------

        sources = self._unique(
            research.get(
                "sources",
                [],
            )
        )

        # -----------------------------------------------------
        # Final structured profile
        # -----------------------------------------------------

        return {
            "name": self._field(
                name,
                website,
            ),

            "website": self._field(
                website,
                website,
            ),

            # Discovery information is preserved,
            # but not falsely presented as official
            # website evidence.
            "state": self._field(
                college.get("state"),
                None,
            ),

            "city": self._field(
                college.get("city"),
                None,
            ),

            "address": address,

            "departments": departments,

            "programs": programs,

            "ai_ml_related": ai_ml_related,

            "generative_ai_related": (
                generative_ai_related
            ),

            "agentic_ai_related": (
                agentic_ai_related
            ),

            "placement_page": placement_page,

            "contact_page": contact_page,

            "official_email": official_email,

            "official_phone": official_phone,

            "innovation": [
                self._field(
                    page.get("url"),
                    page.get("url"),
                )
                for page in innovation_pages
            ],

            "entrepreneurship": [
                self._field(
                    page.get("url"),
                    page.get("url"),
                )
                for page in entrepreneurship_pages
            ],

            "clubs_events": [
                self._field(
                    page.get("url"),
                    page.get("url"),
                )
                for page in club_event_pages
            ],

            "sources": sources,

            "status": status,

            "missing_fields": missing_fields,

            "errors": research.get(
                "errors",
                [],
            ),
        }