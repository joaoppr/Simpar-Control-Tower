# Arquitetura

## Visão lógica
```
 Clouds (AWS · Azure · OCI · GCP · Huawei)
        │  APIs oficiais (Cost Explorer, Cost Mgmt, Usage API, BigQuery Billing, BSS)
        ▼
 Conectores (backend/app/connectors)  ──►  ETL (app/etl/pipeline.py)  ──►  PostgreSQL (modelo unificado + views)
                                                                              │
 React + TypeScript + MUI  ◄──  FastAPI (routers: executivo, empresa, showback, oportunidades, governança, inventário, copilot, conexões)
```
- **Backend:** Python 3.12, FastAPI, SQLAlchemy (SQL parametrizado), Pydantic. Camada semântica em views (`v_cost`, `v_resource`, `v_shared_cost`, `v_opportunity`).
- **Frontend:** React 19, TypeScript, Material UI, Recharts. Build estático servido pelo próprio FastAPI (um processo em `localhost:8000`) ou Vite em dev (`5173`, proxy `/api`).
- **Banco:** PostgreSQL (embarcado via pacote `pgserver` sem Docker/sudo, ou `docker-compose`).
- **ETL:** conectores normalizam custo/recurso/recomendação; `load_costs` grava recursos agregados (conta × serviço) para alimentar os dashboards.
- **IA:** Copilot com ferramentas de dados (`copilot_tools.py`). Offline: roteador por palavras-chave. Com `OPENAI_API_KEY`: function calling usando as mesmas ferramentas.

## Fontes por cloud
| Cloud | Custo (primário) | Inventário / Recomendações |
|---|---|---|
| AWS | **Cost Explorer** (`get_cost_and_usage`) | Resource Groups Tagging API; CE rightsizing e Savings Plans recommendations |
| Azure | Cost Management Query API | ARM Resources; Azure Advisor (categoria Cost) |
| OCI | Usage API (`RequestSummarizedUsages`) | Resource Search |
| GCP | Cloud Billing export (BigQuery) | Recommender API |
| Huawei | BSS (billing) | — (a evoluir) |

> Os conectores **live** foram escritos contra as APIs oficiais e testados apenas com respostas simuladas (teste AWS em `tests/`). Validação com contas reais é o primeiro passo do roadmap.

## Preparação para SaaS
- Multi-tenant por `org` (todas as consultas passam pelas views com `org_id`; hoje fixo em `ORG_CODE`).
- Segredos criptografados (Fernet) fora das respostas da API; `SECRET_KEY` externalizável (KMS/Vault no futuro).
- API stateless, CORS restrito a localhost, SQL parametrizado, configuração por variáveis de ambiente.
- Evoluções: autenticação OIDC/SSO + RBAC por empresa, jobs agendados (Celery/Arq), particionamento de `cost_monthly`, cache, observabilidade.

## Decisões de modelagem
- **Moeda:** tudo em BRL; conectores convertem USD com `fx_usd_brl` da conexão.
- **Custos compartilhados:** pools hospedados na Simpar e rateados por regra (proporcional, igualitário ou percentual fixo) — conserva o total do Grupo.
- **Sem dupla contagem:** cada recurso gera no máximo uma oportunidade; compromissos (SP/RI) são oportunidades de conta.
- **KPIs:** cobertura de tags = custo em recursos com owner, produto, aplicação, centro de custo e ambiente; showback = custo com produto+aplicação; chargeback = custo em produtos com chargeback ativo.
