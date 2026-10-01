from backend.agents.state import AgentState
from backend.agents.campaign_strategy_agent import CampaignStrategyAgent
from backend.agents.personalization_agent import PersonalizationAgent


def main():

    state = AgentState()

    # --------------------------------------------------
    # Sample enriched college
    # --------------------------------------------------

    state.enriched_results = [
        {
            "name": {
                "value": "SRM University AP",
                "source": "http://srmap.edu.in/"
            },

            "city": {
                "value": "Guntur",
                "source": None
            },

            "state": {
                "value": "Andhra Pradesh",
                "source": None
            },

            "departments": [
                {
                    "value": "Computer Science and Engineering",
                    "source": "https://www.srmap.edu.in/seas/computer-science-and-engineering"
                },
                {
                    "value": "Artificial Intelligence and Machine Learning",
                    "source": "https://www.srmap.edu.in/seas/computer-science-and-engineering"
                },
                {
                    "value": "Electrical and Electronics Engineering",
                    "source": "https://www.srmap.edu.in?p=12051"
                }
            ],

            "programs": [
                {
                    "value": "B.Tech",
                    "source": "https://www.srmap.edu.in/seas/computer-science-and-engineering/b-tech-cse-ai-and-future-technologies-programme"
                }
            ],

            "ai_ml_related": {
                "value": True,
                "source": "https://www.srmap.edu.in/seas/computer-science-and-engineering"
            },

            "generative_ai_related": {
                "value": True,
                "source": "https://smcedocpa.srmap.edu.in/crcs/training"
            },

            "agentic_ai_related": {
                "value": False,
                "source": None
            },

            "official_email": {
                "value": "admissions@srmap.edu.in",
                "source": "https://www.srmap.edu.in/contact-us"
            },

            "official_phone": {
                "value": "863-2343000",
                "source": "https://www.srmap.edu.in/contact-us"
            },

            "training": [
                {
                    "value": "https://www.srmap.edu.in/crcs/training",
                    "source": "https://www.srmap.edu.in/crcs/training"
                }
            ],

            "workshop_training_opportunity": [
                {
                    "value": "https://www.srmap.edu.in/life-at-srmap/student-activities-and-workshops",
                    "source": "https://www.srmap.edu.in/life-at-srmap/student-activities-and-workshops"
                }
            ],

            "placement_available": {
                "value": True,
                "source": "https://www.srmap.edu.in/news/srm-university-ap-celebrates-the-exorbitant-success-in-maiden-batch-placement-2021"
            },

            "contact_role": {
                "value": "Training and Placement",
                "source": "https://www.srmap.edu.in/news/srm-university-ap-celebrates-the-exorbitant-success-in-maiden-batch-placement-2021"
            },

            "contact_form": {
                "value": True,
                "source": "https://www.srmap.edu.in/contact-us"
            },

            "whatsapp": {
                "value": None,
                "source": None
            },

            "linkedin": {
                "value": None,
                "source": None
            }
        }
    ]

    # --------------------------------------------------
    # Qualified lead
    # --------------------------------------------------

    state.qualified_leads = [
    {
        "college_name": "SRM University AP",
        "contact_role": "Training and Placement",
        "qualification": "qualified",
        "lead_score": 87,
        "reason": "Strong CSE/AI audience..."
    }
]

    # --------------------------------------------------
    # Step 1: Campaign Strategy
    # --------------------------------------------------

    strategy_agent = CampaignStrategyAgent()
    state = strategy_agent.execute(state)

    print("\n=== Campaign Strategy ===")
    print(state.result)


    # --------------------------------------------------
    # Step 2: Personalization
    # --------------------------------------------------

    personalization_agent = PersonalizationAgent()
    state = personalization_agent.execute(state)

    print("\n=== Personalization ===")
    print("Status:", state.status)
    print("Error:", state.error)

    print("\nPersonalized Message:")

    for key, value in state.personalized_messages[0].items():
        print(f"\n{key}:")
        print(value)


if __name__ == "__main__":
    main()