import sys, os
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
import plotly.express as px
import pandas as pd
from database import query

PALETTE = px.colors.qualitative.Bold
CHURN_COLORS = ["#E74C3C", "#2ECC71"]   # red = churned, green = active


# ── Helpers ────────────────────────────────────────────────────────────────────

def _where(seg, branch, extra=None):
    parts = []
    if seg != "All":
        parts.append(f"segment = '{seg}'")
    if branch != "All":
        parts.append(f"branch = '{branch}'")
    if extra:
        parts.append(extra)
    return "WHERE " + " AND ".join(parts) if parts else ""


# ── Data loaders ───────────────────────────────────────────────────────────────

@st.cache_data
def load_branches():
    return ["All"] + query(
        "SELECT DISTINCT branch FROM customers ORDER BY branch"
    )["branch"].tolist()


@st.cache_data
def load_gender(seg, branch):
    w = _where(seg, branch)
    return query(f"""
        SELECT gender,
               ROUND(AVG(attrition_flag)*100,1) AS attrition_rate,
               COUNT(*) AS customers
        FROM customers {w}
        GROUP BY gender ORDER BY attrition_rate DESC
    """)


@st.cache_data
def load_age(seg, branch):
    w = _where(seg, branch)
    return query(f"""
        SELECT CASE WHEN age < 30 THEN 'Under 30'
                    WHEN age < 40 THEN '30–39'
                    WHEN age < 50 THEN '40–49'
                    ELSE '50+' END AS age_group,
               ROUND(AVG(attrition_flag)*100,1) AS attrition_rate,
               COUNT(*) AS customers
        FROM customers {w}
        GROUP BY age_group ORDER BY MIN(age)
    """)


@st.cache_data
def load_products(seg, branch):
    w = _where(seg, branch)
    row = query(f"""
        SELECT
            ROUND(AVG(CASE WHEN has_loan=1        THEN attrition_flag END)*100,1) AS loan_yes,
            ROUND(AVG(CASE WHEN has_loan=0        THEN attrition_flag END)*100,1) AS loan_no,
            ROUND(AVG(CASE WHEN has_investment=1  THEN attrition_flag END)*100,1) AS inv_yes,
            ROUND(AVG(CASE WHEN has_investment=0  THEN attrition_flag END)*100,1) AS inv_no,
            ROUND(AVG(CASE WHEN has_credit_card=1 THEN attrition_flag END)*100,1) AS card_yes,
            ROUND(AVG(CASE WHEN has_credit_card=0 THEN attrition_flag END)*100,1) AS card_no
        FROM customers {w}
    """).iloc[0]
    return pd.DataFrame([
        {"Product": "Loan",        "Status": "Has Product", "Attrition %": row["loan_yes"]},
        {"Product": "Loan",        "Status": "No Product",  "Attrition %": row["loan_no"]},
        {"Product": "Investment",  "Status": "Has Product", "Attrition %": row["inv_yes"]},
        {"Product": "Investment",  "Status": "No Product",  "Attrition %": row["inv_no"]},
        {"Product": "Credit Card", "Status": "Has Product", "Attrition %": row["card_yes"]},
        {"Product": "Credit Card", "Status": "No Product",  "Attrition %": row["card_no"]},
    ])


@st.cache_data
def load_branch_chart(seg, branch):
    w = _where(seg, branch)
    return query(f"""
        SELECT branch,
               ROUND(AVG(attrition_flag)*100,1) AS attrition_rate,
               COUNT(*) AS customers
        FROM customers {w}
        GROUP BY branch ORDER BY attrition_rate DESC
    """)


@st.cache_data
def load_balance_compare(seg, branch):
    w = _where(seg, branch)
    df = query(f"""
        SELECT segment,
               ROUND(AVG(CASE WHEN attrition_flag=1 THEN balance END), 0) AS Churned,
               ROUND(AVG(CASE WHEN attrition_flag=0 THEN balance END), 0) AS Active
        FROM customers {w}
        GROUP BY segment
    """)
    return df.melt(id_vars="segment", var_name="Status", value_name="avg_balance")


