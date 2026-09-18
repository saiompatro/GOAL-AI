"""Standalone multi-competition scouting. Run from the repository root:
streamlit run src/projects/streamlit_scouting.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st
from projects import analytics
from projects.competitions import COMPETITIONS

st.set_page_config(page_title="GOAL AI · Scouting", page_icon="⚽", layout="wide")
slug = st.sidebar.selectbox("Competition", list(COMPETITIONS), format_func=lambda s: COMPETITIONS[s]["name"])
st.title(f"{COMPETITIONS[slug]['name']} · Player Scouting")
st.caption("Similar playing styles, measured per 90 minutes.")
engine = analytics.scout_model(slug)
source = engine["provenance"]
if source["kind"] == "demo":
    st.warning(source["note"])
else:
    st.info(f"{source['source']} — {source['note']}")
players = sorted(engine["outfield"].player)
col1, col2 = st.columns([1, 2])
with col1:
    name = st.selectbox("Search a player", players, index=players.index("Bukayo Saka") if "Bukayo Saka" in players else 0)
    k = st.slider("Number of matches", 1, 20, 8)
    position = st.selectbox("Position filter", ["All outfield", "FW", "MF", "DF"])
    res = analytics.scouting(slug, name, k, None if position == "All outfield" else position)
    st.subheader(res["player"])
    st.write(f"{res['team']} · {res['position']}")
    st.info(res["cluster"])
    st.bar_chart(pd.DataFrame({"Per 90": res["per90"]}))
    st.caption("Similarity is a distance score, not a probability of equal ability. Players need at least 270 minutes.")
with col2:
    st.subheader("Closest statistical matches")
    table = pd.DataFrame([{"Player": m["player"], "Team": m["team"], "Position": m["position"],
                           "Similarity": m["similarity"], "Cluster": m["cluster"],
                           **{c: m["per90"][c] for c in res["features"]}} for m in res["matches"]])
    st.dataframe(table, width="stretch", hide_index=True)
    exported = table.copy()
    for col in exported.select_dtypes(include=["object", "str"]).columns:
        exported[col] = exported[col].map(lambda v: "'" + v if isinstance(v, str) and v.startswith(("=", "+", "-", "@")) else v)
    exported["Dataset"] = source["kind"]
    st.download_button("Download matches", exported.to_csv(index=False).encode("utf-8-sig"), file_name=f"{slug}-scouting.csv", mime="text/csv")
st.divider()
st.subheader("Playing-style clusters")
for group in res["clusters"]:
    with st.expander(f"{group['name']} · {group['size']} players"):
        members = [r.player for i, r in engine["outfield"].iterrows()
                   if engine["names"][int(engine["cluster"].labels_[i])] == group["name"]]
        st.write(", ".join(members))
