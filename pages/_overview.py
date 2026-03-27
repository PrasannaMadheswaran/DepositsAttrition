import sys, os
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
import plotly.express as px
from database import query

PALETTE = px.colors.qualitative.Bold

_CSS = """
<style>
    /* pointer cursor on drillable bar chart elements */
    .js-plotly-plot .plotly g.trace.bars g.point,
    .js-plotly-plot .plotly g.trace.bars g.point path,
    .js-plotly-plot .plotly g.trace.bars g.point rect,
    .js-plotly-plot .plotly .bars .point path,
    .js-plotly-plot .plotly .bars .point rect {
        cursor: pointer !important;
    }
    /* KPI title hyperlink buttons ─────────────────────────────────
       targets only the button immediately following a .kpi-marker span */
    div:has(.kpi-marker) + div[data-testid="stButton"] > button {
        background:      transparent !important;
        border:          none        !important;
        box-shadow:      none        !important;
        color:           #1565C0    !important;
        font-size:       13px       !important;
        font-weight:     600        !important;
        text-decoration: underline  !important;
        cursor:          pointer    !important;
        padding:         0          !important;
        margin:          0 0 2px 0  !important;
        min-height:      unset      !important;
        height:          auto       !important;
        line-height:     1.5        !important;
        width:           auto       !important;
    }
    div:has(.kpi-marker) + div[data-testid="stButton"] > button:hover {
        color: #0D47A1 !important;
        background: transparent !important;
    }
</style>
"""

# ── Data loaders ───────────────────────────────────────────────────────────────

@st.cache_data
def load_summary():
    kpis = query("""
        SELECT COUNT(*)                                             AS total_customers,
               ROUND(AVG(attrition_flag) * 100, 2)                AS attrition_rate,
               ROUND(SUM(CASE WHEN attrition_flag=1 THEN balance ELSE 0 END), 0)
                                                                   AS deposits_at_risk,
               ROUND(AVG(CASE WHEN attrition_flag=1 THEN balance END), 0)
                                                                   AS avg_churned_balance,
               SUM(attrition_flag)                                 AS total_churned
        FROM customers
    """)
    by_segment = query("""
        SELECT segment, COUNT(*) AS customers, SUM(attrition_flag) AS churned,
               ROUND(AVG(attrition_flag)*100,1) AS attrition_rate
        FROM customers GROUP BY segment ORDER BY attrition_rate DESC
    """)
    by_account = query("""
        SELECT account_type, COUNT(*) AS customers, SUM(attrition_flag) AS churned,
               ROUND(AVG(attrition_flag)*100,1) AS attrition_rate
        FROM customers GROUP BY account_type ORDER BY attrition_rate DESC
    """)
    by_tenure = query("""
        SELECT CASE WHEN tenure_years<=2  THEN '0-2 yrs'
                    WHEN tenure_years<=5  THEN '3-5 yrs'
                    WHEN tenure_years<=10 THEN '6-10 yrs'
                    ELSE '10+ yrs' END AS tenure_bucket,
               ROUND(AVG(attrition_flag)*100,1) AS attrition_rate,
               COUNT(*) AS customers
        FROM customers GROUP BY tenure_bucket ORDER BY MIN(tenure_years)
    """)
    by_type = query("""
        SELECT attrition_type, COUNT(*) AS count
        FROM customers WHERE attrition_flag=1 GROUP BY attrition_type
    """)
    by_seg_risk = query("""
        SELECT segment,
               ROUND(SUM(balance)/1e6, 3) AS deposits_at_risk_m
        FROM customers WHERE attrition_flag = 1
        GROUP BY segment ORDER BY deposits_at_risk_m DESC
    """)
    by_acc_risk = query("""
        SELECT account_type,
               ROUND(SUM(balance)/1e6, 3) AS deposits_at_risk_m
        FROM customers WHERE attrition_flag = 1
        GROUP BY account_type ORDER BY deposits_at_risk_m DESC
    """)
    return kpis, by_segment, by_account, by_tenure, by_type, by_seg_risk, by_acc_risk


