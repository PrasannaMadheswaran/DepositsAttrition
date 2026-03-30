import sys, os
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
import plotly.express as px
from database import query

PALETTE      = px.colors.qualitative.Bold
RISK_COLORS  = {"High": "#E74C3C", "Medium": "#E67E22", "Low": "#F1C40F", "Safe": "#2ECC71"}
RISK_ORDER   = ["High", "Medium", "Low", "Safe"]

_CSS = """
<style>
    .js-plotly-plot .plotly g.trace.bars g.point,
    .js-plotly-plot .plotly g.trace.bars g.point path,
    .js-plotly-plot .plotly g.trace.bars g.point rect,
    .js-plotly-plot .plotly .bars .point path,
    .js-plotly-plot .plotly .bars .point rect {
        cursor: pointer !important;
    }
    div:has(.kpi-marker) + div[data-testid="stButton"] > button {
        background: transparent !important; border: none !important;
        box-shadow: none !important; color: #1565C0 !important;
        font-size: 13px !important; font-weight: 600 !important;
        text-decoration: underline !important; cursor: pointer !important;
        padding: 0 !important; margin: 0 0 2px 0 !important;
        min-height: unset !important; height: auto !important;
        line-height: 1.5 !important; width: auto !important;
    }
    div:has(.kpi-marker) + div[data-testid="stButton"] > button:hover {
        color: #0D47A1 !important; background: transparent !important;
    }
</style>
"""

# ── Data loaders ────────────────────────────────────────────────────────────

@st.cache_data
def load_summary():
    kpis = query("""
        SELECT
            COUNT(*)                                                   AS total_active,
            SUM(CASE WHEN risk_level IN ('High','Medium') THEN 1 ELSE 0 END)
                                                                       AS at_risk_count,
            ROUND(SUM(CASE WHEN risk_level IN ('High','Medium') THEN balance ELSE 0 END), 0)
                                                                       AS deposits_exposed,
            ROUND(AVG(CASE WHEN risk_level = 'High' THEN balance END), 0)
                                                                       AS avg_high_risk_bal
        FROM customers
        WHERE customer_status IN ('Active','Inactive')
    """)

    by_risk = query("""
        SELECT risk_level, COUNT(*) AS customers
        FROM customers WHERE customer_status IN ('Active','Inactive')
        GROUP BY risk_level
    """)
    # enforce order
    by_risk["risk_level"] = pd.Categorical(
        by_risk["risk_level"], categories=RISK_ORDER, ordered=True)
    by_risk = by_risk.sort_values("risk_level")

    by_segment = query("""
        SELECT segment,
               SUM(CASE WHEN risk_level IN ('High','Medium') THEN 1 ELSE 0 END) AS at_risk,
               COUNT(*) AS total,
               ROUND(SUM(CASE WHEN risk_level IN ('High','Medium') THEN 1 ELSE 0 END)*100.0/COUNT(*),1)
                   AS risk_pct
        FROM customers WHERE customer_status IN ('Active','Inactive')
        GROUP BY segment ORDER BY risk_pct DESC
    """)

    by_account = query("""
        SELECT account_type,
               SUM(CASE WHEN risk_level IN ('High','Medium') THEN 1 ELSE 0 END) AS at_risk,
               COUNT(*) AS total,
               ROUND(SUM(CASE WHEN risk_level IN ('High','Medium') THEN 1 ELSE 0 END)*100.0/COUNT(*),1)
                   AS risk_pct
        FROM customers WHERE customer_status IN ('Active','Inactive')
        GROUP BY account_type ORDER BY risk_pct DESC
    """)

    by_branch = query("""
        SELECT branch,
               SUM(CASE WHEN risk_level IN ('High','Medium') THEN 1 ELSE 0 END) AS at_risk,
               COUNT(*) AS total,
               ROUND(SUM(CASE WHEN risk_level IN ('High','Medium') THEN 1 ELSE 0 END)*100.0/COUNT(*),1)
                   AS risk_pct
        FROM customers WHERE customer_status IN ('Active','Inactive')
        GROUP BY branch ORDER BY at_risk DESC
    """)

    by_signal = query("""
        SELECT
            ROUND(AVG(sig_salary_diverted)*100,1)  AS 'Salary Diverted',
            ROUND(AVG(sig_txn_inactive)*100,1)     AS 'Txn Inactive >90d',
            ROUND(AVG(sig_low_balance)*100,1)      AS 'Low Balance >30d',
            ROUND(AVG(sig_complaints)*100,1)       AS 'Complaints ≥2',
            ROUND(AVG(sig_digital_inactive)*100,1) AS 'Digital Inactive',
            ROUND(AVG(sig_fd_maturing)*100,1)      AS 'FD/RD Maturing',
            ROUND(AVG(sig_low_nps)*100,1)          AS 'NPS ≤30'
        FROM customers WHERE customer_status IN ('Active','Inactive')
    """)

    by_status = query("""
        SELECT customer_status, COUNT(*) AS customers,
               ROUND(SUM(balance)/1e6,2) AS balance_m
        FROM customers WHERE customer_status IN ('Active','Inactive')
        GROUP BY customer_status
    """)

    return kpis, by_risk, by_segment, by_account, by_branch, by_signal, by_status


