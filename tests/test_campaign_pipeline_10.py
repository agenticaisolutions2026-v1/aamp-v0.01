import json
from pathlib import Path

from backend.agents.state import AgentState
from backend.agents.campaign_strategy_agent import CampaignStrategyAgent
from backend.agents.personalization_agent import PersonalizationAgent


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "processed"

ENRICHED_FILE = DATA_DIR / "college_enriched_test_10.json"
SCORED_FILE = DATA_DIR / "college_scored_test_10.json"
QUALIFIED_FILE = DATA_DIR / "college_qualified_test_10.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_college_name(record):
    """
    Get college name from different pipeline structures.
    """

    name = record.get("name")

    if isinstance(name, dict):
        return name.get("value")

    if isinstance(name, str):
        return name

    return record.get("college_name")


def main():

    # --------------------------------------------------
    # Load processed pipeline data
    # --------------------------------------------------

    enriched_data = load_json(ENRICHED_FILE)
    scored_data = load_json(SCORED_FILE)
    qualified_data = load_json(QUALIFIED_FILE)

    print("\n" + "=" * 70)
    print("10-COLLEGE CAMPAIGN PIPELINE TEST")
    print("=" * 70)

    print(f"\nEnriched colleges  : {len(enriched_data)}")
    print(f"Scored colleges    : {len(scored_data)}")
    print(f"Qualified leads    : {len(qualified_data)}")

    # --------------------------------------------------
    # Create lookup dictionaries
    # --------------------------------------------------

    scored_by_name = {
        get_college_name(record): record
        for record in scored_data
    }

    qualified_by_name = {
        get_college_name(record): record
        for record in qualified_data
    }

    strategy_agent = CampaignStrategyAgent()
    personalization_agent = PersonalizationAgent()

    campaign_results = []

    # --------------------------------------------------
    # Process each enriched college
    # --------------------------------------------------

    for enriched_college in enriched_data:

        college_name = get_college_name(enriched_college)

        if not college_name:
            print("\nSkipping record with no college name.")
            continue

        # --------------------------------------------------
        # Find qualification
        # --------------------------------------------------

        qualified_lead = qualified_by_name.get(college_name)

        if not qualified_lead:
            print(
                f"\nSkipping: {college_name} "
                f"(no qualification record)"
            )
            continue

        # --------------------------------------------------
        # Only qualified leads continue
        # --------------------------------------------------

        qualification = qualified_lead.get("qualification")

        if qualification != "qualified":
            print("\n" + "-" * 70)
            print(f"Skipping: {college_name}")
            print(f"Qualification      : {qualification}")
            print(f"Lead Score         : {qualified_lead.get('lead_score')}")
            print(f"Contact Role       : {qualified_lead.get('contact_role')}")
            print(f"Reason             : {qualified_lead.get('reason')}")
            continue

        # --------------------------------------------------
        # Create AgentState
        # --------------------------------------------------

        state = AgentState()

        state.enriched_results = [enriched_college]
        state.scores = [
            scored_by_name.get(
                college_name,
                {}
            )
        ]
        state.qualified_leads = [qualified_lead]

        # --------------------------------------------------
        # Campaign Strategy
        # --------------------------------------------------

        state = strategy_agent.execute(state)

        if state.status != "completed":
            print(
                f"\nCampaign strategy failed: "
                f"{college_name}"
            )
            print("Error:", state.error)
            continue

        campaign_strategy = state.campaign_strategies[0]

        # --------------------------------------------------
        # Personalization
        # --------------------------------------------------

        state = personalization_agent.execute(state)

        if state.status != "completed":
            print(
                f"\nPersonalization failed: "
                f"{college_name}"
            )
            print("Error:", state.error)
            continue

        personalized_campaign = (
            state.personalized_messages[0]
        )

        campaign_results.append(
            {
                "college_name": college_name,
                "campaign_strategy": campaign_strategy,
                "personalized_campaign": personalized_campaign,
            }
        )

    # --------------------------------------------------
    # Print summary
    # --------------------------------------------------

    print("\n" + "=" * 70)
    print("CAMPAIGN PIPELINE SUMMARY")
    print("=" * 70)

    print(
        f"\nCampaigns generated: "
        f"{len(campaign_results)}"
    )

    for index, result in enumerate(
        campaign_results,
        start=1,
    ):

        strategy = result["campaign_strategy"]
        campaign = result["personalized_campaign"]

        print("\n" + "-" * 70)
        print(f"{index}. {result['college_name']}")

        print(
            "College ID         :",
            campaign.get("college_id"),
        )

        print(
            "College Name       :",
            campaign.get("college_name"),
        )

        print(
            "City               :",
            campaign.get("city"),
        )

        print(
            "State              :",
            campaign.get("state"),
        )

        print(
            "Priority          :",
            strategy.get("priority"),
        )

        print(
            "Campaign Type     :",
            strategy.get("campaign_type"),
        )

        print(
            "Message Type       :",
            campaign.get("message_type"),
        )

        print(
            "Channel            :",
            strategy.get("recommended_channel"),
        )

        print(
            "Objective          :",
            strategy.get("objective"),
        )

        print(
            "Value Proposition  :",
            strategy.get("value_proposition"),
        )

        print(
            "Audience           :",
            strategy.get("audience"),
        )

        print(
            "Subject            :",
            campaign.get("subject"),
        )

        print(
            "Personalization    :",
            campaign.get("personalization_used"),
        )

        print(
            "Approval Required  :",
            campaign.get("required_human_approval"),
        )

        print(
            "Approval Status    :",
            campaign.get("approval_status"),
        )

        print(
            "Message            :",
            campaign.get("message"),
        )

    print("\n" + "=" * 70)
    print("10-COLLEGE CAMPAIGN PIPELINE TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()