import os
import pandas as pd
import duckdb
import streamlit as st

DB_PATH  = os.path.join(os.path.dirname(__file__), "data", "deposits.db")
CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "customers.csv")

@st.cache_resource
def get_connection():
    if os.path.exists(DB_PATH):
        return duckdb.connect(DB_PATH, read_only=True)
    con = duckdb.connect(":memory:")
    df  = pd.read_csv(CSV_PATH)
    con.execute("CREATE TABLE customers AS SELECT * FROM df")
    return con

def query(sql: str) -> pd.DataFrame:
    return get_connection().execute(sql).df()
