from typing import Any, Dict, Optional


class ContactDiscoveryAgent:
    """
    Discovers a new college contact for a requested role.

    Used primarily by the WRONG_CONTACT workflow.
    """

    def __init__(self, search_service):
        self.search_service = search_service

    def discover_contact(
        self,
        college_name: str,
        college_website: Optional[str],
        requested_role: str,
        existing_contact: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        search_results = self.search_service.search_contact(
            college_name=college_name,
            college_website=college_website,
            requested_role=requested_role,
        )

        existing_email = (
            (existing_contact or {}).get("email") or ""
        ).strip().lower()

        existing_phone = (
            (existing_contact or {}).get("phone") or ""
        ).strip()

        for contact in search_results:

            candidate_email = (
                contact.get("email") or ""
            ).strip().lower()

            candidate_phone = (
                contact.get("phone") or ""
            ).strip()

            # Never return the existing contact
            if (
                candidate_email
                and candidate_email == existing_email
            ):
                continue

            if (
                candidate_phone
                and candidate_phone == existing_phone
            ):
                continue

            return {
                "status": "found",
                "contact": contact,
            }

        return {
            "status": "not_found",
            "contact": None,
            "message": "New contact details not found/available.",
        }