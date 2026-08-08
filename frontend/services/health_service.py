from services.api_client import get

class HealthService:

    @staticmethod
    def get_status() -> dict:
        try:
            # Calls http://localhost:8000/api/v1/health
            return get("/health")
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Backend unreachable: {e}"
            }