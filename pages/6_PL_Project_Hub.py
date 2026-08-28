"""Premier League project directory."""
import streamlit as st

st.caption("PREMIER LEAGUE  /  PROJECT DIRECTORY")
st.title("Premier League ML Lab")
st.write(
    "Turn historical Premier League data into three practical machine-learning workflows. "
    "Start with the guided demo, then swap in football-data.org or an enriched CSV."
)

projects = [
    ("01", "Transfer value predictor", "Linear regression", "Estimate a player's market value from goals, assists, minutes, age, and position.", "pages/7_PL_Transfer_Value.py"),
    ("02", "Match outcome predictor", "Random forest", "Predict a home win, draw, or away win from recent scoring, defending, form, and home advantage.", "pages/8_PL_Match_Outcome.py"),
    ("03", "Player scouting system", "Nearest neighbours + K-means", "Search a player, find the closest statistical matches, and explore playing-style groups.", "pages/9_PL_Player_Scouting.py"),
]

for number, title, model, description, page in projects:
    with st.container(border=True):
        left, right = st.columns([5, 1])
        with left:
            st.caption(f"PROJECT {number}  ·  {model.upper()}")
            st.subheader(title)
            st.write(description)
        with right:
            st.page_link(page, label="Open", icon=":material/arrow_forward:")

st.info(
    "football-data.org supplies competition fixtures, scores, teams, and squads. "
    "Goals, assists, minutes, transfer values, shots, possession, dribbles, and defensive actions "
    "must come from an appropriately licensed enriched player or event-statistics CSV."
)
