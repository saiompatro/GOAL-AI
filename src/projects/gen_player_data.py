"""Generate the bundled Premier League player-season dataset.

The three Premier League projects (transfer-value predictor, match-outcome
predictor, player-scouting system) need a player-level statistics table with a
market/transfer value column. No permissively licensed, ready-to-use table of
per-player PL stats *plus* transfer values ships in this repo, so this script
synthesises a realistic, deterministic one (real player + club names, plausible
correlated stats) that lets every project run out of the box.

`fetch_players.py` is the real-data path: it pulls live rosters from
football-data.org and is what you would use in production. This generator is
the offline fallback so a fresh clone works with no API token.

Run:  python -m projects.gen_player_data      (writes data/players/premier_league_players.csv)
"""
import csv
import os
import random

from projects.common import PLAYERS_CSV, FEATURE_COLUMNS  # noqa: F401  (paths + schema)

# A representative slice of Premier League squads. Kept intentionally small and
# hand-curated so the names are real and the positions are right; the per-season
# statistics are generated below.
SQUADS = {
    "Arsenal": [
        ("Bukayo Saka", "FW", 23), ("Martin Odegaard", "MF", 26),
        ("Gabriel Martinelli", "FW", 24), ("Kai Havertz", "FW", 26),
        ("Declan Rice", "MF", 26), ("William Saliba", "DF", 24),
        ("Gabriel Magalhaes", "DF", 27), ("Ben White", "DF", 27),
        ("Leandro Trossard", "FW", 30), ("David Raya", "GK", 29),
    ],
    "Manchester City": [
        ("Erling Haaland", "FW", 25), ("Phil Foden", "MF", 25),
        ("Bernardo Silva", "MF", 30), ("Rodri", "MF", 29),
        ("Josko Gvardiol", "DF", 24), ("Ruben Dias", "DF", 28),
        ("Kyle Walker", "DF", 35), ("Jeremy Doku", "FW", 23),
        ("Savinho", "FW", 21), ("Ederson", "GK", 32),
    ],
    "Liverpool": [
        ("Mohamed Salah", "FW", 33), ("Luis Diaz", "FW", 28),
        ("Cody Gakpo", "FW", 26), ("Dominik Szoboszlai", "MF", 25),
        ("Alexis Mac Allister", "MF", 27), ("Virgil van Dijk", "DF", 34),
        ("Trent Alexander-Arnold", "DF", 27), ("Ibrahima Konate", "DF", 26),
        ("Ryan Gravenberch", "MF", 23), ("Alisson", "GK", 33),
    ],
    "Manchester United": [
        ("Bruno Fernandes", "MF", 31), ("Marcus Rashford", "FW", 28),
        ("Alejandro Garnacho", "FW", 21), ("Rasmus Hojlund", "FW", 23),
        ("Kobbie Mainoo", "MF", 20), ("Lisandro Martinez", "DF", 28),
        ("Diogo Dalot", "DF", 26), ("Luke Shaw", "DF", 30),
        ("Casemiro", "MF", 34), ("Andre Onana", "GK", 29),
    ],
    "Chelsea": [
        ("Cole Palmer", "FW", 23), ("Nicolas Jackson", "FW", 24),
        ("Enzo Fernandez", "MF", 25), ("Moises Caicedo", "MF", 24),
        ("Christopher Nkunku", "FW", 28), ("Reece James", "DF", 26),
        ("Levi Colwill", "DF", 23), ("Marc Cucurella", "DF", 27),
        ("Noni Madueke", "FW", 23), ("Robert Sanchez", "GK", 28),
    ],
    "Tottenham Hotspur": [
        ("Son Heung-min", "FW", 33), ("James Maddison", "MF", 29),
        ("Dejan Kulusevski", "MF", 25), ("Brennan Johnson", "FW", 25),
        ("Cristian Romero", "DF", 28), ("Micky van de Ven", "DF", 24),
        ("Destiny Udogie", "DF", 23), ("Pape Matar Sarr", "MF", 23),
        ("Dominic Solanke", "FW", 28), ("Guglielmo Vicario", "GK", 29),
    ],
    "Newcastle United": [
        ("Alexander Isak", "FW", 26), ("Anthony Gordon", "FW", 25),
        ("Bruno Guimaraes", "MF", 28), ("Sandro Tonali", "MF", 25),
        ("Sven Botman", "DF", 26), ("Kieran Trippier", "DF", 35),
        ("Fabian Schar", "DF", 34), ("Joelinton", "MF", 29),
        ("Harvey Barnes", "FW", 28), ("Nick Pope", "GK", 33),
    ],
    "Aston Villa": [
        ("Ollie Watkins", "FW", 30), ("Morgan Rogers", "MF", 23),
        ("John McGinn", "MF", 31), ("Youri Tielemans", "MF", 28),
        ("Ezri Konsa", "DF", 28), ("Pau Torres", "DF", 29),
        ("Lucas Digne", "DF", 32), ("Leon Bailey", "FW", 28),
        ("Amadou Onana", "MF", 24), ("Emiliano Martinez", "GK", 33),
    ],
    "Brighton & Hove Albion": [
        ("Kaoru Mitoma", "FW", 28), ("Danny Welbeck", "FW", 35),
        ("Georginio Rutter", "FW", 23), ("Carlos Baleba", "MF", 21),
        ("Jack Hinshelwood", "MF", 20), ("Lewis Dunk", "DF", 34),
        ("Jan Paul van Hecke", "DF", 25), ("Pervis Estupinan", "DF", 27),
        ("Yankuba Minteh", "FW", 21), ("Bart Verbruggen", "GK", 23),
    ],
    "West Ham United": [
        ("Jarrod Bowen", "FW", 29), ("Lucas Paqueta", "MF", 28),
        ("Mohammed Kudus", "FW", 25), ("Tomas Soucek", "MF", 30),
        ("Edson Alvarez", "MF", 28), ("Max Kilman", "DF", 28),
        ("Aaron Wan-Bissaka", "DF", 28), ("Emerson", "DF", 31),
        ("Niclas Fullkrug", "FW", 32), ("Alphonse Areola", "GK", 32),
    ],
    "Crystal Palace": [
        ("Eberechi Eze", "MF", 27), ("Jean-Philippe Mateta", "FW", 28),
        ("Ismaila Sarr", "FW", 27), ("Adam Wharton", "MF", 21),
        ("Daniel Munoz", "DF", 29), ("Marc Guehi", "DF", 25),
        ("Maxence Lacroix", "DF", 25), ("Tyrick Mitchell", "DF", 26),
        ("Will Hughes", "MF", 30), ("Dean Henderson", "GK", 28),
    ],
    "Everton": [
        ("Iliman Ndiaye", "FW", 25), ("Dwight McNeil", "MF", 26),
        ("Abdoulaye Doucoure", "MF", 32), ("Idrissa Gueye", "MF", 36),
        ("Jarrad Branthwaite", "DF", 23), ("James Tarkowski", "DF", 33),
        ("Vitalii Mykolenko", "DF", 26), ("Jake O'Brien", "DF", 24),
        ("Beto", "FW", 27), ("Jordan Pickford", "GK", 31),
    ],
}

