from apscheduler.schedulers.background import BackgroundScheduler

from backend.services.follow_up_service import FollowUpService
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


class CampaignScheduler:
    """
    Scheduler responsible for triggering campaign automation jobs.
    """

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.follow_up_service = FollowUpService()

        self.last_run_at = None
        self.last_processed_count = 0

    # --------------------------------------------------
    # Follow-up automation job
    # --------------------------------------------------

    def process_followups(self):
        """
        Process all campaigns whose follow-up is currently due.
        """

        self.last_run_at = datetime.now(
            timezone.utc
        )

        try:
            results = (
                self.follow_up_service
                .process_due_followups()
            )

            self.last_processed_count = len(results)

            if results:
                print(
                    f"[Scheduler] Processed "
                    f"{len(results)} follow-up(s)"
                )

        except Exception as exc:

            self.last_processed_count = 0

            print(
                f"[Scheduler] Follow-up processing "
                f"failed: {exc}"
            )

    def get_status(self):
        """
        Return the current scheduler status.
        """

        jobs = self.scheduler.get_jobs()

        # Get currently due follow-ups
        try:
            due_followups = (
                self.follow_up_service
                .get_due_followups()
            )

            due_followup_count = len(
                due_followups
            )

        except Exception:
            due_followup_count = 0

        return {
            "running": self.scheduler.running,

            "jobs": [
                {
                    "id": job.id,
                    "next_run_time": (
                        job.next_run_time.isoformat()
                        if job.next_run_time
                        else None
                    ),
                }
                for job in jobs
            ],

            "due_followups": due_followup_count,

            "last_run_at": (
                self.last_run_at.isoformat()
                if self.last_run_at
                else None
            ),

            "last_processed_count":
                self.last_processed_count,
        }

    # --------------------------------------------------
    # Start scheduler
    # --------------------------------------------------

    def start(self):

        self.scheduler.add_job(
            self.process_followups,
            trigger="interval",
            minutes=1,
            id="campaign_followup_job",
            replace_existing=True,
        )

        self.scheduler.start()

        print(
            "[Scheduler] Campaign scheduler started."
        )

    # --------------------------------------------------
    # Stop scheduler
    # --------------------------------------------------

    def shutdown(self):

        if self.scheduler.running:

            self.scheduler.shutdown(
                wait=False
            )

            print(
                "[Scheduler] Campaign scheduler stopped."
            )