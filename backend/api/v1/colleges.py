from fastapi import APIRouter, HTTPException, Query

from backend.services.college_search_service import (
    CollegeSearchService,
)
from backend.database.session import SessionLocal
from backend.models import College, Lead, Campaign
from backend.agents.state import AgentState
from backend.agents.workflow_orchestrator import WorkflowOrchestrator


router = APIRouter()

college_search_service = CollegeSearchService()
workflow_orchestrator = WorkflowOrchestrator()


# =========================================================
# College Search
# =========================================================

@router.get("/colleges/search")
def search_colleges(
    state: str | None = Query(
        default=None,
        description="State name, for example Andhra Pradesh",
    ),
    priority: str | None = Query(
        default=None,
        description="Lead priority: high, medium, or low",
    ),
    min_score: float | None = Query(
        default=None,
        description="Return colleges with lead score above this value",
    ),
    max_score: float | None = Query(
        default=None,
        description="Return colleges with lead score below this value",
    ),
):
    """
    Search colleges with optional lead filters.

    Returns complete college details together with
    lead details when available.
    """

    try:
        results = college_search_service.search_colleges(
            state=state,
            priority=priority,
            min_score=min_score,
            max_score=max_score,
        )

        return {
            "count": len(results),
            "results": results,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =========================================================
# College Overview
# =========================================================

@router.get("/colleges/overview")
def get_college_overview():

    try:
        results = college_search_service.get_college_overview()

        return {
            "count": len(results),
            "results": results,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load college overview: {exc}",
        )

# =========================================================
# Get College By ID
# =========================================================

@router.get("/colleges/{college_id}")
def get_college_by_id(college_id: int):
    """
    Return complete college details by college ID.
    """

    with SessionLocal() as session:

        college = session.query(College).filter(
            College.id == college_id
        ).first()

        if not college:
            raise HTTPException(
                status_code=404,
                detail="College not found.",
            )

        return {
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
            "generative_ai_related": college.generative_ai_related,
            "agentic_ai_related": college.agentic_ai_related,

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
            "placement_available": college.placement_available,

            "sources": college.sources,
            "missing_fields": college.missing_fields,
            "errors": college.errors,
        }


# =========================================================
# Approve Lead
# =========================================================

@router.post("/colleges/{college_id}/lead/approve")
def approve_lead(college_id: int):
    """
    Approve a needs_review lead.

    The lead is moved to qualified status and resumes
    the campaign-generation workflow:

        Campaign Strategy
                ↓
        Personalization
                ↓
              DRAFT
    """

    with SessionLocal() as session:

        # -------------------------------------------------
        # Get college
        # -------------------------------------------------

        college = session.query(College).filter(
            College.id == college_id
        ).first()

        if not college:
            raise HTTPException(
                status_code=404,
                detail="College not found.",
            )

        # -------------------------------------------------
        # Get lead
        # -------------------------------------------------

        lead = session.query(Lead).filter(
            Lead.college_id == college_id
        ).first()

        if not lead:
            raise HTTPException(
                status_code=404,
                detail="Lead not found.",
            )

        # -------------------------------------------------
        # Validate qualification
        # -------------------------------------------------

        if lead.qualification != "needs_review":
            raise HTTPException(
                status_code=400,
                detail=(
                    "Only leads with 'needs_review' qualification "
                    "can be approved."
                ),
            )

        # -------------------------------------------------
        # Get existing campaigns
        # -------------------------------------------------

        existing_campaigns = session.query(Campaign).filter(
            Campaign.college_id == college_id
        ).all()

        campaigns_data = [
            {
                "id": campaign.id,
                "status": campaign.status,
                "campaign_type": campaign.campaign_type,
                "message_type": campaign.message_type,
                "channel": campaign.channel,
                "subject": campaign.subject,
                "priority": campaign.priority,
                "required_approval": campaign.required_approval,
                "approved_at": campaign.approved_at,
            }
            for campaign in existing_campaigns
        ]

        # -------------------------------------------------
        # Approve lead
        # -------------------------------------------------

        lead.qualification = "qualified"

        session.commit()
        session.refresh(lead)

        # -------------------------------------------------
        # Build college data
        # -------------------------------------------------

        college_data = {
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
            "generative_ai_related": college.generative_ai_related,
            "agentic_ai_related": college.agentic_ai_related,

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
            "placement_available": college.placement_available,

            "sources": college.sources,
            "missing_fields": college.missing_fields,
            "errors": college.errors,
        }

        # -------------------------------------------------
        # Build lead data
        # -------------------------------------------------

        lead_data = {
            "id": lead.id,
            "college_id": lead.college_id,
            "contact_role": lead.contact_role,
            "qualification": lead.qualification,
            "lead_score": lead.lead_score,
            "reason": lead.reason,
            "priority": lead.priority,
        }

    # -----------------------------------------------------
    # Resume campaign-generation workflow
    # -----------------------------------------------------

    state = AgentState()

    state.enriched_results = [college_data]
    state.qualified_leads = [lead_data]

    result = workflow_orchestrator.process_college(
        state=state,
        college=college_data,
        lead=lead_data,
        campaigns=campaigns_data,
    )

    if result.status == "failed":
        raise HTTPException(
            status_code=500,
            detail=result.error or result.result,
        )

    if result.status == "waiting":
        raise HTTPException(
            status_code=400,
            detail=result.result,
        )

    return {
        "message": "Lead approved successfully.",
        "college_id": college_id,
        "lead_id": lead.id,
        "qualification": lead.qualification,
        "result": result.result,
    }


# =========================================================
# Reject Lead
# =========================================================

@router.post("/colleges/{college_id}/lead/reject")
def reject_lead(college_id: int):
    """
    Reject a needs_review lead.

    The lead is moved to low_priority and will not
    automatically enter campaign generation.
    """

    with SessionLocal() as session:

        lead = session.query(Lead).filter(
            Lead.college_id == college_id
        ).first()

        if not lead:
            raise HTTPException(
                status_code=404,
                detail="Lead not found.",
            )

        if lead.qualification != "needs_review":
            raise HTTPException(
                status_code=400,
                detail=(
                    "Only leads with 'needs_review' qualification "
                    "can be rejected."
                ),
            )

        lead.qualification = "low_priority"

        session.commit()
        session.refresh(lead)

        return {
            "message": "Lead rejected.",
            "college_id": college_id,
            "lead_id": lead.id,
            "qualification": lead.qualification,
        }