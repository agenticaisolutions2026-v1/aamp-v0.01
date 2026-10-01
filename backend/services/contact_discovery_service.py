import re
from typing import Any, Dict, List, Optional

from backend.tools.college_discovery.tavily_contact_search import (
    TavilyContactSearch,
)


class ContactDiscoveryService:
    """
    Discovers a new contact for a requested role.

    Used by the WRONG_CONTACT workflow.

    Important:
    - Existing contact details are never returned as the new contact.
    - If no different contact is found, the service returns NOT_FOUND.
    """

    def __init__(self):
        self.contact_search = TavilyContactSearch()

    def find_new_contact(
        self,
        college_name: str,
        state: str,
        official_domain: str,
        requested_role: str,
        existing_contact: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        if not college_name or not official_domain:
            return {
                "status": "not_found",
                "contact": None,
                "message": "New contact details not found/available.",
            }

        if not requested_role:
            return {
                "status": "not_found",
                "contact": None,
                "message": "Requested contact role is not available.",
            }

        existing_email = self._normalize_email(
            (existing_contact or {}).get("email")
        )

        existing_phone = self._normalize_phone(
            (existing_contact or {}).get("phone")
        )

        # --------------------------------------------------
        # Search Tavily using primary & fallback queries
        # --------------------------------------------------

        results = self.search_role_contact(
            college_name=college_name,
            state=state,
            official_domain=official_domain,
            requested_role=requested_role,
        )

        if not results:
            return {
                "status": "not_found",
                "contact": None,
                "message": "New contact details not found/available.",
            }

        # --------------------------------------------------
        # Find candidate contacts
        # --------------------------------------------------

        candidates = []

        for result in results:

            content = (
                result.get("content")
                or result.get("raw_content")
                or ""
            )

            title = result.get("title") or ""
            url = result.get("url") or ""

            text = f"{title} {content}".lower()

            # ----------------------------------------------
            # Requested role must appear in the result
            # ----------------------------------------------

            role_terms = self._build_role_terms(
                requested_role
            )

            if not any(
                term.lower() in text
                for term in role_terms
            ):
                continue

            email = self._extract_email(text, official_domain)
            phone = self._extract_phone(text)

            # ----------------------------------------------
            # Fallback: If phone found but no email, try finding
            # domain/general contact email from the same site
            # ----------------------------------------------
            if not email:
                email = self._fallback_domain_email_search(
                    college_name=college_name,
                    official_domain=official_domain,
                    existing_email=existing_email,
                )

            # ----------------------------------------------
            # We need at least one new contact identifier
            # ----------------------------------------------

            if not email and not phone:
                continue

            # ----------------------------------------------
            # Never return the existing contact
            # ----------------------------------------------

            if email and email == existing_email:
                email = None  # Reset matched duplicate email

            if phone and phone == existing_phone:
                phone = None  # Reset matched duplicate phone

            if not email and not phone:
                continue

            candidates.append(
                {
                    "name": None,
                    "role": requested_role,
                    "email": email,
                    "phone": phone,
                    "source": url,
                }
            )

        # --------------------------------------------------
        # Remove duplicate candidates
        # --------------------------------------------------

        candidates = self._remove_duplicates(
            candidates
        )

        if not candidates:
            return {
                "status": "not_found",
                "contact": None,
                "message": "New contact details not found/available.",
            }

        # Prioritize candidates that have an email address
        candidates.sort(key=lambda c: 0 if c.get("email") else 1)

        # --------------------------------------------------
        # Return first valid NEW contact
        # --------------------------------------------------

        return {
            "status": "found",
            "contact": candidates[0],
            "message": "New contact found.",
        }

    # ======================================================
    # Extended Role Search Logic
    # ======================================================

    def search_role_contact(
        self,
        college_name: str,
        state: str,
        official_domain: str,
        requested_role: str,
    ) -> List[Dict[str, Any]]:

        if not college_name or not official_domain or not requested_role:
            return []

        # Primary Targeted Query
        query_1 = (
            f'"{college_name}" '
            f'"{state}" '
            f'site:{official_domain} '
            f'"{requested_role}" '
            'email phone contact'
        )

        raw = self.contact_search.client.search(
            query_1,
            max_results=10,
        )

        results = raw.get("results", [])

        # Secondary Query Fallback if primary returned zero results
        if not results:
            query_2 = (
                f'"{college_name}" '
                f'site:{official_domain} '
                f'placement TPO email "@"'
            )
            raw_fallback = self.contact_search.client.search(
                query_2,
                max_results=10,
            )
            results = raw_fallback.get("results", [])

        return results

    def _fallback_domain_email_search(
        self,
        college_name: str,
        official_domain: str,
        existing_email: str,
    ) -> Optional[str]:
        """
        Attempts a general domain email search if specific role query missed the email.
        """
        try:
            query = f'"{college_name}" site:{official_domain} "@" placement contact'
            raw = self.contact_search.client.search(query, max_results=5)
            
            for res in raw.get("results", []):
                text = f"{res.get('title', '')} {res.get('content', '')}".lower()
                found_email = self._extract_email(text, official_domain)
                
                if found_email and found_email != existing_email:
                    return found_email
        except Exception:
            pass

        return None

    # ======================================================
    # Helpers
    # ======================================================

    @staticmethod
    def _normalize_email(
        email: Optional[str],
    ) -> str:

        if not email:
            return ""

        return email.strip().lower()

    @staticmethod
    def _normalize_phone(
        phone: Optional[str],
    ) -> str:

        if not phone:
            return ""

        return "".join(
            character
            for character in phone
            if character.isdigit()
        )

    @staticmethod
    def _extract_email(
        text: str,
        official_domain: str = "",
    ) -> Optional[str]:

        matches = re.findall(
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            text,
        )

        if not matches:
            return None

        # Filter out common false positive asset extension matches
        valid_emails = [
            e.lower() for e in matches
            if not e.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg'))
        ]

        if not valid_emails:
            return None

        # Prioritize email ending with official domain if available
        if official_domain:
            clean_domain = official_domain.lower().replace("www.", "")
            for email in valid_emails:
                if clean_domain in email:
                    return email

        return valid_emails[0]

    @staticmethod
    def _extract_phone(
        text: str,
    ) -> Optional[str]:

        matches = re.findall(
            r"(?:\+91[\s-]?)?[6-9]\d{9}",
            text,
        )

        if not matches:
            return None

        return matches[0]

    @staticmethod
    def _build_role_terms(
        requested_role: str,
    ) -> List[str]:

        role = requested_role.strip().lower()

        role_terms = [
            role,
        ]

        if "placement officer" in role:
            role_terms.extend(
                [
                    "training and placement officer",
                    "training & placement officer",
                    "placement officer",
                    "tpo",
                    "placement cell",
                    "training and placement",
                ]
            )

        elif "placement" in role:
            role_terms.extend(
                [
                    "placement officer",
                    "training and placement",
                    "training & placement",
                    "placement cell",
                    "tpo",
                ]
            )

        return list(
            dict.fromkeys(role_terms)
        )

    @classmethod
    def _remove_duplicates(
        cls,
        candidates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        unique = []
        seen = set()

        for candidate in candidates:

            email = cls._normalize_email(
                candidate.get("email")
            )

            phone = cls._normalize_phone(
                candidate.get("phone")
            )

            identifier = email or phone

            if not identifier:
                continue

            if identifier in seen:
                continue

            seen.add(identifier)
            unique.append(candidate)

        return unique

    @staticmethod
    def extract_requested_role(message: str) -> str:
        """
        Extract the contact role requested by the college
        from a WRONG_CONTACT response.
        
        If no specific role is named (e.g. "I am not the right person"),
        defaults to 'training and placement officer'.
        """

        if not message:
            return "training and placement officer"

        text = message.strip().lower()

        role_patterns = [
            (
                "training and placement officer",
                [
                    "training and placement officer",
                    "training & placement officer",
                    "placement officer",
                    "placement coordinator",
                    "tpo",
                ],
            ),
            (
                "training and placement department",
                [
                    "training and placement department",
                    "training & placement department",
                    "placement department",
                    "placement cell",
                ],
            ),
            (
                "placement coordinator",
                [
                    "placement coordinator",
                ],
            ),
            (
                "training and placement",
                [
                    "training and placement",
                    "training & placement",
                ],
            ),
            (
                "principal",
                [
                    "principal",
                ],
            ),
            (
                "head of department",
                [
                    "head of department",
                    "hod",
                ],
            ),
        ]

        # 1. Check for specific role matches
        for normalized_role, patterns in role_patterns:
            for pattern in patterns:
                if pattern in text:
                    return normalized_role

        # 2. Fallback for generic WRONG_CONTACT messages
        # ("I am not the right person", "I don't handle this", "contact another department")
        return "training and placement officer"