# per-position statistical archetypes: mean per-90 rates + minutes tendency.
# (goals90, assists90, shots90, key_passes90, dribbles90, tackles90, interceptions90)
ARCHETYPE = {
    "FW": dict(goals90=0.45, assists90=0.20, shots90=2.8, key_passes90=1.3,
               dribbles90=1.8, tackles90=0.6, interceptions90=0.4, base_minutes=2300),
    "MF": dict(goals90=0.14, assists90=0.22, shots90=1.4, key_passes90=1.9,
               dribbles90=1.3, tackles90=2.0, interceptions90=1.3, base_minutes=2500),
    "DF": dict(goals90=0.05, assists90=0.08, shots90=0.5, key_passes90=0.6,
               dribbles90=0.6, tackles90=2.4, interceptions90=1.8, base_minutes=2700),
    "GK": dict(goals90=0.0, assists90=0.02, shots90=0.05, key_passes90=0.2,
               dribbles90=0.1, tackles90=0.1, interceptions90=0.3, base_minutes=2900),
}

SEASONS = ["2022-23", "2023-24", "2024-25"]


def _age_factor(age):
    """Value/output multiplier by age — footballers peak ~25-27."""
    return max(0.45, 1.0 - ((age - 26) ** 2) * 0.012)


def _quality(rng):
    """A player's underlying quality tier, lognormal-ish so a few stars dominate."""
    return max(0.35, rng.gauss(1.0, 0.35))


def generate(seed=42):
    rng = random.Random(seed)
    rows = []
    for team, squad in SQUADS.items():
        for name, pos, base_age in squad:
            quality = _quality(rng)
            for i, season in enumerate(SEASONS):
                age = base_age - (len(SEASONS) - 1 - i)  # older in later seasons
                arch = ARCHETYPE[pos]
                minutes = int(max(500, rng.gauss(arch["base_minutes"], 500)
                                  * min(1.15, quality)))
                nineties = minutes / 90.0
                af = _age_factor(age)

                def stat(rate, spread=0.18):
                    # tight, mostly-multiplicative noise so per-90 rates stay
                    # position-coherent (clean clusters), with a small floor.
                    per90 = max(0.0, rate * quality * af * rng.gauss(1.0, spread)
                                + rng.uniform(0.0, rate * 0.15))
                    return round(per90 * nineties)

                goals = stat(arch["goals90"])
                assists = stat(arch["assists90"])
                shots = stat(arch["shots90"])
                key_passes = stat(arch["key_passes90"])
                dribbles = stat(arch["dribbles90"])
                tackles = stat(arch["tackles90"])
                interceptions = stat(arch["interceptions90"])

                # market value (EUR millions): driven by output, minutes, age,
                # position premium (attackers cost more) and quality tier, with noise.
                pos_premium = {"FW": 1.35, "MF": 1.15, "DF": 0.9, "GK": 0.7}[pos]
                output = goals * 2.2 + assists * 1.4 + (shots + key_passes) * 0.15
                base = (output * 1.1 + nineties * 1.6) * pos_premium
                youth_bonus = max(0.0, (27 - age)) * 1.4
                # 0.42 scale keeps values in a realistic PL band (~4–180 €m)
                value = max(0.8, (base + youth_bonus) * quality
                            * rng.uniform(0.82, 1.18) * 0.42)
                value_eur_m = round(value, 1)

                rows.append({
                    "player": name, "team": team, "season": season,
                    "position": pos, "age": age, "minutes": minutes,
                    "goals": goals, "assists": assists, "shots": shots,
                    "key_passes": key_passes, "dribbles": dribbles,
                    "tackles": tackles, "interceptions": interceptions,
                    "market_value_eur_m": value_eur_m,
                })
    return rows


def main():
    rows = generate()
    os.makedirs(os.path.dirname(PLAYERS_CSV), exist_ok=True)
    fields = ["player", "team", "season", "position", "age", "minutes",
              "goals", "assists", "shots", "key_passes", "dribbles",
              "tackles", "interceptions", "market_value_eur_m"]
    with open(PLAYERS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} player-seasons "
          f"({len(SQUADS)} clubs) -> {PLAYERS_CSV}")


if __name__ == "__main__":
    main()
