from backend.agents.base_agent import BaseAgent
from backend.agents.state import AgentState


class FollowUpAgent(BaseAgent):

    def execute(self, state: AgentState):

        state.status = "completed"

        college = state.enriched_results[0] if state.enriched_results else {}

        message = {
            "college_id": college.get("id"),
            "college_name": college.get("name"),
            "message_type": "follow_up",
            "subject": "Follow-up regarding our AI/ML training proposal",
            "message": (
                "Dear Sir/Madam,\n\n"
                "We are following up on our earlier communication "
                "regarding AI/ML training and workshop opportunities "
                "for your students.\n\n"
                "Please let us know if your institution would be "
                "interested in discussing this further.\n\n"
                "Regards,\n"
                "AAMP Team"
            ),
            "status": "draft",
            "required_human_approval": True,
        }

        state.result = message

        return state