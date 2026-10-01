import streamlit as st
from pathlib import Path

from components.common import init_page


init_page("AAMP")

st.write("Welcome to the Agentic AI Marketing Platform.")

image_path = Path(__file__).parent / "assets" / "aamp_home.png"

st.markdown(
    '<div style="margin-top:-20px;">',
    unsafe_allow_html=True,
)

st.image(
    image_path,
    use_container_width=True,
)

st.markdown("</div>", unsafe_allow_html=True)