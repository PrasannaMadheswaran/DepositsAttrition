# ============================================================
#  Deposits Attrition Data App  —  Database Helper
#  Connects to Supabase PostgreSQL
# ============================================================

import os
import toml
import pandas as pd
import psycopg2
import streamlit as st

secrets = toml.load(os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml"))
DB_URL  = secrets["supabase"]["url"]


@st.cache_resource
def get_connection():
    return psycopg2.connect(DB_URL)


def query(sql: str) -> pd.DataFrame:
    con = get_connection()
    return pd.read_sql(sql, con)
