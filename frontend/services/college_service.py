from services.api_client import get


class CollegeService:

    @staticmethod
    def search(
        state: str | None = None,
        priority: str | None = None,
        min_score: float | None = None,
        max_score: float | None = None,
    ):
        params = {
            "state": state,
            "priority": priority,
            "min_score": min_score,
            "max_score": max_score,
        }

        params = {
            key: value
            for key, value in params.items()
            if value is not None and value != ""
        }

        return get(
            "/colleges/search",
            params=params,
        )
    @staticmethod
    def get_overview():
        return get("/colleges/overview")

    @staticmethod
    def get_by_id(college_id: int):
        return get(
            f"/colleges/{college_id}"
        )