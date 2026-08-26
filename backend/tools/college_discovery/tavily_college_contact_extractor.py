import re
from bs4 import BeautifulSoup


class TavilyCollegeContactExtractor:
    """
    Extracts address, phone and email from college webpages.
    """

    def extract(self, html: str):
        if not html:
            return {
                "address": "",
                "phone": None,
                "email": None,
            }

        soup = BeautifulSoup(html, "html.parser")

        # Remove scripts/styles
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(
            " ",
            strip=True
        )

        email = self._extract_email(text)
        phone = self._extract_phone(text)
        address = self._extract_address(text)

        return {
            "address": address,
            "phone": phone,
            "email": email,
        }

    def _extract_email(self, text: str):
        match = re.search(
            r"[A-Za-z0-9._%+-]+"
            r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            text
        )

        return match.group(0) if match else None

    def _extract_phone(self, text: str):

        patterns = [
            r"\+91[\s-]?[6-9]\d{9}",
            r"\+91[\s-]?[6-9]\d{4}[\s-]?\d{5}",
            r"\b[6-9]\d{9}\b",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text
            )

            if match:
                return match.group(0).strip()

        return None

    def _extract_address(self, text: str):

        patterns = [
            r"Write to:\s*(.{20,300}?)(?=\s+Email:)",
            r"FIND US @\s*(.{20,300}?)(?=\s+CALL US @)",
            r"Address\s*[:\-]\s*(.{20,300})",
            r"Campus Address\s*[:\-]\s*(.{20,300})",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE | re.DOTALL
            )

            if match:

                address = match.group(1)

                address = " ".join(
                    address.split()
                )

                return address.strip()

        return ""