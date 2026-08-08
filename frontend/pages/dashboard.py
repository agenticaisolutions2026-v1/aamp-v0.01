import streamlit as st
from components.common import init_page

init_page("Dashboard")
st.title("Dashboard")

st.metric("Organizations", 25)
st.metric("Campaigns", 108)