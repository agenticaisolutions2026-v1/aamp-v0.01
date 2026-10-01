import json
import logging
from pathlib import Path

from backend.agents.lead_qualification_agent import (
    LeadQualificationAgent,
)
from backend.agents.state import AgentState


logging.basicConfig(level=logging.INFO)


ENRICHED_FILE = Path(
    "data/processed/college_enriched_71.json"
)

SCORED_FILE = Path(
    "data/processed/college_scored_71.json"
)

OUTPUT_FILE = Path(
    "data/processed/college_qualified_71.json"
)


def load_json(file_path: Path):
    """Load JSON data from a file."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def qualify_college(
    agent: LeadQualificationAgent,
    college: dict,
    score_result: dict,
) -> AgentState:
    """Pass enriched college + score to the agent."""

    state = AgentState()

    state.user_query = (
        f"Qualify lead for "
        f"{college.get('name', '')}"
    )

    state.enriched_results = [college]
    state.scores = [score_result]

    return agent.execute(state)


def save_results(results: list):
    """Save qualification results."""

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


def get_college_name(college: dict) -> str:

    name = college.get(
        "name",
        "Unknown College",
    )

    if isinstance(name, dict):
        return name.get(
            "value",
            "Unknown College",
        )

    return name


def main():

    enriched_colleges = load_json(
        ENRICHED_FILE
    )

    scored_colleges = load_json(
        SCORED_FILE
    )

    if len(enriched_colleges) != len(
        scored_colleges
    ):
        raise ValueError(
            "Enriched and scored college counts "
            "do not match"
        )

    print("=" * 80)
    print(
        "LEAD QUALIFICATION TEST — 71 COLLEGES"
    )
    print("=" * 80)

    print(
        f"Enriched colleges: "
        f"{len(enriched_colleges)}"
    )

    print(
        f"Scored colleges  : "
        f"{len(scored_colleges)}"
    )

    agent = LeadQualificationAgent()

    results = []

    qualified = 0
    needs_review = 0
    low_priority = 0
    very_low = 0
    failed = 0

    for index, (
        college,
        score_result,
    ) in enumerate(
        zip(
            enriched_colleges,
            scored_colleges,
        ),
        start=1,
    ):

        college_name = get_college_name(
            college
        )

        print("\n" + "-" * 80)

        print(
            f"[{index}/{len(enriched_colleges)}] "
            f"{college_name}"
        )

        print(
            "College score :",
            score_result.get("score"),
        )

        print(
            "Priority      :",
            score_result.get("priority"),
        )

        priority = score_result.get("priority")

        if priority == "very_low":
            very_low += 1

        try:

            state = qualify_college(
                agent,
                college,
                score_result,
            )

            result = (
                getattr(
                    state,
                    "result",
                    {},
                )
                or {}
            )

            results.append(result)

            status = getattr(
                state,
                "status",
                "failed",
            )

            if status != "completed":

                failed += 1

                print(
                    "Status:",
                    status,
                )

                print(
                    "Error:",
                    getattr(
                        state,
                        "error",
                        "",
                    ),
                )

                continue

            qualification = result.get(
                "qualification"
            )

            if qualification == "qualified":
                qualified += 1

            elif qualification == "needs_review":
                needs_review += 1

            elif qualification == "low_priority":
                low_priority += 1

            print(
                "Contact role :",
                result.get(
                    "contact_role"
                ),
            )

            print(
                "Qualification:",
                qualification,
            )

            print(
                "Lead score   :",
                result.get(
                    "lead_score"
                ),
            )

            print(
                "Reason       :",
                result.get(
                    "reason"
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
                    "college_name": college_name,
                    "qualification": "failed",
                    "error": str(exc),
                }
            )

        # Save after every college
        save_results(results)

    print("\n" + "=" * 80)
    print(
        "71-COLLEGE LEAD QUALIFICATION COMPLETED"
    )
    print("=" * 80)

    print(
        "Processed     :",
        len(results),
    )

    print(
        "Qualified     :",
        qualified,
    )

    print(
        "Needs Review  :",
        needs_review,
    )

    print(
        "Low Priority  :",
        low_priority,
    )

    print(
        "Very Low Score:",
        very_low,
    )

    print(
        "Failed        :",
        failed,
    )

    print(
        "Output        :",
        OUTPUT_FILE,
    )


if __name__ == "__main__":
    main()