import React from 'react'
import { Award, AlertTriangle, HelpCircle, CheckCircle2 } from 'lucide-react'

export function CreditScoreGauge({
  score,
  status,
  riskBand,
  confidenceLabel,
  dataCoverage,
  onRecalculate,
  isRecalculating,
}) {
  const isInsufficient = status === 'INSUFFICIENT_DATA' || score === null

  const getRiskBandConfig = (band) => {
    switch (band) {
      case 'STRONG':
        return {
          label: 'Strong Financial Position',
          color: 'text-emerald-400',
          bg: 'bg-emerald-500/10 border-emerald-500/30',
        }
      case 'GOOD':
        return {
          label: 'Good Financial Health',
          color: 'text-teal-400',
          bg: 'bg-teal-500/10 border-teal-500/30',
        }
      case 'MODERATE':
        return {
          label: 'Moderate Position',
          color: 'text-amber-400',
          bg: 'bg-amber-500/10 border-amber-500/30',
        }
      case 'HIGH_RISK':
        return {
          label: 'High Risk Profile',
          color: 'text-rose-400',
          bg: 'bg-rose-500/10 border-rose-500/30',
        }
      case 'VERY_HIGH_RISK':
        return {
          label: 'Very High Risk',
          color: 'text-red-500',
          bg: 'bg-red-500/10 border-red-500/30',
        }
      default:
        return {
          label: 'Insufficient Data',
          color: 'text-slate-400',
          bg: 'bg-slate-500/10 border-slate-500/30',
        }
    }
  }

  const bandConfig = getRiskBandConfig(riskBand)

  // Circular progress calculation
  const radius = 70
  const circumference = 2 * Math.PI * radius
  const normalizedScore = isInsufficient ? 0 : Math.min(100, Math.max(0, score))
  const strokeDashoffset = circumference - (normalizedScore / 100) * circumference

  return (
    <div className="bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden flex flex-col md:flex-row items-center gap-6">
      {/* Visual Radial Gauge */}
      <div className="relative flex items-center justify-center w-48 h-48 shrink-0">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 160 160">
          <circle
            cx="80"
            cy="80"
            r={radius}
            className="stroke-slate-800"
            strokeWidth="12"
            fill="transparent"
          />
          {!isInsufficient && (
            <circle
              cx="80"
              cy="80"
              r={radius}
              className="stroke-emerald-500 transition-all duration-1000 ease-out"
              strokeWidth="12"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              fill="transparent"
            />
          )}
        </svg>

        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          {isInsufficient ? (
            <>
              <HelpCircle className="w-8 h-8 text-amber-400 mb-1" />
              <span className="text-sm font-semibold text-slate-400">N/A</span>
              <span className="text-xs text-amber-400 font-medium">Insufficient</span>
            </>
          ) : (
            <>
              <span className="text-4xl font-extrabold text-white tracking-tight">{score}</span>
              <span className="text-xs text-slate-400 font-medium mt-0.5">out of 100</span>
            </>
          )}
        </div>
      </div>

      {/* Details & Status */}
      <div className="flex-1 space-y-3 text-center md:text-left">
        <div className="flex flex-wrap items-center justify-center md:justify-start gap-2">
          <span className="text-xs font-bold tracking-wider uppercase text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
            DhanSarthi DCS
          </span>
          <span
            className={`text-xs font-semibold px-3 py-1 rounded-full border ${bandConfig.bg} ${bandConfig.color}`}
          >
            {bandConfig.label}
          </span>
        </div>

        <h2 className="text-2xl font-bold text-white tracking-tight">
          {isInsufficient
            ? 'Insufficient Financial Data'
            : `DhanSarthi Creditworthiness Score: ${score}`}
        </h2>

        <p className="text-sm text-slate-300 leading-relaxed max-w-xl">
          {isInsufficient
            ? 'We need at least 30 days of active financial transactions or verified financial documents inside DhanSarthi before generating your creditworthiness profile.'
            : 'Internal deterministic evaluation calculated from your authenticated income, expense, debt burden, asset reserves, and budget adherence data.'}
        </p>

        <div className="flex flex-wrap items-center justify-center md:justify-start gap-4 pt-2 text-xs text-slate-400">
          <div>
            <span>Data Confidence: </span>
            <strong className="text-slate-200">{confidenceLabel || 'LOW'}</strong>
          </div>
          <div>
            <span>Active Months: </span>
            <strong className="text-slate-200">
              {dataCoverage?.months_available || 0} / 6 Preferred
            </strong>
          </div>
          <div>
            <span>Domains Active: </span>
            <strong className="text-slate-200">
              {dataCoverage?.domains_active_count || 0} / 6
            </strong>
          </div>
        </div>

        <div className="pt-2">
          <button
            onClick={onRecalculate}
            disabled={isRecalculating}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 text-white text-xs font-semibold rounded-xl transition shadow-md flex items-center justify-center gap-2"
          >
            {isRecalculating ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Recalculating DCS...</span>
              </>
            ) : (
              <span>Recalculate Score</span>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default CreditScoreGauge
