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
    .doc-section-teal   { border-left-color: #0097A7 !important; }
    .kpi-box {
        background: #F4F8FF; border-radius: 8px;
        padding: 0.6rem 1rem; margin-bottom: 0.6rem;
    }
    .kpi-name { font-weight: 700; color: #1565C0; font-size: 15px; }
    .kpi-desc { color: #333; font-size: 14px; margin-top: 2px; }
    .kpi-note { color: #777; font-size: 12px; font-style: italic; margin-top: 3px; }
    .tab-card {
        background: #FFFFFF; border-radius: 10px;
        padding: 0.9rem 1.1rem; margin-bottom: 0.8rem;
        border-top: 4px solid #1565C0;
        height: 100%;
    }
    .tab-card h5 { margin: 0 0 6px 0; font-size: 15px; }
    .tab-card p, .tab-card li { font-size: 13px; color: #333; line-height: 1.6; }
</style>
"""


def show():
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom:10px'></div>", unsafe_allow_html=True)

    st.markdown("""
    <div style='background:#1565C0;border-radius:10px;padding:1.2rem 1.6rem;margin-bottom:1.2rem;'>
        <h2 style='color:white;margin:0;'>📖 Deposits Attrition Intelligence</h2>
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
            Every tab is designed to support that workflow — from a portfolio-level health check,
            to a branch call list you can work through today, to plain-English data queries
            you can run without writing a single line of SQL.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Customer Status ─────────────────────────────────────────────────
    st.markdown("""
    <div class='doc-section doc-section-red'>
        <h4 style='margin:0 0 10px 0;'>👤 Customer Status — Active vs Inactive vs Churned</h4>
        <p style='font-size:14px;color:#333;margin:0 0 10px 0;'>
            Every customer is classified into one of three statuses based on transaction activity.
            The Overview, Risk Analysis, and Action List tabs focus on <strong>Active + Inactive</strong>
            customers — those still reachable. Churned customers appear separately in Churn Trends.
        </p>
    </div>
    """, unsafe_allow_html=True)

    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown("""
        <div class='kpi-box'>
            <div class='kpi-name'>✅ Active</div>
            <div class='kpi-desc'>At least one customer-initiated transaction in the last 180 days. The relationship is alive — may still carry risk signals.</div>
        </div>
        """, unsafe_allow_html=True)
    with s2:
        st.markdown("""
        <div class='kpi-box'>
            <div class='kpi-name'>⏸️ Inactive</div>
            <div class='kpi-desc'>No customer transaction for 180–365 days. Account still open — there is still time to act, but urgency is high.</div>
            <div class='kpi-note'>Inactive ≠ Churned. Reach out now.</div>
        </div>
        """, unsafe_allow_html=True)
    with s3:
        st.markdown("""
        <div class='kpi-box'>
            <div class='kpi-name'>❌ Churned</div>
            <div class='kpi-desc'>Account closed, or no transaction for 365+ days (dormant). These customers have already left. Tracked in Churn Trends only.</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Risk Levels ─────────────────────────────────────────────────────
    st.markdown("""
    <div class='doc-section doc-section-orange'>
        <h4 style='margin:0 0 10px 0;'>🚦 Risk Levels — how is risk calculated?</h4>
        <p style='font-size:13px;color:#555;margin:0 0 10px 0;'>
            Each active/inactive customer is assigned a risk level based on how many of the
            7 warning signals are present. The more signals, the higher the urgency.
        </p>
    </div>
    """, unsafe_allow_html=True)

    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.markdown("""
        <div class='kpi-box' style='border-left:4px solid #E74C3C;'>
            <div class='kpi-name' style='color:#E74C3C;'>🔴 High Risk</div>
            <div class='kpi-desc'>3 or more signals present, <strong>or</strong> salary diversion alone. Call within 24 hours.</div>
        </div>
        """, unsafe_allow_html=True)
    with r2:
        st.markdown("""
        <div class='kpi-box' style='border-left:4px solid #E67E22;'>
            <div class='kpi-name' style='color:#E67E22;'>🟠 Medium Risk</div>
            <div class='kpi-desc'>Exactly 2 signals present. Schedule a contact within the week.</div>
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
            <div class='kpi-desc'>No signals detected. Customer is engaged and stable.</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Risk Signals ─────────────────────────────────────────────────────
    st.markdown("""
    <div class='doc-section doc-section-red'>
        <h4 style='margin:0 0 10px 0;'>⚡ The 7 Risk Signals</h4>
        <p style='font-size:13px;color:#555;margin:0;'>
            These are the specific warning signs the system monitors for each customer.
            Each signal is a binary flag (1 = triggered, 0 = not triggered).
        </p>
    </div>
    """, unsafe_allow_html=True)

    sig1, sig2 = st.columns(2)
    with sig1:
        st.markdown("""
        | Signal | Trigger Condition |
        |--------|-------------------|
        | 💸 **Salary Diverted** | Salary credits stopped flowing into this bank (Savings/Current only) |
        | 💤 **Txn Inactive** | No customer-initiated transaction in the last 90+ days |
        | 📉 **Low Balance** | Balance below minimum threshold for 30+ consecutive days |
        | 📅 **FD/RD Maturing** | Fixed or Recurring Deposit maturing within 30 days — renewal at risk |
        """)
    with sig2:
        st.markdown("""
        | Signal | Trigger Condition |
        |--------|-------------------|
        | ⚠️ **Complaints ≥ 2** | 2 or more unresolved complaints on record |
        | 📵 **Digital Inactive** | No mobile/internet banking login in 60+ days |
        | 😞 **Low NPS** | Net Promoter Score is 30 or below |
        """)

    # ── Tab Guide ─────────────────────────────────────────────────────────
    st.markdown("""
    <div class='doc-section doc-section-green'>
        <h4 style='margin:0 0 12px 0;'>🗂️ Tab-by-Tab Guide</h4>
    </div>
    """, unsafe_allow_html=True)

    # Row 1 — Overview, Churn Trends, Risk Analysis
    tc1, tc2, tc3 = st.columns(3)
    with tc1:
        st.markdown("""
        <div class='tab-card' style='border-top-color:#1565C0;'>
            <h5>📊 Overview</h5>
            <p>Portfolio health at a glance — Active + Inactive customers only.</p>
            <ul>
                <li><strong>KPIs:</strong> Active Customers, At-Risk Count, Deposits Exposed (% of portfolio), Loan Outstanding at Risk (% of loan book)</li>
                <li><strong>Charts:</strong> Risk level distribution, at-risk rate by segment and account type, at-risk count by branch, signal frequency heatmap, Top 5 High-Risk customers by balance</li>
                <li><strong>Drill-down:</strong> Click any bar → branch breakdown → individual customer table</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with tc2:
        st.markdown("""
        <div class='tab-card' style='border-top-color:#8E44AD;'>
            <h5>📉 Churn Trends</h5>
            <p>Historical view of confirmed exits — customers who have already churned.</p>
            <ul>
                <li><strong>Window:</strong> Adjustable to last 4 / 8 / 13 / 26 / 52 weeks</li>
                <li><strong>KPIs:</strong> Total Churned, % With Loans, Avg per Week, Avg Signal Count at exit</li>
                <li><strong>Charts:</strong> Weekly volume, exit type breakdown, stacked area by type, branch trend, segment trend</li>
                <li><strong>Drill-down:</strong> Click any chart point → list of customers that week/branch/segment</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with tc3:
        st.markdown("""
        <div class='tab-card' style='border-top-color:#27AE60;'>
            <h5>🔍 Risk Analysis</h5>
            <p>Deeper analytical view of what's driving risk in the active portfolio.</p>
            <ul>
                <li><strong>Row 1:</strong> At-risk rate per signal type, NPS band impact, complaint count impact</li>
                <li><strong>Row 2:</strong> Average balance comparison (At-Risk vs Safe), days since last transaction, average products held</li>
                <li>Filtered to <strong>Active + Inactive</strong> customers only</li>
                <li>Use this monthly to identify which signals are most predictive in your branch</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # Row 2 — Action List, Ask the Data
    tc4, tc5 = st.columns(2)
    with tc4:
        st.markdown("""
        <div class='tab-card' style='border-top-color:#E67E22;'>
            <h5>⚠️ Action List</h5>
            <p>Your daily call list — who to contact and what to say.</p>
            <ul>
                <li><strong>Filters:</strong> Branch, Risk Level (multi-select), Segment, Account Type</li>
                <li><strong>Default view:</strong> High + Medium risk, sorted by risk level then balance</li>
                <li><strong>Columns:</strong> Customer ID, Branch, Segment, Account, Status, Risk badge, Balance, Days Since Txn, Active Signals, Recommended Action</li>
                <li><strong>Actions are prioritised by:</strong> Salary diversion → FD maturing → Complaints → Low balance → Txn inactive → Digital inactive → Low NPS</li>
                <li>Export the list to CSV and share with your team or log in CRM</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with tc5:
        st.markdown("""
        <div class='tab-card' style='border-top-color:#0097A7;'>
            <h5>🧠 Ask the Data</h5>
            <p>Type a question in plain English — it is automatically converted to SQL and run against the database. No SQL knowledge needed.</p>
            <ul>
                <li>Powered by <strong>Groq AI</strong> (llama-3.1-8b-instant) — free and fast</li>
                <li>8 <strong>example question buttons</strong> to get started instantly</li>
                <li>Results shown as a table, downloadable as CSV</li>
                <li>Generated SQL visible in an expandable panel (for verification)</li>
                <li><strong>Safety:</strong> Only SELECT queries are allowed — no data can be modified</li>
                <li>Works across all columns: customer status, risk level, signals, balances, loans, branches, and more</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # ── Recommended Workflow ───────────────────────────────────────────────
    st.markdown("""
    <div class='doc-section doc-section-purple'>
        <h4 style='margin:0 0 10px 0;'>✅ Recommended Workflows</h4>
    </div>
    """, unsafe_allow_html=True)

    wf1, wf2, wf3 = st.columns(3)
    with wf1:
        st.markdown("""
        **📅 Daily (Branch Manager)**
        1. Open **Overview** — check if At-Risk count or Deposits Exposed have moved. Look for any branch showing a spike.
        2. Go to **Action List** — filter to your branch, keep High + Medium risk. Work top-to-bottom (highest balance first).
        3. Check the **Recommended Action** column — a salary diversion call is different from an FD renewal call.
        4. Export the list to CSV and assign calls to your RMs for the day.
        """)
    with wf2:
        st.markdown("""
        **📆 Weekly (Area Manager)**
        1. Open **Churn Trends** — set window to 4 or 8 weeks.
        2. Check if weekly churn volume is rising and which exit type is growing fastest.
        3. Click on a branch bar to see which customers churned this week.
        4. Use **Ask the Data** for ad-hoc questions: *"Which branch had the most salary diversions this month?"*
        """)
    with wf3:
        st.markdown("""
        **📊 Monthly (Analytics / Leadership)**
        1. Open **Risk Analysis** — identify which signals are most predictive across the portfolio.
        2. Compare at-risk rates across segments and account types. Are HNI customers being missed?
        3. Set **Churn Trends** to 13 or 26 weeks. Spot seasonal patterns in exit behaviour.
        4. Use **Ask the Data** for custom deep-dives without needing to export to Excel.
        """)

    # ── Ask the Data Tips ──────────────────────────────────────────────────
    st.markdown("""
    <div class='doc-section doc-section-teal'>
        <h4 style='margin:0 0 10px 0;'>🧠 Tips for Using "Ask the Data"</h4>
        <p style='font-size:13px;color:#555;margin:0 0 10px 0;'>
            The AI understands all column names and business terms. Here are some examples of questions you can ask:
        </p>
    </div>
    """, unsafe_allow_html=True)

    aq1, aq2 = st.columns(2)
    with aq1:
        st.markdown("""
        **Customer queries**
        - *Show me all High risk customers in Muscat Main branch*
        - *List inactive customers in the SME segment with balance above 50,000 OMR*
        - *Which customers have 3 or more complaints and are still active?*
        - *Show top 10 HNI customers by loan outstanding who are at risk*

        **Branch / Segment summaries**
        - *Which branch has the highest at-risk rate?*
        - *How many High risk customers are there per branch?*
        - *Show me average balance by risk level and segment*
        """)
    with aq2:
        st.markdown("""
        **Signal analysis**
        - *How many customers have salary diverted and are still active?*
        - *What percentage of Inactive customers have an FD maturing?*
        - *Show attrition rate by account type*

        **Churn / trend queries**
        - *List churned customers who had a loan outstanding*
        - *Which customers churned via salary diversion in the last 6 months?*
        - *Show me customers who exited with 3 or more risk signals*

        > 💡 **Tip:** Be specific. Include branch names, segments, or thresholds for best results. The generated SQL is shown below the results so you can verify it.
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
        | **NPS** | Net Promoter Score (0–100). ≤ 30 = unhappy customer (Detractor) |
        | **At-Risk** | Customer with High or Medium risk level |
        """)
    with g2:
        st.markdown("""
        | Term | Meaning |
        |------|---------|
        | **Deposits Exposed** | Total OMR balance held by High + Medium risk customers |
        | **Loan Outstanding (At-Risk)** | Total loan balance held by At-Risk customers |
        | **At-Risk Rate** | % of Active + Inactive customers with High or Medium risk |
        | **Exit Week** | Week number (1–52) when a customer was confirmed churned |
        | **Drill-down** | Click a chart bar → branch view → individual customer table |
        | **Churned** | Account closed, or 365+ days of inactivity (dormant = churned) |
        | **Groq / LLM** | AI model powering the Ask the Data natural language engine |
        """)
