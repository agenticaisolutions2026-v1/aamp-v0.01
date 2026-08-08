import streamlit as st
from services.organization_service import OrganizationService
from components.common import init_page

init_page("Organizations")
st.title("Organizations")

try:
    # Loading indicator
    with st.spinner("Loading organizations..."):
        organizations = OrganizationService.get_all()
        #st.dataframe(organizations)
        # No data
        if not organizations:
            st.warning("No organizations found.")
        else:
            st.success(f"Loaded {len(organizations)} organizations successfully.")
            st.dataframe(
                organizations,
                use_container_width=True,
                hide_index=True
            )
except Exception as e:
    st.error(f"❌ Failed to load organizations. {e}")