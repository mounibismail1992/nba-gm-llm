from __future__ import annotations
import time
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from ..config import DEFAULT_HEADERS


TEAM_ABBRS = [
    "ATL","BOS","BRK","CHI","CHO","CLE","DAL","DEN","DET","GSW","HOU","IND","LAC","LAL","MEM","MIA","MIL","MIN","NOP","NYK","OKC","ORL","PHI","PHO","POR","SAC","SAS","TOR","UTA","WAS"
]


def fetch_team_roster(team_abbr: str, year: int, session: requests.Session | None = None) -> List[Dict[str, Any]]:
    sess = session or requests.Session()
    url = f"https://www.basketball-reference.com/teams/{team_abbr}/{year}.html"
    resp = sess.get(url, headers=DEFAULT_HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", id="roster")
    roster: List[Dict[str, Any]] = []
    if not table:
        return roster
    for tr in table.tbody.find_all("tr"):
        cells = tr.find_all("td")
        if not cells:
            continue
        row = {c.get("data-stat"): (c.get_text(strip=True)) for c in cells}
        # player id
        a = tr.find("a")
        if a and a.get("href"):
            row["player_url"] = "https://www.basketball-reference.com" + a.get("href")
        roster.append(row)
    return roster


def fetch_all_rosters(year: int) -> Dict[str, List[Dict[str, Any]]]:
    sess = requests.Session()
    out: Dict[str, List[Dict[str, Any]]] = {}
    for abbr in TEAM_ABBRS:
        try:
            out[abbr] = fetch_team_roster(abbr, year, session=sess)
            time.sleep(0.5)
        except Exception:
            out[abbr] = []
    return out

