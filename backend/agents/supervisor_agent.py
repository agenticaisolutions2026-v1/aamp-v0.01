from .registry import AgentRegistry


class SupervisorAgent:

    def __init__(self):
        self.registry = AgentRegistry()

    def execute(self, state):

        query = state.user_query.lower()

        # -----------------------------------------
        # Marketing
        # -----------------------------------------

        if "marketing" in query:

            agent = self.registry.get_agent(
                "MarketingAgent"
            )

            state.selected_agent = (
                agent.__class__.__name__
            )

            return agent.execute(state)

        # -----------------------------------------
        # Analytics
        # -----------------------------------------

        elif "analytics" in query:

            agent = self.registry.get_agent(
                "AnalyticsAgent"
            )

            state.selected_agent = (
                agent.__class__.__name__
            )

            return agent.execute(state)

        # -----------------------------------------
        # CRM
        # -----------------------------------------

        elif "crm" in query:

            agent = self.registry.get_agent(
                "CRMAgent"
            )

            state.selected_agent = (
                agent.__class__.__name__
            )

            return agent.execute(state)

        # -----------------------------------------
        # College workflow
        # -----------------------------------------

        elif any(
            keyword in query
            for keyword in [
                "college",
                "colleges",
                "university",
                "universities",
                "engineering",
            ]
        ):

            # =====================================
            # 1. College Discovery + Enrichment
            # =====================================

            discovery_agent = (
                self.registry.get_agent(
                    "CollegeDiscoveryAgent"
                )
            )

            state.selected_agent = (
                discovery_agent.__class__.__name__
            )

            state = discovery_agent.execute(
                state
            )

            if state.status == "failed":
                return state

            # -------------------------------------
            # Store discovery/enrichment results
            # -------------------------------------

            if isinstance(
                state.result,
                dict,
            ):

                state.college_results = (
                    state.result.get(
                        "colleges",
                        [],
                    )
                )

                state.enriched_results = (
                    state.result.get(
                        "colleges",
                        [],
                    )
                )

            # =====================================
            # 2. College Scoring
            # =====================================

            scoring_agent = (
                self.registry.get_agent(
                    "CollegeScoringAgent"
                )
            )

            state = scoring_agent.execute(
                state
            )

            if state.status == "failed":
                return state

            # =====================================
            # 3. Lead Qualification
            # =====================================

            qualification_agent = (
                self.registry.get_agent(
                    "LeadQualificationAgent"
                )
            )

            state = qualification_agent.execute(
                state
            )

            if state.status == "failed":
                return state

            # =====================================
            # 4. Campaign Strategy
            # =====================================

            campaign_agent = (
                self.registry.get_agent(
                    "CampaignStrategyAgent"
                )
            )

            state = campaign_agent.execute(
                state
            )

            if state.status == "failed":
                return state

            # -------------------------------------
            # Store campaign results
            # -------------------------------------

            if isinstance(
                state.result,
                dict,
            ):

                state.campaigns = (
                    state.result.get(
                        "campaigns",
                        [],
                    )
                )

            else:

                state.campaigns = []

            # =====================================
            # Final workflow result
            # =====================================

            state.result = {

                "colleges": (
                    state.enriched_results
                ),

                "scores": (
                    state.scores
                ),

                "qualified_leads": (
                    state.qualified_leads
                ),

                "campaigns": (
                    state.campaigns
                ),
            }

            state.status = "success"

            return state

        # -----------------------------------------
        # Default Lead Agent
        # -----------------------------------------

        else:

            agent = self.registry.get_agent(
                "LeadAgent"
            )

            state.selected_agent = (
                agent.__class__.__name__
            )

            return agent.execute(state)