"""Live news sentiment for a national team via Google News RSS (no API key).

Fetches recent headlines for "<team> national football team", scores them with
a small football-tuned lexicon, and returns a score in [-1, 1]. This feeds the
morale signal alongside the results-based momentum from features.py.
Fails soft: returns 0.0 (neutral) with headlines=[] if offline/blocked.
"""
import re
import unicodedata
import requests
import xml.etree.ElementTree as ET


def _ascii(s):
    return "".join(c for c in unicodedata.normalize("NFD", str(s))
                   if unicodedata.category(c) != "Mn")

POS = {"win", "wins", "won", "victory", "triumph", "boost", "confident", "confidence",
       "fit", "returns", "return", "strong", "stunning", "brilliant", "hope", "hopes",
       "favourite", "favorites", "favourites", "record", "unbeaten", "top", "soar",
       "celebrate", "dominant", "comfortable", "thrash", "cruise", "morale"}
NEG = {"injury", "injured", "doubt", "doubts", "crisis", "lose", "loses", "lost",
       "defeat", "blow", "out", "ruled", "scandal", "row", "sacked", "pressure",
       "struggle", "struggles", "fear", "fears", "worry", "worries", "suspended",
       "ban", "banned", "exit", "collapse", "slump", "criticism", "turmoil"}


INJURY = {"injury", "injured", "ruled", "sidelined", "hamstring", "knee", "ankle",
          "surgery", "scan", "fitness", "doubt", "doubtful", "miss", "misses",
          "withdraw", "withdrawn", "suspended", "banned", "out"}


def score_titles(titles):
    """Lexicon sentiment in [-1, 1] plus injury-mention ratio for headlines."""
    score, n, inj = 0.0, 0, 0
    for t in titles:
        words = set(re.findall(r"[a-z']+", t.lower()))
        s = len(words & POS) - len(words & NEG)
        if s:
            score += max(-1, min(1, s))
            n += 1
        if words & INJURY:
            inj += 1
    return (score / max(n, 1)) if titles else 0.0, (inj / len(titles)) if titles else 0.0


# Strong phrases that indicate a player is OUT of the tournament (not mere injury
# doubt). Require several to co-occur across headlines before acting, so a single
# loose match can't drop a player.
WITHDRAW_PHRASES = [
    "out of the world cup", "out of world cup", "ruled out of the world cup",
    "ruled out of world cup", "pulls out of", "pull out of", "pulled out of",
    "withdrawn from", "withdraws from", "withdrawal from", "sent home",
    "miss the world cup", "will miss the world cup", "misses the world cup",
    "axed from", "dropped from the", "out for the rest of",
    "international retirement", "retires from international", "ends career",
    "out of the tournament", "ruled out for the tournament",
]
# headlines about the *replacement* player, which must not flag the replacer
REPLACER_HINTS = ["to replace", "replaces", "replacement for", "called up", "in for"]
# context that means a PRE-tournament window, not the finals -> never a withdrawal
NOT_FINALS = ["qualif", "friendly", "friendlies", "nations league", "warm-up",
              "warmup", "tune-up", "play-off", "playoff", "play off"]
# the headline must show it's about the finals (or a career-ending exit)
FINALS_CTX = ["world cup", "the tournament", "international retirement",
              "retires from international", "ends career", "ends his career"]


def is_withdrawn(player, team, max_items=14):
    """Conservative: True only if >=2 distinct headlines confirm the player is
    out of the World Cup *finals* (not a qualifier/friendly window, not a
    replacement headline). Returns (withdrawn, count, evidence_headline)."""
    surname = re.sub(r"[^a-z ]", "", _ascii(player).lower()).split()[-1] if player else ""
    titles = news_headlines(f'"{player}" {team} world cup', max_items)
    hits = []
    for t in titles:
        tl = _ascii(t).lower()
        if surname and surname not in tl:
            continue
        if any(h in tl for h in REPLACER_HINTS):    # describes the replacer, skip
            continue
        if any(x in tl for x in NOT_FINALS):        # qualifier/friendly window, skip
            continue
        if not any(c in tl for c in FINALS_CTX):    # not clearly about the finals, skip
            continue
        if any(ph in tl for ph in WITHDRAW_PHRASES):
            hits.append(t)
    return (len(hits) >= 2), len(hits), (hits[0] if hits else "")


