import streamlit as st

def create_header():
    st.markdown(
        """
        <div style="
            background-color:#0E4D92;
            color:white;
            padding:18px;
            border-radius:8px;
            margin-top:0
            margin-bottom:25px;
        ">
            <h2 style="margin:0;">
                Agentic AI Marketing Platform (AAMP)
            </h2>
            <p style="margin:0;font-size:16px;">
                Intelligent Campaign Management using AI Agents
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )