from services.api_client import get, post


class OutreachService:

    @staticmethod
    def get_all():
        return get("/outreach")

    @staticmethod
    def get_by_id(outreach_id: int):
        return get(f"/outreach/{outreach_id}")

    @staticmethod
    def check_follow_up(outreach_id: int):
        return get(f"/outreach/{outreach_id}/follow-up")

    @staticmethod
    def send_follow_up(outreach_id: int):
        return post(
            f"/outreach/{outreach_id}/send-follow-up",
            {}
        )

    @staticmethod
    def submit_response(
        outreach_id: int,
        payload: dict
    ):
        return post(
            f"/outreach/{outreach_id}/response",
            payload
        )

    @staticmethod
    def schedule_demo(payload: dict):
        return post(
            "/demo/schedule",
            payload
        )