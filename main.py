from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Ensure we can import the package from src/
ROOT = Path(__file__).parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

def resolve_latest_bbr_year(now: datetime | None = None) -> int:
    dt = now or datetime.utcnow()
    return dt.year + 1 if dt.month >= 7 else dt.year


def main() -> None:
    task = os.getenv("TASK", "contracts").lower()
    team = os.getenv("TEAM", "BOS").upper()
    year_env = os.getenv("YEAR", "auto")

    if isinstance(year_env, str) and year_env.lower() in {"auto", "latest", "current"}:
        year = resolve_latest_bbr_year()
    else:
        year = int(year_env)

    if task == "player_stats":
        try:
            from nba_gm_llm.sources import nba_api_client  # type: ignore
        except ModuleNotFoundError:
            print(
                "Missing nba_api. Run: pip install -r requirements.txt\n"
                "If using venv: PYTHONPATH=src .venv/bin/python main.py"
            )
            raise
        stats_by_season: Dict[str, List[Dict[str, Any]]] = nba_api_client.fetch_active_players_stats_last_n_years(n=5)
        seasons = sorted(stats_by_season.keys())[::-1]
        latest = seasons[0]
        sample = stats_by_season[latest][:5]
        output = {
            "seasons": seasons,
            "counts": {s: len(stats_by_season[s]) for s in seasons},
            "latest_sample": sample,
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    # Default: contracts
    try:
        from nba_gm_llm.scrapers.bbr import fetch_team_contracts  # type: ignore
    except ModuleNotFoundError as e:
        print(
            "Missing dependencies or src path. Try: 'pip install -r requirements.txt' and rerun.\n"
            "If using a venv: 'PYTHONPATH=src .venv/bin/python main.py'"
        )
        raise

    # Contracts page gives current season forward; ignore year mismatch and trust page
    res = fetch_team_contracts(team)
    players = res.get("players", [])

    # Build dictionary: player -> {salary_text, years_remaining, status}
    salaries: Dict[str, dict] = {
        p["player"]: {
            "salary": p.get("current_salary"),
            "salary_text": p.get("current_salary_text") or "",
            "years_remaining": p.get("years_remaining", 0),
            "status": p.get("status", ""),
        }
        for p in players
    }

    output = {
        "team": team,
        "year": res.get("base_year") or year,
        "season": res.get("base_year_label"),
        "count": len(players),
        "salaries": salaries,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
