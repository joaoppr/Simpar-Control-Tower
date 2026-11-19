import { useState } from 'react'
import { Alert, Box, Button, MenuItem, Select, Tab, Tabs, Table, TableBody, TableCell, TableHead, TableRow, Typography, Chip, ToggleButton, ToggleButtonGroup, Snackbar } from '@mui/material'
import DownloadIcon from '@mui/icons-material/Download'
import { ResponsiveContainer, Tooltip, Treemap } from 'recharts'
import { api, useApi, useMeta, qs } from '../api'
import { brl, brlc, pct, PALETTE } from '../format'
import { Bar, Grid, Kpi, Loading, PageHeader, Panel, ttStyle } from '../components/ui'
import { C } from '../theme'

const Cell = (p: any) => {
  const { x, y, width, height, name, value, depth, index } = p
  const color = depth === 1 ? PALETTE[index % PALETTE.length] : '#fff'
  if (width < 4 || height < 4) return null
  return (<g><rect x={x} y={y} width={width} height={height} fill={depth === 1 ? color : 'transparent'} stroke="#fff" strokeWidth={depth === 1 ? 2 : 1} rx={4} opacity={depth === 1 ? 0.92 : 1} />
    {width > 70 && height > 28 && <text x={x + 8} y={y + 18} fill="#fff" fontSize={depth === 1 ? 13 : 11} fontWeight={700}>{String(name).slice(0, Math.floor(width / 7))}</text>}
    {width > 70 && height > 46 && <text x={x + 8} y={y + 34} fill="#fff" fontSize={11} opacity={0.85}>{brlc(value)}</text>}</g>)
}

