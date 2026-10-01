import json
import re
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.connection import engine
from backend.models import College, Lead


# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = Path(
    "data/processed/college_qualified_71.json"
)


# ============================================================
# HELPERS
# ============================================================

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


def normalize_domain(url):
    if not url:
        return ""

    try:
        url = str(url).strip()

        if not url.startswith(
            ("http://", "https://")
        ):
            url = "https://" + url

        domain = urlparse(url).netloc.lower().strip()

        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    except Exception:
        return ""


def get_priority(qualification):

    if qualification == "qualified":
        return "high"

    if qualification == "needs_review":
        return "medium"

    return "low"


# ============================================================
# LOAD JSON
# ============================================================

def load_qualified_leads():

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
            "Expected JSON file to contain a list."
        )

    return data


# ============================================================
# BUILD DATABASE INDEX
# ============================================================

def build_college_indexes(session):

    colleges = session.scalars(
        select(College)
    ).all()

    by_identity = {}
    by_name = {}
    by_domain = {}

    for college in colleges:

        name = normalize_text(
            college.name
        )

        city = normalize_text(
            college.city
        )

        state = normalize_text(
            college.state
        )

        identity = (
            name,
            city,
            state
        )

        by_identity.setdefault(
            identity,
            []
        ).append(college)

        if name:
            by_name.setdefault(
                name,
                []
            ).append(college)

        website = college.website

        if isinstance(website, dict):
            website = website.get("value")

        domain = normalize_domain(
            website
        )

        if domain:
            by_domain.setdefault(
                domain,
                []
            ).append(college)

    return {
        "identity": by_identity,
        "name": by_name,
        "domain": by_domain,
    }


# ============================================================
# FIND COLLEGE
# ============================================================

def find_college(
    record,
    indexes
):

    college_name = (
        record.get("college_name")
        or record.get("name")
        or ""
    )

    name = normalize_text(
        college_name
    )

    city = normalize_text(
        record.get("city")
    )

    state = normalize_text(
        record.get("state")
    )

    # --------------------------------------------------------
    # 1. Exact name + city + state
    # --------------------------------------------------------

    identity = (
        name,
        city,
        state
    )

    matches = indexes["identity"].get(
        identity,
        []
    )

    if len(matches) == 1:
        return matches[0], "name+city+state"

    # --------------------------------------------------------
    # 2. Exact name
    # --------------------------------------------------------

    matches = indexes["name"].get(
        name,
        []
    )

    if len(matches) == 1:
        return matches[0], "name"

    if len(matches) > 1:
        return None, "ambiguous-name"

    return None, "not-found"


# ============================================================
# MAIN
# ============================================================

