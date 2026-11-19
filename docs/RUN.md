# Passo a passo — execução em localhost

## Opção A · um comando (WSL/Linux, sem Docker e sem sudo)
```bash
cd simpar-finops-control-tower
./scripts/run_demo.sh      # cria venv, sobe PostgreSQL embarcado, carrega dados fictícios, compila o frontend e inicia a API
```
Abra **http://localhost:8000**. Requer `python3` e `node` 20+ (no PATH ou em `~/.local/node/bin`).

## Opção B · desenvolvimento (dois terminais)
```bash
make db seed               # PostgreSQL embarcado + dados fictícios
make api                   # http://localhost:8000  (docs: /docs)
make web                   # http://localhost:5173  (hot reload)
```
## Opção C · PostgreSQL via Docker
```bash
docker compose up -d db
cd backend && python -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m app.seed && .venv/bin/uvicorn app.main:app --port 8000
```
## Windows nativo
Instale Python 3.12, Node 20+ e Docker Desktop; use a Opção C e `cd frontend && npm install && npm run build`.

## Variáveis (`.env`, ver `.env.example`)
`DATABASE_URL`, `ORG_CODE`, `OPENAI_API_KEY` (Copilot em linguagem livre), `SECRET_KEY` (criptografia de credenciais).

## Testes e dados
`make test` (8 testes) · `python -m app.seed --ref 2026-10 --seed 42` recria a base determinística.

## Conectar clouds reais
1. `pip install -r backend/requirements-connectors.txt`
2. Em **Conexões e ETL → Nova conexão**, escolha empresa, cloud, modo **Live** e informe as credenciais (somente leitura). Use **Testar** e **Sincronizar**.
3. Permissões mínimas: AWS `ce:Get*`, `tag:GetResources`, `sts:AssumeRole`; Azure *Cost Management Reader* + *Reader*; OCI política de leitura de usage reports; GCP BigQuery Data Viewer + Recommender Viewer; Huawei BSS ReadOnly.