export default function Showback() {
  const meta = useMeta()
  const [tab, setTab] = useState('hier')
  const [company, setCompany] = useState('')
  const [path, setPath] = useState<string[]>([])
  const s = useApi<any>(`/api/showback/summary${qs({ company })}`, [company])
  const pools = useApi<any>('/api/showback/pools', [tab])
  const st = useApi<any>(`/api/showback/statements${qs({ company })}`, [company])
  const [prev, setPrev] = useState<Record<number, any>>({})
  const [msg, setMsg] = useState('')
  const [rules, setRules] = useState<Record<number, any>>({})

  const node = (() => { let n: any[] = s.data?.tree ?? []; let cur: any = null; for (const p of path) { cur = n.find((x) => x.name === p); n = cur?.children ?? [] } return { list: n, cur } })()
  const LEVELS = ['Empresa', 'Produto', 'Aplicação', 'Serviço', 'Recurso']
  const res = useApi<any[]>(path.length === 4 ? `/api/showback/resources${qs({ company: s.data?.tree.find((c: any) => c.name === path[0])?.code, product: path[1], application: path[2], service: path[3] })}` : null, [path.join('|')])

  const preview = async (id: number, method: string, weights: any) => {
    setRules((r) => ({ ...r, [id]: { method, weights } }))
    setPrev((p) => ({ ...p, [id]: null }))
    const d = await api(`/api/showback/pools/${id}/preview`, { method: 'POST', body: JSON.stringify({ method, weights }) })
    setPrev((p) => ({ ...p, [id]: d }))
  }
  const save = async (id: number) => {
    const r = rules[id]; await api(`/api/showback/pools/${id}/rule`, { method: 'PUT', body: JSON.stringify(r) }); setMsg('Regra de rateio salva. Os dashboards já refletem a nova alocação.')
  }

  return (
    <>
      <PageHeader title="Showback e Chargeback" subtitle="Modelo Empresa → Produto → Aplicação → Serviço → Recurso, baseado nas tags das clouds, com rateio de custos compartilhados"
        actions={<Select size="small" value={company} displayEmpty onChange={(e) => { setCompany(e.target.value); setPath([]) }} sx={{ minWidth: 180 }}>
          <MenuItem value="">Todas as empresas</MenuItem>{meta.companies.map((c) => <MenuItem key={c.code} value={c.code}>{c.name}</MenuItem>)}</Select>} />
      {s.data && (<Grid cols="repeat(5, 1fr)">
        <Kpi label="Custo direto" value={brlc(s.data.totals.direct)} accent={C.indigo} />
        <Kpi label="Compartilhado rateado" value={brlc(s.data.totals.shared)} accent="#64748B" />
        <Kpi label="Showback coverage" value={pct(s.data.kpis.showback_coverage)} sub="produto + aplicação via tags" accent={C.teal} />
        <Kpi label="Valor de chargeback" value={brlc(s.data.totals.billable)} sub={`${pct(s.data.kpis.chargeback_coverage)} do custo direto`} accent={C.amber} />
        <Kpi label="Não alocado (sem produto)" value={brlc(s.data.totals.unallocated)} sub="regularizar tags" accent={C.rose} />
      </Grid>)}
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2, borderBottom: `1px solid ${C.line}` }}>
        <Tab value="hier" label="Hierarquia de custos" /><Tab value="pools" label="Rateio de compartilhados" /><Tab value="chargeback" label="Demonstrativo de chargeback" />
      </Tabs>

      {tab === 'hier' && (!s.data ? <Loading error={s.error} /> : (<>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5, flexWrap: 'wrap' }}>
          <Chip label="Grupo" size="small" onClick={() => setPath([])} />
          {path.map((p, i) => <Chip key={i} size="small" color="primary" variant="outlined" label={`${LEVELS[i + 1] ? '' : ''}${p}`} onClick={() => setPath(path.slice(0, i + 1))} />)}
          <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>Nível atual: {LEVELS[path.length]}</Typography>
        </Box>
        <Grid cols="1.2fr 1fr">
          <Panel title="Mapa de custos" subtitle="Clique em uma linha da tabela para detalhar"><ResponsiveContainer width="100%" height={380}>
            <Treemap data={node.list.map((n: any) => ({ name: n.name, value: n.value }))} dataKey="value" content={<Cell />} isAnimationActive={false}><Tooltip contentStyle={ttStyle} formatter={(v: any) => brl(v)} /></Treemap></ResponsiveContainer></Panel>
          <Panel title={`Detalhamento por ${LEVELS[path.length].toLowerCase()}`}>
            {path.length < 4 ? (
              <Box sx={{ maxHeight: 380, overflow: 'auto' }}><Table size="small" stickyHeader><TableHead><TableRow><TableCell>{LEVELS[path.length]}</TableCell><TableCell align="right">Custo direto</TableCell><TableCell>Part.</TableCell></TableRow></TableHead>
                <TableBody>{node.list.map((n: any) => { const tot = node.list.reduce((a: number, b: any) => a + b.value, 0); return (
                  <TableRow key={n.name} hover sx={{ cursor: path.length < 4 ? 'pointer' : 'default' }} onClick={() => setPath([...path, n.name])}>
                    <TableCell><b style={{ color: /^Sem /.test(n.name) ? C.rose : undefined }}>{n.name}</b>{path.length === 1 && n.chargeback && <Chip size="small" label="chargeback" sx={{ ml: 1, height: 18, fontSize: 10 }} color="success" variant="outlined" />}</TableCell>
                    <TableCell align="right">{brl(n.value)}</TableCell><TableCell><Bar value={(n.value / tot) * 100} label={pct((n.value / tot) * 100)} /></TableCell></TableRow>) })}</TableBody></Table></Box>
            ) : (!res.data ? <Loading error={res.error} /> : (
              <Box sx={{ maxHeight: 380, overflow: 'auto' }}><Table size="small" stickyHeader><TableHead><TableRow><TableCell>Recurso</TableCell><TableCell>Região</TableCell><TableCell>Ambiente</TableCell><TableCell align="right">Custo</TableCell></TableRow></TableHead>
                <TableBody>{res.data.map((r: any) => <TableRow key={r.resource_id} hover><TableCell>{r.resource_name}</TableCell><TableCell>{r.region}</TableCell><TableCell>{r.environment ?? '—'}</TableCell><TableCell align="right">{brl(r.cost_brl)}</TableCell></TableRow>)}</TableBody></Table></Box>))}
          </Panel>
        </Grid></>))}

      {tab === 'pools' && (!pools.data ? <Loading error={pools.error} /> : (<>
        <Alert severity="info" sx={{ mb: 2 }}>Custos compartilhados ({brlc(pools.data.total_shared)}/mês) ficam em contas corporativas e são rateados entre as empresas. Escolha a regra, visualize o impacto e salve.</Alert>
        {pools.data.pools.map((p: any) => { const cur = prev[p.id] ?? p; const rule = rules[p.id] ?? { method: p.method, weights: p.weights }; return (
          <Panel key={p.id} sx={{ mb: 2 }} title={p.name} subtitle={p.description} action={<Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Typography sx={{ fontWeight: 700 }}>{brl(p.cost)}/mês</Typography>
            <ToggleButtonGroup size="small" exclusive value={rule.method} onChange={(_, v) => v && preview(p.id, v, v === 'fixed' ? (Object.keys(p.weights).length ? p.weights : Object.fromEntries(cur.allocation.map((a: any) => [a.code, 1 / cur.allocation.length]))) : {})}>
              <ToggleButton value="proportional">Proporcional ao consumo</ToggleButton><ToggleButton value="even">Igualitário</ToggleButton><ToggleButton value="fixed">Percentual fixo</ToggleButton></ToggleButtonGroup>
            <Button size="small" variant="contained" disabled={!rules[p.id]} onClick={() => save(p.id)}>Salvar regra</Button></Box>}>
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 1.5 }}>
              {cur.allocation.map((a: any) => (<Box key={a.code} sx={{ p: 1.25, borderRadius: 2, bgcolor: '#F6F7F9' }}>
                <Typography variant="caption" color="text.secondary">{a.name}</Typography>
                <Typography sx={{ fontWeight: 700 }}>{brlc(a.amount)}</Typography><Typography variant="caption">{pct(a.share)}</Typography></Box>))}
            </Box></Panel>) })}</>))}

      {tab === 'chargeback' && (!st.data ? <Loading error={st.error} /> : (
        <Panel title="Demonstrativo de chargeback do mês" subtitle="Custo direto + rateio proporcional dos compartilhados. Só produtos com chargeback ativo geram cobrança." action={
          <Button size="small" startIcon={<DownloadIcon />} href={`/api/showback/statements.csv${qs({ company })}`}>Exportar CSV</Button>}>
          <Table size="small"><TableHead><TableRow><TableCell>Empresa</TableCell><TableCell>Produto</TableCell><TableCell align="right">Custo direto</TableCell><TableCell align="right">Compartilhado</TableCell><TableCell align="right">Total</TableCell><TableCell align="right">A cobrar (chargeback)</TableCell><TableCell>Status</TableCell></TableRow></TableHead>
            <TableBody>{st.data.rows.map((r: any, i: number) => (
              <TableRow key={i} hover><TableCell>{r.company_name}</TableCell><TableCell><b>{r.product}</b></TableCell><TableCell align="right">{brl(r.direct)}</TableCell><TableCell align="right">{brl(r.shared)}</TableCell><TableCell align="right">{brl(r.total)}</TableCell>
                <TableCell align="right"><b>{r.billable ? brl(r.billable) : '—'}</b></TableCell>
                <TableCell><Chip size="small" label={r.status} color={r.status.startsWith('Fatur') ? 'success' : r.status.startsWith('Não') ? 'error' : 'default'} variant="outlined" /></TableCell></TableRow>))}
              <TableRow><TableCell colSpan={2}><b>Total</b></TableCell><TableCell align="right"><b>{brl(st.data.totals.direct)}</b></TableCell><TableCell align="right"><b>{brl(st.data.totals.shared)}</b></TableCell><TableCell align="right"><b>{brl(st.data.totals.total)}</b></TableCell><TableCell align="right"><b>{brl(st.data.totals.billable)}</b></TableCell><TableCell /></TableRow></TableBody></Table>
        </Panel>))}
      <Snackbar open={!!msg} autoHideDuration={4000} onClose={() => setMsg('')} message={msg} />
    </>
  )
}
