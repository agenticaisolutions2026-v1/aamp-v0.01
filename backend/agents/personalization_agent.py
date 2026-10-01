import logging

from backend.agents.base_agent import BaseAgent
from backend.agents.state import AgentState


logger = logging.getLogger(__name__)


class PersonalizationAgent(BaseAgent):
    """
    Generate personalized outreach messages using verified
    college enrichment data.

    No LLM or external API is used.

    Human approval is mandatory before outreach.
    """

    def execute(self, state: AgentState) -> AgentState:

        try:
            state.status = "running"

            college = self._get_college(state)
            lead = self._get_lead(state)
            strategy = self._get_strategy(state)

            if not isinstance(college, dict):
                raise ValueError(
                    "Enriched college must be a dictionary"
                )

            if not isinstance(lead, dict):
                raise ValueError(
                    "Qualified lead must be a dictionary"
                )

            if not isinstance(strategy, dict):
                raise ValueError(
                    "Campaign strategy must be a dictionary"
                )

            if lead.get("qualification") != "qualified":
                raise ValueError(
                    "Personalization requires a qualified lead"
                )

            college_name = self._get_value(
                college.get("name")
            )

            college_id = college.get("id")

            city = self._get_value(
                college.get("city")
            )

            state_name = self._get_value(
                college.get("state")
            )

            message_type = strategy.get(
                "message_type",
                "initial_outreach"
            )

            campaign_type = strategy.get(
                "campaign_type",
                "institutional_training"
            )

            channel = strategy.get(
                "recommended_channel"
            )

            logger.info(
                "Generating personalized message for %s",
                college_name,
            )

            personalization = (
                self._build_personalization(
                    college
                )
            )

            subject = self._generate_subject(
                college_name,
                campaign_type,
                message_type,
            )

            message = self._generate_message(
                college,
                strategy,
                message_type,
            )

            result = {
                "college_id": college_id,
                "college_name": college_name,
                "city": city,
                "state": state_name,
                "campaign_type": campaign_type,
                "message_type": message_type,
                "channel": channel,
                "subject": subject,
                "message": message,
                "objective": strategy.get("objective"),
                "value_proposition": strategy.get("value_proposition", []),
                "audience": strategy.get("audience", []),
                "priority": strategy.get("priority"),
                "personalization_used": personalization,
                "required_human_approval": True,
                "approval_status": "pending",
            }

            state.personalized_messages = [result]

            # Campaign result for later processing
            state.campaign_results = [result]

            # Backward compatibility
            state.result = result

            # Approval is always required
            state.approval_required = True
            state.approval_status = "pending"

            state.status = "completed"

            return state

        except Exception as exc:

            logger.exception(
                "Personalized message generation failed"
            )

            state.status = "failed"
            state.error = str(exc)

            return state

    # --------------------------------------------------
    # Get enriched college
    # --------------------------------------------------

    def _get_college(self, state):

        if state.enriched_results:

            if isinstance(
                state.enriched_results,
                list,
            ):
                return state.enriched_results[0]

            return state.enriched_results

        return None

    # --------------------------------------------------
    # Get qualified lead
    # --------------------------------------------------

    def _get_lead(self, state):

        if state.qualified_leads:

            if isinstance(
                state.qualified_leads,
                list,
            ):
                return state.qualified_leads[0]

            return state.qualified_leads

        return None

    # --------------------------------------------------
    # Get campaign strategy
    # --------------------------------------------------

    def _get_strategy(self, state):

        if state.campaign_strategies:

            if isinstance(
                state.campaign_strategies,
                list,
            ):
                return state.campaign_strategies[0]

            return state.campaign_strategies

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
    # Get department names
    # --------------------------------------------------

    def _get_departments(self, college):

        departments = college.get(
            "departments"
        )

        if not isinstance(
            departments,
            list,
        ):
            return []

        values = []

        for department in departments:

            value = self._get_value(
                department
            )

            if value:
                values.append(
                    str(value)
                )

        return values

    # --------------------------------------------------
    # Personalization fields
    # --------------------------------------------------

    def _build_personalization(
        self,
        college,
    ):

        personalization = []

        departments = self._get_departments(
            college
        )

        if departments:

            personalization.append({
                "field": "departments",
                "value": departments,
            })

        ai_ml_related = self._get_value(
            college.get("ai_ml_related")
        )

        if ai_ml_related is True:

            personalization.append({
                "field": "ai_ml_related",
                "value": True,
            })

        generative_ai_related = self._get_value(
            college.get(
                "generative_ai_related"
            )
        )

        if generative_ai_related is True:

            personalization.append({
                "field": "generative_ai_related",
                "value": True,
            })

        training = college.get(
            "training"
        )

        if training:

            personalization.append({
                "field": "training",
                "value": True,
            })

        workshop = college.get(
            "workshop_training_opportunity"
        )

        if workshop:

            personalization.append({
                "field": "workshop_training_opportunity",
                "value": True,
            })

        placement = self._get_value(
            college.get(
                "placement_available"
            )
        )

        if placement is True:

            personalization.append({
                "field": "placement_available",
                "value": True,
            })

        contact_role = self._get_value(
            college.get("contact_role")
        )

        if contact_role:

            personalization.append({
                "field": "contact_role",
                "value": contact_role,
            })

        return personalization

    # --------------------------------------------------
    # Generate subject
    # --------------------------------------------------

    def _generate_subject(
        self,
        college_name,
        campaign_type,
        message_type,
    ):

        if message_type == "workshop_proposal":

            return (
                f"Generative AI & Agentic AI Workshop "
                f"Proposal for {college_name}"
            )

        if message_type == "training_proposal":

            return (
                f"Industry AI Training Opportunity "
                f"for {college_name}"
            )

        if message_type == "follow_up":

            return (
                f"Follow-up: AI Training Opportunity "
                f"for {college_name}"
            )

        if message_type == "response_to_interest":

            return (
                f"AI Training & Workshop Discussion "
                f"with {college_name}"
            )

        return (
            "AI Training, Quantum Computing & Workshop "
            f"Opportunity for {college_name}"
        )
    # --------------------------------------------------
    # Generate message
    # --------------------------------------------------

    def _generate_message(
        self,
        college,
        strategy,
        message_type,
    ):

        college_name = self._get_value(
            college.get("name")
        )

        city = self._get_value(
            college.get("city")
        )

        state = self._get_value(
            college.get("state")
        )

        departments = self._get_departments(
            college
        )

        contact_role = self._get_value(
            college.get("contact_role")
        )

        ai_ml_related = self._get_value(
            college.get("ai_ml_related")
        )

        training = college.get(
            "training"
        )

        workshop = college.get(
            "workshop_training_opportunity"
        )

        opening = self._generate_opening(
            college_name,
            city,
            state,
            departments,
            ai_ml_related,
        )

        if message_type == "follow_up":

            return self._follow_up_message(
                college_name,
                contact_role,
            )

        if message_type == "workshop_proposal":

            return self._workshop_message(
                college_name,
                contact_role,
                departments,
                workshop,
            )

        if message_type == "training_proposal":

            return self._training_message(
                college_name,
                contact_role,
                departments,
                training,
            )

        if message_type == "response_to_interest":

            return self._interest_response(
                college_name,
                contact_role,
            )

        return self._initial_message(
            opening,
            college_name,
            contact_role,
            departments,
            ai_ml_related,
            training,
            workshop,
        )
    def _message_signature(self):
        return (
            "\n\n"
            "Thank you,\n"
            "AI & Quantum Training Team."
        )

    # --------------------------------------------------
    # Opening
    # --------------------------------------------------

    def _generate_opening(
        self,
        college_name,
        city,
        state,
        departments,
        ai_ml_related,
    ):

        if departments:

            relevant_departments = [
                department
                for department in departments
                if (
                    "computer" in department.lower()
                    or "artificial intelligence"
                    in department.lower()
                    or "machine learning"
                    in department.lower()
                )
            ]

            if relevant_departments:

                department_text = (
                    ", ".join(
                        relevant_departments[:2]
                    )
                )

                return (
                    f"We noticed that {college_name} "
                    f"has academic areas including "
                    f"{department_text}."
                )

        if ai_ml_related is True:

            return (
                f"We noticed that {college_name} "
                "has an academic focus related to "
                "Artificial Intelligence and Machine Learning."
            )

        return (
            f"We came across {college_name} and "
            "would like to explore a potential "
            "institutional training opportunity."
        )

    # --------------------------------------------------
    # Initial outreach
    # --------------------------------------------------

    def _initial_message(
        self,
        opening,
        college_name,
        contact_role,
        departments,
        ai_ml_related,
        training,
        workshop,
    ):

        greeting = self._greeting(
            contact_role
        )

        message = f"""{greeting}

I hope you are doing well.

{opening}

We conduct industry-focused training programs in Generative AI, Agentic AI and Quantum Computing, designed to help engineering students develop practical and industry-relevant skills.

"""

        if training and workshop:

            message += (
                "We would be happy to explore a "
                "3-day or 1-week workshop, or a "
                "longer-term 6-month training program "
                "that could complement your students' "
                "academic and career development.\n\n"
            )

        elif workshop:

            message += (
                "We would be happy to explore a "
                "3-day or 1-week workshop focused on "
                "emerging AI technologies for your students.\n\n"
            )

        elif training:

            message += (
                "We would be happy to explore a "
                "longer-term training program that "
                "could complement your students' "
                "academic and career development.\n\n"
            )

        else:

            message += (
                "We would be happy to discuss suitable "
                "training or workshop formats based on "
                "your institution's requirements.\n\n"
            )

        message += (
            "Would you be available for a brief "
            "discussion to explore whether this could "
            "be relevant for your institution?"
        )

        message += self._message_signature()

        return message

    # --------------------------------------------------
    # Follow-up
    # --------------------------------------------------

    def _follow_up_message(
        self,
        college_name,
        contact_role,
    ):

        greeting = self._greeting(
            contact_role
        )

        return f"""{greeting}

I wanted to follow up on our earlier message regarding Generative AI, Agentic AI and Quantum Computing training opportunities for {college_name}.

We would be glad to discuss possible workshop or institutional training formats based on your students' requirements.

If this is relevant to your institution, please let us know a convenient time for a brief discussion.

Thank you."""

    # --------------------------------------------------
    # Workshop proposal
    # --------------------------------------------------

    def _workshop_message(
        self,
        college_name,
        contact_role,
        departments,
        workshop,
    ):

        greeting = self._greeting(
            contact_role
        )

        return f"""{greeting}

We would like to explore conducting a practical workshop at {college_name} focused on Generative AI, Agentic AI and emerging AI technologies.

Based on the academic areas identified at the institution, the workshop can be tailored for relevant engineering students.

We can structure the engagement as a 3-day or 1-week workshop with practical, industry-oriented learning.

We would be happy to share a detailed workshop proposal and discuss the requirements with your team.

Would you be available for a brief discussion?"""

    # --------------------------------------------------
    # Training proposal
    # --------------------------------------------------

    def _training_message(
        self,
        college_name,
        contact_role,
        departments,
        training,
    ):

        greeting = self._greeting(
            contact_role
        )

        return f"""{greeting}

We would like to explore a longer-term industry training program for students at {college_name} covering Generative AI, Agentic AI and Quantum Computing.

The program can be structured around the requirements of relevant engineering departments and may be delivered as a 6-month training engagement.

We would be happy to discuss the curriculum, delivery format and possible outcomes with your team.

Would you be available for a brief discussion?"""

    # --------------------------------------------------
    # Response to interest
    # --------------------------------------------------

    def _interest_response(
        self,
        college_name,
        contact_role,
    ):

        greeting = self._greeting(
            contact_role
        )

        return f"""{greeting}

Thank you for your interest in exploring AI training opportunities with us.

We would be happy to discuss the requirements of {college_name} and suggest a suitable workshop or institutional training format covering Generative AI, Agentic AI and Quantum Computing.

Please let us know a convenient time for a brief discussion, and we can take the conversation forward.

Thank you."""

    # --------------------------------------------------
    # Greeting
    # --------------------------------------------------

    @staticmethod
    def _greeting(contact_role):

        if contact_role:
            return (
                f"Dear {contact_role} Team,"
            )

        return "Dear Sir/Madam,"