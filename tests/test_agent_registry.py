from backend.agents.registry import AgentRegistry
from backend.agents.human_review_agent import HumanReviewAgent


def test_human_review_agent_registered():

    registry = AgentRegistry()

    agent = registry.get_agent(
        "HumanReviewAgent"
    )

    assert agent is not None
    assert isinstance(
        agent,
        HumanReviewAgent,
    )

    print("\nHumanReviewAgent registered successfully.")


if __name__ == "__main__":

    test_human_review_agent_registered()

    print("\n" + "=" * 70)
    print("AGENT REGISTRY TEST PASSED")
    print("=" * 70)