@st.cache_data
def load_kpi_drill(metric):
    queries = {
        "total_active"    : ("SELECT branch, COUNT(*) AS value FROM customers WHERE customer_status IN ('Active','Inactive') GROUP BY branch ORDER BY value DESC",
                             "Active + Inactive Customers by Branch", "value", "Customers"),
        "at_risk_count"   : ("SELECT branch, SUM(CASE WHEN risk_level IN ('High','Medium') THEN 1 ELSE 0 END) AS value FROM customers WHERE customer_status IN ('Active','Inactive') GROUP BY branch ORDER BY value DESC",
                             "At-Risk Customers by Branch", "value", "Customers"),
        "deposits_exposed": ("SELECT branch, ROUND(SUM(CASE WHEN risk_level IN ('High','Medium') THEN balance ELSE 0 END),0) AS value FROM customers WHERE customer_status IN ('Active','Inactive') GROUP BY branch ORDER BY value DESC",
                             "Deposits Exposed by Branch (OMR)", "value", "OMR"),
        "avg_high_risk_bal": ("SELECT branch, ROUND(AVG(CASE WHEN risk_level='High' THEN balance END),0) AS value FROM customers WHERE customer_status IN ('Active','Inactive') GROUP BY branch ORDER BY value DESC",
                              "Avg Balance of High-Risk Customers by Branch (OMR)", "value", "OMR"),
    }
    sql, title, val_col, label = queries[metric]
    return query(sql), title, val_col, label


@st.cache_data
def load_chart_drill(chart, selected):
    if chart == "segment":
        df = query(f"""
            SELECT branch,
                   SUM(CASE WHEN risk_level IN ('High','Medium') THEN 1 ELSE 0 END) AS at_risk
            FROM customers WHERE customer_status IN ('Active','Inactive') AND segment='{selected}'
            GROUP BY branch ORDER BY at_risk DESC
        """)
        return df, f"At-Risk Customers by Branch — {selected}", "at_risk", "Customers"

    elif chart == "account_type":
        df = query(f"""
            SELECT branch,
                   SUM(CASE WHEN risk_level IN ('High','Medium') THEN 1 ELSE 0 END) AS at_risk
            FROM customers WHERE customer_status IN ('Active','Inactive') AND account_type='{selected}'
            GROUP BY branch ORDER BY at_risk DESC
        """)
        return df, f"At-Risk Customers by Branch — {selected} Accounts", "at_risk", "Customers"

    elif chart == "risk_level":
        df = query(f"""
            SELECT branch, COUNT(*) AS customers
            FROM customers WHERE customer_status IN ('Active','Inactive') AND risk_level='{selected}'
            GROUP BY branch ORDER BY customers DESC
        """)
        return df, f"Customers by Branch — {selected} Risk", "customers", "Customers"

    elif chart == "branch":
        df = query(f"""
            SELECT risk_level, COUNT(*) AS customers
            FROM customers WHERE customer_status IN ('Active','Inactive') AND branch='{selected}'
            GROUP BY risk_level
        """)
        df["risk_level"] = pd.Categorical(df["risk_level"], categories=RISK_ORDER, ordered=True)
        return df.sort_values("risk_level"), f"Risk Level Breakdown — {selected}", "customers", "Customers"


