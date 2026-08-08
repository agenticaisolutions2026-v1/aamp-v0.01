from services.api_client import get, post

class CampaignService:

    @staticmethod
    def get_all():
        return get("/campaigns")

    @staticmethod
    def create(payload: dict):
        return post("/campaigns", payload)