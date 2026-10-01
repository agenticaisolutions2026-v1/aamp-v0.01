import streamlit as st
import pandas as pd
from collections import defaultdict
from datetime import datetime
import altair as alt

from components.common import init_page
from services.campaign_service import CampaignService
from services.college_service import CollegeService


# ============================================================
# PAGE
# ============================================================

init_page("Analytics")

st.title("Analytics")
st.caption(
    "Measure outreach performance and identify college opportunities."
)


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data(ttl=30)
def load_campaigns():
    return CampaignService.get_all()


@st.cache_data(ttl=30)
def load_colleges():
    return CollegeService.search()


@st.cache_data(ttl=30)
def load_campaign_messages(campaign_id: int):
    return CampaignService.get_messages(campaign_id)


# ============================================================
# HELPERS
# ============================================================

def parse_datetime(value):
    """Convert API datetime values into Python datetime."""
    if not value:
        return None

    if isinstance(value, datetime):
        return value

    try:
        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
    except (TypeError, ValueError):
        return None


def get_month_label(value):
    """Return YYYY-MM label for a datetime value."""
    dt = parse_datetime(value)

    if not dt:
        return None

    return dt.strftime("%Y-%m")


def format_month(month_value):
    """Convert YYYY-MM into a user-friendly month label."""
    try:
        return datetime.strptime(
            month_value,
            "%Y-%m",
        ).strftime("%B %Y")
    except ValueError:
        return month_value


def get_college_data(response):
    """
    Normalize the College API response.

    Current API structure:
    {
        "count": 10,
        "results": [
            {
                "college": {
                    "id": 11,
                    "name": "SRM University AP",
                    ...
                }
            }
        ]
    }
    """

    if not response:
        return []

    if isinstance(response, list):
        return response

    if isinstance(response, dict):
        return response.get("results", [])

    return []


# ============================================================
# LOAD API DATA
# ============================================================

try:
    campaigns_response = load_campaigns()
    colleges_response = load_colleges()

except Exception as exc:
    st.error(
        f"Unable to load analytics data: {exc}"
    )
    st.stop()


# ============================================================
# NORMALIZE CAMPAILS
# ============================================================

if isinstance(campaigns_response, dict):
    campaigns = campaigns_response.get(
        "results",
        [],
    )
else:
    campaigns = campaigns_response or []


if not campaigns:
    st.info(
        "No campaign data is available yet."
    )
    st.stop()


# ============================================================
# COLLEGE LOOKUP
# ============================================================

college_map = {}

college_results = get_college_data(
    colleges_response
)

for item in college_results:

    # Current API format:
    # {"college": {...}}

    if isinstance(item, dict):
        college = item.get(
            "college",
            item,
        )
    else:
        continue

    if not isinstance(college, dict):
        continue

    college_id = college.get("id")

    if college_id is not None:
        college_map[college_id] = college.get(
            "name",
            f"College {college_id}",
        )


# ============================================================
# COLLECT CONVERSATION DATA
# ============================================================

#
# We use conversation_messages for replies.
#
# This is important because a campaign can move:
#
# draft → approved → sent → replied → closed
#
# Therefore current campaign.status cannot reliably tell
# us whether a reply happened.
#

conversation_data = {}

for campaign in campaigns:

    campaign_id = campaign.get("id")

    if campaign_id is None:
        continue

    try:
        messages = load_campaign_messages(
            campaign_id
        )

        if isinstance(messages, dict):
            messages = messages.get(
                "results",
                [],
            )

        conversation_data[campaign_id] = (
            messages or []
        )

    except Exception:
        conversation_data[campaign_id] = []


# ============================================================
# BUILD MONTH LIST AUTOMATICALLY
# ============================================================

available_months = set()

# Months from campaigns
for campaign in campaigns:
    month = get_month_label(
        campaign.get("created_at")
    )

    if month:
        available_months.add(month)


# Months from conversations
for messages in conversation_data.values():

    for message in messages:

        for field in (
            "sent_at",
            "received_at",
            "created_at",
        ):
            month = get_month_label(
                message.get(field)
            )

            if month:
                available_months.add(month)


# Always include the current month
current_month = datetime.now().strftime("%Y-%m")

available_months.add(current_month)


# Newest month first
available_months = sorted(
    available_months,
    reverse=True,
)


# ============================================================
# FILTER
# ============================================================

st.subheader("Performance")

