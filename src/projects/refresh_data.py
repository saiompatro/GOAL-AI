"""Reproducible public match downloads, provider fixtures, and validated player imports.

Run from the root: python src/projects/refresh_data.py --help
Never turn missing provider statistics or transfer values into fabricated facts.
"""
import argparse
from datetime import datetime, timezone
from io import StringIO
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import requests
from projects.competitions import COMPETITIONS, DATA, config
from projects.common import FEATURE_COLUMNS


def write_dataset(slug, kind, df, metadata):
    DATA.mkdir(parents=True, exist_ok=True)
    path = DATA / f"{config(slug)['key']}_{kind}.csv"
    # Validate before touching existing data; replace each file atomically.
    temporary = path.with_suffix(".tmp")
    df.to_csv(temporary, index=False)
    temporary.replace(path)
    metadata["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    temporary.replace(path.with_suffix(".json"))
    print(f"{slug}: {len(df)} {kind} rows")


def parse_ucl(text, start_year):
    """Parse football.txt, taking regulation scores for extra-time/penalty games."""
    rows, date, stage = [], None, ""
    months = {m: i for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("▪"):
            stage = line[1:].strip()
        d = re.match(r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) ([A-Z][a-z]{2}) (\d{1,2})(?: (\d{4}))?$", line)
        if d:
            month = months[d[1]]
            year = int(d[3]) if d[3] else start_year + (month < 7)
            date = datetime(year, month, int(d[2])).date().isoformat()
        m = re.match(r"(?:\d{1,2}:\d{2}\s+)?(.+?) \([A-Z]{3}\)\s+v\s+(.+?) \([A-Z]{3}\)\s+(\d+-\d+.*)$", line)
        if not m or not date:
            continue
        score = m[3]
        if "a.e.t." in score:
            regulation = re.search(r"a\.e\.t\.\s*\((\d+)-(\d+),", score)
            if not regulation:
                raise ValueError(f"Missing regulation score: {line}")
            hs, aws = int(regulation[1]), int(regulation[2])
        else:
            hs, aws = map(int, re.match(r"(\d+)-(\d+)", score).groups())
        def name(n):
            # Source switches to formal FC names after 2021-22.
            aliases = {"Manchester City": "Manchester City FC", "Paris Saint-Germain": "Paris Saint-Germain FC",
                       "Liverpool": "Liverpool FC", "Chelsea": "Chelsea FC", "Real Madrid": "Real Madrid CF",
                       "Bayern München": "FC Bayern München", "FC Salzburg": "FC Red Bull Salzburg",
                       "Atalanta": "Atalanta BC", "Manchester United": "Manchester United FC",
                       "Dinamo Kiev": "FK Dynamo Kyiv"}
            return aliases.get(n.strip(), n.strip())
        rows.append(dict(date=date, season=f"{start_year}-{str(start_year+1)[-2:]}",
                         home_team=name(m[1]), away_team=name(m[2]), home_score=hs, away_score=aws,
                         neutral=int(stage in ("Finals, Final", "Final"))))
    expected = re.search(r"# Matches\s+(\d+)", text)
    if expected and len(rows) != int(expected[1]):
        raise ValueError(f"Incomplete UCL season {start_year}: parsed {len(rows)} / {expected[1]} matches")
    return rows


def _existing_matches(slug):
    """Installed matches and their recorded provenance (empty when nothing is installed)."""
    path = DATA / f"{config(slug)['key']}_matches.csv"
    if not path.exists():
        return pd.DataFrame(), {}
    meta = path.with_suffix(".json")
    return pd.read_csv(path), json.loads(meta.read_text(encoding="utf-8")) if meta.exists() else {}


def fetch_matches(slug, years):
    """Download completed matches season by season.

    Domestic leagues use football-data.co.uk (scores and shots). When that host
    cannot be reached, a season installed from it is kept as it is and a
    fallback feed supplies the rest: FPL-Elo-Insights (Premier League) or
    open-matchday (Bundesliga), both with scores and shots, otherwise
    OpenFootball (scores without shots). Nothing is estimated to fill a gap.
    """
    c = config(slug)
    existing, recorded = None, {}
    frames, urls, sources = [], [], {}
    for year in years:
        season = f"{year}-{str(year+1)[-2:]}"
        if slug == "champions-league":
            url = f"https://raw.githubusercontent.com/openfootball/champions-league/master/{season}/cl.txt"
            r = requests.get(url, timeout=30)
            if r.status_code == 404:
                print(f"{slug} {season}: not published by OpenFootball yet; skipped")
                continue
            r.raise_for_status()
            df = pd.DataFrame(parse_ucl(r.text, year))
            sources[season] = "OpenFootball"
        else:
            code = f"{year%100:02}{(year+1)%100:02}"
            url = f"https://www.football-data.co.uk/mmz4281/{code}/{c['csv']}.csv"
            try:
                r = requests.get(url, timeout=30)
                r.raise_for_status()
            except requests.RequestException as error:
                if existing is None:
                    existing, recorded = _existing_matches(slug)
                kept = existing[existing.season == season] if len(existing) else existing
                # Rows already installed keep the provenance recorded when they were downloaded.
                label = recorded.get("season_sources", {}).get(season) or recorded.get("source", "installed dataset")
                df, top_up_url, sources[season] = _fallback_season(slug, year, season, kept, label, error, year == max(years))
                if top_up_url:
                    urls.append(top_up_url)
                if not len(kept) or "football-data.co.uk" not in label:
                    url = None
            else:
                df = pd.read_csv(StringIO(r.text)).rename(columns={"HomeTeam": "home_team", "AwayTeam": "away_team", "FTHG": "home_score", "FTAG": "away_score", "HS": "home_shots", "AS": "away_shots"})
                df = df.dropna(subset=["Date", "home_team", "away_team", "home_score", "away_score"]).copy()
                df["date"] = pd.to_datetime(df["Date"], dayfirst=True, format="mixed").dt.strftime("%Y-%m-%d")
                df["season"], df["neutral"] = season, 0
                columns = ["date", "season", "home_team", "away_team", "home_score", "away_score", "neutral", "home_shots", "away_shots"]
                df = df[[col for col in columns if col in df]]
                sources[season] = "football-data.co.uk"
        frames.append(df)
        if url:
            urls.append(url)
    df = pd.concat([f for f in frames if len(f)]).sort_values("date", kind="stable").drop_duplicates(["season", "home_team", "away_team"] if slug != "champions-league" else ["date", "home_team", "away_team"])
    for col in ("home_score", "away_score", "neutral"):
        df[col] = df[col].astype(int)
    for col in ("home_shots", "away_shots"):
        if col in df:  # nullable integers keep scores-only rows empty instead of turning counts into floats
            df[col] = df[col].astype("Int64")
    if len(df) < 100:
        raise ValueError("Too few completed matches to train and evaluate a model")
    used = sorted({part for label in sources.values() for part in label.split(" + ")})
    metadata = {"kind": "historical", "source": " + ".join(used), "urls": urls, "target": "90-minute result, excluding extra time and penalties",
                "season_sources": sources, "latest_match": str(df.date.max())}
    if any("OpenFootball" in s for s in used) and slug != "champions-league":
        metadata["note"] = "Rows taken from OpenFootball have scores only; shots are empty for them and are not estimated."
    if "open-matchday" in used:
        from projects import open_matchday
        metadata["terms"] = open_matchday.TERMS
    write_dataset(slug, "matches", df, metadata)


def _fallback_season(slug, year, season, kept, label, error, latest):
    """(rows, source URL or None, source label) for a season football-data.co.uk did not serve.

    A feed with scores and shots (FPL-Elo-Insights, open-matchday) is preferred
    where one covers the competition; OpenFootball (scores only) is the last resort. Rows installed
    from football-data.co.uk are never replaced. Scores-only rows are replaced
    by the fuller record once a source with shots has the same fixture.
    """
    from projects import fpl_insights, open_matchday, openfootball
    complete = len(kept) and label == "football-data.co.uk"
    if latest or not complete:
        for feed in (fpl_insights, open_matchday):  # feeds with shots, most thoroughly checked first
            if slug not in feed.LEAGUES or year < feed.FIRST_YEAR:
                continue
            rows = pd.DataFrame(feed.fetch_season(slug, year))
            if len(rows):
                return _merge_fallback(slug, season, kept, label, rows, feed.LABEL,
                                       feed.season_url(slug, year), replace="football-data.co.uk" not in label)
    if slug in openfootball.LEAGUES:
        rows = pd.DataFrame(openfootball.fetch_season(slug, year))
        return _merge_fallback(slug, season, kept, label, rows, "OpenFootball (scores only)",
                               openfootball.season_url(slug, year), replace=False)
    if len(kept):
        print(f"{slug} {season}: football-data.co.uk unavailable ({error}); kept {len(kept)} installed rows")
        return kept, None, label
    raise error


def _merge_fallback(slug, season, kept, label, rows, source, url, replace):
    """Combine installed rows with a fallback feed.

    replace=False keeps every installed row and adds only fixtures that are not
    installed. replace=True (installed rows are scores-only) takes the feed's
    row for a shared fixture, after checking that both agree on the score.
    """
    if not len(kept):
        print(f"{slug} {season}: football-data.co.uk unavailable; {len(rows)} {source} rows")
        return rows, url, source
    if not len(rows):
        return kept, None, label
    key = ["home_team", "away_team"]
    if replace:
        both = kept.merge(rows, on=key, suffixes=("_installed", "_feed"))
        clash = both[(both.home_score_installed != both.home_score_feed) | (both.away_score_installed != both.away_score_feed)]
        if len(clash):
            raise ValueError(f"{slug} {season}: {source} disagrees with installed scores for "
                             + "; ".join(f"{r.home_team} v {r.away_team}" for r in clash.itertuples()))
        fed = set(zip(rows.home_team, rows.away_team))
        left = kept[[pair not in fed for pair in zip(kept.home_team, kept.away_team)]]
        print(f"{slug} {season}: football-data.co.uk unavailable; {len(rows)} {source} rows "
              f"({len(both)} replace installed scores-only rows, {len(rows) - len(both)} new), {len(left)} installed rows kept")
        return pd.concat([left, rows]), url, f"{label} + {source}" if len(left) else source
    have = set(zip(kept.home_team, kept.away_team))
    new = rows[[pair not in have for pair in zip(rows.home_team, rows.away_team)]]
    print(f"{slug} {season}: football-data.co.uk unavailable; kept {len(kept)} installed rows, added {len(new)} from {source}")
    if not len(new):
        return kept, None, label
    if source not in label:
        label += f" + {source}"
    return pd.concat([kept, new]), url, label


def import_players(slug, path, source):
    df = pd.read_csv(path)
    numeric = ["age", "minutes", "goals", "assists"]
    required = ["player", "team", "season", "position", *numeric, "market_value_eur_m"]
    missing = set(required) - set(df)
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
    if df[required].isna().any().any() or df.duplicated(["player", "season"]).any():
        raise ValueError("Player-seasons must be unique and required columns cannot be empty")
    for col in [*numeric, "market_value_eur_m"]:
        df[col] = pd.to_numeric(df[col], errors="raise")
        if not np.isfinite(df[col]).all() or (df[col] < 0).any():
            raise ValueError(f"{col} must contain finite, nonnegative numbers")
    if not df.position.isin(["GK", "DF", "MF", "FW"]).all():
        raise ValueError("Positions must be GK, DF, MF, or FW")
    if not df.season.astype(str).str.fullmatch(r"\d{4}-\d{2}").all():
        raise ValueError("Seasons must use YYYY-YY format")
    if len(df) < 30 or df.season.nunique() < 2 or df.player.nunique() < 8:
        raise ValueError("Import at least 30 player-seasons across two seasons and eight players")
    latest = df.sort_values("season").groupby("player").tail(1)
    if len(latest[(latest.position != "GK") & (latest.minutes >= 270)]) < 8:
        raise ValueError("Include at least eight outfield players with 270 minutes for scouting")
    final = df.season.max()
    if (df.season == final).sum() < 5 or (df.season < final).sum() < 20:
        raise ValueError("Include at least 20 training rows and five final-season holdout rows")
    write_dataset(slug, "players", df[required], {"kind": "imported", "source": source, "features": numeric, "seasons": sorted(df.season.unique()),
                  "note": "User-supplied season statistics and reference market values. Market value is not a completed transfer fee."})


def fetch_fixtures(slug, year):
    """Scheduled fixtures from football-data.org (needs a token), else from open-matchday where it covers the competition."""
    from projects import open_matchday
    from projects.fetch_players import _token
    token = _token()
    if token:
        r = requests.get(f"https://api.football-data.org/v4/competitions/{config(slug)['code']}/matches",
                         params={"status": "SCHEDULED,TIMED"}, headers={"X-Auth-Token": token}, timeout=30)
        r.raise_for_status()
        payload = {"source": "football-data.org", "matches": r.json().get("matches", [])}
    elif slug in open_matchday.LEAGUES:
        payload = {"source": open_matchday.LABEL, "url": open_matchday.file_url(slug, year, "fixtures"),
                   "terms": open_matchday.TERMS, "matches": open_matchday.fetch_fixtures(slug, year)}
        if not payload["matches"]:
            raise ValueError("The fixture feed returned no scheduled matches; keeping the installed fixtures")
    else:
        raise ValueError("Set FOOTBALL_DATA_TOKEN in .env to download scheduled fixtures")
    payload["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    path = DATA / f"{config(slug)['key']}_fixtures.json"
    DATA.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload), encoding="utf-8")
    temporary.replace(path)
    print(f"Saved {len(payload['matches'])} scheduled fixtures from {payload['source']}")


def fetch_availability(slug, year):
    """Snapshot of injured, doubtful and suspended players (Premier League only so far)."""
    from projects import fpl_insights
    rows, gameweek = fpl_insights.fetch_availability(slug, year)
    df = pd.DataFrame(rows, columns=["player", "full_name", "team", "position", "status", "chance_of_playing", "news", "minutes"])
    if not len(df):
        raise ValueError("The availability feed returned no flagged players; keeping the installed snapshot")
    df["chance_of_playing"] = df["chance_of_playing"].astype("Int64")
    write_dataset(slug, "availability", df, {
        "kind": "snapshot", "source": fpl_insights.LABEL, "urls": fpl_insights.availability_urls(year),
        "season": f"{year}-{str(year + 1)[-2:]}", "gameweek": gameweek, "counts": df.status.value_counts().to_dict(),
        "note": "Premier League availability flags (injured, doubtful, suspended) as published at the retrieval time. "
                "A snapshot, not a history; it is not an input to any model."})


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("competition", choices=[*COMPETITIONS, "all"])
    p.add_argument("--years", nargs="+", type=int, default=[2021, 2022, 2023, 2024, 2025, 2026])
    p.add_argument("--players", type=Path, help="Import observed player-season CSV instead of downloading matches")
    p.add_argument("--source", help="Required attribution for an imported player dataset")
    p.add_argument("--fixtures", action="store_true", help="Refresh fixtures from football-data.org (token) or open-matchday")
    p.add_argument("--availability", action="store_true", help="Refresh the injury and suspension snapshot (Premier League)")
    a = p.parse_args()
    if a.players and (not a.source or a.competition == "all"):
        p.error("Player imports require one competition and --source")
    for slug in (COMPETITIONS if a.competition == "all" else [a.competition]):
        if a.players:
            import_players(slug, a.players, a.source)
        elif a.fixtures:
            fetch_fixtures(slug, max(a.years))
        elif a.availability:
            fetch_availability(slug, max(a.years))
        else:
            fetch_matches(slug, a.years)