def main():

    records = load_qualified_leads()

    print("=" * 70)
    print("LEAD IMPORT")
    print("=" * 70)

    print(
        f"Input qualified records : {len(records)}"
    )

    inserted = 0
    skipped_existing = 0
    skipped_duplicate = 0
    not_found = 0
    ambiguous = 0
    failed = 0

    processed_college_ids = set()

    with Session(engine) as session:

        indexes = build_college_indexes(
            session
        )

        db_college_count = len(
            session.scalars(
                select(College)
            ).all()
        )

        existing_lead_count = len(
            session.scalars(
                select(Lead)
            ).all()
        )

        print(
            f"Database colleges       : "
            f"{db_college_count}"
        )

        print(
            f"Existing leads          : "
            f"{existing_lead_count}"
        )

        print("-" * 70)

        # ====================================================
        # PROCESS RECORDS
        # ====================================================

        for index, record in enumerate(
            records,
            start=1
        ):

            college_name = (
                record.get("college_name")
                or "UNKNOWN"
            )

            try:

                # --------------------------------------------
                # Find college
                # --------------------------------------------

                college, match_type = find_college(
                    record,
                    indexes
                )

                if college is None:

                    if match_type == "ambiguous-name":

                        ambiguous += 1

                        print(
                            f"[AMBIGUOUS "
                            f"{index}/{len(records)}] "
                            f"{college_name}"
                        )

                    else:

                        not_found += 1

                        print(
                            f"[NOT FOUND "
                            f"{index}/{len(records)}] "
                            f"{college_name}"
                        )

                    continue

                # --------------------------------------------
                # Duplicate in current JSON
                # --------------------------------------------

                if college.id in processed_college_ids:

                    skipped_duplicate += 1

                    print(
                        f"[SKIP DUPLICATE "
                        f"{index}/{len(records)}] "
                        f"{college_name}"
                    )

                    print(
                        f"    College ID : "
                        f"{college.id}"
                    )

                    continue

                # --------------------------------------------
                # Existing Lead?
                # --------------------------------------------

                existing_lead = session.scalar(
                    select(Lead).where(
                        Lead.college_id == college.id
                    )
                )

                if existing_lead:

                    skipped_existing += 1

                    processed_college_ids.add(
                        college.id
                    )

                    print(
                        f"[SKIP EXISTING LEAD "
                        f"{index}/{len(records)}] "
                        f"{college_name}"
                    )

                    print(
                        f"    College ID : "
                        f"{college.id}"
                    )

                    print(
                        f"    Lead ID    : "
                        f"{existing_lead.id}"
                    )

                    continue

                # --------------------------------------------
                # Extract lead data
                # --------------------------------------------

                qualification = (
                    record.get(
                        "qualification"
                    )
                    or ""
                ).strip().lower()

                lead_score = record.get(
                    "lead_score"
                )

                reason = record.get(
                    "reason"
                )

                contact_role = record.get(
                    "contact_role"
                )

                # --------------------------------------------
                # Validate lead_score
                # --------------------------------------------

                if lead_score is None:

                    failed += 1

                    print(
                        f"[FAILED "
                        f"{index}/{len(records)}] "
                        f"{college_name}"
                    )

                    print(
                        "    Reason: "
                        "lead_score is missing"
                    )

                    continue

                # --------------------------------------------
                # Create Lead
                # --------------------------------------------

                priority = get_priority(
                    qualification
                )

                lead = Lead(
                    college_id=college.id,
                    contact_role=contact_role,
                    qualification=qualification,
                    lead_score=lead_score,
                    priority=priority,
                    reason=reason,
                )

                session.add(lead)

                # Force INSERT now.
                # This makes any DB error belong
                # specifically to this record.
                session.flush()

                processed_college_ids.add(
                    college.id
                )

                inserted += 1

                print(
                    f"[INSERT "
                    f"{index}/{len(records)}] "
                    f"{college_name}"
                )

                print(
                    f"    College ID   : "
                    f"{college.id}"
                )

                print(
                    f"    Lead Score   : "
                    f"{lead_score}"
                )

                print(
                    f"    Qualification: "
                    f"{qualification}"
                )

                print(
                    f"    Priority     : "
                    f"{priority}"
                )

            except Exception as exc:

                # --------------------------------------------
                # IMPORTANT:
                # Roll back only this failed record
                # so later records can continue.
                # --------------------------------------------

                session.rollback()

                failed += 1

                print(
                    f"[FAILED "
                    f"{index}/{len(records)}] "
                    f"{college_name}"
                )

                print(
                    f"    Error: {exc}"
                )

                # Rebuild indexes after rollback
                indexes = build_college_indexes(
                    session
                )

                continue

        # ====================================================
        # COMMIT SUCCESSFUL INSERTS
        # ====================================================

        session.commit()

        # ====================================================
        # FINAL COUNTS
        # ====================================================

        final_college_count = len(
            session.scalars(
                select(College)
            ).all()
        )

        final_lead_count = len(
            session.scalars(
                select(Lead)
            ).all()
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 70)
    print("LEAD IMPORT SUMMARY")
    print("=" * 70)

    print(
        f"Input records             : {len(records)}"
    )

    print(
        f"Inserted                  : {inserted}"
    )

    print(
        f"Skipped existing Lead     : "
        f"{skipped_existing}"
    )

    print(
        f"Skipped duplicate input   : "
        f"{skipped_duplicate}"
    )

    print(
        f"College not found         : "
        f"{not_found}"
    )

    print(
        f"Ambiguous                 : "
        f"{ambiguous}"
    )

    print(
        f"Failed                    : "
        f"{failed}"
    )

    print(
        f"Final colleges            : "
        f"{final_college_count}"
    )

    print(
        f"Final leads               : "
        f"{final_lead_count}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()