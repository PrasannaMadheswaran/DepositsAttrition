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
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        .main { background-color: #EEF4FB !important; }
        [data-testid="stMetric"] {
            background-color: #FFFFFF;
            border-radius: 8px;
            padding: 0.4rem 0.6rem !important;
        }
    </style>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Overview",
    "📉 Churn Trends",
    "🔍 Risk Analysis",
    "⚠️ Action List",
    "🧠 Ask the Data",
    "📖 Guide",
])

with tab1:
    from pages import _overview as overview
    overview.show()

with tab2:
    from pages import _trends as trends
    trends.show()

with tab3:
    from pages import _eda as eda
    eda.show()

with tab4:
    from pages import _action_list as action_list
    action_list.show()

with tab5:
    from pages import _nl_query as nl_query
    nl_query.show()

with tab6:
    from pages import _docs as docs
    docs.show()
