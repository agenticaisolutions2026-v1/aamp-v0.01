import streamlit as st
from services.health_service import HealthService


def create_sidebar():
    with st.sidebar:

        # =================================================
        # AAMP HEADER
        # =================================================

        st.title("AAMP")

        st.page_link(
            "app.py",
            label="🏠 Home"
        )

        st.markdown("---")


        # =================================================
        # MAIN NAVIGATION
        # =================================================

        st.page_link(
            "pages/Dashboard.py",
            label="📊 Dashboard"
        )

        st.page_link(
            "pages/Organizations.py",
            label="🏢 Organizations"
        )

        st.page_link(
            "pages/Campaigns.py",
            label="📢 Campaigns"
        )

        st.page_link(
            "pages/Outreach.py",
            label="📨 Outreach"
        )

        st.page_link(
            "pages/Agents.py",
            label="👥 Agents"
        )

        st.page_link(
            "pages/Analytics.py",
            label="📈 Analytics"
        )

        st.page_link(
            "pages/Settings.py",
            label="⚙️ Settings"
        )


        # =================================================
        # SYSTEM STATUS
        # =================================================

        st.write("System Status")

        try:

            health = HealthService.get_status()

            if health.get("status") == "healthy":

                st.success(
                    "🟢 Backend: Connected"
                )

            else:

                st.error(
                    "🔴 Backend: Disconnected"
                )

        except Exception:

            st.error(
                "🔴 Backend: Disconnected"
            )


        # =================================================
        # FOOTER
        # =================================================

        st.markdown("---")

        st.caption("Version 1.0")