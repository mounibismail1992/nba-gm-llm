from __future__ import annotations
import argparse
from datetime import datetime
import json
from typing import List, Dict, Any

from nba_gm_llm.scrapers.bbr import fetch_team_salaries


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch and print a sample of NBA player salaries from Basketball-Reference"
    )
    parser.add_argument("--team", default="BOS", help="Team abbreviation, e.g., BOS, LAL, DEN")
    parser.add_argument(
        "--year",
        default="auto",
        help="Season year on BBR (e.g., 2026), or 'auto' for latest",
    )
    parser.add_argument("--limit", type=int, default=5, help="How many rows to show")
    args = parser.parse_args()

    # Resolve year
    if isinstance(args.year, str) and args.year.lower() in {"auto", "latest", "current"}:
        # July or later -> next year; else current year
        now = datetime.utcnow()
        year = now.year + 1 if now.month >= 7 else now.year
    else:
        year = int(args.year)

    rows: List[Dict[str, Any]] = fetch_team_salaries(args.team, year)
    if not rows:
        print(f"No salary rows found for {args.team} {args.year}.")
        return

    sample = rows[: args.limit]
    print(json.dumps(sample, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
