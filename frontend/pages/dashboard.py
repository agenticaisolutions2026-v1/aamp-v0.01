import streamlit as st
from textwrap import dedent
from services.college_service import CollegeService
from services.campaign_service import CampaignService
from services.agent_service import AgentService
from components.common import init_page

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

init_page("Dashboard")


# ============================================================
# AAMP DASHBOARD STYLING
# ============================================================

st.markdown(
    """
<style>

/* ==========================================================
   APP
   ========================================================== */

.stApp {
    background: #F5F7FB;
}

.block-container {
    max-width: 1400px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}


/* ==========================================================
   SIDEBAR
   ========================================================== */

[data-testid="stSidebar"] {
    background: #111C35;
}

[data-testid="stSidebar"] * {
    color: #E5E7EB;
}


/* ==========================================================
   DASHBOARD HEADER
   ========================================================== */

.aamp-header {
    margin-bottom: 1.8rem;
}

.aamp-title {
    color: #172554;
    font-size: 2.15rem;
    font-weight: 750;
    line-height: 1.15;
    margin: 0;
}

.aamp-subtitle {
    color: #64748B;
    font-size: 0.95rem;
    margin-top: 0.45rem;
}


/* ==========================================================
   KPI CARDS
   ========================================================== */

.kpi-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 15px;
    padding: 1.25rem;
    min-height: 135px;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.045);
}

.kpi-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.kpi-label {
    color: #64748B;
    font-size: 0.85rem;
    font-weight: 600;
}

.kpi-icon {
    width: 40px;
    height: 40px;
    border-radius: 11px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.15rem;
    background: #EEF2FF;
}

.kpi-value {
    color: #0F172A;
    font-size: 2rem;
    font-weight: 750;
    margin-top: 0.65rem;
}

.kpi-description {
    color: #94A3B8;
    font-size: 0.74rem;
    margin-top: 0.4rem;
}


/* ==========================================================
   SECTION HEADINGS
   ========================================================== */

.section-title {
    color: #172554;
    font-size: 1.2rem;
    font-weight: 700;
    margin-top: 2rem;
    margin-bottom: 0.25rem;
}

.section-subtitle {
    color: #64748B;
    font-size: 0.82rem;
    margin-bottom: 1rem;
}


/* ==========================================================
   COLLEGE PIPELINE
   ========================================================== */

.pipeline-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 15px;
    padding: 1rem;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
}

.pipeline-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.3rem 0.4rem 0.9rem 0.4rem;
}

.pipeline-heading {
    color: #172554;
    font-size: 1.05rem;
    font-weight: 700;
}

.pipeline-count {
    background: #EEF2FF;
    color: #4338CA;
    border-radius: 999px;
    padding: 0.35rem 0.7rem;
    font-size: 0.75rem;
    font-weight: 700;
}


/* ==========================================================
   COLLEGE ROW
   ========================================================== */

.college-row {
    display: flex;
    align-items: center;
    background: #FFFFFF;
    border-top: 1px solid #F1F5F9;
    padding: 0.8rem 0.45rem;
}

.college-rank {
    width: 45px;
    color: #94A3B8;
    font-size: 0.78rem;
    font-weight: 600;
}

.college-info {
    flex: 1;
}

.college-name {
    color: #1E293B;
    font-size: 0.9rem;
    font-weight: 650;
}

.college-location {
    color: #94A3B8;
    font-size: 0.74rem;
    margin-top: 0.2rem;
}

.college-status {
    margin-right: 1rem;
}

.status-badge {
    background: #ECFDF5;
    color: #047857;
    border-radius: 999px;
    padding: 0.3rem 0.65rem;
    font-size: 0.7rem;
    font-weight: 650;
}


/* ==========================================================
   OPERATION CARDS
   ========================================================== */

.operation-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 15px;
    min-height: 150px;
    padding: 1.3rem;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
}

.operation-icon {
    font-size: 1.5rem;
    margin-bottom: 0.7rem;
}

.operation-title {
    color: #172554;
    font-size: 1rem;
    font-weight: 700;
}

.operation-description {
    color: #64748B;
    font-size: 0.78rem;
    line-height: 1.55;
    margin-top: 0.5rem;
}


/* ==========================================================
   STREAMLIT BUTTON
   ========================================================== */

.stLinkButton > a {
    border-radius: 8px !important;
    border: 1px solid #C7D2FE !important;
    color: #4338CA !important;
    background: #FFFFFF !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
}

.stLinkButton > a:hover {
    background: #EEF2FF !important;
    border-color: #818CF8 !important;
}


/* ==========================================================
   REMOVE EXTRA DIVIDER
   ========================================================== */

hr {
    border-color: #E2E8F0;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
<div class="aamp-header">
    <div class="aamp-title">Dashboard</div>
    <div class="aamp-subtitle">
        Monitor your college marketing operations from one place.
    </div>
</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# LOAD COLLEGES
# ============================================================

try:

    with st.spinner("Loading dashboard..."):

        # Colleges
        response = CollegeService.search()
        count = response.get("count", 0)
        results = response.get("results", [])

        # Campaigns
        campaigns = CampaignService.get_all()
        campaign_count = len(campaigns)

        # Scheduler
        scheduler_status = CampaignService.get_scheduler_status()
        
        # AI Agents
        agents = AgentService.get_all()
        agent_count = len(agents)


    # ========================================================
    # KPI CARDS
    # ========================================================

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
<div class="kpi-card">
    <div class="kpi-top">
        <div class="kpi-label">Colleges</div>
        <div class="kpi-icon">🎓</div>
    </div>
    <div class="kpi-value">{count}</div>
    <div class="kpi-description">Colleges discovered by AAMP</div>
</div>
""",
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
    <div class="kpi-card">
        <div class="kpi-top">
            <div class="kpi-label">AI Agents</div>
            <div class="kpi-icon">🤖</div>
        </div>
        <div class="kpi-value">{agent_count}</div>
        <div class="kpi-description">
            Registered AI agents
        </div>
    </div>
    """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
    <div class="kpi-card">
        <div class="kpi-top">
            <div class="kpi-label">Campaigns</div>
            <div class="kpi-icon">📣</div>
        </div>
        <div class="kpi-value">{campaign_count}</div>
        <div class="kpi-description">
            Campaigns created in AAMP
        </div>
    </div>
    """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
<div class="kpi-card">
    <div class="kpi-top">
        <div class="kpi-label">Leads</div>
        <div class="kpi-icon">👥</div>
    </div>
    <div class="kpi-value">—</div>
    <div class="kpi-description">Lead data coming soon</div>
</div>
""",
            unsafe_allow_html=True,
        )

    # ========================================================
    # CAMPAIGN AUTOMATION
    # ========================================================

    scheduler = scheduler_status.get("scheduler", {})
    scheduler_running = scheduler_status.get("status") == "running"

    jobs = scheduler.get("jobs", [])

    next_run_time = (
        jobs[0].get("next_run_time")
        if jobs
        else None
    )

    due_followups = scheduler.get(
        "due_followups",
        0,
    )

    last_run_at = scheduler.get(
        "last_run_at"
    )

    if next_run_time:
        next_run_time = next_run_time.replace(
            "T", " "
        )[:19]

    if last_run_at:
        last_run_at = (
            datetime.fromisoformat(last_run_at)
            .astimezone(ZoneInfo("Asia/Kolkata"))
            .strftime("%Y-%m-%d %H:%M:%S")
        )
    else:
        last_run_at = "Not yet"

    scheduler_label = (
        "🟢 Running"
        if scheduler_running
        else "🔴 Stopped"
    )

    # Space between KPI cards and automation card
    st.write("")

    with st.container(border=True):

        st.markdown(
            "### ⚙️ Campaign Automation"
        )

        st.caption(
            "Automated follow-up scheduler"
        )

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.write("**Scheduler**")
            st.write(scheduler_label)

        with col2:
            st.write("**Follow-up Job**")
            st.write(
                "Active"
                if jobs
                else "No Job"
            )

        with col3:
            st.write("**Next Check**")
            st.write(
                next_run_time or "—"
            )

        with col4:
            st.write("**Due Follow-ups**")
            st.write(
                str(due_followups)
            )

        with col5:
            st.write("**Last Run**")
            st.write(
                last_run_at
            )
    # ========================================================
    # COLLEGE PIPELINE
    # ========================================================

    st.markdown(
        """
        <div class="section-title">College Pipeline</div>
        <div class="section-subtitle">
            Explore colleges discovered by AAMP.
        </div>
        """,
        unsafe_allow_html=True,
    )


    col1, col2 = st.columns([5, 1.3])


    with col1:

        with st.container(border=True):

            inner_col1, inner_col2 = st.columns([4, 1])

            with inner_col1:

                st.markdown("### 🎓 Andhra Pradesh Colleges")

                st.caption(
                    f"{count} colleges discovered in Andhra Pradesh"
                )

            with inner_col2:

                st.metric(
                    "Colleges",
                    count,
                )


    with col2:

        st.markdown(
            "<div style='height: 22px;'></div>",
            unsafe_allow_html=True,
        )

        st.page_link(
            "pages/ap_colleges.py",
            label="View AP Colleges →",
            use_container_width=True,
        )


    # ========================================================
    # AAMP WORKFLOW
    # ========================================================

    st.markdown(
        """
        <div class="section-title">AAMP Workflow</div>
        <div class="section-subtitle">
            From college discovery to personalized outreach.
        </div>
        """,
        unsafe_allow_html=True,
    )


    workflow = [
        ("🎓", "Discovery", "Find relevant colleges"),
        ("🔎", "Enrichment", "Analyze college information"),
        ("⭐", "Scoring", "Evaluate opportunities"),
        ("👤", "Lead Qualification", "Identify prospects"),
        ("📣", "Campaign", "Prepare personalized campaigns"),
        ("✉️", "Outreach", "Connect with colleges"),
    ]


    workflow_cols = st.columns(6)

    for column, (icon, title, description) in zip(
        workflow_cols,
        workflow,
    ):

        with column:

            with st.container(border=True):

                st.markdown(
                    f"### {icon}"
                )

                st.markdown(
                    f"**{title}**"
                )

                st.caption(
                    description
                )


    # ========================================================
    # QUICK ACCESS
    # ========================================================

    st.markdown(
        """
        <div class="section-title">Quick Access</div>
        <div class="section-subtitle">
            Jump directly to the areas you use most.
        </div>
        """,
        unsafe_allow_html=True,
    )


    col1, col2, col3, col4 = st.columns(4)


    with col1:

        with st.container(border=True):

            st.markdown("### 🎓 AP Colleges")

            st.caption(
                f"Explore {count} discovered colleges."
            )

            st.page_link(
                "pages/ap_colleges.py",
                label="View Colleges →",
                use_container_width=True,
            )


    with col2:

        with st.container(border=True):

            st.markdown("### 📣 Campaigns")

            st.caption(
                f"Manage {campaign_count} campaigns."
            )

            st.page_link(
                "pages/campaigns.py",
                label="View Campaigns →",
                use_container_width=True,
            )


    with col3:

        with st.container(border=True):

            st.markdown("### 🤖 AI Agents")

            st.caption(
                f"Manage {agent_count} registered agents."
            )

            st.page_link(
                "pages/agents.py",
                label="View Agents →",
                use_container_width=True,
            )


    with col4:

        with st.container(border=True):

            st.markdown("### 📊 Analytics")

            st.caption(
                "Explore AAMP performance insights."
            )

            st.page_link(
                "pages/analytics.py",
                label="View Analytics →",
                use_container_width=True,
            )
except Exception as exc:

    st.error(
        f"Failed to load dashboard: {exc}"
    )

