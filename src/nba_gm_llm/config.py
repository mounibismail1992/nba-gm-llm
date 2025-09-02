from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
PROC_DIR = DATA_DIR / "processed"
CORPUS_DIR = DATA_DIR / "corpus"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROC_DIR.mkdir(parents=True, exist_ok=True)
CORPUS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

