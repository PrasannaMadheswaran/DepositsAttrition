import sys, os
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
from database import query as db_query
import pandas as pd

# ── Schema context sent to Groq ───────────────────────────────────────────────
_SCHEMA = """
Table: customers
Each row = one unique banking customer.

Columns:
  customer_id         TEXT    — unique customer identifier (e.g. CUST01001)
  age                 INT     — customer age in years
  gender              TEXT    — Male / Female
  tenure_years        INT     — years with the bank
  segment             TEXT    — HNI / SME / Retail
  branch              TEXT    — branch name (e.g. Muscat Main, Salalah, Sohar, Nizwa, Sur, Ibri, Barka, Rustaq)
  account_type        TEXT    — Savings / Current / FD / RD
  balance             FLOAT   — total deposit balance in OMR
  num_accounts        INT     — number of accounts held
  num_products        INT     — total products (deposit + loan + investment + credit card)
  has_loan            INT     — 1 if customer has a loan, 0 otherwise
  loan_outstanding    FLOAT   — loan balance in OMR (0 if no loan)
  has_investment      INT     — 1 if customer has investment product
  has_credit_card     INT     — 1 if customer has credit card
  avg_monthly_credits FLOAT   — average monthly credit amount (OMR)
  avg_monthly_debits  FLOAT   — average monthly debit amount (OMR)
  num_txn_3m          INT     — number of transactions in last 3 months
  num_txn_6m          INT     — number of transactions in last 6 months
  num_txn_12m         INT     — number of transactions in last 12 months
  days_since_txn      INT     — days since last customer transaction
  days_since_login    INT     — days since last digital banking login
  low_balance_days    INT     — number of days balance was below minimum
  nps_score           INT     — Net Promoter Score (0-100). <=30 = Detractor
  complaint_count     INT     — number of complaints raised
  digital_banking_active INT  — 1 if enrolled in digital banking
  last_branch_visit_days INT  — days since last branch visit
  salary_diverted     INT     — 1 if salary no longer credited here (Savings/Current only)
  account_closed      INT     — 1 if account was explicitly closed
  customer_status     TEXT    — Active / Inactive / Churned
                                Active   = transacted within 180 days
                                Inactive = no transaction for 180-365 days
                                Churned  = account closed or 365+ days inactive
  risk_level          TEXT    — High / Medium / Low / Safe / Churned
                                High   = 3+ signals or salary diverted alone
                                Medium = 2 signals
                                Low    = 1 signal
                                Safe   = 0 signals
  risk_signal_count   INT     — total number of risk signals (0-7)
  sig_salary_diverted INT     — signal: salary diverted (1=yes)
  sig_txn_inactive    INT     — signal: no transaction in 90+ days
  sig_low_balance     INT     — signal: low balance for 30+ days
  sig_complaints      INT     — signal: 2+ complaints
  sig_digital_inactive INT    — signal: no digital login in 60+ days
  sig_fd_maturing     INT     — signal: FD/RD maturing within 30 days
  sig_low_nps         INT     — signal: NPS score <= 30
  exit_week           INT     — week number (1-52) when churned; 0 if not churned
  exit_type           TEXT    — Account Closure / Extended Inactivity / Salary Diversion /
                                Balance Dormancy / Transaction Inactivity / None
  attrition_flag      INT     — 1 if churned, 0 if active/inactive
"""

_SYSTEM_PROMPT = f"""You are a SQL expert for a banking deposits attrition dashboard.
Convert the user's question into a valid DuckDB SQL SELECT query against the customers table.

{_SCHEMA}

Rules:
- Only generate SELECT statements. Never use INSERT, UPDATE, DELETE, DROP, CREATE.
- Use DuckDB SQL syntax.
- Always LIMIT results to 200 rows unless the user asks for aggregation.
- For monetary values, use ROUND(..., 0) to keep it clean.
- For percentages, multiply by 100 and round to 1 decimal place.
- Return ONLY the SQL query — no explanation, no markdown, no code fences.
"""

