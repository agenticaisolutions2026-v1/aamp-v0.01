import logging

from backend.agents.base_agent import BaseAgent
from backend.agents.state import AgentState


logger = logging.getLogger(__name__)


class LeadQualificationAgent(BaseAgent):
    """
    Qualify a college as a potential Generative AI /
    Agentic AI training lead.

    Qualification is based on lead score:
        80-100 -> qualified
        60-79  -> needs_review
        0-59   -> low_priority

    """

    RELEVANT_CONTACT_ROLES = [
        "training and placement",
        "training & placement",
        "placement",
        "placement officer",
        "training officer",
        "training cell",
        "t&p",
        "t&p cell",
        "industry relations",
        "industry interaction",
        "industry liaison",
        "career services",
        "training placement",
        "training and placement cell",
    ]

    def execute(self, state: AgentState) -> AgentState:

        try:
            state.status = "running"

            college = self._get_college(state)
            score_result = self._get_score(state)

            if not isinstance(college, dict):
                raise ValueError(
                    "Enriched college must be a dictionary"
                )

            if not isinstance(score_result, dict):
                raise ValueError(
                    "Score result must be a dictionary"
                )

            college_name = self._get_value(
                college.get("name")
            )

            college_score = score_result.get(
                "score"
            )

            if college_score is None:
                raise ValueError(
                    "College score is missing"
                )

            logger.info(
                "Qualifying lead: %s",
                college_name,
            )

            contact_role = self._find_contact_role(
                college
            )

            has_public_contact = (
                self._has_public_contact(
                    college
                )
            )

            qualification = (
                self._determine_qualification(
                    college_score,
                )
            )

            reason = self._build_reason(
                college,
                score_result,
                qualification,
                contact_role,
                has_public_contact,
            )

            result = {
                "college_name": college_name,
                "contact_role": contact_role,
                "qualification": qualification,
                "lead_score": college_score,
                "reason": reason,
            }

            state.qualified_leads = [result]

            # Backward compatibility
            state.result = result

            state.status = "completed"

            return state

        except Exception as exc:

            logger.exception(
                "Lead qualification failed"
            )

            state.status = "failed"
            state.error = str(exc)

            return state

    # --------------------------------------------------
    # Get enriched college
    # --------------------------------------------------

    def _get_college(self, state: AgentState):

        if state.enriched_results:

            if isinstance(
                state.enriched_results,
                list,
            ):
                return state.enriched_results[0]

            return state.enriched_results

        return None

    # --------------------------------------------------
    # Get scoring result
    # --------------------------------------------------

    def _get_score(self, state: AgentState):

        if state.scores:

            if isinstance(
                state.scores,
                list,
            ):
                return state.scores[0]

            return state.scores

        return None

    # --------------------------------------------------
    # Extract enrichment value
    # --------------------------------------------------

    @staticmethod
    def _get_value(field):

        if isinstance(field, dict):
            return field.get("value")

        return field

    # --------------------------------------------------
    # Check public institutional contact
    # --------------------------------------------------

    def _has_public_contact(self, college):

        email = self._get_value(
            college.get("official_email")
        )

        phone = self._get_value(
            college.get("official_phone")
        )

        contact_page = self._get_value(
            college.get("contact_page")
        )

        return bool(
            email
            or phone
            or contact_page
        )


    # --------------------------------------------------
    # Find contact role
    # --------------------------------------------------

    def _find_contact_role(self, college):

        explicit_role = self._get_value(
            college.get("contact_role")
        )

        if explicit_role:
            return str(explicit_role)

        return None

    # --------------------------------------------------
    # Check whether contact role is relevant
    # --------------------------------------------------

    def _is_relevant_contact_role(
        self,
        contact_role,
    ):

        if not contact_role:
            return False

        role_lower = str(
            contact_role
        ).lower()

        return any(
            relevant_role in role_lower
            for relevant_role in (
                self.RELEVANT_CONTACT_ROLES
            )
        )

    # --------------------------------------------------
    # Determine qualification
    # --------------------------------------------------

    def _determine_qualification(
            
        self,
        score,
    ):

        if score >= 80:
            return "qualified"

        if score >= 60:
            return "needs_review"

        return "low_priority"

    # --------------------------------------------------
    # Build explanation
    # --------------------------------------------------

    def _build_reason(
        self,
        college,
        score_result,
        qualification,
        contact_role,
        has_public_contact,
    ):

        score = score_result.get(
            "score",
            0,
        )

        if qualification == "qualified":

            return (
                "Strong CSE/AI audience and "
                f"relevant {contact_role} contact "
                "available for outreach."
            )

        if qualification == "needs_review":

            if score >= 80:

                if contact_role:

                    return (
                        "Strong college opportunity with "
                        f"{contact_role} contact, but "
                        "human review is required before outreach."
                    )

                return (
                    "Strong college opportunity, but "
                    "a relevant institutional contact "
                    "role is unavailable and requires "
                    "human review."
                )

            if score >= 60:

                if contact_role:

                    return (
                        "Relevant CSE/AI audience with "
                        f"{contact_role} contact; "
                        "human review is required before outreach."
                    )

                return (
                    "Relevant CSE/AI audience, but "
                    "the lead requires human review "
                    "before outreach."
                )

        return (
            "Limited evidence of a strong "
            "Generative AI/Agentic AI training "
            "opportunity."
        )