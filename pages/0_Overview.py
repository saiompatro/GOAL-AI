"""GOAL AI league and competition project directory."""
import streamlit as st

st.title("GOAL AI")
st.markdown(
    "A project workspace for football intelligence. Choose a competition, then open the model or "
    "analysis project you want to explore."
)

world_cup, premier_league = st.columns(2, gap="large")
with world_cup:
    st.subheader("FIFA World Cup 2026")
    st.write("International player, team, head-to-head, venue, weather, and match prediction tools.")
    st.page_link("pages/1_Player_Analysis.py", label="Open World Cup projects", icon=":material/public:")

with premier_league:
    st.subheader("Premier League")
    st.write("Three hands-on machine-learning projects for valuation, results, and player recruitment.")
    st.page_link("pages/6_PL_Project_Hub.py", label="Open Premier League projects", icon=":material/trophy:")

st.divider()
st.caption("Each competition has its own project group in the sidebar, so models and data stay in context.")