EXAMPLE_QUESTIONS = [
    "Show me all High risk customers in Muscat Main branch",
    "Which branch has the most at-risk customers?",
    "What is the average balance of HNI customers by risk level?",
    "List churned customers who had a loan",
    "How many customers are inactive per segment?",
    "What are the top 10 customers by loan outstanding who are High risk?",
    "Show attrition rate by account type",
    "Which customers have more than 3 complaints and are still active?",
]


def _call_groq(question: str) -> str:
    """Call Groq API to convert English question to SQL."""
    try:
        from groq import Groq
    except ImportError:
        st.error("groq package not installed. Run: pip install groq")
        st.stop()

    api_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
    if not api_key:
        st.error("Groq API key not found. Add GROQ_API_KEY to .streamlit/secrets.toml")
        st.stop()

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": question},
        ],
        temperature=0,
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()


def _safe_sql(sql: str) -> str:
    """Strip markdown fences and block non-SELECT statements."""
    sql = sql.replace("```sql", "").replace("```", "").strip()
    first_word = sql.split()[0].upper() if sql.split() else ""
    if first_word != "SELECT":
        raise ValueError(f"Only SELECT queries are allowed. Got: {first_word}")
    return sql


def show():
    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

    st.markdown("""
    <div style='background:#1565C0;border-radius:10px;padding:1rem 1.4rem;margin-bottom:1rem;'>
        <h4 style='color:white;margin:0;'>🧠 Ask the Data</h4>
        <p style='color:#BBDEFB;margin:4px 0 0 0;font-size:13px;'>
            Type a question in plain English — it will be converted to SQL and run against the database.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Example questions ──────────────────────────────────────────────
    st.markdown("**💡 Try one of these:**")
    cols = st.columns(4)
    for i, ex in enumerate(EXAMPLE_QUESTIONS):
        if cols[i % 4].button(ex, key=f"ex_{i}", use_container_width=True):
            st.session_state["nl_question"] = ex
            st.rerun()

    st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)

    # ── Question input ─────────────────────────────────────────────────
    question = st.text_area(
        "Your question",
        value=st.session_state.get("nl_question", ""),
        placeholder="e.g. Show me all High risk customers in Salalah branch with loan outstanding above 10000",
        height=80,
        key="nl_input",
        label_visibility="collapsed",
    )

    col_run, col_clr, _ = st.columns([1, 1, 6])
    run  = col_run.button("▶ Run", type="primary", use_container_width=True)
    clear = col_clr.button("✖ Clear", use_container_width=True)

    if clear:
        st.session_state["nl_question"] = ""
        st.session_state.pop("nl_sql", None)
        st.session_state.pop("nl_result", None)
        st.session_state.pop("nl_error", None)
        st.rerun()

    if run and question.strip():
        with st.spinner("Generating SQL..."):
            try:
                raw_sql = _call_groq(question.strip())
                sql     = _safe_sql(raw_sql)
                df      = db_query(sql)
                st.session_state["nl_sql"]      = sql
                st.session_state["nl_result"]   = df
                st.session_state["nl_error"]    = None
                st.session_state["nl_question"] = question.strip()
            except ValueError as e:
                st.session_state["nl_error"] = f"⛔ {e}"
            except Exception as e:
                st.session_state["nl_error"] = f"❌ {e}"

    # ── Results ────────────────────────────────────────────────────────
    if st.session_state.get("nl_error"):
        st.error(st.session_state["nl_error"])

    if st.session_state.get("nl_sql"):
        with st.expander("📄 Generated SQL", expanded=False):
            st.code(st.session_state["nl_sql"], language="sql")

    if st.session_state.get("nl_result") is not None:
        df = st.session_state["nl_result"]
        st.caption(f"{len(df):,} rows returned")
        st.dataframe(df, use_container_width=True,
                     height=min(36*len(df)+38, 500),
                     hide_index=True)

        # Download button
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, "query_result.csv", "text/csv")
