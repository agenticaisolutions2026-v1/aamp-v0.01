import re


class CollegeExtractor:
    """
    Extracts college candidates from cleaned webpage text.

    Initial responsibility:
        - Detect numbered college-list entries
        - Extract the college name
        - Keep extraction simple

    Does not:
        - Call Tavily
        - Fetch webpages
        - Deduplicate colleges
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

        for i, line in enumerate(lines):

            if not line.isdigit():
                continue

            number = int(line)

            # The college name is normally the next line
            if i + 1 >= len(lines):
                continue

            name = lines[i + 1].strip()

            if not name:
                continue

            colleges.append({
                "name": name,
                "source_number": number
            })

        return colleges