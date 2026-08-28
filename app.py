"""GOAL AI - real football intelligence.

Run with:
    streamlit run app.py
"""
import streamlit as st

st.set_page_config(
    page_title="GOAL AI - Football ML Lab",
    page_icon=":soccer:",
    layout="wide",
    initial_sidebar_state="expanded",
)

pg = st.navigation({
    "GOAL AI": [
        st.Page("pages/0_Overview.py", title="Project overview", icon=":material/home:", default=True),
    ],
    "FIFA World Cup 2026": [
        st.Page("pages/1_Player_Analysis.py", title="Player analysis", icon=":material/person:"),
        st.Page("pages/2_Team_Analysis.py", title="Team analysis", icon=":material/flag:"),
        st.Page("pages/3_Player_Head_to_Head.py", title="Player head to head", icon=":material/groups:"),
        st.Page("pages/4_Team_Head_to_Head.py", title="Team head to head", icon=":material/sports_soccer:"),
        st.Page("pages/5_Match_Prediction.py", title="Match predictor", icon=":material/insights:"),
    ],
    "Premier League": [
        st.Page("pages/6_PL_Project_Hub.py", title="Project directory", icon=":material/trophy:"),
        st.Page("pages/7_PL_Transfer_Value.py", title="Transfer value", icon=":material/price_check:"),
        st.Page("pages/8_PL_Match_Outcome.py", title="Match outcomes", icon=":material/query_stats:"),
        st.Page("pages/9_PL_Player_Scouting.py", title="Player scouting", icon=":material/travel_explore:"),
    ],
})
pg.run()
