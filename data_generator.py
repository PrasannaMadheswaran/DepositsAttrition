import os
import numpy as np
import pandas as pd
import duckdb

SEED, N  = 42, 5000
DB_PATH  = os.path.join(os.path.dirname(__file__), "data", "deposits.db")
CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "customers.csv")

# Omani branches
BRANCHES = ["Muscat Main", "Muscat North", "Muscat South",
            "Salalah", "Sohar", "Nizwa", "Sur", "Ibri", "Barka", "Rustaq"]

def generate(n):
    np.random.seed(SEED)

    seg  = np.random.choice(["Retail","SME","HNI"], n, p=[0.65,0.25,0.10])

    # ── Realistic OMR balances ───────────────────────────────
    # HNI : OMR 30,000 – 300,000
    # SME : OMR 5,000  – 100,000
    # Retail: OMR 200  – 15,000
    bal  = np.where(seg=="HNI", np.random.uniform(30_000, 300_000, n),
           np.where(seg=="SME", np.random.uniform(5_000,  100_000, n),
                                np.random.uniform(200,    15_000,  n))).round(2)

    ten  = np.random.randint(1, 25, n)
    nps  = np.random.randint(-10, 101, n)
    comp = np.random.choice([0,1,2,3,4,5], n, p=[0.50,0.25,0.12,0.07,0.04,0.02])
    dig  = np.random.choice([0,1], n, p=[0.25,0.75])
    lbv  = np.random.randint(1, 730, n)
    has_loan = np.random.choice([0,1],n,p=[0.55,0.45])
    has_inv  = np.random.choice([0,1],n,p=[0.60,0.40])
    has_cc   = np.random.choice([0,1],n,p=[0.50,0.50])
    txn3     = np.random.randint(2,40,n)
    txn6     = txn3 + np.random.randint(2,30,n)
    txn12    = txn6 + np.random.randint(5,50,n)
    credits  = (bal * np.random.uniform(0.04,0.20,n)).round(2)
    debits   = (credits * np.random.uniform(0.40,0.95,n)).round(2)

    # ── Branch assignment (weighted — Muscat branches busier) ─
    branch = np.random.choice(BRANCHES, n,
                p=[0.20,0.15,0.12,0.10,0.09,0.08,0.07,0.07,0.06,0.06])

    # ── Attrition indicators ──────────────────────────────────
    account_closed   = np.random.choice([0,1], n, p=[0.88,0.12])
    low_balance_days = np.where(bal < 300,
                           np.random.randint(0,365,n),
                           np.random.randint(0,30,n))
    balance_dormant  = (low_balance_days >= 90).astype(int)
    days_since_txn   = np.random.randint(1, 730, n)
    txn_inactive     = (days_since_txn >= 180).astype(int)
    salary_diverted  = np.random.choice([0,1], n, p=[0.85,0.15])
    days_since_login = np.where(dig==0,
                           np.random.randint(60,730,n),
                           np.random.randint(1,60,n))
    digitally_disengaged = (days_since_login >= 60).astype(int)

    attrition = np.where(
        (account_closed == 1) | (balance_dormant == 1) |
        (txn_inactive == 1)   | (salary_diverted == 1) |
        ((digitally_disengaged == 1) & (comp >= 2)), 1, 0)

    attrition_type = np.where(attrition==1,
        np.where(account_closed==1,  "Account Closure",
        np.where(salary_diverted==1, "Salary Diversion",
        np.where(balance_dormant==1, "Balance Dormancy",
        np.where(txn_inactive==1,    "Transaction Inactivity",
                                     "Digital Disengagement")))), "None")

    return pd.DataFrame({
        "customer_id"            : [f"CUST{str(i+1001).zfill(5)}" for i in range(n)],
        "age"                    : np.random.randint(22,72,n),
        "gender"                 : np.random.choice(["Male","Female"],n,p=[0.55,0.45]),
        "tenure_years"           : ten,
        "segment"                : seg,
        "branch"                 : branch,
        "account_type"           : np.random.choice(["Savings","Current","FD","RD"],n,p=[0.45,0.25,0.20,0.10]),
        "balance"                : bal,
        "num_accounts"           : np.random.randint(1,5,n),
        "primary_account_flag"   : np.ones(n,dtype=int),
        "avg_monthly_credits"    : credits,
        "avg_monthly_debits"     : debits,
        "num_txn_3m"             : txn3,
        "num_txn_6m"             : txn6,
        "num_txn_12m"            : txn12,
        "num_products"           : 1+has_loan+has_inv+has_cc,
        "has_loan"               : has_loan,
        "has_investment"         : has_inv,
        "has_credit_card"        : has_cc,
        "nps_score"              : nps,
        "digital_banking_active" : dig,
        "last_branch_visit_days" : lbv,
        "complaint_count"        : comp,
        "days_since_txn"         : days_since_txn,
        "days_since_login"       : days_since_login,
        "low_balance_days"       : low_balance_days,
        "salary_diverted"        : salary_diverted,
        "account_closed"         : account_closed,
        "attrition_flag"         : attrition,
        "attrition_type"         : attrition_type,
    })

if __name__ == "__main__":
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    df = generate(N)
    con = duckdb.connect(DB_PATH)
    con.execute("DROP TABLE IF EXISTS customers")
    con.execute("CREATE TABLE customers AS SELECT * FROM df")
    con.close()
    df.to_csv(CSV_PATH, index=False)
    churned = df['attrition_flag'].sum()
    print(f"✅ {N:,} customers generated")
    print(f"📊 Attrition rate : {churned/N*100:.1f}% ({churned:,} churned)")
    print(f"🏦 Branches       : {df['branch'].nunique()} branches")
    print(f"💰 Avg Balance    : OMR {df['balance'].mean():,.0f}")
    print(f"\n  Exit type breakdown:")
    print(df[df.attrition_flag==1]['attrition_type'].value_counts().to_string())
