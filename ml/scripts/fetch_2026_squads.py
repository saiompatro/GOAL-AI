"""Build the approved FIFA 2026 squad player pool CSV.

The source page aggregates announced World Cup squads and cites the national
associations/FIFA where available. The output is intentionally a 2026-only raw
file so the Streamlit player tabs never fall back to historical World Cup
rosters.
"""
from __future__ import annotations

import csv
import re
import sys
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "raw" / "fifa_2026_squads.csv"
SOURCE_URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads"
USER_AGENT = "GoalAI/1.0 (+https://github.com/)"
POSITION_RE = re.compile(r"(GK|DF|MF|FW)")
DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
AGE_RE = re.compile(r"aged\s+(\d+)")


class SquadTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_heading = False
        self.heading_level = ""
        self.heading_text: list[str] = []
        self.current_team = ""

        self.in_table = False
        self.table_depth = 0
        self.current_table_team = ""
        self.in_row = False
        self.in_cell = False
        self.cell_text: list[str] = []
        self.row_cells: list[str] = []
        self.rows: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        classes = set((attrs_dict.get("class") or "").split())

        if tag in {"h2", "h3"}:
            self.in_heading = True
            self.heading_level = tag
            self.heading_text = []
            return

        if tag == "table" and "wikitable" in classes:
            self.in_table = True
            self.table_depth = 1
            self.current_table_team = self.current_team
            return

        if self.in_table and tag == "table":
            self.table_depth += 1
            return

        if self.in_table and tag == "tr":
            self.in_row = True
            self.row_cells = []
            return

        if self.in_row and tag in {"td", "th"}:
            self.in_cell = True
            self.cell_text = []

    def handle_endtag(self, tag: str) -> None:
        if self.in_heading and tag == self.heading_level:
            text = " ".join("".join(self.heading_text).split())
            if self.heading_level == "h3" and text:
                self.current_team = re.sub(r"\s*\[.*?\]\s*$", "", text)
            self.in_heading = False
            return

        if self.in_cell and tag in {"td", "th"}:
            self.row_cells.append(" ".join("".join(self.cell_text).split()))
            self.in_cell = False
            return

        if self.in_row and tag == "tr":
            self._finish_row()
            self.in_row = False
            return

        if self.in_table and tag == "table":
            self.table_depth -= 1
            if self.table_depth == 0:
                self.in_table = False
                self.current_table_team = ""

    def handle_data(self, data: str) -> None:
        if self.in_cell:
            self.cell_text.append(data)
        elif self.in_heading:
            self.heading_text.append(data)

    def _finish_row(self) -> None:
        if len(self.row_cells) < 7 or self.row_cells[0].lower() == "no.":
            return
        if not self.current_table_team:
            return
        _, pos_text, player, birth_text, caps, goals, club = self.row_cells[:7]
        position_match = POSITION_RE.search(pos_text)
        date_match = DATE_RE.search(birth_text)
        age_match = AGE_RE.search(birth_text)
        player = re.sub(r"\s*\(\s*captain\s*\)\s*", "", player, flags=re.IGNORECASE).strip()
        if not player or not position_match:
            return
        self.rows.append(
            {
                "team": self.current_table_team,
                "player_name": player,
                "position": position_match.group(1),
                "date_of_birth": date_match.group(1) if date_match else "",
                "age": age_match.group(1) if age_match else "",
                "caps": _clean_int(caps),
                "goals": _clean_int(goals),
                "club": club,
            }
        )


def _clean_int(value: str) -> str:
    match = re.search(r"-?\d+", value.replace(",", ""))
    return match.group(0) if match else "0"


def fetch_html() -> str:
    req = Request(SOURCE_URL, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def squad_status(team_rows: list[dict[str, str]]) -> str:
    return "official_squad" if len(team_rows) <= 26 else "provisional_squad"


def main() -> int:
    parser = SquadTableParser()
    parser.feed(fetch_html())
    if not parser.rows:
        print(f"No squad rows found at {SOURCE_URL}", file=sys.stderr)
        return 1

    now = datetime.now(UTC).date().isoformat()
    rows: list[dict[str, str]] = []
    for team in sorted({row["team"] for row in parser.rows}):
        team_rows = [row for row in parser.rows if row["team"] == team]
        status = squad_status(team_rows)
        for row in team_rows:
            rows.append(
                {
                    **row,
                    "squad_status": status,
                    "source_url": SOURCE_URL,
                    "retrieved_date": now,
                }
            )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    teams = len({row["team"] for row in rows})
    print(f"Wrote {len(rows):,} players across {teams} teams to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
