import streamlit as st
import pandas as pd
from database.db_manager import get_connection

def incident_history():

    st.header("Incident History")

    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM incidents ORDER BY id DESC", conn)
    conn.close()

    if df.empty:
        st.info("No incidents recorded.")
    else:
        st.dataframe(df)