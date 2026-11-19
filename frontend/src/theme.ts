import { createTheme } from '@mui/material/styles'

export const C = { ink: '#101828', slate: '#475467', mute: '#98A2B3', line: '#E4E7EC', bg: '#F6F7F9', panel: '#FFFFFF',
  indigo: '#4F46E5', teal: '#0E9F8E', amber: '#F59E0B', rose: '#E11D48', navy: '#0B1220' }

export const theme = createTheme({
  palette: { primary: { main: C.indigo }, secondary: { main: C.teal }, background: { default: C.bg, paper: C.panel },
    text: { primary: C.ink, secondary: C.slate }, divider: C.line },
  shape: { borderRadius: 12 },
  typography: { fontFamily: '"Inter","Segoe UI",system-ui,sans-serif', h4: { fontWeight: 700, letterSpacing: '-0.02em' },
    h5: { fontWeight: 700, letterSpacing: '-0.01em' }, h6: { fontWeight: 650 }, button: { textTransform: 'none', fontWeight: 600 } },
  components: {
    MuiPaper: { styleOverrides: { root: { backgroundImage: 'none' } } },
    MuiCard: { styleOverrides: { root: { border: `1px solid ${C.line}`, boxShadow: 'none' } } },
    MuiTableCell: { styleOverrides: { root: { borderColor: C.line, padding: '9px 12px' },
      head: { fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: C.slate, background: '#FAFAFB' } } },
    MuiChip: { styleOverrides: { root: { fontWeight: 600 } } },
    MuiTab: { styleOverrides: { root: { minHeight: 40 } } },
  },
})
