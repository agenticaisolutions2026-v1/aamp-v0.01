import re


class WikipediaCollegeExtractor:
    """
    Extracts engineering college names from
    Wikipedia's Andhra Pradesh higher-education page.
    """

    def extract(self, text: str):
        colleges = []

        if not text:
            return colleges

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        for line in lines:

            # Wikipedia page text may contain numbered/table entries.
            # Keep only lines that look like college/institute names.
            if not self._looks_like_college(line):
                continue

            colleges.append({
                "name": line
            })

        return colleges

    def _looks_like_college(self, name: str):
        name_lower = name.lower()

        keywords = [
            "college",
            "institute",
            "university",
            "engineering",
            "technological",
            "technology",
        ]

        if not any(
            keyword in name_lower
            for keyword in keywords
        ):
            return False

        # Ignore obvious Wikipedia/navigation text.
        ignored = [
            "list of institutions",
            "higher education",
            "references",
            "external links",
            "see also",
            "contents",
        ]

        if any(
            value in name_lower
            for value in ignored
        ):
            return False

        return True