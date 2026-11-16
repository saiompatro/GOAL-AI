"""Run: python -m unittest discover -s tests -v"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from app import app
from projects import analytics, competitions as db
import requests
from projects import fpl_insights, open_matchday, openfootball, refresh_data
from projects.refresh_data import parse_ucl, import_players


class WorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    def test_all_competitions_have_deep_links_and_isolated_tools(self):
        for slug in db.COMPETITIONS:
            with self.subTest(competition=slug):
                for page in ("overview", "matches", "transfers", "scouting"):
                    with self.client.get(f"/competitions/{slug}/{page}") as response:
                        self.assertEqual(response.status_code, 200)
                d = self.client.get(f"/api/workspaces/{slug}")
                self.assertEqual(d.status_code, 200)
                self.assertEqual(d.json["competition"]["slug"], slug)
                player = next(p["player"] for p in d.json["players"] if p["position"] != "GK")
                transfer = self.client.get(f"/api/workspaces/{slug}/transfer", query_string={"player": player})
                self.assertEqual(transfer.status_code, 200)
                self.assertGreaterEqual(transfer.json["predicted_value"], 0)
                self.assertEqual(transfer.json["provenance"]["kind"], "observed")
                scout_player = d.json["scout_players"][0]["player"]
                scout = self.client.get(f"/api/workspaces/{slug}/scouting", query_string={"player": scout_player})
                self.assertEqual(scout.status_code, 200)
                self.assertNotIn(scout_player, [p["player"] for p in scout.json["matches"]])
                home, away = d.json["teams"][:2]
                outcome = self.client.post(f"/api/workspaces/{slug}/match", json={"home": home, "away": away})
                self.assertEqual(outcome.status_code, 200)
                self.assertAlmostEqual(sum(outcome.json["prob"].values()), 1, places=8)
                m = outcome.json["metrics"]
                self.assertLess(m["train_end"], m["test_start"])
                self.assertEqual(sum(map(sum, m["confusion"])), m["n_test"])
                self.assertAlmostEqual(sum(m["confusion"][i][i] for i in range(3)) / m["n_test"], m["accuracy"], places=3)

    def test_models_are_competition_specific(self):
        self.assertIsNot(analytics.player_model("premier-league")["model"], analytics.player_model("la-liga")["model"])
        self.assertEqual(self.client.get("/api/workspaces/la-liga/transfer", query_string={"player": "Bukayo Saka"}).status_code, 400)

    def test_features_do_not_see_current_or_future_results(self):
        original = pd.DataFrame([dict(date=f"2024-01-{day:02}", season="2023-24", home_team="A", away_team="B", home_score=1, away_score=0,
                                     home_shots=5, away_shots=2) for day in range(1, 13)])
        changed = original.copy()
        changed.loc[8:, "home_score"], changed.loc[8:, "home_shots"] = 9, 40
        a, cols, state, _ = analytics.build_match_features(original)
        b, _, changed_state, _ = analytics.build_match_features(changed)
        pd.testing.assert_frame_equal(a.loc[a.date <= "2024-01-09", cols], b.loc[b.date <= "2024-01-09", cols])
        self.assertEqual(state["A"]["scored"], 1)
        self.assertGreater(changed_state["A"]["scored"], 1)
        self.assertNotIn("home_possession", cols)
        self.assertEqual(state["A"]["shots"], 5)

    def test_ucl_uses_regulation_score_and_final_is_neutral(self):
        text = """# Matches 2
▪ Finals, Semifinals
  Wed May 4 2022
    21:00 Real Madrid (ESP) v Manchester City (ENG) 3-1 a.e.t. (2-1, 0-0)
▪ Finals, Final
  Sat May 28
    21:00 Real Madrid (ESP) v Liverpool (ENG) 5-4 pen. 1-1 a.e.t. (0-0, 0-0)
