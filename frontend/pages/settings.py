import streamlit as st

# ------------------------------------------------
# Page Configuration
# ------------------------------------------------
st.set_page_config(
    page_title="Settings",
    page_icon="⚙️",
    layout="wide"
)

# ------------------------------------------------
# Page Title
# ------------------------------------------------
st.title("⚙️ Settings")
st.write("Configure your Agentic AI Marketing Platform")

# ------------------------------------------------
# Organization Settings
# ------------------------------------------------
st.subheader("🏢 Organization Settings")

col1, col2 = st.columns(2)

with col1:
    organization = st.text_input("Organization Name")

with col2:
    admin = st.text_input("Administrator Name")

st.divider()

# ------------------------------------------------
# AI Configuration
# ------------------------------------------------
st.subheader("🤖 AI Configuration")

col1, col2 = st.columns(2)

with col1:
    api_key = st.text_input("OpenAI API Key", type="password")

with col2:
    model = st.selectbox(
        "LLM Model",
        [
            "GPT-4",
            "GPT-4.1",
            "Gemini 2.5",
            "Llama 3"
        ]
    )

st.divider()

# ------------------------------------------------
# Email Configuration
# ------------------------------------------------
st.subheader("📧 Email Configuration")

col1, col2 = st.columns(2)

with col1:
    sender = st.text_input("Sender Email")

    smtp_server = st.text_input("SMTP Server")

with col2:
    smtp_port = st.number_input(
        "SMTP Port",
        value=587
    )

    password = st.text_input(
        "Email Password",
        type="password"
    )

st.divider()

# ------------------------------------------------
# Notification Settings
# ------------------------------------------------
st.subheader("🔔 Notifications")

email_notification = st.checkbox("Email Notifications", value=True)

meeting_notification = st.checkbox("Meeting Notifications", value=True)

campaign_notification = st.checkbox("Campaign Alerts", value=True)

st.divider()

# ------------------------------------------------
# Buttons
# ------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.button("💾 Save Settings")

with col2:
    st.button("🔄 Reset Settings")

st.success("Settings page loaded successfully.")