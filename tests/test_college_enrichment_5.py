import json
from pathlib import Path

from backend.agents.college_enrichment_agent import (
    CollegeEnrichmentAgent,
)
from backend.agents.state import AgentState


INPUT_FILE = Path(
    "college_master_402.json"
)

OUTPUT_FILE = Path(
    "college_enriched_test_5.json"
)

TEST_COUNT = 5


def load_colleges():
    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    colleges = []

    for college in data:

        website = (
            college.get("website")
            or ""
        ).strip()

        if website.startswith(
            ("http://", "https://")
        ):
            colleges.append(college)

        if len(colleges) == TEST_COUNT:
            break

    return colleges


def enrich_college(
    agent,
    college,
):
    state = AgentState()

    state.user_query = (
        f"Enrich {college.get('name', '')}"
    )

    state.result = {
        "name": college.get("name"),
        "website": college.get("website"),
        "state": college.get("state"),
        "city": college.get("city"),
        "address": college.get("address"),
        "source_url": college.get(
            "source_url"
        ),
    }

    return agent.execute(state)


def main():

    colleges = load_colleges()

    print("=" * 80)
    print("COLLEGE ENRICHMENT TEST — 5 COLLEGES")
    print("=" * 80)

    print(
        f"Selected colleges: {len(colleges)}"
    )

    agent = CollegeEnrichmentAgent()

    results = []

    completed = 0
    partial = 0
    failed = 0

    for index, college in enumerate(
        colleges,
        start=1,
    ):

        print("\n" + "-" * 80)

        print(
            f"[{index}/{len(colleges)}] "
            f"{college.get('name')}"
        )

        print(
            "Website:",
            college.get("website"),
        )

        try:

            state = enrich_college(
                agent,
                college,
            )

            result = state.result

            results.append(result)

            status = result.get(
                "status",
                "failed",
            )

            if status == "complete":
                completed += 1

            elif status == "partial":
                partial += 1

            else:
                failed += 1

            print(
                "Status:",
                status,
            )

            print(
                "Missing:",
                result.get(
                    "missing_fields",
                    [],
                ),
            )

        except Exception as exc:

            failed += 1

            print(
                "ERROR:",
                exc,
            )

            results.append(
                {
                    "name": college.get(
                        "name"
                    ),
                    "status": "failed",
                    "missing_fields": [],
                    "errors": [
                        str(exc)
                    ],
                }
            )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            results,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("\n" + "=" * 80)
    print("5-COLLEGE ENRICHMENT COMPLETED")
    print("=" * 80)

    print(
        "Processed       :",
        len(results),
    )

    print(
        "Completed       :",
        completed,
    )

    print(
        "Partial         :",
        partial,
    )

    print(
        "Failed          :",
        failed,
    )

    print(
        "Output          :",
        OUTPUT_FILE,
    )


if __name__ == "__main__":
    main()