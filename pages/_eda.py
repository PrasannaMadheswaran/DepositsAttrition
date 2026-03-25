import sys, os
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
import plotly.express as px
import pandas as pd
from database import query

PALETTE      = px.colors.qualitative.Bold
CHURN_COLORS = ["#E74C3C", "#2ECC71"]   # red = churned, green = active

# ── SQL helper ─────────────────────────────────────────────────────────────────

def _where(seg, branch, extra=None):
    parts = []
    if seg    != "All": parts.append(f"segment = '{seg}'")
    if branch != "All": parts.append(f"branch  = '{branch}'")
    if extra:           parts.append(extra)
    return "WHERE " + " AND ".join(parts) if parts else ""


# ── Data loaders ───────────────────────────────────────────────────────────────

@st.cache_data
def load_branches():
    return ["All"] + query(
        "SELECT DISTINCT branch FROM customers ORDER BY branch"
    )["branch"].tolist()


@st.cache_data
def load_risk_factors(seg, branch):
    """Attrition rate when each risk indicator is present."""
    w = _where(seg, branch)
    row = query(f"""
        SELECT
            ROUND(AVG(CASE WHEN salary_diverted   = 1      THEN attrition_flag END)*100,1) AS salary_diverted,
            ROUND(AVG(CASE WHEN days_since_txn    > 90     THEN attrition_flag END)*100,1) AS txn_inactive,
            ROUND(AVG(CASE WHEN low_balance_days  > 30     THEN attrition_flag END)*100,1) AS low_balance,
            ROUND(AVG(CASE WHEN complaint_count   >= 1     THEN attrition_flag END)*100,1) AS has_complaint,
            ROUND(AVG(CASE WHEN digital_banking_active = 0 THEN attrition_flag END)*100,1) AS digital_inactive,
            ROUND(AVG(CASE WHEN nps_score         <= 30    THEN attrition_flag END)*100,1) AS low_nps
        FROM customers {w}
    """).iloc[0]
    return pd.DataFrame([
        {"Risk Factor": "Salary Diverted",     "Attrition %": row["salary_diverted"]},
        {"Risk Factor": "Txn Inactive > 90d",  "Attrition %": row["txn_inactive"]},
        {"Risk Factor": "Low Balance > 30d",   "Attrition %": row["low_balance"]},
        {"Risk Factor": "Has Complaint",        "Attrition %": row["has_complaint"]},
        {"Risk Factor": "Digital Inactive",     "Attrition %": row["digital_inactive"]},
        {"Risk Factor": "NPS ≤ 30",             "Attrition %": row["low_nps"]},
    ]).sort_values("Attrition %", ascending=True)


# mapping: Risk Factor label → SQL condition for drill-down
_RISK_CONDITIONS = {
    "Salary Diverted":    "salary_diverted = 1",
    "Txn Inactive > 90d": "days_since_txn > 90",
    "Low Balance > 30d":  "low_balance_days > 30",
    "Has Complaint":      "complaint_count >= 1",
    "Digital Inactive":   "digital_banking_active = 0",
    "NPS ≤ 30":          "nps_score <= 30",
}


@st.cache_data
def load_nps_bands(seg, branch):
    w = _where(seg, branch)
    return query(f"""
        SELECT CASE WHEN nps_score <= 30 THEN 'Detractor (≤30)'
                    WHEN nps_score <= 70 THEN 'Passive (31–70)'
                    ELSE 'Promoter (>70)' END AS nps_band,
               ROUND(AVG(attrition_flag)*100,1) AS attrition_rate,
               COUNT(*) AS customers
        FROM customers {w}
        GROUP BY nps_band
        ORDER BY MIN(nps_score)
    """)


@st.cache_data
def load_complaints(seg, branch):
    w = _where(seg, branch)
    return query(f"""
        SELECT CASE WHEN complaint_count = 0 THEN '0'
                    WHEN complaint_count = 1 THEN '1'
                    WHEN complaint_count = 2 THEN '2'
                    ELSE '3+' END AS complaints,
               ROUND(AVG(attrition_flag)*100,1) AS attrition_rate,
               COUNT(*) AS customers
        FROM customers {w}
        GROUP BY complaints
        ORDER BY MIN(complaint_count)
    """)


