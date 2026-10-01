import logging
from backend.config.settings import GROQ_API_KEY
from langchain_groq import ChatGroq

import json

from backend.agents.base_agent import BaseAgent
from backend.agents.state import AgentState


logger = logging.getLogger(__name__)

class ResponseAnalysisAgent(BaseAgent):
    """
    Analyze an incoming college response.

    This agent uses Groq LLM for semantic response classification.
    """

    RESPONSE_CATEGORIES = [
        "REQUEST_PROPOSAL",
        "REQUEST_MEETING",
        "REQUEST_CALL",
        "NEEDS_INFORMATION",
        "INTERESTED",
        "ASK_LATER",
        "NOT_INTERESTED",
        "WRONG_CONTACT",
        "OUT_OF_OFFICE",
        "UNCLEAR",
        "OPT_OUT",
    ]

    def __init__(self):
        super().__init__()

        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model="openai/gpt-oss-20b",
            temperature=0,
        )

    # ==================================================
    # Execute
    # ==================================================

    def execute(self, state: AgentState) -> AgentState:

        try:

            state.status = "running"

            # ------------------------------------------
            # Get incoming response
            # ------------------------------------------

            response = self._get_response(state)

            if not response:
                raise ValueError(
                    "Incoming response is required"
                )

            logger.info(
                "Analyzing incoming response"
            )

            # ------------------------------------------
            # Classify response
            # ------------------------------------------

            classification = self._classify_response(response)

            response_category = classification["response_category"]
            follow_up_hint = classification["follow_up_hint"]


            # ------------------------------------------
            # Determine next action
            # ------------------------------------------

            next_action = (
                self._get_next_action(
                    response_category
                )
            )


            # ------------------------------------------
            # Build result
            # ------------------------------------------

            result = {
                "response_category": response_category,
                "next_action": next_action,
                "follow_up_hint": follow_up_hint,
            }


            # ------------------------------------------
            # Store result
            # ------------------------------------------

            state.response_category = response_category
            state.next_action = next_action

            # Follow-up timing is relevant only for
            # ASK_LATER and OUT_OF_OFFICE.
            state.follow_up_hint = (
                follow_up_hint
                if response_category in {
                    "ASK_LATER",
                    "OUT_OF_OFFICE",
                }
                else "none"
            )

            # Backward compatibility
            state.result = result

            state.status = "completed"

            return state

        except Exception as exc:

            logger.exception(
                "Response analysis failed"
            )

            state.status = "failed"
            state.error = str(exc)

            return state

    # ==================================================
    # Get response
    # ==================================================

    @staticmethod
    def _get_response(state):

        # Support a direct response attribute if
        # AgentState is extended later.
        response = getattr(
            state,
            "incoming_response",
            None,
        )

        if response:
            return str(response).strip()

        # Backward-compatible fallback:
        # state.result may contain the response.
        if isinstance(state.result, str):
            return state.result.strip()

        if isinstance(state.result, dict):

            response = state.result.get(
                "message"
            )

            if response:
                return str(response).strip()

            response = state.result.get(
                "response"
            )

            if response:
                return str(response).strip()

        return None

    # ==================================================
    # Classify response
    # ==================================================

    def _classify_response(self, response: str) -> dict:

        prompt = f"""
    You are a response classification agent for an AI marketing
    campaign targeting colleges and educational institutions.

    Classify the recipient's message into EXACTLY ONE of the
    following 11 categories.

    CATEGORIES:

    1. REQUEST_PROPOSAL
    The recipient asks for a proposal, quotation, commercial proposal,
    training proposal, or proposal document.

    Examples:
    - Please send us a proposal.
    - Kindly share your proposal.
    - Can you provide a proposal?
    - Please forward the training proposal.
    - Send us a detailed proposal.

    2. REQUEST_MEETING
    The recipient wants to arrange, schedule, or have a meeting.

    Examples:
    - Can we schedule a meeting?
    - Please arrange a meeting.
    - We would like to meet.
    - Let's discuss this in a meeting.

    3. REQUEST_CALL
    The recipient asks for a phone call or wants to discuss by phone.

    Examples:
    - Please call me.
    - Can you call tomorrow?
    - Give me a call.
    - Let's discuss this over a call.

    4. NEEDS_INFORMATION
    The recipient asks for additional information, details,
    brochure, syllabus, pricing, fees, duration, curriculum,
    program details, or similar information.

    Use this when they want information but are NOT specifically
    asking for a proposal, meeting, or call.

    5. INTERESTED
    The recipient expresses positive intent, willingness to consider,
    or openness toward the opportunity, without making a more specific
    request.

    Examples:
    - We are interested.
    - This looks interesting.
    - We would like to explore this.
    - Sounds good.
    - We will consider it.
    - We will consider your proposal.
    - We will review this.
    - We will discuss it internally.
    - We will get back to you after discussing it.

    Do NOT require the recipient to explicitly use the word
    "interested". Positive consideration or willingness to explore
    the opportunity is sufficient.

    6. ASK_LATER
    The recipient asks to be contacted or followed up with later.

    Examples:
    - Please contact us later.
    - Get back to me next week.
    - Not now, maybe later.
    - Please follow up later.

    7. NOT_INTERESTED
    The recipient clearly declines the offer.

    Examples:
    - We are not interested.
    - We don't need this.
    - No requirement at present.
    - We will not proceed.

    8. WRONG_CONTACT
    The recipient indicates that they are not the appropriate
    person or department.

    Examples:
    - I am not the right person.
    - Please contact the placement officer.
    - I don't handle this.
    - Please contact another department.

    9. OUT_OF_OFFICE
    The response indicates that the recipient is temporarily
    unavailable, on leave, away from office, or will return later.

    Examples:
    - I am currently out of office.
    - I am on leave until Monday.
    - I will be available next week.

    10. UNCLEAR
    The message does not provide enough information to reliably
    determine the recipient's intent.

    Use UNCLEAR for short, neutral acknowledgements or vague replies
    that do not clearly show interest, rejection, a request, or another
    specific intent.

    Examples:
    - Okay.
    - Okay, thank you.
    - Noted.
    - Thanks.
    - Received.
    - Fine, thank you.

    11. OPT_OUT
    The recipient explicitly asks to stop receiving communication.

    Examples:
    - Please stop contacting me.
    - Remove me from your mailing list.
    - Unsubscribe me.
    - Do not email me again.

    IMPORTANT RULES:

    - Understand the meaning of the message, not just exact keywords.
    - Different wording with the same meaning must receive the same category.
    - Select EXACTLY ONE category.
    - Never invent a category.
    - Do not decide the next application action.
    - Return only valid JSON.
    - The "response_category" value MUST be one of the 11 categories above.

    PRIORITY RULES:

    When a message contains multiple possible intents, select the
    most specific actionable request.

    - If the recipient expresses interest AND requests a proposal,
    choose REQUEST_PROPOSAL.

    - If the recipient expresses interest AND requests a meeting,
    choose REQUEST_MEETING.

    - If the recipient requests a call AND mentions a proposal,
    choose REQUEST_CALL.

    - If the recipient asks for information but does not specifically
    request a proposal, meeting, or call, choose NEEDS_INFORMATION.

    - If the recipient asks to be contacted or followed up later,
    choose ASK_LATER.

    - If the recipient explicitly asks to stop communication,
    choose OPT_OUT regardless of other content.

    - A general positive statement such as "we are interested",
    "sounds good", or "we would like to explore this" should be
    INTERESTED when there is no more specific request.

    - "Please send some information", "please send details", or
    "please send something we can review" should be
    NEEDS_INFORMATION unless the recipient specifically asks
    for a proposal or quotation.


    FOLLOW-UP TIMING RULES:

    - ASK_LATER and OUT_OF_OFFICE responses may have a follow_up_hint.

    - If the recipient asks to follow up in 2 days,
    return "2_days".

    - If the recipient asks to follow up in 3 days,
    return "3_days".

    - If the recipient asks to follow up in 7 days,
    return "7_days".

    - If the recipient says "next week", "in a week",
    or equivalent wording, return "next_week".

    - If the recipient says "next month", "in a month",
    or equivalent wording, return "next_month".

    - If the recipient asks to be contacted later but does
    not provide a specific timing, return "unspecified".

    - For every category other than ASK_LATER and OUT_OF_OFFICE,
    return "none".

    OUT_OF_OFFICE TIMING:

    - If the recipient says they will return or become available
    in 2 days, return "2_days".

    - If the recipient says they will return or become available
    in 3 days, return "3_days".

    - If the recipient says they will return or become available
    in 7 days, return "7_days".

    - If the recipient says they will be available next week,
    return "next_week".

    - If the recipient says they will be available next month,
    return "next_month".

    - If the recipient gives no timing information,
    return "unspecified".

    - Do NOT calculate dates.
    - Do NOT return timestamps.
    - Do NOT invent a timing.
    - Only extract the timing meaning expressed by the recipient.


    Recipient message:

    {response}

    Return exactly:

    {{
        "response_category": "ONE_CATEGORY",
        "follow_up_hint": "ONE_HINT"
    }}
    """

        try:

            result = self.llm.invoke(prompt)

            content = result.content

            if isinstance(content, list):
                content = "".join(
                    str(item) for item in content
                )

            content = str(content).strip()

            parsed = json.loads(content)

            category = parsed.get(
                "response_category",
                "UNCLEAR",
            )

            follow_up_hint = parsed.get(
                "follow_up_hint",
                "none",
            )


            # ------------------------------------------
            # Validate response category
            # ------------------------------------------

            if category not in self.RESPONSE_CATEGORIES:
                logger.warning(
                    "Invalid Groq response category: %s",
                    category,
                )

                return {
                    "response_category": "UNCLEAR",
                    "follow_up_hint": "none",
                }


            # ------------------------------------------
            # Validate follow-up hint
            # ------------------------------------------

            valid_follow_up_hints = {
                "2_days",
                "3_days",
                "7_days",
                "next_week",
                "next_month",
                "unspecified",
                "none",
            }

            if follow_up_hint not in valid_follow_up_hints:

                logger.warning(
                    "Invalid Groq follow-up hint: %s",
                    follow_up_hint,
                )

                follow_up_hint = (
                    "unspecified"
                    if category == "ASK_LATER"
                    else "none"
                )


            # ------------------------------------------
            # Safety rule
            # ------------------------------------------

            # Only ASK_LATER & OUT_OF_OFFICE can have a follow-up hint.
            if category not in {"ASK_LATER", "OUT_OF_OFFICE"}:
                follow_up_hint = "none"


            return {
                "response_category": category,
                "follow_up_hint": follow_up_hint,
            }

        except Exception as exc:

            logger.exception(
                "Groq response classification failed: %s",
                exc,
            )

            return {
                "response_category": "UNCLEAR",
                "follow_up_hint": "none",
            }

    # ==================================================
    # Determine next action
    # ==================================================

    @staticmethod
    def _get_next_action(
        response_category: str,
    ) -> str:

        action_map = {

            "REQUEST_PROPOSAL":
                "HUMAN_REVIEW",

            "REQUEST_MEETING":
                "SCHEDULE_MEETING",

            "REQUEST_CALL":
                "ARRANGE_CALL",

            "NEEDS_INFORMATION":
                "HUMAN_REVIEW",

            "INTERESTED":
                "SEND_INFORMATION",

            "ASK_LATER":
                "WAIT",

            "NOT_INTERESTED":
                "STOP_OUTREACH",

            "WRONG_CONTACT":
                "FIND_UPDATE_CONTACT",

            "OUT_OF_OFFICE":
                "WAIT",

            "UNCLEAR":
                "HUMAN_REVIEW",

            "OPT_OUT":
                "STOP_ALL_OUTREACH",
        }

        return action_map.get(
            response_category,
            "HUMAN_REVIEW",
        )