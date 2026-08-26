from urllib.parse import urlparse


class Deduplicator:
    """
    Removes duplicate colleges from normalized results.

    Uses:
        1. normalized website domain
        2. normalized college name
    """

    def deduplicate(self, colleges):
        unique = {}

        for college in colleges:
            website_key = self._normalize_domain(
                college.get("website", "")
            )

            name_key = self._normalize_name(
                college.get("name", "")
            )

            # Prefer website/domain as the identity.
            key = website_key or name_key

            if not key:
                continue

            if key not in unique:
                unique[key] = college
            else:
                unique[key] = self._merge(
                    unique[key],
                    college
                )

        return list(unique.values())

    def _normalize_domain(self, url):
        """
        Convert different URLs from the same website
        into the same domain key.
        """

        if not url:
            return ""

        try:
            parsed = urlparse(url.lower())

            domain = parsed.netloc

            if domain.startswith("www."):
                domain = domain[4:]

            return domain.strip()

        except Exception:
            return ""

    def _normalize_name(self, name):
        """
        Normalize college name for fallback matching.
        """

        if not name:
            return ""

        name = name.lower()

        for char in [".", ",", "-", "_", "(", ")"]:
            name = name.replace(char, " ")

        return " ".join(name.split())

    def _merge(self, existing, new):
        """
        Keep the existing college but fill missing
        information from the new result.
        """

        # Prefer the longer address/snippet.
        if len(new.get("address", "")) > len(
            existing.get("address", "")
        ):
            existing["address"] = new["address"]

        # Fill missing fields.
        for field in ["city", "phone", "state"]:
            if not existing.get(field) and new.get(field):
                existing[field] = new[field]

        # Keep an existing website unless missing.
        if not existing.get("website") and new.get("website"):
            existing["website"] = new["website"]

        if not existing.get("source_url") and new.get("source_url"):
            existing["source_url"] = new["source_url"]

        return existing