@st.cache_data
def load_balance_profile(seg, branch):
    w = _where(seg, branch)
    df = query(f"""
        SELECT segment,
               ROUND(AVG(CASE WHEN attrition_flag=1 THEN balance END), 0) AS Churned,
               ROUND(AVG(CASE WHEN attrition_flag=0 THEN balance END), 0) AS Active
        FROM customers {w} GROUP BY segment
    """)
    return df.melt(id_vars="segment", var_name="Status", value_name="avg_balance")


@st.cache_data
def load_activity_profile(seg, branch):
    w = _where(seg, branch)
    df = query(f"""
        SELECT segment,
               ROUND(AVG(CASE WHEN attrition_flag=1 THEN days_since_txn END), 0) AS Churned,
               ROUND(AVG(CASE WHEN attrition_flag=0 THEN days_since_txn END), 0) AS Active
        FROM customers {w} GROUP BY segment
    """)
    return df.melt(id_vars="segment", var_name="Status", value_name="avg_days")


@st.cache_data
def load_products_profile(seg, branch):
    w = _where(seg, branch)
    df = query(f"""
        SELECT segment,
               ROUND(AVG(CASE WHEN attrition_flag=1 THEN num_products END), 2) AS Churned,
               ROUND(AVG(CASE WHEN attrition_flag=0 THEN num_products END), 2) AS Active
        FROM customers {w} GROUP BY segment
    """)
    return df.melt(id_vars="segment", var_name="Status", value_name="avg_products")


