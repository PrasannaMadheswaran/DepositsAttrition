# ============================================================
#  Supabase Push Script
#  Uploads customers data from CSV to Supabase PostgreSQL
#  Run once with:  python supabase_push.py
# ============================================================

import os
import toml
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# ── Load connection string ───────────────────────────────────
secrets  = toml.load(os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml"))
DB_URL   = secrets["supabase"]["url"]
CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "customers.csv")

print("\n🚀 Supabase Push Script")
print("=" * 45)

# ── Load CSV ─────────────────────────────────────────────────
print("📄 Loading customers.csv ...")
df = pd.read_csv(CSV_PATH)
print(f"  ✅ {len(df):,} rows loaded")

# ── Connect ──────────────────────────────────────────────────
print("🔌 Connecting to Supabase ...")
con = psycopg2.connect(DB_URL)
cur = con.cursor()
print("  ✅ Connected!")

# ── Create table ─────────────────────────────────────────────
print("📦 Creating customers table ...")
cur.execute("DROP TABLE IF EXISTS customers")
cur.execute("""
    CREATE TABLE customers (
        customer_id             TEXT,
        age                     INTEGER,
        gender                  TEXT,
        tenure_years            INTEGER,
        segment                 TEXT,
        account_type            TEXT,
        balance                 FLOAT,
        num_accounts            INTEGER,
        primary_account_flag    INTEGER,
        avg_monthly_credits     FLOAT,
        avg_monthly_debits      FLOAT,
        num_txn_3m              INTEGER,
        num_txn_6m              INTEGER,
        num_txn_12m             INTEGER,
        num_products            INTEGER,
        has_loan                INTEGER,
        has_investment          INTEGER,
        has_credit_card         INTEGER,
        nps_score               INTEGER,
        digital_banking_active  INTEGER,
        last_branch_visit_days  INTEGER,
        complaint_count         INTEGER,
        attrition_flag          INTEGER,
        attrition_type          TEXT
    )
""")
print("  ✅ Table created!")

# ── Insert data ───────────────────────────────────────────────
print("⬆️  Uploading 5,000 rows ...")
cols   = df.columns.tolist()
values = [tuple(row) for row in df.itertuples(index=False)]
execute_values(cur, f"INSERT INTO customers ({','.join(cols)}) VALUES %s", values)
con.commit()

# ── Verify ────────────────────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM customers")
count = cur.fetchone()[0]
print(f"  ✅ {count:,} rows in Supabase!")

cur.execute("""
    SELECT segment, COUNT(*) AS customers,
           ROUND(AVG(attrition_flag)*100, 1) AS attrition_rate
    FROM customers GROUP BY segment ORDER BY customers DESC
""")
print("\n  Segment Summary:")
for row in cur.fetchall():
    print(f"    {row[0]:<8} {row[1]:>5} customers  |  {row[2]}% attrition")

con.close()
print("\n🎉 Data is live on Supabase!\n")
