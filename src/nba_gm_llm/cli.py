from __future__ import annotations
import json
from pathlib import Path
from typing import List
import typer
from rich import print

from .config import RAW_DIR
from .sources import nba_api_client
from .scrapers import bbr
from .storage import write_jsonl
from .build_corpus import build_corpus

app = typer.Typer(help="NBA GM LLM — data fetch and corpus builder")


@app.command()
def fetch(
    source: str = typer.Option(..., help="nba_api or bbr"),
    season: str = typer.Option("2024-25", help="Season label, e.g., 2024-25 (nba_api) or year 2025 for BBR"),
    what: List[str] = typer.Option(
        ..., 
        help="Items to fetch: nba_api: players,teams,team_gamelogs; bbr: rosters,team_gamelogs,salaries"
    ),
):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if source == "nba_api":
        out_dir = RAW_DIR / "nba_api"
        out_dir.mkdir(parents=True, exist_ok=True)
        if "players" in what:
            rows = nba_api_client.list_players(active_only=False)
            write_jsonl(out_dir / f"players_{season}.jsonl", rows)
            print(f"[green]Wrote players for {season}")
        if "teams" in what:
            rows = nba_api_client.list_teams()
            write_jsonl(out_dir / f"teams_{season}.jsonl", rows)
            print(f"[green]Wrote teams for {season}")
        if "team_gamelogs" in what:
            teams_rows = nba_api_client.list_teams()
            tid_list = [t["id"] for t in teams_rows]
            logs = nba_api_client.fetch_team_gamelogs(tid_list, season)
            rows = []
            for tid, lst in logs.items():
                for r in lst:
                    r["TEAM_ID"] = tid
                    rows.append(r)
            write_jsonl(out_dir / f"team_gamelogs_{season}.jsonl", rows)
            print(f"[green]Wrote team logs for {season}")
    elif source == "bbr":
        out_dir = RAW_DIR / "bbr"
        out_dir.mkdir(parents=True, exist_ok=True)
        year = int(season)
        if "rosters" in what:
            rosters = bbr.fetch_all_rosters(year)
            for abbr, rows in rosters.items():
                write_jsonl(out_dir / f"roster_{year}_{abbr}.jsonl", rows)
            print(f"[green]Wrote rosters for {year}")
        if "salaries" in what:
            salaries = bbr.fetch_all_salaries(year)
            for abbr, rows in salaries.items():
                write_jsonl(out_dir / f"salaries_{year}_{abbr}.jsonl", rows)
            print(f"[green]Wrote salaries for {year}")
        if "team_gamelogs" in what:
            print("[yellow]BBR team_gamelogs not yet implemented in scraper; skipping.")
    else:
        raise typer.BadParameter("source must be nba_api or bbr")


@app.command()
def build_corpus_cmd(
    season: str = typer.Option("2024-25"),
    bbr_year: int = typer.Option(2025, help="Year for BBR rosters to include"),
):
    build_corpus(season, bbr_year)
    print("[green]Corpus built.")


if __name__ == "__main__":
    app()
