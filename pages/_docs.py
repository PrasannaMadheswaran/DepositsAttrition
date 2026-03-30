import sys, os
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st

_CSS = """
<style>
    /* Section header cards */
    .doc-section {
        background: #FFFFFF;
        border-radius: 10px;
        padding: 1.1rem 1.4rem 0.8rem 1.4rem;
        margin-bottom: 1rem;
        border-left: 5px solid #1565C0;
    }
    .doc-section-orange { border-left-color: #E67E22 !important; }
    .doc-section-green  { border-left-color: #27AE60 !important; }
    .doc-section-purple { border-left-color: #8E44AD !important; }
    .doc-section-red    { border-left-color: #C0392B !important; }

    /* KPI definition boxes */
    .kpi-box {
        background: #F4F8FF;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        margin-bottom: 0.6rem;
    }
    .kpi-name  { font-weight: 700; color: #1565C0; font-size: 15px; }
    .kpi-desc  { color: #333; font-size: 14px; margin-top: 2px; }
    .kpi-note  { color: #777; font-size: 12px; font-style: italic; margin-top: 3px; }

    /* Attrition type badges */
    .badge {
        display: inline-block;
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 12px;
        font-weight: 600;
        margin: 2px 3px 2px 0;
    }
    .badge-red    { background:#FADBD8; color:#C0392B; }
    .badge-orange { background:#FDEBD0; color:#E67E22; }
    .badge-blue   { background:#D6EAF8; color:#1565C0; }
    .badge-gray   { background:#EAECEE; color:#555;    }
</style>
"""


