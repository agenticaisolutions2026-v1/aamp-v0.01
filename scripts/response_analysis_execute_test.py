from backend.agents.response_analysis_agent import ResponseAnalysisAgent
from backend.agents.state import AgentState


agent = ResponseAnalysisAgent()


def test_response(message: str):
    print("\n" + "=" * 70)
    print("MESSAGE:")
    print(message)
    print("-" * 70)

    state = AgentState()
    state.incoming_response = message

    state = agent.execute(state)

    print("Status           :", state.status)
    print("Response Category:", state.response_category)
    print("Next Action      :", state.next_action)
    print(
        "Follow-up Hint   :",
        getattr(state, "follow_up_hint", None)
    )

    print("Result           :", state.result)

    if getattr(state, "error", None):
        print("Error            :", state.error)


# ==================================================
# TEST 1 — ASK_LATER
# ==================================================

test_response(
    "Please contact us in 2 days."
)


# ==================================================
# TEST 2 — OUT_OF_OFFICE
# ==================================================

test_response(
    "I am currently out of office. "
    "I will be available next week."
)


# ==================================================
# TEST 3 — INTERESTED
# ==================================================

test_response(
    "We are interested in exploring AI training "
    "opportunities for our students."
)