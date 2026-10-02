class AgentState:

    def __init__(self):

        # User request
        self.user_query = ""

        # College discovery
        self.category = ""
        self.location = ""

        # Agent information
        self.selected_agent = ""

        # Workflow status
        self.status = "idle"
        self.error = ""

        # College pipeline
        self.college_results = []
        self.enriched_results = []

        # Scoring
        self.scores = []

        # Lead qualification
        self.qualified_leads = []

        # Campaign strategy
        self.campaigns = []

        # Final result
        self.result = {}