import logging

from backend.agents.base_agent import BaseAgent
from backend.agents.state import AgentState


logger = logging.getLogger(__name__)


class CampaignStrategyAgent(BaseAgent):
    """
    Generate an outreach campaign strategy for a qualified college lead.

    This agent:
    - recommends an outreach channel
    - determines campaign type
    - determines message type
    - generates a campaign objective
    - identifies target audience
    - assigns campaign priority
    - identifies personalization opportunities

    The agent DOES NOT send messages.
    Human approval is mandatory before outreach.
    """

    def execute(self, state: AgentState) -> AgentState:

        try:
            state.status = "running"

            college = self._get_college(state)
            lead = self._get_lead(state)

            if not isinstance(college, dict):
                raise ValueError(
                    "Enriched college must be a dictionary"
                )

            if not isinstance(lead, dict):
                raise ValueError(
                    "Qualified lead must be a dictionary"
                )

            qualification = lead.get("qualification")

            if qualification != "qualified":
                raise ValueError(
                    "Campaign strategy requires a qualified lead"
                )

            college_name = self._get_value(
                college.get("name")
            )

            logger.info(
                "Generating campaign strategy for: %s",
                college_name,
            )

            recommended_channel = (
                self._recommend_channel(college)
            )

            campaign_type = (
                self._determine_campaign_type(
                    college
                )
            )

            message_type = "initial_outreach"

            objective = (
                self._generate_objective(
                    campaign_type
                )
            )

            audience = (
                self._determine_audience(
                    college
                )
            )

            priority = (
                self._determine_priority(
                    lead,
                    college
                )
            )

            personalization = (
                self._identify_personalization(
                    college
                )
            )

            channel_reason = (
                self._channel_reason(
                    college,
                    recommended_channel
                )
            )

            result = {
                "college_name": college_name,
                "campaign_type": campaign_type,
                "message_type": message_type,
                "recommended_channel": recommended_channel,
                "channel_reason": channel_reason,
                "objective": "Explore AI training and workshop opportunities",
                "value_proposition": [
                    "Generative AI training",
                    "Agentic AI training",
                    "Quantum Computing training"
                ],
                "audience": audience,
                "priority": priority,
                "personalization_opportunities": personalization,
                "required_human_approval": True,
            }

            state.campaign_strategies = [result]

            # Backward compatibility
            state.result = result

            state.status = "completed"

            return state

        except Exception as exc:

            logger.exception(
                "Campaign strategy generation failed"
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
    # Extract enrichment value
    # --------------------------------------------------

    @staticmethod
    def _get_value(field):

        if isinstance(field, dict):
            return field.get("value")

        return field

    # --------------------------------------------------
    # Recommend outreach channel
    # --------------------------------------------------

    def _recommend_channel(self, college):

        email = self._get_value(
            college.get("official_email")
        )

        whatsapp = self._get_value(
            college.get("whatsapp")
        )

        contact_form = self._get_value(
            college.get("contact_form")
        )

        linkedin = self._get_value(
            college.get("linkedin")
        )

        phone = self._get_value(
            college.get("official_phone")
        )

        # Highest priority: official institutional email
        if email:
            return "email"

        # WhatsApp only when an approved/public contact exists
        if whatsapp:
            return "whatsapp"

        # Website contact form
        if contact_form:
            return "contact_form"

        # Institutional LinkedIn
        if linkedin:
            return "linkedin"

        # Phone follow-up
        if phone:
            return "phone"

        return "no_channel"

    # --------------------------------------------------
    # Explain channel recommendation
    # --------------------------------------------------

    def _channel_reason(
        self,
        college,
        channel,
    ):

        if channel == "email":
            return (
                "Official institutional email is available."
            )

        if channel == "whatsapp":
            return (
                "Approved/public WhatsApp contact is available."
            )

        if channel == "contact_form":
            return (
                "No higher-priority direct channel was found; "
                "an institutional website contact form is available."
            )

        if channel == "linkedin":
            return (
                "No higher-priority direct channel was found; "
                "an institutional LinkedIn channel is available."
            )

        if channel == "phone":
            return (
                "No higher-priority digital channel was found; "
                "an official institutional phone number is available."
            )

        return (
            "No suitable outreach channel was found "
            "in the available college information."
        )

    # --------------------------------------------------
    # Determine campaign type
    # --------------------------------------------------

    def _determine_campaign_type(self, college):

        workshop = college.get(
            "workshop_training_opportunity"
        )

        training = college.get(
            "training"
        )

        has_workshop = bool(workshop)
        has_training = bool(training)

        if has_workshop and has_training:
            return "institutional_training"

        if has_workshop:
            return "workshop"

        if has_training:
            return "institutional_training"

        return "institutional_training"

    # --------------------------------------------------
    # Generate campaign objective
    # --------------------------------------------------

    def _generate_objective(self, campaign_type):

        if campaign_type == "workshop":
            return (
                "Explore opportunities to conduct "
                "Generative AI, Agentic AI or Quantum "
                "Computing workshops for engineering students."
            )

        if campaign_type == "institutional_training":
            return (
                "Explore institutional training opportunities "
                "for Generative AI, Agentic AI and Quantum Computing."
            )

        return (
            "Explore AI training and workshop opportunities "
            "with the institution."
        )
    

    # --------------------------------------------------
    # Determine target audience
    # --------------------------------------------------

    def _determine_audience(self, college):

        contact_role = self._get_value(
            college.get("contact_role")
        )

        departments = college.get(
            "departments"
        )

        audience = []

        if contact_role:
            audience.append(
                str(contact_role)
            )

        if departments:
            department_values = []

            if isinstance(departments, list):

                for department in departments:

                    value = self._get_value(
                        department
                    )

                    if value:
                        department_values.append(
                            str(value)
                        )

            if department_values:
                audience.append(
                    "Relevant academic departments"
                )

        audience.append(
            "Engineering students"
        )

        return audience

    # --------------------------------------------------
    # Determine priority
    # --------------------------------------------------

    def _determine_priority(
        self,
        lead,
        college,
    ):

        score = lead.get(
            "lead_score",
            0,
        )

        contact_role = self._get_value(
            college.get("contact_role")
        )

        official_email = self._get_value(
            college.get("official_email")
        )

        ai_ml_related = self._get_value(
            college.get("ai_ml_related")
        )

        # High priority:
        # strong score + useful institutional contact
        if (
            score >= 80
            and contact_role
            and (
                official_email
                or ai_ml_related
            )
        ):
            return "high"

        # Medium priority:
        # qualified but weaker supporting evidence
        if score >= 80:
            return "medium"

        return "low"

    # --------------------------------------------------
    # Identify personalization opportunities
    # --------------------------------------------------

    def _identify_personalization(
        self,
        college,
    ):

        personalization = []

        departments = college.get(
            "departments"
        )

        if departments:

            department_values = []

            if isinstance(departments, list):

                for department in departments:

                    value = self._get_value(
                        department
                    )

                    if value:
                        department_values.append(
                            str(value)
                        )

            if department_values:
                personalization.append({
                    "field": "departments",
                    "value": department_values,
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
            college.get("placement_available")
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