filter_col1, filter_col2 = st.columns(
    [1, 2]
)

with filter_col1:

    selected_month = st.selectbox(
        "Month",
        available_months,
        format_func=format_month,
    )

with filter_col2:

    college_options = {
        "All Colleges": None
    }

    for college_id, college_name in sorted(
        college_map.items(),
        key=lambda item: item[1].lower(),
    ):
        college_options[college_name] = college_id

    selected_college_name = st.selectbox(
        "College",
        list(college_options.keys()),
    )

selected_college_id = college_options[
    selected_college_name
]


# ============================================================
# BUILD MONTHLY COLLEGE PERFORMANCE
# ============================================================

college_stats = defaultdict(
    lambda: {
        "campaigns": 0,
        "sent": 0,
        "replies": 0,
        "last_activity": None,
    }
)


for campaign in campaigns:

    campaign_id = campaign.get("id")
    college_id = campaign.get("college_id")

    if college_id is None:
        continue

    if (
        selected_college_id is not None
        and college_id != selected_college_id
    ):
        continue

    messages = conversation_data.get(
        campaign_id,
        [],
    )

    campaign_month = get_month_label(
        campaign.get("created_at")
    )

    #
    # A campaign belongs to the selected month
    # based on its creation date.
    #
    if campaign_month != selected_month:
        continue

    stats = college_stats[college_id]

    stats["campaigns"] += 1

    # --------------------------------------------------------
    # SENT
    # --------------------------------------------------------

    outbound_messages = [
        message
        for message in messages
        if message.get("direction") == "outbound"
    ]

    if outbound_messages:
        stats["sent"] += 1

    else:
        #
        # Backward-compatible fallback:
        #
        # Campaign #5 was sent before outbound
        # conversation tracking existed.
        #
        status = campaign.get("status")

        if status in {
            "sent",
            "replied",
            "closed",
        }:
            stats["sent"] += 1

    # --------------------------------------------------------
    # REPLIES
    # --------------------------------------------------------

    inbound_messages = [
        message
        for message in messages
        if message.get("direction") == "inbound"
    ]

    stats["replies"] += len(
        inbound_messages
    )

    # --------------------------------------------------------
    # LAST ACTIVITY
    # --------------------------------------------------------

    activity_dates = []

    campaign_created = parse_datetime(
        campaign.get("created_at")
    )

    if campaign_created:
        activity_dates.append(
            campaign_created
        )

    for message in messages:

        for field in (
            "sent_at",
            "received_at",
            "created_at",
        ):

            activity_date = parse_datetime(
                message.get(field)
            )

            if activity_date:
                activity_dates.append(
                    activity_date
                )

    if activity_dates:

        latest_activity = max(
            activity_dates
        )

        if (
            stats["last_activity"] is None
            or latest_activity
            > stats["last_activity"]
        ):
            stats["last_activity"] = (
                latest_activity
            )


# ============================================================
# CREATE DATAFRAME
# ============================================================

performance_rows = []

for college_id, stats in college_stats.items():

    sent = stats["sent"]
    replies = stats["replies"]

    reply_rate = (
        (replies / sent) * 100
        if sent > 0
        else None
    )

    performance_rows.append(
        {
            "College": college_map.get(
                college_id,
                f"College {college_id}",
            ),
            "Campaigns": stats["campaigns"],
            "Sent": sent,
            "Replies": replies,
            "Reply Rate": reply_rate,
            "Last Activity": (
                stats["last_activity"].strftime(
                    "%d %b %Y"
                )
                if stats["last_activity"]
                else "—"
            ),
        }
    )


performance_df = pd.DataFrame(
    performance_rows
)


# ============================================================
# PERFORMANCE TOTALS
# ============================================================

total_campaigns = int(
    performance_df["Campaigns"].sum()
    if not performance_df.empty
    else 0
)

total_sent = int(
    performance_df["Sent"].sum()
    if not performance_df.empty
    else 0
)

total_replies = int(
    performance_df["Replies"].sum()
    if not performance_df.empty
    else 0
)

total_colleges = len(
    performance_df
)

overall_reply_rate = (
    (total_replies / total_sent) * 100
    if total_sent > 0
    else 0
)


# ============================================================
# PERFORMANCE METRICS
# ============================================================

metric1, metric2, metric3, metric4 = st.columns(
    4
)

with metric1:
    st.metric(
        "Campaigns",
        total_campaigns,
    )

with metric2:
    st.metric(
        "Sent",
        total_sent,
    )

