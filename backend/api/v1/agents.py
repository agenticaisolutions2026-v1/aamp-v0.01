from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.agents.state import AgentState
from backend.agents.supervisor_agent import SupervisorAgent
from backend.agents.outreach_orchestrator_agent import (
    OutreachOrchestratorAgent,
)

from backend.database.dependencies import get_db

from backend.services.college_persistence_service import (
    CollegePersistenceService,
)

from backend.services.campaign_persistence_service import (
    CampaignPersistenceService,
)

from backend.services.campaign_approval_service import (
    CampaignApprovalService,
)

from backend.services.outreach_persistence_service import (
    OutreachPersistenceService,
)


router = APIRouter()

supervisor = SupervisorAgent()

outreach_orchestrator = OutreachOrchestratorAgent()


class AgentRequest(BaseModel):
    user_query: str


# =========================================================
# Existing endpoint — keep for frontend
# =========================================================

@router.get("/agents")
def get_agents():

    return [
        {
            "id": 1,
            "name": "Supervisor Agent",
            "status": "Running",
        },
        {
            "id": 2,
            "name": "Marketing Agent",
            "status": "Running",
        },
        {
            "id": 3,
            "name": "Analytics Agent",
            "status": "Idle",
        },
    ]


# =========================================================
# Execute complete agent workflow
# =========================================================

