from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.agents.campaign_strategy_agent import (
    CampaignStrategyAgent,
)
from backend.agents.personalization_agent import (
    PersonalizationAgent,
)
from backend.agents.state import AgentState
from backend.database.connection import engine
from backend.models import College, Lead
from backend.services.campaign_service import CampaignService


class CollegePipelineService:
    """
    Database-backed campaign generation pipeline.

    Flow:

        Lead + College from PostgreSQL
                    ↓
                AgentState
                    ↓
        CampaignStrategyAgent
                    ↓
        PersonalizationAgent
                    ↓
             Campaign draft

    This service does NOT send messages and does NOT
    automatically approve campaigns.
    """

    def __init__(self):
        self.campaign_strategy_agent = CampaignStrategyAgent()
        self.personalization_agent = PersonalizationAgent()
        self.campaign_service = CampaignService()

    def generate_campaign_for_lead(
        self,
        lead_id: int,
    ):
        """
        Generate a campaign draft for one lead.

        Only qualified leads are allowed to proceed.
        """

        with Session(engine) as session:

            # ----------------------------------
            # Load lead
            # ----------------------------------

            lead = session.scalar(
                select(Lead).where(
                    Lead.id == lead_id
                )
            )

            if lead is None:
                raise ValueError(
                    f"Lead not found: {lead_id}"
                )

            # ----------------------------------
            # Validate qualification
            # ----------------------------------

            if lead.qualification != "qualified":
                raise ValueError(
                    "Campaign generation requires "
                    "a qualified lead. "
                    f"Lead {lead_id} has qualification "
                    f"'{lead.qualification}'."
                )

            # ----------------------------------
            # Load college
            # ----------------------------------

            college = session.scalar(
                select(College).where(
                    College.id == lead.college_id
                )
            )

            if college is None:
                raise ValueError(
                    f"College not found: "
                    f"{lead.college_id}"
                )

            # ----------------------------------
            # Convert DB models → agent dictionaries
            # ----------------------------------

            college_data = self._college_to_dict(
                college
            )

            lead_data = self._lead_to_dict(
                lead
            )

            # ----------------------------------
            # Create AgentState
            # ----------------------------------

            state = AgentState()

            state.enriched_results = [
                college_data
            ]

            state.qualified_leads = [
                lead_data
            ]

            # ----------------------------------
            # Campaign Strategy
            # ----------------------------------

            state = (
                self.campaign_strategy_agent.execute(
                    state
                )
            )

            if state.status == "failed":
                raise RuntimeError(
                    "Campaign strategy generation failed: "
                    f"{state.error}"
                )

            # ----------------------------------
            # Personalization
            # ----------------------------------

            state = (
                self.personalization_agent.execute(
                    state
                )
            )

            if state.status == "failed":
                raise RuntimeError(
                    "Personalization failed: "
                    f"{state.error}"
                )

            # ----------------------------------
            # Persist campaign draft
            # ----------------------------------

            if not state.campaign_results:
                raise RuntimeError(
                    "No campaign was generated."
                )

            campaign_data = state.campaign_results[0]

            self.campaign_service.create_campaign(
                campaign_data
            )

            return campaign_data

    # ==================================================
    # College → dictionary
    # ==================================================

    @staticmethod
    def _college_to_dict(college):

        return {
            "id": college.id,
            "name": college.name,
            "website": college.website,
            "state": college.state,
            "city": college.city,
            "address": college.address,

            "departments": college.departments,
            "programs": college.programs,

            "ai_ml_related": college.ai_ml_related,
            "generative_ai_related": (
                college.generative_ai_related
            ),
            "agentic_ai_related": (
                college.agentic_ai_related
            ),

            "official_email": (
                college.official_email
            ),
            "official_phone": (
                college.official_phone
            ),

            "contact_role": college.contact_role,
            "contact_form": college.contact_form,
            "whatsapp": college.whatsapp,
            "linkedin": college.linkedin,

            "placement_page": (
                college.placement_page
            ),
            "contact_page": college.contact_page,

            "innovation": college.innovation,
            "entrepreneurship": (
                college.entrepreneurship
            ),
            "clubs_events": college.clubs_events,

            "training": college.training,
            "workshop_training_opportunity": (
                college.workshop_training_opportunity
            ),
            "placement_available": (
                college.placement_available
            ),

            "sources": college.sources,
            "missing_fields": college.missing_fields,
            "errors": college.errors,
        }

    # ==================================================
    # Lead → dictionary
    # ==================================================

    @staticmethod
    def _lead_to_dict(lead):

        return {
            "id": lead.id,
            "college_id": lead.college_id,
            "contact_role": lead.contact_role,
            "qualification": lead.qualification,
            "lead_score": lead.lead_score,
            "priority": lead.priority,
            "reason": lead.reason,
        }