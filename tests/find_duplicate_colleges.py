import json
import re
from pathlib import Path
from urllib.parse import urlparse


INPUT_FILE = Path(
    "data/processed/college_master_402.json"
)

OUTPUT_FILE = Path(
    "data/processed/college_master_unique_with_website.json"
)


def normalize_text(value):
    if not value:
        return ""

    value = str(value).lower().strip()

    value = re.sub(
        r"[^a-z0-9\s]",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


def normalize_website(value):
    if not value:
        return ""

    value = str(value).strip()

    if not value:
        return ""

    if not value.startswith(("http://", "https://")):
        value = "https://" + value

    try:
        parsed = urlparse(value)

        domain = parsed.netloc.lower().strip()

        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    except Exception:
        return ""


def get_website(college):
    website = college.get("website")

    if isinstance(website, dict):
        return (
            website.get("value")
            or website.get("url")
            or ""
        )

    return website or ""


def main():

    print("=" * 70)
    print("COLLEGE MASTER CLEANUP")
    print("=" * 70)

    print(f"Input : {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print()

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    with INPUT_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:

        colleges = json.load(file)

    if not isinstance(colleges, list):
        raise ValueError(
            "Expected JSON to contain a list of colleges."
        )

    print(
        f"Original records : {len(colleges)}"
    )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    no_website = 0
    duplicate = 0
    unique = 0

    seen_names = set()
    seen_websites = set()
    seen_full_identity = set()

    output = []

    # --------------------------------------------------------
    # Process
    # --------------------------------------------------------

    for index, college in enumerate(
        colleges,
        start=1
    ):

        name = college.get("name") or college.get(
            "college_name"
        )

        city = college.get("city")
        state = college.get("state")

        website = get_website(college)

        # ----------------------------------------------------
        # Website required
        # ----------------------------------------------------

        domain = normalize_website(
            website
        )

        if not domain:

            no_website += 1

            print(
                f"[NO WEBSITE {index}] "
                f"{name}"
            )

            continue

        # ----------------------------------------------------
        # Normalize identity
        # ----------------------------------------------------

        normalized_name = normalize_text(
            name
        )

        normalized_city = normalize_text(
            city
        )

        normalized_state = normalize_text(
            state
        )

        identity = (
            normalized_name,
            domain,
            normalized_city,
            normalized_state,
        )

        # ----------------------------------------------------
        # Duplicate detection
        #
        # A record is duplicate if:
        #
        # 1. Exact identity already exists
        # OR
        # 2. Same website already exists
        #
        # Website is especially important because
        # different college names may refer to the
        # same institution.
        # ----------------------------------------------------

        if identity in seen_full_identity:

            duplicate += 1

            print(
                f"[DUPLICATE {index}] "
                f"{name}"
            )

            print(
                f"    Website: {domain}"
            )

            continue

        if domain in seen_websites:

            duplicate += 1

            print(
                f"[DUPLICATE WEBSITE {index}] "
                f"{name}"
            )

            print(
                f"    Website: {domain}"
            )

            continue

        # ----------------------------------------------------
        # Keep
        # ----------------------------------------------------

        seen_full_identity.add(
            identity
        )

        seen_websites.add(
            domain
        )

        if normalized_name:
            seen_names.add(
                normalized_name
            )

        output.append(
            college
        )

        unique += 1

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False
        )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("CLEANUP SUMMARY")
    print("=" * 70)

    print(
        f"Original records       : {len(colleges)}"
    )

    print(
        f"No website             : {no_website}"
    )

    print(
        f"Duplicates removed     : {duplicate}"
    )

    print(
        f"Unique colleges        : {unique}"
    )

    print(
        f"Output records         : {len(output)}"
    )

    print()
    print(
        f"Saved to: {OUTPUT_FILE}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()