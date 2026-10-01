from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.connection import engine
from backend.models import College, Lead
from sqlalchemy import select

from backend.models import (
    Campaign,
    College,
    ConversationMessage,
    Lead,
)


class CollegeSearchService:
    """
    Retrieves colleges together with their lead information.

    Supported filters:
        - state
        - priority
        - min_score
        - max_score
    """

    VALID_PRIORITIES = {
        "high",
        "medium",
        "low",
    }

    def search_colleges(
        self,
        state: str | None = None,
        priority: str | None = None,
        min_score: float | None = None,
        max_score: float | None = None,
    ) -> list[dict]:

        if priority:
            priority = priority.strip().lower()

            if priority not in self.VALID_PRIORITIES:
                raise ValueError(
                    "Invalid priority. Use high, medium, or low."
                )

        if min_score is not None and max_score is not None:
            if min_score > max_score:
                raise ValueError(
                    "min_score cannot be greater than max_score."
                )

        with Session(engine) as session:

            statement = (
                select(College, Lead)
                .outerjoin(
                    Lead,
                    Lead.college_id == College.id,
                )
            )

            # ------------------------------------------
            # State filter
            # ------------------------------------------

            if state:
                statement = statement.where(
                    College.state.ilike(
                        state.strip()
                    )
                )

            # ------------------------------------------
            # Priority filter
            # ------------------------------------------

            if priority:
                statement = statement.where(
                    Lead.priority == priority
                )

            # ------------------------------------------
            # Minimum score
            # ------------------------------------------

            if min_score is not None:
                statement = statement.where(
                    Lead.lead_score > min_score
                )

            # ------------------------------------------
            # Maximum score
            # ------------------------------------------

            if max_score is not None:
                statement = statement.where(
                    Lead.lead_score < max_score
                )

            statement = statement.order_by(
                Lead.lead_score.desc().nullslast(),
                College.name.asc(),
            )

            results = session.execute(statement).all()

            return [
                self._serialize_result(
                    college,
                    lead,
                )
                for college, lead in results
            ]

    def get_college_overview(self) -> list[dict]:
        """
        Return one overview record per college.

        Includes:
            - college information
            - lead qualification
            - lead score
            - lead priority
            - latest campaign
            - operation status
        """

        with Session(engine) as session:

            colleges = list(
                session.scalars(
                    select(College).order_by(College.name.asc())
                )
            )

            results = []

            for college in colleges:

                # ------------------------------------------
                # Lead
                # ------------------------------------------

                lead = session.scalar(
                    select(Lead)
                    .where(Lead.college_id == college.id)
                    .order_by(
                        Lead.lead_score.desc()
                    )
                )

                # ------------------------------------------
                # Latest campaign
                # ------------------------------------------

                campaign = session.scalar(
                    select(Campaign)
                    .where(
                        Campaign.college_id == college.id
                    )
                    .order_by(
                        Campaign.created_at.desc()
                    )
                )

                operation_status = "No Operation"
                campaign_status = None

                if campaign:

                    # Check whether this campaign ever received
                    # an inbound reply.
                    inbound_message = session.scalar(
                        select(ConversationMessage)
                        .where(
                            ConversationMessage.campaign_id == campaign.id,
                            ConversationMessage.direction == "inbound",
                        )
                        .limit(1)
                    )

                    if inbound_message:
                        operation_status = "Replied"
                    else:
                        operation_status = (
                            campaign.status.capitalize()
                        )
                    campaign_status = campaign.status.capitalize()

                results.append(
                    {
                        "college": {
                            "id": college.id,
                            "name": college.name,
                            "website": college.website,
                            "state": college.state,
                            "city": college.city,
                            "address": college.address,
                            "official_email": college.official_email,
                            "official_phone": college.official_phone,
                            "source_url": college.source_url,
                            "relevance_score": college.relevance_score,
                            "status": college.status,
                        },

                        "lead": (
                            {
                                "id": lead.id,
                                "college_id": lead.college_id,
                                "contact_role": lead.contact_role,
                                "qualification": lead.qualification,
                                "lead_score": lead.lead_score,
                                "priority": lead.priority,
                                "reason": lead.reason,
                                "created_at": lead.created_at,
                                "updated_at": lead.updated_at,
                            }
                            if lead
                            else None
                        ),

                        "campaign": (
                            {
                                "id": campaign.id,
                                "priority": campaign.priority,
                                "status": campaign.status,
                                "channel": campaign.channel,
                                "created_at": campaign.created_at,
                            }
                            if campaign
                            else None
                        ),

                        "operation_status": operation_status,
                        "campaign_status": campaign_status,
                    }
                )

            return results

    @staticmethod
    def _serialize_result(
        college: College,
        lead: Lead | None,
    ) -> dict:

        return {
            "college": {
                "id": college.id,
                "name": college.name,
                "website": college.website,
                "state": college.state,
                "city": college.city,
                "address": college.address,
                "official_email": college.official_email,
                "official_phone": college.official_phone,
                "source_url": college.source_url,
                "relevance_score": college.relevance_score,
                "status": college.status,

                "departments": college.departments,
                "programs": college.programs,

                "ai_ml_related": college.ai_ml_related,
                "generative_ai_related": (
                    college.generative_ai_related
                ),
                "agentic_ai_related": (
                    college.agentic_ai_related
                ),

                "contact_role": college.contact_role,
                "contact_form": college.contact_form,
                "whatsapp": college.whatsapp,
                "linkedin": college.linkedin,

                "placement_page": college.placement_page,
                "contact_page": college.contact_page,

                "innovation": college.innovation,
                "entrepreneurship": college.entrepreneurship,
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
            },

            "lead": (
                {
                    "id": lead.id,
                    "college_id": lead.college_id,
                    "contact_role": lead.contact_role,
                    "qualification": lead.qualification,
                    "lead_score": lead.lead_score,
                    "priority": lead.priority,
                    "reason": lead.reason,
                    "created_at": lead.created_at,
                    "updated_at": lead.updated_at,
                }
                if lead is not None
                else None
            ),
        }