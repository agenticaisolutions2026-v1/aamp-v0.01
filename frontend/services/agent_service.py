from services.api_client import get, post

class AgentService:

    @staticmethod
    def get_all():
        return get("/agents")

    @staticmethod
    def create(payload: dict):
        return post("/agents", payload)