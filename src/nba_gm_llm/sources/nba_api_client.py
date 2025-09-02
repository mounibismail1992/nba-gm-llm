from __future__ import annotations
import time
from typing import Iterable, Dict, Any, List
from nba_api.stats.static import teams, players
from nba_api.stats.endpoints import teamgamelog
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

