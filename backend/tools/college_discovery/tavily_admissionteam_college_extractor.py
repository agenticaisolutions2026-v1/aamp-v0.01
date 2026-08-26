class AdmissionTeamCollegeExtractor:
    """
    Extracts college names from the cleaned AdmissionTeam page text.

    AdmissionTeam structure:
        College Name
        Apply Now
        Boarding Facilities for
        ...
        Location
        ...
        Education Type
        ...

    Does not:
        - Fetch webpages
        - Normalize data
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

        # AdmissionTeam's AP page currently exposes
        # the college names in this section.
        start_marker = "Sort By :"

        if start_marker not in lines:
            return colleges

        start_index = lines.index(start_marker)

        # Stop when the detailed college records begin.
        detail_marker = "Shortlist"

        for line in lines[start_index + 1:]:

            if line == detail_marker:
                break

            if line in {
                "Top Results",
                "Popularity",
                "Rating",
                "5 star",
                "4 star",
                "3 star",
                "2 star",
                "1 star",
                "showing page - 1 Out of 1",
            }:
                continue

            if line:
                colleges.append({
                    "name": line
                })

        return colleges