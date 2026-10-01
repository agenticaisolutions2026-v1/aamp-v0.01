import json
import logging
from pathlib import Path

from backend.agents.college_scoring_agent import CollegeScoringAgent
from backend.agents.state import AgentState


# Setup logging
logging.basicConfig(level=logging.INFO)


INPUT_FILE = Path(
    "data/processed/college_enriched_71.json"
)

OUTPUT_FILE = Path(
    "data/processed/college_scored_71.json"
)


def load_enriched_colleges() -> list:
    """Load the already enriched 71 colleges."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Enriched college file not found: {INPUT_FILE}"
        )

    with INPUT_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "Enriched college data must be a list"
        )

    return data


def score_college(
    agent: CollegeScoringAgent,
    college: dict,
) -> AgentState:
    """Pass one enriched college to the scoring agent."""

    state = AgentState()

    state.user_query = (
        f"Score {college.get('name', '')}"
    )

    # Put enriched college into the new pipeline field
    state.enriched_results = [college]

    return agent.execute(state)


def save_results(results: list) -> None:
    """Save scoring results."""

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


def main():

    colleges = load_enriched_colleges()

    print("=" * 80)
    print("COLLEGE SCORING TEST — 71 COLLEGES")
    print("=" * 80)

    print(
        f"Loaded enriched colleges: {len(colleges)}"
    )

    agent = CollegeScoringAgent()

    results = []

    high = 0
    medium = 0
    low = 0
    very_low = 0
    failed = 0

    for index, college in enumerate(
        colleges,
        start=1,
    ):

        college_name = college.get(
            "name",
            "Unknown College",
        )

        # Handle enrichment name structure
        if isinstance(college_name, dict):
            college_name = college_name.get(
                "value",
                "Unknown College",
            )

        print("\n" + "-" * 80)
        print(
            f"[{index}/{len(colleges)}] "
            f"{college_name}"
        )

        try:

            state = score_college(
                agent,
                college,
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
                    "Status :", status
                )
                print(
                    "Error  :",
                    getattr(
                        state,
                        "error",
                        "",
                    ),
                )

                continue

            score = result.get(
                "score"
            )

            priority = result.get(
                "priority"
            )

            reasons = result.get(
                "reasons",
                [],
            )

            missing = result.get(
                "missing_information",
                [],
            )

            if priority == "high":
                high += 1

            elif priority == "medium":
                medium += 1

            elif priority == "low":
                low += 1

            elif priority == "very_low":
                very_low += 1

            print(
                "Score    :",
                score,
            )

            print(
                "Priority :",
                priority,
            )

            print(
                "Reasons:"
            )

            for reason in reasons:
                print(
                    f"  + {reason}"
                )

            if missing:

                print(
                    "Missing information:"
                )

                for item in missing:
                    print(
                        f"  - {item}"
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
                    "status": "failed",
                    "error": str(exc),
                }
            )

        # Save after every college
        save_results(results)

    print("\n" + "=" * 80)
    print("71-COLLEGE SCORING COMPLETED")
    print("=" * 80)

    print(
        "Processed  :",
        len(results),
    )

    print(
        "High       :",
        high,
    )

    print(
        "Medium     :",
        medium,
    )

    print(
        "Low        :",
        low,
    )

    print(
        "Very Low   :",
        very_low,
    )

    print(
        "Failed     :",
        failed,
    )

    print(
        "Output     :",
        OUTPUT_FILE,
    )


if __name__ == "__main__":
    main()