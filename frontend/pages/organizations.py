import streamlit as st

from components.common import init_page
from services.organization_service import OrganizationService


init_page("Organizations")


# ---------------------------------------------------------
# Page Header
# ---------------------------------------------------------
st.title("Organizations")
st.caption("Manage organizations participating in AAMP.")


# ---------------------------------------------------------
# Load Organizations
# ---------------------------------------------------------
try:
    organizations = OrganizationService.get_all()

    if organizations is None:
        organizations = []

except Exception as e:
    st.error("Unable to load organizations.")
    st.caption(str(e))
    organizations = []


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------
total_organizations = len(organizations)

st.metric(
    "Total Organizations",
    total_organizations,
)


# ---------------------------------------------------------
# Search
# ---------------------------------------------------------
st.markdown("### Organizations")

search = st.text_input(
    "Search organizations",
    placeholder="Search by organization name...",
    label_visibility="collapsed",
)


# ---------------------------------------------------------
# Filter
# ---------------------------------------------------------
filtered_organizations = organizations

if search:
    search_text = search.lower().strip()

    filtered_organizations = [
        organization
        for organization in organizations
        if search_text in str(
            organization.get("name", "")
        ).lower()
    ]


# ---------------------------------------------------------
# Organization List
# ---------------------------------------------------------
if not filtered_organizations:

    if organizations:
        st.info("No organizations match your search.")
    else:
        st.info("No organizations found.")

else:

    for organization in filtered_organizations:

        org_id = organization.get("id")
        name = organization.get(
            "name",
            "Unnamed Organization",
        )

        created_at = organization.get("created_at")

        with st.container(border=True):

            col1, col2, col3 = st.columns([5, 2, 1])

            with col1:
                st.markdown(f"**{name}**")
                st.caption(f"Organization ID: {org_id}")

            with col2:
                st.markdown("**Created**")

                if created_at:
                    st.write(
                        str(created_at)[:10]
                    )
                else:
                    st.write("—")

            with col3:
                st.button(
                    "View",
                    key=f"view_org_{org_id}",
                    disabled=True,
                )