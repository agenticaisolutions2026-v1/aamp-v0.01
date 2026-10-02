from backend.agents.base_agent import BaseAgent
from backend.agents.state import AgentState


class CampaignStrategyAgent(BaseAgent):
    """
    Creates a personalized campaign draft for a qualified
    college lead.

    The strategy considers:
    - college information
    - respondent role
    - available contact channel
    - lead score
    - qualification
    - relevant departments/programs
    - placement/training evidence
    - innovation/entrepreneurship evidence

    The agent creates a DRAFT only.
    It never sends the campaign automatically.
    """

    def execute(
        self,
        state: AgentState,
    ) -> AgentState:

        try:
            state.status = "running"

            leads = state.qualified_leads

            campaigns = []

            for lead in leads:

                campaign = self._create_campaign(
                    lead
                )

                campaigns.append(
                    campaign
                )

            state.result = {
                "campaigns": campaigns,
            }

            state.status = "success"

            return state

        except Exception as exc:

            state.status = "failed"
            state.error = str(exc)

            return state

    # =====================================================
    # Create campaign
    # =====================================================

    def _create_campaign(
        self,
        lead: dict,
    ) -> dict:

        college_name = lead.get(
            "college_name",
            "the college",
        )

        qualification = lead.get(
            "qualification",
            "low_priority",
        )

        lead_score = lead.get(
            "lead_score",
            0,
        )

        priority = lead.get(
            "priority",
            "very_low",
        )

        contact_role = lead.get(
            "contact_role",
            "Institutional Training Coordinator",
        )

        channel = self._recommend_channel(
            lead
        )

        personalization = (
            self._build_personalization(
                lead
            )
        )

        campaign_objective = (
            self._determine_objective(
                contact_role,
                lead,
            )
        )

        subject = self._generate_subject(
            contact_role,
            lead,
        )

        message = self._generate_message(
            college_name=college_name,
            contact_role=contact_role,
            lead=lead,
            personalization=personalization,
        )

        return {
            "college_name": college_name,
            "campaign_type": "institutional_training",
            "recommended_channel": channel,
            "priority": priority,
            "lead_score": lead_score,
            "qualification": qualification,
            "contact_role": contact_role,
            "objective": campaign_objective,
            "subject": subject,
            "message": message,
            "personalization_used": personalization,
            "required_human_approval": True,
            "status": "Draft",
        }

    # =====================================================
    # Recommend communication channel
    # =====================================================

    def _recommend_channel(
        self,
        lead: dict,
    ) -> str:

        official_email = lead.get(
            "official_email"
        )

        approved_whatsapp = lead.get(
            "approved_whatsapp",
            False,
        )

        contact_page = lead.get(
            "contact_page"
        )

        linkedin = lead.get(
            "linkedin"
        )

        official_phone = lead.get(
            "official_phone"
        )

        if official_email:
            return "email"

        if approved_whatsapp:
            return "whatsapp"

        if contact_page:
            return "website_contact_form"

        if linkedin:
            return "linkedin"

        if official_phone:
            return "phone_follow_up"

        return "manual_review"

    # =====================================================
    # Build personalization
    # =====================================================

    def _build_personalization(
        self,
        lead: dict,
    ) -> list:

        personalization = []

        departments = lead.get(
            "departments",
            []
        )

        programs = lead.get(
            "programs",
            []
        )

        placement_page = lead.get(
            "placement_page"
        )

        innovation = lead.get(
            "innovation",
            []
        )

        entrepreneurship = lead.get(
            "entrepreneurship",
            []
        )

        clubs_events = lead.get(
            "clubs_events",
            []
        )

        department_values = (
            self._extract_values(
                departments
            )
        )

        if department_values:
            personalization.append(
                "Relevant departments: "
                + ", ".join(
                    department_values
                )
            )

        program_values = (
            self._extract_values(
                programs
            )
        )

        if program_values:
            personalization.append(
                "Relevant programs: "
                + ", ".join(
                    program_values
                )
            )

        if placement_page:
            personalization.append(
                "Training and placement activity identified"
            )

        if innovation:
            personalization.append(
                "Innovation activity identified"
            )

        if entrepreneurship:
            personalization.append(
                "Entrepreneurship activity identified"
            )

        if clubs_events:
            personalization.append(
                "Technical clubs or events identified"
            )

        return personalization

    # =====================================================
    # Determine campaign objective
    # =====================================================

    def _determine_objective(
        self,
        contact_role: str,
        lead: dict,
    ) -> str:

        role = contact_role.lower()

        if (
            "training and placement"
            in role
        ):
            return (
                "Explore industry-oriented training "
                "and placement-readiness programs "
                "for engineering students."
            )

        if (
            "hod" in role
            or "department" in role
        ):
            return (
                "Explore a department-level technical "
                "workshop or hands-on training program "
                "in emerging technologies."
            )

        if (
            "innovation" in role
            or "incubation" in role
        ):
            return (
                "Explore innovation-focused workshops, "
                "projects and emerging technology "
                "programs for students."
            )

        return (
            "Explore an institutional training or "
            "workshop opportunity in emerging "
            "technologies."
        )

    # =====================================================
    # Generate subject
    # =====================================================

    def _generate_subject(
        self,
        contact_role: str,
        lead: dict,
    ) -> str:

        role = contact_role.lower()

        if (
            "training and placement"
            in role
        ):
            return (
                "Industry-oriented AI training "
                "for student placement readiness"
            )

        if (
            "hod" in role
            or "department" in role
        ):
            return (
                "AI and emerging technology "
                "workshop for your department"
            )

        if (
            "innovation" in role
            or "incubation" in role
        ):
            return (
                "Emerging technology innovation "
                "and student project opportunity"
            )

        return (
            "Institutional training opportunity "
            "in emerging technologies"
        )

    # =====================================================
    # Generate campaign message
    # =====================================================

    def _generate_message(
        self,
        college_name: str,
        contact_role: str,
        lead: dict,
        personalization: list,
    ) -> str:

        role = contact_role.lower()

        personalization_text = (
            self._personalization_sentence(
                personalization
            )
        )

        # -------------------------------------------------
        # Training and Placement Officer
        # -------------------------------------------------

        if (
            "training and placement"
            in role
        ):
            return (
                f"Dear Training and Placement Team,\n\n"
                f"I hope you are doing well.\n\n"
                f"We would like to explore a training "
                f"collaboration with {college_name} "
                f"for engineering students."
                f"{personalization_text}\n\n"
                f"We conduct industry-focused programs "
                f"in Generative AI, Agentic AI and "
                f"Quantum Computing, with hands-on "
                f"learning, real-world use cases and "
                f"practical projects.\n\n"
                f"Our programs help students build "
                f"technical skills, strengthen their "
                f"project portfolios and improve "
                f"internship and placement readiness.\n\n"
                f"We offer flexible formats including "
                f"3-day workshops, 1-week bootcamps and "
                f"customized long-term programs.\n\n"
                f"We would be happy to discuss your "
                f"requirements and share a detailed "
                f"training proposal.\n\n"
                f"Thank you.\n\n"
                f"Regards,\n"
                f"AI & Quantum Training Team"
            )

        # -------------------------------------------------
        # HOD / Department Coordinator
        # -------------------------------------------------

        if (
            "hod" in role
            or "department" in role
        ):
            return (
                f"Dear HOD / Department Coordinator,\n\n"
                f"I hope you are doing well.\n\n"
                f"We would like to explore a technical "
                f"workshop or hands-on training program "
                f"for students at {college_name}."
                f"{personalization_text}\n\n"
                f"Our programs focus on Generative AI, "
                f"Agentic AI and Quantum Computing, with "
                f"practical learning and industry-oriented "
                f"projects.\n\n"
                f"We would be happy to discuss a "
                f"department-specific session aligned "
                f"with your students' academic and "
                f"project requirements.\n\n"
                f"Thank you.\n\n"
                f"Regards,\n"
                f"AI & Quantum Training Team"
            )

        # -------------------------------------------------
        # Innovation / Incubation Cell
        # -------------------------------------------------

        if (
            "innovation" in role
            or "incubation" in role
        ):
            return (
                f"Dear Innovation / Incubation Team,\n\n"
                f"I hope you are doing well.\n\n"
                f"We would like to explore an "
                f"emerging-technology initiative "
                f"with {college_name}."
                f"{personalization_text}\n\n"
                f"We can conduct hands-on programs "
                f"around Generative AI, Agentic AI "
                f"and Quantum Computing, including "
                f"student projects, innovation "
                f"workshops and practical sessions.\n\n"
                f"We would be glad to discuss a "
                f"possible collaboration with your "
                f"innovation ecosystem.\n\n"
                f"Thank you.\n\n"
                f"Regards,\n"
                f"AI & Quantum Training Team"
            )

        # -------------------------------------------------
        # Institutional Training Coordinator
        # -------------------------------------------------

        return (
            f"Dear Institutional Training Coordinator,\n\n"
            f"I hope you are doing well.\n\n"
            f"We would like to explore an "
            f"institutional training opportunity "
            f"with {college_name}."
            f"{personalization_text}\n\n"
            f"We offer practical programs in "
            f"Generative AI, Agentic AI and "
            f"Quantum Computing for engineering "
            f"students.\n\n"
            f"We would be happy to understand "
            f"your requirements and discuss a "
            f"suitable workshop or training "
            f"engagement.\n\n"
            f"Thank you.\n\n"
            f"Regards,\n"
            f"AI & Quantum Training Team"
        )

    # =====================================================
    # Personalization sentence
    # =====================================================

    @staticmethod
    def _personalization_sentence(
        personalization: list,
    ) -> str:

        if not personalization:
            return ""

        return (
            "\n\nBased on the information "
            "available about your institution, "
            "we noted the following relevant "
            "areas: "
            + "; ".join(
                personalization
            )
            + "."
        )

    # =====================================================
    # Extract values from enrichment data
    # =====================================================

    @staticmethod
    def _extract_values(
        values,
    ) -> list:

        result = []

        for value in values:

            if isinstance(
                value,
                dict,
            ):
                value = value.get(
                    "value"
                )

            if value:
                result.append(
                    str(value)
                )

        return result