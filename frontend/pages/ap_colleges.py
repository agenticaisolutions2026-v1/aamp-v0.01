import streamlit as st

from services.college_service import CollegeService
from components.common import init_page


init_page("AP Colleges")


st.title("Andhra Pradesh Colleges")
st.caption("Colleges discovered and managed by AAMP.")


try:

    with st.spinner("Loading colleges..."):
        response = CollegeService.search()

    count = response.get("count", 0)
    results = response.get("results", [])


    st.metric("Total AP Colleges", count)

    st.divider()


    if not results:

        st.info("No colleges available.")

    else:

        for rank, item in enumerate(results, start=1):

            college = item.get("college", {})

            name = college.get(
                "name",
                "Unknown College",
            )

            city = college.get("city") or "N/A"
            state = college.get("state") or "N/A"
            website = college.get("website")


            with st.container(border=True):

                col1, col2, col3 = st.columns(
                    [0.6, 5, 1]
                )

                with col1:
                    st.write(f"**#{rank}**")

                with col2:

                    st.markdown(
                        f"### {name}"
                    )

                    st.caption(
                        f"📍 {city}, {state}"
                    )

                with col3:

                    if website:
                        st.link_button(
                            "Visit",
                            website,
                            use_container_width=True,
                        )


except Exception as exc:

    st.error(
        f"Failed to load colleges: {exc}"
    )