import streamlit as st
from services.agent_service import AgentService
from components.common import init_page

init_page("Agents")
st.title("Agents")
st.write("Agents Management")
try:
    with st.spinner("Loading agents..."):
        agents = AgentService.get_all()
        if not agents:
            st.warning("No agents found.")
        else:
            st.success(f"Loaded {len(agents)} agents successfully.")
            st.dataframe(
                agents,
                use_container_width=True,
                hide_index=True
            )    
except Exception as e:
    st.error(f"❌ Failed to load agents: {e}")

# -------------------------------------------------------
# Naresh - Newly added section for executing agents
# -------------------------------------------------------
st.subheader("Execute Agent")

user_query = st.text_input(
    "Enter your query",
    placeholder="Example: Create Marketing campaign"
)

if st.button("Execute Agent"):
    if not user_query:
        st.warning("Please enter a query.")
    else:
        try:
            with st.spinner("Executing agent..."):
                result = AgentService.execute({
                    "user_query": user_query
                })

            st.success("Agent executed successfully.")

            st.write("**Selected Agent:**", result["selected_agent"])
            st.write("**Status:**", result["status"])
            st.write("**Result:**", result["result"])
            st.write("**Error:**", result["error"])

        except Exception as e:
            st.error(f"❌ Agent execution failed: {e}")