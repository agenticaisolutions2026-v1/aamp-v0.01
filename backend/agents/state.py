class AgentState:

    def __init__(self):
        # Existing fields
        self.user_query = ""
        self.category = ""
        self.location = ""
        self.selected_agent = ""

        # Pipeline status
        self.status = "idle"
        self.error = ""

        # Backward compatibility
        self.result = ""

        # AAMP College Pipeline
        self.college_results = []
        self.enriched_results = []
        self.scores = []
        self.qualified_leads = []

        # AAMP Campaign Pipeline
        self.campaign_strategies = []
        self.personalized_messages = []
        self.campaign_results = []

        # AAMP Response Handling
        self.incoming_response = ""
        self.response_category = ""
        self.next_action = ""

        # Human Approval
        self.approval_required = True
        self.approval_status = "pending"
        self.reviewed_by = ""
        self.approval_reason = ""

