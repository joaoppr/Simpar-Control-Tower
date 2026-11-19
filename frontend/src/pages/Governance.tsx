import { useState } from 'react'
import { Box, Chip, MenuItem, Select, Table, TableBody, TableCell, TableHead, TableRow, TablePagination, Typography } from '@mui/material'
import { PolarAngleAxis, PolarGrid, Radar, RadarChart, ResponsiveContainer, Tooltip, PolarRadiusAxis } from 'recharts'
import { useApi, useMeta, qs } from '../api'
import { brl, brlc, num, pct } from '../format'
import { Bar, CloudChip, Grid, Kpi, Loading, PageHeader, Panel, ttStyle } from '../components/ui'
import { C } from '../theme'

const LV: Record<string, string> = { Run: C.teal, Walk: C.amber, Crawl: C.rose }

export default function Governance() {
  const meta = useMeta()
  const [company, setCompany] = useState('')
  const [issue, setIssue] = useState('any')
  const [page, setPage] = useState(0)
  const g = useApi<any>(`/api/governance/summary${qs({ company })}`, [company])
  const v = useApi<any>(`/api/governance/violations${qs({ company, issue, page: page + 1, page_size: 12 })}`, [company, issue, page])
  const d = g.data
  const mat = d?.selected_maturity ?? d?.maturity_group
  return (
    <>
      <PageHeader title="Governança FinOps" subtitle="Conformidade de tags, ownership, padronização e score de maturidade (Crawl · Walk · Run)"
        actions={<Select size="small" displayEmpty value={company} onChange={(e) => { setCompany(e.target.value); setPage(0) }} sx={{ minWidth: 180 }}><MenuItem value="">Grupo Simpar</MenuItem>{meta.companies.map((c) => <MenuItem key={c.code} value={c.code}>{c.name}</MenuItem>)}</Select>} />
      {!d ? <Loading error={g.error} /> : (<>
        <Grid cols="repeat(6, 1fr)">
          <Kpi label="Cobertura de tags" value={pct(d.totals.tag_coverage_cost)} sub={`${pct(d.totals.tag_coverage)} dos recursos`} accent={d.totals.tag_coverage_cost < 70 ? C.rose : C.teal} />
          {d.issues.slice(0, 5).map((i: any) => <Kpi key={i.key} label={i.name.replace('Sem ', 'Recursos sem ')} value={num(i.resources)} sub={`${pct(i.pct_resources)} · ${brlc(i.cost)}/mês`} accent={C.amber} />)}
        </Grid>
        <Grid cols="1fr 1.4fr">
          <Panel title="Score de maturidade FinOps" subtitle={`${mat.name} · 8 dimensões ponderadas`}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ textAlign: 'center', minWidth: 130 }}>
                <Typography sx={{ fontSize: 54, fontWeight: 800, lineHeight: 1, color: LV[mat.level] }}>{mat.score.toFixed(0)}</Typography>
                <Typography variant="caption" color="text.secondary">de 100</Typography><br />
                <Chip label={mat.level} sx={{ mt: 1, bgcolor: LV[mat.level] + '22', color: LV[mat.level], fontWeight: 700 }} />
              </Box>
              <ResponsiveContainer width="100%" height={280}>
                <RadarChart data={mat.dimensions.map((x: any) => ({ ...x, short: x.name.split(' ')[0] }))}>
                  <PolarGrid stroke={C.line} /><PolarAngleAxis dataKey="short" tick={{ fontSize: 11, fill: C.slate }} /><PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                  <Radar isAnimationActive={false} dataKey="score" name="Score" stroke={C.indigo} fill={C.indigo} fillOpacity={0.3} /><Tooltip contentStyle={ttStyle} /></RadarChart></ResponsiveContainer>
            </Box>
            <Box sx={{ mt: 1 }}>{mat.dimensions.map((x: any) => (
              <Box key={x.key} sx={{ display: 'grid', gridTemplateColumns: '190px 1fr 40px', alignItems: 'center', gap: 1, py: 0.4 }}>
                <Typography variant="body2">{x.name} <span style={{ color: C.mute }}>· {x.weight}%</span></Typography><Bar value={x.score} color={x.score >= 75 ? C.teal : x.score >= 45 ? C.amber : C.rose} label="" /><Typography variant="caption" sx={{ fontWeight: 700 }}>{x.score.toFixed(0)}</Typography></Box>))}</Box>
          </Panel>
          <Panel title="Maturidade e conformidade por empresa" pad={1.5}>
            <Table size="small"><TableHead><TableRow><TableCell>Empresa</TableCell><TableCell>Score</TableCell><TableCell>Nível</TableCell><TableCell>Cobertura de tags</TableCell><TableCell align="right">Sem tags</TableCell><TableCell align="right">Sem owner</TableCell><TableCell align="right">Sem produto</TableCell><TableCell align="right">Sem C. custo</TableCell><TableCell align="right">Fora padrão</TableCell></TableRow></TableHead>
              <TableBody>{d.by_company.map((c: any) => { const m = d.maturity.find((x: any) => x.code === c.code); return (
                <TableRow key={c.code} hover selected={c.code === company}><TableCell><b>{c.name}</b></TableCell><TableCell><b>{m?.score.toFixed(0)}</b></TableCell>
                  <TableCell><Chip size="small" label={m?.level} sx={{ bgcolor: LV[m?.level] + '22', color: LV[m?.level], height: 20 }} /></TableCell>
                  <TableCell><Bar value={c.tag_coverage} color={c.tag_coverage < 60 ? C.rose : c.tag_coverage < 75 ? C.amber : C.teal} label={pct(c.tag_coverage, false)} /></TableCell>
                  <TableCell align="right">{num(c.untagged)}</TableCell><TableCell align="right">{num(c.no_owner)}</TableCell><TableCell align="right">{num(c.no_product)}</TableCell><TableCell align="right">{num(c.no_cost_center)}</TableCell><TableCell align="right">{num(c.non_standard)}</TableCell></TableRow>) })}</TableBody></Table>
            <Box sx={{ mt: 2, px: 1 }}><Typography variant="subtitle2" sx={{ mb: 1 }}>Política de tags obrigatórias</Typography>
              {d.policy.map((p: any) => <Chip key={p.tag_key} label={p.tag_key + (p.allowed_values ? ` ∈ {${p.allowed_values.join(', ')}}` : '')} size="small" variant="outlined" sx={{ mr: 1, mb: 1 }} />)}</Box>
          </Panel>
        </Grid>
      </>)}
      <Panel title="Recursos fora de conformidade" subtitle={v.data ? `${num(v.data.total)} recursos · ${brlc(v.data.total_cost)}/mês` : ''} pad={1.5} action={
        <Select size="small" value={issue} onChange={(e) => { setIssue(e.target.value); setPage(0) }} sx={{ minWidth: 210 }}>
          <MenuItem value="any">Qualquer não conformidade</MenuItem><MenuItem value="no_owner">Sem owner</MenuItem><MenuItem value="no_product">Sem produto</MenuItem><MenuItem value="no_application">Sem aplicação</MenuItem>
          <MenuItem value="no_cost_center">Sem centro de custo</MenuItem><MenuItem value="no_environment">Sem ambiente</MenuItem><MenuItem value="non_standard">Fora de padrão</MenuItem></Select>}>
        {!v.data ? <Loading error={v.error} /> : (<>
          <Table size="small"><TableHead><TableRow><TableCell>Recurso</TableCell><TableCell>Empresa</TableCell><TableCell>Cloud</TableCell><TableCell>Serviço</TableCell><TableCell>Conta</TableCell><TableCell align="right">Custo/mês</TableCell><TableCell>Não conformidades</TableCell></TableRow></TableHead>
            <TableBody>{v.data.rows.map((r: any) => (
              <TableRow key={r.resource_id} hover><TableCell><b>{r.resource_name}</b></TableCell><TableCell>{r.company_name}</TableCell><TableCell><CloudChip code={r.cloud_code} /></TableCell><TableCell>{r.service}</TableCell><TableCell>{r.account_name}</TableCell>
                <TableCell align="right">{brl(r.cost_brl)}</TableCell><TableCell>{r.issue_labels.map((l: string) => <Chip key={l} size="small" label={l} sx={{ mr: 0.5, height: 20, fontSize: 10.5, bgcolor: '#FEF3DC', color: '#B45309' }} />)}</TableCell></TableRow>))}</TableBody></Table>
          <TablePagination component="div" count={v.data.total} page={page} onPageChange={(_, p) => setPage(p)} rowsPerPage={12} rowsPerPageOptions={[12]} labelDisplayedRows={({ from, to, count }) => `${from}–${to} de ${count}`} /></>)}
      </Panel>
    </>
  )
}