@st.cache_data
def load_customer_drill(chart, val, kpi, branch):
    conditions = []
    if branch:
        conditions.append(f"branch = '{branch}'")
    conditions.append("customer_status IN ('Active','Inactive')")

    if chart == "segment":
        conditions.append(f"segment = '{val}'")
        conditions.append("risk_level IN ('High','Medium')")
    elif chart == "account_type":
        conditions.append(f"account_type = '{val}'")
        conditions.append("risk_level IN ('High','Medium')")
    elif chart == "risk_level":
        conditions.append(f"risk_level = '{val}'")
    elif chart == "branch":
        conditions.append(f"risk_level = '{val}'")
    elif kpi in ("at_risk_count", "deposits_exposed"):
        conditions.append("risk_level IN ('High','Medium')")

    where = "WHERE " + " AND ".join(conditions)
    return query(f"""
        SELECT customer_id      AS "Customer ID",
               customer_status  AS "Status",
               risk_level       AS "Risk Level",
               segment          AS "Segment",
               account_type     AS "Account Type",
               ROUND(balance,0) AS "Balance (OMR)",
               tenure_years     AS "Tenure (Yrs)",
               days_since_txn   AS "Days Since Txn",
               risk_signal_count AS "Signals",
               nps_score        AS "NPS",
               complaint_count  AS "Complaints"
        FROM customers {where}
        ORDER BY
            CASE risk_level WHEN 'High' THEN 1 WHEN 'Medium' THEN 2
                            WHEN 'Low' THEN 3 ELSE 4 END,
            balance DESC
        LIMIT 200
    """)


import pandas as pd

# ── Helpers ─────────────────────────────────────────────────────────────────

def _clear_all():
    for k in ["drill_kpi","drill_chart","drill_val","drill_branch"]:
        st.session_state[k] = None

def _back_btn(label, key, level):
    if st.button(label, key=key):
        if level == 0: _clear_all()
        else: st.session_state.drill_branch = None
        st.rerun()

def _drillable_bar(df, title, val_col, label, chart_key, color_col=None, color_map=None):
    st.markdown(
        f"**🔎 {title}** &nbsp;<small style='color:gray'>· click a bar to see customers</small>",
        unsafe_allow_html=True)
    kwargs = dict(x="branch" if "branch" in df.columns else df.columns[0],
                  y=val_col, text=val_col, height=270)
    if color_col and color_map:
        kwargs["color"] = color_col
        kwargs["color_discrete_map"] = color_map
    else:
        kwargs["color"] = kwargs["x"]
        kwargs["color_discrete_sequence"] = PALETTE
    fig = px.bar(df, **kwargs)
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False, margin=dict(t=5,b=5,l=10,r=10),
                      xaxis_title="", yaxis_title=label,
                      dragmode=False, clickmode="event+select")
    return st.plotly_chart(fig, use_container_width=True, on_select="rerun",
                           key=chart_key, selection_mode="points")


# ── Main ─────────────────────────────────────────────────────────────────────

