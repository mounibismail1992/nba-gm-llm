from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import json
from .config import RAW_DIR, CORPUS_DIR


def _iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def build_team_summaries(season: str):
    # nba_api team logs if present
    src_path = RAW_DIR / "nba_api" / f"team_gamelogs_{season}.jsonl"
    out_dir = CORPUS_DIR / season
    out_dir.mkdir(parents=True, exist_ok=True)
    if src_path.exists():
        by_team: Dict[str, List[Dict[str, Any]]] = {}
        for row in _iter_jsonl(src_path):
            tid = str(row.get("TEAM_ID"))
            by_team.setdefault(tid, []).append(row)
        for tid, rows in by_team.items():
            rows = sorted(rows, key=lambda r: r.get("GAME_DATE"))
            # Simple summary
            content = [f"# Team {tid} — Season {season}", "", "Recent Games:"]
            for r in rows[-10:]:
                content.append(f"- {r.get('GAME_DATE')}: {r.get('MATCHUP')} — {r.get('WL')} {r.get('PTS')} pts")
            (out_dir / f"team_{tid}.md").write_text("\n".join(content), encoding="utf-8")


def build_player_roster_notes(year: int):
    src_dir = RAW_DIR / "bbr"
    out_dir = CORPUS_DIR / str(year)
    out_dir.mkdir(parents=True, exist_ok=True)
    # Write one doc per team roster if present
    for p in src_dir.glob(f"roster_{year}_*.jsonl"):
        team = p.stem.split("_")[-1]
        names = [row.get("player") or row.get("player_url", "") for row in _iter_jsonl(p)]
        content = [f"# {team} Roster — {year}", "", *[f"- {n}" for n in names if n]]
        (out_dir / f"roster_{team}.md").write_text("\n".join(content), encoding="utf-8")


def build_corpus(season: str, year_for_bbr: int | None = None):
    build_team_summaries(season)
    if year_for_bbr:
        build_player_roster_notes(year_for_bbr)

