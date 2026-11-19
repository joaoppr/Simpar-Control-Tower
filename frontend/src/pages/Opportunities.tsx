import { useState } from 'react'
import { Box, MenuItem, Select, Table, TableBody, TableCell, TableHead, TableRow, TableSortLabel, TablePagination, Typography, TextField } from '@mui/material'
import { CartesianGrid, LabelList, ReferenceArea, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from 'recharts'
import { api, useApi, useMeta, qs } from '../api'
import { brl, brlc, num, pct } from '../format'
import { Bar, CloudChip, Grid, Kpi, LevelChip, Loading, PageHeader, Panel, StatusChip, ttStyle } from '../components/ui'
import { C } from '../theme'

const RISK_COLOR: Record<string, string> = { Baixo: C.teal, Médio: C.amber, Alto: C.rose }
const STATUSES = ['Identificada', 'Em análise', 'Aprovada', 'Em execução', 'Capturada']

export default function Opportunities() {
  const meta = useMeta()
  const [company, setCompany] = useState('')
  const [cloud, setCloud] = useState('')
  const [type, setType] = useState('')
  const [status, setStatus] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(0)
  const [sort, setSort] = useState('savings')
  const [dir, setDir] = useState('desc')
  const [tick, setTick] = useState(0)
  const sum = useApi<any>(`/api/opportunities/summary${qs({ company, cloud })}`, [tick])
  const list = useApi<any>(`/api/opportunities${qs({ company, cloud, type, status, q: search, sort, dir, page: page + 1, page_size: 15, open_only: status ? false : true })}`, [tick])
  const s = sum.data
  const pts = (s?.types ?? []).map((t: any) => ({ ...t, x: 1 + 2 * (0.5 * ((t.effort_idx - 1) / 2) + 0.5 * Math.min(t.term_days / 180, 1)), y: t.savings_monthly, z: Math.max(80, Math.min(900, t.count * 3)), fill: RISK_COLOR[t.risk] }))
  const ymax = Math.max(...pts.map((p: any) => p.y), 1) * 1.15
  const change = async (id: number, v: string) => { await api(`/api/opportunities/${id}`, { method: 'PATCH', body: JSON.stringify({ status: v }) }); setTick((t) => t + 1) }
  return (
    <>
      <PageHeader title="FinOps Opportunities" subtitle="Ranking e matriz de priorização das alavancas de economia (sem dupla contagem: um recurso pertence a uma única oportunidade)"
        actions={<>
          <Select size="small" displayEmpty value={company} onChange={(e) => { setCompany(e.target.value); setPage(0) }} sx={{ minWidth: 150 }}><MenuItem value="">Todas as empresas</MenuItem>{meta.companies.map((c) => <MenuItem key={c.code} value={c.code}>{c.name}</MenuItem>)}</Select>
          <Select size="small" displayEmpty value={cloud} onChange={(e) => { setCloud(e.target.value); setPage(0) }} sx={{ minWidth: 140 }}><MenuItem value="">Todas as clouds</MenuItem>{meta.clouds.map((c) => <MenuItem key={c.code} value={c.code}>{c.name}</MenuItem>)}</Select></>} />
      {!s ? <Loading error={sum.error} /> : (<>
        <Grid cols="repeat(4, 1fr)">
          <Kpi label="Potencial em aberto" value={brlc(s.total_monthly)} sub="por mês" accent={C.amber} />
          <Kpi label="Potencial anualizado" value={brlc(s.total_annual)} sub={`${pct(s.pct_of_spend)} do gasto mensal`} accent={C.amber} />
          <Kpi label="Capturado (run-rate)" value={brlc(s.captured_monthly)} sub="por mês, já validado" accent={C.teal} />
          <Kpi label="Oportunidades abertas" value={num(s.by_status.filter((x: any) => x.status !== 'Capturada').reduce((a: number, b: any) => a + b.count, 0))} sub={`${s.types.length} alavancas`} accent={C.indigo} />
        </Grid>
        <Grid cols="1.15fr 1fr">
          <Panel title="Matriz de priorização" subtitle="Eixo X: esforço e prazo · Eixo Y: economia mensal · Tamanho: nº de itens · Cor: risco">
            <ResponsiveContainer width="100%" height={560}>
              <ScatterChart margin={{ left: 8, right: 24, top: 16, bottom: 24 }}>
                <CartesianGrid stroke={C.line} />
                <ReferenceArea x1={0.9} x2={2} y1={ymax * 0.35} y2={ymax} fill={C.teal} fillOpacity={0.07} label={{ value: 'QUICK WINS', position: 'insideTopLeft', fontSize: 11, fill: C.teal, fontWeight: 700 }} />
                <ReferenceArea x1={2} x2={3.1} y1={ymax * 0.35} y2={ymax} fill={C.indigo} fillOpacity={0.06} label={{ value: 'PROJETOS ESTRATÉGICOS', position: 'insideTopRight', fontSize: 11, fill: C.indigo, fontWeight: 700 }} />
                <ReferenceArea x1={0.9} x2={2} y1={0} y2={ymax * 0.35} fill="#64748B" fillOpacity={0.04} label={{ value: 'PREENCHER LACUNAS', position: 'insideBottomLeft', fontSize: 11, fill: '#64748B', fontWeight: 700 }} />
                <ReferenceArea x1={2} x2={3.1} y1={0} y2={ymax * 0.35} fill={C.rose} fillOpacity={0.05} label={{ value: 'REAVALIAR', position: 'insideBottomRight', fontSize: 11, fill: C.rose, fontWeight: 700 }} />
                <XAxis type="number" dataKey="x" domain={[0.9, 3.1]} ticks={[1, 2, 3]} tickFormatter={(v) => ({ 1: 'Baixo', 2: 'Médio', 3: 'Alto' } as any)[v]} tick={{ fontSize: 11 }} label={{ value: 'Esforço e prazo de implementação', position: 'bottom', fontSize: 11, fill: C.slate }} />
                <YAxis type="number" dataKey="y" domain={[0, ymax]} tickFormatter={(v) => brlc(v)} width={86} tick={{ fontSize: 11 }} />
                <ZAxis type="number" dataKey="z" range={[160, 1400]} />
                <Tooltip contentStyle={ttStyle} cursor={{ strokeDasharray: '3 3' }} content={({ payload }: any) => payload?.[0] ? (
                  <Box sx={{ ...ttStyle, bgcolor: '#fff', p: 1.5 }}><b>{payload[0].payload.name}</b><br />Economia: {brl(payload[0].payload.savings_monthly)}/mês ({pct(payload[0].payload.savings_pct)})<br />Esforço {payload[0].payload.effort} · Risco {payload[0].payload.risk}<br />Prazo médio {payload[0].payload.term_days} dias · {payload[0].payload.count} itens</Box>) : null} />
                <Scatter isAnimationActive={false} data={pts} fillOpacity={0.8}>
                  <LabelList dataKey="rank" position="center" fill="#fff" fontSize={11} fontWeight={700} />
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </Panel>
          <Panel title="Ranking de oportunidades" subtitle="Ordenado pelo score de prioridade (economia, esforço, risco e prazo)" pad={1.5}>
            <Table size="small">
              <TableHead><TableRow><TableCell>#</TableCell><TableCell>Alavanca</TableCell><TableCell align="right">Economia</TableCell><TableCell>Prior.</TableCell></TableRow></TableHead>
              <TableBody>{s.types.map((t: any) => (
                <TableRow key={t.type} hover sx={{ cursor: 'pointer', bgcolor: type === t.type ? '#EEF2FF' : undefined }} onClick={() => { setType(type === t.type ? '' : t.type); setPage(0) }}>
                  <TableCell sx={{ fontWeight: 700, color: C.mute }}>{t.rank}</TableCell>
                  <TableCell><b>{t.name}</b><Typography variant="caption" sx={{ display: "block" }} color="text.secondary">{t.description}</Typography></TableCell>
                  <TableCell align="right"><b>{brlc(t.savings_monthly)}</b><Typography variant="caption" sx={{ display: "block" }} color="text.secondary">{pct(t.savings_pct)}</Typography></TableCell>
                  <TableCell><LevelChip v={t.priority} /></TableCell></TableRow>))}</TableBody></Table>
          </Panel>
        </Grid>
        <Panel title="Detalhe por alavanca" subtitle="Economia potencial (% e R$), esforço, prazo, risco e prioridade" sx={{ mb: 2 }} pad={1.5}>
          <Table size="small">
            <TableHead><TableRow><TableCell>Alavanca</TableCell><TableCell align="right">Itens</TableCell><TableCell align="right">Economia %</TableCell><TableCell align="right">Economia R$/mês</TableCell><TableCell align="right">R$/ano</TableCell><TableCell>Esforço</TableCell><TableCell align="right">Prazo</TableCell><TableCell>Risco</TableCell><TableCell>Prioridade</TableCell><TableCell>Capturado/mês</TableCell></TableRow></TableHead>
            <TableBody>{s.types.map((t: any) => (
              <TableRow key={t.type} hover><TableCell><b>{t.name}</b></TableCell><TableCell align="right">{t.count}</TableCell><TableCell align="right">{pct(t.savings_pct)}</TableCell>
                <TableCell align="right"><b>{brl(t.savings_monthly)}</b></TableCell><TableCell align="right">{brl(t.savings_annual)}</TableCell><TableCell><LevelChip v={t.effort} /></TableCell>
                <TableCell align="right">{t.term_days} d</TableCell><TableCell><LevelChip v={t.risk} /></TableCell><TableCell><LevelChip v={t.priority} /></TableCell><TableCell>{brl(t.captured_monthly)}</TableCell></TableRow>))}</TableBody></Table>
        </Panel>
      </>)}
      <Panel title="Oportunidades detalhadas" subtitle={list.data ? `${num(list.data.total)} itens · ${brl(list.data.savings_monthly)}/mês${type ? ' · filtrado por alavanca' : ''}` : ''} pad={1.5} action={
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField size="small" placeholder="Buscar recurso..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(0) }} />
          <Select size="small" displayEmpty value={status} onChange={(e) => { setStatus(e.target.value); setPage(0) }} sx={{ minWidth: 150 }}><MenuItem value="">Abertas</MenuItem>{STATUSES.map((x) => <MenuItem key={x} value={x}>{x}</MenuItem>)}</Select></Box>}>
        {!list.data ? <Loading error={list.error} /> : (<>
          <Table size="small">
            <TableHead><TableRow><TableCell>Oportunidade</TableCell><TableCell>Empresa</TableCell><TableCell>Cloud</TableCell>
              <TableCell align="right"><TableSortLabel active={sort === 'savings'} direction={dir as any} onClick={() => { setSort('savings'); setDir(dir === 'desc' ? 'asc' : 'desc') }}>Economia/mês</TableSortLabel></TableCell>
              <TableCell align="right">%</TableCell><TableCell>Esforço</TableCell><TableCell align="right">Prazo</TableCell><TableCell>Risco</TableCell>
              <TableCell><TableSortLabel active={sort === 'score'} direction={dir as any} onClick={() => { setSort('score'); setDir(dir === 'desc' ? 'asc' : 'desc') }}>Score</TableSortLabel></TableCell><TableCell>Status</TableCell></TableRow></TableHead>
            <TableBody>{list.data.rows.map((o: any) => (
              <TableRow key={o.id} hover><TableCell sx={{ maxWidth: 360 }}><b>{o.title}</b><Typography variant="caption" sx={{ display: "block" }} color="text.secondary" noWrap>{o.type_name}</Typography></TableCell>
                <TableCell>{o.company_name}</TableCell><TableCell><CloudChip code={o.cloud_code} /></TableCell><TableCell align="right"><b>{brl(o.savings_monthly_brl)}</b></TableCell>
                <TableCell align="right">{pct(o.savings_pct)}</TableCell><TableCell><LevelChip v={o.effort} /></TableCell><TableCell align="right">{o.term_days} d</TableCell><TableCell><LevelChip v={o.risk} /></TableCell>
                <TableCell><Bar value={o.priority_score} label={o.priority_score.toFixed(0)} /></TableCell>
                <TableCell><Select size="small" variant="standard" value={o.status} onChange={(e) => change(o.id, e.target.value)} disableUnderline sx={{ fontSize: 12 }}>{STATUSES.map((x) => <MenuItem key={x} value={x}><StatusChip v={x} /></MenuItem>)}</Select></TableCell></TableRow>))}</TableBody></Table>
          <TablePagination component="div" count={list.data.total} page={page} onPageChange={(_, p) => setPage(p)} rowsPerPage={15} rowsPerPageOptions={[15]} labelDisplayedRows={({ from, to, count }) => `${from}–${to} de ${count}`} />
        </>)}
      </Panel>
    </>
  )
}
