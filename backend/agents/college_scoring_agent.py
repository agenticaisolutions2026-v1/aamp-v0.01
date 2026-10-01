import logging

from backend.agents.base_agent import BaseAgent
from backend.agents.state import AgentState


logger = logging.getLogger(__name__)


class CollegeScoringAgent(BaseAgent):
    """
    Score an enriched college for Generative AI /
    Agentic AI training opportunities.

    Scoring:
        CSE / ECE / EEE departments      20
        AI / ML / Data Science           20
        Training                         15
        Technical clubs / events         10
        Workshop opportunity             15
        Public institutional contact     10
        Website / information quality    10
        ------------------------------------
        Total                            100

    Priority:
        80-100 -> high
        60-79  -> medium
        40-59  -> low
        0-39   -> very_low

    Missing information is represented as None
    in score_breakdown.
    """

    def execute(self, state: AgentState) -> AgentState:

        try:
            state.status = "running"

            college = self._get_college(state)

            if not isinstance(college, dict):
                raise ValueError(
                    "Enriched college must be a dictionary"
                )

            college_name = self._get_value(
                college.get("name")
            )

            logger.info(
                "Scoring college: %s",
                college_name,
            )

            (
                score,
                score_breakdown,
                reasons,
                missing_information,
            ) = self._calculate_score(college)

            priority = self._get_priority(score)

            result = {
                "college_name": college_name,

                "score_breakdown": score_breakdown,

                "score": score,

                "priority": priority,

                "reasons": reasons,

                "missing_information": missing_information,
            }

            # Store scoring result
            state.scores = [result]

            # Keep backward compatibility
            state.result = result

            state.status = "completed"

            return state

        except Exception as exc:

            logger.exception(
                "College scoring failed"
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

        return state.result

    # --------------------------------------------------
    # Extract value from enrichment object
    # --------------------------------------------------

    @staticmethod
    def _get_value(field):

        if isinstance(field, dict):
            return field.get("value")

        return field

    # --------------------------------------------------
    # Extract values from list
    # --------------------------------------------------

    def _get_values(self, field):

        if not isinstance(field, list):
            return []

        values = []

        for item in field:

            value = self._get_value(item)

            if value:
                values.append(
                    str(value).lower()
                )

        return values

    # --------------------------------------------------
    # Calculate score
    # --------------------------------------------------

    def _calculate_score(self, college):

        score = 0

        reasons = []

        missing_information = []

        # Detailed factor-level scoring
        score_breakdown = {
            "cse_ece_eee": None,
            "ai_ml_data_science": None,
            "training": None,
            "technical_clubs_events": None,
            "workshop_training_opportunity": None,
            "public_institutional_contact": None,
            "website_information_quality": None,
        }

        # ==============================================
        # 1. CSE / ECE / EEE - 20 points
        # ==============================================

        departments = self._get_values(
            college.get("departments")
        )

        core_keywords = [
            "computer science",
            "cse",
            "electronics and communication",
            "ece",
            "electrical and electronics",
            "eee",
        ]

        has_core_department = any(
            any(
                keyword in department
                for keyword in core_keywords
            )
            for department in departments
        )

        if departments:

            if has_core_department:

                score += 20

                score_breakdown[
                    "cse_ece_eee"
                ] = 20

                reasons.append(
                    "Has CSE/ECE/EEE related department"
                )

            else:

                score_breakdown[
                    "cse_ece_eee"
                ] = 0

        else:

            missing_information.append(
                "Department information"
            )

        # ==============================================
        # 2. AI / ML / Data Science - 20 points
        # ==============================================

        programs = self._get_values(
            college.get("programs")
        )

        ai_ml_flag = self._get_value(
            college.get("ai_ml_related")
        )

        ai_keywords = [
            "artificial intelligence",
            "machine learning",
            "ai/ml",
            "data science",
            "data analytics",
        ]

        has_ai_ml = (
            ai_ml_flag is True
            or any(
                any(
                    keyword in value
                    for keyword in ai_keywords
                )
                for value in (
                    departments + programs
                )
            )
        )

        ai_information_available = (
            ai_ml_flag is not None
            or bool(programs)
            or bool(departments)
        )

        if ai_information_available:

            if has_ai_ml:

                score += 20

                score_breakdown[
                    "ai_ml_data_science"
                ] = 20

                reasons.append(
                    "Offers AI/ML/Data Science related "
                    "program or department"
                )

            else:

                score_breakdown[
                    "ai_ml_data_science"
                ] = 0

        else:

            missing_information.append(
                "AI/ML/Data Science information"
            )

        # ==============================================
        # 3. Training - 15 points
        # ==============================================

        training_data = self._get_values(
            college.get("training")
        )

        if training_data:

            score += 15

            score_breakdown[
                "training"
            ] = 15

            reasons.append(
                "Has training information"
            )

        elif "training" in college:

            score_breakdown[
                "training"
            ] = None

            missing_information.append(
                "Training information"
            )

        else:

            score_breakdown[
                "training"
            ] = None

            missing_information.append(
                "Training information"
            )

        # ==============================================
        # 4. Technical / Student Clubs or Events
        #    10 points
        # ==============================================

        if "clubs_events" not in college:

            missing_information.append(
                "Technical clubs/events information"
            )

        else:

            clubs_events = college.get(
                "clubs_events"
            )

            if clubs_events:

                score += 10

                score_breakdown[
                    "technical_clubs_events"
                ] = 10

                reasons.append(
                    "Has technical clubs or events"
                )

            else:

                missing_information.append(
                    "Technical clubs/events information"
                )

        # ==============================================
        # 5. Workshop / Training Opportunity
        #    15 points
        # ==============================================

        workshop_data = self._get_values(
            college.get(
                "workshop_training_opportunity"
            )
        )

        opportunity_keywords = [
            "workshop",
            "training",
            "hackathon",
            "bootcamp",
            "faculty development",
            "technical event",
            "skill development",
            "certification",
        ]

        has_opportunity = any(
            keyword in value
            for value in workshop_data
            for keyword in opportunity_keywords
        )

        if has_opportunity:

            score += 15

            score_breakdown[
                "workshop_training_opportunity"
            ] = 15

            reasons.append(
                "Shows workshop/training opportunity"
            )

        else:

            score_breakdown[
                "workshop_training_opportunity"
            ] = None

            missing_information.append(
                "Workshop/training opportunity information"
            )

        # ==============================================
        # 6. Public Institutional Contact
        #    10 points
        # ==============================================

        email = self._get_value(
            college.get("official_email")
        )

        phone = self._get_value(
            college.get("official_phone")
        )

        contact_page = self._get_value(
            college.get("contact_page")
        )

        if email or phone or contact_page:

            score += 10

            score_breakdown[
                "public_institutional_contact"
            ] = 10

            reasons.append(
                "Has public institutional contact"
            )

        else:

            missing_information.append(
                "Public institutional contact"
            )

        # ==============================================
        # 7. Website / Information Quality
        #    10 points
        # ==============================================

        website = self._get_value(
            college.get("website")
        )

        sources = college.get(
            "sources"
        )

        if website and sources:

            score += 10

            score_breakdown[
                "website_information_quality"
            ] = 10

            reasons.append(
                "Has official website and "
                "supporting information sources"
            )

        else:

            missing_information.append(
                "Website/information quality"
            )

        return (
            score,
            score_breakdown,
            reasons,
            missing_information,
        )

    # --------------------------------------------------
    # Priority
    # --------------------------------------------------

    @staticmethod
    def _get_priority(score):

        if score >= 80:
            return "high"

        if score >= 60:
            return "medium"

        if score >= 40:
            return "low"

        return "very_low"