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
    "Account Closure"      : "#E74C3C",
    "Extended Inactivity"  : "#E67E22",
    "Salary Diversion"     : "#8E44AD",
    "Balance Dormancy"     : "#2980B9",
    "Transaction Inactivity": "#27AE60",
}


@st.cache_data
def load_weekly_trend(weeks):
    return query(f"""
        SELECT exit_week,
               COUNT(*) AS churned,
               ROUND(SUM(balance)/1e6, 3) AS balance_lost_m
        FROM customers
        WHERE customer_status = 'Churned'
          AND exit_week >= (53 - {weeks})
        GROUP BY exit_week
        ORDER BY exit_week
    """)


@st.cache_data
def load_exit_type_trend(weeks):
    return query(f"""
        SELECT exit_week, exit_type, COUNT(*) AS churned
        FROM customers
        WHERE customer_status = 'Churned'
          AND exit_week >= (53 - {weeks})
        GROUP BY exit_week, exit_type
        ORDER BY exit_week
    """)


@st.cache_data
def load_segment_trend(weeks):
    return query(f"""
        SELECT exit_week, segment, COUNT(*) AS churned
        FROM customers
        WHERE customer_status = 'Churned'
          AND exit_week >= (53 - {weeks})
        GROUP BY exit_week, segment
        ORDER BY exit_week
    """)


@st.cache_data
def load_branch_churn(weeks):
    return query(f"""
        SELECT branch,
               COUNT(*) AS churned,
               ROUND(SUM(balance)/1e6, 3) AS balance_lost_m
        FROM customers
        WHERE customer_status = 'Churned'
          AND exit_week >= (53 - {weeks})
        GROUP BY branch
        ORDER BY churned DESC
    """)


@st.cache_data
def load_exit_type_summary(weeks):
    return query(f"""
        SELECT exit_type, COUNT(*) AS churned,
               ROUND(SUM(balance)/1e6,3) AS balance_lost_m
        FROM customers
        WHERE customer_status = 'Churned'
          AND exit_week >= (53 - {weeks})
        GROUP BY exit_type
        ORDER BY churned DESC
    """)


@st.cache_data
def load_summary_kpis(weeks):
    return query(f"""
        SELECT COUNT(*) AS total_churned,
               ROUND(SUM(balance)/1e6, 3) AS total_balance_m,
               ROUND(AVG(balance), 0)     AS avg_balance,
               ROUND(COUNT(*)*1.0 / {weeks}, 1) AS avg_per_week
        FROM customers
        WHERE customer_status = 'Churned'
          AND exit_week >= (53 - {weeks})
    """)


def show():
    H = 240
    M = dict(t=10, b=5, l=30, r=10)

    # ── Filter bar ─────────────────────────────────────────────────────
    fc1, fc2 = st.columns([3, 5])
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
            "Showing confirmed exits — customers who closed accounts or became inactive for 365+ days."
            "</div>", unsafe_allow_html=True)

    st.divider()

    kpis    = load_summary_kpis(weeks).iloc[0]
    weekly  = load_weekly_trend(weeks)
    by_type = load_exit_type_trend(weeks)
    by_seg  = load_segment_trend(weeks)
    branch  = load_branch_churn(weeks)
    summary = load_exit_type_summary(weeks)

    # ── KPI row ─────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🚪 Total Churned",    f"{int(kpis['total_churned']):,}",
              help=f"Churned in the last {weeks} weeks")
    k2.metric("💸 Balance Lost",     f"OMR {kpis['total_balance_m']}M",
              help="Total deposit balance of churned customers")
    k3.metric("📊 Avg per Week",     f"{kpis['avg_per_week']}",
              help="Average weekly churn rate")
    k4.metric("💰 Avg Balance Lost", f"OMR {int(kpis['avg_balance']):,}",
              help="Average balance per churned customer")

    st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)

    # ── Row 1: Weekly trend ──────────────────────────────────────────────
    col1, col2 = st.columns([3, 2])

    with col1:
        st.caption(f"**Weekly Churn Volume** · last {weeks} weeks")
        fig1 = px.line(weekly, x="exit_week", y="churned",
                       markers=True, height=H,
                       color_discrete_sequence=["#E74C3C"])
        fig1.update_traces(line_width=2.5, marker_size=7)
        fig1.add_bar(x=weekly["exit_week"], y=weekly["churned"],
                     marker_color="rgba(231,76,60,0.15)", name="")
        fig1.update_layout(showlegend=False, margin=M,
                           xaxis_title="Week", yaxis_title="Customers Churned",
                           dragmode=False)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.caption("**Exit Type Summary**")
        fig2 = px.bar(summary.sort_values("churned"),
                      x="churned", y="exit_type", orientation="h",
                      color="exit_type", text="churned",
                      color_discrete_map=EXIT_COLORS, height=H)
        fig2.update_traces(textposition="outside")
        fig2.update_layout(showlegend=False, margin=M,
                           xaxis_title="", yaxis_title="",
                           dragmode=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<div style='margin-top:4px'></div>", unsafe_allow_html=True)

    # ── Row 2: Stacked trend + Branch ────────────────────────────────────
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
        st.caption("**Churn by Branch**")
        fig4 = px.bar(branch.sort_values("churned", ascending=True),
                      x="churned", y="branch", orientation="h",
                      color="churned", text="churned",
                      color_continuous_scale="Reds", height=H)
        fig4.update_traces(textposition="outside")
        fig4.update_layout(coloraxis_showscale=False, margin=M,
                           xaxis_title="", yaxis_title="",
                           dragmode=False)
        st.plotly_chart(fig4, use_container_width=True)

    # ── Row 3: Segment trend ──────────────────────────────────────────────
    st.caption(f"**Churn by Segment Over Time** · last {weeks} weeks")
    fig5 = px.line(by_seg, x="exit_week", y="churned", color="segment",
                   markers=True, height=220,
                   color_discrete_sequence=PALETTE)
    fig5.update_layout(margin=dict(t=5,b=5,l=30,r=10),
                       xaxis_title="Week", yaxis_title="Customers Churned",
                       legend=dict(orientation="h", y=1.12, x=0),
                       dragmode=False)
    st.plotly_chart(fig5, use_container_width=True)
