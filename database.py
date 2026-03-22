import os
import pandas as pd
import duckdb
import streamlit as st

DB_PATH  = os.path.join(os.path.dirname(__file__), "data", "deposits.db")
CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "customers.csv")

@st.cache_resource
def get_connection():
    try:
        if os.path.exists(DB_PATH):
            return duckdb.connect(DB_PATH, read_only=True)
        if not os.path.exists(CSV_PATH):
            st.error(f"Data file not found: {CSV_PATH}\nExpected at: {os.path.abspath(CSV_PATH)}")
            st.stop()
        con = duckdb.connect(":memory:")
        df  = pd.read_csv(CSV_PATH)
        con.execute("CREATE TABLE customers AS SELECT * FROM df")
        return con
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        st.stop()

def query(sql: str) -> pd.DataFrame:
    return get_connection().execute(sql).df()
