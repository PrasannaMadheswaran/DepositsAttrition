import sys, os
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
import plotly.express as px
import pandas as pd
from database import query

PALETTE      = px.colors.qualitative.Bold
RISK_COLORS  = {"High": "#E74C3C", "Medium": "#E67E22", "Low": "#F1C40F", "Safe": "#2ECC71"}
STATUS_COLORS = ["#E74C3C", "#2ECC71"]   # At-Risk = red, Safe = green

_SIGNAL_CONDITIONS = {
    "Salary Diverted"     : "sig_salary_diverted = 1",
    "Txn Inactive >90d"   : "sig_txn_inactive = 1",
    "Low Balance >30d"    : "sig_low_balance = 1",
    "Complaints ≥2"       : "sig_complaints = 1",
    "Digital Inactive"    : "sig_digital_inactive = 1",
    "FD/RD Maturing"      : "sig_fd_maturing = 1",
    "NPS ≤30"             : "sig_low_nps = 1",
}


def _where(seg, branch, extra=None):
    parts = ["customer_status IN ('Active','Inactive')"]
    if seg    != "All": parts.append(f"segment = '{seg}'")
    if branch != "All": parts.append(f"branch  = '{branch}'")
    if extra:           parts.append(extra)
    return "WHERE " + " AND ".join(parts)


@st.cache_data
def load_branches():
    return ["All"] + query(
        "SELECT DISTINCT branch FROM customers ORDER BY branch"
    )["branch"].tolist()


@st.cache_data
def load_signal_rates(seg, branch):
    """% of customers with each signal who are High/Medium risk."""
    w = _where(seg, branch)
    row = query(f"""
        SELECT
            ROUND(AVG(CASE WHEN sig_salary_diverted=1  THEN CASE WHEN risk_level IN ('High','Medium') THEN 1.0 ELSE 0 END END)*100,1) AS sal,
            ROUND(AVG(CASE WHEN sig_txn_inactive=1     THEN CASE WHEN risk_level IN ('High','Medium') THEN 1.0 ELSE 0 END END)*100,1) AS txn,
            ROUND(AVG(CASE WHEN sig_low_balance=1      THEN CASE WHEN risk_level IN ('High','Medium') THEN 1.0 ELSE 0 END END)*100,1) AS bal,
            ROUND(AVG(CASE WHEN sig_complaints=1       THEN CASE WHEN risk_level IN ('High','Medium') THEN 1.0 ELSE 0 END END)*100,1) AS comp,
            ROUND(AVG(CASE WHEN sig_digital_inactive=1 THEN CASE WHEN risk_level IN ('High','Medium') THEN 1.0 ELSE 0 END END)*100,1) AS dig,
            ROUND(AVG(CASE WHEN sig_fd_maturing=1      THEN CASE WHEN risk_level IN ('High','Medium') THEN 1.0 ELSE 0 END END)*100,1) AS fd,
            ROUND(AVG(CASE WHEN sig_low_nps=1          THEN CASE WHEN risk_level IN ('High','Medium') THEN 1.0 ELSE 0 END END)*100,1) AS nps
        FROM customers {w}
    """).iloc[0]
    return pd.DataFrame([
        {"Signal": "Salary Diverted",   "At-Risk %": row["sal"]},
        {"Signal": "Txn Inactive >90d", "At-Risk %": row["txn"]},
        {"Signal": "Low Balance >30d",  "At-Risk %": row["bal"]},
        {"Signal": "Complaints ≥2",     "At-Risk %": row["comp"]},
        {"Signal": "Digital Inactive",  "At-Risk %": row["dig"]},
        {"Signal": "FD/RD Maturing",    "At-Risk %": row["fd"]},
        {"Signal": "NPS ≤30",           "At-Risk %": row["nps"]},
    ]).sort_values("At-Risk %", ascending=True)


@st.cache_data
def load_nps_bands(seg, branch):
    w = _where(seg, branch)
    return query(f"""
        SELECT CASE WHEN nps_score <= 30 THEN 'Detractor (≤30)'
                    WHEN nps_score <= 70 THEN 'Passive (31–70)'
                    ELSE 'Promoter (>70)' END AS nps_band,
               ROUND(AVG(CASE WHEN risk_level IN ('High','Medium') THEN 1.0 ELSE 0 END)*100,1)
                   AS at_risk_pct,
               COUNT(*) AS customers
        FROM customers {w}
        GROUP BY nps_band ORDER BY MIN(nps_score)
    """)


