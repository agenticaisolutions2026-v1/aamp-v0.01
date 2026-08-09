from services.api_client import get, post

class AgentService:

    @staticmethod
    def get_all():
        return get("/agents")

    @staticmethod
    def create(payload: dict):
        return post("/agents", payload)

    @staticmethod       # Naresh - Newly added
    def execute(payload: dict):
        return post("/agents/execute", payload)





   