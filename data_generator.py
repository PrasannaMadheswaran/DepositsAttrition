"""
data_generator.py
─────────────────
Generates a CUSTOMER-LEVEL synthetic dataset for the Deposits Attrition dashboard.

Each row = one unique customer.
  • account_type   = primary/dominant account type held by the customer
  • balance        = total deposit balance across all accounts (OMR)
  • num_products   = count of distinct product relationships (deposit + loan + investment + CC)

Attrition definition (customer-level, NOT account-level):
  A customer is "attritioned" when they materially sever the banking relationship:
    PRIMARY triggers (sufficient alone):
      (a) account_closed  — customer explicitly closed their primary deposit account and
                            did NOT open a replacement (≠ FD/RD maturity/auto-renewal)
      (b) salary_diverted — salary credits stopped flowing into this bank
                            (applicable ONLY for Savings / Current accounts)
    SECONDARY signals (need 2+ combined, or 1 + score threshold):
      - balance_dormant   — avg balance < minimum for 30+ days
      - txn_inactive      — no transaction in 90+ days
      - has_complaints    — 2+ unresolved complaints
      - digitally_disengaged — not logged in for 60+ days AND not digital-active

FD / RD maturity logic:
  - FD/RD maturity is treated as attrition ONLY when ALL of:
      (1) customer's primary account is FD or RD
      (2) customer holds only 1 product (single-account)
      (3) customer did NOT renew (random probability based on tenure / NPS)
  - Auto-renewed FDs, or customers who opened a new account = NOT attritioned

Target attrition rate: 15–22%
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
    age    = np.where(seg == "HNI",
                 rng.integers(35, 70, n),
             np.where(seg == "SME",
                 rng.integers(28, 65, n),
                 rng.integers(22, 60, n)))
    gender = rng.choice(["Male", "Female"], n, p=[0.55, 0.45])

    # ── Tenure (years with the bank) ─────────────────────────────────────────
    # HNI customers tend to have longer tenures
    tenure = np.where(seg == "HNI",
                 rng.integers(3, 25, n),
             np.where(seg == "SME",
                 rng.integers(2, 20, n),
                 rng.integers(1, 18, n)))

    # ── Primary account type ──────────────────────────────────────────────────
    # HNI: more FDs; SME: mostly Current; Retail: mostly Savings
    account_type = np.where(
        seg == "HNI",
        rng.choice(["Savings", "Current", "FD", "RD"], n, p=[0.20, 0.25, 0.40, 0.15]),
    np.where(
        seg == "SME",
        rng.choice(["Savings", "Current", "FD", "RD"], n, p=[0.15, 0.55, 0.22, 0.08]),
        rng.choice(["Savings", "Current", "FD", "RD"], n, p=[0.55, 0.20, 0.17, 0.08]),
    ))

    # ── Balance (total across all accounts, OMR) ──────────────────────────────
    bal = np.where(seg == "HNI",
              rng.uniform(30_000, 300_000, n),
          np.where(seg == "SME",
              rng.uniform(5_000,  100_000, n),
              rng.uniform(200,     15_000, n))).round(2)

    # ── Products held ─────────────────────────────────────────────────────────
    has_loan = rng.choice([0, 1], n, p=[0.55, 0.45])
    has_inv  = rng.choice([0, 1], n, p=[0.60, 0.40])
    has_cc   = rng.choice([0, 1], n, p=[0.50, 0.50])
    num_products = 1 + has_loan + has_inv + has_cc   # min 1 (deposit itself)

    # ── Transactional features ────────────────────────────────────────────────
    # Realistic days_since_txn: most customers active (1–90d), minority inactive
    is_inactive_txn = rng.random(n) < np.where(seg == "HNI", 0.06,
                                               np.where(seg == "SME", 0.09, 0.15))
    days_since_txn  = np.where(is_inactive_txn,
                          rng.integers(91, 730, n),
                          rng.integers(1,   90, n))

    num_txn_3m  = rng.integers(0, 35, n)
    num_txn_6m  = num_txn_3m  + rng.integers(0, 25, n)
    num_txn_12m = num_txn_6m  + rng.integers(2, 45, n)

    avg_monthly_credits = (bal * rng.uniform(0.04, 0.20, n)).round(2)
    avg_monthly_debits  = (avg_monthly_credits * rng.uniform(0.40, 0.95, n)).round(2)

    # ── NPS score (0–100) ─────────────────────────────────────────────────────
    # Skewed slightly positive; HNI customers tend to give higher scores
    nps_base = np.where(seg == "HNI", 65, np.where(seg == "SME", 55, 50))
    nps_score = np.clip(
        (nps_base + rng.normal(0, 22, n)).astype(int), 0, 100
    )

    # ── Complaint count ───────────────────────────────────────────────────────
    complaint_count = rng.choice([0, 1, 2, 3, 4, 5], n,
                                  p=[0.55, 0.23, 0.11, 0.06, 0.03, 0.02])

    # ── Digital engagement ────────────────────────────────────────────────────
    digital_banking_active = rng.choice([0, 1], n, p=[0.22, 0.78])
    days_since_login = np.where(digital_banking_active == 0,
                           rng.integers(60, 730, n),
                           rng.integers(1,   60, n))

    # ── Balance dormancy ──────────────────────────────────────────────────────
    # Low-balance days correlated with segment
    dormancy_prob = np.where(seg == "HNI", 0.03,
                   np.where(seg == "SME", 0.06, 0.14))
    is_low_balance = rng.random(n) < dormancy_prob
    low_balance_days = np.where(is_low_balance,
                           rng.integers(31, 365, n),
                           rng.integers(0,   30, n))

    # ── Branch ────────────────────────────────────────────────────────────────
    branch = rng.choice(BRANCHES, n,
                p=[0.20, 0.15, 0.12, 0.10, 0.09, 0.08, 0.07, 0.07, 0.06, 0.06])

    # ── Salary diversion (Savings / Current only) ─────────────────────────────
    is_txn_account = np.isin(account_type, ["Savings", "Current"])
    _sal_raw        = rng.choice([0, 1], n, p=[0.88, 0.12])
    salary_diverted = np.where(is_txn_account, _sal_raw, 0)

    # ── Explicit account closure (excludes FD/RD maturity) ───────────────────
    # Base 7% probability; higher for low-NPS and high-complaint customers
    closure_prob = (
        0.04
        + np.where(nps_score < 30, 0.05, 0.0)
        + np.where(complaint_count >= 2, 0.04, 0.0)
        + np.where(tenure <= 2, 0.02, 0.0)
    )
    account_closed = (rng.random(n) < closure_prob).astype(int)

    # ── FD/RD non-renewal (only for single-product FD/RD customers) ──────────
    is_fd_rd         = np.isin(account_type, ["FD", "RD"])
    is_single_product = (num_products == 1)
    # Non-renewal probability decreases with tenure and NPS
    non_renewal_base = 0.20
    non_renewal_prob = non_renewal_base - (tenure / 100) - (nps_score / 1000)
    non_renewal_prob = np.clip(non_renewal_prob, 0.05, 0.35)
    fd_rd_non_renewal = (
        is_fd_rd & is_single_product & (rng.random(n) < non_renewal_prob)
    ).astype(int)

    # Merge: account_closed includes FD/RD non-renewal
    account_closed = np.clip(account_closed + fd_rd_non_renewal, 0, 1)

    # ── Derived binary signals ────────────────────────────────────────────────
    balance_dormant      = (low_balance_days  >= 30).astype(int)
    txn_inactive         = (days_since_txn    >= 90).astype(int)
    has_complaints       = (complaint_count   >= 2).astype(int)
    digitally_disengaged = (days_since_login  >= 60).astype(int)

    # ── Attrition scoring ─────────────────────────────────────────────────────
    # Primary triggers alone are sufficient
    primary = (account_closed == 1) | (salary_diverted == 1)

    # Secondary signals — need 2+ or score
    secondary_score = (
        balance_dormant
        + txn_inactive
        + has_complaints
        + digitally_disengaged
    )
    secondary = secondary_score >= 3

    attrition = (primary | secondary).astype(int)

    # ── Attrition type (most severe primary trigger first) ───────────────────
    attrition_type = np.where(attrition == 0, "None",
        np.where(account_closed  == 1, "Account Closure",
        np.where(salary_diverted == 1, "Salary Diversion",
        np.where(balance_dormant == 1, "Balance Dormancy",
        np.where(txn_inactive    == 1, "Transaction Inactivity",
                                        "Digital Disengagement")))))

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
        "primary_account_flag"   : np.ones(n, dtype=int),
        "avg_monthly_credits"    : avg_monthly_credits,
        "avg_monthly_debits"     : avg_monthly_debits,
        "num_txn_3m"             : num_txn_3m,
        "num_txn_6m"             : num_txn_6m,
        "num_txn_12m"            : num_txn_12m,
        "num_products"           : num_products,
        "has_loan"               : has_loan,
        "has_investment"         : has_inv,
        "has_credit_card"        : has_cc,
        "nps_score"              : nps_score,
        "digital_banking_active" : digital_banking_active,
        "last_branch_visit_days" : rng.integers(1, 730, n),
        "complaint_count"        : complaint_count,
        "days_since_txn"         : days_since_txn,
        "days_since_login"       : days_since_login,
        "low_balance_days"       : low_balance_days,
        "salary_diverted"        : salary_diverted,
        "account_closed"         : account_closed,
        "attrition_flag"         : attrition,
        "attrition_type"         : attrition_type,
    })
    return df


if __name__ == "__main__":
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    df = generate(N)

    # Save to DuckDB
    con = duckdb.connect(DB_PATH)
    con.execute("DROP TABLE IF EXISTS customers")
    con.execute("CREATE TABLE customers AS SELECT * FROM df")
    con.close()

    # Save to CSV (fallback for Streamlit Cloud)
    df.to_csv(CSV_PATH, index=False)

    churned = df["attrition_flag"].sum()
    print(f"✅  {N:,} customers generated  (customer-level, one row per customer)")
    print(f"📊  Attrition rate : {churned/N*100:.1f}%  ({churned:,} churned)")
    print(f"🏦  Branches       : {df['branch'].nunique()} branches")
    print(f"💰  Avg Balance    : OMR {df['balance'].mean():,.0f}")
    print(f"\n  Exit type breakdown:")
    print(df[df.attrition_flag == 1]["attrition_type"].value_counts().to_string())
    print(f"\n  Segment breakdown:")
    seg_stats = df.groupby("segment").agg(
        customers=("customer_id", "count"),
        attrition_rate=("attrition_flag", lambda x: f"{x.mean()*100:.1f}%")
    )
    print(seg_stats.to_string())
    print(f"\n  Account type breakdown:")
    at_stats = df.groupby("account_type").agg(
        customers=("customer_id", "count"),
        attrition_rate=("attrition_flag", lambda x: f"{x.mean()*100:.1f}%")
    )
    print(at_stats.to_string())
