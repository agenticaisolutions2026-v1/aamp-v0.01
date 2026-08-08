import streamlit as st
from components.sidebar import create_sidebar
from components.header import create_header

def init_page(title):
    st.set_page_config(
        page_title=title,
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
    create_sidebar()
    create_header()