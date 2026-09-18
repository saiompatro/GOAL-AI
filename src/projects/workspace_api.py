"""Competition pages and API, independent of the existing World Cup experience."""
from datetime import datetime, timezone
from io import BytesIO, StringIO
import csv
import json
import threading

from flask import Blueprint, jsonify, request, send_file, send_from_directory, url_for, Response
from projects import competitions as db
from projects import analytics

workspace = Blueprint("workspace", __name__)
_plot_lock = threading.Lock()


@workspace.errorhandler(ValueError)
def invalid(e):
    return jsonify(error=str(e)), 400


@workspace.route("/competitions/<slug>")
@workspace.route("/competitions/<slug>/<page>")
def page(slug, page="overview"):
    if slug not in db.COMPETITIONS or page not in ("overview", "matches", "transfers", "scouting"):
        return "Page not found", 404
    return send_from_directory(db.ROOT / "web", "workspace.html")


@workspace.route("/assets/<path:filename>")
def asset(filename):
    return send_from_directory(db.ROOT / "web", filename)


@workspace.route("/api/workspaces")
def registry():
    return jsonify([{"slug": slug, **c} for slug, c in db.COMPETITIONS.items()])


@workspace.route("/api/workspaces/<slug>")
def overview(slug):
    c = db.config(slug)
    df, provenance = db.players(slug)
    latest = db.latest_snapshot(df)
    scouts, scout_source = db.scout_players(slug)
    scouts = db.latest_snapshot(scouts)
    scouts = scouts[(scouts.position != "GK") & (scouts.minutes >= 270)]
    matches, match_source = db.matches(slug)
    season = str(matches.season.max())
    recent = matches[matches.season == season]
    teams = sorted(set(recent.home_team) | set(recent.away_team))
    # Aggregate form is not an official table: no deductions, tie-breakers, or UCL groups.
    form = []
    for team in teams:
        played = matches[(matches.home_team == team) | (matches.away_team == team)].tail(6)
        points, scored, conceded, results = 0, 0, 0, []
        for r in played.itertuples():
            gf, ga = (r.home_score, r.away_score) if r.home_team == team else (r.away_score, r.home_score)
            points += 3 if gf > ga else 1 if gf == ga else 0
            scored += gf
            conceded += ga
            results.append("W" if gf > ga else "D" if gf == ga else "L")
        form.append(dict(team=team, points=int(points), scored=int(scored), conceded=int(conceded), form=results, played=len(played)))
    form.sort(key=lambda x: (-x["points"], -(x["scored"]-x["conceded"]), x["team"]))
    path = db.DATA / f"{c['key']}_fixtures.json"
    fixtures = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    if fixtures:
        now = datetime.now(timezone.utc).isoformat()
        fixtures["matches"] = [m for m in fixtures["matches"] if m.get("utcDate", "") > now]
    return jsonify(competition={"slug": slug, **c},
        players=latest.sort_values("player").to_dict("records"), player_source=provenance,
        scout_players=scouts.sort_values("player").to_dict("records"), scout_source=scout_source,
        match_source=match_source, teams=teams, form=form,
        summary=dict(matches=len(matches), seasons=matches.season.nunique(), players=len(latest),
                     player_seasons=df.season.nunique(), player_latest_season=str(df.season.max()),
                     scouting_season=str(scouts.season.max()), scout_profiles=len(scouts), latest_season=season,
                     through=str(matches.date.max()), first_season=str(matches.season.min())),
        recent=matches.tail(6).iloc[::-1][["date", "home_team", "away_team", "home_score", "away_score"]].to_dict("records"), fixtures=fixtures)


@workspace.route("/api/workspaces/<slug>/transfer", methods=["GET", "POST"])
def transfer(slug):
    db.config(slug)
    return jsonify(analytics.transfer(slug, request.args.get("player"), request.get_json() if request.method == "POST" else None))