@st.cache_data
def load_activity_compare(seg, branch):
    w = _where(seg, branch)
    df = query(f"""
        SELECT segment,
               ROUND(AVG(CASE WHEN attrition_flag=1 THEN days_since_txn END), 0) AS Churned,
               ROUND(AVG(CASE WHEN attrition_flag=0 THEN days_since_txn END), 0) AS Active
        FROM customers {w}
        GROUP BY segment
    """)
    return df.melt(id_vars="segment", var_name="Status", value_name="avg_days")


@st.cache_data
def load_drill_customers(dim, val, seg, branch):
    age_map = {
        "Under 30": "age < 30",
        "30–39":    "age BETWEEN 30 AND 39",
        "40–49":    "age BETWEEN 40 AND 49",
        "50+":      "age >= 50",
    }
    extra = {
        "gender": f"gender = '{val}'",
        "age":    age_map.get(val),
        "branch": f"branch = '{val}'",
    }.get(dim)

    w = _where(seg, branch, extra)
    return query(f"""
        SELECT customer_id     AS "Customer ID",
               age             AS "Age",
               gender          AS "Gender",
               segment         AS "Segment",
               account_type    AS "Account Type",
               ROUND(balance,0)AS "Balance (OMR)",
               tenure_years    AS "Tenure (Yrs)",
               attrition_type  AS "Exit Type",
               days_since_txn  AS "Days Since Txn"
        FROM customers {w}
        ORDER BY balance DESC
        LIMIT 200
    """)


# ── Main ───────────────────────────────────────────────────────────────────────

