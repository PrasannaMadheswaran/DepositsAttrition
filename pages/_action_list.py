import sys, os
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
import pandas as pd
from database import query

RISK_BADGE = {
    "High"  : "🔴 High",
    "Medium": "🟠 Medium",
    "Low"   : "🟡 Low",
    "Safe"  : "🟢 Safe",
}

SIGNAL_LABELS = {
    "sig_salary_diverted" : "💸 Salary Diverted",
    "sig_txn_inactive"    : "💤 Txn Inactive",
    "sig_low_balance"     : "📉 Low Balance",
    "sig_complaints"      : "⚠️ Complaints",
    "sig_digital_inactive": "📵 Digital Inactive",
    "sig_fd_maturing"     : "📅 FD Maturing",
    "sig_low_nps"         : "😞 Low NPS",
}

RECOMMENDED_ACTION = {
    "sig_salary_diverted" : "Call customer — offer salary account benefit / loyalty reward",
    "sig_txn_inactive"    : "Send reactivation offer — cashback or fee waiver",
    "sig_low_balance"     : "RM visit — explore financial difficulties or competitor offer",
    "sig_complaints"      : "Escalate to branch manager — resolve complaint within 48hrs",
    "sig_digital_inactive": "Offer digital onboarding session — simplify app usage",
    "sig_fd_maturing"     : "Proactive FD renewal call — offer preferred rate",
    "sig_low_nps"         : "Service recovery call — understand dissatisfaction root cause",
}


@st.cache_data
def load_branches():
    return ["All"] + query(
        "SELECT DISTINCT branch FROM customers ORDER BY branch"
    )["branch"].tolist()


@st.cache_data
def load_action_list(branch, risk_levels, segment, account_type):
    conditions = ["customer_status IN ('Active','Inactive')"]
    if branch     != "All": conditions.append(f"branch = '{branch}'")
    if segment    != "All": conditions.append(f"segment = '{segment}'")
    if account_type != "All": conditions.append(f"account_type = '{account_type}'")
    if risk_levels:
        lvls = "','".join(risk_levels)
        conditions.append(f"risk_level IN ('{lvls}')")

    where = "WHERE " + " AND ".join(conditions)
    return query(f"""
        SELECT customer_id, branch, segment, account_type,
               customer_status, risk_level, risk_signal_count,
               ROUND(balance,0) AS balance,
               tenure_years, days_since_txn, nps_score, complaint_count,
               sig_salary_diverted, sig_txn_inactive, sig_low_balance,
               sig_complaints, sig_digital_inactive, sig_fd_maturing, sig_low_nps
        FROM customers {where}
        ORDER BY
            CASE risk_level WHEN 'High' THEN 1 WHEN 'Medium' THEN 2
                            WHEN 'Low' THEN 3 ELSE 4 END,
            balance DESC
        LIMIT 500
    """)


def _signals_text(row):
    return ", ".join(
        lbl for col, lbl in SIGNAL_LABELS.items() if row.get(col, 0) == 1
    ) or "—"


def _top_action(row):
    # Pick the highest-priority triggered signal's action
    priority = ["sig_salary_diverted", "sig_fd_maturing", "sig_complaints",
                "sig_low_balance", "sig_txn_inactive", "sig_digital_inactive", "sig_low_nps"]
    for sig in priority:
        if row.get(sig, 0) == 1:
            return RECOMMENDED_ACTION[sig]
    return "Monitor — no urgent action"


def show():
    st.markdown("<div style='margin-bottom:6px'></div>", unsafe_allow_html=True)

    # ── Filter bar ─────────────────────────────────────────────────────
    f1, f2, f3, f4, f5 = st.columns([2, 2, 2, 2, 1])
    with f1:
        branch = st.selectbox("Branch", load_branches(), key="al_branch")
    with f2:
        risk_levels = st.multiselect("Risk Level", ["High", "Medium", "Low", "Safe"],
                                     default=["High", "Medium"], key="al_risk")
    with f3:
        segment = st.selectbox("Segment", ["All", "HNI", "SME", "Retail"], key="al_seg")
    with f4:
        account_type = st.selectbox("Account Type",
                                    ["All", "Savings", "Current", "FD", "RD"],
                                    key="al_acc")
    with f5:
        st.markdown("<div style='margin-top:26px'></div>", unsafe_allow_html=True)
        export = st.button("⬇️ Export", key="al_export")

    st.divider()

    df_raw = load_action_list(branch, risk_levels, segment, account_type)

    if df_raw.empty:
        st.info("No customers match the selected filters.")
        return

    # ── Summary strip ───────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Customers Listed",  f"{len(df_raw):,}")
    k2.metric("High Risk",         f"{(df_raw.risk_level=='High').sum():,}")
    k3.metric("Medium Risk",       f"{(df_raw.risk_level=='Medium').sum():,}")
    k4.metric("Deposits Exposed",  f"OMR {df_raw[df_raw.risk_level.isin(['High','Medium'])]['balance'].sum():,.0f}")

    st.markdown("<div style='margin-top:6px'></div>", unsafe_allow_html=True)

    # ── Build display table ─────────────────────────────────────────────
    sig_cols = list(SIGNAL_LABELS.keys())
    display  = pd.DataFrame({
        "Customer ID"   : df_raw["customer_id"],
        "Branch"        : df_raw["branch"],
        "Segment"       : df_raw["segment"],
        "Account"       : df_raw["account_type"],
        "Status"        : df_raw["customer_status"],
        "Risk"          : df_raw["risk_level"].map(RISK_BADGE),
        "Balance (OMR)" : df_raw["balance"].apply(lambda x: f"{int(x):,}"),
        "Days Since Txn": df_raw["days_since_txn"],
        "Signals"       : df_raw.apply(lambda r: _signals_text(r[sig_cols].to_dict()), axis=1),
        "Recommended Action": df_raw.apply(lambda r: _top_action(r[sig_cols].to_dict()), axis=1),
    })

    st.dataframe(
        display,
        use_container_width=True,
        height=min(36 * len(display) + 38, 520),
        hide_index=True,
        column_config={
            "Risk"              : st.column_config.TextColumn("Risk", width="small"),
            "Balance (OMR)"     : st.column_config.TextColumn("Balance (OMR)", width="medium"),
            "Signals"           : st.column_config.TextColumn("Active Signals", width="large"),
            "Recommended Action": st.column_config.TextColumn("Recommended Action", width="large"),
        }
    )
    st.caption(f"{len(display)} customers listed (max 500) · sorted by risk level then balance")

    # ── Export ──────────────────────────────────────────────────────────
    if export:
        csv = display.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"action_list_{branch.replace(' ','_')}.csv",
            mime="text/csv",
            key="al_download"
        )