"""
        rows = parse_ucl(text, 2021)
        self.assertEqual((rows[0]["home_score"], rows[0]["away_score"]), (2, 1))
        self.assertEqual((rows[1]["home_score"], rows[1]["away_score"]), (0, 0))
        self.assertEqual(rows[1]["neutral"], 1)
        self.assertEqual(rows[1]["date"], "2022-05-28")

    def test_openfootball_rows_keep_only_played_matches_with_known_clubs(self):
        payload = {"matches": [
            dict(date="2026-08-15", team1="FC Barcelona", team2="Real Madrid CF", score={"ft": [2, 1], "ht": [1, 0]}),
            dict(date="2026-08-16", team1="Valencia CF", team2="RC Celta de Vigo", score=[0, 0]),
            dict(date="2026-08-17", team1="Getafe CF", team2="Sevilla FC", score=None),
            dict(date="2026-08-18", team1="Elche CF", team2="Levante UD", score={})]}
        rows = openfootball.parse_season("la-liga", 2026, payload)
        self.assertEqual([(r["home_team"], r["away_team"], r["home_score"], r["away_score"]) for r in rows],
                         [("Barcelona", "Real Madrid", 2, 1), ("Valencia", "Celta", 0, 0)])
        self.assertTrue(all(r["season"] == "2026-27" and r["neutral"] == 0 for r in rows))
        payload["matches"].append(dict(date="2026-08-19", team1="Unknown FC", team2="Sevilla FC", score=[1, 0]))
        with self.assertRaises(ValueError):
            openfootball.parse_season("la-liga", 2026, payload)

    def test_openfootball_maps_premier_league_clubs_to_dataset_names(self):
        payload = {"matches": [
            dict(date="2026-08-22", team1="Hull City AFC", team2="Nottingham Forest FC", score={"ft": [1, 2]}),
            dict(date="2026-08-23", team1="Coventry City FC", team2="Manchester United FC", score={"ft": [0, 0]})]}
        rows = openfootball.parse_season("premier-league", 2026, payload)
        self.assertEqual([(r["home_team"], r["away_team"]) for r in rows],
                         [("Hull", "Nott'm Forest"), ("Coventry", "Man United")])
        installed = set(pd.read_csv(db.DATA / "premier_league_matches.csv").home_team)
        self.assertLessEqual(installed, set(openfootball.LEAGUES["premier-league"][1].values()))

    def test_openfootball_maps_bundesliga_clubs_to_dataset_names(self):
        payload = {"matches": [
            dict(date="2026-08-29", team1="SV 07 Elversberg", team2="Borussia Mönchengladbach", score={"ft": [2, 1]}),
            dict(date="2026-08-30", team1="SC Paderborn 07", team2="FC Bayern München", score={"ft": [0, 3]})]}
        rows = openfootball.parse_season("bundesliga", 2026, payload)
        self.assertEqual([(r["home_team"], r["away_team"]) for r in rows],
                         [("Elversberg", "M'gladbach"), ("Paderborn", "Bayern Munich")])
        installed = set(pd.read_csv(db.DATA / "bundesliga_matches.csv").home_team)
        self.assertLessEqual(installed, set(openfootball.LEAGUES["bundesliga"][1].values()))

    def test_openfootball_maps_serie_a_clubs_to_dataset_names(self):
        payload = {"matches": [
            dict(date="2026-08-22", team1="FC Internazionale Milano", team2="Frosinone Calcio", score={"ft": [3, 0]}),
            dict(date="2026-08-23", team1="AC Monza", team2="Hellas Verona FC", score={"ft": [1, 1]})]}
        rows = openfootball.parse_season("serie-a", 2026, payload)
        self.assertEqual([(r["home_team"], r["away_team"]) for r in rows],
                         [("Inter", "Frosinone"), ("Monza", "Verona")])
        installed = set(pd.read_csv(db.DATA / "serie_a_matches.csv").home_team)
        self.assertLessEqual(installed, set(openfootball.LEAGUES["serie-a"][1].values()))

    def test_blocked_source_keeps_installed_rows_and_adds_only_new_scores(self):
        installed = pd.DataFrame([dict(date=f"2025-09-{day:02}", season="2025-26", home_team="Barcelona", away_team=away,
                                       home_score=1, away_score=0, neutral=0, home_shots=12, away_shots=7)
                                  for day, away in enumerate(["Sevilla", "Valencia"], 1)])
        installed = pd.concat([installed, pd.DataFrame([dict(date="2025-10-01", season="2025-26", home_team=f"H{i}", away_team=f"A{i}",
                               home_score=0, away_score=0, neutral=0, home_shots=9, away_shots=9) for i in range(100)])])
        feed = {2025: [dict(date="2025-09-01", season="2025-26", home_team="Barcelona", away_team="Sevilla", home_score=9, away_score=9, neutral=0)],
                2026: [dict(date="2026-08-15", season="2026-27", home_team="Malaga", away_team="Barcelona", home_score=0, away_score=3, neutral=0)]}
        with tempfile.TemporaryDirectory() as temp:
            installed.to_csv(Path(temp) / "la_liga_matches.csv", index=False)
            (Path(temp) / "la_liga_matches.json").write_text('{"source": "football-data.co.uk"}', encoding="utf-8")
            with patch("projects.refresh_data.DATA", Path(temp)), \
                 patch("projects.refresh_data.requests.get", side_effect=requests.ConnectionError("blocked")), \
                 patch.object(openfootball, "fetch_season", side_effect=lambda slug, year: feed[year]):
                refresh_data.fetch_matches("la-liga", [2025, 2026])
            out = pd.read_csv(Path(temp) / "la_liga_matches.csv")
            meta = json.loads((Path(temp) / "la_liga_matches.json").read_text(encoding="utf-8"))
        self.assertEqual(len(out), len(installed) + 1)
        kept = out[(out.home_team == "Barcelona") & (out.away_team == "Sevilla")].iloc[0]
        self.assertEqual((kept.home_score, kept.home_shots), (1, 12))  # installed row is never overwritten
        new = out[out.season == "2026-27"].iloc[0]
        self.assertEqual((new.home_team, new.away_score), ("Malaga", 3))
        self.assertTrue(pd.isna(new.home_shots))  # no shots are invented for scores-only rows
        self.assertEqual(meta["season_sources"], {"2025-26": "football-data.co.uk", "2026-27": "OpenFootball (scores only)"})
        self.assertEqual(meta["latest_match"], "2026-08-15")

    def test_fpl_insights_rows_keep_finished_matches_with_uk_dates_and_shots(self):
        frame = pd.DataFrame([
            dict(kickoff_time="2026-08-21T19:00:00", home_team=3.0, away_team=9.0, home_score=3.0, away_score=0.0,
                 finished=True, match_id="a", home_total_shots=20.0, away_total_shots=4.0),
            # 23:30 UTC in August is 00:30 the next day in the UK, the date football-data.co.uk records.
            dict(kickoff_time="2026-08-22T23:30:00", home_team=88.0, away_team=1.0, home_score=2.0, away_score=0.0,
                 finished=True, match_id="b", home_total_shots=None, away_total_shots=None),
            dict(kickoff_time="2026-11-21T15:00:00", home_team=43.0, away_team=14.0, home_score=None, away_score=None,
                 finished=False, match_id="c", home_total_shots=None, away_total_shots=None)])
        rows = fpl_insights.parse_matches("premier-league", 2026, frame)
        self.assertEqual([(r["date"], r["home_team"], r["away_team"], r["home_score"], r["away_score"], r["home_shots"], r["away_shots"])
                          for r in rows],
                         [("2026-08-21", "Arsenal", "Coventry", 3, 0, 20, 4), ("2026-08-23", "Hull", "Man United", 2, 0, None, None)])
        self.assertTrue(all(r["season"] == "2026-27" and r["neutral"] == 0 for r in rows))
        installed = set(pd.read_csv(db.DATA / "premier_league_matches.csv").query("season >= '2025-26'").home_team)
        self.assertLessEqual(installed, set(fpl_insights.LEAGUES["premier-league"][1].values()))
        frame.loc[0, "home_team"] = 999.0
        with self.assertRaises(ValueError):
            fpl_insights.parse_matches("premier-league", 2026, frame)

    def _refresh_premier_league(self, installed, feed):
        with tempfile.TemporaryDirectory() as temp:
            installed.to_csv(Path(temp) / "premier_league_matches.csv", index=False)
            (Path(temp) / "premier_league_matches.json").write_text(json.dumps({"season_sources": {
                "2025-26": "football-data.co.uk", "2026-27": "OpenFootball (scores only)"}}), encoding="utf-8")
            with patch("projects.refresh_data.DATA", Path(temp)), \
                 patch("projects.refresh_data.requests.get", side_effect=requests.ConnectionError("blocked")), \
                 patch.object(openfootball, "fetch_season", return_value=[]), \
                 patch.object(fpl_insights, "fetch_season", side_effect=lambda slug, year: feed[year]):
                refresh_data.fetch_matches("premier-league", [2025, 2026])
            return (pd.read_csv(Path(temp) / "premier_league_matches.csv"),
                    json.loads((Path(temp) / "premier_league_matches.json").read_text(encoding="utf-8")))

    def test_feed_with_shots_replaces_scores_only_rows_but_not_downloaded_seasons(self):
        row = lambda date, season, home, away, hs, as_, shots: dict(
            date=date, season=season, home_team=home, away_team=away, home_score=hs, away_score=as_, neutral=0,
            home_shots=shots, away_shots=shots)
        installed = pd.DataFrame([row("2025-10-01", "2025-26", f"H{i}", f"A{i}", 1, 0, 9) for i in range(100)]
                                 + [row("2026-08-21", "2026-27", "Arsenal", "Coventry", 3, 0, None)])
        feed = {2026: [row("2026-08-21", "2026-27", "Arsenal", "Coventry", 3, 0, 20),
                       row("2026-11-07", "2026-27", "Leeds", "Tottenham", 1, 0, 16)]}
        out, meta = self._refresh_premier_league(installed, feed)
        self.assertEqual(len(out), 102)
        self.assertEqual(out[out.season == "2025-26"].home_shots.tolist(), [9] * 100)  # the complete season is not refetched
        current = out[out.season == "2026-27"]
        self.assertEqual(current.home_shots.tolist(), [20, 16])
        self.assertEqual(meta["season_sources"], {"2025-26": "football-data.co.uk", "2026-27": "FPL-Elo-Insights"})
        self.assertEqual(meta["latest_match"], "2026-11-07")
        self.assertNotIn("note", meta)
        feed[2026][0]["home_score"] = 1  # two sources that disagree on a result stop the refresh
        with self.assertRaises(ValueError):
            self._refresh_premier_league(installed, feed)

    def test_open_matchday_rows_map_clubs_and_keep_shots_only_when_observed(self):
        frame = pd.DataFrame([
            dict(gw=1, date="2026-08-28", time="19:30", home="FC Bayern München", away="VfB Stuttgart",
                 ft_home=5, ft_away=1, home_shots=21.0, away_shots=11.0, source="openligadb"),
            # A row supplied by football-data.co.uk already carries the dataset spelling; shots may be missing.
            dict(gw=9, date="2026-11-08", time="18:30", home="Hoffenheim", away="FC Schalke 04",
                 ft_home=2, ft_away=1, home_shots=None, away_shots=None, source="fd.co.uk")])
        rows = open_matchday.parse_results("bundesliga", 2026, frame)
        self.assertEqual([(r["date"], r["home_team"], r["away_team"], r["home_score"], r["away_score"], r["home_shots"], r["away_shots"])
                          for r in rows],
                         [("2026-08-28", "Bayern Munich", "Stuttgart", 5, 1, 21, 11), ("2026-11-08", "Hoffenheim", "Schalke 04", 2, 1, None, None)])
        self.assertTrue(all(r["season"] == "2026-27" and r["neutral"] == 0 for r in rows))
        current = pd.read_csv(db.DATA / "bundesliga_matches.csv").query("season == '2026-27'")
        self.assertEqual(set(current.home_team), set(open_matchday.LEAGUES["bundesliga"][1].values()))
        with self.assertRaises(ValueError):  # the same fixture twice
            open_matchday.parse_results("bundesliga", 2026, pd.concat([frame, frame]))
        frame.loc[0, "home"] = "FC Hollywood"
        with self.assertRaises(ValueError):
            open_matchday.parse_results("bundesliga", 2026, frame)

    def test_open_matchday_fixtures_use_dataset_names_and_utc_kickoffs(self):
        frame = pd.DataFrame([dict(gw=11, date="2026-11-28", time=None, home="SC Freiburg", away="RB Leipzig"),
                              dict(gw=10, date="2026-11-20", time="20:30", home="FC Bayern München", away="1. FC Köln")])
        self.assertEqual(open_matchday.parse_fixtures("bundesliga", frame), [
            dict(utcDate="2026-11-20T19:30:00Z", matchday=10, homeTeam={"name": "Bayern Munich"}, awayTeam={"name": "FC Koln"}),
            dict(utcDate="2026-11-28T23:59:00Z", matchday=11, homeTeam={"name": "Freiburg"}, awayTeam={"name": "RB Leipzig"})])

    def test_blocked_source_takes_a_shots_feed_for_a_league_without_fpl_data(self):
        row = lambda date, season, home, away, hs, as_, shots: dict(
            date=date, season=season, home_team=home, away_team=away, home_score=hs, away_score=as_, neutral=0,
            home_shots=shots, away_shots=shots)
        installed = pd.DataFrame([row("2025-10-01", "2025-26", f"H{i}", f"A{i}", 1, 0, 9) for i in range(100)]
                                 + [row("2026-08-28", "2026-27", "Bayern Munich", "Stuttgart", 5, 1, None)])
        feed = [row("2026-08-28", "2026-27", "Bayern Munich", "Stuttgart", 5, 1, 21),
                row("2026-11-08", "2026-27", "Hoffenheim", "Schalke 04", 2, 1, 15)]
        with tempfile.TemporaryDirectory() as temp:
            installed.to_csv(Path(temp) / "bundesliga_matches.csv", index=False)
            (Path(temp) / "bundesliga_matches.json").write_text(json.dumps({"season_sources": {
                "2025-26": "football-data.co.uk", "2026-27": "OpenFootball (scores only)"}}), encoding="utf-8")
            with patch("projects.refresh_data.DATA", Path(temp)), \
                 patch("projects.refresh_data.requests.get", side_effect=requests.ConnectionError("blocked")), \
                 patch.object(openfootball, "fetch_season", return_value=[]), \
                 patch.object(open_matchday, "fetch_season", side_effect=lambda slug, year: feed if year == 2026 else []):
                refresh_data.fetch_matches("bundesliga", [2025, 2026])
            out = pd.read_csv(Path(temp) / "bundesliga_matches.csv")
            meta = json.loads((Path(temp) / "bundesliga_matches.json").read_text(encoding="utf-8"))
        self.assertEqual(out[out.season == "2025-26"].home_shots.tolist(), [9] * 100)
        self.assertEqual(out[out.season == "2026-27"].home_shots.tolist(), [21, 15])
        self.assertEqual(meta["season_sources"], {"2025-26": "football-data.co.uk", "2026-27": "open-matchday"})
        self.assertEqual((meta["latest_match"], meta["terms"]), ("2026-11-08", open_matchday.TERMS))

    def test_overview_serves_upcoming_fixtures_between_current_teams(self):
        data = self.client.get("/api/workspaces/bundesliga").get_json()
        self.assertEqual(data["fixtures"]["source"], "open-matchday")
        teams = {m[side]["name"] for m in data["fixtures"]["matches"] for side in ("homeTeam", "awayTeam")}
        self.assertLessEqual(teams, set(data["teams"]))

    def test_availability_lists_injured_doubtful_and_suspended_players_only(self):
        stats = pd.DataFrame([
            dict(id=1, gw=9, status="i", chance_of_playing_next_round=0, news="Old flag", minutes=10),
            dict(id=1, gw=10, status="a", chance_of_playing_next_round=None, news=None, minutes=100),
            dict(id=2, gw=10, status="d", chance_of_playing_next_round=75.0, news="Calf injury - 75% chance of playing", minutes=461),
            dict(id=3, gw=10, status="u", chance_of_playing_next_round=0, news="Has joined Al Hilal permanently", minutes=0),
            dict(id=4, gw=10, status="s", chance_of_playing_next_round=0, news="Suspended until 29 Nov", minutes=19)])
        players = pd.DataFrame([dict(player_id=i, first_name="First", second_name=f"Last{i}", web_name=f"P{i}", team_code=code, position=pos)
                                for i, code, pos in [(1, 3, "Forward"), (2, 7, "Midfielder"), (3, 3, "Midfielder"), (4, 3, "Defender")]])
        rows, gameweek = fpl_insights.parse_availability("premier-league", stats, players)
        self.assertEqual(gameweek, 10)
        self.assertEqual([(r["player"], r["team"], r["position"], r["status"], r["chance_of_playing"]) for r in rows],
                         [("P4", "Arsenal", "DF", "suspended", 0), ("P2", "Aston Villa", "MF", "doubtful", 75)])

    def test_overview_serves_the_availability_snapshot_for_current_teams(self):
        data = self.client.get("/api/workspaces/premier-league").get_json()
        snapshot = data["availability"]
        self.assertEqual(snapshot["source"], "FPL-Elo-Insights")
        self.assertTrue(snapshot["players"])
        self.assertLessEqual({p["team"] for p in snapshot["players"]}, set(data["teams"]))
        self.assertLessEqual({p["status"] for p in snapshot["players"]}, {"injured", "doubtful", "suspended"})
        self.assertIsNone(self.client.get("/api/workspaces/la-liga").get_json()["availability"])

    def test_similarity_does_not_depend_on_result_count(self):
        a = analytics.scouting("premier-league", "Bukayo Saka", 3)
        b = analytics.scouting("premier-league", "Bukayo Saka", 8)
        self.assertEqual(a["matches"], b["matches"][:3])

    def test_bad_requests_and_world_cup(self):
        for path in ("/", "/world-cup"):
            with self.client.get(path) as response:
                self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/competitions/unknown").status_code, 404)
        self.assertEqual(self.client.get("/api/workspaces/unknown").status_code, 400)
        base = "/api/workspaces/premier-league"
        self.assertEqual(self.client.post(base + "/match", json={"home": "Arsenal", "away": "Arsenal"}).status_code, 400)
        self.assertEqual(self.client.get(base + "/scouting?k=garbage").status_code, 400)
        self.assertEqual(self.client.post(base + "/transfer", json={"age": -1}).status_code, 400)
        self.assertEqual(self.client.post(base + "/transfer", json={"age": 25, "minutes": 2000, "goals": "nan"}).status_code, 400)

    def test_import_validation_and_provenance(self):
        df, _ = db.players("la-liga")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "input.csv"
            df.to_csv(path, index=False)
            with patch("projects.refresh_data.DATA", Path(temp)), patch.object(db, "DATA", Path(temp)):
                import_players("la-liga", path, "Test reference data")
                loaded, metadata = db.players("la-liga")
                self.assertEqual(len(loaded), len(df))
                self.assertEqual(metadata["kind"], "imported")
                self.assertEqual(metadata["source"], "Test reference data")
                df["goals"] = df["goals"].astype(float)
                df.loc[0, "goals"] = np.inf
                df.to_csv(path, index=False)
                with self.assertRaises(ValueError):
                    import_players("la-liga", path, "Invalid data")
                self.assertTrue(np.isfinite(db.players("la-liga")[0].goals).all())

    def test_export_charts(self):
        for kind in ("match", "transfer", "scouting"):
            r = self.client.get(f"/api/workspaces/premier-league/plot/{kind}.png")
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.mimetype, "image/png")
            self.assertTrue(r.data.startswith(b"\x89PNG"))

    def test_scouting_export_matches_filtered_results(self):
        import csv
        from io import StringIO
        q = {"player": "Bukayo Saka", "position": "DF", "k": 3}
        result = self.client.get("/api/workspaces/premier-league/scouting", query_string=q).json
        response = self.client.get(result["export_url"])
        self.assertEqual(response.status_code, 200)
        rows = list(csv.DictReader(StringIO(response.data.decode("utf-8-sig"))))
        self.assertEqual([r["Player"] for r in rows], [r["player"] for r in result["matches"]])
        self.assertTrue(all(r["Position"] == "DF" and r["Dataset"] == "observed" for r in rows))

    def test_recorded_saka_scouting_stats_and_missing_ucl_fields(self):
        df, source = db.scout_players("premier-league")
        saka = df[df.player == "Bukayo Saka"].iloc[0]
        self.assertEqual((saka.minutes, saka.goals, saka.assists, saka.shots), (1729, 6, 10, 66))
        self.assertEqual((saka.key_passes, saka.dribbles, saka.tackles, saka.interceptions), (58, 41, 29, 3))
        ucl = analytics.scouting("champions-league", "Bukayo Saka")
        self.assertEqual(ucl["features"], ["goals", "assists"])
        self.assertEqual(ucl["provenance"]["scope"], "basic")
        self.assertNotIn("shots", ucl["per90"])
        csv = self.client.get("/api/workspaces/champions-league/scouting.csv?player=Bukayo%20Saka")
        self.assertNotIn("shots_per90", csv.text)

    def test_values_follow_feature_cutoff_and_incomplete_seasons_are_excluded(self):
        for slug in db.COMPETITIONS:
            df, meta = db.players(slug)
            self.assertFalse(df.duplicated(["player_id", "season"]).any())
            self.assertTrue((df.valuation_date > df.feature_cutoff).all())
            days = (pd.to_datetime(df.valuation_date) - pd.to_datetime(df.feature_cutoff)).dt.days
            self.assertTrue(days.between(1, 90).all())
            self.assertTrue(np.isfinite(df[["age", "minutes", "goals", "assists", "market_value_eur_m"]]).all().all())
            latest = analytics.player_model(slug)["latest"]
            self.assertEqual(latest.season.nunique(), 1)
            if slug in ("champions-league", "ligue-1"):
                self.assertEqual(df.season.max(), "2024-25")
                self.assertIn("2025", meta["excluded_incomplete_seasons"])

    def test_valuation_join_never_uses_prior_or_stale_values(self):
        from projects.prepare_player_data import attach_values
        stats = pd.DataFrame({"player_id": [1, 2, 3], "feature_cutoff": pd.to_datetime(["2025-05-31"] * 3)})
        values = pd.DataFrame({"player_id": [1, 1, 1, 2, 3],
            "valuation_date": pd.to_datetime(["2025-05-01", "2025-05-31", "2025-06-10", "2025-09-10", "2025-05-30"]),
            "market_value_eur_m": [1, 2, 3, 4, 5]})
        joined = attach_values(stats, values).set_index("player_id")
        self.assertEqual(joined.loc[1, "market_value_eur_m"], 3)
        self.assertTrue(joined.loc[[2, 3], "market_value_eur_m"].isna().all())

    def test_named_estimate_does_not_use_its_own_valuation_target(self):
        from sklearn.base import clone
        b = analytics.player_model("premier-league")
        train = b["df"][b["df"].season < b["metrics"]["test_season"]]
        independent = clone(b["holdout_model"]).fit(train[b["features"]], train.market_value_eur_m)
        row = b["latest"][b["latest"].player == "Bukayo Saka"]
        expected = round(max(0, independent.predict(row[b["features"]])[0]), 1)
        result = analytics.transfer("premier-league", "Bukayo Saka")
        self.assertEqual(result["predicted_value"], expected)
        self.assertEqual(result["prediction_basis"], "Held-out estimate")

    def test_missing_observed_files_fail_instead_of_generating_players(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(db, "DATA", Path(temp)):
            with self.assertRaisesRegex(ValueError, "Observed player data is missing"):
                db.players("premier-league")

    def test_artifact_roundtrip_and_stale_input_rejection(self):
        from projects import model_store
        with tempfile.TemporaryDirectory() as temp, patch.object(model_store, "DIRECTORY", Path(temp)):
            model_store.save("premier-league", "valuation", {"test": "observed"})
            self.assertEqual(model_store.load("premier-league", "valuation"), {"test": "observed"})
            with patch.object(model_store, "signature", return_value={"inputs": "changed"}):
                self.assertIsNone(model_store.load("premier-league", "valuation"))

    def test_legacy_player_routes_use_observed_models(self):
        prediction = self.client.get("/api/pl/transfer/predict?player=Bukayo%20Saka", follow_redirects=True)
        self.assertEqual(prediction.status_code, 200)
        self.assertEqual(prediction.json["provenance"]["kind"], "observed")
        custom = self.client.post("/api/pl/transfer/custom", json={"age": 24, "minutes": 2400, "goals": 10, "assists": 6, "position": "FW"}, follow_redirects=True)
        self.assertEqual(custom.status_code, 200)
        self.assertIsNone(custom.json["reference_value"])
        scouting = self.client.get("/api/pl/scouting/similar?player=Bukayo%20Saka", follow_redirects=True)
        self.assertEqual(scouting.json["provenance"]["kind"], "observed")

    def test_provider_fetch_does_not_invent_statistics(self):
        from projects.fetch_players import fetch_rosters
        with patch("projects.fetch_players._token", return_value="test-token"), patch("projects.fetch_players.requests.get") as get:
            get.return_value.json.return_value = {"teams": [{"name": "Example", "squad": [{"id": 1, "name": "Player", "position": "Forward"}]}]}
            rows = fetch_rosters("PD", 2023)
            self.assertEqual(get.call_args.kwargs["params"], {"season": 2023})
            get.return_value.raise_for_status.assert_called_once()
            self.assertNotIn("goals", rows[0])
            self.assertNotIn("market_value_eur_m", rows[0])


if __name__ == "__main__":
    unittest.main()
