import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Filter, HelpCircle, CheckCircle2, X } from 'lucide-react'

const CATEGORIES = [
  'All Assets',
  'Stocks',
  'Mutual Funds',
  'ETFs',
  'Gold',
  'Bonds',
  'T-Bills',
  'FD/RD',
  'Crypto',
]

export default function OpportunityScanner({
  opportunities,
  isLoading,
  onSelectForCompare,
  selectedCompareIds = [],
}) {
  const [selectedCategory, setSelectedCategory] = useState('All Assets')
  const [searchQuery, setSearchQuery] = useState('')
  const [minScore, setMinScore] = useState(0)
  const [activeModalItem, setActiveModalItem] = useState(null)

  const filtered = (opportunities || []).filter((item) => {
    if (
      selectedCategory !== 'All Assets' &&
      item.asset_category.lower() !== selectedCategory.lower()
    ) {
      return false
    }
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      const matchName = item.name.toLowerCase().includes(q)
      const matchSym = item.symbol.toLowerCase().includes(q)
      const matchCat = item.asset_category.toLowerCase().includes(q)
      if (!matchName && !matchSym && !matchCat) return false
    }
    if (item.scores.opportunity_score < minScore) return false
    return true
  })

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-emerald-500 bg-emerald-500/10 border-emerald-500/30'
    if (score >= 60) return 'text-blue-500 bg-blue-500/10 border-blue-500/30'
    if (score >= 40) return 'text-amber-500 bg-amber-500/10 border-amber-500/30'
    return 'text-rose-500 bg-rose-500/10 border-rose-500/30'
  }

  const getRiskBadge = (risk) => {
    switch (risk?.toLowerCase()) {
      case 'low':
        return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'
      case 'moderate':
        return 'bg-blue-500/10 text-blue-500 border-blue-500/20'
      case 'high':
        return 'bg-amber-500/10 text-amber-500 border-amber-500/20'
      case 'very high':
        return 'bg-rose-500/10 text-rose-500 border-rose-500/20'
      default:
        return 'bg-muted text-text-muted border-border'
    }
  }

  return (
    <div className="w-full bg-card border border-border/80 rounded-2xl p-5 md:p-6 shadow-sm flex flex-col gap-6">
      {/* Section Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/60 pb-4">
        <div>
          <h3 className="text-lg font-bold text-foreground tracking-tight flex items-center gap-2">
            🎯 Investment Opportunity Scanner
          </h3>
          <p className="text-xs text-text-muted">
            Data-driven market signals, demand velocity, and normalized scoring across asset classes
          </p>
        </div>

        {/* Search Bar & Slider */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative shrink-0 w-full sm:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
            <input
              type="text"
              placeholder="Search symbol or name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-muted/40 border border-border/60 rounded-xl text-xs text-foreground placeholder:text-text-muted focus:outline-none focus:border-primary transition-all"
            />
          </div>
          <div className="flex items-center gap-2 text-xs font-semibold text-text-muted bg-muted/40 px-3 py-2 rounded-xl border border-border/60">
            <Filter className="h-3.5 w-3.5 text-primary" />
            <span>Min Score:</span>
            <span className="font-bold text-foreground font-mono">{minScore}</span>
            <input
              type="range"
              min="0"
              max="90"
              step="5"
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
              className="w-20 accent-primary cursor-pointer"
            />
          </div>
        </div>
      </div>

      {/* Category Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto scrollbar-none pb-1">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold shrink-0 transition-all ${
              selectedCategory === cat
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'bg-muted/40 text-text-muted hover:text-foreground hover:bg-muted/80'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Grid of Cards */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div key={n} className="h-48 bg-muted/40 rounded-2xl animate-pulse" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="py-12 text-center text-text-muted text-xs bg-muted/20 rounded-2xl border border-dashed border-border/60">
          No investment opportunities match the selected category and filters.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((item) => {
            const isSelectedForCompare = selectedCompareIds.includes(item.id)
            return (
              <motion.div
                key={item.id}
                layout
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-background border border-border/80 hover:border-primary/50 rounded-2xl p-5 flex flex-col justify-between gap-4 transition-all shadow-sm group relative overflow-hidden"
              >
                {/* Card Top Header */}
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted px-2 py-0.5 rounded bg-muted">
                        {item.asset_category}
                      </span>
                      <h4 className="text-sm font-black text-foreground mt-1 tracking-tight group-hover:text-primary transition-colors">
                        {item.name}
                      </h4>
                      <p className="text-xs font-mono text-text-muted">{item.symbol}</p>
                    </div>

                    {/* Opportunity Score Pill */}
                    <div
                      className={`flex flex-col items-center justify-center p-2.5 rounded-xl border font-mono ${getScoreColor(
                        item.scores.opportunity_score
                      )}`}
                    >
                      <span className="text-[9px] uppercase font-sans font-bold opacity-80">
                        Opp Score
                      </span>
                      <span className="text-lg font-black leading-none mt-0.5">
                        {item.scores.opportunity_score}
                      </span>
                    </div>
                  </div>

                  {/* Price & Change */}
                  <div className="flex items-center gap-2 mt-3 text-xs">
                    <span className="font-bold text-foreground font-mono">
                      {item.currency === 'INR' ? '₹' : '$'}
                      {Number(item.price).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </span>
                    <span
                      className={`font-semibold text-[11px] ${
                        Number(item.change_percent) >= 0 ? 'text-emerald-500' : 'text-rose-500'
                      }`}
                    >
                      {Number(item.change_percent) >= 0 ? '+' : ''}
                      {Number(item.change_percent).toFixed(2)}%
                    </span>
                  </div>

                  {/* Multi-Score Bar Metrics */}
                  <div className="grid grid-cols-3 gap-2 my-3 py-2 border-y border-border/50 text-[11px]">
                    <div>
                      <span className="text-text-muted block text-[9px]">Demand</span>
                      <span className="font-bold text-foreground font-mono">
                        {item.scores.demand_score}/100
                      </span>
                    </div>
                    <div>
                      <span className="text-text-muted block text-[9px]">Momentum</span>
                      <span className="font-bold text-foreground font-mono">
                        {item.scores.momentum_score}/100
                      </span>
                    </div>
                    <div>
                      <span className="text-text-muted block text-[9px]">Risk-Adj</span>
                      <span className="font-bold text-foreground font-mono">
                        {item.scores.risk_adjusted_score}/100
                      </span>
                    </div>
                  </div>

                  {/* Demand Rationale summary */}
                  <p className="text-xs text-text-muted line-clamp-2 leading-relaxed">
                    💡 {item.demand_rationale}
                  </p>
                </div>

                {/* Card Footer Badges & Actions */}
                <div className="pt-2 border-t border-border/40 flex flex-wrap items-center justify-between gap-2 text-xs">
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${getRiskBadge(item.risk_level)}`}
                    >
                      {item.risk_level} Risk
                    </span>
                    <span className="text-[10px] font-semibold text-text-muted bg-muted px-2 py-0.5 rounded-md">
                      {item.suggested_horizon}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => onSelectForCompare && onSelectForCompare(item)}
                      className={`text-[11px] font-bold px-2.5 py-1 rounded-lg border transition-all ${
                        isSelectedForCompare
                          ? 'bg-primary text-primary-foreground border-primary'
                          : 'bg-muted/40 text-text-muted border-border/60 hover:text-foreground hover:bg-muted'
                      }`}
                    >
                      {isSelectedForCompare ? 'Selected' : '+ Compare'}
                    </button>
                    <button
                      onClick={() => setActiveModalItem(item)}
                      className="p-1 text-text-muted hover:text-primary transition-colors"
                      title="Why this score?"
                    >
                      <HelpCircle className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>
      )}

      {/* "Why This Score?" Detail Modal */}
      <AnimatePresence>
        {activeModalItem && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-card border border-border rounded-2xl p-6 max-w-lg w-full shadow-2xl flex flex-col gap-4 text-xs"
            >
              <div className="flex items-center justify-between border-b border-border/60 pb-3">
                <div>
                  <h3 className="text-base font-bold text-foreground">{activeModalItem.name}</h3>
                  <p className="text-text-muted font-mono">
                    {activeModalItem.symbol} · {activeModalItem.asset_category}
                  </p>
                </div>
                <button
                  onClick={() => setActiveModalItem(null)}
                  className="p-1 rounded-lg hover:bg-muted text-text-muted"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Rationale explanation */}
              <div className="bg-primary/10 border border-primary/20 rounded-xl p-3 text-foreground leading-relaxed">
                <strong>Opportunity Rationale:</strong> {activeModalItem.explanation}
              </div>

              {/* Signals checklist */}
              <div>
                <h4 className="font-bold text-foreground mb-2 flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" /> Grounded Market Signals
                </h4>
                <ul className="space-y-1.5 text-text-muted">
                  {activeModalItem.scores.signals.map((sig, i) => (
                    <li
                      key={i}
                      className="flex items-center gap-2 bg-muted/30 px-2.5 py-1.5 rounded-lg"
                    >
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                      <span className="capitalize">{sig.replace(/_/g, ' ')}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Confidence & Provider details */}
              <div className="grid grid-cols-2 gap-3 pt-2 border-t border-border/60 text-text-muted font-mono">
                <div>
                  Confidence Score:{' '}
                  <strong className="text-foreground">
                    {(activeModalItem.scores.confidence * 100).toFixed(0)}%
                  </strong>
                </div>
                <div>
                  Data Source:{' '}
                  <strong className="text-foreground">{activeModalItem.provider}</strong>
                </div>
              </div>

              {/* Mandatory Safety Notice */}
              <div className="bg-muted/40 p-3 rounded-xl text-[10px] text-text-muted leading-tight border border-border/40">
                ℹ️ Educational disclaimers: All opportunity scores are analytical assessments
                computed from quantitative market data. Returns are subject to market risks and
                never guaranteed.
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
