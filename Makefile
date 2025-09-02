PY ?= python

.PHONY: fetch-nba fetch-bbr corpus

fetch-nba:
	$(PY) -m nba_gm_llm.cli fetch --source nba_api --season 2024-25 --what players teams team_gamelogs

fetch-bbr:
	$(PY) -m nba_gm_llm.cli fetch --source bbr --season 2025 --what rosters team_gamelogs

corpus:
	$(PY) -m nba_gm_llm.cli build-corpus --season 2024-25

