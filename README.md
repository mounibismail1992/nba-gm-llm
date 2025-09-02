NBA GM LLM — Data Ingestion + Corpus Builder

Overview
- Goal: fetch up-to-date NBA data and build a corpus to power an “NBA GM” assistant (rosters, player logs, team stats, summaries).
- Sources supported out of the box:
  - nba_api (stats.nba.com community client; best for structured, recent data)
  - Basketball-Reference (HTML scraping; robust public reference)

Important
- Respect websites’ Terms of Service and robots.txt when scraping. Prefer official or permitted APIs (nba_api) when possible.
- stats.nba.com may require specific headers and is rate limited. See notes below.

Quick Start
1) Environment
   - Python 3.9+
   - Install: `pip install -r requirements.txt`
   - Optional: set `HTTP_PROXY`/`HTTPS_PROXY` if needed.

2) Fetch data
   - nba_api players/teams/game logs (example season 2024-25):
     `python -m nba_gm_llm.cli fetch --source nba_api --season 2024-25 --what players teams team_gamelogs`

   - Basketball-Reference rosters + salaries + per-game team logs:
     `python -m nba_gm_llm.cli fetch --source bbr --season auto --what rosters salaries team_gamelogs`

3) Build corpus
   - Generate markdown summaries for teams and players:
     `python -m nba_gm_llm.cli build-corpus --season 2024-25`

4) Makefile shortcuts
   - `make fetch-nba`   (nba_api basics)
   - `make fetch-bbr`   (Basketball-Reference basics)
   - `make corpus`

Data Layout
- `data/raw/<source>/` — JSONL dumps (per entity)
- `data/processed/` — Parquet tables (optional; via DuckDB/Pandas)
- `data/corpus/` — Markdown docs ready for RAG ingestion

Notes on Sources
- nba_api
  - Library: https://github.com/swar/nba_api
  - Often requires a browser-like User-Agent and HTTPS. We set headers internally; you may need VPN in some regions.
  - Respect rate limits; add sleep if needed.

- Basketball-Reference
  - Public HTML; light, polite scraping only. Cache locally and avoid hammering.
  - Team page pattern: `https://www.basketball-reference.com/teams/<TEAM>/<YEAR>.html` (e.g., BOS/2025.html)
  - Salaries table id: `salaries2` on the team page (may be in a commented block; handled).
  - Use `--season auto` to target the latest season year (July or later -> next calendar year).

Extending
- Add adapters under `src/nba_gm_llm/sources/` or `src/nba_gm_llm/scrapers/`.
- Add processors under `src/nba_gm_llm/processing/`.

Next (optional)
- Build embeddings + vector store (Qdrant/Chroma) and a QA agent over the corpus.
- Add salary cap/contract data (ensure ToS compliance; many sites restrict scraping).