@st.cache_data
def load_drill_customers(dim, val, seg, branch):
    nps_map = {
        "Detractor (≤30)": "nps_score <= 30",
        "Passive (31–70)": "nps_score BETWEEN 31 AND 70",
        "Promoter (>70)":  "nps_score > 70",
    }
    complaint_map = {
        "0":  "complaint_count = 0",
        "1":  "complaint_count = 1",
        "2":  "complaint_count = 2",
        "3+": "complaint_count >= 3",
    }
    extra = (
        _RISK_CONDITIONS.get(val)    if dim == "risk"      else
        nps_map.get(val)             if dim == "nps"       else
        complaint_map.get(val)       if dim == "complaint" else
        None
    )
    w = _where(seg, branch, extra)
    return query(f"""
        SELECT customer_id      AS "Customer ID",
               age              AS "Age",
               gender           AS "Gender",
               segment          AS "Segment",
               account_type     AS "Account Type",
               ROUND(balance,0) AS "Balance (OMR)",
               tenure_years     AS "Tenure (Yrs)",
               nps_score        AS "NPS",
               complaint_count  AS "Complaints",
               attrition_type   AS "Exit Type",
               days_since_txn   AS "Days Since Txn"
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

    # ══════════════════════════════════════════════════════════════════
    # ROW 1 — Risk Drivers  (what triggers churn?)
    # ══════════════════════════════════════════════════════════════════
    st.markdown("##### 🔴 Risk Drivers — what triggers churn?")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption("**Attrition Rate by Risk Factor** · 💡 click to drill down")
        df1 = load_risk_factors(seg, branch)
        fig1 = px.bar(df1, x="Attrition %", y="Risk Factor", orientation="h",
                      color="Attrition %", text="Attrition %",
                      color_continuous_scale="Reds", height=H)
        fig1.update_traces(texttemplate="%{text}%", textposition="outside")
        fig1.update_layout(coloraxis_showscale=False, xaxis_range=[0, 110],
                           margin=M, xaxis_title="", yaxis_title="",
                           dragmode=False, clickmode="event+select")
        ev1 = st.plotly_chart(fig1, use_container_width=True, on_select="rerun",
                              key="eda_risk", selection_mode="points")
        if ev1 and ev1.selection and ev1.selection.points:
            st.session_state.eda_dim = "risk"
            st.session_state.eda_val = ev1.selection.points[0]["y"]
            st.rerun()

    with col2:
        st.caption("**NPS Band vs Attrition Rate** · 💡 click to drill down")
        df2 = load_nps_bands(seg, branch)
        colors = {"Detractor (≤30)":  "#E74C3C",
                  "Passive (31–70)":  "#F39C12",
                  "Promoter (>70)":   "#2ECC71"}
        fig2 = px.bar(df2, x="nps_band", y="attrition_rate",
                      color="nps_band", text="attrition_rate",
                      color_discrete_map=colors, height=H)
        fig2.update_traces(texttemplate="%{text}%", textposition="outside")
        fig2.update_layout(showlegend=False, yaxis_range=[0, 100], margin=M,
                           xaxis_title="", yaxis_title="",
                           dragmode=False, clickmode="event+select")
        ev2 = st.plotly_chart(fig2, use_container_width=True, on_select="rerun",
                              key="eda_nps", selection_mode="points")
        if ev2 and ev2.selection and ev2.selection.points:
            st.session_state.eda_dim = "nps"
            st.session_state.eda_val = ev2.selection.points[0]["x"]
            st.rerun()

    with col3:
        st.caption("**Complaint Count vs Attrition Rate** · 💡 click to drill down")
        df3 = load_complaints(seg, branch)
        fig3 = px.bar(df3, x="complaints", y="attrition_rate",
                      color="attrition_rate", text="attrition_rate",
                      color_continuous_scale="Oranges", height=H)
        fig3.update_traces(texttemplate="%{text}%", textposition="outside")
        fig3.update_layout(coloraxis_showscale=False, yaxis_range=[0, 100],
                           margin=M, xaxis_title="No. of Complaints", yaxis_title="",
                           dragmode=False, clickmode="event+select")
        ev3 = st.plotly_chart(fig3, use_container_width=True, on_select="rerun",
                              key="eda_comp", selection_mode="points")
        if ev3 and ev3.selection and ev3.selection.points:
            st.session_state.eda_dim = "complaint"
            st.session_state.eda_val = ev3.selection.points[0]["x"]
            st.rerun()

    # ══════════════════════════════════════════════════════════════════
    # ROW 2 — Behavioural Profile  (how do churners differ?)
    # ══════════════════════════════════════════════════════════════════
    st.markdown("<div style='margin-top:4px'></div>", unsafe_allow_html=True)
    st.markdown("##### 🔵 Behavioural Profile — how do churners differ from active customers?")
    col4, col5, col6 = st.columns(3)

    with col4:
        st.caption("**Avg Balance — Churned vs Active**")
        df4 = load_balance_profile(seg, branch)
        fig4 = px.bar(df4, x="segment", y="avg_balance", color="Status",
                      barmode="group", text="avg_balance",
                      color_discrete_sequence=CHURN_COLORS, height=H)
        fig4.update_traces(texttemplate="OMR %{text:,.0f}", textposition="outside")
        fig4.update_layout(margin=M, xaxis_title="", yaxis_title="",
                           legend=dict(orientation="h", y=1.12, x=0.15))
        st.plotly_chart(fig4, use_container_width=True)

    with col5:
        st.caption("**Avg Days Since Last Txn — Churned vs Active**")
        df5 = load_activity_profile(seg, branch)
        fig5 = px.bar(df5, x="segment", y="avg_days", color="Status",
                      barmode="group", text="avg_days",
                      color_discrete_sequence=CHURN_COLORS, height=H)
        fig5.update_traces(texttemplate="%{text}d", textposition="outside")
        fig5.update_layout(margin=M, xaxis_title="", yaxis_title="",
                           legend=dict(orientation="h", y=1.12, x=0.15))
        st.plotly_chart(fig5, use_container_width=True)

    with col6:
        st.caption("**Avg Products Held — Churned vs Active**")
        df6 = load_products_profile(seg, branch)
        fig6 = px.bar(df6, x="segment", y="avg_products", color="Status",
                      barmode="group", text="avg_products",
                      color_discrete_sequence=CHURN_COLORS, height=H)
        fig6.update_traces(texttemplate="%{text}", textposition="outside")
        fig6.update_layout(margin=M, xaxis_title="", yaxis_title="",
                           legend=dict(orientation="h", y=1.12, x=0.15))
        st.plotly_chart(fig6, use_container_width=True)
