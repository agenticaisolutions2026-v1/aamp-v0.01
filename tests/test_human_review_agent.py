from backend.agents.human_review_agent import HumanReviewAgent
from backend.agents.state import AgentState


def create_test_state():
    state = AgentState()

    state.qualified_leads = [
        {
            "college_id": 123,
            "college_name": "SRM University AP",
            "contact_role": "Training and Placement",
            "qualification": "qualified",
            "lead_score": 100,
            "reason": (
                "Strong CSE/AI/ML relevance with "
                "training and placement opportunities."
            ),
        }
    ]

    return state


def test_pending_review():

    agent = HumanReviewAgent()
    state = create_test_state()

    state = agent.execute(state)

    assert state.approval_required is True
    assert state.approval_status == "pending"
    assert state.status == "waiting_for_approval"

    print("\nTEST 1 - Pending Review")
    print("Approval required :", state.approval_required)
    print("Approval status   :", state.approval_status)
    print("Status            :", state.status)


def test_approved_review():

    agent = HumanReviewAgent()
    state = create_test_state()

    state = agent.execute(state)

    state = agent.approve(
        state,
        approved_by="admin",
        reason=(
            "Relevant AI audience and "
            "placement contact."
        ),
    )

    assert state.approval_required is True
    assert state.approval_status == "approved"
    assert state.reviewed_by == "admin"
    assert state.status == "approved"

    print("\nTEST 2 - Approved")
    print("Approval required :", state.approval_required)
    print("Approval status   :", state.approval_status)
    print("Reviewed by       :", state.reviewed_by)
    print("Reason            :", state.approval_reason)
    print("Status            :", state.status)


def test_rejected_review():

    agent = HumanReviewAgent()
    state = create_test_state()

    state = agent.execute(state)

    state = agent.reject(
        state,
        rejected_by="admin",
        reason=(
            "No current training requirement."
        ),
    )

    assert state.approval_required is True
    assert state.approval_status == "rejected"
    assert state.reviewed_by == "admin"
    assert state.status == "rejected"

    print("\nTEST 3 - Rejected")
    print("Approval required :", state.approval_required)
    print("Approval status   :", state.approval_status)
    print("Rejected by       :", state.reviewed_by)
    print("Reason            :", state.approval_reason)
    print("Status            :", state.status)


if __name__ == "__main__":

    test_pending_review()
    test_approved_review()
    test_rejected_review()

    print("\n" + "=" * 70)
    print("HUMAN REVIEW TESTS PASSED")
    print("=" * 70)