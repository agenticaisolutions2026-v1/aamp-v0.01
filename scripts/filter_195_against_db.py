import json
import re
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.connection import engine
from backend.models import College


# =========================================================
# FILES
# =========================================================

INPUT_FILE = Path(
    "data/processed/college_master_unique_195.json"
)

OUTPUT_FILE = Path(
    "data/processed/college_master_new_from_163.json"
)


# =========================================================
# NORMALIZATION
# =========================================================

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


def normalize_phone(value):
    if not value:
        return ""

    return re.sub(
        r"\D",
        "",
        str(value)
    )


def get_website(college):
    website = college.get("website")

    if isinstance(website, dict):
        return (
            website.get("value")
            or website.get("url")
            or ""
        )

    return website or ""


def get_phone(college):
    return (
        college.get("phone")
        or college.get("phone_number")
        or college.get("contact_phone")
        or ""
    )


# =========================================================
# DB COLLEGE IDENTITY
# =========================================================

def build_db_identity_sets():

    with Session(engine) as session:

        colleges = session.scalars(
            select(College)
        ).all()

    print(
        f"Existing colleges in DB : {len(colleges)}"
    )

    existing_names = set()
    existing_name_city = set()
    existing_websites = set()
    existing_phones = set()

    for college in colleges:

        name = normalize_text(
            getattr(college, "name", "")
        )

        city = normalize_text(
            getattr(college, "city", "")
        )

        website = normalize_website(
            getattr(college, "website", "")
        )

        phone = normalize_phone(
            getattr(college, "phone", "")
        )

        if name:
            existing_names.add(name)

        if name or city:
            existing_name_city.add(
                (name, city)
            )

        if website:
            existing_websites.add(website)

        if phone:
            existing_phones.add(phone)

    return (
        existing_names,
        existing_name_city,
        existing_websites,
        existing_phones,
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 70)
    print("FILTER 195 COLLEGES AGAINST DATABASE")
    print("=" * 70)

    print(
        f"Input  : {INPUT_FILE}"
    )

    print(
        f"Output : {OUTPUT_FILE}"
    )

    print()

    # -----------------------------------------------------
    # Check input
    # -----------------------------------------------------

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    # -----------------------------------------------------
    # Load 195 colleges
    # -----------------------------------------------------

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
        f"Input colleges          : {len(colleges)}"
    )

    print()

    # -----------------------------------------------------
    # Load existing DB identities
    # -----------------------------------------------------

    (
        existing_names,
        existing_name_city,
        existing_websites,
        existing_phones,
    ) = build_db_identity_sets()

    print()

    # -----------------------------------------------------
    # Statistics
    # -----------------------------------------------------

    duplicate = 0
    new_colleges = 0

    duplicate_website = 0
    duplicate_phone = 0
    duplicate_name_city = 0

    output = []

    # -----------------------------------------------------
    # Compare 195 against DB
    # -----------------------------------------------------

    for index, college in enumerate(
        colleges,
        start=1
    ):

        name = (
            college.get("name")
            or college.get("college_name")
            or ""
        )

        city = (
            college.get("city")
            or ""
        )

        website = get_website(
            college
        )

        phone = get_phone(
            college
        )

        # -------------------------------------------------
        # Normalize
        # -------------------------------------------------

        normalized_name = normalize_text(
            name
        )

        normalized_city = normalize_text(
            city
        )

        domain = normalize_website(
            website
        )

        normalized_phone = normalize_phone(
            phone
        )

        # -------------------------------------------------
        # Duplicate detection
        #
        # Same website
        # OR same phone
        # OR same college name + city
        # -------------------------------------------------

        is_duplicate = False

        if (
            domain
            and domain in existing_websites
        ):

            is_duplicate = True
            duplicate_website += 1

            print(
                f"[DUPLICATE WEBSITE {index}] "
                f"{name}"
            )

            print(
                f"    City    : {city}"
            )

            print(
                f"    Website : {domain}"
            )

        elif (
            normalized_phone
            and normalized_phone in existing_phones
        ):

            is_duplicate = True
            duplicate_phone += 1

            print(
                f"[DUPLICATE PHONE {index}] "
                f"{name}"
            )

            print(
                f"    City  : {city}"
            )

            print(
                f"    Phone : {normalized_phone}"
            )

        elif (
            normalized_name
            and (
                normalized_name,
                normalized_city,
            ) in existing_name_city
        ):

            is_duplicate = True
            duplicate_name_city += 1

            print(
                f"[DUPLICATE NAME + CITY {index}] "
                f"{name}"
            )

            print(
                f"    City: {city}"
            )

        # -------------------------------------------------
        # Skip duplicate
        # -------------------------------------------------

        if is_duplicate:

            duplicate += 1
            continue

        # -------------------------------------------------
        # New college
        # -------------------------------------------------

        output.append(
            college
        )

        new_colleges += 1

    # -----------------------------------------------------
    # Save new colleges
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    print()
    print("=" * 70)
    print("FILTER SUMMARY")
    print("=" * 70)

    print(
        f"Input colleges          : {len(colleges)}"
    )

    print(
        print(f"Existing colleges in DB : {len(colleges)}")
    )

    print(
        f"Duplicates found        : {duplicate}"
    )

    print(
        f"  - Website duplicates  : "
        f"{duplicate_website}"
    )

    print(
        f"  - Phone duplicates    : "
        f"{duplicate_phone}"
    )

    print(
        f"  - Name + City         : "
        f"{duplicate_name_city}"
    )

    print(
        f"New colleges            : {new_colleges}"
    )

    print(
        f"Output records          : {len(output)}"
    )

    print()
    print(
        f"Saved to: {OUTPUT_FILE}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()