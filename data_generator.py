"""
data_generator.py
─────────────────
Generates a CUSTOMER-LEVEL synthetic dataset for the Deposits Attrition dashboard.

Each row = one unique customer.

Customer Status:
  - Active   : last customer-initiated transaction within 180 days
  - Inactive : no customer-initiated transaction for 180–365 days (at risk of churning)
  - Churned  : account explicitly closed OR no transaction beyond 365 days
               → feeds the Churn Trends tab (historical analysis)

Risk Level (Active customers only):
  - High   : 3+ signals, or salary_diverted alone
  - Medium : 2 signals
  - Low    : 1 signal
  - Safe   : 0 signals

Risk Signals (Active + Inactive):
  sig_salary_diverted  — salary credits stopped (Savings/Current only)
  sig_txn_inactive     — no transaction in 90+ days
  sig_low_balance      — balance below minimum for 30+ days
  sig_complaints       — 2+ unresolved complaints
  sig_digital_inactive — no login in 60+ days
  sig_fd_maturing      — FD/RD maturing within 30 days
  sig_low_nps          — NPS score ≤ 30

exit_week (Churned only): week number 1–52 for trend analysis
"""

import os
import numpy as np
import pandas as pd
import duckdb

SEED = 42
N    = 5000

DB_PATH  = os.path.join(os.path.dirname(__file__), "data", "deposits.db")
CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "customers.csv")

BRANCHES = [
    "Muscat Main", "Muscat North", "Muscat South",
    "Salalah", "Sohar", "Nizwa", "Sur", "Ibri", "Barka", "Rustaq",
]


