# ============================================================
#  Deposits Attrition Data App  —  Overview Page
#  KPI cards + attrition summary charts
# ============================================================

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.express as px
from database import query


# ── Load all summary data ────────────────────────────────────
@st.cache_data
def load_summary():

    kpis = query("""
        SELECT
            COUNT(*)                                             AS total_customers,
            ROUND(AVG(attrition_flag)::numeric * 100, 2)        AS attrition_rate,
            ROUND(SUM(CASE WHEN attrition_flag = 1
                          THEN balance ELSE 0 END)::numeric, 0) AS deposits_at_risk,
            ROUND(AVG(balance)::numeric, 0)                     AS avg_balance,
            SUM(attrition_flag)                                 AS total_churned
        FROM customers
    """)

    by_segment = query("""
        SELECT segment,
               COUNT(*)                                       AS customers,
               SUM(attrition_flag)                            AS churned,
               ROUND(AVG(attrition_flag)::numeric * 100, 1)  AS attrition_rate
        FROM customers
        GROUP BY segment
        ORDER BY attrition_rate DESC
    """)

    by_account = query("""
        SELECT account_type,
               COUNT(*)                                       AS customers,
               SUM(attrition_flag)                            AS churned,
               ROUND(AVG(attrition_flag)::numeric * 100, 1)  AS attrition_rate
        FROM customers
        GROUP BY account_type
        ORDER BY attrition_rate DESC
    """)

    by_tenure = query("""
        SELECT
            CASE
                WHEN tenure_years <= 2  THEN '0-2 yrs'
                WHEN tenure_years <= 5  THEN '3-5 yrs'
                WHEN tenure_years <= 10 THEN '6-10 yrs'
                ELSE '10+ yrs'
            END AS tenure_bucket,
            ROUND(AVG(attrition_flag)::numeric * 100, 1) AS attrition_rate,
            COUNT(*)                                      AS customers
        FROM customers
        GROUP BY tenure_bucket
        ORDER BY MIN(tenure_years)
    """)

    by_type = query("""
        SELECT attrition_type, COUNT(*) AS count
        FROM   customers
        WHERE  attrition_flag = 1
        GROUP  BY attrition_type
    """)

    deposits_by_segment = query("""
        SELECT segment,
               ROUND((SUM(balance) / 1e6)::numeric, 2) AS total_deposits_m
        FROM   customers
        GROUP  BY segment
    """)

    return kpis, by_segment, by_account, by_tenure, by_type, deposits_by_segment


# ── Page ─────────────────────────────────────────────────────
def show():
    st.title("📊 Overview Dashboard")
    st.caption("High-level snapshot of deposit attrition across the portfolio.")
    st.divider()

    kpis, by_segment, by_account, by_tenure, by_type, deposits_by_segment = load_summary()

    k = kpis.iloc[0]

    # ── KPI Cards ────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        label="👥 Total Customers",
        value=f"{int(k['total_customers']):,}",
    )
    c2.metric(
        label="⚠️ Attrition Rate",
        value=f"{k['attrition_rate']}%",
        delta=f"{int(k['total_churned']):,} customers churned",
        delta_color="inverse",
    )
    c3.metric(
        label="💰 Deposits at Risk",
        value=f"₹ {int(k['deposits_at_risk']):,}",
        delta="Balance of churned customers",
        delta_color="inverse",
    )
    c4.metric(
        label="🏦 Avg Customer Balance",
        value=f"₹ {int(k['avg_balance']):,}",
    )

    st.divider()

    # ── Row 1: Attrition by Segment + Account Type ───────────
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Attrition Rate by Segment")
        fig = px.bar(
            by_segment, x="segment", y="attrition_rate",
            color="segment", text="attrition_rate",
            labels={"attrition_rate": "Attrition Rate (%)", "segment": "Segment"},
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(showlegend=False, yaxis_range=[0, 40])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Attrition Rate by Account Type")
        fig2 = px.bar(
            by_account, x="account_type", y="attrition_rate",
            color="account_type", text="attrition_rate",
            labels={"attrition_rate": "Attrition Rate (%)", "account_type": "Account Type"},
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig2.update_traces(texttemplate="%{text}%", textposition="outside")
        fig2.update_layout(showlegend=False, yaxis_range=[0, 40])
        st.plotly_chart(fig2, use_container_width=True)

    # ── Row 2: Tenure + Exit Type ────────────────────────────
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Attrition Rate by Customer Tenure")
        fig3 = px.bar(
            by_tenure, x="tenure_bucket", y="attrition_rate",
            color="attrition_rate", text="attrition_rate",
            labels={"attrition_rate": "Attrition Rate (%)", "tenure_bucket": "Tenure"},
            color_continuous_scale="Reds",
        )
        fig3.update_traces(texttemplate="%{text}%", textposition="outside")
        fig3.update_layout(coloraxis_showscale=False, yaxis_range=[0, 45])
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.subheader("Churned Customers — Exit Type")
        fig4 = px.pie(
            by_type, names="attrition_type", values="count",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig4.update_traces(textinfo="percent+label")
        st.plotly_chart(fig4, use_container_width=True)

    # ── Row 3: Total Deposits by Segment ─────────────────────
    st.subheader("Total Deposits by Segment (₹ Million)")
    fig5 = px.bar(
        deposits_by_segment, x="segment", y="total_deposits_m",
        color="segment", text="total_deposits_m",
        labels={"total_deposits_m": "Deposits (₹ M)", "segment": "Segment"},
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    fig5.update_traces(texttemplate="₹ %{text}M", textposition="outside")
    fig5.update_layout(showlegend=False)
    st.plotly_chart(fig5, use_container_width=True)
