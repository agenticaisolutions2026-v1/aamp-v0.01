from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.demo_scheduling_service import (
    DemoSchedulingService,
)


router = APIRouter()


# =========================================================
# Request Model
# =========================================================

class DemoScheduleRequest(BaseModel):
    college_name: str
    recipient: str
    selected_date: str
    selected_time: str


# =========================================================
# Get Available Demo Slots
# =========================================================

@router.get("/demo/slots")
def get_demo_slots():

    service = DemoSchedulingService()

    slots = service.get_available_slots(
        days=7
    )

    # Convert datetime objects into JSON-safe values
    available_slots = []

    for slot in slots:

        available_slots.append(
            {
                "date": slot["date"],
                "time": slot["time"],
            }
        )

    return {
        "status": "success",
        "slots": available_slots,
    }


# =========================================================
# Schedule Demo
# =========================================================

@router.post("/demo/schedule")
def schedule_demo(
    request: DemoScheduleRequest,
):

    service = DemoSchedulingService()

    result = service.schedule_demo(
        college_name=request.college_name,
        recipient=request.recipient,
        selected_date=request.selected_date,
        selected_time=request.selected_time,
    )

    # -----------------------------------------------------
    # Check scheduling result
    # -----------------------------------------------------

    if result.get("status") != "scheduled":

        raise HTTPException(
            status_code=400,
            detail=result.get(
                "reason",
                "Demo scheduling failed.",
            ),
        )

    # -----------------------------------------------------
    # Return structured response
    # -----------------------------------------------------

    return {
        "status": "scheduled",
        "college_name": result[
            "college_name"
        ],
        "recipient": result[
            "recipient"
        ],
        "demo_date": result[
            "demo_date"
        ],
        "demo_time": result[
            "demo_time"
        ],
        "confirmation_message": result[
            "confirmation_message"
        ],
        "real_message_sent": result[
            "real_message_sent"
        ],
        "message": (
            "Demo scheduled successfully."
        ),
    }