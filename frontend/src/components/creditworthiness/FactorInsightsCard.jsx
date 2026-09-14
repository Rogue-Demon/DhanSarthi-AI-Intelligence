import React from 'react'
import { CheckCircle2, AlertTriangle } from 'lucide-react'

export function FactorInsightsCard({ positiveFactors = [], riskFactors = [] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Positive Drivers */}
      <div className="bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
          <div className="p-1.5 bg-emerald-500/10 text-emerald-400 rounded-lg">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Positive Financial Signals
            </h3>
            <p className="text-xs text-slate-400">
              Strengths supporting your creditworthiness profile
            </p>
          </div>
        </div>

        {positiveFactors.length === 0 ? (
          <p className="text-xs text-slate-500 italic py-4 text-center">
            No distinct positive signals identified yet.
          </p>
        ) : (
          <ul className="space-y-3">
            {positiveFactors.map((factor, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2.5 text-xs text-slate-300 leading-relaxed bg-emerald-950/20 border border-emerald-500/10 p-2.5 rounded-lg"
              >
                <span className="text-emerald-400 font-bold shrink-0">✓</span>
                <span>{factor}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Areas to Improve / Risk Factors */}
      <div className="bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
          <div className="p-1.5 bg-amber-500/10 text-amber-400 rounded-lg">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white tracking-tight">Areas to Improve</h3>
            <p className="text-xs text-slate-400">Key risk areas affecting your overall rating</p>
          </div>
        </div>

        {riskFactors.length === 0 ? (
          <p className="text-xs text-slate-500 italic py-4 text-center">
            No critical risk areas identified.
          </p>
        ) : (
          <ul className="space-y-3">
            {riskFactors.map((factor, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2.5 text-xs text-slate-300 leading-relaxed bg-amber-950/20 border border-amber-500/10 p-2.5 rounded-lg"
              >
                <span className="text-amber-400 font-bold shrink-0">⚠</span>
                <span>{factor}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

export default FactorInsightsCard
