# Wireframes (baixa fidelidade)

Layout comum: barra lateral escura (navegação) · cabeçalho com chips "DADOS SIMULADOS", mês de referência e moeda · conteúdo em cartões brancos sobre fundo cinza claro.

## 1. Executivo · CIO Grupo
```
[KPI Total Spend][KPI Saving Capturado][KPI Saving Potencial][KPI Forecast/Budget]
[Tags][Showback][Chargeback][% Ociosos]   [% Otimizados][Compartilhados][Recursos][YTD]
[ Evolução: realizado + budget + forecast (faixa) ............ ][ Donut por cloud ]
[ Empresa × cloud (barras empilhadas) ][ Budget x Realizado por empresa ]
[ Economia capturada x potencial      ][ Tabela por empresa: custo, budget, var., MoM ]
[ Top 20 maiores consumidores (aplicações | recursos | contas) ]
```
## 2. CIO Empresa
```
(chips das 7 empresas)
[Custo][Budget][Forecast][Saving potencial][Tags][% ociosos]
[ Tendência/forecast ........... ][ Donut cloud ]
[ Abas: Cloud|Produto|Aplicação|C.custo|Ambiente|Owner|Serviço → barras + tabela ]
[ Desvios do mês ][ Quick wins ]   [ Oportunidades da empresa ]
```
## 3. Showback e Chargeback
```
[Direto][Compartilhado][Showback %][Valor chargeback][Não alocado]
Abas: Hierarquia (treemap + drill Empresa→Produto→App→Serviço→Recurso) | Rateio (pools + regra + prévia + salvar) | Demonstrativo (tabela + CSV)
```
## 4. FinOps Opportunities
```
[Potencial/mês][Anualizado][Capturado][Abertas]
[ Matriz: x=esforço/prazo, y=economia, bolha=itens, cor=risco, 4 quadrantes ][ Ranking P1/P2/P3 ]
[ Tabela por alavanca: % · R$ · esforço · prazo · risco · prioridade ]
[ Lista detalhada com filtros e mudança de status ]
```
## 5. Governança
```
[Cobertura][Sem owner][Sem produto][Sem aplicação][Sem C.custo][Sem ambiente]
[ Score + radar 8 dimensões ][ Tabela por empresa (score, nível, cobertura) + política de tags ]
[ Recursos fora de conformidade (filtro por tipo) ]
```
## 6. Inventário · 7. Copilot · 8. Conexões
```
Inventário: barra de filtros (busca, empresa, cloud, serviço, região, ambiente, produto, tags, ociosos) + tabela ordenável paginada + CSV
Copilot: chat com tabelas nas respostas + perguntas sugeridas
Conexões: lista de conectores (testar/sincronizar/remover) + execuções de ETL + diálogo "Nova conexão" por provedor
```
