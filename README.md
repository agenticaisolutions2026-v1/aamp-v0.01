# aamp-v0.01

uv run python tests\classify_enriched_colleges.py

**D:\AgenticAI-Project\aamp-v0.01\backend\services\college_enrichment_service.py**

```python
import logging
import re
from typing import Any
from urllib.parse import urlparse

from backend.tools.college_discovery.website_enricher import (
    WebsiteEnricher,
)
from backend.tools.college_discovery.tavily_contact_search import (
    TavilyContactSearch,
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

    EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

    PHONE_PATTERNS = [
        re.compile(r"\+91[\s.-]?[6-9]\d{4}[\s.-]?\d{5}"),
        re.compile(r"\b[6-9]\d{9}\b"),
        re.compile(r"(?:\+?91[\s.-]?)?(?:\(?0?\d{2,5}\)?[\s.-]?)?\d{6,8}\b"),
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
        contact_search: TavilyContactSearch | None = None,
    ):
        self.website_enricher = (
            website_enricher
            or WebsiteEnricher()
        )

        self.contact_search = (
            contact_search
            or TavilyContactSearch()
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

        # Normal extraction
        official_email = self._find_email(
            contact_priority_pages
        )

        official_phone = self._find_phone(
            contact_priority_pages
        )

        address = self._find_address(
            contact_priority_pages
        )

        # -----------------------------------------------------
        # Contact fallback
        # -----------------------------------------------------


        if (
            official_email["value"] is None
            or official_phone["value"] is None
            or address["value"] is None
        ):
            parsed_domain = urlparse(website).netloc

            contact_results = self.contact_search.search_details(
                college_name=name,
                state=self._current_state,
                official_domain=parsed_domain,
            )

            if official_email["value"] is None:
                official_email = self._find_email(
                    contact_results
                )

            if official_phone["value"] is None:
                official_phone = self._find_phone(
                    contact_results
                )

            if address["value"] is None:
                address = self._find_address(
                    contact_results
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
```

## **test_college_enrichment_10**

```python
import json
from pathlib import Path

from backend.agents.college_enrichment_agent import (
    CollegeEnrichmentAgent,
)
from backend.agents.state import AgentState


INPUT_FILE = Path(
    "data.json"
)

OUTPUT_FILE = Path(
    "college_enriched_test_10.json"
)



def load_colleges():
    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    return data


def enrich_college(
    agent,
    college,
):
    state = AgentState()

    state.user_query = (
        f"Enrich {college.get('name', '')}"
    )

    state.result = {
        "name": college.get("name"),
        "website": college.get("website"),
        "state": college.get("state"),
        "city": college.get("city"),
        "address": college.get("address"),
        "source_url": college.get(
            "source_url"
        ),
    }

    return agent.execute(state)


def main():

    colleges = load_colleges()

    print("=" * 80)
    print("COLLEGE ENRICHMENT TEST — 10 COLLEGES")
    print("=" * 80)

    print(
        f"Selected colleges: {len(colleges)}"
    )

    agent = CollegeEnrichmentAgent()

    results = []

    completed = 0
    partial = 0
    failed = 0

    for index, college in enumerate(
        colleges,
        start=1,
    ):

        print("\n" + "-" * 80)

        print(
            f"[{index}/{len(colleges)}] "
            f"{college.get('name')}"
        )

        print(
            "Website:",
            college.get("website"),
        )

        try:

            state = enrich_college(
                agent,
                college,
            )

            result = state.result

            results.append(result)

            status = result.get(
                "status",
                "failed",
            )

            if status == "complete":
                completed += 1

            elif status == "partial":
                partial += 1

            else:
                failed += 1

            print(
                "Status:",
                status,
            )

            print(
                "Missing:",
                result.get(
                    "missing_fields",
                    [],
                ),
            )

        except Exception as exc:

            failed += 1

            print(
                "ERROR:",
                exc,
            )

            results.append(
                {
                    "name": college.get(
                        "name"
                    ),
                    "status": "failed",
                    "missing_fields": [],
                    "errors": [
                        str(exc)
                    ],
                }
            )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            results,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("\n" + "=" * 80)
    print("10-COLLEGE ENRICHMENT COMPLETED")
    print("=" * 80)

    print(
        "Processed       :",
        len(results),
    )

    print(
        "Completed       :",
        completed,
    )

    print(
        "Partial         :",
        partial,
    )

    print(
        "Failed          :",
        failed,
    )

    print(
        "Output          :",
        OUTPUT_FILE,
    )


if __name__ == "__main__":
    main()
```