def player_sentiment(player, team, max_items=12):
    """News sentiment for one key player; injury talk weighs in negatively."""
    titles = news_headlines(f'"{player}" {team} world cup', max_items)
    s, inj_ratio = score_titles(titles)
    # injury chatter is the most predictive bad news a squad can have
    s -= 0.8 * inj_ratio
    return max(-1.0, min(1.0, s)), inj_ratio > 0.25, titles


def news_items(query, max_items=25):
    """Fresh Google News RSS items as (title, pubdate) — pubdate may be None."""
    from email.utils import parsedate_to_datetime
    url = ("https://news.google.com/rss/search?q=" + requests.utils.quote(query)
           + "&hl=en-US&gl=US&ceid=US:en")
    try:
        xml = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"}).text
        root = ET.fromstring(xml)
    except Exception:
        return []
    out = []
    for i in list(root.iter("item"))[:max_items]:
        title = i.findtext("title", "")
        try:
            dt = parsedate_to_datetime(i.findtext("pubDate", ""))
        except Exception:
            dt = None
        out.append((title, dt))
    return out


def news_headlines(query, max_items=25):
    """Fresh Google News RSS headlines for an arbitrary query (no key, no cache)."""
    return [t for t, _ in news_items(query, max_items)]


def player_report(player, team, max_items=14):
    """One news fetch per player -> sentiment + injury status + injury date.
    Used by the live layer so each key player is queried only once.
    Returns dict: sentiment, injury_talk, injury_date (ISO or None),
    injury_headline, headlines."""
    items = news_items(f'"{player}" {team} world cup', max_items)
    titles = [t for t, _ in items]
    s, inj_ratio = score_titles(titles)
    s -= 0.8 * inj_ratio                                  # injury talk weighs negative
    surname = re.sub(r"[^a-z ]", "", _ascii(player).lower()).split()[-1] if player else ""
    inj_dated = []
    for t, dt in items:
        tl = _ascii(t).lower()
        if surname and surname not in tl:
            continue
        if any(h in tl for h in REPLACER_HINTS):          # about a replacement, skip
            continue
        if set(re.findall(r"[a-z']+", tl)) & INJURY:
            inj_dated.append((dt, t))
    injured = inj_ratio > 0.25 and bool(inj_dated)
    date_iso, headline = None, ""
    if inj_dated:
        dated = [x for x in inj_dated if x[0] is not None]
        if dated:
            first_dt, headline = min(dated)                # earliest report = when it broke
            date_iso = first_dt.date().isoformat()
        else:
            headline = inj_dated[0][1]
    return {"sentiment": max(-1.0, min(1.0, s)), "injury_talk": injured,
            "injury_date": date_iso, "injury_headline": headline, "headlines": titles}


def team_sentiment(team, max_items=25):
    titles = news_headlines(f'"{team}" national football team world cup', max_items)
    if not titles:
        return 0.0, []
    score, n = 0.0, 0
    for t in titles:
        words = set(re.findall(r"[a-z']+", t.lower()))
        s = len(words & POS) - len(words & NEG)
        if s:
            score += max(-1, min(1, s))
            n += 1
    return (score / max(n, 1)) if titles else 0.0, titles


if __name__ == "__main__":
    for team in ["Brazil", "England"]:
        s, heads = team_sentiment(team)
        print(f"{team}: sentiment {s:+.2f} from {len(heads)} headlines")
        for h in heads[:3]:
            print("   -", h)