def generate(n=N):
    rng = np.random.default_rng(SEED)

    # ── Segment & demographics ────────────────────────────────────────────────
    seg    = rng.choice(["Retail", "SME", "HNI"], n, p=[0.65, 0.25, 0.10])
    age    = np.where(seg == "HNI", rng.integers(35, 70, n),
             np.where(seg == "SME", rng.integers(28, 65, n),
                                    rng.integers(22, 60, n)))
    gender = rng.choice(["Male", "Female"], n, p=[0.55, 0.45])
    tenure = np.where(seg == "HNI", rng.integers(3, 25, n),
             np.where(seg == "SME", rng.integers(2, 20, n),
                                    rng.integers(1, 18, n)))

    # ── Primary account type ──────────────────────────────────────────────────
    account_type = np.where(
        seg == "HNI",
        rng.choice(["Savings", "Current", "FD", "RD"], n, p=[0.20, 0.25, 0.40, 0.15]),
        np.where(seg == "SME",
        rng.choice(["Savings", "Current", "FD", "RD"], n, p=[0.15, 0.55, 0.22, 0.08]),
        rng.choice(["Savings", "Current", "FD", "RD"], n, p=[0.55, 0.20, 0.17, 0.08])))

    # ── Balance ───────────────────────────────────────────────────────────────
    bal = np.where(seg == "HNI", rng.uniform(30_000, 300_000, n),
          np.where(seg == "SME", rng.uniform(5_000,  100_000, n),
                                 rng.uniform(200,     15_000,  n))).round(2)

    # ── Products ──────────────────────────────────────────────────────────────
    has_loan = rng.choice([0, 1], n, p=[0.55, 0.45])
    has_inv  = rng.choice([0, 1], n, p=[0.60, 0.40])
    has_cc   = rng.choice([0, 1], n, p=[0.50, 0.50])
    num_products = 1 + has_loan + has_inv + has_cc

    # ── Loan outstanding (OMR) — 0 if no loan ────────────────────────────────
    # Correlated with segment: HNI carry larger loans
    loan_outstanding = np.where(
        has_loan == 0, 0,
        np.where(seg == "HNI", rng.uniform(20_000, 200_000, n),
        np.where(seg == "SME", rng.uniform(5_000,   80_000, n),
                               rng.uniform(1_000,   25_000, n)))
    ).round(2)

    # ── Transaction activity ──────────────────────────────────────────────────
    # days_since_txn covers full range: active → inactive → churned
    # Churned customers have 366–730 days; inactive 180–365; active 1–179
    status_draw = rng.random(n)
    is_churned_txn  = status_draw < 0.15                        # ~15% churned by inactivity
    is_inactive_txn = (status_draw >= 0.15) & (status_draw < 0.28)  # ~13% inactive
    # rest are active

    days_since_txn = np.where(is_churned_txn,
                         rng.integers(366, 730, n),
                     np.where(is_inactive_txn,
                         rng.integers(180, 365, n),
                         rng.integers(1,   179, n)))

    num_txn_3m  = rng.integers(0, 35, n)
    num_txn_6m  = num_txn_3m + rng.integers(0, 25, n)
    num_txn_12m = num_txn_6m + rng.integers(2, 45, n)

    avg_monthly_credits = (bal * rng.uniform(0.04, 0.20, n)).round(2)
    avg_monthly_debits  = (avg_monthly_credits * rng.uniform(0.40, 0.95, n)).round(2)

    # ── NPS (0–100) ───────────────────────────────────────────────────────────
    nps_base  = np.where(seg == "HNI", 65, np.where(seg == "SME", 55, 50))
    nps_score = np.clip((nps_base + rng.normal(0, 22, n)).astype(int), 0, 100)

    # ── Complaints ────────────────────────────────────────────────────────────
    complaint_count = rng.choice([0, 1, 2, 3, 4, 5], n,
                                  p=[0.55, 0.23, 0.11, 0.06, 0.03, 0.02])

    # ── Digital engagement ────────────────────────────────────────────────────
    digital_banking_active = rng.choice([0, 1], n, p=[0.22, 0.78])
    days_since_login = np.where(digital_banking_active == 0,
                           rng.integers(60, 730, n),
                           rng.integers(1,  60,  n))

    # ── Balance dormancy ──────────────────────────────────────────────────────
    dormancy_prob    = np.where(seg == "HNI", 0.03,
                       np.where(seg == "SME", 0.06, 0.14))
    is_low_balance   = rng.random(n) < dormancy_prob
    low_balance_days = np.where(is_low_balance,
                           rng.integers(31, 365, n),
                           rng.integers(0,  30,  n))

    # ── Branch ────────────────────────────────────────────────────────────────
    branch = rng.choice(BRANCHES, n,
                p=[0.20, 0.15, 0.12, 0.10, 0.09, 0.08, 0.07, 0.07, 0.06, 0.06])

    # ── Salary diversion (Savings/Current only) ───────────────────────────────
    is_txn_account  = np.isin(account_type, ["Savings", "Current"])
    salary_diverted = np.where(is_txn_account,
                          rng.choice([0, 1], n, p=[0.88, 0.12]), 0)

    # ── FD/RD maturing within 30 days ─────────────────────────────────────────
    is_fd_rd        = np.isin(account_type, ["FD", "RD"])
    fd_maturing     = (is_fd_rd & (rng.random(n) < 0.15)).astype(int)

    # ── Explicit account closure (for churned customers) ──────────────────────
    closure_prob = (0.04
        + np.where(nps_score < 30, 0.05, 0.0)
        + np.where(complaint_count >= 2, 0.04, 0.0)
        + np.where(tenure <= 2, 0.02, 0.0))
    account_closed = (rng.random(n) < closure_prob).astype(int)

    # FD/RD single-product non-renewal → also churned
    is_single_product = (num_products == 1)
    non_renewal_prob  = np.clip(0.20 - (tenure / 100) - (nps_score / 1000), 0.05, 0.35)
    fd_rd_non_renewal = (is_fd_rd & is_single_product & (rng.random(n) < non_renewal_prob)).astype(int)
    account_closed    = np.clip(account_closed + fd_rd_non_renewal, 0, 1)

    # ── Customer Status ───────────────────────────────────────────────────────
    # Churned: explicitly closed OR no transaction for 365+ days
    is_churned  = (account_closed == 1) | (days_since_txn >= 366)
    # Inactive: no transaction 180–365 days (and not churned)
    is_inactive = (~is_churned) & (days_since_txn >= 180)
    # Active: everyone else
    customer_status = np.where(is_churned, "Churned",
                      np.where(is_inactive, "Inactive", "Active"))

    # ── Risk signals (meaningful for Active + Inactive) ───────────────────────
    sig_salary_diverted  = salary_diverted
    sig_txn_inactive     = (days_since_txn    >= 90).astype(int)
    sig_low_balance      = (low_balance_days  >= 30).astype(int)
    sig_complaints       = (complaint_count   >= 2).astype(int)
    sig_digital_inactive = (days_since_login  >= 60).astype(int)
    sig_fd_maturing      = fd_maturing
    sig_low_nps          = (nps_score         <= 30).astype(int)

    risk_signal_count = (
        sig_salary_diverted
        + sig_txn_inactive
        + sig_low_balance
        + sig_complaints
        + sig_digital_inactive
        + sig_fd_maturing
        + sig_low_nps
    )

    # Risk level — only meaningful for Active/Inactive
    risk_level = np.where(is_churned, "Churned",
                 np.where((sig_salary_diverted == 1) | (risk_signal_count >= 3), "High",
                 np.where(risk_signal_count == 2, "Medium",
                 np.where(risk_signal_count == 1, "Low", "Safe"))))

    # ── Exit week (Churned customers — for weekly trend analysis) ─────────────
    # Simulate exits spread across last 52 weeks, more recent weeks heavier
    weights      = np.linspace(0.5, 1.5, 52)
    week_probs   = weights / weights.sum()
    exit_week_all = rng.choice(np.arange(1, 53), n, p=week_probs)
    exit_week     = np.where(is_churned, exit_week_all, 0)  # 0 = not churned

    # ── Exit type (Churned customers) ─────────────────────────────────────────
    exit_type = np.where(~is_churned, "None",
                np.where(account_closed  == 1,      "Account Closure",
                np.where(salary_diverted == 1,      "Salary Diversion",
                np.where(days_since_txn  >= 366,    "Extended Inactivity",
                np.where(sig_low_balance == 1,      "Balance Dormancy",
                                                    "Transaction Inactivity")))))

    # ── Assemble DataFrame ────────────────────────────────────────────────────
    df = pd.DataFrame({
        "customer_id"            : [f"CUST{str(i+1001).zfill(5)}" for i in range(n)],
        "age"                    : age,
        "gender"                 : gender,
        "tenure_years"           : tenure,
        "segment"                : seg,
        "branch"                 : branch,
        "account_type"           : account_type,
        "balance"                : bal,
        "num_accounts"           : rng.integers(1, 5, n),
        "num_products"           : num_products,
        "has_loan"               : has_loan,
        "loan_outstanding"       : loan_outstanding,
        "has_investment"         : has_inv,
        "has_credit_card"        : has_cc,
        "avg_monthly_credits"    : avg_monthly_credits,
        "avg_monthly_debits"     : avg_monthly_debits,
        "num_txn_3m"             : num_txn_3m,
        "num_txn_6m"             : num_txn_6m,
        "num_txn_12m"            : num_txn_12m,
        "days_since_txn"         : days_since_txn,
        "days_since_login"       : days_since_login,
        "low_balance_days"       : low_balance_days,
        "nps_score"              : nps_score,
        "complaint_count"        : complaint_count,
        "digital_banking_active" : digital_banking_active,
        "last_branch_visit_days" : rng.integers(1, 730, n),
        "salary_diverted"        : salary_diverted,
        "account_closed"         : account_closed,
        # ── Status & risk ──────────────────────────────────────────
        "customer_status"        : customer_status,
        "risk_level"             : risk_level,
        "risk_signal_count"      : risk_signal_count,
        "sig_salary_diverted"    : sig_salary_diverted,
        "sig_txn_inactive"       : sig_txn_inactive,
        "sig_low_balance"        : sig_low_balance,
        "sig_complaints"         : sig_complaints,
        "sig_digital_inactive"   : sig_digital_inactive,
        "sig_fd_maturing"        : sig_fd_maturing,
        "sig_low_nps"            : sig_low_nps,
        # ── Churn history ──────────────────────────────────────────
        "exit_week"              : exit_week,
        "exit_type"              : exit_type,
        "attrition_flag"         : is_churned.astype(int),
    })
    return df


