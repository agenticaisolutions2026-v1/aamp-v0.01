import re


class Normalizer:
    """
    Converts raw SerpAPI results into a consistent college structure.
    """

    def normalize(self, raw_results):
        colleges = []

        places = raw_results.get("local_results", {}).get("places", [])

        for place in places:
            name = place.get("title", "").strip()

            if not name:
                continue

            address = place.get("address", "").strip()

            website = (
                place.get("links", {}).get("website", "")
                or ""
            ).strip()

            phone = place.get("phone")

            college = {
                "name": name,
                "website": website,
                "state": self.extract_state_from_address(address),
                "city": self.extract_city_from_address(address),
                "address": address,
                "phone": phone,
                "source_url": website or None
            }

            colleges.append(college)

        return colleges


    def extract_state_from_address(self, address):
        if "Andhra Pradesh" in address:
            return "Andhra Pradesh"

        if "Telangana" in address:
            return "Telangana"

        return ""


    def extract_city_from_address(self, address):
        if not address:
            return ""

        parts = [
            part.strip()
            for part in address.split(",")
            if part.strip()
        ]

        if len(parts) >= 2:
            return parts[0]

        return ""

    def is_list_page(self, title, link):
        """
        Identify search results that represent a list/ranking/category
        rather than an individual college.
        """

        text = f"{title} {link}".lower()

        patterns = [
            "list of",
            "colleges in",
            "top engineering colleges",
            "best engineering colleges",
            "engineering colleges in",
            "category:",
            "category/",
            "rankings",
            "ranking",
            "colleges/"
        ]

        return any(pattern in text for pattern in patterns)

    def extract_state(self, item):
        """
        Extract state from the search result.
        """

        text = " ".join([
            item.get("title", ""),
            item.get("snippet", ""),
            item.get("link", "")
        ]).lower()

        if "telangana" in text and "andhra pradesh" not in text:
            return "Telangana"

        if "andhra pradesh" in text:
            return "Andhra Pradesh"

        return ""

    def extract_city(self, item):
        """
        Try to extract a city from the search result.
        """

        text = " ".join([
            item.get("title", ""),
            item.get("snippet", "")
        ])

        match = re.search(
            r"located in ([A-Za-z\s]+)",
            text,
            re.IGNORECASE
        )

        if match:
            return match.group(1).strip()

        return ""

    def extract_phone(self, item):
        """
        Extract an Indian phone number when available.
        """

        text = " ".join([
            item.get("title", ""),
            item.get("snippet", "")
        ])

        match = re.search(
            r"(?:\+91[\s-]?)?[6-9]\d{9}",
            text
        )

        return match.group(0) if match else None




