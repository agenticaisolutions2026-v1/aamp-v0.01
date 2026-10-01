from services.api_client import get, post, patch, delete


class CampaignService:

    @staticmethod
    def get_all():
        return get("/campaigns")

    @staticmethod
    def get_by_status(status: str):
        return get(f"/campaigns/status/{status}")

    @staticmethod
    def get_by_college(college_id: int):
        return get(f"/campaigns/college/{college_id}")

    @staticmethod
    def get_by_id(campaign_id: int):
        return get(f"/campaigns/{campaign_id}")

    @staticmethod
    def create(payload: dict):
        return post("/campaigns", payload)

    @staticmethod
    def approve(
        campaign_id: int,
        approved_by: str,
        reason: str = "",
    ):
        return post(
            f"/campaigns/{campaign_id}/approve",
            {
                "approved_by": approved_by,
                "reason": reason,
            },
        )

    @staticmethod
    def reject(
        campaign_id: int,
        rejected_by: str,
        reason: str = "",
    ):
        return post(
            f"/campaigns/{campaign_id}/reject",
            {
                "rejected_by": rejected_by,
                "reason": reason,
            },
        )

    @staticmethod
    def update(
        campaign_id: int,
        payload: dict,
    ):
        return patch(
            f"/campaigns/{campaign_id}/draft",
            payload,
        )

    @staticmethod
    def close(campaign_id: int):
        return post(
            f"/campaigns/{campaign_id}/close",
            {},
        )

    @staticmethod
    def send(campaign_id: int):
        return post(
            f"/campaigns/{campaign_id}/send",
            {},
        )

    @staticmethod
    def get_history(campaign_id: int):
        return get(f"/campaigns/{campaign_id}/history")


    @staticmethod
    def get_messages(campaign_id: int):
        return get(f"/campaigns/{campaign_id}/messages")

    @staticmethod
    def delete(campaign_id: int):
        return delete(f"/campaigns/{campaign_id}")

    @staticmethod
    def recreate(campaign_id: int):
        return post(
            "/campaigns/recreate",
            {"campaign_id": campaign_id},
        )


    @staticmethod
    def get_scheduler_status():
        return get("/campaigns/scheduler/status")