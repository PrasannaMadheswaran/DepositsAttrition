import streamlit as st

st.set_page_config(page_title="Deposits Attrition", page_icon="🏦",
                   layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        [data-testid="collapsedControl"] { display: none; }
        .block-container { padding-top: 0.3rem; padding-bottom: 0rem; }
        header { visibility: hidden; }
        div[data-testid="stTabs"] { margin-top: 0rem; }
        div[data-testid="stMetric"] { padding: 0.2rem 0; }
        div[data-testid="stVerticalBlock"] { gap: 0rem; }
    </style>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🔍 EDA", "🤖 ML Model", "⚠️ Risk Scoring"])

with tab1:
    from pages import _overview as overview
    overview.show()

with tab2:
    st.info("🔜 EDA coming soon!")

with tab3:
    st.info("🔜 ML Model coming soon!")

with tab4:
    st.info("🔜 Risk Scoring coming soon!")
