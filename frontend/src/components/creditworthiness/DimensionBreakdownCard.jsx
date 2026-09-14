import React from 'react'

export function DimensionBreakdownCard({ dimensionScores }) {
  if (!dimensionScores || Object.keys(dimensionScores).length === 0) {
    return null
  }

  const dimensionsList = Object.values(dimensionScores)

  return (
    <div className="bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-lg font-bold text-white tracking-tight">
            Creditworthiness Dimensions
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Weighted performance across 6 financial pillars
          </p>
        </div>
        <span className="text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full font-medium">
          6 Pillars Evaluated
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {dimensionsList.map((dim) => {
          const scoreVal = Math.min(100, Math.max(0, dim.score || 0))
          const weightPct = Math.round((dim.weight || 0) * 100)

          let colorClass = 'bg-emerald-500'
          if (scoreVal < 40) colorClass = 'bg-rose-500'
          else if (scoreVal < 70) colorClass = 'bg-amber-500'

          return (
            <div
              key={dim.name}
              className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 space-y-2"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-slate-200">{dim.label}</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">Weight: {weightPct}%</span>
                  <span className="text-sm font-bold text-white">{Math.round(scoreVal)}/100</span>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
                <div
                  className={`h-full ${colorClass} transition-all duration-700 ease-out`}
                  style={{ width: `${scoreVal}%` }}
                />
              </div>

              <p className="text-xs text-slate-400 leading-normal">{dim.description}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default DimensionBreakdownCard
