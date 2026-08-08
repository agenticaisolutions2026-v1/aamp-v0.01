import streamlit as st
from services.campaign_service import CampaignService
from components.common import init_page

init_page("Campaigns")

st.title("Campaigns")
st.write("Campaign Management")
try:
    with st.spinner("Loading campaigns..."):
        campaigns = CampaignService.get_all()
        if not campaigns:
            st.warning("No campaigns found.")
        else:
            st.success(f"Loaded {len(campaigns)} campaigns successfully.")
            st.dataframe(
                campaigns,
                use_container_width=True,
                hide_index=True
            )
except Exception as e:
    st.error(f"❌ Failed to load campaigns: {e}")