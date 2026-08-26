class TavilyCollegeNormalizer:
    """
    Converts extracted Tavily college candidates
    into the standard AAMP college structure.
    """

    def normalize(
        self,
        colleges,
        state: str,
        source_url: str
    ):
        normalized = []

        for college in colleges:

            name = college.get("name", "").strip()

            if not name:
                continue

            normalized.append({
                "name": name,
                "website": "",
                "state": state,
                "city": self.extract_city(name),
                "address": "",
                "phone": None,
                "source_url": source_url,
                "careers360_rating": college.get(
                    "careers360_rating",
                    ""
                )
            })

        return normalized

    def extract_city(self, name: str):
        """
        Initial city extraction.

        Many source entries use:
            College Name, City
        """

        if "," not in name:
            return ""

        parts = [
            part.strip()
            for part in name.split(",")
            if part.strip()
        ]

        if len(parts) >= 2:
            return parts[-1]

        return ""