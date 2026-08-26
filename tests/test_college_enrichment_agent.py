from backend.agents.college_enrichment_agent import (
    CollegeEnrichmentAgent,
)
from backend.agents.state import AgentState


def main():

    state = AgentState()

    state.user_query = (
        "Enrich GITAM Institute of Technology"
    )

    state.result = {
        "name": "SVCE – Sri Venkateswara College of Engineering, Tirupati",
        "website": "https://www.svce.ac.in",
        "state": "Andhra Pradesh",
        "city": "Tirupati",
        "address": None,
        "source_url": "https://www.svce.ac.in",
    }

    agent = CollegeEnrichmentAgent()

    result = agent.execute(state)

    print("=" * 80)
    print("COLLEGE ENRICHMENT AGENT TEST")
    print("=" * 80)

    print("Status:", result.status)
    print("Error:", result.error)

    print("\nStructured Result:")

    print(result.result)


if __name__ == "__main__":
    main()