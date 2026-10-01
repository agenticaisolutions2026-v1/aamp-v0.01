import re

from sqlalchemy import select, and_

from backend.agents.base_agent import BaseAgent
from backend.agents.state import AgentState
from backend.database.session import SessionLocal
from backend.models import College, Lead, Campaign


class DatabaseQueryAgent(BaseAgent):

    def execute(self, state: AgentState):

        query = state.user_query.strip()

        if not query:
            state.status = "failed"
            state.error = "Query cannot be empty."
            return state

        with SessionLocal() as session:

            # --------------------------------------------------
            # Extract state
            # --------------------------------------------------

            state_names = [
                "Andhra Pradesh",
                "Telangana",
                "Tamil Nadu",
                "Karnataka",
                "Kerala",
                "Maharashtra",
                "Odisha",
                "West Bengal",
                "Delhi",
                "Gujarat",
                "Rajasthan",
                "Madhya Pradesh",
                "Uttar Pradesh",
                "Bihar",
                "Jharkhand",
                "Chhattisgarh",
                "Punjab",
                "Haryana",
            ]

            requested_state = None

            for state_name in state_names:
                if re.search(
                    rf"\b{re.escape(state_name)}\b",
                    query,
                    re.IGNORECASE,
                ):
                    requested_state = state_name
                    break

            # --------------------------------------------------
            # Extract lead score condition
            # --------------------------------------------------

            score_match = re.search(
                r"(?:lead\s*score|leadscore|lead)\s*"
                r"(above|below|over|under|>=|<=|>|<|equal to|=)?\s*"
                r"(\d+(?:\.\d+)?)",
                query,
                re.IGNORECASE
            )

            score_operator = None
            score_value = None

            if score_match:
                score_operator = score_match.group(1)

                if score_operator:
                    score_operator = score_operator.lower()
                else:
                    score_operator = "="

                score_value = float(score_match.group(2))

            # --------------------------------------------------
            # Extract priority
            # --------------------------------------------------

            priorities = [
                priority
                for priority in ["high", "medium", "low"]
                if re.search(
                    rf"\b{priority}\s+priority\b|\bpriority\s+{priority}\b",
                    query,
                    re.IGNORECASE,
                )
            ]

            requested_priority = priorities[0] if priorities else None

            # --------------------------------------------------
            # Department / AI topic detection
            # --------------------------------------------------

            topic_map = {
                "cse": ["cse", "computer science", "computer science engineering"],
                "ece": ["ece", "electronics", "electronics and communication"],
                "ai_ml": ["ai/ml", "ai ml", "artificial intelligence", "machine learning"],
                "generative_ai": ["generative ai", "gen ai"],
                "agentic_ai": ["agentic ai", "agentic"],
            }

            requested_topics = []

            for topic, keywords in topic_map.items():
                if any(
                    re.search(
                        rf"\b{re.escape(keyword)}\b",
                        query,
                        re.IGNORECASE,
                    )
                    for keyword in keywords
                ):
                    requested_topics.append(topic)

            # --------------------------------------------------
            # Contact filter detection
            # --------------------------------------------------

            contact_map = {
                "website": "website",
                "email": "official_email",
                "phone": "official_phone",
                "whatsapp": "whatsapp",
                "linkedin": "linkedin",
                "contact_form": "contact_form",
            }

            requested_contacts = []

            for keyword, field in contact_map.items():
                if re.search(
                    rf"\b{re.escape(keyword)}\b",
                    query,
                    re.IGNORECASE,
                ):
                    requested_contacts.append(field)

            # --------------------------------------------------
            # Specific college search
            # --------------------------------------------------

            specific_college = None

            college_patterns = [
                r"(?:details\s+of|information\s+about)\s+(.+?)(?:\?|$)",
                r"(?:find)\s+(.+?)\s+(?:college|university)\s+(?:in)\s+.+?(?:with)\s+"
                r"(?:email|phone|website|whatsapp|linkedin|contact\s+form)",
                r"(?:is)\s+(.+?)\s+(?:updated|available)",
            ]

            for pattern in college_patterns:
                match = re.search(
                    pattern,
                    query,
                    re.IGNORECASE,
                )

                if match:
                    specific_college = match.group(1).strip()
                    break

            # --------------------------------------------------
            # Base query
            # --------------------------------------------------

            statement = select(College)

            conditions = []

            # --------------------------------------------------
            # State filter
            # --------------------------------------------------

            if requested_state:
                conditions.append(
                    College.state == requested_state
                        
                )

            # --------------------------------------------------
            # Specific college filter
            # --------------------------------------------------

            if specific_college:

                conditions.append(
                    College.name.ilike(
                        f"%{specific_college}%"
                    )
                )


            # --------------------------------------------------
            # Execute query
            # --------------------------------------------------

            if conditions:
                statement = statement.where(and_(*conditions))
            print("DEBUG CONDITIONS:", conditions)
            print("DEBUG SQL:", statement)

            colleges = session.execute(statement).scalars().all()

            print("DEBUG requested_state:", requested_state)
            print("DEBUG requested_topics:", requested_topics)
            print("DEBUG specific_college:", specific_college)
            print("DEBUG SQL colleges:", len(colleges))

            for college in colleges[:3]:
                print("DEBUG COLLEGE:", college.name)
                print("DEBUG AI_ML:", college.ai_ml_related)

            # Python filtering
            filtered_rows = []

            for college in colleges:
                keep = True
                # --------------------------------------------------
                # Lead score / priority filtering
                # --------------------------------------------------

                lead = session.execute(
                    select(Lead)
                    .where(Lead.college_id == college.id)
                ).scalars().first()

                if score_match:
                    if not lead:
                        keep = False
                    elif score_operator in ["above", "over", ">"]:
                        keep &= lead.lead_score > score_value
                    elif score_operator in ["below", "under", "<"]:
                        keep &= lead.lead_score < score_value
                    elif score_operator in [">=", "greater than or equal to"]:
                        keep &= lead.lead_score >= score_value
                    elif score_operator in ["<=", "less than or equal to"]:
                        keep &= lead.lead_score <= score_value
                    elif score_operator in ["=", "equal to"]:
                        keep &= lead.lead_score == score_value

                if requested_priority:
                    if not lead:
                        keep = False
                    else:
                        keep &= (
                            lead.priority.lower() == requested_priority.lower()
                        )


                # ---------- AI / Department filtering ----------
                for topic in requested_topics:

                    if topic == "ai_ml":
                        keep &= bool(
                            college.ai_ml_related
                            and college.ai_ml_related.get("value") is True
                        )

                    elif topic == "generative_ai":
                        keep &= bool(
                            college.generative_ai_related
                            and college.generative_ai_related.get("value") is True
                        )

                    elif topic == "agentic_ai":
                        keep &= bool(
                            college.agentic_ai_related
                            and college.agentic_ai_related.get("value") is True
                        )

                    elif topic == "cse":
                        keep &= any(
                            "computer science" in dept.get("value", "").lower()
                            for dept in (college.departments or [])
                        )

                    elif topic == "ece":
                        keep &= any(
                            "electronics" in dept.get("value", "").lower()
                            for dept in (college.departments or [])
                        )

                # --------------------------------------------------
                # Contact filtering
                # --------------------------------------------------

                if requested_contacts:

                    contact_matches = []

                    for contact_field in requested_contacts:

                        if contact_field == "website":
                            contact_matches.append(
                                bool(college.website)
                            )

                        elif contact_field == "contact":
                            contact_matches.append(
                                bool(
                                    college.official_email
                                    and college.official_email.get("value")
                                )
                                or bool(
                                    college.official_phone
                                    and college.official_phone.get("value")
                                )
                                or bool(
                                    college.contact_form
                                    and college.contact_form.get("value")
                                )
                            )

                        else:
                            contact_data = getattr(
                                college,
                                contact_field,
                                None,
                            )

                            contact_matches.append(
                                bool(
                                    contact_data
                                    and contact_data.get("value")
                                )
                            )

                    # General query: only keep colleges with the requested information
                    if not specific_college:
                        keep &= any(contact_matches)

            # --------------------------------------------------
            # Load lead and campaign data for matched colleges
            # --------------------------------------------------

            rows = []

            for college in colleges:

                lead = session.execute(
                    select(Lead)
                    .where(Lead.college_id == college.id)
                ).scalars().first()

                campaign = session.execute(
                    select(Campaign)
                    .where(Campaign.college_id == college.id)
                    .order_by(Campaign.created_at.desc())
                ).scalars().first()

                rows.append((college, lead, campaign))

            # --------------------------------------------------
            # Build response
            # --------------------------------------------------

            results = []

            for college, lead, campaign in rows:

                results.append({
                    "college": {
                        "id": college.id,
                        "name": college.name,
                        "website": college.website,
                        "state": college.state,
                        "city": college.city,
                        "address": college.address,
                        "official_email": college.official_email,
                        "official_phone": college.official_phone,
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
                        "status": college.status,
                    },
                    "lead": (
                        {
                            "id": lead.id,
                            "lead_score": lead.lead_score,
                            "priority": lead.priority,
                            "qualification": lead.qualification,
                            "contact_role": lead.contact_role,
                            "reason": lead.reason,
                        }
                        if lead
                        else None
                    ),
                    "campaign": (
                        {
                            "id": campaign.id,
                            "status": campaign.status,
                            "campaign_type": campaign.campaign_type,
                            "message_type": campaign.message_type,
                            "channel": campaign.channel,
                            "priority": campaign.priority,
                            "created_at": campaign.created_at,
                        }
                        if campaign
                        else None
                    ),
                })

            # --------------------------------------------------
            # Final state
            # --------------------------------------------------

            state.status = "completed"

            state.result = {
                "query": query,
                "count": len(results),
                "results": results,
            }

            if not results:
                state.result["message"] = (
                    "No information available in the "
                    "AAMP database for this query."
                )

            return state