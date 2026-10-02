from backend.agents.base_agent import BaseAgent
from backend.agents.state import AgentState


class LeadQualificationAgent(BaseAgent):
    """
    Qualifies colleges as potential training leads.

    Qualification categories:
        - qualified
        - needs_review
        - low_priority

    The original enriched college information is preserved
    so the Campaign Strategy Agent can create personalized
    campaigns.

    The respondent role is recommended from the available
    college evidence. It is not treated as a confirmed
    person's identity.
    """

    def execute(
        self,
        state: AgentState,
    ) -> AgentState:

        try:
            state.status = "running"

            scores = state.scores

            enriched_colleges = (
                state.enriched_results
            )

            qualified_leads = []

            for score_data in scores:

                college = self._find_college(
                    score_data.get(
                        "college_name",
                        "",
                    ),
                    enriched_colleges,
                )

                lead = self._qualify_lead(
                    score_data,
                    college,
                )

                qualified_leads.append(
                    lead
                )

            state.qualified_leads = (
                qualified_leads
            )

            state.result = (
                qualified_leads
            )

            state.status = "success"

            return state

        except Exception as exc:

            state.status = "failed"
            state.error = str(exc)

            return state

    # =====================================================
    # Find matching enriched college
    # =====================================================

    @staticmethod
    def _find_college(
        college_name: str,
        colleges: list,
    ):

        for college in colleges:

            if not isinstance(
                college,
                dict,
            ):
                continue

            name = college.get(
                "name",
                "",
            )

            if isinstance(
                name,
                dict,
            ):
                name = name.get(
                    "value",
                    "",
                )

            if name == college_name:
                return college

        return {}

    # =====================================================
    # Qualify lead
    # =====================================================

    def _qualify_lead(
        self,
        score_data: dict,
        college: dict,
    ) -> dict:

        college_name = score_data.get(
            "college_name",
            "",
        )

        score = score_data.get(
            "score",
            0,
        )

        priority = score_data.get(
            "priority",
            "very_low",
        )

        reasons = score_data.get(
            "reasons",
            [],
        )

        # -----------------------------------------
        # Determine qualification
        # -----------------------------------------

        if score >= 80:

            qualification = "qualified"

        elif score >= 60:

            qualification = "needs_review"

        else:

            qualification = "low_priority"

        # -----------------------------------------
        # Determine recommended respondent
        # -----------------------------------------

        contact_role = (
            self._determine_contact_role(
                college
            )
        )

        # -----------------------------------------
        # Build lead reason
        # -----------------------------------------

        if qualification == "qualified":

            reason = (
                "Strong CSE/AI audience and "
                "relevant institutional training activity"
            )

        elif qualification == "needs_review":

            reason = (
                "Moderate training potential; "
                "requires human review before outreach"
            )

        else:

            reason = (
                "Limited evidence of immediate "
                "training opportunity"
            )

        # -----------------------------------------
        # Preserve college information
        # -----------------------------------------

        return {

            # College identity
            "college_name": college_name,

            # Recommended respondent
            "contact_role": contact_role,

            # Contact information
            "official_email": self._value(
                college.get(
                    "official_email"
                )
            ),

            "official_phone": self._value(
                college.get(
                    "official_phone"
                )
            ),

            # College information
            "website": self._value(
                college.get(
                    "website"
                )
            ),

            "state": self._value(
                college.get(
                    "state"
                )
            ),

            "city": self._value(
                college.get(
                    "city"
                )
            ),

            "departments": college.get(
                "departments",
                [],
            ),

            "programs": college.get(
                "programs",
                [],
            ),

            "placement_page": self._value(
                college.get(
                    "placement_page"
                )
            ),

            "contact_page": self._value(
                college.get(
                    "contact_page"
                )
            ),

            "innovation": college.get(
                "innovation",
                [],
            ),

            "entrepreneurship": college.get(
                "entrepreneurship",
                [],
            ),

            "clubs_events": college.get(
                "clubs_events",
                [],
            ),

            # Scoring information
            "qualification": qualification,

            "lead_score": score,

            "priority": priority,

            "reason": reason,

            "score_reasons": reasons,
        }

    # =====================================================
    # Determine recommended respondent role
    # =====================================================

    @staticmethod
    def _determine_contact_role(
        college: dict,
    ) -> str:

        placement_page = college.get(
            "placement_page"
        )

        official_email = college.get(
            "official_email"
        )

        departments = college.get(
            "departments",
            []
        )

        innovation = college.get(
            "innovation",
            []
        )

        entrepreneurship = college.get(
            "entrepreneurship",
            []
        )

        # -----------------------------------------
        # Placement / training evidence
        # -----------------------------------------

        if (
            placement_page
            or official_email
        ):

            return (
                "Training and Placement Officer"
            )

        # -----------------------------------------
        # AI / CSE department evidence
        # -----------------------------------------

        department_text = (
            " ".join(
                LeadQualificationAgent
                ._extract_values(
                    departments
                )
            )
            .lower()
        )

        if any(
            keyword in department_text
            for keyword in [
                "computer science",
                "artificial intelligence",
                "machine learning",
                "data science",
                "information technology",
            ]
        ):

            return (
                "HOD / Department Coordinator"
            )

        # -----------------------------------------
        # Innovation / entrepreneurship evidence
        # -----------------------------------------

        if (
            innovation
            or entrepreneurship
        ):

            return (
                "Innovation / Incubation Cell"
            )

        # -----------------------------------------
        # Default
        # -----------------------------------------

        return (
            "Institutional Training Coordinator"
        )

    # =====================================================
    # Extract values
    # =====================================================

    @staticmethod
    def _extract_values(
        values,
    ):

        result = []

        for value in values:

            if isinstance(
                value,
                dict,
            ):

                value = value.get(
                    "value"
                )

            if value:

                result.append(
                    str(value)
                )

        return result

    # =====================================================
    # Extract value from structured field
    # =====================================================

    @staticmethod
    def _value(
        field,
    ):

        if isinstance(
            field,
            dict,
        ):

            return field.get(
                "value"
            )

        return field