from services.api_client import get, post


class CampaignService:

    @staticmethod
    def get_all():
        return get("/campaigns")

    @staticmethod
    def create(payload: dict):
        return post("/campaigns", payload)

    @staticmethod
    def approve(campaign_id: int):
        return post(f"/campaigns/{campaign_id}/approve", {})

    @staticmethod
    def reject(campaign_id: int):
        return post(f"/campaigns/{campaign_id}/reject", {})