from __future__ import annotations
from pathlib import Path
from typing import Iterable, Dict, Any
import json
import pandas as pd
import duckdb as ddb


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def to_parquet(path: Path, rows: Iterable[Dict[str, Any]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(list(rows))
    df.to_parquet(path, index=False)


def duckdb_write(path: Path, table: str, rows: Iterable[Dict[str, Any]]):
    con = ddb.connect(str(path))
    df = pd.DataFrame(list(rows))
    con.execute(f"CREATE TABLE IF NOT EXISTS {table} AS SELECT * FROM df WHERE 0=1")
    con.register("df", df)
    con.execute(f"INSERT INTO {table} SELECT * FROM df")
    con.close()

