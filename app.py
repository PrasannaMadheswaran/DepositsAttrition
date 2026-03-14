# ============================================================
#  Deposits Attrition Data App  —  Main Entry Point
#  Run with:  streamlit run app.py
# ============================================================

import streamlit as st

st.set_page_config(
    page_title="Deposits Attrition App",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar navigation ──────────────────────────────────────
st.sidebar.title("🏦 Deposits Attrition")
st.sidebar.caption("Financial Institution · Analytics MVP")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigate",
    [
        "📊 Overview",
        "🔍 EDA",
        "🤖 ML Model",
        "⚠️ Risk Scoring",
    ],
)

st.sidebar.divider()
st.sidebar.info("Built step-by-step with Claude · MVP v1.0")

# ── Route to pages ───────────────────────────────────────────
if page == "📊 Overview":
    from pages import overview
    overview.show()

elif page == "🔍 EDA":
    from pages import eda
    eda.show()

elif page == "🤖 ML Model":
    from pages import model
    model.show()

elif page == "⚠️ Risk Scoring":
    from pages import risk_scoring
    risk_scoring.show()
