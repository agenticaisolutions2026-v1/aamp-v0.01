import streamlit as st

from components.common import init_page

init_page("Dashboard")

# ---------------------------------------------------------
# Dashboard Header
# ---------------------------------------------------------
st.markdown(
    """
    <div style="
        padding: 10px 0 20px 0;
        border-bottom: 1px solid #d9e2ec;
        margin-bottom: 25px;
    ">
        <h1 style="
            color: #243b53;
            font-size: 38px;
            margin-bottom: 6px;
        ">
            📊 Dashboard
        </h1>

        <p style="
            color: #627d98;
            font-size: 16px;
            margin: 0;
        ">
            Monitor your AI-powered marketing activities from one place.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# Overview
# ---------------------------------------------------------
st.markdown(
    """
    <h2 style="
        color: #243b53;
        font-size: 26px;
        margin-bottom: 15px;
    ">
        📈 Platform Overview
    </h2>
    """,
    unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="🏫 Organizations",
        value="25"
    )

with col2:
    st.metric(
        label="📢 Campaigns",
        value="108"
    )

with col3:
    st.metric(
        label="📨 Outreach",
        value="16"
    )

with col4:
    st.metric(
        label="🤖 AI Agents",
        value="11"
    )

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# Campaign Status
# ---------------------------------------------------------
st.markdown(
    """
    <h2 style="
        color: #243b53;
        font-size: 26px;
        margin-bottom: 15px;
    ">
        📋 Campaign Status
    </h2>
    """,
    unsafe_allow_html=True
)

status1, status2, status3, status4 = st.columns(4)

with status1:
    st.markdown(
        """
        <div style="
            background: #ffffff;
            border: 1px solid #d9e2ec;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        ">
            <div style="font-size: 28px;">🟡</div>
            <div style="color: #486581; font-size: 14px;">
                Pending Approval
            </div>
            <div style="
                color: #243b53;
                font-size: 28px;
                font-weight: 600;
                margin-top: 5px;
            ">
                5
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with status2:
    st.markdown(
        """
        <div style="
            background: #ffffff;
            border: 1px solid #d9e2ec;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        ">
            <div style="font-size: 28px;">🔵</div>
            <div style="color: #486581; font-size: 14px;">
                Approved
            </div>
            <div style="
                color: #243b53;
                font-size: 28px;
                font-weight: 600;
                margin-top: 5px;
            ">
                8
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with status3:
    st.markdown(
        """
        <div style="
            background: #ffffff;
            border: 1px solid #d9e2ec;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        ">
            <div style="font-size: 28px;">🟢</div>
            <div style="color: #486581; font-size: 14px;">
                Sent
            </div>
            <div style="
                color: #243b53;
                font-size: 28px;
                font-weight: 600;
                margin-top: 5px;
            ">
                3
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with status4:
    st.markdown(
        """
        <div style="
            background: #ffffff;
            border: 1px solid #d9e2ec;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        ">
            <div style="font-size: 28px;">💬</div>
            <div style="color: #486581; font-size: 14px;">
                Replied
            </div>
            <div style="
                color: #243b53;
                font-size: 28px;
                font-weight: 600;
                margin-top: 5px;
            ">
                1
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# Campaign Workflow
# ---------------------------------------------------------
st.markdown(
    """
    <h2 style="
        color: #243b53;
        font-size: 26px;
        margin-bottom: 15px;
    ">
        🔄 Campaign Workflow
    </h2>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style="
        background: #ffffff;
        border: 1px solid #d9e2ec;
        border-radius: 12px;
        padding: 25px;
    ">

        <div style="
            color: #334e68;
            font-size: 16px;
            line-height: 2;
        ">
            🏫 College Discovery
            &nbsp; → &nbsp;
            🎯 Lead Qualification
            &nbsp; → &nbsp;
            📢 Campaign Strategy
            &nbsp; → &nbsp;
            ✍️ Personalized Message
            &nbsp; → &nbsp;
            👤 Human Approval
            &nbsp; → &nbsp;
            📧 Outreach
            &nbsp; → &nbsp;
            🔄 Follow-up
            &nbsp; → &nbsp;
            💬 Response
        </div>

    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# System Status
# ---------------------------------------------------------
st.markdown(
    """
    <div style="
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 12px;
        padding: 18px 22px;
    ">
        <div style="
            color: #166534;
            font-size: 18px;
            font-weight: 600;
        ">
            🟢 Backend Connected
        </div>

        <div style="
            color: #4b5563;
            margin-top: 5px;
            font-size: 14px;
        ">
            AAMP backend services are running normally.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)