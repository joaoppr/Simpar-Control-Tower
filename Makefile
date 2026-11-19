.PHONY: demo db seed api web test build
demo: ; ./scripts/run_demo.sh
db: ; ./scripts/embedded_pg.sh start
seed: ; cd backend && .venv/bin/python -m app.seed
api: ; cd backend && .venv/bin/uvicorn app.main:app --reload --port 8888
web: ; cd frontend && npm run dev
build: ; cd frontend && npm run build
test: ; cd backend && .venv/bin/python -m pytest -q
