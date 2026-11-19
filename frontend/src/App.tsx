import { useEffect, useState } from 'react'
import { NavLink, Route, Routes, Navigate, useLocation } from 'react-router-dom'
import { Box, Chip, List, ListItemButton, ListItemIcon, ListItemText, Typography, Tooltip } from '@mui/material'
import DashboardIcon from '@mui/icons-material/SpaceDashboardOutlined'
import BusinessIcon from '@mui/icons-material/BusinessOutlined'
import AccountTreeIcon from '@mui/icons-material/AccountTreeOutlined'
import SavingsIcon from '@mui/icons-material/SavingsOutlined'
import GavelIcon from '@mui/icons-material/GavelOutlined'
import Inventory2Icon from '@mui/icons-material/Inventory2Outlined'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesomeOutlined'
import CableIcon from '@mui/icons-material/CableOutlined'
import { api, Meta, MetaCtx } from './api'
import { mlong } from './format'
import { C } from './theme'
import { DemoChip, Loading } from './components/ui'
import Executive from './pages/Executive'
import Company from './pages/Company'
import Showback from './pages/Showback'
import Opportunities from './pages/Opportunities'
import Governance from './pages/Governance'
import Inventory from './pages/Inventory'
import Copilot from './pages/Copilot'
import Connections from './pages/Connections'

const NAV = [
  { to: '/executivo', label: 'Executivo · CIO Grupo', icon: <DashboardIcon /> },
  { to: '/empresa', label: 'CIO Empresa', icon: <BusinessIcon /> },
  { to: '/showback', label: 'Showback e Chargeback', icon: <AccountTreeIcon /> },
  { to: '/oportunidades', label: 'FinOps Opportunities', icon: <SavingsIcon /> },
  { to: '/governanca', label: 'Governança', icon: <GavelIcon /> },
  { to: '/inventario', label: 'Inventário Multicloud', icon: <Inventory2Icon /> },
  { to: '/copilot', label: 'IA FinOps Copilot', icon: <AutoAwesomeIcon /> },
  { to: '/conexoes', label: 'Conexões e ETL', icon: <CableIcon /> },
]

export default function App() {
  const [meta, setMeta] = useState<Meta | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const loc = useLocation()
  useEffect(() => { api<Meta>('/api/meta').then(setMeta).catch((e) => setErr(String(e.message))) }, [])
  if (!meta) return <Loading error={err ? `Não foi possível carregar a API: ${err}. Verifique se o backend está em execução.` : null} />
  const title = NAV.find((n) => loc.pathname.startsWith(n.to))?.label ?? ''
  return (
    <MetaCtx.Provider value={meta}>
      <Box sx={{ display: 'flex', minHeight: '100vh' }}>
        <Box component="aside" sx={{ width: 256, flexShrink: 0, bgcolor: C.navy, color: '#fff', position: 'sticky', top: 0, height: '100vh', display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ p: 2.5, pb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
              <Box sx={{ width: 34, height: 34, borderRadius: 2, bgcolor: C.indigo, display: 'grid', placeItems: 'center' }}>
                <svg width="20" height="20" viewBox="0 0 32 32"><path d="M6 22l7-8 5 5 8-11" stroke="#fff" strokeWidth="3.4" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>
              </Box>
              <Box>
                <Typography sx={{ fontWeight: 700, fontSize: 14, lineHeight: 1.15 }}>Simpar FinOps</Typography>
                <Typography sx={{ fontSize: 12, color: '#98A2B3', lineHeight: 1.15 }}>Control Tower</Typography>
              </Box>
            </Box>
          </Box>
          <List sx={{ px: 1.25, flex: 1 }}>
            {NAV.map((n) => (
              <ListItemButton key={n.to} component={NavLink} to={n.to} sx={{ borderRadius: 2, mb: 0.25, color: '#C7CDD9', py: 1,
                '&.active': { bgcolor: 'rgba(79,70,229,.28)', color: '#fff' }, '&:hover': { bgcolor: 'rgba(255,255,255,.06)' } }}>
                <ListItemIcon sx={{ minWidth: 36, color: 'inherit' }}>{n.icon}</ListItemIcon>
                <ListItemText primary={n.label} slotProps={{ primary: { sx: { fontSize: 13.5, fontWeight: 600 } } }} />
              </ListItemButton>
            ))}
          </List>
          <Box sx={{ p: 2, borderTop: '1px solid rgba(255,255,255,.08)' }}>
            <Typography sx={{ fontSize: 11, color: '#98A2B3' }}>Organização</Typography>
            <Typography sx={{ fontSize: 13, fontWeight: 600 }}>{meta.org.name}</Typography>
            <Typography sx={{ fontSize: 11, color: '#667085', mt: 0.5 }}>v1.0 · modo local</Typography>
          </Box>
        </Box>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Box component="header" sx={{ height: 56, px: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between', bgcolor: '#fff', borderBottom: `1px solid ${C.line}`, position: 'sticky', top: 0, zIndex: 5 }}>
            <Typography sx={{ fontWeight: 600, color: C.slate, fontSize: 14 }}>{title}</Typography>
            <Box sx={{ display: 'flex', gap: 1.25, alignItems: 'center' }}>
              <DemoChip />
              <Tooltip title="Mês fechado de referência dos dados"><Chip size="small" variant="outlined" label={`Referência: ${mlong(meta.reference_month)}`} /></Tooltip>
              <Chip size="small" variant="outlined" label="BRL" />
            </Box>
          </Box>
          <Box sx={{ p: 3, maxWidth: 1680, mx: 'auto' }}>
            <Routes>
              <Route path="/" element={<Navigate to="/executivo" replace />} />
              <Route path="/executivo" element={<Executive />} />
              <Route path="/empresa" element={<Company />} />
              <Route path="/empresa/:code" element={<Company />} />
              <Route path="/showback" element={<Showback />} />
              <Route path="/oportunidades" element={<Opportunities />} />
              <Route path="/governanca" element={<Governance />} />
              <Route path="/inventario" element={<Inventory />} />
              <Route path="/copilot" element={<Copilot />} />
              <Route path="/conexoes" element={<Connections />} />
            </Routes>
          </Box>
        </Box>
      </Box>
    </MetaCtx.Provider>
  )
}
