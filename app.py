"""GOAL AI - Streamlit entry point.

Run with:
    streamlit run app.py
"""
import streamlit as st

st.set_page_config(
    page_title="GOAL AI",
    page_icon="GOAL",
    layout="wide",
    initial_sidebar_state="expanded",
)

pg = st.navigation([
    st.Page("pages/1_Dashboard.py", title="Dashboard", icon=":material/home:"),
    st.Page("pages/2_Predict.py", title="Predict", icon=":material/sports_soccer:"),
    st.Page("pages/3_Teams.py", title="Teams", icon=":material/flag:"),
    st.Page("pages/4_Players.py", title="Players", icon=":material/person:"),
    st.Page("pages/5_Model.py", title="Model", icon=":material/model_training:"),
    st.Page("pages/6_Bracket.py", title="Bracket", icon=":material/emoji_events:"),
    st.Page("pages/7_Simulator.py", title="Simulator", icon=":material/tune:"),
])
pg.run()
