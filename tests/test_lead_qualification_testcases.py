from backend.agents.lead_qualification_agent import LeadQualificationAgent
from backend.agents.state import AgentState


def create_state(
    lead_score,
    college_name="Test College",
    ai_ml_related=None,
    placement_available=None,
):
    state = AgentState()

    state.enriched_results = [
        {
            "name": {
                "value": college_name
            },
            "ai_ml_related": {
                "value": ai_ml_related
            },
            "placement_available": {
                "value": placement_available
            },
            "contact_role": {
                "value": "Training and Placement"
            },
            "official_email": {
                "value": "placement@testcollege.edu"
            },
            "official_phone": {
                "value": None
            },
            "contact_page": {
                "value": "https://testcollege.edu/contact"
            },
        }
    ]

    state.scores = [
        {
            "score": lead_score
        }
    ]

    return state


# ============================================================
# Test 1 - Strong College
# ============================================================

def test_strong_college():

    agent = LeadQualificationAgent()

    state = create_state(
        lead_score=90,
        college_name="Strong AI College",
        ai_ml_related=True,
        placement_available=True,
    )

    state = agent.execute(state)

    lead = state.qualified_leads[0]

    assert lead["lead_score"] == 90
    assert lead["qualification"] == "qualified"

    print("\nTEST 1 - Strong College")
    print("Lead score   :", lead["lead_score"])
    print("Qualification:", lead["qualification"])


# ============================================================
# Test 2 - Exact Qualified Boundary
# Score = 80
# ============================================================

def test_qualified_boundary():

    agent = LeadQualificationAgent()

    state = create_state(
        lead_score=80,
        college_name="Qualified Boundary College",
        ai_ml_related=True,
        placement_available=True,
    )

    state = agent.execute(state)

    lead = state.qualified_leads[0]

    assert lead["lead_score"] == 80
    assert lead["qualification"] == "qualified"

    print("\nTEST 2 - Qualified Boundary")
    print("Lead score   :", lead["lead_score"])
    print("Qualification:", lead["qualification"])


# ============================================================
# Test 3 - Moderate College
# ============================================================

def test_moderate_college():

    agent = LeadQualificationAgent()

    state = create_state(
        lead_score=70,
        college_name="Moderate College",
        ai_ml_related=True,
        placement_available=True,
    )

    state = agent.execute(state)

    lead = state.qualified_leads[0]

    assert lead["lead_score"] == 70
    assert lead["qualification"] == "needs_review"

    print("\nTEST 3 - Moderate College")
    print("Lead score   :", lead["lead_score"])
    print("Qualification:", lead["qualification"])


# ============================================================
# Test 4 - Exact Needs Review Boundary
# Score = 60
# ============================================================

def test_needs_review_boundary():

    agent = LeadQualificationAgent()

    state = create_state(
        lead_score=60,
        college_name="Review Boundary College",
        ai_ml_related=True,
        placement_available=True,
    )

    state = agent.execute(state)

    lead = state.qualified_leads[0]

    assert lead["lead_score"] == 60
    assert lead["qualification"] == "needs_review"

    print("\nTEST 4 - Needs Review Boundary")
    print("Lead score   :", lead["lead_score"])
    print("Qualification:", lead["qualification"])


# ============================================================
# Test 5 - Exact Low Priority Boundary
# Score = 59
# ============================================================

def test_low_priority_boundary():

    agent = LeadQualificationAgent()

    state = create_state(
        lead_score=59,
        college_name="Low Priority Boundary College",
        ai_ml_related=False,
        placement_available=False,
    )

    state = agent.execute(state)

    lead = state.qualified_leads[0]

    assert lead["lead_score"] == 59
    assert lead["qualification"] == "low_priority"

    print("\nTEST 5 - Low Priority Boundary")
    print("Lead score   :", lead["lead_score"])
    print("Qualification:", lead["qualification"])


# ============================================================
# Test 6 - Missing Information
# ============================================================

def test_missing_information():

    agent = LeadQualificationAgent()

    state = create_state(
        lead_score=70,
        college_name="Missing Information College",
        ai_ml_related=None,
        placement_available=None,
    )

    state = agent.execute(state)

    lead = state.qualified_leads[0]

    assert state.status == "completed"

    assert (
        state.enriched_results[0]["ai_ml_related"]["value"]
        is None
    )

    assert (
        state.enriched_results[0]["placement_available"]["value"]
        is None
    )

    assert lead["lead_score"] == 70
    assert lead["qualification"] == "needs_review"

    print("\nTEST 6 - Missing Information")
    print("College       :", lead["college_name"])
    print("AI/ML program :", state.enriched_results[0]["ai_ml_related"]["value"])
    print("Placement     :", state.enriched_results[0]["placement_available"]["value"])
    print("Lead score    :", lead["lead_score"])
    print("Qualification :", lead["qualification"])


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":

    test_strong_college()
    test_qualified_boundary()
    test_moderate_college()
    test_needs_review_boundary()
    test_low_priority_boundary()
    test_missing_information()

    print("\n" + "=" * 70)
    print("ALL LEAD QUALIFICATION TEST CASES PASSED")
    print("=" * 70)