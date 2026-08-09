class AgentState:
    def __init__(self):
        self.user_query = ""
        self.selected_agent = ""
        self.status = 'idle'
        self.result = ""
        self.error = ""