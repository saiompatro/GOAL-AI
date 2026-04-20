"""GOAL AI — Streamlit entry point.

Run with:
    streamlit run app.py
"""
import streamlit as st

st.set_page_config(
    page_title="GOAL AI",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

pg = st.navigation([
    st.Page("pages/1_Dashboard.py",  title="Dashboard",  icon="🏠"),
    st.Page("pages/2_Predict.py",    title="Predict",    icon="⚽"),
    st.Page("pages/3_Teams.py",      title="Teams",      icon="🏳"),
    st.Page("pages/4_Players.py",    title="Players",    icon="👤"),
    st.Page("pages/5_Model.py",      title="Model",      icon="🤖"),
])
pg.run()