@st.cache_data
def load_kpi_drill(metric: str):
    queries = {
        "total_customers" : ("SELECT branch, COUNT(*) AS value FROM customers GROUP BY branch ORDER BY value DESC",
                             "Total Customers by Branch", "value", "Customers"),
        "attrition_rate"  : ("SELECT branch, ROUND(AVG(attrition_flag)*100,1) AS value FROM customers GROUP BY branch ORDER BY value DESC",
                             "Attrition Rate by Branch (%)", "value", "Rate %"),
        "deposits_at_risk": ("SELECT branch, ROUND(SUM(CASE WHEN attrition_flag=1 THEN balance ELSE 0 END),0) AS value FROM customers GROUP BY branch ORDER BY value DESC",
                             "Deposits at Risk by Branch (OMR)", "value", "OMR"),
        "avg_churned_balance": ("SELECT branch, ROUND(AVG(CASE WHEN attrition_flag=1 THEN balance END),0) AS value FROM customers GROUP BY branch ORDER BY value DESC",
                               "Avg Balance of Churned Customers by Branch (OMR)", "value", "OMR"),
    }
    sql, title, val_col, label = queries[metric]
    return query(sql), title, val_col, label


@st.cache_data
def load_chart_drill(chart: str, selected: str):
    if chart == "segment":
        df = query(f"""
            SELECT branch, ROUND(AVG(attrition_flag)*100,1) AS attrition_rate
            FROM customers WHERE segment='{selected}'
            GROUP BY branch ORDER BY attrition_rate DESC
        """)
        return df, f"Attrition Rate by Branch — {selected} Segment", "attrition_rate", "Rate %"

    elif chart == "account_type":
        df = query(f"""
            SELECT branch, ROUND(AVG(attrition_flag)*100,1) AS attrition_rate
            FROM customers WHERE account_type='{selected}'
            GROUP BY branch ORDER BY attrition_rate DESC
        """)
        return df, f"Attrition Rate by Branch — {selected} Accounts", "attrition_rate", "Rate %"

    elif chart == "exit_type":
        df = query(f"""
            SELECT branch, COUNT(*) AS count
            FROM customers WHERE attrition_type='{selected}'
            GROUP BY branch ORDER BY count DESC
        """)
        return df, f"Branch Breakdown — {selected}", "count", "Customers"

    elif chart == "tenure":
        tenure_map = {
            "0-2 yrs" : "tenure_years <= 2",
            "3-5 yrs" : "tenure_years BETWEEN 3 AND 5",
            "6-10 yrs": "tenure_years BETWEEN 6 AND 10",
            "10+ yrs" : "tenure_years > 10",
        }
        cond = tenure_map.get(selected, "tenure_years > 0")
        df = query(f"""
            SELECT branch, ROUND(AVG(attrition_flag)*100,1) AS attrition_rate
            FROM customers WHERE {cond}
            GROUP BY branch ORDER BY attrition_rate DESC
        """)
        return df, f"Attrition Rate by Branch — Tenure {selected}", "attrition_rate", "Rate %"

    elif chart == "customers_segment":
        df = query(f"""
            SELECT branch, COUNT(*) AS customers
            FROM customers WHERE segment='{selected}'
            GROUP BY branch ORDER BY customers DESC
        """)
        return df, f"Customers by Branch — {selected} Segment", "customers", "Customers"

    elif chart == "deposits_seg_risk":
        df = query(f"""
            SELECT branch, ROUND(SUM(balance)/1e6, 3) AS deposits_at_risk_m
            FROM customers WHERE attrition_flag=1 AND segment='{selected}'
            GROUP BY branch ORDER BY deposits_at_risk_m DESC
        """)
        return df, f"Deposits at Risk by Branch — {selected} Segment (OMR M)", "deposits_at_risk_m", "OMR M"

    elif chart == "deposits_acc_risk":
        df = query(f"""
            SELECT branch, ROUND(SUM(balance)/1e6, 3) AS deposits_at_risk_m
            FROM customers WHERE attrition_flag=1 AND account_type='{selected}'
            GROUP BY branch ORDER BY deposits_at_risk_m DESC
        """)
        return df, f"Deposits at Risk by Branch — {selected} Accounts (OMR M)", "deposits_at_risk_m", "OMR M"