def show():
    for key in ["drill_kpi","drill_chart","drill_val","drill_branch"]:
        if key not in st.session_state:
            st.session_state[key] = None

    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

    kpis, by_risk, by_segment, by_account, by_branch, by_signal, by_status = load_summary()
    k = kpis.iloc[0]
    H = 210
    M = dict(t=5, b=5, l=30, r=10)

    # ── KPI Cards ────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown('<span class="kpi-marker"></span>', unsafe_allow_html=True)
        if st.button("👥 Active Customers", key="b1", help="Click to drill down by branch"):
            _clear_all(); st.session_state.drill_kpi = "total_active"
        st.metric("Active Customers", f"{int(k['total_active']):,}",
                  help="Active + Inactive customers currently in the bank.",
                  label_visibility="collapsed")
    with c2:
        st.markdown('<span class="kpi-marker"></span>', unsafe_allow_html=True)
        if st.button("🔴 At-Risk Customers", key="b2", help="Click to drill down by branch"):
            _clear_all(); st.session_state.drill_kpi = "at_risk_count"
        st.metric("At-Risk Customers", f"{int(k['at_risk_count']):,}",
                  delta=f"{k['at_risk_count']/k['total_active']*100:.1f}% of portfolio",
                  delta_color="inverse",
                  help="Customers with High or Medium risk signals.",
                  label_visibility="collapsed")
    with c3:
        st.markdown('<span class="kpi-marker"></span>', unsafe_allow_html=True)
        if st.button("💰 Deposits Exposed", key="b3", help="Click to drill down by branch"):
            _clear_all(); st.session_state.drill_kpi = "deposits_exposed"
        st.metric("Deposits Exposed", f"OMR {int(k['deposits_exposed']):,}",
                  help="Total balance held by High + Medium risk customers.",
                  label_visibility="collapsed")
    with c4:
        st.markdown('<span class="kpi-marker"></span>', unsafe_allow_html=True)
        if st.button("📉 Avg Bal (High Risk)", key="b4", help="Click to drill down by branch"):
            _clear_all(); st.session_state.drill_kpi = "avg_high_risk_bal"
        val4 = int(k['avg_high_risk_bal']) if k['avg_high_risk_bal'] else 0
        st.metric("Avg Bal (High Risk)", f"OMR {val4:,}",
                  help="Average balance of High-risk customers — prioritise by this.",
                  label_visibility="collapsed")

    st.markdown("<div style='margin-top:4px'></div>", unsafe_allow_html=True)

    # ── Level 2: Customer table ───────────────────────────────────────────────
    if st.session_state.drill_branch:
        branch = st.session_state.drill_branch
        ctx    = st.session_state.drill_val or ""
        col_hd, col_bk = st.columns([7, 1])
        with col_hd:
            st.markdown(f"**👥 Customers — {branch}" + (f" · {ctx}" if ctx else "") + "**")
        with col_bk:
            _back_btn("⬆️ Branches", key="back_to_L1", level=1)
        df_c = load_customer_drill(
            st.session_state.drill_chart, st.session_state.drill_val,
            st.session_state.drill_kpi, branch)
        st.dataframe(df_c, use_container_width=True,
                     height=min(36*len(df_c)+38, 380), hide_index=True)
        st.caption(f"{len(df_c)} customers shown (max 200) · sorted by risk level then balance")
        return

    # ── Level 1: Branch breakdown ─────────────────────────────────────────────
    if st.session_state.drill_kpi:
        col_hd, col_bk = st.columns([7, 1])
        with col_bk:
            _back_btn("⬆️ Dashboard", key="back_to_L0_kpi", level=0)
        df_d, title, val_col, lbl = load_kpi_drill(st.session_state.drill_kpi)
        ev = _drillable_bar(df_d, title, val_col, lbl, chart_key="kpi_drill")
        if ev and ev.selection and ev.selection.points:
            st.session_state.drill_branch = ev.selection.points[0]["x"]
            st.rerun()
        return

    if st.session_state.drill_chart:
        col_hd, col_bk = st.columns([7, 1])
        with col_bk:
            _back_btn("⬆️ Dashboard", key="back_to_L0_chart", level=0)
        df_d, title, val_col, lbl = load_chart_drill(
            st.session_state.drill_chart, st.session_state.drill_val)
        x_col = "branch" if "branch" in df_d.columns else df_d.columns[0]
        ev = _drillable_bar(df_d, title, val_col, lbl, chart_key="chart_drill",
                            color_col="risk_level" if x_col=="risk_level" else None,
                            color_map=RISK_COLORS if x_col=="risk_level" else None)
        if ev and ev.selection and ev.selection.points:
            st.session_state.drill_branch = ev.selection.points[0]["x"]
            st.rerun()
        return

    # ── Level 0: Main dashboard ───────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    # Chart 1 — Risk Level Distribution
    with col1:
        st.caption("**Risk Level Distribution** · 💡 click a bar to drill down")
        fig1 = px.bar(by_risk, x="risk_level", y="customers",
                      color="risk_level", text="customers",
                      color_discrete_map=RISK_COLORS, height=H)
        fig1.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig1.update_layout(showlegend=False, margin=M, xaxis_title="", yaxis_title="",
                           dragmode=False, clickmode="event+select")
        ev1 = st.plotly_chart(fig1, use_container_width=True, on_select="rerun",
                              key="risk_chart", selection_mode="points")
        if ev1 and ev1.selection and ev1.selection.points:
            _clear_all()
            st.session_state.drill_chart = "risk_level"
            st.session_state.drill_val   = ev1.selection.points[0]["x"]

    # Chart 2 — At-Risk % by Segment
    with col2:
        st.caption("**At-Risk Rate by Segment** · 💡 click a bar to drill down")
        fig2 = px.bar(by_segment, x="segment", y="risk_pct",
                      color="segment", text="risk_pct",
                      color_discrete_sequence=PALETTE, height=H)
        fig2.update_traces(texttemplate="%{text}%", textposition="outside")
        fig2.update_layout(showlegend=False, yaxis_range=[0,100], margin=M,
                           xaxis_title="", yaxis_title="",
                           dragmode=False, clickmode="event+select")
        ev2 = st.plotly_chart(fig2, use_container_width=True, on_select="rerun",
                              key="seg_chart", selection_mode="points")
        if ev2 and ev2.selection and ev2.selection.points:
            _clear_all()
            st.session_state.drill_chart = "segment"
            st.session_state.drill_val   = ev2.selection.points[0]["x"]

    # Chart 3 — At-Risk % by Account Type
    with col3:
        st.caption("**At-Risk Rate by Account Type** · 💡 click a bar to drill down")
        fig3 = px.bar(by_account, x="account_type", y="risk_pct",
                      color="account_type", text="risk_pct",
                      color_discrete_sequence=px.colors.qualitative.Pastel, height=H)
        fig3.update_traces(texttemplate="%{text}%", textposition="outside")
        fig3.update_layout(showlegend=False, yaxis_range=[0,100], margin=M,
                           xaxis_title="", yaxis_title="",
                           dragmode=False, clickmode="event+select")
        ev3 = st.plotly_chart(fig3, use_container_width=True, on_select="rerun",
                              key="acc_chart", selection_mode="points")
        if ev3 and ev3.selection and ev3.selection.points:
            _clear_all()
            st.session_state.drill_chart = "account_type"
            st.session_state.drill_val   = ev3.selection.points[0]["x"]

    st.markdown("<div style='margin-top:6px'></div>", unsafe_allow_html=True)
    col4, col5, col6 = st.columns(3)

    # Chart 4 — At-Risk Count by Branch
    with col4:
        st.caption("**At-Risk Customers by Branch** · 💡 click a bar to drill down")
        fig4 = px.bar(by_branch.sort_values("at_risk", ascending=True),
                      x="at_risk", y="branch", orientation="h",
                      color="at_risk", text="at_risk",
                      color_continuous_scale="Reds", height=H)
        fig4.update_traces(textposition="outside")
        fig4.update_layout(coloraxis_showscale=False, margin=M,
                           xaxis_title="", yaxis_title="",
                           dragmode=False, clickmode="event+select")
        ev4 = st.plotly_chart(fig4, use_container_width=True, on_select="rerun",
                              key="branch_chart", selection_mode="points")
        if ev4 and ev4.selection and ev4.selection.points:
            _clear_all()
            st.session_state.drill_chart = "branch"
            st.session_state.drill_val   = ev4.selection.points[0]["y"]

    # Chart 5 — Signal Frequency
    with col5:
        st.caption("**Risk Signal Frequency** · % of active customers with each signal")
        sig_row = by_signal.iloc[0]
        sig_df  = pd.DataFrame([
            {"Signal": k, "% Customers": v}
            for k, v in sig_row.items()
        ]).sort_values("% Customers", ascending=True)
        fig5 = px.bar(sig_df, x="% Customers", y="Signal", orientation="h",
                      color="% Customers", text="% Customers",
                      color_continuous_scale="Oranges", height=H)
        fig5.update_traces(texttemplate="%{text}%", textposition="outside")
        fig5.update_layout(coloraxis_showscale=False, margin=M,
                           xaxis_title="", yaxis_title="",
                           dragmode=False)
        st.plotly_chart(fig5, use_container_width=True)

    # Chart 6 — Active vs Inactive balance
    with col6:
        st.caption("**Portfolio Split — Active vs Inactive**")
        fig6 = px.bar(by_status, x="customer_status", y=["customers", "balance_m"],
                      barmode="group",
                      color_discrete_sequence=["#3498DB", "#E74C3C"], height=H)
        fig6.update_layout(margin=M, xaxis_title="", yaxis_title="",
                           legend=dict(orientation="h", y=1.1, x=0),
                           dragmode=False)
        st.plotly_chart(fig6, use_container_width=True)
