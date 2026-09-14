import { Link } from 'react-router-dom'
import { ShieldCheck, ArrowRight, AlertCircle } from 'lucide-react'
import { useCreditworthiness } from '@/hooks/useCreditworthiness'
import { cn } from '@/utils'

export function DcsSummaryWidget({ className }) {
  const { summaryData, isSummaryLoading } = useCreditworthiness()

  if (isSummaryLoading) {
    return (
      <div
        className={cn(
          'clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl animate-pulse flex flex-col gap-3',
          className
        )}
      >
        <div className="h-4 bg-muted/40 w-1/3 rounded" />
        <div className="h-8 bg-muted/40 w-1/2 rounded" />
        <div className="h-4 bg-muted/40 w-2/3 rounded" />
      </div>
    )
  }

  const {
    creditworthiness_score,
    status,
    risk_band,
    confidence_label,
    months_available = 0,
    loan_readiness,
    score_status,
  } = summaryData || {}

  const isInsufficient =
    status === 'INSUFFICIENT_DATA' ||
    creditworthiness_score === null ||
    creditworthiness_score === undefined

  const getRiskBandBadge = (band) => {
    switch (band) {
      case 'STRONG':
        return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'
      case 'GOOD':
        return 'bg-blue-500/10 text-blue-500 border-blue-500/20'
      case 'MODERATE':
        return 'bg-amber-500/10 text-amber-500 border-amber-500/20'
      case 'HIGH_RISK':
      case 'VERY_HIGH_RISK':
        return 'bg-rose-500/10 text-rose-500 border-rose-500/20'
      default:
        return 'bg-muted/30 text-text-muted border-border'
    }
  }

  const formatReadiness = (state) => {
    switch (state) {
      case 'READY':
        return 'Loan Ready'
      case 'NEARLY_READY':
        return 'Nearly Ready'
      case 'BUILD_HISTORY':
        return 'Build History'
      case 'HIGH_RISK':
        return 'High Risk'
      default:
        return 'Insufficient Data'
    }
  }

  return (
    <div
      className={cn(
        'clay-surface bg-card p-5 border border-white/60 dark:border-white/5 shadow-card flex flex-col justify-between gap-4 select-none relative group overflow-hidden rounded-2xl text-left',
        className
      )}
    >
      {/* Top Header Row */}
      <div className="flex items-center justify-between gap-2 border-b border-border/50 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-xl bg-primary/10 text-primary border border-primary/20">
            <ShieldCheck className="h-4 w-4" />
          </div>
          <div>
            <h4 className="text-xs font-black text-text-primary tracking-tight">
              DhanSarthi Creditworthiness Score
            </h4>
            <span className="text-[10px] font-bold text-text-muted">
              Proprietary DCS Assessment
            </span>
          </div>
        </div>

        {score_status === 'STALE' && (
          <span className="text-[9px] font-extrabold bg-amber-500/10 text-amber-500 border border-amber-500/20 px-2 py-0.5 rounded-full">
            Data Updated
          </span>
        )}
      </div>

      {/* Main Content Body */}
      {isInsufficient ? (
        <div className="flex flex-col gap-2.5 py-1">
          <div className="flex items-center gap-2 text-amber-500 font-black text-sm">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>Build your financial history</span>
          </div>
          <p className="text-xs text-text-muted font-bold leading-relaxed">
            DhanSarthi needs more verified financial history before calculating your
            creditworthiness score.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 py-1 items-center">
          {/* Score */}
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
              Score
            </span>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-black text-text-primary tracking-tight">
                {creditworthiness_score}
              </span>
              <span className="text-xs font-bold text-text-muted">/ 100</span>
            </div>
          </div>

          {/* Risk Band */}
          <div className="flex flex-col gap-1">
            <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
              Risk Band
            </span>
            <span
              className={cn(
                'text-[10px] font-black px-2 py-0.5 rounded-full border w-fit uppercase',
                getRiskBandBadge(risk_band)
              )}
            >
              {risk_band ? risk_band.replace('_', ' ') : 'N/A'}
            </span>
          </div>

          {/* Confidence & Coverage */}
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
              Confidence & History
            </span>
            <span className="text-xs font-black text-text-primary">
              {confidence_label || 'LOW'} • {months_available} mo
            </span>
          </div>

          {/* Loan Readiness */}
          <div className="flex flex-col gap-1">
            <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
              Loan Readiness
            </span>
            <span className="text-xs font-black text-primary">
              {formatReadiness(loan_readiness)}
            </span>
          </div>
        </div>
      )}

      {/* Action CTA Footer */}
      <div className="pt-2 border-t border-border/40 flex justify-between items-center">
        <span className="text-[10px] font-bold text-text-muted">
          Internal assessment • Not a CIBIL score
        </span>
        <Link
          to="/creditworthiness"
          className="inline-flex items-center gap-1.5 text-xs font-black text-primary hover:text-primary-hover transition-colors"
        >
          <span>View Creditworthiness</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>
    </div>
  )
}

export default DcsSummaryWidget
