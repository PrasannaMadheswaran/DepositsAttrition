# ============================================================
#  Deposits Attrition Data App  —  Database Helper
#  Connects to Supabase PostgreSQL
# ============================================================

import os
import toml
import pandas as pd
import psycopg2
import streamlit as st

# ── Load secrets (local) or env var (Streamlit Cloud) ────────
try:
    secrets = toml.load(os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml"))
    DB_URL  = secrets["supabase"]["url"]
except Exception:
    DB_URL  = st.secrets["supabase"]["url"]


@st.cache_resource
def get_connection():
    return psycopg2.connect(DB_URL, sslmode="require", connect_timeout=10)


def query(sql: str) -> pd.DataFrame:
    try:
        con = get_connection()
        return pd.read_sql(sql, con)
    except Exception:
        # Reconnect if connection dropped
        get_connection.clear()
        con = get_connection()
        return pd.read_sql(sql, con)
