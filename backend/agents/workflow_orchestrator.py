from backend.agents.state import AgentState
from backend.agents.campaign_strategy_agent import CampaignStrategyAgent
from backend.agents.personalization_agent import PersonalizationAgent
from backend.services.campaign_service import CampaignService


class WorkflowOrchestrator:

    def __init__(self):
        self.strategy_agent = CampaignStrategyAgent()
        self.personalization_agent = PersonalizationAgent()
        self.campaign_service = CampaignService()

    # ==========================================================
    # Convert PostgreSQL College model to dictionary
    # ==========================================================

    @staticmethod
    def _college_to_dict(college) -> dict:
        """
        Convert the SQLAlchemy College model into the dictionary
        format expected by CampaignStrategyAgent and
        PersonalizationAgent.

        The College record contains the already enriched data
        stored in PostgreSQL.
        """

        return {
            "id": college.id,
            "name": college.name,
            "website": college.website,
            "state": college.state,
            "city": college.city,
            "address": college.address,

            # Contact information
            "official_email": college.official_email,
            "official_phone": college.official_phone,
            "contact_role": college.contact_role,
            "contact_form": college.contact_form,
            "whatsapp": college.whatsapp,
            "linkedin": college.linkedin,

            # Academic information
            "departments": college.departments,
            "programs": college.programs,

            # AI relevance
            "ai_ml_related": college.ai_ml_related,
            "generative_ai_related": college.generative_ai_related,
            "agentic_ai_related": college.agentic_ai_related,

            # Institutional information
            "placement_page": college.placement_page,
            "contact_page": college.contact_page,
            "innovation": college.innovation,
            "entrepreneurship": college.entrepreneurship,
            "clubs_events": college.clubs_events,
            "training": college.training,
            "workshop_training_opportunity": (
                college.workshop_training_opportunity
            ),
            "placement_available": college.placement_available,

            # Verification / provenance
            "source_url": college.source_url,
            "sources": college.sources,
            "missing_fields": college.missing_fields,
            "errors": college.errors,

            # Other database fields
            "relevance_score": college.relevance_score,
            "status": college.status,
        }

    # ==========================================================
    # Process one college
    # ==========================================================

    def process_college(
        self,
        state: AgentState,
        college: dict,
        lead: dict,
        campaigns: list[dict],
    ) -> AgentState:

        # Use the fully enriched college data from PostgreSQL
        state.enriched_results = [college]

        # Use already qualified/scored lead data from PostgreSQL
        state.qualified_leads = [lead]

        # ------------------------------------------------------
        # Active campaign → do not create another campaign
        # ------------------------------------------------------

        active_campaigns = [
            campaign
            for campaign in campaigns
            if campaign.get("status") in [
                "draft",
                "approved",
                "sent",
                "replied",
            ]
        ]

        if active_campaigns:
            state.status = "skipped"
            state.result = {
                "college_id": college.get("id"),
                "college_name": college.get("name"),
                "action": "skip",
                "reason": "Active campaign already exists",
                "campaigns": active_campaigns,
            }
            return state

        # ------------------------------------------------------
        # Closed campaign → human decision required
        # ------------------------------------------------------

        closed_campaigns = [
            campaign
            for campaign in campaigns
            if campaign.get("status") == "closed"
        ]

        if closed_campaigns:
            state.status = "waiting"
            state.result = {
                "college_id": college.get("id"),
                "college_name": college.get("name"),
                "action": "human_decision",
                "reason": (
                    "Previous campaign is closed. "
                    "Human decision required for a new campaign."
                ),
                "closed_campaigns": closed_campaigns,
                "create_new_campaign_available": True,
            }
            return state

        # ======================================================
        # Qualification Gate
        # ======================================================

        qualification = lead.get("qualification")

        # ------------------------------------------------------
        # 1. Qualified → continue automatically
        # ------------------------------------------------------

        if qualification == "qualified":
            pass

        # ------------------------------------------------------
        # 2. Needs Review → stop automatic campaign creation
        # ------------------------------------------------------

        elif qualification == "needs_review":
            state.status = "waiting"
            state.result = {
                "college_id": college.get("id"),
                "college_name": college.get("name"),
                "action": "human_review",
                "reason": (
                    "Lead requires human review before campaign creation"
                ),
                "lead": lead,
            }
            return state

        # ------------------------------------------------------
        # 3. Low Priority → stop workflow
        # ------------------------------------------------------

        elif qualification == "low_priority":
            state.status = "skipped"
            state.result = {
                "college_id": college.get("id"),
                "college_name": college.get("name"),
                "action": "stop",
                "reason": "Lead is low priority",
                "lead": lead,
            }
            return state

        # ------------------------------------------------------
        # Unexpected qualification value
        # ------------------------------------------------------

        else:
            state.status = "failed"
            state.error = (
                f"Unknown lead qualification: {qualification}"
            )

            state.result = {
                "college_id": college.get("id"),
                "college_name": college.get("name"),
                "action": "error",
                "reason": "Unknown lead qualification",
                "qualification": qualification,
                "lead": lead,
            }

            return state

        # ======================================================
        # Campaign Strategy
        # ======================================================

        state = self.strategy_agent.execute(state)

        if state.status == "failed":
            return state

        # ======================================================
        # Personalization
        # ======================================================

        state = self.personalization_agent.execute(state)

        if state.status == "failed":
            return state

        # ======================================================
        # Persist generated campaign as DRAFT
        # ======================================================

        campaign_data = {
            "college_id": college.get("id"),
            "campaign_type": (
                state.campaign_strategies[0]["campaign_type"]
            ),
            "message_type": (
                state.campaign_strategies[0]["message_type"]
            ),
            "channel": (
                state.personalized_messages[0]["channel"]
            ),
            "subject": (
                state.personalized_messages[0]["subject"]
            ),
            "message": (
                state.personalized_messages[0]["message"]
            ),
            "priority": (
                state.personalized_messages[0]["priority"]
            ),
        }

        campaign = self.campaign_service.create_campaign(
            campaign_data
        )

        state.result["campaign_id"] = campaign.id
        state.result["campaign_status"] = campaign.status
        state.result["action"] = "campaign_created"

        return state

    # ==========================================================
    # Process multiple colleges
    # ==========================================================

    def process_colleges(
        self,
        state: AgentState,
        colleges: list[dict],
    ) -> AgentState:

        from sqlalchemy import select

        from backend.database.session import SessionLocal
        from backend.models.lead import Lead
        from backend.models.campaign import Campaign
        from backend.models.college import College

        results = []

        # ------------------------------------------------------
        # Get college IDs from discovery results
        # ------------------------------------------------------

        college_ids = [
            college.get("id")
            for college in colleges
            if college.get("id") is not None
        ]

        if not college_ids:
            state.status = "completed"
            state.result = {
                "count": 0,
                "results": [],
            }
            return state

        # ======================================================
        # Load current database records
        # ======================================================

        with SessionLocal() as session:

            # --------------------------------------------------
            # Leads
            # --------------------------------------------------

            leads = session.execute(
                select(Lead).where(
                    Lead.college_id.in_(college_ids)
                )
            ).scalars().all()

            # --------------------------------------------------
            # Existing campaigns
            # --------------------------------------------------

            campaigns = session.execute(
                select(Campaign).where(
                    Campaign.college_id.in_(college_ids)
                )
            ).scalars().all()

            # --------------------------------------------------
            # IMPORTANT:
            # Load the complete enriched College records.
            # --------------------------------------------------

            colleges_db = session.execute(
                select(College).where(
                    College.id.in_(college_ids)
                )
            ).scalars().all()

        # ======================================================
        # Build lead map
        # ======================================================

        lead_map = {
            lead.college_id: {
                "id": lead.id,
                "college_id": lead.college_id,
                "contact_role": lead.contact_role,
                "qualification": lead.qualification,
                "lead_score": lead.lead_score,
                "reason": lead.reason,
                "priority": lead.priority,
            }
            for lead in leads
        }

        # ======================================================
        # Build enriched college map
        # ======================================================

        college_map = {
            college.id: college
            for college in colleges_db
        }

        # ======================================================
        # Build campaign map
        # ======================================================

        campaign_map = {}

        for campaign in campaigns:

            campaign_map.setdefault(
                campaign.college_id,
                []
            ).append({
                "id": campaign.id,
                "status": campaign.status,
                "campaign_type": campaign.campaign_type,
                "message_type": campaign.message_type,
                "channel": campaign.channel,
                "subject": campaign.subject,
                "priority": campaign.priority,
                "required_approval": campaign.required_approval,
                "approved_at": campaign.approved_at,
            })

        # ======================================================
        # Process each discovered college
        # ======================================================

        for discovered_college in colleges:

            college_id = discovered_college.get("id")

            # --------------------------------------------------
            # Lead must exist
            # --------------------------------------------------

            lead = lead_map.get(college_id)

            if not lead:
                results.append({
                    "college_id": college_id,
                    "college_name": discovered_college.get("name"),
                    "action": "skip",
                    "reason": "No lead record found",
                })
                continue

            # --------------------------------------------------
            # Get complete enriched College record
            # --------------------------------------------------

            college_db = college_map.get(college_id)

            if not college_db:
                results.append({
                    "college_id": college_id,
                    "college_name": discovered_college.get("name"),
                    "action": "skip",
                    "reason": (
                        "College record not found in database"
                    ),
                })
                continue

            # --------------------------------------------------
            # Convert SQLAlchemy College → dictionary
            # --------------------------------------------------

            enriched_college = self._college_to_dict(
                college_db
            )

            # --------------------------------------------------
            # Create state for this college
            # --------------------------------------------------

            college_state = AgentState()

            college_state.user_query = state.user_query
            college_state.category = state.category
            college_state.location = state.location

            # --------------------------------------------------
            # Process using enriched database record
            # --------------------------------------------------

            college_state = self.process_college(
                college_state,
                enriched_college,
                lead,
                campaign_map.get(
                    college_id,
                    [],
                ),
            )

            results.append(
                college_state.result
            )

        # ======================================================
        # Final state
        # ======================================================

        state.status = "completed"

        state.result = {
            "count": len(results),
            "results": results,
        }

        return state