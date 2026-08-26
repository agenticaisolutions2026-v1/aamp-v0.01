import json


BLOCKED_DOMAINS = [
    "justdial.com",
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "youtube.com",
    "wikipedia.org",
    "careers360.com",
    "shiksha.com",
    "collegedunia.com",
    "collegedekho.com",
    "zoominfo.com",
]


def has_value(value):
    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    return True


def is_valid_website(website):
    if not has_value(website):
        return False

    website_lower = website.lower()

    return not any(
        domain in website_lower
        for domain in BLOCKED_DOMAINS
    )


def classify():

    with open(
        "enriched_colleges.json",
        "r",
        encoding="utf-8"
    ) as f:

        colleges = json.load(f)

    complete = []
    missing_fields = []
    invalid_website = []

    field_counts = {
        "website": 0,
        "address": 0,
        "phone": 0,
        "email": 0,
    }

    for college in colleges:

        website = college.get("website")
        address = college.get("address")
        phone = college.get("phone")
        email = college.get("email")

        website_ok = is_valid_website(website)
        address_ok = has_value(address)
        phone_ok = has_value(phone)
        email_ok = has_value(email)

        # --------------------------------------------
        # Field counts
        # --------------------------------------------

        if website_ok:
            field_counts["website"] += 1

        if address_ok:
            field_counts["address"] += 1

        if phone_ok:
            field_counts["phone"] += 1

        if email_ok:
            field_counts["email"] += 1

        # --------------------------------------------
        # Invalid website
        # --------------------------------------------

        if not website_ok:

            invalid_website.append(college)

            continue

        # --------------------------------------------
        # Completely complete record
        # --------------------------------------------

        if (
            address_ok
            and phone_ok
            and email_ok
        ):

            complete.append(college)

        else:

            missing = []

            if not address_ok:
                missing.append("address")

            if not phone_ok:
                missing.append("phone")

            if not email_ok:
                missing.append("email")

            record = dict(college)

            record["missing_fields"] = missing

            missing_fields.append(record)

    # --------------------------------------------
    # Save complete colleges
    # --------------------------------------------

    with open(
        "complete_colleges.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            complete,
            f,
            indent=2,
            ensure_ascii=False
        )

    # --------------------------------------------
    # Save colleges with missing fields
    # --------------------------------------------

    with open(
        "missing_fields_colleges.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            missing_fields,
            f,
            indent=2,
            ensure_ascii=False
        )

    # --------------------------------------------
    # Save invalid websites
    # --------------------------------------------

    with open(
        "invalid_website_colleges.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            invalid_website,
            f,
            indent=2,
            ensure_ascii=False
        )

    # --------------------------------------------
    # Summary
    # --------------------------------------------

    print("\n========================================")
    print("FIELD-LEVEL COLLEGE ANALYSIS")
    print("========================================")

    print("Total colleges:", len(colleges))

    print("\nFIELD AVAILABILITY")
    print("----------------------------------------")

    print(
        "Valid website:",
        field_counts["website"]
    )

    print(
        "Address:",
        field_counts["address"]
    )

    print(
        "Phone:",
        field_counts["phone"]
    )

    print(
        "Email:",
        field_counts["email"]
    )

    print("\nRECORD CLASSIFICATION")
    print("----------------------------------------")

    print(
        "Complete:",
        len(complete)
    )

    print(
        "Missing one or more fields:",
        len(missing_fields)
    )

    print(
        "Invalid/missing website:",
        len(invalid_website)
    )

    print(
        "Check:",
        len(complete)
        + len(missing_fields)
        + len(invalid_website)
    )

    # --------------------------------------------
    # Missing-field combinations
    # --------------------------------------------

    combinations = {}

    for college in missing_fields:

        fields = tuple(
            college["missing_fields"]
        )

        combinations[fields] = (
            combinations.get(fields, 0) + 1
        )

    print("\nMISSING FIELD COMBINATIONS")
    print("----------------------------------------")

    for fields, count in sorted(
        combinations.items(),
        key=lambda item: item[1],
        reverse=True
    ):

        print(
            f"{', '.join(fields)}: {count}"
        )

    print("\n========================================")


if __name__ == "__main__":
    classify()