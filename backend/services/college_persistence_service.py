from sqlalchemy.orm import Session

from backend.services.college_service import CollegeService


class CollegePersistenceService:

    @staticmethod
    def save_college(
        db: Session,
        enriched_college: dict,
    ):
        def value(field):
            data = enriched_college.get(field)

            if isinstance(data, dict):
                return data.get("value")

            return data

        college_data = {
            "name": value("name"),
            "website": value("website"),
            "state": value("state"),
            "city": value("city"),
            "address": value("address"),
            "phone": value("official_phone"),
            "email": value("official_email"),
            "departments": enriched_college.get(
                "departments",
                [],
            ),
            "programs": enriched_college.get(
                "programs",
                [],
            ),
            "placement_page": value(
                "placement_page"
            ),
            "contact_page": value(
                "contact_page"
            ),
            "source_url": value("website"),
        }

        return CollegeService.create(
            db=db,
            college_data=college_data,
        )