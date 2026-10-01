import logging
import re
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
        1. Clean college name and domain for precision search.
        2. Execute structured Tavily searches without term-bloat or strict quote locks.
        3. Classify official pages + allow official social channels (LinkedIn, WhatsApp).
        4. Run targeted fallback searches for missing categories.
    """
    PAGE_KEYWORDS = {
        "contact": [
            "contact",
            "contact-us",
            "contactus",
            "reach-us",
            "location",
            "address",
        ],
        "departments": [
            "department",
            "departments",
            "cse",
            "computer-science",
            "artificial-intelligence",
            "machine-learning",
            "data-science",
            "ece",
            "eee",
            "civil",
            "mechanical",
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
            "academics",
        ],
        "placement": [
            "placement",
            "placements",
            "training-placement",
            "training_and_placement",
            "career",
            "jobs",
            "tpo",
        ],
        "training": [
            "training",
            "trainings",
            "training-program",
            "training-programs",
            "training-cell",
            "skill-development",
            "skill-development-program",
            "industry-training",
        ],
        "workshop": [
            "workshop",
            "workshops",
            "bootcamp",
            "bootcamps",
            "hackathon",
            "hackathons",
            "technical-event",
            "technical-events",
            "student-activities",
            "symposium",
        ],
        "admissions": [
            "admission",
            "admissions",
        ],
        "innovation": [
            "innovation",
            "iic",
            "incubation",
            "research",
        ],
        "entrepreneurship": [
            "entrepreneur",
            "entrepreneurship",
            "startup",
            "venture",
            "edc",
            "e-cell",
        ],
        "clubs_events": [
            "club",
            "clubs",
            "student-club",
            "technical-club",
            "student-activities",
            "activities",
            "events",
            "news",
        ],
        "contact_form": [
            "contact-us",
            "contact",
            "enquiry",
            "inquiry",
            "reach-us",
            "get-in-touch",
        ],
        "whatsapp": [
            "whatsapp",
            "wa.me",
            "whatsapp-us",
            "chat-on-whatsapp",
        ],
        "linkedin": [
            "linkedin",
            "linkedin.com",
        ],
    }
    ALLOWED_SOCIAL_DOMAINS = {
        "linkedin.com",
        "wa.me",
        "whatsapp.com",
    }
    FALLBACK_GROUPS = [
        (
            "academic",
            ["departments", "programs"],
            "departments CSE computer science engineering programs B.Tech M.Tech",
        ),
        (
            "placement_contact",
            ["placement", "contact"],
            "contact address phone email placement cell training",
        ),
        (
            "training_workshop",
            ["training", "workshop"],
            "student training programs technical workshops hackathons bootcamps",
        ),
        (
            "institutional",
            ["innovation", "entrepreneurship", "clubs_events"],
            "innovation cell entrepreneurship incubation student clubs technical events",
        ),
        (
            "contact_channels",
            ["contact_form", "whatsapp", "linkedin"],
            "contact form enquiry WhatsApp LinkedIn official",
        ),
    ]
    MAX_FALLBACK_SEARCHES = 3
    def __init__(self, search_client: TavilySearchClient | None = None):
        self.search_client = search_client or TavilySearchClient()
    # ---------------------------------------------------------
    # Domain & String Helpers
    # ---------------------------------------------------------
    @staticmethod
    def _clean_college_name(college_name: str) -> str:
        """
        Strips dashes, special characters, and redundant location suffixes to prevent search quote-lock.
        Example: "BCET Visakhapatnam – Behara College of Engineering and Technology, Visakhapatnam"
        --> "Behara College of Engineering and Technology Visakhapatnam"
        """
        if not college_name:
            return ""
        
        # Remove text inside parentheses or dashes
        cleaned = re.sub(r"\s*[–\-\|]\s*", " ", college_name)
        cleaned = re.sub(r"[^\w\s]", " ", cleaned)
        words = cleaned.split()
        
        # Deduplicate consecutive words
        seen, unique_words = set(), []
        for w in words:
            wl = w.lower()
            if wl not in seen or len(wl) <= 3:
                seen.add(wl)
                unique_words.append(w)
        return " ".join(unique_words)
    @staticmethod
    def _normalize_domain(website: str) -> str:
        website = website.strip()
        if not website.startswith(("http://", "https://")):
            website = "https://" + website
        domain = urlparse(website).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    def _is_allowed_domain(self, url: str, official_domain: str, category_context: list[str]) -> bool:
        try:
            result_domain = urlparse(url).netloc.lower()
            if result_domain.startswith("www."):
                result_domain = result_domain[4:]
            # Official domain or subdomain
            if result_domain == official_domain or result_domain.endswith("." + official_domain):
                return True
            # Allow social domains for social/contact channels
            if any(social in result_domain for social in self.ALLOWED_SOCIAL_DOMAINS):
                return True
            return False
        except Exception:
            return False
    # ---------------------------------------------------------
    # Page classification
    # ---------------------------------------------------------
    def _classify_page(self, url: str, title: str, content: str = "") -> list[str]:
        text = f"{url} {title} {content[:300]}".lower()
        categories = []
        # Check for Homepage
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        if not path or path in ["index.html", "index.php", "home", "home.html", "default.aspx"]:
            categories.extend(["contact", "departments", "programs"])
        for category, keywords in self.PAGE_KEYWORDS.items():
            if any(keyword.lower() in text for keyword in keywords):
                if category not in categories:
                    categories.append(category)
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
        for result in response.get("results", []):
            url = (result.get("url") or "").strip()
            title = (result.get("title") or "").strip()
            content = result.get("content") or ""
            if not url:
                continue
            categories = self._classify_page(url=url, title=title, content=content)
            if not self._is_allowed_domain(url, official_domain, categories):
                ignored_results.append({
                    "title": title,
                    "url": url,
                    "reason": "non_official_domain",
                })
                continue
            page = {
                "title": title,
                "url": url,
                "content": content,
                "categories": categories,
            }
            if url not in sources:
                sources.append(url)
            for category in categories:
                existing_urls = {item.get("url") for item in pages[category]}
                if url not in existing_urls:
                    pages[category].append(page)
    # ---------------------------------------------------------
    # Missing category detection & Query builders
    # ---------------------------------------------------------
    @staticmethod
    def _has_any_category(
        pages: dict[str, list[dict[str, Any]]],
        categories: list[str],
    ) -> bool:
        return any(pages.get(category) for category in categories)
    def _build_broad_query(self, college_name: str, website: str) -> str:
        clean_name = self._clean_college_name(college_name)
        official_domain = self._normalize_domain(website)
        return (
            f"{clean_name} site:{official_domain} "
            f"official website departments engineering placement contact courses"
        )
    def _build_fallback_query(
        self,
        college_name: str,
        website: str,
        group_name: str,
        keywords: str,
    ) -> str:
        clean_name = self._clean_college_name(college_name)
        official_domain = self._normalize_domain(website)
        # Allow social fallback searches to search broader web for official accounts
        if group_name == "contact_channels":
            return f'"{clean_name}" {keywords}'
        return f"{clean_name} site:{official_domain} {keywords}"
    # ---------------------------------------------------------
    # Main method
    # ---------------------------------------------------------
    def find_relevant_pages(
        self,
        college_name: str,
        website: str,
        max_results: int = 10,
    ) -> dict[str, Any]:
        official_domain = self._normalize_domain(website)
        pages = {category: [] for category in self.PAGE_KEYWORDS}
        sources = []
        ignored_results = []
        errors = []
        search_count = 0
        # =====================================================
        # 1. BROAD SEARCH
        # =====================================================
        broad_query = self._build_broad_query(college_name, website)
        logger.info("Broad Tavily search for: %s", college_name)
        try:
            response = self.search_client.search(
                query=broad_query,
                max_results=max_results,
            )
            search_count += 1
            if response.get("error"):
                errors.append({"type": "broad_search", "error": response["error"]})
            else:
                self._process_results(
                    response=response,
                    official_domain=official_domain,
                    pages=pages,
                    sources=sources,
                    ignored_results=ignored_results,
                )
        except Exception as exc:
            logger.exception("Broad Tavily search failed")
            errors.append({"type": "broad_search", "error": str(exc)})
        # =====================================================
        # 2. CONTROLLED FALLBACK SEARCHES
        # =====================================================
        for group_name, categories, keywords in self.FALLBACK_GROUPS:
            if search_count >= self.MAX_FALLBACK_SEARCHES + 1:
                break
            if self._has_any_category(pages, categories):
                logger.info("Skipping fallback '%s' because useful pages already exist", group_name)
                continue
            query = self._build_fallback_query(
                college_name, website, group_name, keywords
            )
            logger.info("Fallback Tavily search '%s' for: %s", group_name, college_name)
            try:
                response = self.search_client.search(
                    query=query,
                    max_results=max_results,
                )
                search_count += 1
                if response.get("error"):
                    errors.append({
                        "type": f"fallback_{group_name}",
                        "error": response["error"],
                    })
                else:
                    self._process_results(
                        response=response,
                        official_domain=official_domain,
                        pages=pages,
                        sources=sources,
                        ignored_results=ignored_results,
                    )
            except Exception as exc:
                logger.exception("Fallback search failed: %s", group_name)
                errors.append({"type": f"fallback_{group_name}", "error": str(exc)})
        has_pages = any(pages[category] for category in pages)
        status = "complete" if has_pages else "partial"
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
