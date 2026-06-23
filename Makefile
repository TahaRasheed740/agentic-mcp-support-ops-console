.PHONY: up down logs test lint typecheck build ingest-knowledge eval-retrieval eval-mcp report-investigations

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

test:
	uv run --project services/api pytest services/api/tests

lint:
	uv run --project services/api ruff check services/api scripts
	npm run lint

typecheck:
	uv run --project services/api mypy --config-file services/api/pyproject.toml services/api/src
	npm run typecheck

build:
	npm run build

ingest-knowledge:
	uv run --project services/api python -m tracedesk_api.knowledge_ingest --force

eval-retrieval:
	uv run --project services/api python -m tracedesk_api.retrieval_eval --mode hybrid --limit 8 --output reports/retrieval/latest.json

eval-mcp:
	docker compose exec -T api python -m tracedesk_api.mcp_layer.contract_eval

report-investigations:
	docker compose exec -T api python -m tracedesk_api.investigations.report
