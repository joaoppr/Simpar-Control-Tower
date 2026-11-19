import { useState } from 'react'
import { Box, Chip, Table, TableBody, TableCell, TableHead, TableRow, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material'
import { useApi, qs } from '../api'
import { brl, brlc, num, pct, mlong } from '../format'
import { Bar, CloudChip, Grid, Kpi, Loading, PageHeader, Panel } from '../components/ui'
import { BudgetBars, CloudDonut, SavingsBars, StackedCompanyCloud, TrendChart } from '../components/charts'
import { C } from '../theme'

export default function Executive() {
  const { data, loading, error } = useApi<any>('/api/executive/overview')
  const [dim, setDim] = useState('application')
  const top = useApi<any[]>(`/api/executive/top-consumers${qs({ dimension: dim, limit: 20 })}`, [dim])
  if (!data) return <Loading error={error} />
  const k = data.kpis
  return (
    <>
      <PageHeader title="Visão Executiva do Grupo" subtitle={`Consolidação multi-cloud de 7 empresas e 5 provedores · ${mlong(data.month)}`} />
      <Grid cols="repeat(4, 1fr)">
        <Kpi label="Total Spend" value={brlc(k.total_spend)} delta={k.mom_pct} good="down" sub="vs. mês anterior" accent={C.indigo} />
        <Kpi label="Saving Capturado" value={brlc(k.saving_captured_month)} sub={`/mês · ${brlc(k.saving_captured_ytd)} no ano`} accent={C.teal} />
        <Kpi label="Saving Potencial" value={brlc(k.saving_potential)} sub={`/mês · ${pct(k.saving_potential_pct)} do gasto · ${num(k.opportunities_open)} oportunidades`} accent={C.amber} />
        <Kpi label="Forecast próximo mês" value={brlc(k.forecast_next_month)} sub={`Budget do mês: ${brlc(k.budget)} (${pct(k.budget_var_pct, true)})`} accent="#2563EB" />
      </Grid>
      <Grid cols="repeat(4, 1fr)">
        <Kpi label="Cobertura de Tags" value={pct(k.tag_coverage)} sub="custo com as 5 tags obrigatórias" accent={k.tag_coverage < 70 ? C.rose : C.teal} hint="% do custo direto em recursos com owner, produto, aplicação, centro de custo e ambiente" />
        <Kpi label="Showback Coverage" value={pct(k.showback_coverage)} sub="custo atribuído a produto e aplicação" accent={C.indigo} />
        <Kpi label="Chargeback Coverage" value={pct(k.chargeback_coverage)} sub="custo em produtos com chargeback ativo" accent={C.indigo} />
        <Kpi label="% Recursos Ociosos" value={pct(k.idle_resources_pct)} sub={`${num(k.idle_resources)} recursos · ${pct(k.idle_pct)} do custo`} accent={C.rose} />
      </Grid>
      <Grid cols="repeat(4, 1fr)" sx={{ mt: -0 }}>
        <Kpi label="% Recursos Otimizados" value={pct(k.optimized_resources_pct)} sub={`${pct(k.optimized_pct)} do custo já otimizado`} accent={C.teal} />
        <Kpi label="Custos compartilhados" value={brlc(k.shared_allocated)} sub="rateados entre as empresas" accent="#64748B" />
        <Kpi label="Recursos monitorados" value={num(k.resources)} sub={`${num(k.untagged_resources)} sem conformidade de tags`} accent="#64748B" />
        <Kpi label="Acumulado no ano (YTD)" value={brlc(k.ytd_spend)} sub="custo total com rateio" accent="#64748B" />
      </Grid>

      <Grid cols="2fr 1fr">
        <Panel title="Evolução mensal, budget e forecast" subtitle="Realizado (12 meses), budget e projeção dos próximos 3 meses com faixa de confiança"><TrendChart data={data.trend} /></Panel>
        <Panel title="Distribuição por cloud" subtitle="Custo do mês com rateio proporcional dos compartilhados"><CloudDonut data={data.by_cloud} /></Panel>
      </Grid>
      <Grid cols="1fr 1fr">
        <Panel title="Consumo por empresa e cloud" subtitle="Custo direto por provedor"><StackedCompanyCloud data={data.by_company} /></Panel>
        <Panel title="Budget x Realizado por empresa" subtitle="Vermelho: acima de 3% do budget · Âmbar: acima do budget"><BudgetBars data={data.budget_vs_actual} /></Panel>
      </Grid>
      <Grid cols="1fr 1fr">
        <Panel title="Economia capturada x potencial" subtitle="Run-rate mensal de economia validada vs. oportunidades em aberto"><SavingsBars data={data.savings} potential={k.saving_potential} /></Panel>
        <Panel title="Consumo por empresa" subtitle="Custo, budget, variação e tendência">
          <Table size="small">
            <TableHead><TableRow><TableCell>Empresa</TableCell><TableCell align="right">Custo</TableCell><TableCell align="right">Budget</TableCell><TableCell align="right">Var.</TableCell><TableCell align="right">MoM</TableCell><TableCell>Part.</TableCell></TableRow></TableHead>
            <TableBody>
              {data.by_company.map((c: any) => (
                <TableRow key={c.code} hover>
                  <TableCell><Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: c.color }} /><b>{c.name}</b></Box></TableCell>
                  <TableCell align="right">{brlc(c.cost)}</TableCell>
                  <TableCell align="right">{brlc(c.budget)}</TableCell>
                  <TableCell align="right" sx={{ color: c.variance_pct > 0 ? C.rose : C.teal, fontWeight: 700 }}>{pct(c.variance_pct, true)}</TableCell>
                  <TableCell align="right">{pct(c.mom_pct, true)}</TableCell>
                  <TableCell><Bar value={c.share * 2.5} color={c.color} label={pct(c.share, false)} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Panel>
      </Grid>
      <Panel title="Top 20 maiores consumidores" action={
        <ToggleButtonGroup size="small" exclusive value={dim} onChange={(_, v) => v && setDim(v)}>
          <ToggleButton value="application">Aplicações</ToggleButton><ToggleButton value="resource">Recursos</ToggleButton><ToggleButton value="account">Contas</ToggleButton>
        </ToggleButtonGroup>}>
        {!top.data ? <Loading error={top.error} /> : (
          <Table size="small">
            <TableHead><TableRow><TableCell>#</TableCell><TableCell>{dim === 'resource' ? 'Recurso' : dim === 'account' ? 'Conta' : 'Aplicação'}</TableCell><TableCell>Empresa</TableCell><TableCell>{dim === 'application' ? 'Produto' : 'Detalhe'}</TableCell><TableCell>Cloud</TableCell><TableCell align="right">Custo mensal</TableCell><TableCell align="right">MoM</TableCell><TableCell>% do total</TableCell></TableRow></TableHead>
            <TableBody>
              {top.data.map((r: any) => (
                <TableRow key={r.rank} hover>
                  <TableCell sx={{ color: C.mute, fontWeight: 700 }}>{r.rank}</TableCell>
                  <TableCell><b>{r.name}</b></TableCell><TableCell>{r.company_name}</TableCell><TableCell>{r.detail}</TableCell>
                  <TableCell>{String(r.cloud_code).split(' · ').map((c: string) => <CloudChip key={c} code={c} />)}</TableCell>
                  <TableCell align="right"><b>{brl(r.cost)}</b></TableCell>
                  <TableCell align="right" sx={{ color: (r.mom_pct ?? 0) > 8 ? C.rose : C.slate }}>{pct(r.mom_pct, true)}</TableCell>
                  <TableCell><Bar value={r.share * 8} label={pct(r.share)} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Panel>
    </>
  )
}
