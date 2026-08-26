import re


class TavilyContentCollegeExtractor:
    """
    Extracts college names from Tavily search-result content.

    Initial strategy:
        - Look for common college/institute/university names
        - Keep extraction conservative
        - Do not fetch webpages
        - Do not normalize
        - Do not deduplicate
    """

    def extract(self, content: str):
        colleges = []

        if not content:
            return colleges

        patterns = [
            r"\b[A-Z][A-Za-z&'.\-]*(?:\s+[A-Z][A-Za-z&'.\-]*)*"
            r"\s+(?:University|College|Institute|Institutes)"
            r"(?:\s+of\s+[A-Za-z&'.\-]+(?:\s+[A-Za-z&'.\-]+)*)?"
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)

            for match in matches:
                name = match.strip()

                if name and name not in colleges:
                    colleges.append(name)

        return [
            {"name": name}
            for name in colleges
        ]