with metric3:
    st.metric(
        "Replies",
        total_replies,
    )

with metric4:
    st.metric(
        "Reply Rate",
        f"{overall_reply_rate:.1f}%",
    )


st.divider()


# ============================================================
# COLLEGE PERFORMANCE TABLE
# ============================================================

st.subheader(
    f"College Performance · {format_month(selected_month)}"
)

search_col = st.text_input(
    "Search colleges",
    placeholder="Search by college name...",
)


if performance_df.empty:

    st.info(
        "No college activity is available "
        f"for {format_month(selected_month)}."
    )

else:

    filtered_df = performance_df.copy()

    if search_col:
        filtered_df = filtered_df[
            filtered_df["College"].str.contains(
                search_col,
                case=False,
                na=False,
            )
        ]

    display_df = filtered_df.copy()

    display_df["Reply Rate"] = (
        display_df["Reply Rate"].apply(
            lambda value: (
                f"{value:.1f}%"
                if pd.notna(value)
                else "—"
            )
        )
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "College": st.column_config.TextColumn(
                "College",
                width="large",
            ),
            "Campaigns": st.column_config.NumberColumn(
                "Campaigns",
            ),
            "Sent": st.column_config.NumberColumn(
                "Sent",
            ),
            "Replies": st.column_config.NumberColumn(
                "Replies",
            ),
            "Reply Rate": st.column_config.TextColumn(
                "Reply Rate",
            ),
            "Last Activity": st.column_config.TextColumn(
                "Last Activity",
            ),
        },
    )

    st.caption(
        f"{len(filtered_df)} college"
        f"{'s' if len(filtered_df) != 1 else ''}"
        f" shown."
    )


st.divider()


# ============================================================
# MONTHLY OUTREACH PERFORMANCE
# ============================================================

st.subheader("Monthly Outreach Performance")


# ============================================================
# BUILD MONTHLY DATA
# ============================================================

monthly_stats = defaultdict(
    lambda: {
        "Sent": 0,
        "Replies": 0,
    }
)


for campaign in campaigns:

    campaign_id = campaign.get("id")

    if campaign_id is None:
        continue

    # Specific college filter
    if (
        selected_college_id is not None
        and campaign.get("college_id")
        != selected_college_id
    ):
        continue

    campaign_month = get_month_label(
        campaign.get("created_at")
    )

    if not campaign_month:
        continue

    messages = conversation_data.get(
        campaign_id,
        [],
    )

    # --------------------------------------------------------
    # SENT
    # --------------------------------------------------------

    outbound_messages = [
        message
        for message in messages
        if message.get("direction") == "outbound"
    ]

    if outbound_messages:

        monthly_stats[campaign_month]["Sent"] += 1

    elif campaign.get("status") in {
        "sent",
        "replied",
        "closed",
    }:

        # Supports older campaigns that were sent
        # before conversation tracking was added.
        monthly_stats[campaign_month]["Sent"] += 1

    # --------------------------------------------------------
    # REPLIES
    # --------------------------------------------------------

    inbound_messages = [
        message
        for message in messages
        if message.get("direction") == "inbound"
    ]

    monthly_stats[campaign_month]["Replies"] += len(
        inbound_messages
    )


# ============================================================
# CREATE MONTH RANGE
# ============================================================

monthly_rows = []


if monthly_stats:

    first_month = min(
        monthly_stats.keys()
    )

    first_date = datetime.strptime(
        first_month,
        "%Y-%m",
    )

    current_date = datetime.now().replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    current = first_date

    while current <= current_date:

        month_key = current.strftime(
            "%Y-%m"
        )

        monthly_rows.append(
            {
                "month_key": month_key,
                "month": format_month(
                    month_key
                ),
                "sent": monthly_stats.get(
                    month_key,
                    {},
                ).get(
                    "Sent",
                    0,
                ),
                "replies": monthly_stats.get(
                    month_key,
                    {},
                ).get(
                    "Replies",
                    0,
                ),
            }
        )

        # Move to next month
        if current.month == 12:

            current = current.replace(
                year=current.year + 1,
                month=1,
            )

        else:

            current = current.replace(
                month=current.month + 1
            )


# ============================================================
# DISPLAY MONTHLY PERFORMANCE
# ============================================================

if not monthly_rows:

    st.info(
        "Monthly outreach data will appear "
        "after campaign activity begins."
    )

