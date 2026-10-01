import json
from pathlib import Path

from sqlalchemy.orm import Session

from backend.database.connection import engine
from backend.models import College


INPUT_FILE = Path(
    "data/processed/college_enriched_71.json"
)

TARGET_DB_ID = 82
SOURCE_INDEX = 69


def get_value(data, field):
    value = data.get(field)

    if isinstance(value, dict):
        return value.get("value")

    return value


def main():

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        colleges = json.load(file)

    if len(colleges) < SOURCE_INDEX:
        raise ValueError(
            f"Input file contains only {len(colleges)} "
            f"records; cannot access #{SOURCE_INDEX}."
        )

    source = colleges[SOURCE_INDEX - 1]

    print("=" * 80)
    print("REPLACE COLLEGE DATA")
    print("=" * 80)

    print(
        "Source #69:",
        get_value(source, "name"),
    )

    print(
        "Source website:",
        get_value(source, "website"),
    )

    print(
        "Source city:",
        get_value(source, "city"),
    )

    with Session(engine) as session:

        college = (
            session.query(College)
            .filter(
                College.id == TARGET_DB_ID
            )
            .one_or_none()
        )

        if college is None:
            raise ValueError(
                f"College ID {TARGET_DB_ID} "
                "was not found."
            )

        print(
            "\nCurrent DB record:"
        )

        print(
            "ID:",
            college.id,
        )

        print(
            "Name:",
            college.name,
        )

        print(
            "Website:",
            college.website,
        )

        print(
            "City:",
            college.city,
        )

        # ------------------------------------------
        # Replace ALL college fields
        # ------------------------------------------

        college.name = get_value(
            source,
            "name",
        )

        college.website = get_value(
            source,
            "website",
        )

        college.state = get_value(
            source,
            "state",
        )

        college.city = get_value(
            source,
            "city",
        )

        college.address = get_value(
            source,
            "address",
        )

        college.source_url = (
            source.get(
                "sources",
                [None],
            )[0]
            if source.get("sources")
            else None
        )

        college.relevance_score = None

        college.status = source.get(
            "status",
            "discovered",
        )

        college.departments = source.get(
            "departments"
        )

        college.programs = source.get(
            "programs"
        )

        college.ai_ml_related = source.get(
            "ai_ml_related"
        )

        college.generative_ai_related = (
            source.get(
                "generative_ai_related"
            )
        )

        college.agentic_ai_related = (
            source.get(
                "agentic_ai_related"
            )
        )

        college.official_email = (
            source.get(
                "official_email"
            )
        )

        college.official_phone = (
            source.get(
                "official_phone"
            )
        )

        college.contact_role = (
            source.get(
                "contact_role"
            )
        )

        college.contact_form = (
            source.get(
                "contact_form"
            )
        )

        college.whatsapp = source.get(
            "whatsapp"
        )

        college.linkedin = source.get(
            "linkedin"
        )

        college.placement_page = (
            source.get(
                "placement_page"
            )
        )

        college.contact_page = (
            source.get(
                "contact_page"
            )
        )

        college.training = source.get(
            "training"
        )

        college.workshop_training_opportunity = (
            source.get(
                "workshop_training_opportunity"
            )
        )

        college.placement_available = (
            source.get(
                "placement_available"
            )
        )

        college.innovation = source.get(
            "innovation"
        )

        college.entrepreneurship = source.get(
            "entrepreneurship"
        )

        college.clubs_events = source.get(
            "clubs_events"
        )

        college.sources = source.get(
            "sources"
        )

        college.missing_fields = source.get(
            "missing_fields"
        )

        college.errors = source.get(
            "errors"
        )

        session.commit()

        session.refresh(college)

        print(
            "\nUpdated DB record:"
        )

        print(
            "ID:",
            college.id,
        )

        print(
            "Name:",
            college.name,
        )

        print(
            "Website:",
            college.website,
        )

        print(
            "State:",
            college.state,
        )

        print(
            "City:",
            college.city,
        )

        print(
            "Email:",
            college.official_email,
        )

        print(
            "Phone:",
            college.official_phone,
        )

    print("\n" + "=" * 80)
    print("REPLACEMENT COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()