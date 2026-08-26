from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


class TavilyCollegeContactPageFinder:
    """
    Finds contact/about pages from an official college website.
    """

    KEYWORDS = [
        "contact",
        "contact-us",
        "contact us",
        "reach-us",
        "reach us",
        "get-in-touch",
        "get in touch",
    ]

    def find(self, html: str, base_url: str):
        if not html or not base_url:
            return []

        soup = BeautifulSoup(html, "html.parser")

        pages = []

        for link in soup.find_all("a", href=True):

            href = link.get("href", "").strip()

            if not href:
                continue

            absolute_url = urljoin(base_url, href)
            if "#" in absolute_url:
                absolute_url = absolute_url.split("#")[0]

            # Only keep links belonging to the same domain
            if not self._same_domain(
                absolute_url,
                base_url
            ):
                continue

            link_text = link.get_text(
                " ",
                strip=True
            ).lower()

            href_lower = href.lower()

            if any(
                keyword in link_text
                or keyword in href_lower
                for keyword in self.KEYWORDS
            ):
                if absolute_url not in pages:
                    pages.append(absolute_url)

        return pages

    def _same_domain(self, url1: str, url2: str):
        domain1 = urlparse(url1).netloc.lower()
        domain2 = urlparse(url2).netloc.lower()

        if domain1.startswith("www."):
            domain1 = domain1[4:]

        if domain2.startswith("www."):
            domain2 = domain2[4:]

        return domain1 == domain2