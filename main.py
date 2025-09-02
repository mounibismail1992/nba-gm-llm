from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from typing import Dict
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
    try:
        from nba_gm_llm.scrapers.bbr import fetch_team_salaries  # type: ignore
    except ModuleNotFoundError as e:
        print(
            "Missing dependencies or src path. Try: 'pip install -r requirements.txt' and rerun.\n"
            "If using a venv: 'PYTHONPATH=src .venv/bin/python main.py'"
        )
        raise
    team = os.getenv("TEAM", "BOS").upper()
    year_env = os.getenv("YEAR", "auto")

    if isinstance(year_env, str) and year_env.lower() in {"auto", "latest", "current"}:
        year = resolve_latest_bbr_year()
    else:
        year = int(year_env)

    rows = fetch_team_salaries(team, year)

    # Build a simple dictionary: player -> pretty salary text (fallback to "")
    salaries: Dict[str, str] = {r["player"]: (r.get("salary_text") or "") for r in rows}

    output = {
        "team": team,
        "year": year,
        "count": len(rows),
        "salaries": salaries,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