else:

    for index, row in enumerate(
        monthly_rows
    ):

        # ----------------------------------------------------
        # Month heading
        # ----------------------------------------------------

        st.markdown(
            f"**{row['month']}**"
        )

        # ----------------------------------------------------
        # Prepare two horizontal bars
        # ----------------------------------------------------

        chart_data = pd.DataFrame(
            {
                "Metric": [
                    "Sent",
                    "Replies",
                ],
                "Count": [
                    row["sent"],
                    row["replies"],
                ],
            }
        )

        chart_data = chart_data.set_index(
            "Metric"
        )

        # ----------------------------------------------------
        # Horizontal chart
        # ----------------------------------------------------

        st.bar_chart(
            chart_data,
            horizontal=True,
            use_container_width=True,
        )

        # ----------------------------------------------------
        # Separate months visually
        # ----------------------------------------------------

        if index < len(monthly_rows) - 1:
            st.divider()


    # --------------------------------------------------------
    # Explanation
    # --------------------------------------------------------

    st.caption(
        "Monthly performance. New months are added "
        "automatically as campaign activity grows."
    )

# ============================================================
# TOP PERFORMING COLLEGES
# ============================================================

st.subheader("Top Performing Colleges")

if performance_df.empty:

    st.info(
        "No performance data is available."
    )

else:

    top_df = performance_df[
        performance_df["Sent"] > 0
    ].copy()

    if top_df.empty:

        st.info(
            "No colleges have completed outreach "
            "in the selected month yet."
        )

    else:

        top_df = top_df.sort_values(
            by="Reply Rate",
            ascending=False,
        ).head(10)

        top_display = top_df[
            [
                "College",
                "Sent",
                "Replies",
                "Reply Rate",
            ]
        ].copy()

        top_display["Reply Rate"] = (
            top_display["Reply Rate"].map(
                lambda value: f"{value:.1f}%"
            )
        )

        st.dataframe(
            top_display,
            use_container_width=True,
            hide_index=True,
        )


st.divider()


# ============================================================
# AAMP INSIGHTS
# ============================================================

st.subheader("AAMP Insights")


if performance_df.empty:

    st.info(
        "Insights will appear when campaign "
        "activity is available."
    )

else:

    insight_col1, insight_col2 = st.columns(
        2
    )

    # --------------------------------------------------------
    # BEST PERFORMER
    # --------------------------------------------------------

    with insight_col1:

        best_df = performance_df[
            performance_df["Sent"] > 0
        ].sort_values(
            by="Reply Rate",
            ascending=False,
        )

        if not best_df.empty:

            best = best_df.iloc[0]

            st.success(
                f"⭐ **Best response:** "
                f"{best['College']} has a "
                f"{best['Reply Rate']:.1f}% "
                "reply rate this month."
            )

        else:

            st.info(
                "⭐ No completed outreach is "
                "available yet."
            )

    # --------------------------------------------------------
    # FOLLOW-UP OPPORTUNITY
    # --------------------------------------------------------

    with insight_col2:

        no_reply_df = performance_df[
            (performance_df["Sent"] > 0)
            & (performance_df["Replies"] == 0)
        ]

        if not no_reply_df.empty:

            st.warning(
                f"⚠️ **Follow-up opportunity:** "
                f"{len(no_reply_df)} college"
                f"{'s' if len(no_reply_df) != 1 else ''} "
                "received outreach but have not "
                "replied."
            )

        else:

            st.success(
                "✓ All colleges with completed "
                "outreach have received at least "
                "one reply."
            )

    # --------------------------------------------------------
    # HIGH RESPONSE
    # --------------------------------------------------------

    high_response_df = performance_df[
        performance_df["Reply Rate"] >= 50
    ]

    if not high_response_df.empty:

        st.info(
            f"🔥 **High-response colleges:** "
            f"{len(high_response_df)} college"
            f"{'s' if len(high_response_df) != 1 else ''} "
            "have a reply rate of 50% or higher."
        )

    # --------------------------------------------------------
    # NO OUTREACH
    # --------------------------------------------------------

    no_outreach_df = performance_df[
        performance_df["Sent"] == 0
    ]

    if not no_outreach_df.empty:

        st.info(
            f"📌 **Outreach opportunity:** "
            f"{len(no_outreach_df)} college"
            f"{'s' if len(no_outreach_df) != 1 else ''} "
            "have campaigns but no recorded "
            "outbound outreach yet."
        )