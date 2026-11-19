import { useState } from 'react'
import { Box, Button, Chip, FormControlLabel, MenuItem, Select, Switch, Table, TableBody, TableCell, TableHead, TableRow, TablePagination, TableSortLabel, TextField, Typography } from '@mui/material'
import DownloadIcon from '@mui/icons-material/Download'
import { useApi, qs } from '../api'
import { brl, brlc, num, CLOUD_NAME } from '../format'
import { CloudChip, Kpi, Grid, Loading, PageHeader, Panel } from '../components/ui'
import { C } from '../theme'

const F = ({ label, value, set, items, fmt }: any) => (
  <Select size="small" displayEmpty value={value} onChange={(e) => set(e.target.value)} sx={{ minWidth: 140, fontSize: 13 }}>
    <MenuItem value="">{label}</MenuItem>
    {items.map((i: any) => <MenuItem key={i.value} value={i.value}>{(fmt ? fmt(i.value) : i.value) || '(vazio)'} · {i.n}</MenuItem>)}
  </Select>
)

export default function Inventory() {
  const [f, setF] = useState<any>({ company: '', cloud: '', service: '', region: '', environment: '', owner: '', product: '' })
  const [search, setSearch] = useState('')
  const [tagged, setTagged] = useState<string>('')
  const [idle, setIdle] = useState(false)
  const [sort, setSort] = useState('cost')
  const [dir, setDir] = useState('desc')
  const [page, setPage] = useState(0)
  const [size, setSize] = useState(25)
  const facets = useApi<any>('/api/inventory/facets')
  const params = { ...f, q: search, tagged: tagged === '' ? undefined : tagged, idle: idle ? true : undefined, sort, dir, page: page + 1, page_size: size }
  const { data, error } = useApi<any>(`/api/inventory${qs(params)}`, [JSON.stringify(params)])
  const set = (k: string) => (v: string) => { setF((o: any) => ({ ...o, [k]: v })); setPage(0) }
  const th = (k: string, label: string, right = false) => (
    <TableCell align={right ? 'right' : 'left'}><TableSortLabel active={sort === k} direction={dir as any} onClick={() => { setSort(k); setDir(sort === k && dir === 'desc' ? 'asc' : 'desc') }}>{label}</TableSortLabel></TableCell>)
  const fa = facets.data
  return (
    <>
      <PageHeader title="Inventário Multicloud" subtitle="Visão única de recursos de AWS, Azure, OCI, Google Cloud e Huawei com custo mensal e atributos de governança"
        actions={<Button startIcon={<DownloadIcon />} variant="outlined" href={`/api/inventory/export.csv${qs({ company: f.company, cloud: f.cloud, service: f.service, tagged: tagged || undefined })}`}>Exportar CSV</Button>} />
      <Panel sx={{ mb: 2 }} pad={2}>
        <Box sx={{ display: 'flex', gap: 1.25, flexWrap: 'wrap', alignItems: 'center' }}>
          <TextField size="small" placeholder="Buscar por recurso, aplicação ou owner" value={search} onChange={(e) => { setSearch(e.target.value); setPage(0) }} sx={{ width: 300 }} />
          {fa && <>
            <F label="Empresa" value={f.company} set={set('company')} items={fa.company} />
            <F label="Cloud" value={f.cloud} set={set('cloud')} items={fa.cloud} fmt={(v: string) => CLOUD_NAME[v]} />
            <F label="Serviço" value={f.service} set={set('service')} items={fa.service} />
            <F label="Região" value={f.region} set={set('region')} items={fa.region} />
            <F label="Ambiente" value={f.environment} set={set('environment')} items={fa.environment} />
            <F label="Produto" value={f.product} set={set('product')} items={fa.product.filter((x: any) => x.value)} />
          </>}
          <Select size="small" displayEmpty value={tagged} onChange={(e) => { setTagged(e.target.value); setPage(0) }} sx={{ minWidth: 150 }}><MenuItem value="">Tags: todos</MenuItem><MenuItem value="true">Tags completas</MenuItem><MenuItem value="false">Tags incompletas</MenuItem></Select>
          <FormControlLabel control={<Switch size="small" checked={idle} onChange={(e) => { setIdle(e.target.checked); setPage(0) }} />} label={<Typography variant="body2">Somente ociosos/órfãos</Typography>} />
          <Button size="small" onClick={() => { setF({ company: '', cloud: '', service: '', region: '', environment: '', owner: '', product: '' }); setSearch(''); setTagged(''); setIdle(false); setPage(0) }}>Limpar</Button>
        </Box>
      </Panel>
      {!data ? <Loading error={error} /> : (<>
        <Grid cols="repeat(3, 1fr)"><Kpi label="Recursos no filtro" value={num(data.total)} /><Kpi label="Custo mensal no filtro" value={brlc(data.total_cost)} accent={C.teal} /><Kpi label="Custo médio por recurso" value={brl(data.total ? data.total_cost / data.total : 0)} accent={C.amber} /></Grid>
        <Panel pad={0}>
          <Box sx={{ overflow: 'auto' }}>
            <Table size="small"><TableHead><TableRow>{th('company', 'Empresa')}{th('cloud', 'Cloud')}<TableCell>Conta</TableCell>{th('service', 'Serviço')}{th('name', 'Recurso')}{th('region', 'Região')}{th('owner', 'Owner')}{th('product', 'Produto')}{th('application', 'Aplicação')}{th('environment', 'Ambiente')}{th('cost', 'Custo mensal', true)}<TableCell>Status</TableCell></TableRow></TableHead>
              <TableBody>{data.rows.map((r: any) => (
                <TableRow key={r.resource_id} hover><TableCell>{r.company_name}</TableCell><TableCell><CloudChip code={r.cloud_code} /></TableCell><TableCell sx={{ color: C.slate }}>{r.account_name}</TableCell><TableCell>{r.service}</TableCell>
                  <TableCell><b>{r.resource_name}</b></TableCell><TableCell>{r.region}</TableCell><TableCell sx={{ color: r.owner ? undefined : C.rose }}>{r.owner ?? '—'}</TableCell><TableCell sx={{ color: r.product_name ? undefined : C.rose }}>{r.product_name ?? '—'}</TableCell>
                  <TableCell>{r.application_name ?? '—'}</TableCell><TableCell>{r.environment ?? '—'}</TableCell><TableCell align="right"><b>{brl(r.cost_brl)}</b></TableCell>
                  <TableCell sx={{ whiteSpace: 'nowrap' }}>{!r.fully_tagged && <Chip size="small" label="tags" sx={{ mr: 0.5, height: 20, bgcolor: '#FEF3DC', color: '#B45309' }} />}{r.idle && <Chip size="small" label="ocioso" sx={{ mr: 0.5, height: 20, bgcolor: '#FDECEF', color: C.rose }} />}{r.is_optimized && <Chip size="small" label="otimizado" sx={{ height: 20, bgcolor: '#E3F5F2', color: C.teal }} />}</TableCell></TableRow>))}</TableBody></Table>
          </Box>
          <TablePagination component="div" count={data.total} page={page} onPageChange={(_, p) => setPage(p)} rowsPerPage={size} onRowsPerPageChange={(e) => { setSize(+e.target.value); setPage(0) }} rowsPerPageOptions={[25, 50, 100]} labelRowsPerPage="Linhas" labelDisplayedRows={({ from, to, count }) => `${from}–${to} de ${count}`} />
        </Panel></>)}
    </>
  )
}