@router.post("/agents/execute")
def execute_agent(
    request: AgentRequest,
    db: Session = Depends(get_db),
):

    # -----------------------------------------
    # 1. Create agent state
    # -----------------------------------------

    state = AgentState()

    state.user_query = request.user_query

    # -----------------------------------------
    # 2. Execute Supervisor Agent
    # -----------------------------------------

    result = supervisor.execute(state)

    # -----------------------------------------
    # 3. Save discovered/enriched colleges
    # -----------------------------------------

    saved_colleges = []

    if (
        result.status == "success"
        and isinstance(result.result, dict)
    ):

        colleges = result.result.get(
            "colleges",
            [],
        )

        for college in colleges:

            try:

                saved_college = (
                    CollegePersistenceService.save_college(
                        db=db,
                        enriched_college=college,
                    )
                )

                saved_colleges.append(
                    {
                        "id": saved_college.id,
                        "name": saved_college.name,
                        "website": saved_college.website,
                        "phone": saved_college.phone,
                        "email": saved_college.email,
                    }
                )

            except Exception as exc:

                saved_colleges.append(
                    {
                        "name": college.get(
                            "name",
                            "Unknown",
                        ),
                        "error": str(exc),
                    }
                )

    # -----------------------------------------
    # 4. Save campaign drafts / approvals
    # -----------------------------------------

    saved_campaigns = []

    campaigns = []

    if isinstance(
        result.result,
        dict,
    ):

        campaigns = result.result.get(
            "campaigns",
            [],
        )

    for campaign in campaigns:

        try:

            # ---------------------------------
            # Find matching saved college
            # ---------------------------------

            college_id = None
            college_email = None

            campaign_college_name = (
                campaign.get(
                    "college_name",
                    "",
                )
            )

            for saved_college in saved_colleges:

                if (
                    saved_college.get("name")
                    == campaign_college_name
                ):

                    college_id = (
                        saved_college.get("id")
                    )

                    college_email = (
                        saved_college.get("email")
                    )

                    break

            # ---------------------------------
            # Add college information
            # ---------------------------------

            campaign["college_id"] = college_id

            # ---------------------------------
            # 4A. Evaluate campaign approval
            # ---------------------------------

            lead_score = campaign.get(
                "lead_score",
                0,
            )

            approval = (
                CampaignApprovalService.evaluate(
                    lead_score
                )
            )

            # ---------------------------------
            # 4B. Add Tier information
            # ---------------------------------

            campaign["tier"] = approval["tier"]

            campaign["required_human_approval"] = (
                approval["required_human_approval"]
            )

            campaign["status"] = (
                approval["campaign_status"]
            )

            # ---------------------------------
            # 4C. Auto approval timestamp
            # ---------------------------------

            if (
                approval["approval_status"]
                == "approved"
            ):

                campaign["approved_at"] = (
                    datetime.utcnow()
                )

            else:

                campaign["approved_at"] = None

            # ---------------------------------
            # 4D. Save campaign
            # ---------------------------------

            saved_campaign = (
                CampaignPersistenceService.save_campaign(
                    db=db,
                    campaign_data=campaign,
                )
            )

            # ---------------------------------
            # 4E. Tier 1 Auto Approval
            #
            # Automatically create outreach
            # queue for Tier 1 campaigns.
            # ---------------------------------

            auto_outreach = None
            auto_outreach_error = None

            if (
                approval["approval_status"]
                == "approved"
                and approval["required_human_approval"]
                is False
            ):

                campaign_data = {
                    "campaign_id": saved_campaign.id,
                    "college_id": saved_campaign.college_id,
                    "college_name": (
                        saved_campaign.college_name
                    ),
                    "priority": saved_campaign.priority,
                    "channel": saved_campaign.channel,
                    "subject": saved_campaign.subject,
                    "message": saved_campaign.message,
                    "required_human_approval": False,
                    "approval_status": "approved",
                    "recipient": college_email,
                }

                outreach_state = AgentState()

                outreach_state.result = {
                    "campaign": campaign_data
                }

                try:

                    outreach_result = (
                        outreach_orchestrator.execute(
                            outreach_state
                        )
                    )

                    if (
                        outreach_result.status
                        == "success"
                    ):

                        outreach_data = (
                            outreach_result.result.get(
                                "outreach"
                            )
                        )

                        if outreach_data:

                            auto_outreach = (
                                OutreachPersistenceService.save_outreach(
                                    db=db,
                                    outreach_data=outreach_data,
                                )
                            )

                        else:

                            auto_outreach_error = (
                                "Outreach Orchestrator "
                                "returned no outreach data."
                            )

                    else:

                        auto_outreach_error = (
                            outreach_result.error
                            or "Outreach queue creation failed."
                        )

                except Exception as exc:

                    auto_outreach_error = str(exc)

            # ---------------------------------
            # 4F. Return saved campaign
            # ---------------------------------

            campaign_response = {
                "id": saved_campaign.id,
                "college_id": (
                    saved_campaign.college_id
                ),
                "college_name": (
                    saved_campaign.college_name
                ),
                "channel": (
                    saved_campaign.channel
                ),
                "contact_role": (
                    saved_campaign.contact_role
                ),
                "subject": (
                    saved_campaign.subject
                ),
                "priority": (
                    saved_campaign.priority
                ),
                "lead_score": (
                    saved_campaign.lead_score
                ),
                "tier": (
                    saved_campaign.tier
                ),
                "qualification": (
                    saved_campaign.qualification
                ),
                "status": (
                    saved_campaign.status
                ),
                "required_human_approval": (
                    saved_campaign.required_human_approval
                ),
                "approval_type": (
                    approval["approval_type"]
                ),
                "approval_status": (
                    approval["approval_status"]
                ),
                "reason": (
                    approval["reason"]
                ),
            }

            # ---------------------------------
            # 4G. Add auto outreach information
            # ---------------------------------

            if auto_outreach:

                campaign_response[
                    "outreach"
                ] = {
                    "id": auto_outreach.id,
                    "campaign_id": (
                        auto_outreach.campaign_id
                    ),
                    "college_id": (
                        auto_outreach.college_id
                    ),
                    "channel": (
                        auto_outreach.channel
                    ),
                    "recipient": (
                        auto_outreach.recipient
                    ),
                    "status": (
                        auto_outreach.status
                    ),
                    "next_action": "send",
                    "real_message_sent": False,
                }

            elif auto_outreach_error:

                campaign_response[
                    "outreach"
                ] = {
                    "status": "failed",
                    "error": auto_outreach_error,
                    "real_message_sent": False,
                }

            else:

                campaign_response[
                    "outreach"
                ] = None

            saved_campaigns.append(
                campaign_response
            )

        except Exception as exc:

            saved_campaigns.append(
                {
                    "college_name": campaign.get(
                        "college_name",
                        "Unknown",
                    ),
                    "error": str(exc),
                }
            )

    # -----------------------------------------
    # 5. Return final response
    # -----------------------------------------

    return {
        "user_query": result.user_query,
        "selected_agent": result.selected_agent,
        "status": result.status,

        "result": result.result,

        "saved_colleges": saved_colleges,

        "saved_campaigns": saved_campaigns,

        "error": result.error,
    }