import { ReactNode } from 'react'
import { Box, Card, Chip, CircularProgress, Alert, Typography, LinearProgress, Stack } from '@mui/material'
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward'
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward'
import { C } from '../theme'
import { CLOUD_COLOR, CLOUD_NAME } from '../format'

export const Loading = ({ error }: { error?: string | null }) =>
  error ? <Alert severity="error" sx={{ m: 2 }}>{error}</Alert> :
    <Box sx={{ display: 'grid', placeItems: 'center', height: 240 }}><CircularProgress size={28} /></Box>

export const PageHeader = ({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) => (
  <Box sx={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', mb: 2.5, gap: 2, flexWrap: 'wrap' }}>
    <Box>
      <Typography variant="h5">{title}</Typography>
      {subtitle && <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>{subtitle}</Typography>}
    </Box>
    <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>{actions}</Stack>
  </Box>
)

export const Panel = ({ title, subtitle, action, children, sx, pad = 2.5 }: { title?: string; subtitle?: string; action?: ReactNode; children: ReactNode; sx?: any; pad?: number }) => (
  <Card sx={{ p: pad, height: '100%', ...sx }}>
    {(title || action) && (
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1.5, gap: 1 }}>
        <Box>
          <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>{title}</Typography>
          {subtitle && <Typography variant="caption" color="text.secondary">{subtitle}</Typography>}
        </Box>
        {action}
      </Box>
    )}
    {children}
  </Card>
)

export const Grid = ({ cols, gap = 2, children, sx }: { cols: string; gap?: number; children: ReactNode; sx?: any }) => (
  <Box sx={{ display: 'grid', gridTemplateColumns: cols, gap, mb: 2, ...sx }}>{children}</Box>
)

export const Kpi = ({ label, value, sub, delta, good, accent = C.indigo, hint }: { label: string; value: string; sub?: string; delta?: number | null; good?: 'down' | 'up'; accent?: string; hint?: string }) => {
  const up = (delta ?? 0) > 0
  const isGood = delta == null ? true : good === 'down' ? !up : good === 'up' ? up : true
  return (
    <Card sx={{ p: 2.25, position: 'relative', overflow: 'hidden' }} title={hint}>
      <Box sx={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 4, bgcolor: accent }} />
      <Typography variant="caption" sx={{ color: C.slate, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 11 }}>{label}</Typography>
      <Typography sx={{ fontSize: 26, fontWeight: 700, letterSpacing: '-0.02em', lineHeight: 1.25, mt: 0.5 }}>{value}</Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5, minHeight: 20 }}>
        {delta != null && (
          <Box sx={{ display: 'inline-flex', alignItems: 'center', color: isGood ? C.teal : C.rose, fontWeight: 700, fontSize: 12 }}>
            {up ? <ArrowUpwardIcon sx={{ fontSize: 14 }} /> : <ArrowDownwardIcon sx={{ fontSize: 14 }} />}{Math.abs(delta).toFixed(1).replace('.', ',')}%
          </Box>
        )}
        {sub && <Typography variant="caption" color="text.secondary">{sub}</Typography>}
      </Box>
    </Card>
  )
}

export const CloudChip = ({ code, size = 'small' }: { code: string; size?: 'small' | 'medium' }) => (
  <Chip size={size} label={CLOUD_NAME[code] || code} sx={{ bgcolor: (CLOUD_COLOR[code] || '#64748B') + '1A', color: CLOUD_COLOR[code] || '#475467', height: 22, fontSize: 11 }} />
)

const LV: Record<string, string> = { Baixo: C.teal, Médio: C.amber, Alto: C.rose, P1: C.rose, P2: C.amber, P3: '#64748B' }
export const LevelChip = ({ v }: { v: string }) => (
  <Chip size="small" label={v} sx={{ bgcolor: (LV[v] || '#64748B') + '1F', color: LV[v] === C.amber ? '#B45309' : LV[v] || '#475467', height: 22, fontSize: 11 }} />
)

export const StatusChip = ({ v }: { v: string }) => {
  const m: Record<string, string> = { Identificada: '#64748B', 'Em análise': C.indigo, Aprovada: '#2563EB', 'Em execução': C.amber, Capturada: C.teal,
    connected: C.teal, error: C.rose, pending: C.amber, success: C.teal, running: C.amber }
  const lbl: Record<string, string> = { connected: 'Conectado', error: 'Erro', pending: 'Pendente', success: 'Sucesso', running: 'Executando' }
  return <Chip size="small" label={lbl[v] || v} sx={{ bgcolor: (m[v] || '#64748B') + '1F', color: m[v] === C.amber ? '#B45309' : m[v], height: 22, fontSize: 11 }} />
}

export const Bar = ({ value, color = C.indigo, label }: { value: number; color?: string; label?: string }) => (
  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 120 }}>
    <LinearProgress variant="determinate" value={Math.min(100, Math.max(0, value))} sx={{ flex: 1, height: 6, borderRadius: 3, bgcolor: '#EEF0F4', '& .MuiLinearProgress-bar': { bgcolor: color } }} />
    <Typography variant="caption" sx={{ width: 44, textAlign: 'right', fontWeight: 600 }}>{label ?? `${value.toFixed(0)}%`}</Typography>
  </Box>
)

export const DemoChip = () => (
  <Chip size="small" label="DADOS SIMULADOS" sx={{ bgcolor: '#FEF3DC', color: '#B45309', fontWeight: 700, fontSize: 10, letterSpacing: '0.06em' }} />
)

export const ttStyle = { borderRadius: 10, border: `1px solid ${C.line}`, boxShadow: '0 6px 24px rgba(16,24,40,.08)', fontSize: 12 }
