import React from 'react'
import { TrendingUp, Calendar } from 'lucide-react'

export function CreditHistoryChart({ history = [] }) {
  if (!history || history.length === 0) {
    return (
      <div className="bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-2xl p-6 shadow-xl text-center space-y-2">
        <TrendingUp className="w-8 h-8 text-slate-600 mx-auto" />
        <h3 className="text-sm font-bold text-slate-300">No Historical Score Snapshots Yet</h3>
        <p className="text-xs text-slate-500">
          Historical DCS creditworthiness snapshots will automatically appear here as your financial
          tracking progresses over time.
        </p>
      </div>
    )
  }

  // Find max score for relative scaling
  const validScores = history.map((h) => h.score || 0)
  const maxScore = Math.max(100, ...validScores)

  return (
    <div className="bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-emerald-500/10 text-emerald-400 rounded-lg">
            <TrendingUp className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white tracking-tight">
              DCS Score Progression History
            </h3>
            <p className="text-xs text-slate-400">
              Historical snapshots tracking your internal score movement
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-3 pt-2">
        {history.map((snap, idx) => {
          const scoreVal = snap.score !== null && snap.score !== undefined ? snap.score : 0
          const pct = Math.min(100, Math.max(0, (scoreVal / maxScore) * 100))

          return (
            <div key={idx} className="flex items-center gap-4 text-xs">
              <div className="w-24 shrink-0 text-slate-400 flex items-center gap-1">
                <Calendar className="w-3 h-3 text-slate-500" />
                <span>{snap.snapshot_date}</span>
              </div>

              <div className="flex-1 bg-slate-950 border border-slate-800 h-6 rounded-lg p-1 relative overflow-hidden flex items-center">
                <div
                  className="bg-emerald-600/80 h-full rounded transition-all duration-500"
                  style={{ width: `${pct}%` }}
                />
                <span className="absolute right-2 font-bold text-white text-xs">
                  {snap.score !== null ? `${snap.score} pts` : 'N/A'}
                </span>
              </div>

              <span className="w-24 shrink-0 text-right font-medium text-slate-300">
                {snap.risk_band}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default CreditHistoryChart
