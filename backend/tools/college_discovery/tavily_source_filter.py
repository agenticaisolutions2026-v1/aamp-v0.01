class TavilySourceFilter:
    """
    Filters Tavily search results for useful college-discovery sources.

    Responsibility:
        - Remove irrelevant sources
        - Keep potentially useful college-list sources
        - Do not extract college records
    """

    EXCLUDED_DOMAINS = {
        "youtube.com",
        "www.youtube.com",
        "scribd.com",
        "www.scribd.com",
    }

    def filter(self, results):
        sources = []

        for result in results:
            url = result.get("url", "")
            title = result.get("title", "")
            content = result.get("content", "")

            if not url:
                continue

            # Remove unwanted domains
            if any(
                domain in url.lower()
                for domain in self.EXCLUDED_DOMAINS
            ):
                continue

            text = f"{title} {content}".lower()

            # Keep relevant college/engineering sources
            if (
                "college" not in text
                and "engineering" not in text
            ):
                continue

            sources.append(result)

        return sources