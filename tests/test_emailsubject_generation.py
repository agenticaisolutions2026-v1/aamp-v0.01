from backend.agents.personalization_agent import PersonalizationAgent


def main():
    agent = PersonalizationAgent()

    subject = agent._generate_subject(
        college_name="SRM University AP",
        campaign_type="institutional_training",
        message_type="initial_outreach",
    )

    print("=" * 70)
    print("TESTING CAMPAIGN SUBJECT GENERATION")
    print("=" * 70)
    print()
    print("College      :", "SRM University AP")
    print("Message Type :", "initial_outreach")
    print()
    print("Generated Subject:")
    print(subject)
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()