from backend.agents.base_agent import BaseAgent
from backend.agents.state import AgentState


class CollegeScoringAgent(BaseAgent):
    """
    Scores enriched colleges from 0 to 100.

    Scoring factors:
        - CSE / ECE / EEE department: 20
        - AI / ML / Data Science: 20
        - Training / placement: 15
        - Technical clubs / events: 10
        - Workshop / training opportunity: 15
        - Relevant public contact: 10
        - Website / information quality: 10
    """

    def execute(
        self,
        state: AgentState,
    ) -> AgentState:

        try:
            state.status = "running"

            colleges = state.enriched_results

            if not colleges and isinstance(
                state.result,
                dict,
            ):
                colleges = state.result.get(
                    "colleges",
                    [],
                )

            scored_colleges = []

            for college in colleges:
                scored_colleges.append(
                    self._score_college(
                        college
                    )
                )

            state.scores = scored_colleges
            state.result = scored_colleges
            state.status = "success"

            return state

        except Exception as exc:
            state.status = "failed"
            state.error = str(exc)

            return state

    def _score_college(
        self,
        college: dict,
    ) -> dict:

        score = 0
        reasons = []

        departments = self._values(
            college.get(
                "departments",
                [],
            )
        )

        programs = self._values(
            college.get(
                "programs",
                [],
            )
        )

        department_text = " ".join(
            departments
        ).lower()

        program_text = " ".join(
            programs
        ).lower()

        # -----------------------------------------
        # 1. CSE / ECE / EEE departments — 20
        # -----------------------------------------

        if any(
            keyword in department_text
            for keyword in [
                "computer science",
                "electronics and communication",
                "electrical and electronics",
                "cse",
                "ece",
                "eee",
            ]
        ):
            score += 20
            reasons.append(
                "Has relevant engineering department"
            )

        # -----------------------------------------
        # 2. AI / ML / Data Science — 20
        # -----------------------------------------

        ai_field = college.get(
            "ai_ml_related",
            {},
        )

        ai_value = (
            ai_field.get("value")
            if isinstance(ai_field, dict)
            else ai_field
        )

        ai_text = (
            department_text
            + " "
            + program_text
        )

        if (
            ai_value is True
            or any(
                keyword in ai_text
                for keyword in [
                    "artificial intelligence",
                    "machine learning",
                    "data science",
                    "ai & ml",
                    "ai and ml",
                ]
            )
        ):
            score += 20
            reasons.append(
                "Has AI/ML or Data Science relevance"
            )

        # -----------------------------------------
        # 3. Training / placement — 15
        # -----------------------------------------

        if self._field_value(
            college.get(
                "placement_page"
            )
        ):
            score += 15
            reasons.append(
                "Has active placement or training information"
            )

        # -----------------------------------------
        # 4. Technical clubs / events — 10
        # -----------------------------------------

        clubs_events = college.get(
            "clubs_events",
            [],
        )

        if clubs_events:
            score += 10
            reasons.append(
                "Has technical clubs or student events"
            )

        # -----------------------------------------
        # 5. Workshop / training opportunity — 15
        # -----------------------------------------

        innovation = college.get(
            "innovation",
            [],
        )

        entrepreneurship = college.get(
            "entrepreneurship",
            [],
        )

        if (
            innovation
            or entrepreneurship
        ):
            score += 15
            reasons.append(
                "Has innovation or training opportunity"
            )

        # -----------------------------------------
        # 6. Relevant public contact — 10
        # -----------------------------------------

        email = self._field_value(
            college.get(
                "official_email"
            )
        )

        phone = self._field_value(
            college.get(
                "official_phone"
            )
        )

        if email or phone:
            score += 10
            reasons.append(
                "Has relevant public institutional contact"
            )

        # -----------------------------------------
        # 7. Website / information quality — 10
        # -----------------------------------------

        website = self._field_value(
            college.get(
                "website"
            )
        )

        sources = college.get(
            "sources",
            [],
        )

        if (
            website
            and len(sources) >= 3
        ):
            score += 10
            reasons.append(
                "Has good official website information"
            )

        priority = self._priority(
            score
        )

        college_name = self._field_value(
            college.get(
                "name"
            )
        )

        return {
            "college_name": college_name,
            "score": score,
            "priority": priority,
            "reasons": reasons,
        }

    @staticmethod
    def _field_value(
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

    @staticmethod
    def _values(
        items,
    ):
        values = []

        for item in items:
            if isinstance(
                item,
                dict,
            ):
                value = item.get(
                    "value"
                )
            else:
                value = item

            if value:
                values.append(
                    str(value)
                )

        return values

    @staticmethod
    def _priority(
        score: int,
    ) -> str:

        if score >= 80:
            return "high"

        if score >= 60:
            return "medium"

        if score >= 40:
            return "low"

        return "very_low"