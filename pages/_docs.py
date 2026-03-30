import sys, os
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st

_CSS = """
<style>
    .doc-section {
        background: #FFFFFF; border-radius: 10px;
        padding: 1.1rem 1.4rem 0.8rem 1.4rem;
        margin-bottom: 1rem; border-left: 5px solid #1565C0;
    }
    .doc-section-orange { border-left-color: #E67E22 !important; }
    .doc-section-green  { border-left-color: #27AE60 !important; }
    .doc-section-purple { border-left-color: #8E44AD !important; }
    .doc-section-red    { border-left-color: #C0392B !important; }
    .kpi-box {
        background: #F4F8FF; border-radius: 8px;
        padding: 0.6rem 1rem; margin-bottom: 0.6rem;
    }
    .kpi-name { font-weight: 700; color: #1565C0; font-size: 15px; }
    .kpi-desc { color: #333; font-size: 14px; margin-top: 2px; }
    .kpi-note { color: #777; font-size: 12px; font-style: italic; margin-top: 3px; }
</style>
"""


def show():
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom:10px'></div>", unsafe_allow_html=True)

    st.markdown("""
    <div style='background:#1565C0;border-radius:10px;padding:1.2rem 1.6rem;margin-bottom:1.2rem;'>
        <h2 style='color:white;margin:0;'>📖 Dashboard Guide</h2>
        <p style='color:#BBDEFB;margin:4px 0 0 0;font-size:14px;'>
            Deposits Attrition Intelligence — Oman Banking
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Purpose ────────────────────────────────────────────────────────
    st.markdown("""
    <div class='doc-section'>
        <h4 style='margin:0 0 8px 0;'>🎯 What is this dashboard for?</h4>
        <p style='margin:0;font-size:14px;color:#333;line-height:1.7;'>
            This dashboard helps <strong>branch managers and relationship managers</strong>
            identify <strong>active customers who are showing early warning signs of leaving</strong>
            — before they actually close their accounts or move to another bank.
            <br><br>
            The goal is simple: <strong>spot the risk early, act fast, retain the customer.</strong>
            Every tab in this dashboard is designed to support that workflow — from spotting
            at-risk trends down to a branch-level call list you can work through today.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Customer Status ─────────────────────────────────────────────────
    st.markdown("""
    <div class='doc-section doc-section-red'>
        <h4 style='margin:0 0 10px 0;'>👤 Customer Status — what do Active and Inactive mean?</h4>
        <p style='font-size:14px;color:#333;margin:0 0 10px 0;'>
            Every customer in this dashboard is either <strong>Active</strong> or <strong>Inactive</strong>.
            Customers who have already left are tracked separately in the <strong>Churn Trends</strong> tab.
        </p>
    </div>
    """, unsafe_allow_html=True)

    s1, s2 = st.columns(2)
    with s1:
        st.markdown("""
        <div class='kpi-box'>
            <div class='kpi-name'>✅ Active</div>
            <div class='kpi-desc'>Customer has made at least one transaction in the last 180 days. The relationship is alive but may still carry risk signals.</div>
        </div>
        """, unsafe_allow_html=True)
    with s2:
        st.markdown("""
        <div class='kpi-box'>
            <div class='kpi-name'>⏸️ Inactive</div>
            <div class='kpi-desc'>No customer-initiated transactions for 180–365 days. Still technically in the bank but showing strong disengagement. Needs urgent outreach.</div>
            <div class='kpi-note'>Inactive ≠ Churned. The account is still open — there is still time to act.</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Risk Levels ─────────────────────────────────────────────────────
    st.markdown("""
    <div class='doc-section doc-section-orange'>
        <h4 style='margin:0 0 10px 0;'>🚦 Risk Levels — how is risk calculated?</h4>
        <p style='font-size:13px;color:#555;margin:0 0 10px 0;'>
            Each active/inactive customer is assigned a risk level based on how many warning
            signals are present on their account. The more signals, the higher the urgency.
        </p>
    </div>
    """, unsafe_allow_html=True)

    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.markdown("""
        <div class='kpi-box' style='border-left:4px solid #E74C3C;'>
            <div class='kpi-name' style='color:#E74C3C;'>🔴 High Risk</div>
            <div class='kpi-desc'>3 or more signals present, or salary diversion alone. Call within 24 hours.</div>
        </div>
        """, unsafe_allow_html=True)
    with r2:
        st.markdown("""
        <div class='kpi-box' style='border-left:4px solid #E67E22;'>
            <div class='kpi-name' style='color:#E67E22;'>🟠 Medium Risk</div>
            <div class='kpi-desc'>Exactly 2 signals. Schedule a contact within the week.</div>
        </div>
        """, unsafe_allow_html=True)
    with r3:
        st.markdown("""
        <div class='kpi-box' style='border-left:4px solid #F1C40F;'>
            <div class='kpi-name' style='color:#b7950b;'>🟡 Low Risk</div>
            <div class='kpi-desc'>1 signal present. Monitor — no immediate action required.</div>
        </div>
        """, unsafe_allow_html=True)
    with r4:
        st.markdown("""
        <div class='kpi-box' style='border-left:4px solid #2ECC71;'>
            <div class='kpi-name' style='color:#27AE60;'>🟢 Safe</div>
            <div class='kpi-desc'>No signals. Customer is engaged and stable.</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Risk Signals ─────────────────────────────────────────────────────
    st.markdown("""
    <div class='doc-section doc-section-red'>
        <h4 style='margin:0 0 10px 0;'>⚡ The 7 Risk Signals</h4>
        <p style='font-size:13px;color:#555;margin:0;'>
            These are the specific warning signs the system monitors for each customer.
        </p>
    </div>
    """, unsafe_allow_html=True)

    sig1, sig2 = st.columns(2)
    with sig1:
        st.markdown("""
        | Signal | Trigger |
        |--------|---------|
        | 💸 **Salary Diverted** | Salary credits stopped flowing into this bank (Savings/Current only) |
        | 💤 **Txn Inactive** | No customer transaction in the last 90+ days |
        | 📉 **Low Balance** | Balance below minimum threshold for 30+ consecutive days |
        | 📅 **FD/RD Maturing** | Fixed or Recurring Deposit maturing within 30 days — renewal at risk |
        """)
    with sig2:
        st.markdown("""
        | Signal | Trigger |
        |--------|---------|
        | ⚠️ **Complaints ≥2** | 2 or more unresolved complaints on record |
        | 📵 **Digital Inactive** | No mobile/internet banking login in 60+ days |
        | 😞 **Low NPS** | Customer's Net Promoter Score is 30 or below |
        """)

    # ── Tab Guide ─────────────────────────────────────────────────────────
    st.markdown("""
    <div class='doc-section doc-section-green'>
        <h4 style='margin:0 0 10px 0;'>🗂️ Tab-by-Tab Guide</h4>
    </div>
    """, unsafe_allow_html=True)

    t1, t2 = st.columns(2)
    with t1:
        st.markdown("""
        **📊 Overview**
        Portfolio health at a glance — Active + Inactive customers only.
        - KPIs: Active Customers, At-Risk Count, Deposits Exposed, Avg Balance (High Risk)
        - Charts: Risk level split, at-risk rates by segment/account type, at-risk count by branch, signal frequency, active vs inactive split
        - Click any bar → branch breakdown → individual customer table

        **📉 Churn Trends**
        Historical view of confirmed exits — customers who have already left.
        - Adjustable window: last 4 / 8 / 13 / 26 / 52 weeks
        - Weekly churn volume, exit type breakdown, branch and segment trends
        - Use this to spot if churn is accelerating, and which branch or segment is driving it

        **🔍 Risk Analysis**
        Deeper dive into what's causing risk in the active portfolio.
        - Row 1: Which signals have the highest at-risk rates? NPS and complaint impact
        - Row 2: How do at-risk customers differ from safe ones? (balance, activity, products)
        - Filter by segment or branch to focus the analysis
        """)
    with t2:
        st.markdown("""
        **⚠️ Action List**
        Your daily call list — who to contact and what to say.
        - Filter by branch, risk level, segment, and account type
        - Each row shows: customer details, active signals, and a recommended action
        - Default view: High + Medium risk customers, sorted by risk then balance
        - Export to CSV to share with your team or log in your CRM

        **🤖 ML Model** *(coming soon)*
        A machine learning model trained on historical churn patterns.
        Will assign a probability score to each active customer.

        **📖 Guide** *(this page)*
        Reference for understanding the dashboard, risk definitions, and recommended workflows.
        """)

    # ── Recommended Workflow ───────────────────────────────────────────────
    st.markdown("""
    <div class='doc-section doc-section-purple'>
        <h4 style='margin:0 0 10px 0;'>✅ Recommended Daily Workflow</h4>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    1. **Start on Overview** — check if At-Risk count or Deposits Exposed have moved since yesterday. Look for any branch showing a spike.
    2. **Go to Action List** — filter to your branch, keep Risk Level as High + Medium. Work through the list top-to-bottom (highest balance first).
    3. **Check the signal** — the "Recommended Action" column tells you what to say. A salary diversion call is different from an FD renewal call.
    4. **Weekly: open Churn Trends** — set the window to 4 or 8 weeks. Check if your branch churn count is rising and which exit type is growing fastest.
    5. **Monthly: open Risk Analysis** — identify which signals are most predictive in your branch. Use this to focus coaching conversations with your team.
    """)

    # ── Glossary ─────────────────────────────────────────────────────────
    st.markdown("""
    <div class='doc-section doc-section-purple'>
        <h4 style='margin:0 0 6px 0;'>📋 Glossary</h4>
    </div>
    """, unsafe_allow_html=True)

    g1, g2 = st.columns(2)
    with g1:
        st.markdown("""
        | Term | Meaning |
        |------|---------|
        | **HNI** | High Net-worth Individual — balance typically OMR 30K+ |
        | **SME** | Small & Medium Enterprise |
        | **Retail** | Standard individual deposit customer |
        | **FD** | Fixed Deposit — auto-renews unless customer declines |
        | **RD** | Recurring Deposit — monthly contributions |
        | **NPS** | Net Promoter Score (0–100). ≤30 = unhappy customer |
        """)
    with g2:
        st.markdown("""
        | Term | Meaning |
        |------|---------|
        | **Deposits Exposed** | OMR balance held by High + Medium risk customers |
        | **At-Risk Rate** | % of customers with High or Medium risk level |
        | **Exit Week** | Week number (1–52) when a customer was confirmed churned |
        | **Drill-down** | Click a bar chart → branch view → customer table |
        | **Churn** | Customer confirmed to have left (account closed or 365+ days inactive) |
        """)
