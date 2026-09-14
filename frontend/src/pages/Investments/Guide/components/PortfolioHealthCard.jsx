import { HeartPulse, ShieldAlert, Info } from 'lucide-react'

export default function PortfolioHealthCard({ analysis, isLoading }) {
  if (isLoading) {
    return (
      <div className="w-full bg-card border border-border/80 rounded-2xl p-6 animate-pulse flex flex-col gap-4">
        <div className="h-6 w-48 bg-muted rounded-md" />
        <div className="h-32 bg-muted/40 rounded-xl" />
      </div>
    )
  }

  if (!analysis) return null

  const {
    diversification_score,
    concentration_risk,
    liquidity_score,
    portfolio_health_score,
    growth_exposure_percent,
    observations,
  } = analysis

  const getHealthColor = (score) => {
    if (score >= 75) return 'text-emerald-500 bg-emerald-500/10 border-emerald-500/30'
    if (score >= 55) return 'text-blue-500 bg-blue-500/10 border-blue-500/30'
    return 'text-amber-500 bg-amber-500/10 border-amber-500/30'
  }

  return (
    <div className="w-full bg-card border border-border/80 rounded-2xl p-5 md:p-6 shadow-sm flex flex-col gap-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/60 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
            <HeartPulse className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-foreground tracking-tight">
              Portfolio Health & Integration Analysis
            </h3>
            <p className="text-xs text-text-muted">
              Evaluates active holdings from your portfolio for diversification, concentration risk,
              and liquidity
            </p>
          </div>
        </div>

        <div
          className={`flex items-center gap-3 px-4 py-2 rounded-xl border ${getHealthColor(portfolio_health_score)} font-mono`}
        >
          <span className="text-xs font-sans font-bold uppercase tracking-wider text-text-muted">
            Health Score
          </span>
          <span className="text-xl font-black">{portfolio_health_score}/100</span>
        </div>
      </div>

      {/* Main Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-background border border-border/60 rounded-xl p-3.5 flex flex-col gap-1">
          <span className="text-[11px] text-text-muted font-medium">Diversification</span>
          <span className="text-base font-black text-foreground font-mono">
            {diversification_score}/100
          </span>
        </div>

        <div className="bg-background border border-border/60 rounded-xl p-3.5 flex flex-col gap-1">
          <span className="text-[11px] text-text-muted font-medium">Concentration Risk</span>
          <span
            className={`text-base font-black font-mono ${concentration_risk === 'High' ? 'text-rose-500' : 'text-emerald-500'}`}
          >
            {concentration_risk}
          </span>
        </div>

        <div className="bg-background border border-border/60 rounded-xl p-3.5 flex flex-col gap-1">
          <span className="text-[11px] text-text-muted font-medium">Liquidity Score</span>
          <span className="text-base font-black text-foreground font-mono">
            {liquidity_score}/100
          </span>
        </div>

        <div className="bg-background border border-border/60 rounded-xl p-3.5 flex flex-col gap-1">
          <span className="text-[11px] text-text-muted font-medium">Growth Exposure</span>
          <span className="text-base font-black text-primary font-mono">
            {growth_exposure_percent}%
          </span>
        </div>
      </div>

      {/* Actionable Observations */}
      <div className="bg-background border border-border/80 rounded-2xl p-4 flex flex-col gap-3">
        <h4 className="text-xs font-bold text-foreground uppercase tracking-wider flex items-center gap-1.5">
          <ShieldAlert className="h-4 w-4 text-primary" /> Actionable Observations
        </h4>

        {observations && observations.length > 0 ? (
          <ul className="space-y-2 text-xs text-text-muted">
            {observations.map((obs, i) => (
              <li
                key={i}
                className="flex items-start gap-2 bg-muted/30 p-2.5 rounded-xl border border-border/40"
              >
                <Info className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                <span className="leading-relaxed">{obs}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-text-muted">
            Your active portfolio shows a balanced diversification score with healthy risk parameter
            controls.
          </p>
        )}
      </div>
    </div>
  )
}
