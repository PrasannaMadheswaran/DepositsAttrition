import sys, os
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
import plotly.express as px
import pandas as pd
from database import query

PALETTE     = px.colors.qualitative.Bold
EXIT_COLORS = {
    "Account Closure"       : "#E74C3C",
    "Extended Inactivity"   : "#E67E22",
    "Salary Diversion"      : "#8E44AD",
    "Balance Dormancy"      : "#2980B9",
    "Transaction Inactivity": "#27AE60",
}

_CSS = """
<style>
    .js-plotly-plot .plotly g.trace.bars g.point,
    .js-plotly-plot .plotly g.trace.bars g.point path,
    .js-plotly-plot .plotly g.trace.bars g.point rect {
        cursor: pointer !important;
    }
</style>
"""


# ── Data loaders ─────────────────────────────────────────────────────────────

@st.cache_data
def load_weekly_trend(weeks):
    return query(f"""
        SELECT exit_week, COUNT(*) AS churned
        FROM customers
        WHERE customer_status = 'Churned'
          AND exit_week >= (53 - {weeks})
        GROUP BY exit_week ORDER BY exit_week
    """)


@st.cache_data
def load_exit_type_trend(weeks):
    return query(f"""
        SELECT exit_week, exit_type, COUNT(*) AS churned
        FROM customers
        WHERE customer_status = 'Churned'
          AND exit_week >= (53 - {weeks})
        GROUP BY exit_week, exit_type ORDER BY exit_week
    """)


@st.cache_data
def load_segment_trend(weeks):
    return query(f"""
        SELECT exit_week, segment, COUNT(*) AS churned
        FROM customers
        WHERE customer_status = 'Churned'
          AND exit_week >= (53 - {weeks})
        GROUP BY exit_week, segment ORDER BY exit_week
    """)


@st.cache_data
def load_branch_churn(weeks):
    return query(f"""
        SELECT branch, COUNT(*) AS churned
        FROM customers
        WHERE customer_status = 'Churned'
          AND exit_week >= (53 - {weeks})
        GROUP BY branch ORDER BY churned DESC
    """)


@st.cache_data
def load_exit_type_summary(weeks):
    return query(f"""
        SELECT exit_type, COUNT(*) AS churned
        FROM customers
        WHERE customer_status = 'Churned'
          AND exit_week >= (53 - {weeks})
        GROUP BY exit_type ORDER BY churned DESC
    """)


@st.cache_data
def load_summary_kpis(weeks):
    return query(f"""
        SELECT COUNT(*) AS total_churned,
               ROUND(AVG(has_loan) * 100, 1)    AS pct_with_loans,
               ROUND(AVG(risk_signal_count), 1) AS avg_signal_count,
               ROUND(COUNT(*)*1.0 / {weeks}, 1) AS avg_per_week
        FROM customers
        WHERE customer_status = 'Churned'
          AND exit_week >= (53 - {weeks})
    """)


@st.cache_data
def load_drill_customers(dim, val, weeks):
    conditions = [
        "customer_status = 'Churned'",
        f"exit_week >= (53 - {weeks})"
    ]
    if dim == "exit_type":
        conditions.append(f"exit_type = '{val}'")
    elif dim == "branch":
        conditions.append(f"branch = '{val}'")
    elif dim == "week":
        conditions.append(f"exit_week = {val}")
    elif dim == "segment":
        conditions.append(f"segment = '{val}'")

    where = "WHERE " + " AND ".join(conditions)
    return query(f"""
        SELECT customer_id      AS "Customer ID",
               segment          AS "Segment",
               account_type     AS "Account Type",
               branch           AS "Branch",
               exit_type        AS "Exit Type",
               exit_week        AS "Exit Week",
               tenure_years     AS "Tenure (Yrs)",
               risk_signal_count AS "Signals",
               has_loan         AS "Had Loan",
               nps_score        AS "NPS"
        FROM customers {where}
        ORDER BY tenure_years DESC
        LIMIT 200
    """)


# ── Main ─────────────────────────────────────────────────────────────────────