@workspace.route("/api/workspaces/<slug>/scouting")
def scouting(slug):
    db.config(slug)
    data = analytics.scouting(slug, request.args.get("player", ""), int(request.args.get("k", 8)), request.args.get("position") or None)
    data["export_url"] = url_for("workspace.scouting_csv", slug=slug, player=request.args.get("player", ""), k=request.args.get("k", 8), position=request.args.get("position", ""))
    return jsonify(data)


@workspace.route("/api/workspaces/<slug>/scouting.csv")
def scouting_csv(slug):
    db.config(slug)
    data = analytics.scouting(slug, request.args.get("player", ""), int(request.args.get("k", 8)), request.args.get("position") or None)
    stream = StringIO()
    writer = csv.writer(stream)
    writer.writerow(["Player", "Team", "Position", "Season", "Similarity", "Cluster", *[f"{c}_per90" for c in data["features"]], "Dataset", "Source"])
    for p in data["matches"]:
        row = [p["player"], p["team"], p["position"], p["season"], p["similarity"], p["cluster"], *[p["per90"][c] for c in data["features"]], data["provenance"]["kind"], data["provenance"]["source"]]
        writer.writerow(["'" + v if isinstance(v, str) and v.startswith(("=", "+", "-", "@", "\t", "\r")) else v for v in row])
    return Response("\ufeff" + stream.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f'attachment; filename="{slug}-scouting.csv"'})


@workspace.route("/api/workspaces/<slug>/match", methods=["POST"])
def match(slug):
    db.config(slug)
    q = request.get_json()
    if not isinstance(q, dict) or not isinstance(q.get("neutral", False), bool):
        raise ValueError("Enter teams and a boolean neutral-venue flag")
    return jsonify(analytics.outcome(slug, q.get("home", ""), q.get("away", ""), q.get("neutral", False)))


@workspace.route("/api/workspaces/<slug>/plot/<kind>.png")
def plot(slug, kind):
    db.config(slug)
    if kind not in ("transfer", "scouting", "match"):
        raise ValueError("Unknown chart")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    with _plot_lock:
        fig, ax = plt.subplots(figsize=(8, 5), layout="constrained")
        try:
            if kind == "transfer":
                b = analytics.player_model(slug)
                e = b["evaluation"]
                ax.scatter(e["actual"], e["predicted"], c="#568d28", alpha=.7)
                limit = max(*e["actual"], *e["predicted"])
                ax.plot([0, limit], [0, limit], "--", color="#85908c")
                ax.set(xlabel="Reference value (€m)", ylabel="Predicted value (€m)", title=f"Held-out season {b['metrics']['test_season']} · {b['provenance']['kind']} data")
            elif kind == "match":
                b = analytics.match_model(slug)
                cm = b["metrics"]["confusion"]
                ax.imshow(cm, cmap="Greens")
                for i in range(3):
                    for j in range(3):
                        ax.text(j, i, cm[i][j], ha="center", va="center")
                ax.set(xticks=range(3), yticks=range(3), xticklabels=["Home", "Draw", "Away"], yticklabels=["Home", "Draw", "Away"], xlabel="Predicted", ylabel="Observed", title=f"Held-out {b['metrics']['test_season']} · 90-minute outcomes")
            else:
                from sklearn.decomposition import PCA
                b = analytics.scout_model(slug)
                xy = PCA(n_components=2).fit_transform(b["z"])
                for i, name in b["names"].items():
                    mask = b["cluster"].labels_ == i
                    ax.scatter(xy[mask, 0], xy[mask, 1], label=name, alpha=.8)
                ax.legend(fontsize=8)
                ax.set(xlabel="Style component 1", ylabel="Style component 2", title=f"Per-90 clusters · {b['provenance']['scope']} · {b['latest'].season.max()}")
            stream = BytesIO()
            fig.savefig(stream, format="png", dpi=130)
            stream.seek(0)
            return send_file(stream, mimetype="image/png", download_name=f"{slug}-{kind}.png")
        finally:
            plt.close(fig)
