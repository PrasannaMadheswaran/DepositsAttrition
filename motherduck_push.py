# ============================================================
#  MotherDuck Push Script
#  Uploads local deposits.db to MotherDuck cloud
#  Run with:  python motherduck_push.py
# ============================================================

import os
import duckdb

# ── Step 1: Load token ───────────────────────────────────────
print("\n🦆 MotherDuck Push Script")
print("=" * 45)

# Try reading from .streamlit/secrets.toml first
token = None
secrets_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")

if os.path.exists(secrets_path):
    with open(secrets_path) as f:
        for line in f:
            if "token" in line and "=" in line:
                token = line.split("=")[1].strip().strip('"').strip("'")
                break

# Fallback to env var
if not token or token == "paste_your_motherduck_token_here":
    token = os.environ.get("MOTHERDUCK_TOKEN")

if not token:
    print("\n❌  No token found!")
    print("    Please paste your MotherDuck token into:")
    print("    .streamlit/secrets.toml  →  token = \"your_token_here\"")
    print("    OR set env var:  set MOTHERDUCK_TOKEN=your_token_here")
    exit(1)

print(f"  ✅  Token found: {token[:12]}...")

# ── Step 2: Check local DB ───────────────────────────────────
db_path = os.path.join(os.path.dirname(__file__), "data", "deposits.db")
if not os.path.exists(db_path):
    print(f"\n❌  Local database not found at: {db_path}")
    print("    Run  python data_generator.py  first!")
    exit(1)

local_con = duckdb.connect(db_path, read_only=True)
row_count  = local_con.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
print(f"  ✅  Local DB found: {row_count:,} customers")
local_con.close()

# ── Step 3: Connect to MotherDuck ───────────────────────────
print(f"\n  Connecting to MotherDuck ...")
try:
    md_con = duckdb.connect(f"md:?motherduck_token={token}")
    print("  ✅  Connected to MotherDuck!")
except Exception as e:
    print(f"\n❌  Connection failed: {e}")
    print("    Check your token is valid at: https://app.motherduck.com")
    exit(1)

# ── Step 4: Create database on MotherDuck ───────────────────
print(f"\n  Creating database 'deposits_attrition' on MotherDuck ...")
try:
    md_con.execute("CREATE DATABASE IF NOT EXISTS deposits_attrition")
    print("  ✅  Database created (or already exists)")
except Exception as e:
    print(f"❌  Failed to create database: {e}")
    exit(1)

# ── Step 5: Attach local DB and copy table ───────────────────
print(f"\n  Uploading customers table ...")
try:
    md_con.execute(f"ATTACH '{db_path}' AS local_db (READ_ONLY)")
    md_con.execute("USE deposits_attrition")
    md_con.execute("DROP TABLE IF EXISTS customers")
    md_con.execute("CREATE TABLE customers AS SELECT * FROM local_db.main.customers")
    count = md_con.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    print(f"  ✅  {count:,} customers uploaded to MotherDuck!")
except Exception as e:
    print(f"❌  Upload failed: {e}")
    exit(1)

# ── Step 6: Verify ───────────────────────────────────────────
print(f"\n  Verifying upload ...")
summary = md_con.execute("""
    SELECT segment,
           COUNT(*)                          AS customers,
           ROUND(AVG(attrition_flag)*100,1)  AS attrition_rate_pct
    FROM   customers
    GROUP  BY segment
    ORDER  BY customers DESC
""").df()
print(summary.to_string(index=False))

md_con.close()

print("\n🎉  Done! Your data is live on MotherDuck.")
print("    Database : deposits_attrition")
print("    Table    : customers")
print(f"    Rows     : {count:,}")
print("\n    ✅  You should now see it in your MotherDuck console at:")
print("    https://app.motherduck.com\n")