def show():
    for k in ["eda_dim", "eda_val"]:
        if k not in st.session_state:
            st.session_state[k] = None

    H = 215
    M = dict(t=5, b=5, l=30, r=10)

    # ── Filter bar ────────────────────────────────────────────────────
    fc1, fc2, fc3 = st.columns([3, 2, 1])
    with fc1:
        seg = st.radio("Segment", ["All", "HNI", "SME", "Retail"],
                       horizontal=True, key="eda_seg")
    with fc2:
        branch = st.selectbox("Branch", load_branches(), key="eda_branch")
    with fc3:
        st.markdown("<div style='margin-top:26px'></div>", unsafe_allow_html=True)
        if st.session_state.eda_dim and st.button("✖ Clear", key="eda_clear"):
            st.session_state.eda_dim = None
            st.session_state.eda_val = None
            st.rerun()

    st.divider()

    # ── Drill-down: customer table ─────────────────────────────────────
    if st.session_state.eda_dim:
        col_h, col_b = st.columns([7, 1])
        with col_h:
            st.markdown(f"**👥 Customers — {st.session_state.eda_val}**")
        with col_b:
            if st.button("⬆️ Back", key="eda_back"):
                st.session_state.eda_dim = None
                st.session_state.eda_val = None
                st.rerun()
        df_c = load_drill_customers(
            st.session_state.eda_dim, st.session_state.eda_val, seg, branch)
        st.dataframe(df_c, use_container_width=True,
                     height=min(36 * len(df_c) + 38, 400), hide_index=True)
        st.caption(f"{len(df_c)} customers shown (max 200)")
        return

    # ── Row 1: Attrition Drivers ──────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption("**Attrition Rate by Gender** · 💡 click to drill down")
        df1 = load_gender(seg, branch)
        fig1 = px.bar(df1, x="gender", y="attrition_rate", color="gender",
                      text="attrition_rate",
                      color_discrete_sequence=PALETTE, height=H)
        fig1.update_traces(texttemplate="%{text}%", textposition="outside")
        fig1.update_layout(showlegend=False, yaxis_range=[0, 100], margin=M,
                           xaxis_title="", yaxis_title="",
                           dragmode=False, clickmode="event+select")
        ev1 = st.plotly_chart(fig1, use_container_width=True, on_select="rerun",
                              key="eda_g", selection_mode="points")
        if ev1 and ev1.selection and ev1.selection.points:
            st.session_state.eda_dim = "gender"
            st.session_state.eda_val = ev1.selection.points[0]["x"]
            st.rerun()

    with col2:
        st.caption("**Attrition Rate by Age Group** · 💡 click to drill down")
        df2 = load_age(seg, branch)
        fig2 = px.bar(df2, x="age_group", y="attrition_rate", color="age_group",
                      text="attrition_rate",
                      color_discrete_sequence=px.colors.qualitative.Pastel, height=H)
        fig2.update_traces(texttemplate="%{text}%", textposition="outside")
        fig2.update_layout(showlegend=False, yaxis_range=[0, 100], margin=M,
                           xaxis_title="", yaxis_title="",
                           dragmode=False, clickmode="event+select")
        ev2 = st.plotly_chart(fig2, use_container_width=True, on_select="rerun",
                              key="eda_a", selection_mode="points")
        if ev2 and ev2.selection and ev2.selection.points:
            st.session_state.eda_dim = "age"
            st.session_state.eda_val = ev2.selection.points[0]["x"]
            st.rerun()

    with col3:
        st.caption("**Product Holding vs Attrition Rate**")
        df3 = load_products(seg, branch)
        fig3 = px.bar(df3, x="Product", y="Attrition %", color="Status",
                      barmode="group", text="Attrition %",
                      color_discrete_sequence=CHURN_COLORS, height=H)
        fig3.update_traces(texttemplate="%{text}%", textposition="outside")
        fig3.update_layout(yaxis_range=[0, 100], margin=M,
                           xaxis_title="", yaxis_title="",
                           legend=dict(orientation="h", y=1.1, x=0.2))
        st.plotly_chart(fig3, use_container_width=True)

    # ── Row 2: Segment & Branch Comparison ────────────────────────────
    st.markdown("<div style='margin-top:4px'></div>", unsafe_allow_html=True)
    col4, col5, col6 = st.columns(3)

    with col4:
        st.caption("**Attrition Rate by Branch** · 💡 click to drill down")
        df4 = load_branch_chart(seg, branch)
        fig4 = px.bar(df4, x="branch", y="attrition_rate",
                      color="attrition_rate", text="attrition_rate",
                      color_continuous_scale="Reds", height=H)
        fig4.update_traces(texttemplate="%{text}%", textposition="outside")
        fig4.update_layout(coloraxis_showscale=False, yaxis_range=[0, 100],
                           margin=M, xaxis_title="", yaxis_title="",
                           dragmode=False, clickmode="event+select")
        ev4 = st.plotly_chart(fig4, use_container_width=True, on_select="rerun",
                              key="eda_b", selection_mode="points")
        if ev4 and ev4.selection and ev4.selection.points:
            st.session_state.eda_dim = "branch"
            st.session_state.eda_val = ev4.selection.points[0]["x"]
            st.rerun()

    with col5:
        st.caption("**Avg Balance — Churned vs Active by Segment**")
        df5 = load_balance_compare(seg, branch)
        fig5 = px.bar(df5, x="segment", y="avg_balance", color="Status",
                      barmode="group", text="avg_balance",
                      color_discrete_sequence=CHURN_COLORS, height=H)
        fig5.update_traces(texttemplate="OMR %{text:,.0f}", textposition="outside")
        fig5.update_layout(margin=M, xaxis_title="", yaxis_title="",
                           legend=dict(orientation="h", y=1.1, x=0.2))
        st.plotly_chart(fig5, use_container_width=True)

    with col6:
        st.caption("**Avg Days Since Txn — Churned vs Active by Segment**")
        df6 = load_activity_compare(seg, branch)
        fig6 = px.bar(df6, x="segment", y="avg_days", color="Status",
                      barmode="group", text="avg_days",
                      color_discrete_sequence=CHURN_COLORS, height=H)
        fig6.update_traces(texttemplate="%{text}d", textposition="outside")
        fig6.update_layout(margin=M, xaxis_title="", yaxis_title="",
                           legend=dict(orientation="h", y=1.1, x=0.2))
        st.plotly_chart(fig6, use_container_width=True)
