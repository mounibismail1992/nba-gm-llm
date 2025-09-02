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


def fetch_team_contracts(team_abbr: str, session: requests.Session | None = None) -> Dict[str, Any]:
    """Fetch team contracts table and derive per-player status and years remaining.

    Returns a dict with keys:
      - team: team abbr
      - base_year_label: e.g., '2025-26' for y1
      - base_year: e.g., 2026 (int)
      - players: list of dicts with
          player, player_url, player_id,
          current_salary (int|None), current_salary_text (str),
          years_remaining (int),
          status (str: one of guaranteed, non_guaranteed, player_option, team_option),
          flags (list[str]) among {non_guaranteed, player_option, team_option}
    """
    sess = session or requests.Session()
    url = f"https://www.basketball-reference.com/contracts/{team_abbr}.html"
    resp = sess.get(url, headers=DEFAULT_HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", id="contracts")
    if not table:
        # Some pages might be commented; attempt to extract from wrapper
        wrapper = soup.find(id="all_contracts")
        if wrapper:
            for el in wrapper.descendants:
                if isinstance(el, Comment):
                    inner = BeautifulSoup(el, "html.parser")
                    table = inner.find("table", id="contracts")
                    if table:
                        break
    if not table:
        return {"team": team_abbr, "base_year_label": None, "base_year": None, "players": []}

    # Map header labels for y1..y6
    header_map: Dict[str, str] = {}
    thead = table.find("thead")
    if thead:
        header_row = thead.find_all("tr")[-1] if thead.find_all("tr") else None
        if header_row:
            for th in header_row.find_all("th"):
                ds = th.get("data-stat")
                if ds and ds.startswith("y"):
                    header_map[ds] = th.get_text(strip=True)
    base_label = header_map.get("y1")
    base_year = None
    if base_label and "-" in base_label:
        try:
            tail = base_label.split("-")[-1]
            if len(tail) == 2:
                base_year = 2000 + int(tail)
            else:
                base_year = int(tail)
        except Exception:
            base_year = None

    players: List[Dict[str, Any]] = []
    tbody = table.find("tbody")
    if not tbody:
        return {"team": team_abbr, "base_year_label": base_label, "base_year": base_year, "players": players}

    year_cols = [f"y{i}" for i in range(1, 7)]
    for tr in tbody.find_all("tr"):
        th = tr.find("th", {"data-stat": "player"})
        if not th:
            continue
        a = th.find("a")
        player = th.get_text(strip=True)
        href = a.get("href") if a else None
        player_url = ("https://www.basketball-reference.com" + href) if href else None
        player_id = th.get("csk")

        flags: List[str] = []
        years_remaining = 0
        current_salary = None
        current_salary_text = ""

        for idx, col in enumerate(year_cols):
            td = tr.find("td", {"data-stat": col})
            if not td:
                continue
            text = td.get_text(strip=True)
            csk = td.get("csk")
            has_value = bool(text) or (csk is not None and csk != "")
            if has_value:
                years_remaining += 1
                if idx == 0:  # current season column
                    current_salary_text = text
                    try:
                        current_salary = int(csk) if csk not in (None, "") else None
                    except ValueError:
                        current_salary = None
            # flags
            classes = td.get("class", [])
            if classes and any("salary-pl" == c for c in classes):
                if "player_option" not in flags:
                    flags.append("player_option")
            if classes and any("salary-tm" == c for c in classes):
                if "team_option" not in flags:
                    flags.append("team_option")
            if td.find("em") and "non_guaranteed" not in flags:
                flags.append("non_guaranteed")

        # Derive primary status
        if "player_option" in flags:
            status = "player_option"
        elif "team_option" in flags:
            status = "team_option"
        elif "non_guaranteed" in flags:
            status = "non_guaranteed"
        else:
            status = "guaranteed"

        players.append({
            "player": player,
            "player_url": player_url,
            "player_id": player_id,
            "current_salary": current_salary,
            "current_salary_text": current_salary_text,
            "years_remaining": years_remaining,
            "status": status,
            "flags": flags,
        })

    return {"team": team_abbr, "base_year_label": base_label, "base_year": base_year, "players": players}
