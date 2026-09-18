"""Run: python -m unittest discover -s tests -v"""
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
