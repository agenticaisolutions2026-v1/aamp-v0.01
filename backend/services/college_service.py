from sqlalchemy.orm import Session

from backend.database.models import College


class CollegeService:

    @staticmethod
    def create(
        db: Session,
        college_data: dict,
    ):

        college = College(
            name=college_data.get(
                "name",
                "",
            ),

            website=college_data.get(
                "website"
            ),

            state=college_data.get(
                "state"
            ),

            city=college_data.get(
                "city"
            ),

            address=college_data.get(
                "address"
            ),

            phone=college_data.get(
                "phone"
            ),

            email=college_data.get(
                "email"
            ),

            departments=str(
                college_data.get(
                    "departments",
                    [],
                )
            ),

            programs=str(
                college_data.get(
                    "programs",
                    [],
                )
            ),

            placement_page=college_data.get(
                "placement_page"
            ),

            contact_page=college_data.get(
                "contact_page"
            ),

            source_url=college_data.get(
                "source_url"
            ),

            status=college_data.get(
                "status",
                "active",
            ),
        )

        db.add(college)

        db.commit()

        db.refresh(college)

        return college

    @staticmethod
    def get_all(
        db: Session,
    ):
        return db.query(
            College
        ).all()