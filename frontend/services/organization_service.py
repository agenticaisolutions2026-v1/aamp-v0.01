from services.api_client import get, post


class OrganizationService:

    @staticmethod
    def get_all():
        data = get("/organizations")
        return data
    #   return get("/organizations")

    @staticmethod
    def create(payload: dict):
        return post("/organizations", payload)