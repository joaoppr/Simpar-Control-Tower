# Roadmap evolutivo

| Fase | Foco | Entregas |
|---|---|---|
| 0 · Demo (atual) | Demonstração executiva | 7 módulos, base fictícia, Copilot offline, conectores escritos |
| 1 · Piloto real (0–6 sem) | Validar dados reais | Testar conectores com contas reais (AWS CE primeiro), mapear contas→empresas, normalizar tags e câmbio, reconciliar com Finanças |
| 2 · Produto interno (2–4 m) | Operação contínua | Jobs agendados de ETL, SSO/RBAC por empresa, alertas de anomalia e budget, workflow de oportunidades (aprovação/owner), trilha de auditoria |
| 3 · FinOps avançado (4–8 m) | Valor financeiro | Unit economics, comparação TCO multi-cloud com cenários (câmbio, Oracle/Exadata), planejamento de compromissos, chargeback integrado ao ERP |
| 4 · SaaS (8–12 m) | Multi-tenant | Isolamento por tenant, billing de uso, onboarding self-service de contas, marketplace de conectores, Copilot com RAG e ações |

**Riscos principais:** qualidade de tags, diferenças de moeda/descontos entre provedores, acesso a credenciais de leitura, definição de regras de rateio aprovadas pelo CFO.
