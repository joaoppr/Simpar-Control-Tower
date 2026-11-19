import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Box, Tab, Tabs, Table, TableBody, TableCell, TableHead, TableRow, Typography, Chip } from '@mui/material'
import { useApi, useMeta } from '../api'
import { brl, brlc, pct, num } from '../format'
import { Bar, CloudChip, Grid, Kpi, LevelChip, Loading, PageHeader, Panel } from '../components/ui'
import { CloudDonut, HBars, TrendChart } from '../components/charts'
import { C } from '../theme'

const DIMS: [string, string][] = [['cloud', 'Cloud'], ['product', 'Produto'], ['application', 'Aplicação'], ['cost_center', 'Centro de custo'], ['environment', 'Ambiente'], ['owner', 'Owner'], ['service', 'Serviço']]

export default function Company() {
  const meta = useMeta()
  const nav = useNavigate()
  const { code = meta.companies[1].code } = useParams()
  const [dim, setDim] = useState('product')
  const { data, error } = useApi<any>(`/api/company/${code}/overview`, [code])
  return (
    <>
      <PageHeader title="Visão do CIO da Empresa" subtitle="Custos por cloud, produto, aplicação, centro de custo, ambiente e owner · desvios e oportunidades" />
      <Box sx={{ display: 'flex', gap: 1, mb: 2.5, flexWrap: 'wrap' }}>
        {meta.companies.map((c) => (
          <Chip key={c.code} label={c.name} onClick={() => nav(`/empresa/${c.code}`)} variant={c.code === code ? 'filled' : 'outlined'}
            sx={{ px: 1, bgcolor: c.code === code ? c.color : undefined, color: c.code === code ? '#fff' : undefined, borderColor: c.color }} />
        ))}
      </Box>
      {!data ? <Loading error={error} /> : (() => {
        const k = data.kpis
        const rows = data.breakdown[dim]
        return (<>
          <Grid cols="repeat(6, 1fr)">
            <Kpi label="Custo do mês" value={brlc(k.total_spend)} delta={k.mom_pct} good="down" sub="vs. mês anterior" />
            <Kpi label="Budget" value={brlc(k.budget)} sub={`${pct(k.budget_var_pct, true)} vs. budget`} accent={k.budget_var_pct > 0 ? C.rose : C.teal} />
            <Kpi label="Forecast (próx. mês)" value={brlc(k.forecast_next_month)} accent={C.amber} />
            <Kpi label="Saving potencial" value={brlc(k.saving_potential)} sub={`${pct(k.saving_potential_pct)} do gasto`} accent={C.amber} />
            <Kpi label="Cobertura de tags" value={pct(k.tag_coverage)} accent={k.tag_coverage < 70 ? C.rose : C.teal} />
            <Kpi label="% ociosos" value={pct(k.idle_resources_pct)} sub={`${num(k.idle_resources)} recursos`} accent={C.rose} />
          </Grid>
          <Grid cols="2fr 1fr">
            <Panel title="Tendência, budget e forecast"><TrendChart data={data.trend} height={290} /></Panel>
            <Panel title="Custos por cloud"><CloudDonut data={data.breakdown.cloud.map((d: any) => ({ ...d, code: d.name, name: d.name.toUpperCase() }))} height={290} /></Panel>
          </Grid>
          <Panel title="Quebra de custos" action={<Tabs value={dim} onChange={(_, v) => setDim(v)} variant="scrollable" scrollButtons="auto">{DIMS.map(([v, l]) => <Tab key={v} value={v} label={l} />)}</Tabs>}>
            <Grid cols="1fr 1.3fr" sx={{ mb: 0 }}>
              <HBars data={rows} height={320} color={C.indigo} />
              <Box sx={{ maxHeight: 340, overflow: 'auto' }}>
                <Table size="small" stickyHeader>
                  <TableHead><TableRow><TableCell>{DIMS.find((d) => d[0] === dim)![1]}</TableCell><TableCell align="right">Custo</TableCell><TableCell align="right">MoM</TableCell><TableCell>Part.</TableCell></TableRow></TableHead>
                  <TableBody>{rows.map((r: any) => (
                    <TableRow key={r.name} hover>
                      <TableCell>{dim === 'cloud' ? <CloudChip code={r.name} /> : <b style={{ color: /^Sem|sem-/.test(r.name) ? C.rose : undefined }}>{r.name}</b>}</TableCell>
                      <TableCell align="right">{brl(r.cost)}</TableCell>
                      <TableCell align="right" sx={{ color: (r.mom_pct ?? 0) > 10 ? C.rose : C.slate }}>{pct(r.mom_pct, true)}</TableCell>
                      <TableCell><Bar value={r.share} label={pct(r.share)} /></TableCell>
                    </TableRow>))}</TableBody>
                </Table>
              </Box>
            </Grid>
          </Panel>
          <Box sx={{ height: 16 }} />
          <Grid cols="1fr 1fr">
            <Panel title="Desvios do mês" subtitle="Variações relevantes de aplicação x cloud vs. mês anterior">
              {data.deviations.length === 0 ? <Typography variant="body2" color="text.secondary">Sem desvios relevantes.</Typography> : (
                <Table size="small"><TableHead><TableRow><TableCell>Aplicação</TableCell><TableCell>Cloud</TableCell><TableCell align="right">Mês</TableCell><TableCell align="right">Δ R$</TableCell><TableCell align="right">Δ %</TableCell><TableCell>Sev.</TableCell></TableRow></TableHead>
                  <TableBody>{data.deviations.map((d: any, i: number) => (
                    <TableRow key={i} hover><TableCell><b>{d.application}</b></TableCell><TableCell><CloudChip code={d.cloud_code} /></TableCell><TableCell align="right">{brl(d.cost)}</TableCell>
                      <TableCell align="right" sx={{ color: d.delta > 0 ? C.rose : C.teal, fontWeight: 700 }}>{d.delta > 0 ? '+' : ''}{brl(d.delta)}</TableCell>
                      <TableCell align="right">{pct(d.pct, true)}</TableCell><TableCell><LevelChip v={d.severity === 'alta' ? 'Alto' : 'Médio'} /></TableCell></TableRow>))}</TableBody></Table>)}
            </Panel>
            <Panel title="Quick wins" subtitle="Baixo esforço e prazo de até 20 dias">
              {data.quick_wins.map((o: any) => (
                <Box key={o.id} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 1, borderBottom: `1px solid ${C.line}`, gap: 2 }}>
                  <Box sx={{ minWidth: 0 }}><Typography variant="body2" sx={{ fontWeight: 600 }} noWrap>{o.title}</Typography>
                    <Typography variant="caption" color="text.secondary">{o.term_days} dias · risco {o.risk.toLowerCase()}</Typography></Box>
                  <Box sx={{ textAlign: 'right', flexShrink: 0 }}><Typography sx={{ fontWeight: 700, color: C.teal }}>{brl(o.savings_monthly_brl)}/mês</Typography><CloudChip code={o.cloud_code} /></Box>
                </Box>))}
            </Panel>
          </Grid>
          <Panel title="Oportunidades de economia" subtitle="Maiores itens em aberto da empresa">
            <Table size="small"><TableHead><TableRow><TableCell>Oportunidade</TableCell><TableCell>Cloud</TableCell><TableCell align="right">Economia/mês</TableCell><TableCell align="right">%</TableCell><TableCell>Esforço</TableCell><TableCell align="right">Prazo</TableCell><TableCell>Risco</TableCell></TableRow></TableHead>
              <TableBody>{data.opportunities.map((o: any) => (
                <TableRow key={o.id} hover><TableCell><b>{o.title}</b></TableCell><TableCell><CloudChip code={o.cloud_code} /></TableCell><TableCell align="right"><b>{brl(o.savings_monthly_brl)}</b></TableCell>
                  <TableCell align="right">{pct(o.savings_pct)}</TableCell><TableCell><LevelChip v={o.effort} /></TableCell><TableCell align="right">{o.term_days} d</TableCell><TableCell><LevelChip v={o.risk} /></TableCell></TableRow>))}</TableBody></Table>
          </Panel>
        </>)
      })()}
    </>
  )
}
