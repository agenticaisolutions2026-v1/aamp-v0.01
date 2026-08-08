from backend.clients.http_client import http_client


class APIClient:

    def __init__(self, base_url: str):
        self.base_url = base_url

    async def get(self, endpoint: str):
        response = await http_client.get(
            f"{self.base_url}{endpoint}"
        )
        response.raise_for_status()
        return response.json()

    async def post(self, endpoint: str, data: dict):
        response = await http_client.post(
            f"{self.base_url}{endpoint}",
            json=data
        )
        response.raise_for_status()
        return response.json()