@st.cache_data
def load_customer_drill(chart, val, kpi, branch):
    """Return up to 200 customers filtered by branch + the active drill context."""
    conditions = [f"branch = '{branch}'"]

    if chart in ("segment", "customers_segment", "deposits_seg_risk"):
        conditions.append(f"segment = '{val}'")
        if chart == "deposits_seg_risk":
            conditions.append("attrition_flag = 1")
    elif chart in ("account_type", "deposits_acc_risk"):
        conditions.append(f"account_type = '{val}'")
        if chart == "deposits_acc_risk":
            conditions.append("attrition_flag = 1")
    elif chart == "exit_type":
        conditions.append(f"attrition_type = '{val}'")
    elif chart == "tenure":
        tenure_map = {
            "0-2 yrs" : "tenure_years <= 2",
            "3-5 yrs" : "tenure_years BETWEEN 3 AND 5",
            "6-10 yrs": "tenure_years BETWEEN 6 AND 10",
            "10+ yrs" : "tenure_years > 10",
        }
        if val in tenure_map:
            conditions.append(tenure_map[val])

    # KPI-specific filters
    if kpi in ("attrition_rate", "deposits_at_risk"):
        conditions.append("attrition_flag = 1")

    where = " AND ".join(conditions)
    df = query(f"""
        SELECT customer_id   AS "Customer ID",
               age           AS "Age",
               gender        AS "Gender",
               segment       AS "Segment",
               account_type  AS "Account Type",
               ROUND(balance, 0) AS "Balance (OMR)",
               tenure_years  AS "Tenure (Yrs)",
               attrition_type AS "Exit Type",
               days_since_txn AS "Days Since Txn"
        FROM customers
        WHERE {where}
        ORDER BY balance DESC
        LIMIT 200
    """)
    return df


# ── Helpers ────────────────────────────────────────────────────────────────────

def _clear_all():
    for k in ["drill_kpi","drill_chart","drill_val","drill_branch"]:
        st.session_state[k] = None

def _back_btn(label, key, level):
    if st.button(label, key=key):
        if level == 0:
            _clear_all()
        else:
            st.session_state.drill_branch = None
        st.rerun()

def _drillable_bar(df, title, val_col, label, chart_key):
    """Branch breakdown bar — single click selects a branch → Level 2."""
    st.markdown(
        f"**🔎 {title}** &nbsp;"
        f"<small style='color:gray'>· click a branch bar to see customers</small>",
        unsafe_allow_html=True)
    fig = px.bar(df, x="branch", y=val_col, color="branch", text=val_col,
                 color_discrete_sequence=PALETTE, height=270)
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False, margin=dict(t=5,b=5,l=10,r=10),
                      xaxis_title="", yaxis_title=label,
                      dragmode=False, clickmode="event+select")
    ev = st.plotly_chart(fig, use_container_width=True, on_select="rerun",
                         key=chart_key, selection_mode="points")
    return ev


# ── Main ───────────────────────────────────────────────────────────────────────

