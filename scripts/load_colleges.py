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


def load_colleges():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "College data must be a list"
        )

    return data


def get_value(data, field):
    """
    Extract actual value from an enrichment evidence object.

    Example:
        {
            "value": "SRM University AP",
            "source": "https://srmap.edu.in"
        }

    returns:
        "SRM University AP"

    If the field is already a normal value,
    return it unchanged.
    """

    value = data.get(field)

    if isinstance(value, dict):
        return value.get("value")

    return value


def normalize_text(value):
    """
    Normalize text for duplicate comparison.
    """

    if value is None:
        return ""

    value = str(value).lower().strip()

    value = re.sub(
        r"[^a-z0-9\s]",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value


def normalize_domain(value):
    """
    Extract normalized domain from a website URL.

    Examples:

        https://www.example.edu/
        http://example.edu

    both become:

        example.edu
    """

    if not value:
        return ""

    value = str(value).strip().lower()

    if not value.startswith(
        ("http://", "https://")
    ):
        value = "https://" + value

    try:

        parsed = urlparse(value)

        domain = parsed.netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    except Exception:

        return ""


def make_name_location_key(
    name,
    city,
    state,
):
    """
    Create normalized identity key using:

        name + city + state
    """

    return (
        normalize_text(name),
        normalize_text(city),
        normalize_text(state),
    )


def main():

    colleges = load_colleges()

    print("=" * 80)
    print(
        "LOADING 71 ENRICHED COLLEGES INTO POSTGRESQL"
    )
    print("=" * 80)

    print(
        f"Input colleges: {len(colleges)}"
    )

    with Session(engine) as session:

        # --------------------------------------------------
        # Load existing colleges
        # --------------------------------------------------

        existing_colleges = (
            session.query(College)
            .all()
        )

        print(
            f"Existing colleges in DB: "
            f"{len(existing_colleges)}"
        )

        # --------------------------------------------------
        # Build duplicate indexes
        # --------------------------------------------------

        existing_domains = set()

        existing_name_location = set()

        for existing in existing_colleges:

            domain = normalize_domain(
                existing.website
            )

            if domain:
                existing_domains.add(
                    domain
                )

            key = make_name_location_key(
                existing.name,
                existing.city,
                existing.state,
            )

            existing_name_location.add(
                key
            )

        # --------------------------------------------------
        # Track duplicates inside current input
        # --------------------------------------------------

        input_domains = set()

        input_name_location = set()

        inserted = 0
        skipped_existing = 0
        skipped_duplicate_input = 0

        # --------------------------------------------------
        # Process colleges
        # --------------------------------------------------

        for index, college_data in enumerate(
            colleges,
            start=1,
        ):

            name = get_value(
                college_data,
                "name",
            )

            website = get_value(
                college_data,
                "website",
            )

            state = get_value(
                college_data,
                "state",
            )

            city = get_value(
                college_data,
                "city",
            )

            domain = normalize_domain(
                website
            )

            name_location_key = (
                make_name_location_key(
                    name,
                    city,
                    state,
                )
            )

            # --------------------------------------------------
            # Existing DB duplicate check
            # --------------------------------------------------

            if (
                domain
                and domain in existing_domains
            ):

                skipped_existing += 1

                print(
                    f"[SKIP DB {index}/{len(colleges)}] "
                    f"{name}"
                )

                print(
                    f"  Reason: website already exists "
                    f"({domain})"
                )

                continue

            if (
                name_location_key
                in existing_name_location
            ):

                skipped_existing += 1

                print(
                    f"[SKIP DB {index}/{len(colleges)}] "
                    f"{name}"
                )

                print(
                    "  Reason: "
                    "name + city + state already exists"
                )

                continue

            # --------------------------------------------------
            # Duplicate inside current 71-file
            # --------------------------------------------------

            if (
                domain
                and domain in input_domains
            ):

                skipped_duplicate_input += 1

                print(
                    f"[SKIP INPUT {index}/{len(colleges)}] "
                    f"{name}"
                )

                print(
                    f"  Reason: duplicate website "
                    f"in input file ({domain})"
                )

                continue

            if (
                name_location_key
                in input_name_location
            ):

                skipped_duplicate_input += 1

                print(
                    f"[SKIP INPUT {index}/{len(colleges)}] "
                    f"{name}"
                )

                print(
                    "  Reason: duplicate "
                    "name + city + state "
                    "in input file"
                )

                continue

            # --------------------------------------------------
            # Create College
            # --------------------------------------------------

            college = College(

                # ----------------------------------
                # Basic information
                # ----------------------------------

                name=name,

                website=website,

                state=state,

                city=city,

                address=get_value(
                    college_data,
                    "address",
                ),

                source_url=(
                    college_data.get(
                        "sources",
                        [None],
                    )[0]
                    if college_data.get("sources")
                    else None
                ),

                relevance_score=None,

                status=college_data.get(
                    "status",
                    "discovered",
                ),

                # ----------------------------------
                # Academic information
                # ----------------------------------

                departments=college_data.get(
                    "departments"
                ),

                programs=college_data.get(
                    "programs"
                ),

                ai_ml_related=college_data.get(
                    "ai_ml_related"
                ),

                generative_ai_related=college_data.get(
                    "generative_ai_related"
                ),

                agentic_ai_related=college_data.get(
                    "agentic_ai_related"
                ),

                # ----------------------------------
                # Contact information
                # ----------------------------------

                official_email=college_data.get(
                    "official_email"
                ),

                official_phone=college_data.get(
                    "official_phone"
                ),

                contact_role=college_data.get(
                    "contact_role"
                ),

                contact_form=college_data.get(
                    "contact_form"
                ),

                whatsapp=college_data.get(
                    "whatsapp"
                ),

                linkedin=college_data.get(
                    "linkedin"
                ),

                # ----------------------------------
                # Placement / training
                # ----------------------------------

                placement_page=college_data.get(
                    "placement_page"
                ),

                contact_page=college_data.get(
                    "contact_page"
                ),

                training=college_data.get(
                    "training"
                ),

                workshop_training_opportunity=(
                    college_data.get(
                        "workshop_training_opportunity"
                    )
                ),

                placement_available=college_data.get(
                    "placement_available"
                ),

                # ----------------------------------
                # Institutional information
                # ----------------------------------

                innovation=college_data.get(
                    "innovation"
                ),

                entrepreneurship=college_data.get(
                    "entrepreneurship"
                ),

                clubs_events=college_data.get(
                    "clubs_events"
                ),

                # ----------------------------------
                # Evidence / metadata
                # ----------------------------------

                sources=college_data.get(
                    "sources"
                ),

                missing_fields=college_data.get(
                    "missing_fields"
                ),

                errors=college_data.get(
                    "errors"
                ),
            )

            session.add(college)

            inserted += 1

            # Add to indexes immediately so
            # duplicates later in the same file
            # are detected.

            if domain:
                input_domains.add(domain)

            input_name_location.add(
                name_location_key
            )

            print(
                f"[INSERT {index}/{len(colleges)}] "
                f"{name}"
            )

        # --------------------------------------------------
        # Commit
        # --------------------------------------------------

        session.commit()

        # --------------------------------------------------
        # Final DB count
        # --------------------------------------------------

        final_count = (
            session.query(College).count()
        )

    # ------------------------------------------------------
    # Summary
    # ------------------------------------------------------

    print("\n" + "=" * 80)
    print("COLLEGE IMPORT COMPLETED")
    print("=" * 80)

    print(
        "Input colleges        :",
        len(colleges),
    )

    print(
        "Inserted              :",
        inserted,
    )

    print(
        "Skipped existing DB   :",
        skipped_existing,
    )

    print(
        "Skipped input duplicate:",
        skipped_duplicate_input,
    )

    print(
        "Final DB colleges     :",
        final_count,
    )

    print("=" * 80)


if __name__ == "__main__":
    main()