@st.cache_data
def load_complaints(seg, branch):
    w = _where(seg, branch)
    return query(f"""
        SELECT CASE WHEN complaint_count=0 THEN '0'
                    WHEN complaint_count=1 THEN '1'
                    WHEN complaint_count=2 THEN '2'
                    ELSE '3+' END AS complaints,
               ROUND(AVG(CASE WHEN risk_level IN ('High','Medium') THEN 1.0 ELSE 0 END)*100,1)
                   AS at_risk_pct,
               COUNT(*) AS customers
        FROM customers {w}
        GROUP BY complaints ORDER BY MIN(complaint_count)
    """)


@st.cache_data
def load_balance_profile(seg, branch):
    w = _where(seg, branch)
    df = query(f"""
        SELECT segment,
               ROUND(AVG(CASE WHEN risk_level IN ('High','Medium') THEN balance END),0) AS "At-Risk",
               ROUND(AVG(CASE WHEN risk_level IN ('Low','Safe')    THEN balance END),0) AS "Safe"
        FROM customers {w} GROUP BY segment
    """)
    return df.melt(id_vars="segment", var_name="Status", value_name="avg_balance")


@st.cache_data
def load_activity_profile(seg, branch):
    w = _where(seg, branch)
    df = query(f"""
        SELECT segment,
               ROUND(AVG(CASE WHEN risk_level IN ('High','Medium') THEN days_since_txn END),0) AS "At-Risk",
               ROUND(AVG(CASE WHEN risk_level IN ('Low','Safe')    THEN days_since_txn END),0) AS "Safe"
        FROM customers {w} GROUP BY segment
    """)
    return df.melt(id_vars="segment", var_name="Status", value_name="avg_days")


