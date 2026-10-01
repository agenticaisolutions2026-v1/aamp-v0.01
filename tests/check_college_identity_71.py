import json
import re
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from backend.database.connection import engine
from backend.models import College


INPUT_FILE = Path(
    "data/processed/college_enriched_71.json"
)


def normalize_text(value):
    if value is None:
        return ""

    if isinstance(value, dict):
        value = value.get("value", "")

    value = str(value).lower().strip()

    # Remove punctuation and extra spaces
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value


def normalize_website(value):
    if not value:
        return ""

    if isinstance(value, dict):
        value = value.get("value", "")

    value = str(value).strip().lower()

    if not value.startswith(("http://", "https://")):
        value = "https://" + value

    try:
        parsed = urlparse(value)
        domain = parsed.netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        return domain
    except Exception:
        return ""


def get_value(data, field):
    value = data.get(field)

    if isinstance(value, dict):
        return value.get("value")

    return value


def classify_college(input_college, existing_colleges):

    input_name = normalize_text(
        get_value(input_college, "name")
    )

    input_city = normalize_text(
        get_value(input_college, "city")
    )

    input_state = normalize_text(
        get_value(input_college, "state")
    )

    input_website = normalize_website(
        get_value(input_college, "website")
    )

    # --------------------------------------------------
    # 1. Exact website match
    # --------------------------------------------------

    if input_website:

        for existing in existing_colleges:

            existing_website = normalize_website(
                existing.website
            )

            if (
                existing_website
                and input_website == existing_website
            ):
                return (
                    "EXACT MATCH",
                    existing,
                    "same website",
                )

    # --------------------------------------------------
    # 2. Exact name + city + state
    # --------------------------------------------------

    for existing in existing_colleges:

        existing_name = normalize_text(
            existing.name
        )

        existing_city = normalize_text(
            existing.city
        )

        existing_state = normalize_text(
            existing.state
        )

        if (
            input_name
            and input_name == existing_name
            and input_city == existing_city
            and input_state == existing_state
        ):
            return (
                "EXACT MATCH",
                existing,
                "same name + city + state",
            )

    # --------------------------------------------------
    # 3. Same name, but location differs
    # --------------------------------------------------

    for existing in existing_colleges:

        existing_name = normalize_text(
            existing.name
        )

        if (
            input_name
            and input_name == existing_name
        ):

            return (
                "POSSIBLE MATCH",
                existing,
                "same name but location differs",
            )

    # --------------------------------------------------
    # 4. No match
    # --------------------------------------------------

    return (
        "NEW COLLEGE",
        None,
        "no matching website/name",
    )


def main():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"File not found: {INPUT_FILE}"
        )

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        input_colleges = json.load(file)

    with Session(engine) as session:

        existing_colleges = (
            session.query(College)
            .order_by(College.id)
            .all()
        )

    print("=" * 100)
    print("COLLEGE IDENTITY CHECK — 71 COLLEGES")
    print("=" * 100)

    print(
        f"Input colleges   : {len(input_colleges)}"
    )

    print(
        f"Existing colleges: {len(existing_colleges)}"
    )

    exact_matches = 0
    possible_matches = 0
    new_colleges = 0

    results = []

    for index, college in enumerate(
        input_colleges,
        start=1,
    ):

        name = get_value(
            college,
            "name",
        )

        website = get_value(
            college,
            "website",
        )

        city = get_value(
            college,
            "city",
        )

        state = get_value(
            college,
            "state",
        )

        status, existing, reason = (
            classify_college(
                college,
                existing_colleges,
            )
        )

        if status == "EXACT MATCH":
            exact_matches += 1

        elif status == "POSSIBLE MATCH":
            possible_matches += 1

        else:
            new_colleges += 1

        print("\n" + "-" * 100)

        print(
            f"[{index}/{len(input_colleges)}] "
            f"{name}"
        )

        print(
            f"Input location : {city}, {state}"
        )

        print(
            f"Input website  : {website}"
        )

        print(
            f"Result         : {status}"
        )

        print(
            f"Reason         : {reason}"
        )

        if existing:

            print(
                f"Existing DB ID : {existing.id}"
            )

            print(
                f"Existing name  : {existing.name}"
            )

            print(
                f"Existing city  : {existing.city}"
            )

            print(
                f"Existing state : {existing.state}"
            )

            print(
                f"Existing site  : {existing.website}"
            )

        results.append(
            {
                "input_name": name,
                "input_city": city,
                "input_state": state,
                "input_website": website,
                "status": status,
                "reason": reason,
                "existing_id": (
                    existing.id
                    if existing
                    else None
                ),
            }
        )

    print("\n" + "=" * 100)
    print("IDENTITY CHECK SUMMARY")
    print("=" * 100)

    print(
        "Input colleges   :",
        len(input_colleges),
    )

    print(
        "Exact matches    :",
        exact_matches,
    )

    print(
        "Possible matches :",
        possible_matches,
    )

    print(
        "New colleges     :",
        new_colleges,
    )

    print(
        "Expected final   :",
        len(existing_colleges)
        + new_colleges,
    )

    print("=" * 100)


if __name__ == "__main__":
    main()