from __future__ import annotations
import time
from typing import Iterable, Dict, Any, List
from datetime import datetime
from nba_api.stats.static import teams, players
from nba_api.stats.endpoints import teamgamelog, leaguedashplayerstats
from nba_api.stats.library.parameters import Season


def list_teams() -> List[Dict[str, Any]]:
    return teams.get_teams()


def list_players(active_only: bool = True) -> List[Dict[str, Any]]:
    return players.get_players() if not active_only else [p for p in players.get_players() if p.get("is_active")]


def fetch_team_gamelogs(team_ids: Iterable[int], season: str, sleep: float = 0.6) -> Dict[int, List[Dict[str, Any]]]:
    out: Dict[int, List[Dict[str, Any]]] = {}
    for tid in team_ids:
        gl = teamgamelog.TeamGameLog(team_id=tid, season=Season(season)).get_normalized_dict()
        out[tid] = gl.get("TeamGameLog", [])
        time.sleep(sleep)  # be polite
    return out


def _season_label_from_end_year(end_year: int) -> str:
    return f"{end_year-1}-{str(end_year)[-2:]}"


def last_n_seasons_labels(n: int = 5, now: datetime | None = None) -> List[str]:
    """Return labels for the last n completed NBA seasons.

    Heuristic: if month >= July, the most recent completed season ends this calendar year;
    otherwise it ended last calendar year.
    """
    dt = now or datetime.utcnow()
    latest_end = dt.year if dt.month >= 7 else dt.year - 1
    end_years = [latest_end - i for i in range(n)]
    return [_season_label_from_end_year(y) for y in end_years]


def get_active_player_ids() -> List[int]:
    return [p["id"] for p in list_players(active_only=True)]


def fetch_league_player_stats_by_season(season: str) -> List[Dict[str, Any]]:
    """Fetch league-wide player per-season stats (per nba.com public endpoint).

    Uses LeagueDashPlayerStats for the specified season label (e.g., '2024-25').
    """
    resp = leaguedashplayerstats.LeagueDashPlayerStats(season=season).get_normalized_dict()
    return resp.get("LeagueDashPlayerStats", [])


def fetch_active_players_stats_last_n_years(n: int = 5, sleep: float = 0.6) -> Dict[str, List[Dict[str, Any]]]:
    seasons = last_n_seasons_labels(n)
    active_ids = set(get_active_player_ids())
    out: Dict[str, List[Dict[str, Any]]] = {}
    for s in seasons:
        rows = fetch_league_player_stats_by_season(s)
        # Filter to currently active players
        filtered = []
        for r in rows:
            pid = r.get("PLAYER_ID")
            try:
                pid_int = int(pid) if pid is not None else -1
            except Exception:
                pid_int = -1
            if pid_int in active_ids:
                filtered.append(r)
        rows = filtered
        out[s] = rows
        time.sleep(sleep)
    return out
