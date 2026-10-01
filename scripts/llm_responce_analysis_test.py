import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(PROJECT_ROOT))

from backend.agents.response_analysis_agent import ResponseAnalysisAgent


agent = ResponseAnalysisAgent()

test_messages = [
    "Please send us a proposal.",
    "Kindly forward a detailed proposal for the training program.",
    "Can we schedule a meeting next week?",
    "Please call me tomorrow.",
    "Please send more details about the program.",
    "We are interested in this opportunity.",
    "Please contact us next month.",
    "I am not the right person. Please contact the placement officer.",
    "I am currently out of office until Monday.",
    "We are not interested at this time.",
    "Please remove me from your mailing list.",
    "Okay, noted.",
    "Thanks for reaching out. This sounds interesting. Please send us something we can review internally.",

    "Could you share a detailed proposal with the scope and pricing?",

    "We would be happy to discuss this. Let me know when you are available.",

    "I am not handling training programs. Please coordinate with our TPO.",

    "Can you send some information first? We will discuss it with the management.",

    "Not now, please reach out after the semester starts.",

    "Please don't send any further emails.",

    "We are interested, but please send the proposal first.",

    "Could you call me so that we can discuss the proposal?",

    "Thank you for your email. I am currently away and will return on Monday.",

    "We don't have any requirement currently, but maybe we can explore this later.",

    "Okay, we will get back to you.",
]

for message in test_messages:
    category = agent._classify_response(message)

    print("=" * 70)
    print("MESSAGE :", message)
    print("CATEGORY:", category)