def show():
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom:10px'></div>", unsafe_allow_html=True)

    # ── Page title ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div style='background:#1565C0;border-radius:10px;padding:1.2rem 1.6rem;margin-bottom:1.2rem;'>
        <h2 style='color:white;margin:0;'>📖 Dashboard Guide</h2>
        <p style='color:#BBDEFB;margin:4px 0 0 0;font-size:14px;'>
            Deposits Attrition Intelligence — Oman Banking
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — Purpose
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div class='doc-section'>
        <h4 style='margin:0 0 8px 0;'>🎯 What is this dashboard?</h4>
        <p style='margin:0;font-size:14px;color:#333;line-height:1.7;'>
            This dashboard helps <strong>branch managers and relationship managers</strong>
            identify customers who are likely to close their accounts or move their deposits
            to another bank — a process known as <strong>deposit attrition</strong>.
            <br><br>
            By monitoring attrition patterns early, the team can take proactive steps —
            such as a retention call, a product offer, or a branch visit — before a
            customer is lost.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — What counts as attrition?
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div class='doc-section doc-section-red'>
        <h4 style='margin:0 0 10px 0;'>⚠️ What counts as customer attrition?</h4>
        <p style='margin:0 0 10px 0;font-size:14px;color:#333;'>
            A customer is marked as <strong>attrited</strong> when they have meaningfully
            severed their relationship with the bank. This is NOT simply an account maturity
            or an internal product switch. There are two ways a customer can be attrited:
        </p>
        <p style='font-size:13px;color:#333;margin:6px 0 4px 0;'><strong>Primary triggers</strong> (either one is sufficient):</p>
        <ul style='font-size:13px;color:#444;margin:0 0 8px 0;line-height:1.8;'>
            <li><strong>Account Closure</strong> — customer explicitly closed their primary deposit account and did not open a replacement. For Fixed Deposit and Recurring Deposit customers, this only applies if they held a single product and chose not to renew it.</li>
            <li><strong>Salary Diversion</strong> — the customer stopped receiving their salary into this bank (applicable to Savings and Current accounts only).</li>
        </ul>
        <p style='font-size:13px;color:#333;margin:6px 0 4px 0;'><strong>Combined risk signals</strong> (3 or more together indicate attrition):</p>
        <ul style='font-size:13px;color:#444;margin:0;line-height:1.8;'>
            <li>Balance falling below minimum threshold for 30+ days</li>
            <li>No transactions for 90+ days</li>
            <li>2 or more unresolved complaints</li>
            <li>No digital banking login for 60+ days</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 3 — KPI cards
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div class='doc-section doc-section-orange'>
        <h4 style='margin:0 0 10px 0;'>📊 KPI Cards — Overview Tab</h4>
        <p style='font-size:13px;color:#555;margin:0 0 10px 0;'>
            The four cards at the top of the Overview tab give an instant snapshot of the bank's deposit health.
            Each title is clickable — it drills down to a branch-level comparison.
        </p>
    </div>
    """, unsafe_allow_html=True)

    k1, k2 = st.columns(2)
    with k1:
        st.markdown("""
        <div class='kpi-box'>
            <div class='kpi-name'>👥 Total Customers</div>
            <div class='kpi-desc'>Total number of customers in the portfolio — both active and attrited.</div>
            <div class='kpi-note'>Click to compare customer count across branches.</div>
        </div>
        <div class='kpi-box'>
            <div class='kpi-name'>💰 Deposits at Risk (OMR)</div>
            <div class='kpi-desc'>Total deposit balance held by attrited customers at the time of their last activity. This is the OMR amount the bank has lost or is at risk of losing.</div>
            <div class='kpi-note'>Click to compare deposits at risk across branches.</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown("""
        <div class='kpi-box'>
            <div class='kpi-name'>⚠️ Attrition Rate</div>
            <div class='kpi-desc'>Percentage of customers who have attrited out of the total portfolio. The sub-number shows the actual count of churned customers.</div>
            <div class='kpi-note'>Target range: 15–22%. Higher rates need immediate branch-level investigation.</div>
        </div>
        <div class='kpi-box'>
            <div class='kpi-name'>📉 Avg Balance (Churned)</div>
            <div class='kpi-desc'>Average deposit balance of attrited customers only. Shows the typical size of the customer being lost — useful for prioritising retention efforts (higher balance = higher urgency).</div>
            <div class='kpi-note'>Click to compare average churned balance across branches.</div>
        </div>
        """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 4 — Overview charts
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div class='doc-section doc-section-orange'>
        <h4 style='margin:0 0 10px 0;'>📈 Overview Charts</h4>
        <p style='font-size:13px;color:#555;margin:0;'>
            Six charts split across two rows. The top row shows <strong>who is churning</strong>;
            the bottom row shows <strong>the financial impact</strong>.
            Every bar is clickable — clicking drills into a branch breakdown, and clicking
            a branch shows the individual customers behind that number.
        </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        **Row 1 — Who is churning?**
        - **Attrition by Segment** — compares HNI, SME, and Retail attrition rates. Helps spot if a particular customer tier is more at risk.
        - **Attrition by Account Type** — compares Savings, Current, FD, and RD. Useful for product-level interventions.
        - **Attrition by Tenure** — shows whether new customers (0–2 yrs) or long-tenured customers (10+ yrs) are churning more.
        """)
    with c2:
        st.markdown("""
        **Row 2 — Financial impact (churned customers only)**
        - **Exit Type Breakdown** — how customers are leaving: Account Closure, Salary Diversion, Balance Dormancy, or Transaction Inactivity.
        - **Deposits at Risk by Segment** — total OMR balance lost per segment (HNI, SME, Retail).
        - **Deposits at Risk by Account Type** — total OMR balance lost per account product type.
        """)
    with c3:
        st.markdown("""
        **How drill-downs work**

        1. **Click any bar** on the main dashboard → opens a branch-level breakdown of that same metric.
        2. **Click any branch bar** → opens a table of individual customers behind that number.
        3. **Click ⬆️ Back** buttons to return to the previous level.

        Alternatively, clicking any **KPI card title** (blue underlined link) also drills into a branch comparison for that metric.
        """)

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 5 — EDA tab
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div class='doc-section doc-section-green'>
        <h4 style='margin:0 0 10px 0;'>🔍 EDA Tab — Risk Drivers & Behavioural Profile</h4>
        <p style='font-size:13px;color:#555;margin:0 0 8px 0;'>
            The EDA (Exploratory Data Analysis) tab goes deeper than the Overview —
            it explains <em>why</em> customers churn and <em>how</em> churned customers
            differ from active ones in their day-to-day banking behaviour.
        </p>
        <p style='font-size:13px;color:#555;margin:0;'>
            Use the <strong>Segment</strong> and <strong>Branch</strong> filters at the top
            to focus the analysis on a specific customer group or location.
        </p>
    </div>
    """, unsafe_allow_html=True)

    e1, e2 = st.columns(2)
    with e1:
        st.markdown("""
        **Row 1 — Risk Drivers** *(what triggers churn?)*

        - **Attrition Rate by Risk Factor** — for each warning signal (salary diverted, no transactions, low balance, complaints, digital inactivity, low NPS), this shows the attrition rate among customers who have that signal. Click any bar to see those customers.
        - **NPS Band vs Attrition Rate** — compares Detractors (score ≤ 30), Passives (31–70), and Promoters (> 70). A high Detractor attrition rate signals a service quality issue.
        - **Complaint Count vs Attrition Rate** — shows whether customers with 0, 1, 2, or 3+ complaints churn at different rates. Rising complaints are a leading indicator of attrition.
        """)
    with e2:
        st.markdown("""
        **Row 2 — Behavioural Profile** *(how do churners differ?)*

        - **Avg Balance — Churned vs Active** — side-by-side comparison of the average deposit balance for churned and active customers, split by segment. A large gap means the bank is losing high-value customers.
        - **Avg Days Since Last Txn — Churned vs Active** — shows how long before churning a customer had stopped transacting. Larger gaps = more dormancy before exit.
        - **Avg Products Held — Churned vs Active** — customers with more products (loans, cards, investments) typically churn less. A lower product count in churned customers confirms the cross-sell opportunity.
        """)

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 6 — Customer segments & exit types glossary
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div class='doc-section doc-section-purple'>
        <h4 style='margin:0 0 10px 0;'>📋 Glossary</h4>
    </div>
    """, unsafe_allow_html=True)

    g1, g2 = st.columns(2)
    with g1:
        st.markdown("**Customer Segments**")
        st.markdown("""
        | Segment | Description |
        |---------|-------------|
        | **HNI** | High Net-worth Individual — balance typically OMR 30K+ |
        | **SME** | Small & Medium Enterprise — business accounts |
        | **Retail** | Individual customers with standard deposit accounts |
        """)
        st.markdown("**Account Types**")
        st.markdown("""
        | Type | Description |
        |------|-------------|
        | **Savings** | Standard savings account with interest |
        | **Current** | Transaction account, typically used for salary |
        | **FD** | Fixed Deposit — locked for a term, auto-renewed unless declined |
        | **RD** | Recurring Deposit — regular monthly contributions |
        """)
    with g2:
        st.markdown("**Exit / Attrition Types**")
        st.markdown("""
        | Exit Type | What it means |
        |-----------|---------------|
        | **Account Closure** | Customer explicitly closed their account and did not replace it |
        | **Salary Diversion** | Salary credits moved to another bank (Savings/Current only) |
        | **Balance Dormancy** | Balance stayed below minimum for 30+ consecutive days |
        | **Transaction Inactivity** | No transactions for 90+ consecutive days |
        """)
        st.markdown("**Key Terms**")
        st.markdown("""
        | Term | Meaning |
        |------|---------|
        | **Deposits at Risk** | Total OMR balance held by attrited customers |
        | **Attrition Rate** | % of customers who have attrited from total portfolio |
        | **NPS** | Net Promoter Score (0–100). ≤30 = Detractor, 31–70 = Passive, >70 = Promoter |
        | **Drill-down** | Click a chart bar to see a branch breakdown, then individual customers |
        """)
