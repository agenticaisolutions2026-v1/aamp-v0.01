import streamlit as st
#from pages.organizations import show_organizations

st.set_page_config(
    page_title="AAMP",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {
        display:none;
    }
    </style>
    """, unsafe_allow_html=True)
from components.sidebar import create_sidebar
from components.header import create_header
create_sidebar()
create_header()
#st.title("Agentic AI Marketing Platform")
st.write("Welcome")