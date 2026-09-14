import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { Scale, Trash2 } from 'lucide-react'

export default function CompareInvestments({ selectedAssets = [], onRemoveAsset, allAssets = [] }) {
  // Map selected items
  const itemsToCompare = (allAssets || []).filter((a) => selectedAssets.some((s) => s.id === a.id))

  if (itemsToCompare.length < 2) {
    return (
      <div className="w-full bg-card border border-border/80 rounded-2xl p-6 shadow-sm flex flex-col items-center justify-center text-center gap-4 min-h-[250px]">
        <div className="p-3 rounded-full bg-primary/10 text-primary">
          <Scale className="h-6 w-6" />
        </div>
        <div>
          <h4 className="font-bold text-foreground">Compare Investments (2 to 5 Assets)</h4>
          <p className="text-xs text-text-muted mt-1 max-w-md">
            Click <strong>"+ Compare"</strong> on any opportunity card above to compare metrics
            side-by-side.
          </p>
        </div>
      </div>
    )
  }

  // Build Recharts comparison dataset
  const chartData = itemsToCompare.map((item) => ({
    name: item.symbol,
    Opportunity: item.scores.opportunity_score,
    Demand: item.scores.demand_score,
    Momentum: item.scores.momentum_score,
    Fundamental: item.scores.fundamental_score || 70,
    RiskAdjusted: item.scores.risk_adjusted_score,
  }))

  return (
    <div className="w-full bg-card border border-border/80 rounded-2xl p-5 md:p-6 shadow-sm flex flex-col gap-6">
      <div className="flex items-center justify-between border-b border-border/60 pb-4">
        <div>
          <h3 className="text-lg font-bold text-foreground tracking-tight flex items-center gap-2">
            ⚖️ Investment Comparison Tool
          </h3>
          <p className="text-xs text-text-muted">
            Side-by-side score comparison, yield signals, and risk balance across selected assets
          </p>
        </div>
        <span className="text-xs font-mono font-bold text-primary px-3 py-1 bg-primary/10 rounded-lg">
          {itemsToCompare.length} / 5 Assets Selected
        </span>
      </div>

      {/* Comparison Chart */}
      <div className="w-full bg-background border border-border/80 rounded-2xl p-4 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" opacity={0.5} />
            <XAxis dataKey="name" stroke="#a1a1aa" fontSize={11} />
            <YAxis domain={[0, 100]} stroke="#a1a1aa" fontSize={11} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#18181b',
                borderColor: '#27272a',
                borderRadius: '8px',
                fontSize: '11px',
              }}
            />
            <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
            <Bar dataKey="Opportunity" fill="#10B981" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Demand" fill="#3B82F6" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Momentum" fill="#F59E0B" radius={[4, 4, 0, 0]} />
            <Bar dataKey="RiskAdjusted" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Side by Side Comparison Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-border/60 text-text-muted font-bold">
              <th className="p-3 bg-muted/30">Metric</th>
              {itemsToCompare.map((item) => (
                <th key={item.id} className="p-3 bg-muted/30 min-w-[160px]">
                  <div className="flex items-center justify-between">
                    <span>{item.name}</span>
                    <button
                      onClick={() => onRemoveAsset && onRemoveAsset(item.id)}
                      className="p-1 text-text-muted hover:text-rose-500 transition-colors"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border/40 font-medium">
            <tr>
              <td className="p-3 text-text-muted font-semibold bg-muted/10">Category / Symbol</td>
              {itemsToCompare.map((item) => (
                <td key={item.id} className="p-3 font-mono">
                  {item.asset_category} ({item.symbol})
                </td>
              ))}
            </tr>
            <tr>
              <td className="p-3 text-text-muted font-semibold bg-muted/10">Price / NAV</td>
              {itemsToCompare.map((item) => (
                <td key={item.id} className="p-3 font-mono font-bold text-foreground">
                  {item.currency === 'INR' ? '₹' : '$'}
                  {Number(item.price).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                </td>
              ))}
            </tr>
            <tr>
              <td className="p-3 text-text-muted font-semibold bg-muted/10">Opportunity Score</td>
              {itemsToCompare.map((item) => (
                <td key={item.id} className="p-3 font-mono font-black text-emerald-500">
                  {item.scores.opportunity_score}/100
                </td>
              ))}
            </tr>
            <tr>
              <td className="p-3 text-text-muted font-semibold bg-muted/10">Demand Score</td>
              {itemsToCompare.map((item) => (
                <td key={item.id} className="p-3 font-mono font-bold text-blue-500">
                  {item.scores.demand_score}/100
                </td>
              ))}
            </tr>
            <tr>
              <td className="p-3 text-text-muted font-semibold bg-muted/10">Risk-Adjusted Score</td>
              {itemsToCompare.map((item) => (
                <td key={item.id} className="p-3 font-mono font-bold text-purple-500">
                  {item.scores.risk_adjusted_score}/100
                </td>
              ))}
            </tr>
            <tr>
              <td className="p-3 text-text-muted font-semibold bg-muted/10">Risk Profile</td>
              {itemsToCompare.map((item) => (
                <td key={item.id} className="p-3">
                  <span className="px-2 py-0.5 rounded bg-muted text-[10px] font-bold">
                    {item.risk_level}
                  </span>
                </td>
              ))}
            </tr>
            <tr>
              <td className="p-3 text-text-muted font-semibold bg-muted/10">Suggested Horizon</td>
              {itemsToCompare.map((item) => (
                <td key={item.id} className="p-3 text-text-muted font-mono">
                  {item.suggested_horizon}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}