if __name__ == "__main__":
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    df = generate(N)

    con = duckdb.connect(DB_PATH)
    con.execute("DROP TABLE IF EXISTS customers")
    con.execute("CREATE TABLE customers AS SELECT * FROM df")
    con.close()

    df.to_csv(CSV_PATH, index=False)

    total    = len(df)
    active   = (df.customer_status == "Active").sum()
    inactive = (df.customer_status == "Inactive").sum()
    churned  = (df.customer_status == "Churned").sum()

    print(f"✅  {total:,} customers generated")
    print(f"\n  Status breakdown:")
    print(f"    Active   : {active:,}  ({active/total*100:.1f}%)")
    print(f"    Inactive : {inactive:,}  ({inactive/total*100:.1f}%)")
    print(f"    Churned  : {churned:,}  ({churned/total*100:.1f}%)")

    act = df[df.customer_status != "Churned"]
    print(f"\n  Risk Level (Active + Inactive):")
    print(act["risk_level"].value_counts().to_string())

    print(f"\n  Exit type breakdown (Churned):")
    print(df[df.customer_status == "Churned"]["exit_type"].value_counts().to_string())

    print(f"\n  Signal frequency (Active + Inactive):")
    sigs = ["sig_salary_diverted","sig_txn_inactive","sig_low_balance",
            "sig_complaints","sig_digital_inactive","sig_fd_maturing","sig_low_nps"]
    for s in sigs:
        pct = act[s].mean() * 100
        print(f"    {s:25s}: {pct:.1f}%")
