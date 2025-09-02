from __future__ import annotations
import time
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup, Comment
from ..config import DEFAULT_HEADERS
from datetime import datetime


TEAM_ABBRS = [
    "ATL","BOS","BRK","CHI","CHO","CLE","DAL","DEN","DET","GSW","HOU","IND","LAC","LAL","MEM","MIA","MIL","MIN","NOP","NYK","OKC","ORL","PHI","PHO","POR","SAC","SAS","TOR","UTA","WAS"
]


def current_bbr_year(now: datetime | None = None) -> int:
    """Return the BBR year corresponding to the upcoming or current season.

    Heuristic: if month >= 7 (July), use next calendar year; else use current year.
    Example: Sept 2025 -> 2026; Jan 2025 -> 2025.
    """
    dt = now or datetime.utcnow()
    return dt.year + 1 if dt.month >= 7 else dt.year


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


def fetch_team_salaries(team_abbr: str, year: int, session: requests.Session | None = None) -> List[Dict[str, Any]]:
    """Fetch salaries table from a Basketball-Reference team season page.

    Returns a list of rows with keys: player, player_url, player_id, salary, salary_text, team, year.
    """
    sess = session or requests.Session()
    url = f"https://www.basketball-reference.com/teams/{team_abbr}/{year}.html"
    resp = sess.get(url, headers=DEFAULT_HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    # Salaries table is often within a commented HTML block inside #all_salaries2
    container = soup.find(id="all_salaries2")
    table = None
    if container:
        table = container.find("table", id="salaries2")
        if table is None:
            for el in container.children:
                if isinstance(el, Comment):
                    inner = BeautifulSoup(el, "html.parser")
                    table = inner.find("table", id="salaries2")
                    if table is not None:
                        break
    if table is None:
        table = soup.find("table", id="salaries2")
    rows: List[Dict[str, Any]] = []
    if not table or not table.tbody:
        return rows
    for tr in table.tbody.find_all("tr"):
        tds = tr.find_all("td")
        if not tds:
            continue
        # Map by data-stat
        data: Dict[str, Any] = {td.get("data-stat"): td for td in tds}
        player_cell = data.get("player")
        salary_cell = data.get("salary")
        if not player_cell:
            continue
        a = player_cell.find("a")
        player_name = player_cell.get_text(strip=True)
        player_href = a.get("href") if a else None
        player_id = player_cell.get("data-append-csv")
        # Salary may be empty (two-way/non-guaranteed)
        salary_text = salary_cell.get_text(strip=True) if salary_cell else ""
        csk = salary_cell.get("csk") if salary_cell else None
        try:
            salary = int(csk) if csk is not None and csk != "" else None
        except ValueError:
            salary = None
        row = {
            "player": player_name,
            "player_url": ("https://www.basketball-reference.com" + player_href) if player_href else None,
            "player_id": player_id,
            "salary": salary,
            "salary_text": salary_text,
            "team": team_abbr,
            "year": year,
        }
        rows.append(row)
    return rows


def fetch_all_salaries(year: int) -> Dict[str, List[Dict[str, Any]]]:
    sess = requests.Session()
    out: Dict[str, List[Dict[str, Any]]] = {}
    for abbr in TEAM_ABBRS:
        try:
            out[abbr] = fetch_team_salaries(abbr, year, session=sess)
            time.sleep(0.5)
        except Exception:
            out[abbr] = []
    return out