@st.cache_data
def load_products_profile(seg, branch):
    w = _where(seg, branch)
    df = query(f"""
        SELECT segment,
               ROUND(AVG(CASE WHEN risk_level IN ('High','Medium') THEN num_products END),2) AS "At-Risk",
               ROUND(AVG(CASE WHEN risk_level IN ('Low','Safe')    THEN num_products END),2) AS "Safe"
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
        "0": "complaint_count = 0", "1": "complaint_count = 1",
        "2": "complaint_count = 2", "3+": "complaint_count >= 3",
    }
    extra = (
        _SIGNAL_CONDITIONS.get(val) if dim == "signal"    else
        nps_map.get(val)            if dim == "nps"       else
        complaint_map.get(val)      if dim == "complaint" else
        None
    )
    w = _where(seg, branch, extra)
    return query(f"""
        SELECT customer_id      AS "Customer ID",
               customer_status  AS "Status",
               risk_level       AS "Risk Level",
               segment          AS "Segment",
               account_type     AS "Account Type",
               ROUND(balance,0) AS "Balance (OMR)",
               tenure_years     AS "Tenure (Yrs)",
               days_since_txn   AS "Days Since Txn",
               nps_score        AS "NPS",
               complaint_count  AS "Complaints",
               risk_signal_count AS "Signals"
        FROM customers {w}
        ORDER BY
            CASE risk_level WHEN 'High' THEN 1 WHEN 'Medium' THEN 2
                            WHEN 'Low' THEN 3 ELSE 4 END,
            balance DESC
        LIMIT 200
    """)


def show():
    for k in ["eda_dim", "eda_val"]:
        if k not in st.session_state:
            st.session_state[k] = None

    H = 215
    M = dict(t=5, b=5, l=30, r=10)

    # ── Filter bar ─────────────────────────────────────────────────────
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

    # ── Drill-down: customer table ──────────────────────────────────────
    if st.session_state.eda_dim:
        col_h, col_b = st.columns([7, 1])
        with col_h:
            st.markdown(f"**👥 Active Customers — {st.session_state.eda_val}**")
        with col_b:
            if st.button("⬆️ Back", key="eda_back"):
                st.session_state.eda_dim = None
                st.session_state.eda_val = None
                st.rerun()
        df_c = load_drill_customers(
            st.session_state.eda_dim, st.session_state.eda_val, seg, branch)
        st.dataframe(df_c, use_container_width=True,
                     height=min(36*len(df_c)+38, 400), hide_index=True)
        st.caption(f"{len(df_c)} customers shown (max 200) · sorted by risk level then balance")
        return

    # ══════════════════════════════════════════════════════════════════
    # ROW 1 — Risk Drivers
    # ══════════════════════════════════════════════════════════════════
    st.markdown("##### 🔴 Risk Drivers — which signals predict attrition?")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption("**At-Risk Rate by Signal** · 💡 click to see those customers")
        df1 = load_signal_rates(seg, branch)
        fig1 = px.bar(df1, x="At-Risk %", y="Signal", orientation="h",
                      color="At-Risk %", text="At-Risk %",
                      color_continuous_scale="Reds", height=H)
        fig1.update_traces(texttemplate="%{text}%", textposition="outside")
        fig1.update_layout(coloraxis_showscale=False, xaxis_range=[0,115],
                           margin=M, xaxis_title="", yaxis_title="",
                           dragmode=False, clickmode="event+select")
        ev1 = st.plotly_chart(fig1, use_container_width=True, on_select="rerun",
                              key="eda_signal", selection_mode="points")
        if ev1 and ev1.selection and ev1.selection.points:
            st.session_state.eda_dim = "signal"
            st.session_state.eda_val = ev1.selection.points[0]["y"]
            st.rerun()

    with col2:
        st.caption("**NPS Band vs At-Risk Rate** · 💡 click to drill down")
        df2 = load_nps_bands(seg, branch)
        nps_colors = {"Detractor (≤30)": "#E74C3C",
                      "Passive (31–70)":  "#F39C12",
                      "Promoter (>70)":   "#2ECC71"}
        fig2 = px.bar(df2, x="nps_band", y="at_risk_pct",
                      color="nps_band", text="at_risk_pct",
                      color_discrete_map=nps_colors, height=H)
        fig2.update_traces(texttemplate="%{text}%", textposition="outside")
        fig2.update_layout(showlegend=False, yaxis_range=[0,100], margin=M,
                           xaxis_title="", yaxis_title="At-Risk %",
                           dragmode=False, clickmode="event+select")
        ev2 = st.plotly_chart(fig2, use_container_width=True, on_select="rerun",
                              key="eda_nps", selection_mode="points")
        if ev2 and ev2.selection and ev2.selection.points:
            st.session_state.eda_dim = "nps"
            st.session_state.eda_val = ev2.selection.points[0]["x"]
            st.rerun()

    with col3:
        st.caption("**Complaints vs At-Risk Rate** · 💡 click to drill down")
        df3 = load_complaints(seg, branch)
        fig3 = px.bar(df3, x="complaints", y="at_risk_pct",
                      color="at_risk_pct", text="at_risk_pct",
                      color_continuous_scale="Oranges", height=H)
        fig3.update_traces(texttemplate="%{text}%", textposition="outside")
        fig3.update_layout(coloraxis_showscale=False, yaxis_range=[0,100],
                           margin=M, xaxis_title="No. of Complaints", yaxis_title="",
                           dragmode=False, clickmode="event+select")
        ev3 = st.plotly_chart(fig3, use_container_width=True, on_select="rerun",
                              key="eda_comp", selection_mode="points")
        if ev3 and ev3.selection and ev3.selection.points:
            st.session_state.eda_dim = "complaint"
            st.session_state.eda_val = ev3.selection.points[0]["x"]
            st.rerun()

    # ══════════════════════════════════════════════════════════════════
    # ROW 2 — Behavioural Profile
    # ══════════════════════════════════════════════════════════════════
    st.markdown("<div style='margin-top:4px'></div>", unsafe_allow_html=True)
    st.markdown("##### 🔵 Behavioural Profile — how do at-risk customers differ from safe ones?")
    col4, col5, col6 = st.columns(3)

    with col4:
        st.caption("**Avg Balance — At-Risk vs Safe**")
        df4 = load_balance_profile(seg, branch)
        fig4 = px.bar(df4, x="segment", y="avg_balance", color="Status",
                      barmode="group", text="avg_balance",
                      color_discrete_sequence=STATUS_COLORS, height=H)
        fig4.update_traces(texttemplate="OMR %{text:,.0f}", textposition="outside")
        fig4.update_layout(margin=M, xaxis_title="", yaxis_title="",
                           legend=dict(orientation="h", y=1.12, x=0.1))
        st.plotly_chart(fig4, use_container_width=True)

    with col5:
        st.caption("**Avg Days Since Last Txn — At-Risk vs Safe**")
        df5 = load_activity_profile(seg, branch)
        fig5 = px.bar(df5, x="segment", y="avg_days", color="Status",
                      barmode="group", text="avg_days",
                      color_discrete_sequence=STATUS_COLORS, height=H)
        fig5.update_traces(texttemplate="%{text}d", textposition="outside")
        fig5.update_layout(margin=M, xaxis_title="", yaxis_title="",
                           legend=dict(orientation="h", y=1.12, x=0.1))
        st.plotly_chart(fig5, use_container_width=True)

    with col6:
        st.caption("**Avg Products Held — At-Risk vs Safe**")
        df6 = load_products_profile(seg, branch)
        fig6 = px.bar(df6, x="segment", y="avg_products", color="Status",
                      barmode="group", text="avg_products",
                      color_discrete_sequence=STATUS_COLORS, height=H)
        fig6.update_traces(texttemplate="%{text}", textposition="outside")
        fig6.update_layout(margin=M, xaxis_title="", yaxis_title="",
                           legend=dict(orientation="h", y=1.12, x=0.1))
        st.plotly_chart(fig6, use_container_width=True)
