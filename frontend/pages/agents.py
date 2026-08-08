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