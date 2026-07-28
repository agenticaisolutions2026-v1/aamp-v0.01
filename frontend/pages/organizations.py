import streamlit as st
import pandas as pd

# ------------------------------------------------
# Page Configuration
# ------------------------------------------------
st.set_page_config(
    page_title="Organizations",
    page_icon="🏫",
    layout="wide"
)

# ------------------------------------------------
# Page Title
# ------------------------------------------------
st.title("🏫 Organizations")
st.write("Manage Colleges and Educational Institutions")

# ------------------------------------------------
# Summary Cards
# ------------------------------------------------
st.subheader("📈 Organization Summary")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="
        background-color:#E3F2FD;
        padding:20px;
        border-radius:12px;
        text-align:center;
        box-shadow:2px 2px 8px rgba(0,0,0,0.1);">
        <h4>🏫 Total Colleges</h4>
        <h2 style="color:#1565C0;">120</h2>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="
        background-color:#E8F5E9;
        padding:20px;
        border-radius:12px;
        text-align:center;
        box-shadow:2px 2px 8px rgba(0,0,0,0.1);">
        <h4>🌎 States Covered</h4>
        <h2 style="color:#2E7D32;">5</h2>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="
        background-color:#F3E5F5;
        padding:20px;
        border-radius:12px;
        text-align:center;
        box-shadow:2px 2px 8px rgba(0,0,0,0.1);">
        <h4>🤖 AI/ML Departments</h4>
        <h2 style="color:#6A1B9A;">45</h2>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ------------------------------------------------
# Search Filters
# ------------------------------------------------
st.subheader("🔍 Search Organizations")

col1, col2 = st.columns(2)

with col1:
    state = st.selectbox(
        "Select State",
        [
            "Telangana",
            "Andhra Pradesh",
            "Tamil Nadu",
            "Karnataka",
            "Kerala"
        ]
    )

with col2:
    department = st.selectbox(
        "Department",
        [
            "All",
            "AI & ML",
            "Computer Science",
            "Data Science",
            "ECE"
        ]
    )

st.text_input("🔎 Search College")

col1, col2 = st.columns(2)

with col1:
    st.button("🔍 Find Colleges")

with col2:
    st.button("❌ Clear Search")

st.divider()

# ------------------------------------------------
# Sample Data
# ------------------------------------------------
st.subheader("🏫 College List")

df = pd.DataFrame({
    "College": [
        "VNR VJIET",
        "CBIT",
        "JNTUH",
        "MGIT",
        "KL University",
        "VIT AP"
    ],
    "State": [
        "Telangana",
        "Telangana",
        "Telangana",
        "Telangana",
        "Andhra Pradesh",
        "Andhra Pradesh"
    ],
    "Department": [
        "AI & ML",
        "Computer Science",
        "ECE",
        "AI & DS",
        "Computer Science",
        "AI & ML"
    ],
    "Website": [
        "www.vnrvjiet.ac.in",
        "www.cbit.ac.in",
        "www.jntuh.ac.in",
        "www.mgit.ac.in",
        "www.kluniversity.in",
        "www.vitap.ac.in"
    ]
})

st.dataframe(df, use_container_width=True)

st.success("✅ Organization data loaded successfully.")