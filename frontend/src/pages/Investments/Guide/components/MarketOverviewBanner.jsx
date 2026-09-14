import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Activity, Clock, ShieldCheck, AlertCircle } from 'lucide-react'

export default function MarketOverviewBanner({ overview, isLoading, isError }) {
  if (isLoading) {
    return (
      <div className="w-full bg-card/60 backdrop-blur-md border border-border/60 rounded-2xl p-6 animate-pulse flex flex-col gap-4">
        <div className="h-6 w-48 bg-muted rounded-md" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="h-24 bg-muted/50 rounded-xl" />
          <div className="h-24 bg-muted/50 rounded-xl" />
          <div className="h-24 bg-muted/50 rounded-xl" />
        </div>
      </div>
    )
  }

  if (isError || !overview) {
    return (
      <div className="w-full bg-destructive/10 border border-destructive/20 rounded-2xl p-6 flex items-center gap-4 text-destructive">
        <AlertCircle className="h-6 w-6 shrink-0" />
        <div>
          <h4 className="font-bold">Market Overview Unavailable</h4>
          <p className="text-xs opacity-90">
            Live indices currently unreachable. Falling back to cached baseline indicators.
          </p>
        </div>
      </div>
    )
  }

  const {
    nifty_50,
    sensex,
    bank_nifty,
    market_direction,
    market_breadth,
    volatility_index,
    updated_at,
    source,
    is_stale,
  } = overview

  const renderIndexCard = (indexData) => {
    if (!indexData) return null
    const isPositive = Number(indexData.change_percent) >= 0

    return (
      <div className="bg-background/80 border border-border/80 rounded-xl p-4 flex flex-col gap-1 shadow-sm hover:border-primary/40 transition-all">
        <div className="flex items-center justify-between text-xs font-bold text-text-muted">
          <span>{indexData.name}</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted font-mono">
            {indexData.status}
          </span>
        </div>
        <div className="text-xl font-black text-foreground tracking-tight">
          ₹{Number(indexData.value).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
        </div>
        <div
          className={`flex items-center gap-1 text-xs font-bold ${isPositive ? 'text-emerald-500' : 'text-rose-500'}`}
        >
          {isPositive ? (
            <TrendingUp className="h-3.5 w-3.5" />
          ) : (
            <TrendingDown className="h-3.5 w-3.5" />
          )}
          <span>
            {isPositive ? '+' : ''}
            {Number(indexData.change).toFixed(2)} ({isPositive ? '+' : ''}
            {Number(indexData.change_percent).toFixed(2)}%)
          </span>
        </div>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full bg-card border border-border/80 rounded-2xl p-5 md:p-6 shadow-sm flex flex-col gap-5"
    >
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/60 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
            <Activity className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-foreground tracking-tight flex items-center gap-2">
              Market Intelligence Overview
              {is_stale && (
                <span className="text-[10px] bg-amber-500/10 text-amber-500 px-2 py-0.5 rounded-md font-bold">
                  Stale Cache
                </span>
              )}
            </h2>
            <p className="text-xs text-text-muted">
              Real-time benchmark indices and macro volatility parameters
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-muted/60 text-text-secondary font-medium">
            <ShieldCheck className="h-3.5 w-3.5 text-primary" />
            <span>
              Source: <strong>{source}</strong>
            </span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-muted/60 text-text-muted">
            <Clock className="h-3.5 w-3.5" />
            <span>
              Updated:{' '}
              {new Date(updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        </div>
      </div>

      {/* Main Benchmark Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {renderIndexCard(nifty_50)}
        {renderIndexCard(sensex)}
        {renderIndexCard(bank_nifty)}
      </div>

      {/* Market Parameters Footer */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 text-xs font-semibold">
        <div className="flex items-center justify-between p-3 rounded-xl bg-muted/40 border border-border/40">
          <span className="text-text-muted">Market Direction:</span>
          <span className="text-primary font-bold">{market_direction}</span>
        </div>
        <div className="flex items-center justify-between p-3 rounded-xl bg-muted/40 border border-border/40">
          <span className="text-text-muted">Market Breadth:</span>
          <span className="text-foreground font-bold">{market_breadth}</span>
        </div>
        <div className="flex items-center justify-between p-3 rounded-xl bg-muted/40 border border-border/40">
          <span className="text-text-muted">Volatility (VIX):</span>
          <span className="text-emerald-500 font-bold">{volatility_index} (Low Volatility)</span>
        </div>
      </div>
    </motion.div>
  )
}
