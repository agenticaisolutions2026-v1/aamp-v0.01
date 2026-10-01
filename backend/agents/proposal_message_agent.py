from backend.agents.base_agent import BaseAgent
from backend.agents.state import AgentState


class ProposalMessageAgent(BaseAgent):

    def execute(self, state: AgentState):

        state.status = "completed"

        college = state.enriched_results[0] if state.enriched_results else {}

        message = {
            "college_id": college.get("id"),
            "college_name": college.get("name"),
            "message_type": "proposal_message",
            "subject": "AI/ML Training & Workshop Proposal",
            "message": (
                "Dear Sir/Madam,\n\n"
                "Thank you for your positive response. "
                "We would be pleased to share our proposal for "
                "an AI/ML training and workshop program for your students.\n\n"
                "We would be happy to discuss the program, requirements, "
                "and possible schedule with your institution.\n\n"
                "Regards,\n"
                "AAMP Team"
            ),
            "status": "draft",
            "required_human_approval": True,
        }

        state.result = message

        return state