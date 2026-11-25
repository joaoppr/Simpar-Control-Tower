# Simpar FinOps Control Tower

Plataforma executiva de FinOps multi-cloud do Grupo Simpar (Simpar, Movida, JSL, Vamos, Automob, CSInfra, CSBrasil) para AWS, Azure, OCI, Google Cloud e Huawei Cloud.

> **Todos os dados da demonstração são fictícios.** Nada aqui representa custos, produtos ou aplicações reais do Grupo.

## Execução rápida (localhost)
```bash
./scripts/run_demo.sh        # PostgreSQL embarcado + dados fictícios + build + API
# abra http://localhost:8000
```
Modo desenvolvimento: `make db seed` · `make api` (porta 8000) · `make web` (porta 5173, proxy para a API).
Veja `docs/RUN.md` para o passo a passo completo (WSL, Windows nativo, Docker, OpenAI, conectores reais).

## Documentação
`docs/ARCHITECTURE.md` · `docs/DATA_MODEL.md` · `docs/WIREFRAMES.md` · `docs/UX_UI.md` · `docs/ROADMAP.md` · `docs/RUN.md` · SQL em `database/`.

## Publicacao
Veja `docs/DEPLOYMENT.md` para publicar a demonstracao em `/cases/simpar`,
incluindo as configuracoes de subcaminho, backend e protecao de acesso.
