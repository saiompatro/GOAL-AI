"""Project 3 — Player scouting system.

Take player statistics and find which players have the most similar playing
styles. Give it a player like Saka and it returns the players with the closest
profile across goals, assists, passing, shots, dribbles and defensive actions.
K-means clustering groups players into playing-style buckets, and a small
dashboard lets you search a player and see their closest statistical matches.

Tech stack: pandas, scikit-learn, matplotlib, streamlit (standalone dashboard
in `streamlit_scouting.py`; the same engine also serves the Flask/HTML UI).

CLI:
    python -m projects.player_scouting                 # cluster summary
    python -m projects.player_scouting "Bukayo Saka"   # nearest matches
    python -m projects.player_scouting --plot          # 2-D style map (PCA)
"""
import os

from projects.common import (STYLE_COLUMNS, MODELS_DIR, load_players,
                             latest_player_seasons)

MODEL_PATH = os.path.join(MODELS_DIR, "player_scouting.joblib")
N_CLUSTERS = 6
# human-readable names are assigned to clusters at fit time by their centroids.


def _per90(df):
    """Style stats normalised per-90 so squad players compare to starters."""
    import numpy as np
    nineties = (df["minutes"] / 90.0).clip(lower=3)
    out = df.copy()
    for c in STYLE_COLUMNS:
        out[c + "_p90"] = df[c] / nineties
    return out


P90_COLS = [c + "_p90" for c in STYLE_COLUMNS]


def _name_cluster(z_centroid, cols):
    """Label a K-means centroid from its *standardised* per-90 stats, so a style
    is judged by how far above the league average it sits on each axis (raw
    defensive counts are numerically larger and would otherwise always win)."""
    d = dict(zip(cols, z_centroid))
    scores = {
        "Goal threat": d["goals_p90"] * 1.1 + d["shots_p90"],
        "Creator": d["assists_p90"] + d["key_passes_p90"] * 1.1,
        "Ball progressor": d["dribbles_p90"] * 1.2,
        "Defensive engine": d["tackles_p90"] + d["interceptions_p90"],
    }
    return max(scores, key=scores.get)


def train(save=True):
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    from sklearn.neighbors import NearestNeighbors
    import joblib

    df = latest_player_seasons(load_players())
    df = df[df["position"] != "GK"]  # style similarity doesn't apply to keepers
    df = _per90(df).reset_index(drop=True)

    scaler = StandardScaler()
    Z = scaler.fit_transform(df[P90_COLS].values)

    km = KMeans(n_clusters=N_CLUSTERS, n_init=10, random_state=0)
    labels = km.fit_predict(Z)
    cluster_names = {i: _name_cluster(km.cluster_centers_[i], P90_COLS)
                     for i in range(N_CLUSTERS)}
    # disambiguate duplicate names with a numeric suffix
    seen = {}
    for i in range(N_CLUSTERS):
        base = cluster_names[i]
        seen[base] = seen.get(base, 0) + 1
        if list(cluster_names.values()).count(base) > 1:
            cluster_names[i] = f"{base} {seen[base]}"

    nn = NearestNeighbors(n_neighbors=min(11, len(df)), metric="euclidean")
    nn.fit(Z)

    bundle = {"scaler": scaler, "kmeans": km, "nn": nn,
              "labels": labels, "cluster_names": cluster_names,
              "players": df, "cols": P90_COLS, "Z": Z}
    if save:
        os.makedirs(MODELS_DIR, exist_ok=True)
        joblib.dump({k: v for k, v in bundle.items() if k not in ("players", "Z")},
                    MODEL_PATH)
    return bundle


_bundle = None


def _get():
    global _bundle
    if _bundle is None:
        _bundle = train(save=True)
    return _bundle


def reload():
    global _bundle
    _bundle = None


def list_players():
    b = _get()
    df = b["players"]
    out = []
    for i, r in df.iterrows():
        out.append({"player": r["player"], "team": r["team"],
                    "position": r["position"],
                    "cluster": b["cluster_names"][int(b["labels"][i])]})
    return sorted(out, key=lambda x: x["player"])


def similar(name, k=8):
    """Closest statistical matches to a named player."""
    import numpy as np
    b = _get()
    df = b["players"]
    mask = df["player"].str.lower() == str(name).lower()
    if not mask.any():
        return {"error": f"unknown player '{name}'"}
    idx = int(np.where(mask.values)[0][0])
    dist, nbr = b["nn"].kneighbors(b["Z"][idx:idx + 1], n_neighbors=min(k + 1, len(df)))
    dist, nbr = dist[0], nbr[0]
    scale = dist.max() or 1.0
    matches = []
    for d, j in zip(dist, nbr):
        if j == idx:
            continue
        r = df.iloc[j]
        matches.append({
            "player": r["player"], "team": r["team"], "position": r["position"],
            "cluster": b["cluster_names"][int(b["labels"][j])],
            "similarity": round(float(1 - d / (scale * 1.15)), 3),
            "per90": {c: round(float(r[c + "_p90"]), 2) for c in STYLE_COLUMNS},
        })
        if len(matches) >= k:
            break
    src = df.iloc[idx]
    return {
        "player": src["player"], "team": src["team"], "position": src["position"],
        "cluster": b["cluster_names"][int(b["labels"][idx])],
        "per90": {c: round(float(src[c + "_p90"]), 2) for c in STYLE_COLUMNS},
        "matches": matches,
    }


def clusters():
    """Playing-style groups with their members."""
    b = _get()
    df, labels, names = b["players"], b["labels"], b["cluster_names"]
    groups = {}
    for i, r in df.iterrows():
        cid = int(labels[i])
        groups.setdefault(cid, {"name": names[cid], "players": []})
        groups[cid]["players"].append(r["player"])
    return [{"id": cid, "name": g["name"], "size": len(g["players"]),
             "players": sorted(g["players"])}
            for cid, g in sorted(groups.items())]


def plot(path=None):
    """2-D style map: PCA of the per-90 space, coloured by K-means cluster."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.decomposition import PCA
    b = _get()
    xy = PCA(n_components=2, random_state=0).fit_transform(b["Z"])
    path = path or os.path.join(MODELS_DIR, "player_style_map.png")
    plt.figure(figsize=(7, 6))
    sc = plt.scatter(xy[:, 0], xy[:, 1], c=b["labels"], cmap="tab10", s=24, alpha=0.8)
    plt.title("Premier League player style map (PCA + K-means)")
    plt.xlabel("style dim 1"); plt.ylabel("style dim 2")
    plt.tight_layout(); plt.savefig(path, dpi=110); plt.close()
    return path


def main():
    import sys
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        res = similar(args[0])
        if "error" in res:
            print(res["error"]); return
        print(f"{res['player']} ({res['team']}, {res['position']}) — "
              f"cluster: {res['cluster']}")
        print("  closest matches:")
        for m in res["matches"]:
            print(f"    {m['player']:<24} {m['team']:<22} "
                  f"sim={m['similarity']:.2f}  [{m['cluster']}]")
    else:
        for c in clusters():
            print(f"[{c['name']}] ({c['size']}): "
                  f"{', '.join(c['players'][:6])}"
                  f"{' ...' if c['size'] > 6 else ''}")
    if "--plot" in sys.argv:
        print("wrote", plot())


if __name__ == "__main__":
    main()
