import { useEffect, useRef, useState } from 'react'
import { Avatar, Box, Chip, IconButton, InputBase, Paper, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material'
import SendIcon from '@mui/icons-material/Send'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import { api, useApi } from '../api'
import { PageHeader } from '../components/ui'
import { brl, pct } from '../format'
import { C } from '../theme'

type Msg = { role: 'user' | 'assistant'; content: string; table?: { columns: string[]; rows: any[][] } | null; mode?: string }
const SUGGEST = ['Quanto a Movida gastou em AWS este mês?', 'Qual a maior oportunidade de economia da JSL?', 'Quais recursos sem tag existem na Vamos?', 'Qual o potencial de saving do grupo?',
  'Qual o forecast do grupo?', 'Quais recursos ociosos a Automob tem?', 'Qual a maturidade FinOps das empresas?', 'Budget x realizado por empresa']

const md = (s: string) => s.split(/(\*\*[^*]+\*\*)/g).map((p, i) => p.startsWith('**') ? <b key={i}>{p.slice(2, -2)}</b> : <span key={i}>{p}</span>)
const cell = (v: any, col: string) => typeof v === 'number' ? (/%|Var|Score|^#$/.test(col) ? (col === '#' || col === 'Score' ? v : pct(v, /Var/.test(col))) : /R\$|Custo|Forecast|Faixa|Budget|Economia|Potencial/.test(col) ? brl(v) : v) : v ?? '—'

export default function Copilot() {
  const [msgs, setMsgs] = useState<Msg[]>([{ role: 'assistant', content: 'Olá! Sou o Copilot FinOps do Grupo Simpar. Respondo com base nos dados carregados (custos, oportunidades, tags, budget e forecast). O que você quer saber?' }])
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const status = useApi<any>('/api/copilot/status')
  const end = useRef<HTMLDivElement>(null)
  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth' }) }, [msgs])
  const send = async (m: string) => {
    if (!m.trim() || busy) return
    const hist = msgs.filter((x) => x.content).map((x) => ({ role: x.role, content: x.content }))
    setMsgs((x) => [...x, { role: 'user', content: m }]); setText(''); setBusy(true)
    try { const r = await api('/api/copilot/chat', { method: 'POST', body: JSON.stringify({ message: m, history: hist }) }); setMsgs((x) => [...x, { role: 'assistant', content: r.text, table: r.table, mode: r.mode }]) }
    catch (e: any) { setMsgs((x) => [...x, { role: 'assistant', content: `Erro ao consultar: ${e.message}` }]) } finally { setBusy(false) }
  }
  return (
    <>
      <PageHeader title="IA FinOps Copilot" subtitle="Assistente conversacional sobre os dados carregados" actions={<Chip size="small" variant="outlined" label={status.data?.mode === 'openai' ? `OpenAI · ${status.data.model}` : 'Modo offline (sem OpenAI)'} />} />
      <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 2, alignItems: 'start' }}>
        <Paper variant="outlined" sx={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 210px)', minHeight: 480, borderColor: C.line }}>
          <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
            {msgs.map((m, i) => (
              <Box key={i} sx={{ display: 'flex', gap: 1.5, mb: 2.5, flexDirection: m.role === 'user' ? 'row-reverse' : 'row' }}>
                <Avatar sx={{ width: 32, height: 32, bgcolor: m.role === 'user' ? C.slate : C.indigo }}>{m.role === 'user' ? 'V' : <AutoAwesomeIcon sx={{ fontSize: 18 }} />}</Avatar>
                <Box sx={{ maxWidth: '82%' }}>
                  <Box sx={{ p: 1.75, borderRadius: 3, bgcolor: m.role === 'user' ? C.indigo : '#F4F5F7', color: m.role === 'user' ? '#fff' : C.ink, fontSize: 14, lineHeight: 1.55 }}>{md(m.content)}</Box>
                  {m.table && m.table.rows.length > 0 && (
                    <Box sx={{ mt: 1, border: `1px solid ${C.line}`, borderRadius: 2, overflow: 'hidden', bgcolor: '#fff' }}>
                      <Table size="small"><TableHead><TableRow>{m.table.columns.map((c) => <TableCell key={c}>{c}</TableCell>)}</TableRow></TableHead>
                        <TableBody>{m.table.rows.map((r, ri) => <TableRow key={ri}>{r.map((v, ci) => <TableCell key={ci} align={typeof v === 'number' ? 'right' : 'left'}>{cell(v, m.table!.columns[ci])}</TableCell>)}</TableRow>)}</TableBody></Table>
                    </Box>)}
                </Box>
              </Box>))}
            {busy && <Typography variant="caption" color="text.secondary">Consultando dados…</Typography>}
            <div ref={end} />
          </Box>
          <Box sx={{ p: 2, borderTop: `1px solid ${C.line}`, display: 'flex', gap: 1, alignItems: 'center' }}>
            <InputBase fullWidth placeholder="Pergunte sobre custos, oportunidades, tags, forecast…" value={text} onChange={(e) => setText(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && send(text)} sx={{ px: 2, py: 1, bgcolor: '#F4F5F7', borderRadius: 3 }} />
            <IconButton color="primary" onClick={() => send(text)} disabled={busy}><SendIcon /></IconButton>
          </Box>
        </Paper>
        <Paper variant="outlined" sx={{ p: 2, borderColor: C.line }}>
          <Typography variant="subtitle2" sx={{ mb: 1.5 }}>Perguntas sugeridas</Typography>
          {SUGGEST.map((s) => <Chip key={s} label={s} onClick={() => send(s)} sx={{ mb: 1, mr: 1, height: 'auto', '& .MuiChip-label': { whiteSpace: 'normal', py: 0.75 } }} variant="outlined" />)}
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>As respostas usam somente os dados carregados (simulados). Para respostas em linguagem livre, configure OPENAI_API_KEY no backend.</Typography>
        </Paper>
      </Box>
    </>
  )
}
