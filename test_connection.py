# ============================================================
#  Quick connectivity test — Supabase PostgreSQL
# ============================================================

import toml, os
import psycopg2
import pandas as pd

secrets = toml.load(os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml"))
DB_URL  = secrets["supabase"]["url"]

print("🔌 Connecting to Supabase PostgreSQL ...")
con = psycopg2.connect(DB_URL)
cur = con.cursor()

cur.execute("SELECT version()")
print(f"✅ Connected! PostgreSQL version: {cur.fetchone()[0][:40]}")

cur.execute("SELECT COUNT(*) FROM customers")
print(f"📊 Customers in DB: {cur.fetchone()[0]:,}")

con.close()
print("\n🎉 Supabase connection is working!")