# **LEAD QUALIFICATION TEST**

(aamp-v0.01) D:\AgenticAI-Project\aamp-v0.01>uv run python -m tests.test_lead_qualification_testcases

TEST 1 - Strong College
Lead score   : 90
Qualification: qualified

TEST 2 - Qualified Boundary
Lead score   : 80
Qualification: qualified

TEST 3 - Moderate College
Lead score   : 70
Qualification: needs_review

TEST 4 - Needs Review Boundary
Lead score   : 60
Qualification: needs_review

TEST 5 - Low Priority Boundary
Lead score   : 59
Qualification: low_priority

TEST 6 - Missing Information
College       : Missing Information College
AI/ML program : None
Placement     : None
Lead score    : 70
Qualification : needs_review

======================================================================
ALL LEAD QUALIFICATION TEST CASES PASSED
========================================



**D:\AgenticAI-Project\aamp-v0.01\backend\agents\workflow_orchestrator.py code:**


```python
from backend.agents.state import AgentState
from backend.agents.campaign_strategy_agent import CampaignStrategyAgent
from backend.agents.personalization_agent import PersonalizationAgent
from backend.services.campaign_service import CampaignService


class WorkflowOrchestrator:

    def __init__(self):
        self.strategy_agent = CampaignStrategyAgent()
        self.personalization_agent = PersonalizationAgent()
        self.campaign_service = CampaignService()

    def process_college(
        self,
        state: AgentState,
        college: dict,
        lead: dict,
        campaigns: list[dict],
    ) -> AgentState:

        # Use already enriched college data from PostgreSQL
        state.enriched_results = [college]

        # Use already qualified/scored lead data from PostgreSQL
        state.qualified_leads = [lead]

        # Active campaign → do not create another campaign
        active_campaigns = [
            campaign
            for campaign in campaigns
            if campaign.get("status") in [
                "draft",
                "approved",
                "sent",
                "replied",
            ]
        ]

        if active_campaigns:
            state.status = "skipped"
            state.result = {
                "college_id": college.get("id"),
                "college_name": college.get("name"),
                "action": "skip",
                "reason": "Active campaign already exists",
                "campaigns": active_campaigns,
            }
            return state

        # Closed campaign → do not automatically create a new campaign.
        # Human can decide whether to re-campaign.
        closed_campaigns = [
            campaign
            for campaign in campaigns
            if campaign.get("status") == "closed"
        ]

        if closed_campaigns:
            state.status = "waiting"
            state.result = {
                "college_id": college.get("id"),
                "college_name": college.get("name"),
                "action": "human_decision",
                "reason": (
                    "Previous campaign is closed. "
                    "Human decision required for a new campaign."
                ),
                "closed_campaigns": closed_campaigns,
                "create_new_campaign_available": True,
            }
            return state

        # ---------------------------------------------------------
        # Qualification Gate
        # ---------------------------------------------------------

        qualification = lead.get("qualification")

        # 1. Qualified → continue automatically
        if qualification == "qualified":
            pass

        # 2. Needs Review → stop automatic campaign creation
        elif qualification == "needs_review":
            state.status = "waiting"
            state.result = {
                "college_id": college.get("id"),
                "college_name": college.get("name"),
                "action": "human_review",
                "reason": "Lead requires human review before campaign creation",
                "lead": lead,
            }
            return state

        # 3. Low Priority → stop workflow
        elif qualification == "low_priority":
            state.status = "skipped"
            state.result = {
                "college_id": college.get("id"),
                "college_name": college.get("name"),
                "action": "stop",
                "reason": "Lead is low priority",
                "lead": lead,
            }
            return state

        # Unexpected qualification value
        else:
            state.status = "failed"
            state.error = (
                f"Unknown lead qualification: {qualification}"
            )
            state.result = {
                "college_id": college.get("id"),
                "college_name": college.get("name"),
                "action": "error",
                "reason": "Unknown lead qualification",
                "qualification": qualification,
                "lead": lead,
            }
            return state

        # Campaign Strategy
        state = self.strategy_agent.execute(state)

        if state.status == "failed":
            return state

        # Personalization
        state = self.personalization_agent.execute(state)

        if state.status == "failed":
            return state

        # Persist generated campaign as draft
        campaign_data = {
            "college_id": college.get("id"),
            "campaign_type": state.campaign_strategies[0]["campaign_type"],
            "message_type": state.campaign_strategies[0]["message_type"],
            "channel": state.personalized_messages[0]["channel"],
            "subject": state.personalized_messages[0]["subject"],
            "message": state.personalized_messages[0]["message"],
            "priority": state.personalized_messages[0]["priority"],
        }

        campaign = self.campaign_service.create_campaign(campaign_data)

        state.result["campaign_id"] = campaign.id
        state.result["campaign_status"] = campaign.status
        state.result["action"] = "campaign_created"

        return state

    def process_colleges(
        self,
        state: AgentState,
        colleges: list[dict],
    ) -> AgentState:

        from sqlalchemy import select
        from backend.database.session import SessionLocal
        from backend.models.lead import Lead
        from backend.models.campaign import Campaign

        results = []

        college_ids = [
            college.get("id")
            for college in colleges
            if college.get("id") is not None
        ]

        if not college_ids:
            state.status = "completed"
            state.result = {
                "count": 0,
                "results": [],
            }
            return state

        with SessionLocal() as session:

            leads = session.execute(
                select(Lead).where(
                    Lead.college_id.in_(college_ids)
                )
            ).scalars().all()

            campaigns = session.execute(
                select(Campaign).where(
                    Campaign.college_id.in_(college_ids)
                )
            ).scalars().all()

        lead_map = {
            lead.college_id: {
                "id": lead.id,
                "college_id": lead.college_id,
                "contact_role": lead.contact_role,
                "qualification": lead.qualification,
                "lead_score": lead.lead_score,
                "reason": lead.reason,
                "priority": lead.priority,
            }
            for lead in leads
        }

        campaign_map = {}

        for campaign in campaigns:
            campaign_map.setdefault(
                campaign.college_id,
                []
            ).append({
                "id": campaign.id,
                "status": campaign.status,
                "campaign_type": campaign.campaign_type,
                "message_type": campaign.message_type,
                "channel": campaign.channel,
                "subject": campaign.subject,
                "priority": campaign.priority,
                "required_approval": campaign.required_approval,
                "approved_at": campaign.approved_at,
            })

        for college in colleges:

            college_id = college.get("id")

            lead = lead_map.get(college_id)

            if not lead:
                results.append({
                    "college_id": college_id,
                    "college_name": college.get("name"),
                    "action": "skip",
                    "reason": "No lead record found",
                })
                continue

            college_state = AgentState()

            college_state.user_query = state.user_query
            college_state.category = state.category
            college_state.location = state.location

            college_state = self.process_college(
                college_state,
                college,
                lead,
                campaign_map.get(college_id, []),
            )

            results.append(college_state.result)

        state.status = "completed"

        state.result = {
            "count": len(results),
            "results": results,
        }

        return state
```
