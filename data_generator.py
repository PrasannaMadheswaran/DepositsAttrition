# ============================================================
#  Deposits Attrition Data App  —  Data Generator
#  Generates 5,000 synthetic customers and stores them in:
#    • data/customers.csv       (for GitHub / backup)
#    • Supabase PostgreSQL      (persistent cloud database)
#
#  Run once with:  python data_generator.py
# ============================================================

import os
import toml
import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

SEED = 42
N    = 5000
np.random.seed(SEED)

CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "customers.csv")
secrets  = toml.load(os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml"))
DB_URL   = secrets["supabase"]["url"]


# ── Generate data ────────────────────────────────────────────
def generate_customers(n):
    segments     = np.random.choice(["Retail", "SME", "HNI"], n, p=[0.65, 0.25, 0.10])
    genders      = np.random.choice(["Male", "Female"],        n, p=[0.55, 0.45])
    age          = np.random.randint(22, 72, n)
    tenure       = np.random.randint(1, 25, n)
    account_type = np.random.choice(["Savings","Current","FD","RD"], n, p=[0.45,0.25,0.20,0.10])
    num_accounts = np.random.randint(1, 5, n)
    primary_flag = np.ones(n, dtype=int)

    balance = np.where(
        segments == "HNI",  np.random.uniform(300_000, 2_000_000, n),
        np.where(segments == "SME", np.random.uniform(50_000, 500_000, n),
                 np.random.uniform(5_000, 100_000, n))
    ).round(2)

    avg_monthly_credits = (balance * np.random.uniform(0.04, 0.20, n)).round(2)
    avg_monthly_debits  = (avg_monthly_credits * np.random.uniform(0.40, 0.95, n)).round(2)
    num_txn_3m          = np.random.randint(2, 40, n)
    num_txn_6m          = num_txn_3m + np.random.randint(2, 30, n)
    num_txn_12m         = num_txn_6m + np.random.randint(5, 50, n)

    has_loan        = np.random.choice([0,1], n, p=[0.55,0.45])
    has_investment  = np.random.choice([0,1], n, p=[0.60,0.40])
    has_credit_card = np.random.choice([0,1], n, p=[0.50,0.50])
    num_products    = 1 + has_loan + has_investment + has_credit_card

    nps_score              = np.random.randint(-10, 101, n)
    digital_banking_active = np.random.choice([0,1], n, p=[0.25,0.75])
    last_branch_visit_days = np.random.randint(1, 730, n)
    complaint_count        = np.random.choice([0,1,2,3,4,5], n, p=[0.50,0.25,0.12,0.07,0.04,0.02])

    logit = (
          1.8 * complaint_count - 0.06 * nps_score
        - 0.6 * (tenure / 25)  - 0.5  * (balance / balance.max())
        - 0.5 * num_products   + 0.7  * (1 - digital_banking_active)
        + 0.3 * (last_branch_visit_days / 730) + np.random.normal(0, 1, n)
    )
    prob      = 1 / (1 + np.exp(-logit))
    attrition = (np.random.rand(n) < prob).astype(int)
    attrition_type = np.where(attrition == 1,
        np.random.choice(["Full Withdrawal","Account Closure","Partial Withdrawal"],
                         n, p=[0.40,0.35,0.25]), "None")

    return pd.DataFrame({
        "customer_id": [f"CUST{str(i+1001).zfill(5)}" for i in range(n)],
        "age": age, "gender": genders, "tenure_years": tenure,
        "segment": segments, "account_type": account_type,
        "balance": balance, "num_accounts": num_accounts,
        "primary_account_flag": primary_flag,
        "avg_monthly_credits": avg_monthly_credits,
        "avg_monthly_debits": avg_monthly_debits,
        "num_txn_3m": num_txn_3m, "num_txn_6m": num_txn_6m, "num_txn_12m": num_txn_12m,
        "num_products": num_products, "has_loan": has_loan,
        "has_investment": has_investment, "has_credit_card": has_credit_card,
        "nps_score": nps_score, "digital_banking_active": digital_banking_active,
        "last_branch_visit_days": last_branch_visit_days,
        "complaint_count": complaint_count,
        "attrition_flag": attrition, "attrition_type": attrition_type,
    })


# ── Push to Supabase ─────────────────────────────────────────
def push_to_supabase(df):
    con = psycopg2.connect(DB_URL)
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS customers")
    cur.execute("""
        CREATE TABLE customers (
            customer_id TEXT, age INTEGER, gender TEXT, tenure_years INTEGER,
            segment TEXT, account_type TEXT, balance FLOAT, num_accounts INTEGER,
            primary_account_flag INTEGER, avg_monthly_credits FLOAT,
            avg_monthly_debits FLOAT, num_txn_3m INTEGER, num_txn_6m INTEGER,
            num_txn_12m INTEGER, num_products INTEGER, has_loan INTEGER,
            has_investment INTEGER, has_credit_card INTEGER, nps_score INTEGER,
            digital_banking_active INTEGER, last_branch_visit_days INTEGER,
            complaint_count INTEGER, attrition_flag INTEGER, attrition_type TEXT
        )
    """)
    cols   = df.columns.tolist()
    values = [tuple(row) for row in df.itertuples(index=False)]
    execute_values(cur, f"INSERT INTO customers ({','.join(cols)}) VALUES %s", values)
    con.commit()
    cur.execute("SELECT COUNT(*) FROM customers")
    print(f"  ✅ {cur.fetchone()[0]:,} rows pushed to Supabase!")
    con.close()


# ── Main ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🏦  Deposits Attrition — Data Generator")
    print("=" * 45)
    print(f"  Generating {N:,} synthetic customers ...")
    df = generate_customers(N)
    print(f"  ✅ DataFrame shape: {df.shape}")

    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    df.to_csv(CSV_PATH, index=False)
    print(f"  ✅ CSV saved: data/customers.csv")

    print("  Pushing to Supabase ...")
    push_to_supabase(df)

    print("\n🎉 Done! Data is ready in Supabase and CSV.\n")
