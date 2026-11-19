import { Area, Bar, BarChart, CartesianGrid, Cell, ComposedChart, Legend, Line, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { C } from '../theme'
import { brlc, mlabel, CLOUD_COLOR, CLOUD_NAME, PALETTE } from '../format'
import { ttStyle } from './ui'

const ax = { fontSize: 11, fill: C.slate }

export const TrendChart = ({ data, height = 320 }: { data: any[]; height?: number }) => {
  const d = data.map((r) => ({ ...r, band: r.forecast_low != null && r.actual == null ? [r.forecast_low, r.forecast_high] : null, m: mlabel(r.month) }))
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={d} margin={{ left: 4, right: 12, top: 8 }}>
        <defs>
          <linearGradient id="gA" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={C.indigo} stopOpacity={0.25} /><stop offset="100%" stopColor={C.indigo} stopOpacity={0.02} /></linearGradient>
        </defs>
        <CartesianGrid vertical={false} stroke={C.line} />
        <XAxis dataKey="m" tick={ax} axisLine={false} tickLine={false} />
        <YAxis tick={ax} axisLine={false} tickLine={false} width={86} tickFormatter={(v) => brlc(v)} domain={['auto', 'auto']} />
        <Tooltip contentStyle={ttStyle} formatter={(v: any, n: any) => [Array.isArray(v) ? `${brlc(v[0])} – ${brlc(v[1])}` : brlc(v), n]} />
        <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
        <Area isAnimationActive={false} dataKey="band" name="Faixa do forecast" stroke="none" fill={C.amber} fillOpacity={0.16} />
        <Area isAnimationActive={false} dataKey="actual" name="Realizado" stroke={C.indigo} strokeWidth={2.5} fill="url(#gA)" dot={{ r: 3 }} connectNulls={false} />
        <Line isAnimationActive={false} dataKey="budget" name="Budget" stroke={C.slate} strokeWidth={1.75} strokeDasharray="5 4" dot={false} />
        <Line isAnimationActive={false} dataKey="forecast" name="Forecast" stroke={C.amber} strokeWidth={2.5} strokeDasharray="2 4" dot={{ r: 3 }} />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

export const CloudDonut = ({ data, height = 280 }: { data: { code?: string; name: string; cost: number; share: number }[]; height?: number }) => (
  <ResponsiveContainer width="100%" height={height}>
    <PieChart>
      <Pie isAnimationActive={false} data={data} dataKey="cost" nameKey="name" innerRadius="58%" outerRadius="86%" paddingAngle={2} stroke="none">
        {data.map((d, i) => <Cell key={i} fill={CLOUD_COLOR[d.code || ''] || PALETTE[i % PALETTE.length]} />)}
      </Pie>
      <Tooltip contentStyle={ttStyle} formatter={(v: any) => brlc(v)} />
      <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} formatter={(v: any, e: any) => `${v} · ${e.payload.share?.toFixed(1).replace('.', ',')}%`} />
    </PieChart>
  </ResponsiveContainer>
)

export const StackedCompanyCloud = ({ data, height = 320 }: { data: any[]; height?: number }) => {
  const rows = data.map((c) => ({ name: c.name, ...c.by_cloud })).sort((a, b) => 0)
  const clouds = Object.keys(CLOUD_COLOR)
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={rows} layout="vertical" margin={{ left: 12, right: 16 }}>
        <CartesianGrid horizontal={false} stroke={C.line} />
        <XAxis type="number" tick={ax} axisLine={false} tickLine={false} tickFormatter={(v) => brlc(v)} />
        <YAxis type="category" dataKey="name" tick={{ ...ax, fill: C.ink, fontWeight: 600 }} axisLine={false} tickLine={false} width={72} />
        <Tooltip contentStyle={ttStyle} formatter={(v: any, n: any) => [brlc(v), CLOUD_NAME[n] || n]} />
        <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} formatter={(v: any) => CLOUD_NAME[v] || v} />
        {clouds.map((c) => <Bar isAnimationActive={false} key={c} dataKey={c} stackId="a" fill={CLOUD_COLOR[c]} />)}
      </BarChart>
    </ResponsiveContainer>
  )
}

export const BudgetBars = ({ data, height = 320 }: { data: { name: string; actual: number; budget: number; variance_pct: number }[]; height?: number }) => (
  <ResponsiveContainer width="100%" height={height}>
    <BarChart data={data} margin={{ left: 4, right: 8 }}>
      <CartesianGrid vertical={false} stroke={C.line} />
      <XAxis dataKey="name" tick={ax} axisLine={false} tickLine={false} />
      <YAxis tick={ax} axisLine={false} tickLine={false} width={86} tickFormatter={(v) => brlc(v)} />
      <Tooltip contentStyle={ttStyle} formatter={(v: any) => brlc(v)} />
      <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
      <Bar isAnimationActive={false} dataKey="budget" name="Budget" fill="#CBD5E1" radius={[4, 4, 0, 0]} />
      <Bar isAnimationActive={false} dataKey="actual" name="Realizado" radius={[4, 4, 0, 0]}>
        {data.map((d, i) => <Cell key={i} fill={d.variance_pct > 3 ? C.rose : d.variance_pct > 0 ? C.amber : C.teal} />)}
      </Bar>
    </BarChart>
  </ResponsiveContainer>
)

export const SavingsBars = ({ data, potential, height = 300 }: { data: { month: string; captured: number }[]; potential: number; height?: number }) => {
  const d = data.map((r) => ({ m: mlabel(r.month), captured: r.captured, potential }))
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={d} margin={{ left: 4, right: 8 }}>
        <CartesianGrid vertical={false} stroke={C.line} />
        <XAxis dataKey="m" tick={ax} axisLine={false} tickLine={false} />
        <YAxis tick={ax} axisLine={false} tickLine={false} width={86} tickFormatter={(v) => brlc(v)} />
        <Tooltip contentStyle={ttStyle} formatter={(v: any) => brlc(v)} />
        <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
        <Bar isAnimationActive={false} dataKey="captured" name="Economia capturada / mês" fill={C.teal} radius={[4, 4, 0, 0]} />
        <Line isAnimationActive={false} dataKey="potential" name="Potencial em aberto / mês" stroke={C.amber} strokeWidth={2} strokeDasharray="5 4" dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

export const HBars = ({ data, height = 280, color = C.indigo }: { data: { name: string; cost: number }[]; height?: number; color?: string }) => (
  <ResponsiveContainer width="100%" height={height}>
    <BarChart data={data.slice(0, 8)} layout="vertical" margin={{ left: 8, right: 16 }}>
      <CartesianGrid horizontal={false} stroke={C.line} />
      <XAxis type="number" tick={ax} axisLine={false} tickLine={false} tickFormatter={(v) => brlc(v)} />
      <YAxis type="category" dataKey="name" tick={{ ...ax, fill: C.ink }} axisLine={false} tickLine={false} width={150} />
      <Tooltip contentStyle={ttStyle} formatter={(v: any) => brlc(v)} />
      <Bar isAnimationActive={false} dataKey="cost" name="Custo" fill={color} radius={[0, 4, 4, 0]} barSize={16} />
    </BarChart>
  </ResponsiveContainer>
)