def show():
    for k in ["trend_dim", "trend_val"]:
        if k not in st.session_state:
            st.session_state[k] = None

    st.markdown(_CSS, unsafe_allow_html=True)

    H = 240
    M = dict(t=10, b=5, l=30, r=10)

    # ── Filter bar ────────────────────────────────────────────────────────
    fc1, fc2, fc3 = st.columns([3, 5, 1])
    with fc1:
        weeks = st.select_slider(
            "Analysis window",
            options=[4, 8, 13, 26, 52],
            value=13,
            format_func=lambda x: f"Last {x} weeks",
            key="trend_weeks")
    with fc2:
        st.markdown(
            "<div style='margin-top:28px;color:#666;font-size:13px;'>"
            "Confirmed exits — accounts closed or inactive for 365+ days."
            "</div>", unsafe_allow_html=True)
    with fc3:
        st.markdown("<div style='margin-top:26px'></div>", unsafe_allow_html=True)
        if st.session_state.trend_dim and st.button("✖ Clear", key="trend_clear"):
            st.session_state.trend_dim = None
            st.session_state.trend_val = None
            st.rerun()

    st.divider()

    # ── Drill-down: customer table ────────────────────────────────────────
    if st.session_state.trend_dim:
        col_h, col_b = st.columns([7, 1])
        with col_h:
            st.markdown(f"**👥 Churned Customers — {st.session_state.trend_val}**")
        with col_b:
            if st.button("⬆️ Back", key="trend_back"):
                st.session_state.trend_dim = None
                st.session_state.trend_val = None
                st.rerun()
        df_c = load_drill_customers(
            st.session_state.trend_dim, st.session_state.trend_val, weeks)
        st.dataframe(df_c, use_container_width=True,
                     height=min(36*len(df_c)+38, 420), hide_index=True)
        st.caption(f"{len(df_c)} customers shown (max 200)")
        return

    # ── KPIs ──────────────────────────────────────────────────────────────
    kpis    = load_summary_kpis(weeks).iloc[0]
    weekly  = load_weekly_trend(weeks)
    by_type = load_exit_type_trend(weeks)
    by_seg  = load_segment_trend(weeks)
    branch  = load_branch_churn(weeks)
    summary = load_exit_type_summary(weeks)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🚪 Total Churned",    f"{int(kpis['total_churned']):,}",
              help=f"Churned in the last {weeks} weeks")
    k2.metric("🏦 % With Loans",     f"{kpis['pct_with_loans']}%",
              help="Share of churned customers who had an active loan")
    k3.metric("📊 Avg per Week",     f"{kpis['avg_per_week']}",
              help="Average weekly churn count")
    k4.metric("⚡ Avg Signal Count", f"{kpis['avg_signal_count']}",
              help="Avg risk signals churned customers had before exiting")

    st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)

    # ── Row 1: Weekly trend + Exit Type Summary ───────────────────────────
    col1, col2 = st.columns([3, 2])

    with col1:
        st.caption(f"**Weekly Churn Volume** · last {weeks} weeks · 💡 click a point to see customers")
        fig1 = px.line(weekly, x="exit_week", y="churned",
                       markers=True, height=H,
                       color_discrete_sequence=["#E74C3C"])
        fig1.update_traces(line_width=2.5, marker_size=9)
        fig1.add_bar(x=weekly["exit_week"], y=weekly["churned"],
                     marker_color="rgba(231,76,60,0.15)", name="")
        fig1.update_layout(showlegend=False, margin=M,
                           xaxis_title="Week", yaxis_title="Customers Churned",
                           dragmode=False, clickmode="event+select")
        ev1 = st.plotly_chart(fig1, use_container_width=True, on_select="rerun",
                              key="trend_weekly", selection_mode="points")
        if ev1 and ev1.selection and ev1.selection.points:
            st.session_state.trend_dim = "week"
            st.session_state.trend_val = ev1.selection.points[0]["x"]
            st.rerun()

    with col2:
        st.caption("**Exit Type Summary** · 💡 click a bar to see customers")
        fig2 = px.bar(summary.sort_values("churned"),
                      x="churned", y="exit_type", orientation="h",
                      color="exit_type", text="churned",
                      color_discrete_map=EXIT_COLORS, height=H)
        fig2.update_traces(textposition="outside")
        fig2.update_layout(showlegend=False, margin=M,
                           xaxis_title="", yaxis_title="",
                           dragmode=False, clickmode="event+select")
        ev2 = st.plotly_chart(fig2, use_container_width=True, on_select="rerun",
                              key="trend_exit_type", selection_mode="points")
        if ev2 and ev2.selection and ev2.selection.points:
            st.session_state.trend_dim = "exit_type"
            st.session_state.trend_val = ev2.selection.points[0]["y"]
            st.rerun()

    st.markdown("<div style='margin-top:4px'></div>", unsafe_allow_html=True)

    # ── Row 2: Stacked area + Branch ─────────────────────────────────────
    col3, col4 = st.columns([3, 2])

    with col3:
        st.caption(f"**Churn by Exit Type Over Time** · last {weeks} weeks")
        fig3 = px.area(by_type, x="exit_week", y="churned",
                       color="exit_type", height=H,
                       color_discrete_map=EXIT_COLORS)
        fig3.update_layout(margin=M, xaxis_title="Week", yaxis_title="Customers",
                           legend=dict(orientation="h", y=-0.25, x=0, font_size=11),
                           dragmode=False)
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.caption("**Churn by Branch** · 💡 click a bar to see customers")
        fig4 = px.bar(branch.sort_values("churned", ascending=True),
                      x="churned", y="branch", orientation="h",
                      color="churned", text="churned",
                      color_continuous_scale="Reds", height=H)
        fig4.update_traces(textposition="outside")
        fig4.update_layout(coloraxis_showscale=False, margin=M,
                           xaxis_title="", yaxis_title="",
                           dragmode=False, clickmode="event+select")
        ev4 = st.plotly_chart(fig4, use_container_width=True, on_select="rerun",
                              key="trend_branch", selection_mode="points")
        if ev4 and ev4.selection and ev4.selection.points:
            st.session_state.trend_dim = "branch"
            st.session_state.trend_val = ev4.selection.points[0]["y"]
            st.rerun()

    # ── Row 3: Segment trend ──────────────────────────────────────────────
    st.caption(f"**Churn by Segment Over Time** · last {weeks} weeks · 💡 click a point to see customers")
    fig5 = px.line(by_seg, x="exit_week", y="churned", color="segment",
                   markers=True, height=220,
                   color_discrete_sequence=PALETTE)
    fig5.update_layout(margin=dict(t=5,b=5,l=30,r=10),
                       xaxis_title="Week", yaxis_title="Customers Churned",
                       legend=dict(orientation="h", y=1.12, x=0),
                       dragmode=False, clickmode="event+select")
    ev5 = st.plotly_chart(fig5, use_container_width=True, on_select="rerun",
                          key="trend_segment", selection_mode="points")
    if ev5 and ev5.selection and ev5.selection.points:
        st.session_state.trend_dim = "segment"
        st.session_state.trend_val = ev5.selection.points[0]["legendgroup"]
        st.rerun()
