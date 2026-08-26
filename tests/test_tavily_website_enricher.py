from backend.tools.college_discovery.website_enricher import (
    WebsiteEnricher,
)


def main():
    enricher = WebsiteEnricher()

    result = enricher.find_relevant_pages(
        college_name="GITAM Institute of Technology",
        website="https://gitam.ac.in",
        max_results=10,
    )

    print("=" * 80)
    print("WEBSITE ENRICHER TEST")
    print("=" * 80)

    print("College:", result["college_name"])
    print("Website:", result["website"])
    print("Status:", result["status"])

    print("\nOfficial sources:")
    for url in result["sources"]:
        print(" -", url)

    print("\nPages by category:")

    for category, pages in result["pages"].items():

        print(
            f"\n[{category.upper()}] "
            f"{len(pages)} page(s)"
        )

        for page in pages:
            print(
                " -",
                page["title"],
                "->",
                page["url"],
            )

    print("\nIgnored non-official results:")

    for item in result["ignored_results"]:
        print(
            " -",
            item["url"],
        )


if __name__ == "__main__":
    main()