def show():
    for key in ["drill_kpi","drill_chart","drill_val","drill_branch"]:
        if key not in st.session_state:
            st.session_state[key] = None

    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

    kpis, by_segment, by_account, by_tenure, by_type, by_seg_risk, by_acc_risk = load_summary()
    k  = kpis.iloc[0]
    H  = 210
    M  = dict(t=5, b=5, l=30, r=10)

    # ── KPI Cards (always visible) ─────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown('<span class="kpi-marker"></span>', unsafe_allow_html=True)
        if st.button("👥 Total Customers", key="b1",
                     help="Click to drill down by branch"):
            _clear_all()
            st.session_state.drill_kpi = "total_customers"
        st.metric("Total Customers", f"{int(k['total_customers']):,}",
                  help="Total customers — active + churned.",
                  label_visibility="collapsed")
    with c2:
        st.markdown('<span class="kpi-marker"></span>', unsafe_allow_html=True)
        if st.button("⚠️ Attrition Rate", key="b2",
                     help="Click to drill down by branch"):
            _clear_all()
            st.session_state.drill_kpi = "attrition_rate"
        st.metric("Attrition Rate", f"{k['attrition_rate']}%",
                  delta=f"{int(k['total_churned']):,} churned", delta_color="inverse",
                  help=f"= ({int(k['total_churned']):,} ÷ {int(k['total_customers']):,}) × 100",
                  label_visibility="collapsed")
    with c3:
        st.markdown('<span class="kpi-marker"></span>', unsafe_allow_html=True)
        if st.button("💰 Deposits at Risk", key="b3",
                     help="Click to drill down by branch"):
            _clear_all()
            st.session_state.drill_kpi = "deposits_at_risk"
        st.metric("Deposits at Risk", f"OMR {int(k['deposits_at_risk']):,}",
                  delta="Churned customer balances", delta_color="inverse",
                  help="SUM(balance) WHERE attrition_flag = 1",
                  label_visibility="collapsed")
    with c4:
        st.markdown('<span class="kpi-marker"></span>', unsafe_allow_html=True)
        if st.button("📉 Avg Balance (Churned)", key="b4",
                     help="Click to drill down by branch"):
            _clear_all()
            st.session_state.drill_kpi = "avg_churned_balance"
        st.metric("Avg Balance (Churned)", f"OMR {int(k['avg_churned_balance']):,}",
                  help="AVG(balance) of churned customers only — shows the typical deposit size being lost.",
                  label_visibility="collapsed")

    st.markdown("<div style='margin-top:4px'></div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # LEVEL 2 — Customer table (branch was clicked in the branch chart)
    # ══════════════════════════════════════════════════════════════════════════
    if st.session_state.drill_branch:
        branch = st.session_state.drill_branch
        ctx    = st.session_state.drill_val or ""
        label  = f"{branch}" + (f" · {ctx}" if ctx else "")

        col_hd, col_bk = st.columns([7, 1])
        with col_hd:
            st.markdown(f"**👥 Customers — {label}**", unsafe_allow_html=True)
        with col_bk:
            _back_btn("⬆️ Branches", key="back_to_L1", level=1)

        df_cust = load_customer_drill(
            st.session_state.drill_chart,
            st.session_state.drill_val,
            st.session_state.drill_kpi,
            branch)

        st.dataframe(
            df_cust,
            use_container_width=True,
            height=min(36 * len(df_cust) + 38, 380),
            hide_index=True)

        st.caption(f"{len(df_cust)} customers shown (max 200)")
        return  # stop — don't render charts below

    # ══════════════════════════════════════════════════════════════════════════
    # LEVEL 1 — Branch breakdown (KPI button or chart bar was clicked)
    # ══════════════════════════════════════════════════════════════════════════
    if st.session_state.drill_kpi:
        col_hd, col_bk = st.columns([7, 1])
        with col_bk:
            _back_btn("⬆️ Dashboard", key="back_to_L0_kpi", level=0)
        df_d, title, val_col, lbl = load_kpi_drill(st.session_state.drill_kpi)
        ev_d = _drillable_bar(df_d, title, val_col, lbl, chart_key="kpi_drill")
        if ev_d and ev_d.selection and ev_d.selection.points:
            st.session_state.drill_branch = ev_d.selection.points[0]["x"]
            st.rerun()
        return

    if st.session_state.drill_chart:
        col_hd, col_bk = st.columns([7, 1])
        with col_bk:
            _back_btn("⬆️ Dashboard", key="back_to_L0_chart", level=0)
        df_d, title, val_col, lbl = load_chart_drill(
            st.session_state.drill_chart, st.session_state.drill_val)
        ev_d = _drillable_bar(df_d, title, val_col, lbl, chart_key="chart_drill")
        if ev_d and ev_d.selection and ev_d.selection.points:
            st.session_state.drill_branch = ev_d.selection.points[0]["x"]
            st.rerun()
        return

    # ══════════════════════════════════════════════════════════════════════════
    # LEVEL 0 — Main dashboard (6 charts)
    # ══════════════════════════════════════════════════════════════════════════
    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption("**Attrition by Segment** · 💡 click a bar to drill down")
        fig = px.bar(by_segment, x="segment", y="attrition_rate", color="segment",
                     text="attrition_rate",
                     color_discrete_sequence=PALETTE, height=H)
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(showlegend=False, yaxis_range=[0,100], margin=M,
                          xaxis_title="", yaxis_title="",
                          dragmode=False, clickmode="event+select")
        ev1 = st.plotly_chart(fig, use_container_width=True, on_select="rerun",
                              key="seg_chart", selection_mode="points")
        if ev1 and ev1.selection and ev1.selection.points:
            _clear_all()
            st.session_state.drill_chart = "segment"
            st.session_state.drill_val   = ev1.selection.points[0]["x"]

    with col2:
        st.caption("**Attrition by Account Type** · 💡 click a bar to drill down")
        fig2 = px.bar(by_account, x="account_type", y="attrition_rate",
                      color="account_type", text="attrition_rate",
                      color_discrete_sequence=px.colors.qualitative.Pastel, height=H)
        fig2.update_traces(texttemplate="%{text}%", textposition="outside")
        fig2.update_layout(showlegend=False, yaxis_range=[0,100], margin=M,
                           xaxis_title="", yaxis_title="",
                           dragmode=False, clickmode="event+select")
        ev2 = st.plotly_chart(fig2, use_container_width=True, on_select="rerun",
                              key="acc_chart", selection_mode="points")
        if ev2 and ev2.selection and ev2.selection.points:
            _clear_all()
            st.session_state.drill_chart = "account_type"
            st.session_state.drill_val   = ev2.selection.points[0]["x"]

    with col3:
        st.caption("**Attrition by Tenure** · 💡 click a bar to drill down")
        fig3 = px.bar(by_tenure, x="tenure_bucket", y="attrition_rate",
                      color="attrition_rate", text="attrition_rate",
                      color_continuous_scale="Reds", height=H)
        fig3.update_traces(texttemplate="%{text}%", textposition="outside")
        fig3.update_layout(coloraxis_showscale=False, yaxis_range=[0,100],
                           margin=M, xaxis_title="", yaxis_title="",
                           dragmode=False, clickmode="event+select")
        ev3 = st.plotly_chart(fig3, use_container_width=True, on_select="rerun",
                              key="ten_chart", selection_mode="points")
        if ev3 and ev3.selection and ev3.selection.points:
            _clear_all()
            st.session_state.drill_chart = "tenure"
            st.session_state.drill_val   = ev3.selection.points[0]["x"]

    st.markdown("<div style='margin-top:6px'></div>", unsafe_allow_html=True)
    col4, col5, col6 = st.columns(3)

    with col4:
        st.caption("**Exit Type Breakdown** · 💡 click a bar to drill down")
        by_type_sorted = by_type.sort_values("count", ascending=True)
        fig4 = px.bar(by_type_sorted, x="count", y="attrition_type",
                      orientation="h", color="attrition_type", text="count",
                      color_discrete_sequence=px.colors.qualitative.Set2, height=H)
        fig4.update_traces(textposition="outside")
        fig4.update_layout(showlegend=False, margin=M,
                           xaxis_title="", yaxis_title="",
                           dragmode=False, clickmode="event+select")
        ev4 = st.plotly_chart(fig4, use_container_width=True, on_select="rerun",
                              key="exit_chart", selection_mode="points")
        if ev4 and ev4.selection and ev4.selection.points:
            _clear_all()
            st.session_state.drill_chart = "exit_type"
            st.session_state.drill_val   = ev4.selection.points[0]["y"]

    with col5:
        st.caption("**Deposits at Risk by Segment (OMR M)** · churned customers only · 💡 click to drill down")
        fig5 = px.bar(by_seg_risk, x="segment", y="deposits_at_risk_m",
                      color="segment", text="deposits_at_risk_m",
                      color_discrete_sequence=px.colors.qualitative.Set2, height=H)
        fig5.update_traces(texttemplate="OMR %{text}M", textposition="outside")
        fig5.update_layout(showlegend=False, margin=M, xaxis_title="", yaxis_title="OMR M",
                           dragmode=False, clickmode="event+select")
        ev5 = st.plotly_chart(fig5, use_container_width=True, on_select="rerun",
                              key="dep_seg_risk_chart", selection_mode="points")
        if ev5 and ev5.selection and ev5.selection.points:
            _clear_all()
            st.session_state.drill_chart = "deposits_seg_risk"
            st.session_state.drill_val   = ev5.selection.points[0]["x"]

    with col6:
        st.caption("**Deposits at Risk by Account Type (OMR M)** · churned customers only · 💡 click to drill down")
        fig6 = px.bar(by_acc_risk, x="account_type", y="deposits_at_risk_m",
                      color="account_type", text="deposits_at_risk_m",
                      color_discrete_sequence=px.colors.qualitative.Pastel, height=H)
        fig6.update_traces(texttemplate="OMR %{text}M", textposition="outside")
        fig6.update_layout(showlegend=False, margin=M, xaxis_title="", yaxis_title="OMR M",
                           dragmode=False, clickmode="event+select")
        ev6 = st.plotly_chart(fig6, use_container_width=True, on_select="rerun",
                              key="dep_acc_risk_chart", selection_mode="points")
        if ev6 and ev6.selection and ev6.selection.points:
            _clear_all()
            st.session_state.drill_chart = "deposits_acc_risk"
            st.session_state.drill_val   = ev6.selection.points[0]["x"]
