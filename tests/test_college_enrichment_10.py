import json
import logging
from pathlib import Path

from backend.agents.college_enrichment_agent import CollegeEnrichmentAgent
from backend.agents.state import AgentState


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(level=logging.INFO)


# ============================================================
# FILES
# ============================================================

INPUT_FILE = Path(
    "data/processed/new_colleges_80.json"
)

OUTPUT_FILE = Path(
    "data/processed/new_colleges_enriched_80.json"
)


# ============================================================
# LOAD COLLEGES
# ============================================================

def load_colleges() -> list:
    """
    Load all colleges from the 53-college input file.
    """

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    with INPUT_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "Input JSON must contain a list of colleges."
        )

    return data


# ============================================================
# ENRICH ONE COLLEGE
# ============================================================

def enrich_college(
    agent: CollegeEnrichmentAgent,
    college: dict,
) -> AgentState:
    """
    Initialize AgentState and execute CollegeEnrichmentAgent.
    """

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
        "source_url": college.get("source_url"),
    }

    return agent.execute(state)


# ============================================================
# SAVE RESULTS
# ============================================================

def save_incremental_results(
    results: list,
) -> None:
    """
    Save progress after every college.

    This protects the completed results if Tavily/API
    processing is interrupted.
    """

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
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


# ============================================================
# MAIN
# ============================================================

def main():

    colleges = load_colleges()

    print("=" * 80)
    print("COLLEGE ENRICHMENT — 53 COLLEGES")
    print("=" * 80)

    print(
        f"Input file : {INPUT_FILE}"
    )

    print(
        f"Loaded colleges: {len(colleges)}"
    )

    print(
        f"Output file: {OUTPUT_FILE}"
    )

    print("=" * 80)


    agent = CollegeEnrichmentAgent()

    results = []

    completed = 0
    partial = 0
    failed = 0


    # ========================================================
    # PROCESS COLLEGES
    # ========================================================

    for index, college in enumerate(
        colleges,
        start=1,
    ):

        print(
            "\n"
            + "-" * 80
        )

        print(
            f"[{index}/{len(colleges)}] "
            f"{college.get('name')}"
        )

        print(
            "Website:",
            college.get("website")
        )


        try:

            state = enrich_college(
                agent,
                college,
            )

            result = (
                getattr(
                    state,
                    "result",
                    {}
                )
                or {}
            )

            results.append(result)


            # ----------------------------------------------
            # Count status
            # ----------------------------------------------

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
                "Status :",
                status
            )

            print(
                "Missing:",
                result.get(
                    "missing_fields",
                    []
                )
            )


        except Exception as exc:

            failed += 1

            print(
                "ERROR  :",
                exc
            )


            results.append(
                {
                    "name": college.get(
                        "name"
                    ),

                    "website": college.get(
                        "website"
                    ),

                    "state": college.get(
                        "state"
                    ),

                    "city": college.get(
                        "city"
                    ),

                    "status": "failed",

                    "missing_fields": [
                        "execution_error"
                    ],

                    "errors": [
                        str(exc)
                    ],
                }
            )


        # ----------------------------------------------
        # Save after every college
        # ----------------------------------------------

        save_incremental_results(
            results
        )


    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print(
        "\n"
        + "=" * 80
    )

    print(
        "53-COLLEGE ENRICHMENT COMPLETED"
    )

    print(
        "=" * 80
    )

    print(
        "Processed :",
        len(results)
    )

    print(
        "Completed :",
        completed
    )

    print(
        "Partial   :",
        partial
    )

    print(
        "Failed    :",
        failed
    )

    print(
        "Output    :",
        OUTPUT_FILE
    )

    print(
        "=" * 80
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()