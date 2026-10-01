from backend.services.college_search_service import (
    CollegeSearchService,
)


def main():

    service = CollegeSearchService()

    print("=" * 70)
    print("COLLEGE SEARCH SERVICE TEST")
    print("=" * 70)

    results = service.search_colleges(
        state="Andhra Pradesh"
    )

    print()
    print("Total colleges:", len(results))
    print()

    for item in results:

        college = item["college"]
        lead = item["lead"]

        print(
            f"{college['name']:<60}"
        )

        if lead:
            print(
                f"  Score: {lead['lead_score']} | "
                f"Priority: {lead['priority']} | "
                f"Qualification: {lead['qualification']}"
            )
        else:
            print("  Lead: None")

        print()


if __name__ == "__main__":
    main()