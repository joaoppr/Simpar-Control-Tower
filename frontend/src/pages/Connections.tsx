import { useState } from 'react'
import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Select, Table, TableBody, TableCell, TableHead, TableRow, TextField, ToggleButton, ToggleButtonGroup, Typography, Snackbar, IconButton, Tooltip } from '@mui/material'
import SyncIcon from '@mui/icons-material/Sync'
import PowerIcon from '@mui/icons-material/PowerSettingsNew'
import DeleteIcon from '@mui/icons-material/Delete'
import AddIcon from '@mui/icons-material/Add'
import { api, useApi, useMeta } from '../api'
import { num } from '../format'
import { CloudChip, Grid, Kpi, Loading, PageHeader, Panel, StatusChip } from '../components/ui'
import { C } from '../theme'

const dt = (s?: string) => (s ? new Date(s).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' }) : '—')

export default function Connections() {
  const meta = useMeta()
  const [tick, setTick] = useState(0)
  const conns = useApi<any[]>('/api/connections', [tick])
  const runs = useApi<any[]>('/api/connections/runs/recent', [tick])
  const prov = useApi<any[]>('/api/connections/providers')
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState<any>({ company: 'simpar', cloud: 'aws', display_name: '', mode: 'demo', config: {}, secrets: {} })
  const [msg, setMsg] = useState('')
  const [busy, setBusy] = useState<number | null>(null)
  const spec = prov.data?.find((p) => p.cloud === form.cloud)
  const act = async (id: number, kind: 'test' | 'sync') => {
    setBusy(id)
    try { const r = await api(`/api/connections/${id}/${kind}`, { method: 'POST' }); setMsg(kind === 'test' ? r.message : r.status === 'success' ? `Sincronização concluída (${num(r.rows_cost)} linhas de custo)` : `Falha: ${r.message}`) }
    catch (e: any) { setMsg(e.message) } finally { setBusy(null); setTick((t) => t + 1) }
  }
  const create = async () => {
    const config: any = {}, secrets: any = {}
    spec.fields.forEach((f: any) => { const v = form.config[f.key]; if (v) (f.secret ? secrets : config)[f.key] = v })
    await api('/api/connections', { method: 'POST', body: JSON.stringify({ company: form.company, cloud: form.cloud, display_name: form.display_name || `${form.company} · ${form.cloud}`, mode: form.mode, config, secrets }) })
    setOpen(false); setForm({ ...form, display_name: '', config: {} }); setTick((t) => t + 1); setMsg('Conexão criada. Use "Testar" para validar as credenciais.')
  }
  const list = conns.data ?? []
  return (
    <>
      <PageHeader title="Conexões e ETL" subtitle="Credenciais por tenant/conta/assinatura. Segredos são criptografados (Fernet) e nunca retornam pela API" actions={<Button variant="contained" startIcon={<AddIcon />} onClick={() => setOpen(true)}>Nova conexão</Button>} />
      <Alert severity="info" sx={{ mb: 2 }}>Todas as conexões atuais estão em <b>modo demonstração</b> (dados simulados). Conexões em modo <b>live</b> usam os conectores oficiais — AWS Cost Explorer (primário), Azure Cost Management, OCI Usage API, Google Cloud Billing/BigQuery e Huawei BSS — e exigem os SDKs de <code>requirements-connectors.txt</code>.</Alert>
      <Grid cols="repeat(4, 1fr)">
        <Kpi label="Conexões" value={num(list.length)} /><Kpi label="Conectadas" value={num(list.filter((c) => c.status === 'connected').length)} accent={C.teal} />
        <Kpi label="Com erro" value={num(list.filter((c) => c.status === 'error').length)} accent={C.rose} /><Kpi label="Modo live" value={num(list.filter((c) => c.mode === 'live').length)} accent={C.amber} />
      </Grid>
      <Panel title="Conectores" pad={1.5} sx={{ mb: 2 }}>
        {!conns.data ? <Loading error={conns.error} /> : (
          <Table size="small"><TableHead><TableRow><TableCell>Conexão</TableCell><TableCell>Empresa</TableCell><TableCell>Cloud</TableCell><TableCell>Fonte de custo</TableCell><TableCell>Modo</TableCell><TableCell>Status</TableCell><TableCell>Última sincronização</TableCell><TableCell>Mensagem</TableCell><TableCell align="right">Ações</TableCell></TableRow></TableHead>
            <TableBody>{list.map((c) => (
              <TableRow key={c.id} hover><TableCell><b>{c.display_name}</b></TableCell><TableCell>{c.company_name}</TableCell><TableCell><CloudChip code={c.cloud_code} /></TableCell><TableCell sx={{ color: C.slate, fontSize: 12 }}>{c.cost_source}</TableCell>
                <TableCell>{c.mode === 'live' ? 'Live' : 'Demo'}</TableCell><TableCell><StatusChip v={c.status} /></TableCell><TableCell>{dt(c.last_sync_at)}</TableCell><TableCell sx={{ maxWidth: 260, fontSize: 12, color: C.slate }}>{c.last_message}</TableCell>
                <TableCell align="right" sx={{ whiteSpace: 'nowrap' }}>
                  <Tooltip title="Testar conexão"><span><IconButton size="small" disabled={busy === c.id} onClick={() => act(c.id, 'test')}><PowerIcon fontSize="small" /></IconButton></span></Tooltip>
                  <Tooltip title="Sincronizar (ETL)"><span><IconButton size="small" disabled={busy === c.id} onClick={() => act(c.id, 'sync')}><SyncIcon fontSize="small" /></IconButton></span></Tooltip>
                  <Tooltip title="Remover"><IconButton size="small" onClick={async () => { await api(`/api/connections/${c.id}`, { method: 'DELETE' }); setTick((t) => t + 1) }}><DeleteIcon fontSize="small" /></IconButton></Tooltip></TableCell></TableRow>))}</TableBody></Table>)}
      </Panel>
      <Panel title="Execuções recentes de ETL" pad={1.5}>
        {!runs.data ? <Loading error={runs.error} /> : (
          <Table size="small"><TableHead><TableRow><TableCell>Conexão</TableCell><TableCell>Início</TableCell><TableCell>Status</TableCell><TableCell align="right">Linhas de custo</TableCell><TableCell align="right">Recursos</TableCell><TableCell align="right">Recomendações</TableCell><TableCell>Mensagem</TableCell></TableRow></TableHead>
            <TableBody>{runs.data.slice(0, 12).map((r) => <TableRow key={r.id} hover><TableCell>{r.display_name}</TableCell><TableCell>{dt(r.started_at)}</TableCell><TableCell><StatusChip v={r.status} /></TableCell><TableCell align="right">{num(r.rows_cost)}</TableCell><TableCell align="right">{num(r.rows_resources)}</TableCell><TableCell align="right">{num(r.rows_recs)}</TableCell><TableCell sx={{ fontSize: 12, color: C.slate }}>{r.message}</TableCell></TableRow>)}</TableBody></Table>)}
      </Panel>
      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Nova conexão de cloud</DialogTitle>
        <DialogContent sx={{ display: 'grid', gap: 2, pt: '12px !important' }}>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Select size="small" fullWidth value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })}>{meta.companies.map((c) => <MenuItem key={c.code} value={c.code}>{c.name}</MenuItem>)}</Select>
            <Select size="small" fullWidth value={form.cloud} onChange={(e) => setForm({ ...form, cloud: e.target.value, config: {} })}>{meta.clouds.map((c) => <MenuItem key={c.code} value={c.code}>{c.name}</MenuItem>)}</Select>
          </Box>
          <TextField size="small" label="Nome da conexão" value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} />
          <ToggleButtonGroup size="small" exclusive value={form.mode} onChange={(_, v) => v && setForm({ ...form, mode: v })}><ToggleButton value="demo">Demonstração</ToggleButton><ToggleButton value="live">Live (API real)</ToggleButton></ToggleButtonGroup>
          {spec && <Typography variant="caption" color="text.secondary">Fonte: {spec.cost_source}</Typography>}
          {spec?.fields.map((f: any) => <TextField key={f.key} size="small" label={f.label} placeholder={f.placeholder} type={f.secret ? 'password' : 'text'} multiline={f.key.includes('json') || f.key === 'private_key'} minRows={f.key.includes('json') || f.key === 'private_key' ? 3 : 1}
            value={form.config[f.key] ?? ''} onChange={(e) => setForm({ ...form, config: { ...form.config, [f.key]: e.target.value } })} />)}
        </DialogContent>
        <DialogActions><Button onClick={() => setOpen(false)}>Cancelar</Button><Button variant="contained" onClick={create}>Criar conexão</Button></DialogActions>
      </Dialog>
      <Snackbar open={!!msg} autoHideDuration={5000} onClose={() => setMsg('')} message={msg} />
    </>
  )
}
