import logging

from backend.agents.base_agent import BaseAgent
from backend.agents.state import AgentState


logger = logging.getLogger(__name__)


class HumanReviewAgent(BaseAgent):
    """
    Human approval gate for the AAMP college lead pipeline.

    Workflow:

        Lead Qualification
                ↓
        Human Review Agent
                ↓
          pending
           ↙    ↘
      approved  rejected
           ↓
      Approved Outreach

    The agent does NOT automatically approve a lead.
    Human approval must be explicitly provided.
    """

    VALID_APPROVAL_STATUSES = [
        "pending",
        "approved",
        "rejected",
    ]

    def execute(
        self,
        state: AgentState,
    ) -> AgentState:

        try:
            state.status = "running"

            # Human review is required by default.
            state.approval_required = True

            # Do not automatically approve anything.
            if not state.approval_status:
                state.approval_status = "pending"

            if state.approval_status not in (
                self.VALID_APPROVAL_STATUSES
            ):
                raise ValueError(
                    "Invalid approval status. "
                    "Use: pending, approved, or rejected."
                )

            logger.info(
                "Human review for lead: %s",
                self._get_college_name(state),
            )

            if state.approval_status == "pending":

                state.status = "waiting_for_approval"

                logger.info(
                    "Lead is waiting for human approval."
                )

                return state

            if state.approval_status == "approved":

                state.status = "approved"

                logger.info(
                    "Lead approved by human: %s",
                    state.reviewed_by,
                )

                return state

            if state.approval_status == "rejected":

                state.status = "rejected"

                logger.info(
                    "Lead rejected by human: %s",
                    state.reviewed_by,
                )

                return state

            return state

        except Exception as exc:

            logger.exception(
                "Human review failed"
            )

            state.status = "failed"
            state.error = str(exc)

            return state

    # --------------------------------------------------
    # Human approval action
    # --------------------------------------------------

    def approve(
        self,
        state: AgentState,
        approved_by: str,
        reason: str = "",
    ) -> AgentState:

        if not approved_by:
            raise ValueError(
                "approved_by is required"
            )

        state.approval_required = True
        state.approval_status = "approved"
        state.reviewed_by = approved_by
        state.approval_reason = reason
        state.status = "approved"

        logger.info(
            "Lead approved by %s",
            state.reviewed_by,
        )

        return state

    # --------------------------------------------------
    # Human rejection action
    # --------------------------------------------------

    def reject(
        self,
        state: AgentState,
        rejected_by: str,
        reason: str = "",
    ) -> AgentState:

        if not rejected_by:
            raise ValueError(
                "rejected_by is required"
            )

        state.approval_required = True
        state.approval_status = "rejected"
        state.reviewed_by = rejected_by
        state.approval_reason = reason
        state.status = "rejected"

        logger.info(
            "Lead rejected by %s",
            state.reviewed_by,
        )

        return state

    # --------------------------------------------------
    # Get college name
    # --------------------------------------------------

    def _get_college_name(
        self,
        state: AgentState,
    ):

        if state.qualified_leads:

            lead = state.qualified_leads[0]

            if isinstance(lead, dict):
                return lead.get(
                    "college_name",
                    "Unknown college",
                )

        if state.scores:

            score = state.scores[0]

            if isinstance(score, dict):
                return score.get(
                    "college_name",
                    "Unknown college",
                )

        return "Unknown college"