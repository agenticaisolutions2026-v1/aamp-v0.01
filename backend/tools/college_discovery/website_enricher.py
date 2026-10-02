import logging
from typing import Any
from urllib.parse import urlparse

from backend.tools.college_discovery.tavily_search_client import (
    TavilySearchClient,
)


logger = logging.getLogger(__name__)


class WebsiteEnricher:
    """
    Finds relevant official college website pages using Tavily.

    Strategy:
        1. One broad search for the college.
        2. Inspect the official results.
        3. Run targeted fallback searches ONLY for important
           missing categories.
        4. Maximum targeted fallbacks are controlled.
        5. Return page candidates and source URLs.

    No database logic.
    No SQL.
    No final field extraction.
    """

    PAGE_KEYWORDS = {
        "contact": [
            "contact",
            "contact-us",
            "contactus",
            "reach-us",
        ],
        "departments": [
            "department",
            "departments",
            "cse",
            "computer-science",
            "artificial-intelligence",
            "machine-learning",
            "data-science",
        ],
        "programs": [
            "program",
            "programs",
            "course",
            "courses",
            "btech",
            "b-tech",
            "mtech",
            "m-tech",
            "engineering",
        ],
        "placement": [
            "placement",
            "placements",
            "training-placement",
            "training_and_placement",
            "career",
        ],
        "admissions": [
            "admission",
            "admissions",
        ],
        "innovation": [
            "innovation",
            "iic",
            "incubation",
        ],
        "entrepreneurship": [
            "entrepreneur",
            "entrepreneurship",
            "startup",
            "venture",
        ],
        "clubs_events": [
            "club",
            "clubs",
            "event",
            "events",
            "workshop",
            "workshops",
            "student-activities",
            "activities",
        ],
    }

    # These fallback groups are used only when
    # important categories are missing.
    FALLBACK_GROUPS = [
        (
            "academic",
            [
                "departments",
                "programs",
            ],
            (
                "departments CSE computer science "
                "artificial intelligence machine learning "
                "engineering programs courses B.Tech M.Tech"
            ),
        ),
        (
            "placement_contact",
            [
                "placement",
                "contact",
            ],
            (
                "contact email official email "
                "address phone "
                "placement placement-cell "
                "training placement "
                "training and placement "
                "career tpo "
                "training placement officer"
            ),
        ),
        (
            "institutional",
            [
                "innovation",
                "entrepreneurship",
                "clubs_events",
            ],
            (
                "innovation cell entrepreneurship "
                "incubation startup student clubs "
                "technical events workshops"
            ),
        ),
    ]

    MAX_FALLBACK_SEARCHES = 2

    def __init__(
        self,
        search_client: TavilySearchClient | None = None,
    ):
        self.search_client = (
            search_client
            or TavilySearchClient()
        )

    # ---------------------------------------------------------
    # Domain helpers
    # ---------------------------------------------------------

    @staticmethod
    def _normalize_domain(
        website: str,
    ) -> str:

        website = website.strip()

        if not website.startswith(
            ("http://", "https://")
        ):
            website = "https://" + website

        domain = urlparse(
            website
        ).netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    @staticmethod
    def _is_official_domain(
        url: str,
        official_domain: str,
    ) -> bool:

        try:

            result_domain = urlparse(
                url
            ).netloc.lower()

            if result_domain.startswith("www."):
                result_domain = result_domain[4:]

            return (
                result_domain == official_domain
                or result_domain.endswith(
                    "." + official_domain
                )
            )

        except Exception:
            return False

    # ---------------------------------------------------------
    # Page classification
    # ---------------------------------------------------------

    def _classify_page(
        self,
        url: str,
        title: str,
    ) -> list[str]:
        """
        Classification uses URL + title only.

        Page content is deliberately not used here.
        """

        text = (
            f"{url} {title}"
        ).lower()

        categories = []

        for (
            category,
            keywords,
        ) in self.PAGE_KEYWORDS.items():

            if any(
                keyword.lower() in text
                for keyword in keywords
            ):
                categories.append(
                    category
                )

        return categories

    # ---------------------------------------------------------
    # Result processing
    # ---------------------------------------------------------

    def _process_results(
        self,
        response: dict[str, Any],
        official_domain: str,
        pages: dict[str, list[dict[str, Any]]],
        sources: list[str],
        ignored_results: list[dict[str, Any]],
    ):

        for result in response.get(
            "results",
            [],
        ):

            url = (
                result.get("url")
                or ""
            ).strip()

            title = (
                result.get("title")
                or ""
            ).strip()

            content = (
                result.get("content")
                or ""
            )

            if not url:
                continue

            # -------------------------------------------------
            # Only accept official college-domain pages.
            # -------------------------------------------------

            if not self._is_official_domain(
                url,
                official_domain,
            ):

                ignored_results.append(
                    {
                        "title": title,
                        "url": url,
                        "reason": (
                            "non_official_domain"
                        ),
                    }
                )

                continue

            categories = (
                self._classify_page(
                    url=url,
                    title=title,
                )
            )

            page = {
                "title": title,
                "url": url,
                "content": content,
                "categories": categories,
            }

            if url not in sources:
                sources.append(url)

            for category in categories:

                existing_urls = {
                    item.get("url")
                    for item in pages[
                        category
                    ]
                }

                if url not in existing_urls:
                    pages[category].append(
                        page
                    )

    # ---------------------------------------------------------
    # Missing category detection
    # ---------------------------------------------------------

    @staticmethod
    def _has_any_category(
        pages: dict[str, list[dict[str, Any]]],
        categories: list[str],
    ) -> bool:

        return any(
            pages.get(category)
            for category in categories
        )

    # ---------------------------------------------------------
    # Query builders
    # ---------------------------------------------------------

    def _build_broad_query(
        self,
        college_name: str,
        website: str,
    ) -> str:

        return (
            f'"{college_name}" '
            f'"{website}" '
            f"official college website "
            f"departments CSE AI ML "
            f"engineering programs "
            f"placement training "
            f"admissions contact "
            f"innovation entrepreneurship "
            f"student clubs technical events workshops"
        )

    def _build_fallback_query(
        self,
        college_name: str,
        website: str,
        keywords: str,
    ) -> str:

        official_domain = (
            self._normalize_domain(
                website
            )
        )

        return (
            f'"{college_name}" '
            f'site:{official_domain} '
            f"{keywords}"
        )

    # ---------------------------------------------------------
    # Main method
    # ---------------------------------------------------------

    def find_relevant_pages(
        self,
        college_name: str,
        website: str,
        max_results: int = 10,
    ) -> dict[str, Any]:

        official_domain = (
            self._normalize_domain(
                website
            )
        )

        pages = {
            category: []
            for category in self.PAGE_KEYWORDS
        }

        sources = []
        ignored_results = []
        errors = []

        search_count = 0

        # =====================================================
        # 1. BROAD SEARCH
        # =====================================================

        broad_query = self._build_broad_query(
            college_name,
            website,
        )

        logger.info(
            "Broad Tavily search for: %s",
            college_name,
        )

        try:

            response = (
                self.search_client.search(
                    query=broad_query,
                    max_results=max_results,
                )
            )

            search_count += 1

            if response.get("error"):

                errors.append(
                    {
                        "type": "broad_search",
                        "error": response["error"],
                    }
                )

            else:

                self._process_results(
                    response=response,
                    official_domain=official_domain,
                    pages=pages,
                    sources=sources,
                    ignored_results=(
                        ignored_results
                    ),
                )

        except Exception as exc:

            logger.exception(
                "Broad Tavily search failed"
            )

            errors.append(
                {
                    "type": "broad_search",
                    "error": str(exc),
                }
            )

        # =====================================================
        # 2. CONTROLLED FALLBACK SEARCHES
        # =====================================================

        for (
            group_name,
            categories,
            keywords,
        ) in self.FALLBACK_GROUPS:

            if (
                search_count
                >= self.MAX_FALLBACK_SEARCHES + 1
            ):
                break

            # If at least one important category
            # in this group already has useful pages,
            # do not spend another Tavily call.
            if self._has_any_category(
                pages,
                categories,
            ):
                logger.info(
                    "Skipping fallback '%s' "
                    "because useful pages already exist",
                    group_name,
                )
                continue

            query = self._build_fallback_query(
                college_name,
                website,
                keywords,
            )

            logger.info(
                "Fallback Tavily search '%s' for: %s",
                group_name,
                college_name,
            )

            try:

                response = (
                    self.search_client.search(
                        query=query,
                        max_results=max_results,
                    )
                )

                search_count += 1

                if response.get("error"):

                    errors.append(
                        {
                            "type": (
                                f"fallback_{group_name}"
                            ),
                            "error": response[
                                "error"
                            ],
                        }
                    )

                else:

                    self._process_results(
                        response=response,
                        official_domain=(
                            official_domain
                        ),
                        pages=pages,
                        sources=sources,
                        ignored_results=(
                            ignored_results
                        ),
                    )

            except Exception as exc:

                logger.exception(
                    "Fallback search failed: %s",
                    group_name,
                )

                errors.append(
                    {
                        "type": (
                            f"fallback_{group_name}"
                        ),
                        "error": str(exc),
                    }
                )

        # =====================================================
        # 3. FINAL STATUS
        # =====================================================

        has_pages = any(
            pages[category]
            for category in pages
        )

        status = (
            "complete"
            if has_pages
            else "partial"
        )

        return {
            "college_name": college_name,
            "website": website,
            "status": status,
            "pages": pages,
            "sources": sources,
            "ignored_results": ignored_results,
            "errors": errors,
            "search_count": search_count,
        }