import re


class Careers360CollegeExtractor:
    """
    Extracts college names from the Careers360 ranking section.

    Targets:
        Top 10 Engineering Colleges in Andhra Pradesh
        With Careers360 Ranking 2026

    Does not:
        - Fetch webpages
        - Call Tavily
        - Normalize
        - Deduplicate
        - Save to database
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

        start_marker = (
            "Top 10 Engineering Colleges in Andhra Pradesh "
            "With Careers360 Ranking 2026"
        )

        try:
            start_index = lines.index(start_marker)
        except ValueError:
            return colleges

        # Find the next relevant section.
        end_index = len(lines)

        for i in range(start_index + 1, len(lines)):
            if lines[i].startswith("Top 5 Engineering Colleges"):
                end_index = i
                break

        section = lines[start_index + 1:end_index]

        # Find the table header.
        try:
            header_index = section.index("College Name")
        except ValueError:
            return colleges

        section = section[header_index + 2:]

        i = 0

        while i < len(section) - 1:

            college_name = section[i]
            rating = section[i + 1]

            # Careers360 ratings seen on this page.
            if re.fullmatch(r"A{2,4}\+?|_", rating):
                colleges.append({
                    "name": college_name,
                    "careers360_rating": rating
                })

                i += 2
            else:
                i += 1

        return colleges

    