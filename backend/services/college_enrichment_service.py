import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from backend.tools.college_discovery.website_enricher import WebsiteEnricher
from backend.tools.college_discovery.tavily_contact_search import TavilyContactSearch
logger = logging.getLogger(__name__)
class CollegeEnrichmentService:
    """
    Converts official college website research into a structured college profile.
    Uses Direct Web Scraping first, and falls back to Tavily API for missing fields.
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
        "b.tech", "btech", "b.tech.", "m.tech", "mtech", "m.tech.",
        "b.e.", "b.e", "m.e.", "m.e", "b.sc", "b.sc.", "m.sc", "m.sc.",
        "bca", "mca", "mba", "ph.d", "phd"
    ]
    CONTACT_ROLE_PATTERNS = {
        # Tier 1: Placement & Career Roles
        "Training and Placement": [
            "training and placement", "training & placement", "training placement",
            "placement and training", "placement & training", "t&p cell", "t & p cell", "t&p",
        ],
        "Placement": [
            "placement officer", "placement cell", "placement coordinator",
            "placement department", "career services", "placement dean", "placement director",
        ],
        "Training": [
            "training officer", "training cell", "training coordinator",
            "training department", "skill development cell",
        ],
        "Industry Relations": [
            "industry relations", "industry interaction", "industry liaison",
            "corporate relations", "corporate liaison",
        ],
        
        # Tier 2: Departmental Leadership
        "Head of Department": [
            "head of department", "head of the department", "hod", "h.o.d.",
            "department head", "programme coordinator",
        ],
        "Faculty / Professor": [
            "professor", "associate professor", "assistant professor",
            "faculty", "faculty contact", "convener",
        ],
        # Tier 3: Executive Leadership
        "Principal / Director": [
            "principal", "director", "vice chancellor", "pro vice chancellor",
            "vc office", "dean",
        ],
        # Tier 4: General Administration
        "Admissions": [
            "admission cell", "admission officer", "admissions coordinator",
            "admission counselor", "admission helpdesk",
        ],
        "Administration": [
            "registrar", "administrative officer", "office superintendent",
            "helpdesk", "enquiry cell", "contact us", "general enquiry",
        ],
    }
    EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    INSTITUTIONAL_PREFIXES = [
        "admissions@", "info@", "contact@", "principal@", 
        "registrar@", "enquiry@", "helpdesk@", "tpo@", "placement@"
    ]
    PHONE_PATTERNS = [
        re.compile(r"\+91[\s.-]?[6-9]\d{4}[\s.-]?\d{5}"),
        re.compile(r"\b0?\d{3,5}[\s.-]?\d{6,8}\b"),
        re.compile(r"\b[6-9]\d{9}\b"),
    ]
    # Core mandatory fields required for a valid enriched college profile
    CORE_FIELDS = [
        "departments",
        "programs",
        "placement_page",
        "contact_page",
        "official_email",
        "official_phone",
        "address",
    ]
    def __init__(
        self,
        website_enricher: Optional[WebsiteEnricher] = None,
        contact_search: Optional[TavilyContactSearch] = None,
    ):
        self.website_enricher = website_enricher or WebsiteEnricher()
        self.contact_search = contact_search or TavilyContactSearch()
        self._current_city = ""
        self._current_state = ""
    # ---------------------------------------------------------
    # Helper Methods
    # ---------------------------------------------------------
    @staticmethod
    def _unique(values: List[str]) -> List[str]:
        result, seen = [], set()
        for v in values:
            val = str(v or "").strip()
            if val and val.lower() not in seen:
                seen.add(val.lower())
                result.append(val)
        return result
    @staticmethod
    def _field(value: Any, source: Optional[str]) -> Dict[str, Any]:
        return {"value": value, "source": source}
    @staticmethod
    def _clean_email(raw_email: Optional[str]) -> Optional[str]:
        if not raw_email:
            return None
        cleaned = raw_email.strip(" ._-")
        match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", cleaned)
        return match.group(0) if match else None
    @staticmethod
    def _sanitize_address(address_val: Optional[str]) -> Optional[str]:
        if not address_val:
            return None
        cleaned = re.sub(r"\s+", " ", address_val).strip()
        bad_doc_patterns = r"(?:institution list|alphabetical order|nirf|ranking|page \d+ of \d+)"
        if re.search(bad_doc_patterns, cleaned, re.IGNORECASE):
            return None
        if len(cleaned) < 20:
            return cleaned
        generic_address_pattern = re.compile(
            r"(?:(?:Plot|Door|D\.|H\.|Sy\.|No\.|Flat|Campus|Near|Opp\.|Beside|K\.?\s*Kotturu|3rd Mile|R\.V\.S|NH-\d+)?\s*[\w\s\.,\-\&\(\)]+?)"
            r"(?:\b[1-9]\d{5}\b|Andhra Pradesh|Telangana|Karnataka|Tamil Nadu|Maharashtra|Delhi|Kerala|Gujarat|Rajasthan|Uttar Pradesh|West Bengal|Madhya Pradesh|Bihar|Punjab|Haryana)",
            re.IGNORECASE
        )
        match = generic_address_pattern.search(cleaned)
        if match:
            extracted = match.group(0).strip(" ,.-")
            if len(extracted) >= 15:
                return extracted
        pin_match = re.search(r".*?\b[1-9]\d{5}\b", cleaned)
        if pin_match:
            extracted = pin_match.group(0).strip(" ,.-")
            if len(extracted) > 180:
                extracted = "..." + extracted[-170:]
            return extracted
        if len(cleaned) > 180:
            return cleaned[:180].rstrip(" ,.-") + "..."
        return cleaned
    @staticmethod
    def _page_text(page: Dict[str, Any]) -> str:
        return f"{page.get('title', '')} {page.get('content', '')}"
    def _all_pages(self, pages: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        result, seen = [], set()
        for category_pages in pages.values():
            for page in category_pages:
                url = str(page.get("url") or "").strip()
                if url and url not in seen:
                    seen.add(url)
                    result.append(page)
        return result
    def _normalize_program(self, program: str) -> str:
        val = str(program or "").strip().upper().replace(" ", "").rstrip(".")
        normalized = {
            "B.TECH": "B.Tech", "BTECH": "B.Tech",
            "M.TECH": "M.Tech", "MTECH": "M.Tech",
            "B.E.": "B.E", "B.E": "B.E", "BE": "B.E",
            "M.E.": "M.E", "M.E": "M.E", "ME": "M.E",
            "B.SC": "B.Sc", "BSC": "B.Sc",
            "M.SC": "M.Sc", "MSC": "M.Sc",
            "BCA": "BCA", "MCA": "MCA", "MBA": "MBA",
            "PH.D": "Ph.D", "PHD": "Ph.D",
        }
        return normalized.get(val, program.strip())
    # ---------------------------------------------------------
    # Extractor Functions
    # ---------------------------------------------------------
    def _find_email(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        all_found = []
        for page in pages:
            content = page.get("content") or ""
            matches = self.EMAIL_PATTERN.findall(content)
            for match in matches:
                clean = self._clean_email(match)
                if clean:
                    if any(clean.lower().startswith(prefix) for prefix in self.INSTITUTIONAL_PREFIXES):
                        return self._field(clean, page.get("url"))
                    all_found.append(self._field(clean, page.get("url")))
        return all_found[0] if all_found else self._field(None, None)
    def _find_phone(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        for page in pages:
            content = page.get("content") or ""
            for pattern in self.PHONE_PATTERNS:
                matches = pattern.findall(content)
                for match in matches:
                    clean = match.strip()
                    digits_only = re.sub(r"\D", "", clean)
                    if len(digits_only) >= 8 and len(digits_only) != 6:
                        return self._field(clean, page.get("url"))
        return self._field(None, None)
    def _find_address(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        address_labels = ["address:", "address -", "address :", "college address:", "campus address:", "location:", "located at:"]
        expected_city = self._current_city.strip().lower()
        expected_state = self._current_state.strip().lower()
        bad_terms = ["email", "@", "social media", "thank you", "alphabetical order", "institution list", "nirf", "ranking"]
        # 1. Primary label or city search
        for page in pages:
            page_url = page.get("url", "").lower()
            if "nirf" in page_url or "rank" in page_url:
                continue
            content = page.get("content") or ""
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            for index, line in enumerate(lines):
                lower = line.lower()
                matched_label = next((l for l in address_labels if l in lower), None)
                candidates = []
                if matched_label:
                    remainder = line[lower.find(matched_label) + len(matched_label):].strip(" :-\t")
                    if remainder: candidates.append(remainder)
                    if index + 1 < len(lines): candidates.append(lines[index + 1])
                else:
                    if (expected_city and expected_city in lower) or (expected_state and expected_state in lower):
                        candidates.append(line)
                for candidate in candidates:
                    cand_lower = candidate.lower()
                    if any(bad in cand_lower for bad in bad_terms):
                        continue
                    if len(candidate) < 15:
                        continue
                    has_number = bool(re.search(r"\d", candidate))
                    has_address_term = any(t in cand_lower for t in ["road", "street", "nagar", "campus", "district", "pin", "pincode", "andhra pradesh", "telangana", "india"])
                    if has_number or has_address_term:
                        return self._field(candidate, page.get("url"))
        # 2. Fallback: Search for Indian 6-digit PIN code or state in any page
        for page in pages:
            content = page.get("content") or ""
            pin_match = re.search(r"(?:[A-Za-z0-9\s,\-\.]{10,120})\b[1-9]\d{5}\b", content)
            if pin_match:
                candidate = pin_match.group(0).strip()
                if not any(bad in candidate.lower() for bad in bad_terms):
                    return self._field(candidate, page.get("url"))
        return self._field(None, None)
    def _extract_departments(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        departments = []
        for page in pages:
            text = self._page_text(page).lower()
            for dept, patterns in self.DEPARTMENT_PATTERNS.items():
                if any(p.lower() in text for p in patterns):
                    departments.append(self._field(dept, page.get("url")))
        result, seen = [], set()
        for item in departments:
            key = item["value"].lower()
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result
    def _extract_programs(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        programs = []
        for page in pages:
            text = (page.get("content") or "").lower()
            for pattern in self.PROGRAM_PATTERNS:
                if pattern in text:
                    programs.append(self._field(pattern.upper(), page.get("url")))
        result, seen = [], set()
        for item in programs:
            norm = self._normalize_program(item["value"])
            if norm.lower() not in seen:
                seen.add(norm.lower())
                result.append(self._field(norm, item["source"]))
        return result
    def _find_contact_role(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        tier1_placement = None
        tier2_hod = None
        tier3_executive = None
        tier4_admin = None
        for page in pages:
            text = self._page_text(page).lower()
            url = page.get("url")
            for role, patterns in self.CONTACT_ROLE_PATTERNS.items():
                if any(pattern in text for pattern in patterns):
                    field_match = self._field(role, url)
                    if role in ["Training and Placement", "Placement", "Training", "Industry Relations"]:
                        if not tier1_placement:
                            tier1_placement = field_match
                    elif role in ["Head of Department", "Faculty / Professor"]:
                        if not tier2_hod:
                            tier2_hod = field_match
                    elif role in ["Principal / Director"]:
                        if not tier3_executive:
                            tier3_executive = field_match
                    else:
                        if not tier4_admin:
                            tier4_admin = field_match
        if tier1_placement: return tier1_placement
        if tier2_hod: return tier2_hod
        if tier3_executive: return tier3_executive
        if tier4_admin: return tier4_admin
        return self._field("General Administration", None)
    def _find_keyword_evidence(self, pages: List[Dict[str, Any]], keywords: List[str]) -> Dict[str, Any]:
        for page in pages:
            text = self._page_text(page).lower()
            if any(k.lower() in text for k in keywords):
                return self._field(True, page.get("url"))
        return self._field(False, None)
    def _find_contact_form(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        form_keywords = ["<form", "contact form", "enquiry form", "inquiry form", "send message", "submit enquiry", "get in touch", "reach us"]
        for page in pages:
            url = (page.get("url") or "").lower()
            content = (page.get("content") or "").lower()
            
            # Check URL for contact form indicators
            if any(k in url for k in ["contact", "enquiry", "inquiry", "reach-us"]):
                return self._field(True, page.get("url"))
            # Check page content
            if any(k in content for k in form_keywords):
                return self._field(True, page.get("url"))
        return self._field(False, None)
    def _find_social_link(self, pages: List[Dict[str, Any]], patterns: List[str]) -> Dict[str, Any]:
        for page in pages:
            content = page.get("content") or ""
            url = page.get("url") or ""
            
            # Check if current page itself is a social profile
            for pattern in patterns:
                match = re.search(pattern, url, re.IGNORECASE)
                if match:
                    return self._field(match.group(0).rstrip(".,);]"), url)
            # Check page content for social links
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    return self._field(match.group(0).rstrip(".,);]"), url)
        return self._field(None, None)
    # ---------------------------------------------------------
    # Main Method
    # ---------------------------------------------------------
    def enrich_college(self, college: Dict[str, Any]) -> Dict[str, Any]:
        name = college.get("name")
        website = college.get("website")
        self._current_city = college.get("city") or ""
        self._current_state = college.get("state") or ""
        if not website:
            return {
                "name": self._field(name, None),
                "website": self._field(None, None),
                "status": "failed",
                "missing_fields": ["website"],
                "sources": [],
                "errors": ["Official website unavailable"],
            }
        logger.info("Enriching college: %s", name)
        research = self.website_enricher.find_relevant_pages(college_name=name, website=website)
        if research.get("status") == "failed":
            return {
                "name": self._field(name, None),
                "website": self._field(website, website),
                "status": "failed",
                "missing_fields": ["website_research"],
                "sources": [],
                "errors": research.get("errors", []),
            }
        pages = research.get("pages", {})
        all_pages = self._all_pages(pages)
        academic_pages = pages.get("departments", []) + pages.get("programs", [])
        placement_pages = pages.get("placement", [])
        contact_pages = pages.get("contact", [])
        innovation_pages = pages.get("innovation", [])
        entrepreneurship_pages = pages.get("entrepreneurship", [])
        club_event_pages = pages.get("clubs_events", [])
        training_pages = pages.get("training", [])
        workshop_pages = pages.get("workshop", [])
        # Extract structured data
        departments = self._extract_departments(academic_pages or all_pages)
        programs = self._extract_programs(academic_pages or all_pages)
        # Primary Scrape Extraction
        contact_priority = contact_pages + placement_pages + all_pages
        official_email = self._find_email(contact_priority)
        official_phone = self._find_phone(contact_priority)
        address = self._find_address(contact_priority)
        contact_role = self._find_contact_role(contact_priority)
        # Tavily Fallback Extraction for Core Contact Data
        if official_email["value"] is None or official_phone["value"] is None or address["value"] is None:
            parsed_domain = urlparse(website).netloc
            contact_results = self.contact_search.search_details(
                college_name=name,
                state=self._current_state,
                official_domain=parsed_domain,
            )
            if official_email["value"] is None:
                official_email = self._find_email(contact_results)
            if official_phone["value"] is None:
                official_phone = self._find_phone(contact_results)
            if address["value"] is None:
                address = self._find_address(contact_results)
        # Sanitize Address String
        if address["value"]:
            address["value"] = self._sanitize_address(address["value"])
        # Smart fallback for contact_page and placement_page from source URLs
        sources = self._unique(research.get("sources", []))
        placement_url = placement_pages[0].get("url") if placement_pages else next((s for s in sources if any(k in s.lower() for k in ["placement", "job", "career"])), None)
        contact_url = contact_pages[0].get("url") if contact_pages else next((s for s in sources if any(k in s.lower() for k in ["contact", "location", "reach-us"])), website)
        placement_page = self._field(placement_url, placement_url)
        placement_available = self._field(True if placement_url else False, placement_url or website)
        contact_page = self._field(contact_url, contact_url)
        # Training & Workshop opportunities fallback logic
        training = [self._field(p.get("url"), p.get("url")) for p in (training_pages or placement_pages)]
        if not training and placement_url:
            training = [self._field(placement_url, placement_url)]
        workshop_training_opportunity = [self._field(p.get("url"), p.get("url")) for p in (workshop_pages or club_event_pages)]
        if not workshop_training_opportunity and placement_url:
            workshop_training_opportunity = [self._field(placement_url, placement_url)]
        contact_form = self._find_contact_form(all_pages)
        whatsapp = self._find_social_link(all_pages, [r"https?://(?:www\.)?wa\.me/[^\s\"'<]+", r"https?://(?:api\.)?whatsapp\.com/[^\s\"'<]+"])
        linkedin = self._find_social_link(all_pages, [
            r"https?://(?:www\.)?linkedin\.com/company/[^\s\"'<]+",
            r"https?://(?:www\.)?linkedin\.com/school/[^\s\"'<]+",
            r"https?://(?:www\.)?linkedin\.com/in/[^\s\"'<]+",
            r"https?://(?:www\.)?linkedin\.com/edu/[^\s\"'<]+",
        ])
        # Smart fallback for innovation, entrepreneurship, and clubs from source URLs or content
        if not innovation_pages:
            inno_urls = [s for s in sources if any(k in s.lower() for k in ["iic", "innovation", "research", "incubation"])]
            innovation_pages = [{"url": u} for u in inno_urls]
        if not entrepreneurship_pages:
            ent_urls = [s for s in sources if any(k in s.lower() for k in ["edc", "e-cell", "entrepreneur", "startup"])]
            entrepreneurship_pages = [{"url": u} for u in ent_urls]
        if not club_event_pages:
            club_urls = [s for s in sources if any(k in s.lower() for k in ["club", "event", "activity", "news"])]
            club_event_pages = [{"url": u} for u in club_urls]
        # AI Evidence Tagging
        ai_ml = self._find_keyword_evidence(all_pages, ["artificial intelligence", "machine learning", "ai and ml", "ai & ml"])
        gen_ai = self._find_keyword_evidence(all_pages, ["generative ai", "genai", "large language model"])
        agentic_ai = self._find_keyword_evidence(all_pages, ["agentic ai", "ai agents"])
        # Check Core Fields Completeness
        core_missing = []
        if not departments: core_missing.append("departments")
        if not programs: core_missing.append("programs")
        if placement_page["value"] is None: core_missing.append("placement_page")
        if contact_page["value"] is None: core_missing.append("contact_page")
        if official_email["value"] is None: core_missing.append("official_email")
        if official_phone["value"] is None: core_missing.append("official_phone")
        if address["value"] is None: core_missing.append("address")
        # Record all missing fields (core + optional)
        all_missing = list(core_missing)
        if not innovation_pages: all_missing.append("innovation_information")
        if not entrepreneurship_pages: all_missing.append("entrepreneurship_information")
        if not club_event_pages: all_missing.append("clubs_events")
        if not training: all_missing.append("training")
        if not workshop_training_opportunity: all_missing.append("workshop_training_opportunity")
        if not contact_form["value"]: all_missing.append("contact_form")
        if not whatsapp["value"]: all_missing.append("whatsapp")
        if not linkedin["value"]: all_missing.append("linkedin")
        # Status evaluates to "complete" if all core fields are found
        status = "complete" if not core_missing else "partial"
        return {
            "name": self._field(name, website),
            "website": self._field(website, website),
            "state": self._field(college.get("state"), None),
            "city": self._field(college.get("city"), None),
            "address": address,
            "departments": departments,
            "programs": programs,
            "ai_ml_related": ai_ml,
            "generative_ai_related": gen_ai,
            "agentic_ai_related": agentic_ai,
            "official_email": official_email,
            "official_phone": official_phone,
            "innovation": [self._field(p.get("url"), p.get("url")) for p in innovation_pages],
            "entrepreneurship": [self._field(p.get("url"), p.get("url")) for p in entrepreneurship_pages],
            "clubs_events": [self._field(p.get("url"), p.get("url")) for p in club_event_pages],
            "training": training,
            "workshop_training_opportunity": workshop_training_opportunity,
            "placement_page": placement_page,
            "placement_available": placement_available,
            "contact_role": contact_role,
            "contact_page": contact_page,
            "contact_form": contact_form,
            "whatsapp": whatsapp,
            "linkedin": linkedin,
            "sources": sources,
            "status": status,
            "missing_fields": all_missing,
            "errors": research.get("errors", []),
        }
