from backend.agents.response_analysis_agent import ResponseAnalysisAgent
from backend.agents.state import AgentState


agent = ResponseAnalysisAgent()


test_messages = [
    "Yes, we are interested. Please send the proposal.",
    "Thank you, but we are not interested.",
    "Please send the course details and pricing.",
    "Please call me tomorrow to discuss this.",
    "I am not responsible for training. Please contact our placement officer.",
    "Please don't contact us again.",
    "I received your email.",
]


for message in test_messages:

    state = AgentState()

    state.incoming_response = message

    result_state = agent.execute(state)

    print("=" * 70)
    print(f"Response : {message}")
    print(f"Category : {result_state.response_category}")
    print(f"Action   : {result_state.next_action}")
    print(f"Status   : {result_state.status}")