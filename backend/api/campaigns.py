from fastapi import APIRouter

router = APIRouter()


@router.get("/campaigns")
def get_campaigns():
    return [
        {
            "id": 1,
            "name": "AI Workshop",
            "department": "AI & ML",
            "status": "Active"
        },
        {
            "id": 2,
            "name": "Placement Drive",
            "department": "Computer Science",
            "status": "Completed"
        },
        {
            "id": 3,
            "name": "Internship Program",
            "department": "ECE",
            "status": "Upcoming"
        }
    ]