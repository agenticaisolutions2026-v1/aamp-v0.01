from sqlalchemy.orm import Session

from backend.models.college import College


class CollegeRepository:

    @staticmethod
    def create(db: Session, college: College):
        db.add(college)
        db.flush()
        return college

    @staticmethod
    def get_all(db: Session):
        return db.query(College).all()

    @staticmethod
    def get_by_id(
        db: Session,
        college_id: int,
    ):
        return (
            db.query(College)
            .filter(College.id == college_id)
            .first()
        )

    @staticmethod
    def update(
        db: Session,
        college: College,
        data: dict,
    ):
        for field, value in data.items():
            setattr(college, field, value)

        db.flush()
        return college

    @staticmethod
    def delete(
        db: Session,
        college: College,
    ):
        db.delete(college)
        db.flush()