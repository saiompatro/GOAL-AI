"""Project 3 dashboard — standalone Streamlit app for the player scouting system.

Search for a player and see their closest statistical matches and playing-style
cluster, exactly as described in the project brief. The same engine
(`player_scouting.py`) also powers the Scouting panel in the main Flask/HTML UI;
this is the standalone Streamlit version its tech stack calls for.

Run:  streamlit run projects/streamlit_scouting.py     (from the src/ directory)
"""
import os
import sys

# allow `streamlit run projects/streamlit_scouting.py` from src/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st  # noqa: E402

from projects import player_scouting as scout  # noqa: E402
from projects.common import STYLE_COLUMNS  # noqa: E402


st.set_page_config(page_title="PL Player Scouting", page_icon="⚽", layout="wide")
st.title("⚽ Premier League — Player Scouting System")
st.caption("Find players with the most similar playing style · nearest-neighbours "
           "similarity + K-means style clusters · pandas · scikit-learn · matplotlib")


@st.cache_resource
def engine():
    scout.train(save=True)
    return True


engine()
players = [p["player"] for p in scout.list_players()]

col1, col2 = st.columns([1, 2])
with col1:
    name = st.selectbox("Search a player", players,
                        index=players.index("Bukayo Saka") if "Bukayo Saka" in players else 0)
    k = st.slider("Number of matches", 3, 10, 8)

res = scout.similar(name, k=k)
if "error" in res:
    st.error(res["error"])
    st.stop()

with col1:
    st.subheader(f"{res['player']}")
    st.write(f"**{res['team']}** · {res['position']}")
    st.info(f"Playing-style cluster: **{res['cluster']}**")
    st.write("Per-90 profile")
    st.bar_chart({c: res["per90"][c] for c in STYLE_COLUMNS})

with col2:
    st.subheader("Closest statistical matches")
    st.dataframe(
        [{"Player": m["player"], "Team": m["team"], "Pos": m["position"],
          "Similarity": m["similarity"], "Cluster": m["cluster"],
          **{c: m["per90"][c] for c in STYLE_COLUMNS}} for m in res["matches"]],
        use_container_width=True, hide_index=True,
    )

st.divider()
st.subheader("Playing-style clusters (K-means)")
for c in scout.clusters():
    with st.expander(f"{c['name']} — {c['size']} players"):
        st.write(", ".join(c["players"]))
